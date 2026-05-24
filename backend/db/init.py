from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

from services.fallback_engine import build_fallback_recommendation
from services.cluster_engine import build_rule_based_clusters
from services.signal_engine import compute_all_signals, load_data_stores
from services.sku_scanner import get_candidates

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS queue_runs (
  id              TEXT PRIMARY KEY,
  triggered_at    TEXT NOT NULL,
  status          TEXT NOT NULL CHECK(status IN ('running','complete','failed')),
  sku_count       INTEGER,
  completed_at    TEXT,
  cost_usd        REAL,
  prompt_version  TEXT NOT NULL DEFAULT 'v1.0'
);
CREATE TABLE IF NOT EXISTS sku_recommendations (
  id                           TEXT PRIMARY KEY,
  run_id                       TEXT NOT NULL,
  sku_id                       TEXT NOT NULL,
  recommended_price            REAL NOT NULL,
  action_type                  TEXT NOT NULL CHECK(action_type IN
    ('reduce_price','raise_price','hold_price','escalate_to_human')),
  confidence                   TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
  margin_floor                 REAL NOT NULL,
  margin_at_recommended        REAL NOT NULL,
  margin_pct_at_recommended    REAL NOT NULL,
  competitor_classification    TEXT NOT NULL CHECK(competitor_classification IN
    ('grey_market','authorized','unknown','none')),
  temporal_persistence         TEXT CHECK(temporal_persistence IN
    ('short_cycle','medium_cycle','structural','unknown','none')),
  competitor_price_gap         REAL NOT NULL,
  revenue_at_risk_7d           REAL NOT NULL,
  days_to_stockout_current     INTEGER,
  days_to_stockout_recommended INTEGER,
  projected_velocity_change    TEXT NOT NULL,
  reasoning                    TEXT NOT NULL,
  flags                        TEXT NOT NULL DEFAULT '[]',
  model_used                   TEXT NOT NULL,
  source                       TEXT NOT NULL CHECK(source IN
    ('ai_claude_sonnet','ai_gpt4o_fallback','ai_grok_fallback','rule_engine_fallback')),
  prompt_version               TEXT NOT NULL DEFAULT 'v1.0',
  input_tokens                 INTEGER,
  output_tokens                INTEGER,
  latency_ms                   INTEGER,
  generated_at                 TEXT NOT NULL,
  status                       TEXT NOT NULL DEFAULT 'pending' CHECK(status IN
    ('pending','approved','overridden','snoozed','archived')),
  FOREIGN KEY (run_id) REFERENCES queue_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_sku_rec_run_id ON sku_recommendations(run_id);
CREATE INDEX IF NOT EXISTS idx_sku_rec_sku_id ON sku_recommendations(sku_id);
CREATE INDEX IF NOT EXISTS idx_sku_rec_status ON sku_recommendations(status);
CREATE TABLE IF NOT EXISTS action_clusters (
  id                       TEXT PRIMARY KEY,
  run_id                   TEXT NOT NULL,
  cluster_name             TEXT NOT NULL,
  root_cause               TEXT NOT NULL,
  action_type              TEXT NOT NULL,
  sku_ids                  TEXT NOT NULL,
  sku_count                INTEGER NOT NULL,
  combined_gmv_at_risk     REAL NOT NULL,
  combined_working_capital REAL NOT NULL,
  headline                 TEXT NOT NULL,
  impact_score             REAL NOT NULL,
  display_order            INTEGER NOT NULL,
  FOREIGN KEY (run_id) REFERENCES queue_runs(id)
);
CREATE INDEX IF NOT EXISTS idx_cluster_run_id ON action_clusters(run_id);
CREATE TABLE IF NOT EXISTS decisions (
  id                         TEXT PRIMARY KEY,
  sku_id                     TEXT NOT NULL,
  recommendation_id          TEXT NOT NULL,
  decision                   TEXT NOT NULL CHECK(decision IN
    ('approved','overridden','snoozed')),
  original_recommended_price REAL NOT NULL,
  human_chosen_price         REAL,
  snooze_duration_hours      INTEGER,
  override_reason_category   TEXT CHECK(override_reason_category IN (
    'map_constraint','competitor_context','festival_season','brand_instruction',
    'price_direction_wrong','price_magnitude_wrong','data_quality_doubt','other')),
  override_reason_free_text  TEXT,
  override_insight           TEXT,
  decided_at                 TEXT NOT NULL,
  resurfaced_at              TEXT,
  outcome_check_due_at       TEXT,
  buy_box_recovered          INTEGER CHECK(buy_box_recovered IN (0,1)),
  velocity_delta             REAL,
  outcome_note               TEXT,
  FOREIGN KEY (recommendation_id) REFERENCES sku_recommendations(id)
);
CREATE INDEX IF NOT EXISTS idx_decisions_sku_id ON decisions(sku_id);
CREATE INDEX IF NOT EXISTS idx_decisions_decided_at ON decisions(decided_at);
CREATE TABLE IF NOT EXISTS portfolio_synthesis (
  id            TEXT PRIMARY KEY,
  generated_at  TEXT NOT NULL,
  records_count INTEGER NOT NULL,
  report_json   TEXT NOT NULL,
  model_used    TEXT NOT NULL DEFAULT 'gemini-1.5-pro'
);
"""


def _db_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "decisions.db")))


async def initialize_database() -> None:
    db_path = _db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await _ensure_sku_recommendation_source_constraint(db)
        await db.commit()

        await _seed_if_needed(db)


async def _ensure_sku_recommendation_source_constraint(db: aiosqlite.Connection) -> None:
    cursor = await db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sku_recommendations'")
    row = await cursor.fetchone()
    await cursor.close()
    if not row or not row[0] or "ai_grok_fallback" in row[0]:
        return

    await db.execute("PRAGMA foreign_keys=OFF")
    await db.execute("ALTER TABLE sku_recommendations RENAME TO sku_recommendations_legacy")
    await db.execute(
        """
        CREATE TABLE sku_recommendations (
          id                           TEXT PRIMARY KEY,
          run_id                       TEXT NOT NULL,
          sku_id                       TEXT NOT NULL,
          recommended_price            REAL NOT NULL,
          action_type                  TEXT NOT NULL CHECK(action_type IN
            ('reduce_price','raise_price','hold_price','escalate_to_human')),
          confidence                   TEXT NOT NULL CHECK(confidence IN ('high','medium','low')),
          margin_floor                 REAL NOT NULL,
          margin_at_recommended        REAL NOT NULL,
          margin_pct_at_recommended    REAL NOT NULL,
          competitor_classification    TEXT NOT NULL CHECK(competitor_classification IN
            ('grey_market','authorized','unknown','none')),
          temporal_persistence         TEXT CHECK(temporal_persistence IN
            ('short_cycle','medium_cycle','structural','unknown','none')),
          competitor_price_gap         REAL NOT NULL,
          revenue_at_risk_7d           REAL NOT NULL,
          days_to_stockout_current     INTEGER,
          days_to_stockout_recommended INTEGER,
          projected_velocity_change    TEXT NOT NULL,
          reasoning                    TEXT NOT NULL,
          flags                        TEXT NOT NULL DEFAULT '[]',
          model_used                   TEXT NOT NULL,
          source                       TEXT NOT NULL CHECK(source IN
            ('ai_claude_sonnet','ai_gpt4o_fallback','ai_grok_fallback','rule_engine_fallback')),
          prompt_version               TEXT NOT NULL DEFAULT 'v1.0',
          input_tokens                 INTEGER,
          output_tokens                INTEGER,
          latency_ms                   INTEGER,
          generated_at                 TEXT NOT NULL,
          status                       TEXT NOT NULL DEFAULT 'pending' CHECK(status IN
            ('pending','approved','overridden','snoozed','archived')),
          FOREIGN KEY (run_id) REFERENCES queue_runs(id)
        );
        """
    )
    await db.execute(
        """
        INSERT INTO sku_recommendations (
          id, run_id, sku_id, recommended_price, action_type, confidence,
          margin_floor, margin_at_recommended, margin_pct_at_recommended,
          competitor_classification, temporal_persistence, competitor_price_gap,
          revenue_at_risk_7d, days_to_stockout_current, days_to_stockout_recommended,
          projected_velocity_change, reasoning, flags, model_used, source,
          prompt_version, input_tokens, output_tokens, latency_ms, generated_at, status
        )
        SELECT
          id, run_id, sku_id, recommended_price, action_type, confidence,
          margin_floor, margin_at_recommended, margin_pct_at_recommended,
          competitor_classification, temporal_persistence, competitor_price_gap,
          revenue_at_risk_7d, days_to_stockout_current, days_to_stockout_recommended,
          projected_velocity_change, reasoning, flags, model_used, source,
          prompt_version, input_tokens, output_tokens, latency_ms, generated_at, status
        FROM sku_recommendations_legacy
        """
    )
    await db.execute("DROP TABLE sku_recommendations_legacy")
    await db.execute("PRAGMA foreign_keys=ON")


async def _seed_if_needed(db: aiosqlite.Connection) -> None:
    load_data_stores()
    skus = json.loads((DATA_DIR / "skus.json").read_text(encoding="utf-8"))
    competitors = json.loads((DATA_DIR / "competitors.json").read_text(encoding="utf-8"))
    fee_config = json.loads((DATA_DIR / "fee_config.json").read_text(encoding="utf-8"))
    competitors_by_sku = {entry["sku_id"]: entry for entry in competitors}

    seed_data = json.loads((DATA_DIR / "decisions_seed.json").read_text(encoding="utf-8"))
    seed_run = seed_data["seed_run"]
    decisions = seed_data["decisions"]

    cursor = await db.execute("SELECT COUNT(*) FROM queue_runs")
    run_count = (await cursor.fetchone())[0]
    await cursor.close()

    if run_count == 0:
        await db.execute(
            "INSERT INTO queue_runs (id, triggered_at, status, sku_count, completed_at, cost_usd, prompt_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                seed_run["id"],
                seed_run["triggered_at"],
                seed_run["status"],
                seed_run["sku_count"],
                seed_run["completed_at"],
                seed_run["cost_usd"],
                seed_run["prompt_version"],
            ),
        )

    cursor = await db.execute("SELECT COUNT(*) FROM sku_recommendations")
    rec_count = (await cursor.fetchone())[0]
    await cursor.close()

    if rec_count == 0:
        # Build fallback recommendations for seeded visibility
        all_signals = {
            sku["sku_id"]: compute_all_signals(sku, competitors_by_sku.get(sku["sku_id"]), fee_config)
            for sku in skus
        }
        candidate_ids = set(get_candidates(all_signals))
        decision_map = {d["sku_id"]: d for d in decisions}

        for sku in skus:
            if sku["sku_id"] not in candidate_ids:
                continue
            payload = {
                "sku_id": sku["sku_id"],
                "sku_name": sku["sku_name"],
                "brand": sku["brand"],
                "sub_category": sku["sub_category"],
                "current_price": sku["current_price"],
                "cost": sku["cost"],
                "target_margin_pct": sku["target_margin_pct"],
                "map_price": sku.get("map_price"),
                "map_enforced": sku["map_enforced"],
                "buy_box_status": all_signals[sku["sku_id"]]["state_3"],
                "buy_box_winner": all_signals[sku["sku_id"]]["competitor"],
                "daily_velocity_30d": sku["daily_velocity_30d"],
                "units_on_hand": sku["units_on_hand"],
                "computed_margin_floor": all_signals[sku["sku_id"]]["margin_floor"],
            }
            rec = build_fallback_recommendation(payload)
            rec_id = decision_map.get(sku["sku_id"], {}).get("recommendation_id")
            if not rec_id:
                rec_id = f"seed-{uuid.uuid4().hex[:8]}"

            await db.execute(
                """
                INSERT INTO sku_recommendations (
                  id, run_id, sku_id, recommended_price, action_type, confidence,
                  margin_floor, margin_at_recommended, margin_pct_at_recommended,
                  competitor_classification, temporal_persistence, competitor_price_gap,
                  revenue_at_risk_7d, days_to_stockout_current, days_to_stockout_recommended,
                  projected_velocity_change, reasoning, flags, model_used, source,
                  prompt_version, generated_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec_id,
                    seed_run["id"],
                    sku["sku_id"],
                    rec.recommended_price,
                    rec.action_type,
                    rec.confidence,
                    rec.margin_floor,
                    rec.margin_at_recommended_price,
                    rec.margin_pct_at_recommended_price,
                    rec.competitor_classification,
                    rec.temporal_persistence,
                    rec.competitor_price_gap,
                    rec.revenue_at_risk_7d,
                    rec.days_to_stockout_current,
                    rec.days_to_stockout_recommended,
                    rec.projected_velocity_change,
                    rec.reasoning,
                    json.dumps(rec.flags),
                    rec.model_used or "rule_engine_fallback",
                    rec.source or "rule_engine_fallback",
                    seed_run["prompt_version"],
                    rec.generated_at or datetime.now(timezone.utc).isoformat(),
                    "pending",
                ),
            )

    cursor = await db.execute("SELECT COUNT(*) FROM decisions")
    decision_count = (await cursor.fetchone())[0]
    await cursor.close()

    if decision_count == 0:
        for decision in decisions:
            await db.execute(
                """
                INSERT INTO decisions (
                  id, sku_id, recommendation_id, decision, original_recommended_price,
                  human_chosen_price, snooze_duration_hours, override_reason_category,
                  override_reason_free_text, override_insight, decided_at, resurfaced_at,
                  buy_box_recovered, velocity_delta, outcome_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision["id"],
                    decision["sku_id"],
                    decision["recommendation_id"],
                    decision["decision"],
                    decision["original_recommended_price"],
                    decision.get("human_chosen_price"),
                    decision.get("snooze_duration_hours"),
                    decision.get("override_reason_category"),
                    decision.get("override_reason_free_text"),
                    decision.get("override_insight"),
                    decision["decided_at"],
                    decision.get("resurfaced_at"),
                    decision.get("buy_box_recovered"),
                    decision.get("velocity_delta"),
                    decision.get("outcome_note"),
                ),
            )
            await db.execute(
                "UPDATE sku_recommendations SET status = ? WHERE id = ?",
                (decision["decision"], decision["recommendation_id"]),
            )

    cursor = await db.execute("SELECT COUNT(*) FROM action_clusters")
    cluster_count = (await cursor.fetchone())[0]
    await cursor.close()

    if cluster_count == 0:
        all_signals = {
            sku["sku_id"]: compute_all_signals(sku, competitors_by_sku.get(sku["sku_id"]), fee_config)
            for sku in skus
        }
        skus_by_id = {sku["sku_id"]: sku for sku in skus}
        cursor = await db.execute(
            """
            SELECT id, sku_id, recommended_price, action_type, confidence,
                   competitor_classification, temporal_persistence, revenue_at_risk_7d, flags
            FROM sku_recommendations
            WHERE run_id=?
            """,
            (seed_run["id"],),
        )
        rows = await cursor.fetchall()
        await cursor.close()

        cluster_inputs = []
        for row in rows:
            sku = skus_by_id.get(row[1])
            if not sku:
                continue
            signals = all_signals[row[1]]
            cluster_inputs.append(
                {
                    "id": row[0],
                    "sku_id": row[1],
                    "sku_name": sku["sku_name"],
                    "brand": sku["brand"],
                    "sub_category": sku["sub_category"],
                    "buy_box_state_6": signals["state_6"],
                    "action_type": row[3],
                    "confidence": row[4],
                    "competitor_classification": row[5],
                    "temporal_persistence": row[6],
                    "doc_urgency": signals["doc_urgency"],
                    "revenue_at_risk_7d": row[7],
                    "working_capital_at_risk": sku["cost"] * sku["units_on_hand"],
                    "impact_score": signals["impact_score"],
                    "flags": json.loads(row[8]),
                }
            )

        clusters = build_rule_based_clusters(cluster_inputs)
        clusters.sort(key=lambda cluster: cluster.get("impact_score", 0.0), reverse=True)
        for display_order, cluster in enumerate(clusters, start=1):
            await db.execute(
                """
                INSERT INTO action_clusters (
                  id, run_id, cluster_name, root_cause, action_type, sku_ids, sku_count,
                  combined_gmv_at_risk, combined_working_capital, headline, impact_score, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"seed-cluster-{display_order:02d}",
                    seed_run["id"],
                    cluster["cluster_name"],
                    cluster["root_cause"],
                    cluster["action_type"],
                    json.dumps(cluster["sku_ids"]),
                    cluster["sku_count"],
                    cluster["combined_gmv_at_risk_inr"],
                    cluster["combined_working_capital_inr"],
                    cluster["headline"],
                    cluster["impact_score"],
                    display_order,
                ),
            )

    await db.commit()
