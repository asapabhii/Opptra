from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import aiosqlite


async def fetch_latest_run(db: aiosqlite.Connection) -> Optional[dict]:
    cursor = await db.execute(
        "SELECT id, triggered_at, status, sku_count, completed_at, cost_usd, prompt_version FROM queue_runs ORDER BY triggered_at DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    return {
        "id": row[0],
        "triggered_at": row[1],
        "status": row[2],
        "sku_count": row[3],
        "completed_at": row[4],
        "cost_usd": row[5],
        "prompt_version": row[6],
    }


async def insert_queue_run(db: aiosqlite.Connection, run_id: str, sku_count: int) -> None:
    await db.execute(
        "INSERT INTO queue_runs (id, triggered_at, status, sku_count) VALUES (?, ?, 'running', ?)",
        (run_id, datetime.now(timezone.utc).isoformat(), sku_count),
    )


async def update_queue_run_complete(
    db: aiosqlite.Connection, run_id: str, cost_usd: float, prompt_version: str
) -> None:
    await db.execute(
        "UPDATE queue_runs SET status='complete', completed_at=?, cost_usd=?, prompt_version=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), cost_usd, prompt_version, run_id),
    )


async def update_queue_run_failed(db: aiosqlite.Connection, run_id: str) -> None:
    await db.execute(
        "UPDATE queue_runs SET status='failed', completed_at=? WHERE id=?",
        (datetime.now(timezone.utc).isoformat(), run_id),
    )


