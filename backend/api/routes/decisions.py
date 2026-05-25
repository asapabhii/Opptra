from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.dependencies import get_db
from db.queries import (
    fetch_decision_by_recommendation_id,
    fetch_decisions,
    fetch_recommendation_by_id,
    insert_decision,
    update_recommendation_status,
)
from db.init import reset_demo_state
from services.signal_engine import get_sku_by_id
from services.override_insights import extract_override_insight

router = APIRouter()


@router.get("")
async def get_decision_log(
    brand: str | None = None,
    decision_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sku_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    async with await get_db() as db:
        result = await fetch_decisions(
            db,
            {
                "brand": brand,
                "decision": decision_type,
                "date_from": date_from,
                "date_to": date_to,
                "sku_id": sku_id,
                "limit": limit,
                "offset": offset,
            },
        )

    enriched = []
    for decision in result["decisions"]:
        sku = get_sku_by_id(decision["sku_id"])
        if not sku:
            continue
        if brand and sku["brand"] != brand:
            continue
        decision["sku_name"] = sku["sku_name"]
        decision["brand"] = sku["brand"]
        enriched.append(decision)

    result["decisions"] = enriched
    result["total_count"] = len(enriched)
    return result


@router.post("/reset-demo")
async def reset_demo():
    await reset_demo_state()
    return {"status": "ok", "message": "Demo state reset to seeded decisions."}


@router.post("")
async def post_decision(payload: dict, background_tasks: BackgroundTasks):
    required = {"sku_id", "recommendation_id", "decision"}
    if not required.issubset(payload.keys()):
        raise HTTPException(status_code=422, detail="Missing required fields")

    if payload["decision"] == "overridden" and not payload.get("human_chosen_price"):
        raise HTTPException(status_code=422, detail="human_chosen_price is required when decision is overridden")

    if payload["decision"] == "snoozed" and not payload.get("snooze_duration_hours"):
        raise HTTPException(status_code=422, detail="snooze_duration_hours is required when decision is snoozed")

    if payload["decision"] == "overridden" and not payload.get("override_reason_category"):
        raise HTTPException(status_code=422, detail="override_reason_category is required when decision is overridden")

    async with await get_db() as db:
        recommendation = await fetch_recommendation_by_id(db, payload["recommendation_id"])
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        if recommendation["status"] != "pending":
            existing = await fetch_decision_by_recommendation_id(db, payload["recommendation_id"])
            if existing and existing["decision"] == payload["decision"]:
                return existing
            raise HTTPException(status_code=409, detail="Recommendation already decided")

    snooze_duration = payload.get("snooze_duration_hours")
    resurfaced_at = None
    if payload["decision"] == "snoozed" and snooze_duration:
        resurfaced_at = (datetime.now(timezone.utc) + timedelta(hours=snooze_duration)).isoformat()

    decision = {
        "id": f"d-{uuid.uuid4().hex[:8]}",
        "sku_id": payload["sku_id"],
        "recommendation_id": payload["recommendation_id"],
        "decision": payload["decision"],
        "original_recommended_price": recommendation["recommended_price"],
        "human_chosen_price": payload.get("human_chosen_price"),
        "snooze_duration_hours": snooze_duration,
        "override_reason_category": payload.get("override_reason_category"),
        "override_reason_free_text": payload.get("override_reason_free_text"),
        "override_insight": None,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "resurfaced_at": resurfaced_at,
        "outcome_check_due_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "buy_box_recovered": None,
        "velocity_delta": None,
        "outcome_note": None,
    }

    async with await get_db() as db:
        await insert_decision(db, decision)
        await update_recommendation_status(db, payload["recommendation_id"], payload["decision"])
        await db.commit()

    if decision["decision"] == "overridden":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            payload_for_ai = {
                "sku_context_summary": payload.get("sku_context_summary", ""),
                "ai_recommendation_summary": payload.get("ai_recommendation_summary", ""),
                "human_override_price": payload.get("human_chosen_price"),
                "human_override_reason": payload.get("override_reason_free_text", ""),
            }
            background_tasks.add_task(_attach_override_insight, decision["id"], payload_for_ai, api_key)

    return decision


async def _attach_override_insight(decision_id: str, ai_payload: dict, api_key: str) -> None:
    insight = await extract_override_insight(api_key, ai_payload)
    async with await get_db() as db:
        await db.execute(
            "UPDATE decisions SET override_insight = ? WHERE id = ?",
            (json.dumps(insight), decision_id),
        )
        await db.commit()
