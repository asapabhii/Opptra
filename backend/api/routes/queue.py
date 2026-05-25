from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from api.dependencies import get_db
from db.queries import (
    fetch_clusters_for_run,
    fetch_latest_run,
    fetch_recent_decisions_for_skus,
    fetch_recommendations_for_run,
    insert_cluster,
    insert_queue_run,
    insert_recommendation,
    update_queue_run_complete,
    update_queue_run_failed,
)
from models.sku import DecisionHistoryItem
from services.ai_orchestrator import run_parallel
from services.cluster_engine import form_clusters
from services.payload_builder import build_payloads
from services.signal_engine import compute_all_signals, get_competitor_by_sku, get_fee_config, get_skus
from services.sku_scanner import get_candidates

router = APIRouter()

RUN_PROGRESS: dict[str, dict] = {}


@router.get("/runs/latest")
async def get_latest_queue_run():
    async with await get_db() as db:
        run = await fetch_latest_run(db)
        if not run:
            return {"run": None, "clusters": [], "recommendations": []}

        clusters = await fetch_clusters_for_run(db, run["id"])
        recommendations = await fetch_recommendations_for_run(db, run["id"])

    return {"run": run, "clusters": clusters, "recommendations": recommendations}


@router.post("/run", status_code=status.HTTP_202_ACCEPTED)
async def post_queue_run(background_tasks: BackgroundTasks):
    async with await get_db() as db:
        latest = await fetch_latest_run(db)
        if latest and latest["status"] == "running":
            raise HTTPException(status_code=409, detail="A queue run is already in progress")

        run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"
        await insert_queue_run(db, run_id, 0)
        await db.commit()

    RUN_PROGRESS[run_id] = {
        "run_id": run_id,
        "status": "running",
        "skus_processed": 0,
        "total_skus": 0,
        "current_sku_name": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    background_tasks.add_task(_process_queue_run, run_id)

    return {
        "run_id": run_id,
        "status": "running",
        "message": f"Queue run started. Poll /api/queue/runs/{run_id}/status for progress.",
    }


@router.get("/runs/{run_id}/status")
async def get_queue_run_status(run_id: str):
    if run_id in RUN_PROGRESS:
        return RUN_PROGRESS[run_id]

    async with await get_db() as db:
        latest = await fetch_latest_run(db)

    if latest and latest["id"] == run_id:
        return {
            "run_id": run_id,
            "status": latest["status"],
            "skus_processed": latest["sku_count"] or 0,
            "total_skus": latest["sku_count"] or 0,
            "current_sku_name": None,
        }

    raise HTTPException(status_code=404, detail=f"Queue run {run_id} not found")


async def _process_queue_run(run_id: str) -> None:
    try:
        RUN_PROGRESS.setdefault(
            run_id,
            {
                "run_id": run_id,
                "status": "running",
                "skus_processed": 0,
                "total_skus": 0,
                "current_sku_name": None,
                "started_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        skus = get_skus()
        fee_config = get_fee_config()
        competitors_by_sku = {sku["sku_id"]: get_competitor_by_sku(sku["sku_id"]) for sku in skus}
        signals_by_sku = {
            sku["sku_id"]: compute_all_signals(sku, competitors_by_sku.get(sku["sku_id"]), fee_config)
            for sku in skus
        }
        candidate_ids = set(get_candidates(signals_by_sku))
        candidate_skus = [sku for sku in skus if sku["sku_id"] in candidate_ids]
        candidate_skus.sort(
            key=lambda sku: signals_by_sku[sku["sku_id"]]["impact_score"], reverse=True
        )

        RUN_PROGRESS[run_id]["total_skus"] = len(candidate_skus)

        async with await get_db() as db:
            await db.execute("UPDATE queue_runs SET sku_count=? WHERE id=?", (len(candidate_skus), run_id))
            recent = await fetch_recent_decisions_for_skus(
                db, [sku["sku_id"] for sku in candidate_skus]
            )
            await db.commit()

        decision_history_by_sku = _build_decision_history(candidate_skus, recent)
        payloads = build_payloads(
            candidate_skus, signals_by_sku, competitors_by_sku, fee_config, decision_history_by_sku
        )

        def progress_hook(payload: dict, _rec: object) -> None:
            progress = RUN_PROGRESS.get(run_id)
            if not progress:
                return
            progress["current_sku_name"] = payload.get("sku_name")
            progress["skus_processed"] += 1

        recommendations = await run_parallel(
            [payload.model_dump() for payload in payloads],
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
            os.getenv("XAI_API_KEY"),
            progress_hook=progress_hook,
        )

        successful_recommendations = [rec for rec in recommendations if rec is not None]
        failed_count = len(recommendations) - len(successful_recommendations)
        if not successful_recommendations:
            raise RuntimeError("No live AI provider succeeded for any SKU")

        enriched_recommendations = []
        for sku, rec in zip(candidate_skus, recommendations):
            if rec is None:
                continue
            signals = signals_by_sku[sku["sku_id"]]
            enriched_recommendations.append(
                {
                    "id": f"rec-{uuid.uuid4().hex[:8]}",
                    "sku_id": sku["sku_id"],
                    "sku_name": sku["sku_name"],
                    "brand": sku["brand"],
                    "sub_category": sku["sub_category"],
                    "buy_box_state_6": signals["state_6"],
                    "doc_urgency": signals["doc_urgency"],
                    "revenue_at_risk_7d": signals["gmv_at_risk_7d"],
                    "working_capital_at_risk": sku["cost"] * sku["units_on_hand"],
                    "impact_score": signals["impact_score"],
                    **rec.model_dump(),
                }
            )

        clusters = await form_clusters(
            enriched_recommendations,
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("OPENAI_API_KEY"),
            os.getenv("XAI_API_KEY"),
        )
        impact_by_sku = {rec["sku_id"]: rec["impact_score"] for rec in enriched_recommendations}
        for cluster in clusters:
            cluster["impact_score"] = sum(impact_by_sku.get(sku_id, 0.0) for sku_id in cluster["sku_ids"])
        clusters.sort(key=lambda cluster: cluster.get("impact_score", 0.0), reverse=True)

        async with await get_db() as db:
            for rec in enriched_recommendations:
                await insert_recommendation(
                    db, run_id, {**rec, "status": "pending", "prompt_version": "v1.0"}
                )
            for display_order, cluster in enumerate(clusters, start=1):
                await insert_cluster(db, run_id, _cluster_record(cluster), display_order)
            await update_queue_run_complete(db, run_id, 0.0, "v1.0")
            await db.commit()

        RUN_PROGRESS[run_id]["status"] = "complete"
        RUN_PROGRESS[run_id]["current_sku_name"] = None
        if failed_count:
            RUN_PROGRESS[run_id]["warning"] = (
                f"{failed_count} SKU(s) failed live AI and were skipped. "
                "The rest completed normally."
            )
    except Exception as exc:
        async with await get_db() as db:
            await update_queue_run_failed(db, run_id)
            await db.commit()
        if run_id in RUN_PROGRESS:
            RUN_PROGRESS[run_id]["status"] = "failed"
            RUN_PROGRESS[run_id]["error"] = str(exc)


def _build_decision_history(
    candidate_skus: list[dict], recent: dict[str, list[dict]]
) -> dict[str, list[DecisionHistoryItem]]:
    decision_history_by_sku: dict[str, list[DecisionHistoryItem]] = {}
    for sku in candidate_skus:
        history_items = []
        for decision in recent.get(sku["sku_id"], []):
            to_price = decision.get("human_chosen_price") or decision.get("original_recommended_price")
            from_price = sku["current_price"]
            if to_price is None:
                to_price = from_price
            if to_price < from_price:
                action = "price_reduced"
            elif to_price > from_price:
                action = "price_raised"
            elif decision.get("decision") == "snoozed":
                action = "held"
            else:
                action = "held"
            history_items.append(
                DecisionHistoryItem(
                    date=decision["date"],
                    action=action,
                    from_price=from_price,
                    to_price=to_price,
                    outcome_velocity_delta=decision.get("outcome_velocity_delta"),
                    buy_box_recovered=decision.get("buy_box_recovered"),
                )
            )
        decision_history_by_sku[sku["sku_id"]] = history_items
    return decision_history_by_sku


def _cluster_record(cluster: dict) -> dict:
    return {
        "id": f"cluster-{uuid.uuid4().hex[:8]}",
        "cluster_name": cluster["cluster_name"],
        "root_cause": cluster["root_cause"],
        "action_type": cluster["action_type"],
        "sku_ids": cluster["sku_ids"],
        "sku_count": cluster["sku_count"],
        "combined_gmv_at_risk_inr": cluster["combined_gmv_at_risk_inr"],
        "combined_working_capital_inr": cluster["combined_working_capital_inr"],
        "headline": cluster["headline"],
        "impact_score": cluster.get("impact_score", 0.0),
    }
