from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.dependencies import get_db
from db.queries import fetch_decisions, fetch_latest_run, fetch_recommendations_for_run
from services.signal_engine import get_competitor_by_sku, get_fee_config, get_sku_by_id, compute_all_signals

router = APIRouter()


@router.get("/{sku_id}")
async def get_sku_detail(sku_id: str):
    sku = get_sku_by_id(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    fee_config = get_fee_config()
    competitor = get_competitor_by_sku(sku_id)
    signals = compute_all_signals(sku, competitor, fee_config)

    recommendation = None
    decision_history = []
    async with await get_db() as db:
        run = await fetch_latest_run(db)
        if run:
            recs = await fetch_recommendations_for_run(db, run["id"])
            recommendation = next((r for r in recs if r["sku_id"] == sku_id), None)
        decisions = await fetch_decisions(db, {"sku_id": sku_id, "limit": 20, "offset": 0})
        decision_history = decisions["decisions"]

    return {
        "sku": {
            "sku_id": sku["sku_id"],
            "sku_name": sku["sku_name"],
            "brand": sku["brand"],
            "sub_category": sku["sub_category"],
            "current_price": sku["current_price"],
            "cost": sku["cost"],
            "units_on_hand": sku["units_on_hand"],
            "daily_velocity_30d": sku["daily_velocity_30d"],
            "velocity_trend": sku["velocity_trend"],
            "map_price": sku.get("map_price"),
            "map_enforced": sku["map_enforced"],
            "festival_season": sku["festival_season"],
        },
        "signals": {
            "buy_box_state_6": signals["state_6"],
            "buy_box_state_3": signals["state_3"],
            "doc_current": signals["doc_current"],
            "doc_urgency": signals["doc_urgency"],
            "margin_floor": signals["margin_floor"],
            "storage_accrual_per_unit": signals["storage_accrual_per_unit"],
            "gmv_at_risk_7d_inr": signals["gmv_at_risk_7d"],
            "impact_score": signals["impact_score"],
            "competitor": signals["competitor"],
            "competitor_price_age_hours": competitor.get("competitor_price_age_hours") if competitor else None,
            "all_competitors": competitor.get("all_competitors") if competitor else [],
        },
        "recommendation": recommendation,
        "decision_history": decision_history,
    }
