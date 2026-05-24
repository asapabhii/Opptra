from __future__ import annotations

from typing import Any, Dict, List

from models.sku import BuyBoxWinner, DecisionHistoryItem, SkuContextPayload
from services.signal_engine import (
    classify_doc_urgency,
    compute_margin_floor,
    compute_storage_accrual,
    get_fba_fee,
)


def build_payload(
    sku: dict,
    signals: dict,
    competitor_data: dict | None,
    fee_config: dict,
    decision_history: List[DecisionHistoryItem],
) -> SkuContextPayload:
    marketplace_fee_pct = fee_config["marketplace_fees_pct"]["amazon_india"][sku["sub_category"]]
    fba_fee = get_fba_fee(sku["weight_kg"], fee_config)
    returns_provision = fee_config["returns_provision_pct"][sku["sub_category"]]
    storage_accrual = compute_storage_accrual(signals["doc_current"], sku["units_on_hand"], fee_config)
    computed_margin_floor = compute_margin_floor(
        sku["cost"],
        sku["sub_category"],
        sku["weight_kg"],
        signals["doc_current"],
        sku["units_on_hand"],
        sku["target_margin_pct"],
        fee_config,
    )

    buy_box_winner = None
    competitor_count = 0
    all_competitor_prices: List[float] = []
    competitor_price_age_hours = None
    competitor_price_stale = False

    if competitor_data:
        competitor_count = len(competitor_data.get("all_competitors", []))
        all_competitor_prices = [c["price"] for c in competitor_data.get("all_competitors", [])]
        competitor_price_age_hours = competitor_data.get("competitor_price_age_hours")
        if competitor_price_age_hours is not None:
            competitor_price_stale = competitor_price_age_hours > 6
        if competitor_data.get("buy_box_winner"):
            buy_box_winner = BuyBoxWinner(**competitor_data["buy_box_winner"])

    doc_urgency = classify_doc_urgency(signals["doc_current"])

    return SkuContextPayload(
        sku_id=sku["sku_id"],
        sku_name=sku["sku_name"],
        brand=sku["brand"],
        marketplace="amazon_india",
        sub_category=sku["sub_category"],
        current_price=sku["current_price"],
        cost=sku["cost"],
        marketplace_fee_pct=marketplace_fee_pct,
        fba_fee_inr=fba_fee,
        returns_provision_pct=returns_provision,
        storage_accrual_inr=storage_accrual,
        target_margin_pct=sku["target_margin_pct"],
        computed_margin_floor=computed_margin_floor,
        map_price=sku.get("map_price"),
        map_enforced=sku["map_enforced"],
        buy_box_status=signals["state_3"],
        buy_box_suppression_reason=None,
        buy_box_at_risk=signals.get("buy_box_at_risk", False),
        buy_box_winner=buy_box_winner,
        price_gap_inr=signals.get("price_gap_inr", 0.0),
        price_gap_pct=signals.get("price_gap_pct", 0.0),
        units_on_hand=sku["units_on_hand"],
        daily_velocity_7d=sku["daily_velocity_7d"],
        daily_velocity_30d=sku["daily_velocity_30d"],
        daily_velocity_90d=sku["daily_velocity_90d"],
        velocity_trend=sku["velocity_trend"],
        doc_current=signals["doc_current"],
        doc_urgency=doc_urgency,
        competitor_count=competitor_count,
        all_competitor_prices=all_competitor_prices,
        competitor_price_age_hours=competitor_price_age_hours,
        competitor_price_stale=competitor_price_stale,
        decision_history=decision_history,
        festival_season=sku["festival_season"],
        brand_notes=sku.get("brand_notes"),
    )


def build_payloads(
    skus: List[dict],
    signals_by_sku: Dict[str, dict],
    competitors_by_sku: Dict[str, dict],
    fee_config: dict,
    decision_history_by_sku: Dict[str, List[DecisionHistoryItem]],
) -> List[SkuContextPayload]:
    payloads: List[SkuContextPayload] = []
    for sku in skus:
        payloads.append(
            build_payload(
                sku,
                signals_by_sku[sku["sku_id"]],
                competitors_by_sku.get(sku["sku_id"]),
                fee_config,
                decision_history_by_sku.get(sku["sku_id"], []),
            )
        )
    return payloads
