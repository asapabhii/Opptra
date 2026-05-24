from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from models.recommendation import AiRecommendation


def build_fallback_recommendation(payload: dict) -> AiRecommendation:
    computed_floor = payload["computed_margin_floor"]
    map_price = payload.get("map_price") if payload.get("map_enforced") else None
    recommended_price = max(computed_floor, map_price or 0)

    action_type = "reduce_price" if payload["current_price"] > recommended_price else "hold_price"
    competitor = payload.get("buy_box_winner")
    competitor_price = competitor.get("price") if competitor else None
    competitor_classification = "none"
    if competitor:
        competitor_classification = competitor.get("seller_type_hint", "unknown")

    margin_at_recommended = recommended_price - computed_floor
    margin_pct = margin_at_recommended / recommended_price if recommended_price else 0.0

    revenue_at_risk = 0.0
    if payload.get("buy_box_status") == "lost" and competitor_price is not None:
        revenue_at_risk = payload["daily_velocity_30d"] * competitor_price * 7

    days_to_stockout_current = None
    if payload["daily_velocity_30d"] > 0:
        days_to_stockout_current = int(payload["units_on_hand"] / payload["daily_velocity_30d"])

    flags = []
    if competitor is None:
        flags.append("no_competitor_data")

    return AiRecommendation(
        recommended_price=recommended_price,
        action_type=action_type,
        confidence="low",
        margin_floor=computed_floor,
        margin_at_recommended_price=margin_at_recommended,
        margin_pct_at_recommended_price=margin_pct,
        competitor_classification=competitor_classification,
        temporal_persistence="none" if competitor is None else "unknown",
        competitor_price_gap=(recommended_price - competitor_price) if competitor_price else 0.0,
        revenue_at_risk_7d=revenue_at_risk,
        days_to_stockout_current=days_to_stockout_current,
        days_to_stockout_recommended=days_to_stockout_current,
        projected_velocity_change="unknown",
        reasoning="Automated fallback - AI service unavailable. Verify manually before acting.",
        flags=flags,
        model_used="rule_engine_fallback",
        source="rule_engine_fallback",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
