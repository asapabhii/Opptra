from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from api.dependencies import get_db
from db.queries import fetch_decisions, fetch_latest_run
from services.pattern_synthesis import synthesize_patterns
from services.signal_engine import (
    compute_portfolio_summary,
    get_competitor_by_sku,
    get_fee_config,
    get_skus,
    _derive_most_urgent_action,
)

router = APIRouter()


@router.get("/summary")
async def get_portfolio_summary():
    skus = get_skus()
    fee_config = get_fee_config()
    competitors = {sku["sku_id"]: get_competitor_by_sku(sku["sku_id"]) for sku in skus}
    summary = compute_portfolio_summary(skus, competitors, fee_config)
    items = []
    for sku in skus:
        signals = summary["signals"][sku["sku_id"]]
        action, reason = _derive_most_urgent_action(sku, signals, competitors.get(sku["sku_id"]))
        tags = ["all"]
        if signals["state_6"] in ("losing_narrowly", "losing_substantially"):
            tags.append("buy_box_lost")
        if signals["doc_current"] >= 60:
            tags.append("bloated_stale")
        if signals["doc_current"] < 8:
            tags.append("stockout_risk")
        if action == "escalate_to_human":
            tags.append("escalate")
        items.append(
            {
                "sku_id": sku["sku_id"],
                "sku_name": sku["sku_name"],
                "brand": sku["brand"],
                "buy_box_state_6": signals["state_6"],
                "doc_current": signals["doc_current"],
                "doc_urgency": signals["doc_urgency"],
                "gmv_at_risk_7d_inr": signals["gmv_at_risk_7d"],
                "working_capital_inr": sku["cost"] * sku["units_on_hand"],
                "impact_score": signals["impact_score"],
                "recommended_action": action,
                "recommended_reason": reason,
                "tags": tags,
            }
        )
    return {
        "total_skus": summary["total_skus"],
        "buy_box_lost_count": summary["buy_box_lost_count"],
        "buy_box_lost_delta": summary["buy_box_lost_delta"],
        "buy_box_at_risk_count": summary["buy_box_at_risk_count"],
        "gmv_at_risk_7d_inr": summary["gmv_at_risk_7d_inr"],
        "gmv_at_risk_delta_pct": summary["gmv_at_risk_delta_pct"],
        "working_capital_at_risk_inr": summary["working_capital_at_risk_inr"],
        "working_capital_delta_pct": summary["working_capital_delta_pct"],
        "phantom_stockout_risk_count": summary["phantom_stockout_risk_count"],
        "most_urgent_sku_id": summary["most_urgent_sku_id"],
        "most_urgent_sku_name": summary["most_urgent_sku_name"],
        "most_urgent_action": summary["most_urgent_action"],
        "most_urgent_reason": summary["most_urgent_reason"],
        "narrative": summary["narrative"],
        "critical_alerts": summary["critical_alerts"],
        "items": items,
    }


@router.post("/synthesis")
async def post_portfolio_synthesis():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Gemini service unavailable")

    async with await get_db() as db:
        decisions = await fetch_decisions(db, {"limit": 200, "offset": 0})

    try:
        report = synthesize_patterns(api_key, decisions["decisions"])
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Gemini service unavailable") from exc
    except ValueError as exc:
        # Ensure JSON extraction/parsing issues don't become a raw 500.
        raise HTTPException(
            status_code=502,
            detail=f"Portfolio synthesis failed to parse Gemini output: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Portfolio synthesis failed: {exc}",
        ) from exc

    report["id"] = f"syn-{uuid.uuid4().hex[:8]}"
    report["generated_at"] = datetime.now(timezone.utc).isoformat()
    return report