async def insert_recommendation(db: aiosqlite.Connection, run_id: str, rec: dict) -> None:
    await db.execute(
        """
        INSERT INTO sku_recommendations (
          id, run_id, sku_id, recommended_price, action_type, confidence,
          margin_floor, margin_at_recommended, margin_pct_at_recommended,
          competitor_classification, temporal_persistence, competitor_price_gap,
          revenue_at_risk_7d, days_to_stockout_current, days_to_stockout_recommended,
          projected_velocity_change, reasoning, flags, model_used, source,
          prompt_version, input_tokens, output_tokens, latency_ms, generated_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rec["id"],
            run_id,
            rec["sku_id"],
            rec["recommended_price"],
            rec["action_type"],
            rec["confidence"],
            rec["margin_floor"],
            rec["margin_at_recommended_price"],
            rec["margin_pct_at_recommended_price"],
            rec["competitor_classification"],
            rec["temporal_persistence"],
            rec["competitor_price_gap"],
            rec["revenue_at_risk_7d"],
            rec.get("days_to_stockout_current"),
            rec.get("days_to_stockout_recommended"),
            rec["projected_velocity_change"],
            rec["reasoning"],
            json.dumps(rec.get("flags", [])),
            rec.get("model_used"),
            rec.get("source"),
            rec.get("prompt_version", "v1.0"),
            rec.get("input_tokens"),
            rec.get("output_tokens"),
            rec.get("latency_ms"),
            rec.get("generated_at"),
            rec.get("status", "pending"),
        ),
    )


async def fetch_recommendation_by_id(db: aiosqlite.Connection, recommendation_id: str) -> Optional[dict]:
    cursor = await db.execute(
        "SELECT id, sku_id, recommended_price, action_type, status FROM sku_recommendations WHERE id=?",
        (recommendation_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    return {
        "id": row[0],
        "sku_id": row[1],
        "recommended_price": row[2],
        "action_type": row[3],
        "status": row[4],
    }


async def fetch_decision_by_recommendation_id(
    db: aiosqlite.Connection, recommendation_id: str
) -> Optional[dict]:
    cursor = await db.execute(
        "SELECT id, sku_id, recommendation_id, decision, original_recommended_price, human_chosen_price, snooze_duration_hours, override_reason_category, override_reason_free_text, override_insight, decided_at, resurfaced_at, outcome_check_due_at, buy_box_recovered, velocity_delta, outcome_note FROM decisions WHERE recommendation_id=? ORDER BY decided_at DESC LIMIT 1",
        (recommendation_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if not row:
        return None
    return {
        "id": row[0],
        "sku_id": row[1],
        "recommendation_id": row[2],
        "decision": row[3],
        "original_recommended_price": row[4],
        "human_chosen_price": row[5],
        "snooze_duration_hours": row[6],
        "override_reason_category": row[7],
        "override_reason_free_text": row[8],
        "override_insight": row[9],
        "decided_at": row[10],
        "resurfaced_at": row[11],
        "outcome_check_due_at": row[12],
        "buy_box_recovered": row[13],
        "velocity_delta": row[14],
        "outcome_note": row[15],
    }


async def update_recommendation_status(
    db: aiosqlite.Connection, recommendation_id: str, status: str
) -> None:
    await db.execute(
        "UPDATE sku_recommendations SET status=? WHERE id=?",
        (status, recommendation_id),
    )


async def fetch_recommendations_for_run(db: aiosqlite.Connection, run_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT id, sku_id, recommended_price, action_type, confidence, margin_floor, margin_at_recommended, margin_pct_at_recommended, competitor_classification, temporal_persistence, competitor_price_gap, revenue_at_risk_7d, days_to_stockout_current, days_to_stockout_recommended, projected_velocity_change, reasoning, flags, model_used, source, prompt_version, generated_at, status FROM sku_recommendations WHERE run_id=?",
        (run_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    recommendations = []
    for row in rows:
        recommendations.append(
            {
                "id": row[0],
                "sku_id": row[1],
                "recommended_price": row[2],
                "action_type": row[3],
                "confidence": row[4],
                "margin_floor": row[5],
                "margin_at_recommended": row[6],
                "margin_pct_at_recommended": row[7],
                "competitor_classification": row[8],
                "temporal_persistence": row[9],
                "competitor_price_gap": row[10],
                "revenue_at_risk_7d": row[11],
                "days_to_stockout_current": row[12],
                "days_to_stockout_recommended": row[13],
                "projected_velocity_change": row[14],
                "reasoning": row[15],
                "flags": json.loads(row[16]),
                "model_used": row[17],
                "source": row[18],
                "prompt_version": row[19],
                "generated_at": row[20],
                "status": row[21],
            }
        )
    return recommendations


async def insert_cluster(db: aiosqlite.Connection, run_id: str, cluster: dict, display_order: int) -> None:
    await db.execute(
        """
        INSERT INTO action_clusters (
          id, run_id, cluster_name, root_cause, action_type, sku_ids, sku_count,
          combined_gmv_at_risk, combined_working_capital, headline, impact_score, display_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cluster["id"],
            run_id,
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


async def fetch_clusters_for_run(db: aiosqlite.Connection, run_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT id, cluster_name, root_cause, action_type, sku_ids, sku_count, combined_gmv_at_risk, combined_working_capital, headline, impact_score, display_order FROM action_clusters WHERE run_id=? ORDER BY display_order ASC",
        (run_id,),
    )
    rows = await cursor.fetchall()
    await cursor.close()
    clusters = []
    for row in rows:
        clusters.append(
            {
                "id": row[0],
                "cluster_name": row[1],
                "root_cause": row[2],
                "action_type": row[3],
                "sku_ids": json.loads(row[4]),
                "sku_count": row[5],
                "combined_gmv_at_risk_inr": row[6],
                "combined_working_capital_inr": row[7],
                "headline": row[8],
                "impact_score": row[9],
                "display_order": row[10],
            }
        )
    return clusters


async def fetch_decisions(db: aiosqlite.Connection, filters: dict) -> dict:
    base = "SELECT id, sku_id, decision, original_recommended_price, human_chosen_price, override_reason_category, override_insight, decided_at, buy_box_recovered, velocity_delta, outcome_note FROM decisions"
    clauses = []
    params: list[Any] = []
    if filters.get("sku_id"):
        clauses.append("sku_id=?")
        params.append(filters["sku_id"])
    if filters.get("decision"):
        clauses.append("decision=?")
        params.append(filters["decision"])
    if filters.get("date_from"):
        clauses.append("decided_at>=?")
        params.append(filters["date_from"])
    if filters.get("date_to"):
        clauses.append("decided_at<=?")
        params.append(filters["date_to"])
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    order = " ORDER BY decided_at DESC"
    limit = " LIMIT ? OFFSET ?"
    params.extend([filters.get("limit", 50), filters.get("offset", 0)])

    cursor = await db.execute(base + where + order + limit, params)
    rows = await cursor.fetchall()
    await cursor.close()

    decisions = []
    for row in rows:
        decisions.append(
            {
                "id": row[0],
                "sku_id": row[1],
                "decision": row[2],
                "original_recommended_price": row[3],
                "human_chosen_price": row[4],
                "override_reason_category": row[5],
                "override_insight": row[6],
                "decided_at": row[7],
                "buy_box_recovered": row[8],
                "velocity_delta": row[9],
                "outcome_note": row[10],
            }
        )
    return {
        "decisions": decisions,
        "total_count": len(decisions),
        "limit": filters.get("limit", 50),
        "offset": filters.get("offset", 0),
    }


async def fetch_recent_decisions_for_skus(
    db: aiosqlite.Connection, sku_ids: list[str], limit_per_sku: int = 5
) -> dict[str, list[dict]]:
    if not sku_ids:
        return {}
    placeholders = ",".join("?" for _ in sku_ids)
    query = (
        "SELECT sku_id, decided_at, decision, original_recommended_price, human_chosen_price, "
        "buy_box_recovered, velocity_delta "
        "FROM decisions WHERE sku_id IN (" + placeholders + ") ORDER BY decided_at DESC"
    )
    cursor = await db.execute(query, sku_ids)
    rows = await cursor.fetchall()
    await cursor.close()

    grouped: dict[str, list[dict]] = {sku_id: [] for sku_id in sku_ids}
    for row in rows:
        sku_id = row[0]
        if len(grouped[sku_id]) >= limit_per_sku:
            continue
        grouped[sku_id].append(
            {
                "date": row[1],
                "decision": row[2],
                "original_recommended_price": row[3],
                "human_chosen_price": row[4],
                "buy_box_recovered": row[5],
                "outcome_velocity_delta": row[6],
            }
        )
    return grouped


async def insert_decision(db: aiosqlite.Connection, decision: dict) -> dict:
    await db.execute(
        """
        INSERT INTO decisions (
          id, sku_id, recommendation_id, decision, original_recommended_price,
          human_chosen_price, snooze_duration_hours, override_reason_category,
          override_reason_free_text, override_insight, decided_at, resurfaced_at,
          outcome_check_due_at, buy_box_recovered, velocity_delta, outcome_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            decision.get("outcome_check_due_at"),
            decision.get("buy_box_recovered"),
            decision.get("velocity_delta"),
            decision.get("outcome_note"),
        ),
    )
    return decision
