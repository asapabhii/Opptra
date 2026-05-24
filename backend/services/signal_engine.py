from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_SKUS: list[dict] = []
_SKUS_BY_ID: dict[str, dict] = {}
_COMPETITORS_BY_SKU: dict[str, dict] = {}
_BRAND_AUTH: list[dict] = []
_FEE_CONFIG: dict[str, Any] = {}


class BuyBoxState6(str, Enum):
    WINNING_CLEANLY = "winning_cleanly"
    WINNING_AT_RISK = "winning_at_risk"
    LOSING_NARROWLY = "losing_narrowly"
    LOSING_SUBSTANTIALLY = "losing_substantially"
    SUPPRESSED = "suppressed"
    NOT_ELIGIBLE = "not_eligible"


class BuyBoxState3(str, Enum):
    WON = "won"
    LOST = "lost"
    NO_BUY_BOX = "no_buy_box"


def load_data_stores() -> None:
    global _SKUS, _SKUS_BY_ID, _COMPETITORS_BY_SKU, _BRAND_AUTH, _FEE_CONFIG

    _SKUS = json.loads((DATA_DIR / "skus.json").read_text(encoding="utf-8"))
    _SKUS_BY_ID = {sku["sku_id"]: sku for sku in _SKUS}
    competitors = json.loads((DATA_DIR / "competitors.json").read_text(encoding="utf-8"))
    _COMPETITORS_BY_SKU = {entry["sku_id"]: entry for entry in competitors}
    _BRAND_AUTH = json.loads((DATA_DIR / "brand_authorization.json").read_text(encoding="utf-8"))
    _FEE_CONFIG = json.loads((DATA_DIR / "fee_config.json").read_text(encoding="utf-8"))


def get_skus() -> list[dict]:
    return _SKUS


def get_sku_by_id(sku_id: str) -> Optional[dict]:
    return _SKUS_BY_ID.get(sku_id)


def get_competitor_by_sku(sku_id: str) -> Optional[dict]:
    return _COMPETITORS_BY_SKU.get(sku_id)


def get_fee_config() -> dict:
    return _FEE_CONFIG


def get_fba_fee(weight_kg: float, fee_config: dict) -> float:
    for tier in fee_config["fba_fee_tiers_inr"]:
        if weight_kg <= tier["max_weight_kg"]:
            return tier["fee"]
    return fee_config["fba_fee_tiers_inr"][-1]["fee"]


def compute_storage_accrual(doc_current: float, units_on_hand: int, fee_config: dict) -> float:
    threshold = fee_config["storage_accrual_threshold_days"]
    if doc_current <= threshold:
        return 0.0
    months_over = (doc_current - threshold) / 30.0
    return fee_config["storage_cost_per_unit_per_month_inr"] * months_over


def compute_margin_floor(
    cost: float,
    sub_category: str,
    weight_kg: float,
    doc_current: float,
    units_on_hand: int,
    target_margin_pct: float,
    fee_config: dict,
) -> float:
    marketplace_fee = cost * fee_config["marketplace_fees_pct"]["amazon_india"][sub_category]
    fba_fee = get_fba_fee(weight_kg, fee_config)
    returns_provision = cost * fee_config["returns_provision_pct"][sub_category]
    storage_accrual = compute_storage_accrual(doc_current, units_on_hand, fee_config)
    target_margin = cost * target_margin_pct
    return cost + marketplace_fee + fba_fee + returns_provision + storage_accrual + target_margin


def compute_doc(
    units_on_hand: int,
    velocity_7d: float,
    velocity_30d: float,
    velocity_trend: str,
) -> float:
    if velocity_trend == "accelerating" and velocity_7d > 0:
        velocity = velocity_7d
    elif velocity_30d > 0:
        velocity = velocity_30d
    elif velocity_7d > 0:
        velocity = velocity_7d
    else:
        return 999.0
    return units_on_hand / velocity


def classify_doc_urgency(doc: float) -> str:
    if doc >= 90:
        return "critical"
    if doc >= 60:
        return "high"
    if doc >= 30:
        return "moderate"
    return "low"


def classify_buy_box(
    sku_current_price: float,
    competitor_data: Optional[dict],
    account_health_issue: bool = False,
    fair_pricing_violation: bool = False,
) -> Tuple[BuyBoxState6, BuyBoxState3, dict]:
    extra_context: dict = {}
    if account_health_issue:
        return BuyBoxState6.NOT_ELIGIBLE, BuyBoxState3.NO_BUY_BOX, {
            "suppression_reason": "account_health"
        }
    if fair_pricing_violation:
        return BuyBoxState6.SUPPRESSED, BuyBoxState3.NO_BUY_BOX, {
            "suppression_reason": "fair_pricing_policy"
        }
    if competitor_data is None:
        return BuyBoxState6.WINNING_CLEANLY, BuyBoxState3.WON, {}

    buy_box_winner = competitor_data.get("buy_box_winner")
    nearest_price = competitor_data.get("nearest_competitor_price")
    nearest_gap = competitor_data.get("nearest_competitor_gap_pct")

    if buy_box_winner is None:
        if nearest_price is not None and nearest_gap is not None:
            abs_gap = abs(nearest_gap)
            if abs_gap <= 0.05:
                extra_context["buy_box_at_risk"] = True
                extra_context["nearest_competitor_gap_pct"] = nearest_gap
                extra_context["nearest_competitor_price"] = nearest_price
                return BuyBoxState6.WINNING_AT_RISK, BuyBoxState3.WON, extra_context
        return BuyBoxState6.WINNING_CLEANLY, BuyBoxState3.WON, {}

    gap_inr = sku_current_price - buy_box_winner["price"]
    gap_pct = gap_inr / sku_current_price
    extra_context["price_gap_inr"] = gap_inr
    extra_context["price_gap_pct"] = gap_pct

    if gap_pct <= 0.08:
        return BuyBoxState6.LOSING_NARROWLY, BuyBoxState3.LOST, extra_context
    return BuyBoxState6.LOSING_SUBSTANTIALLY, BuyBoxState3.LOST, extra_context


def compute_gmv_at_risk_7d(
    units_on_hand: int,
    daily_velocity_30d: float,
    competitor_price: Optional[float],
) -> float:
    if competitor_price is None:
        return 0.0
    daily_lost_revenue = daily_velocity_30d * competitor_price
    return daily_lost_revenue * 7


def compute_impact_score(revenue_at_risk_7d: float, doc_current: float, price_gap_pct: float) -> float:
    doc_urgency_normalized = min(doc_current / 180.0, 1.0)
    return (revenue_at_risk_7d * 0.4) + (doc_urgency_normalized * 0.3) + (price_gap_pct * 0.3)


def compute_all_signals(sku: dict, competitor_data: Optional[dict], fee_config: dict) -> dict:
    doc_current = compute_doc(
        sku["units_on_hand"],
        sku["daily_velocity_7d"],
        sku["daily_velocity_30d"],
        sku["velocity_trend"],
    )
    doc_urgency = classify_doc_urgency(doc_current)
    storage_accrual = compute_storage_accrual(doc_current, sku["units_on_hand"], fee_config)
    margin_floor = compute_margin_floor(
        sku["cost"],
        sku["sub_category"],
        sku["weight_kg"],
        doc_current,
        sku["units_on_hand"],
        sku["target_margin_pct"],
        fee_config,
    )
    state_6, state_3, extra = classify_buy_box(sku["current_price"], competitor_data)

    buy_box_winner = None
    competitor_price = None
    if competitor_data:
        buy_box_winner = competitor_data.get("buy_box_winner")
        if buy_box_winner is not None:
            competitor_price = buy_box_winner.get("price")
        else:
            competitor_price = competitor_data.get("nearest_competitor_price")

    gmv_at_risk = compute_gmv_at_risk_7d(
        sku["units_on_hand"], sku["daily_velocity_30d"], competitor_price
    )

    price_gap_pct = extra.get("price_gap_pct")
    if price_gap_pct is None:
        price_gap_pct = extra.get("nearest_competitor_gap_pct", 0.0)
    impact_score = compute_impact_score(gmv_at_risk, doc_current, abs(price_gap_pct))

    return {
        "sku_id": sku["sku_id"],
        "state_6": state_6.value,
        "state_3": state_3.value,
        "doc_current": doc_current,
        "doc_urgency": doc_urgency,
        "margin_floor": margin_floor,
        "storage_accrual_per_unit": storage_accrual,
        "gmv_at_risk_7d": gmv_at_risk,
        "impact_score": impact_score,
        "competitor": buy_box_winner,
        "price_gap_inr": extra.get("price_gap_inr", 0.0),
        "price_gap_pct": extra.get("price_gap_pct", 0.0),
        "buy_box_at_risk": extra.get("buy_box_at_risk", False),
        "nearest_competitor_price": extra.get("nearest_competitor_price"),
        "nearest_competitor_gap_pct": extra.get("nearest_competitor_gap_pct"),
    }


def compute_portfolio_summary(skus: list, competitors: dict, fee_config: dict) -> dict:
    all_signals = {
        sku["sku_id"]: compute_all_signals(sku, competitors.get(sku["sku_id"]), fee_config)
        for sku in skus
    }
    bb_lost = [s for s in all_signals.values() if s["state_6"] in ("losing_narrowly", "losing_substantially")]
    bb_at_risk = [s for s in all_signals.values() if s["state_6"] == "winning_at_risk"]
    phantom_stockout = [s for s in all_signals.values() if s["doc_current"] < 8]
    high_doc = [s for s in all_signals.values() if s["doc_current"] > 90]
    gmv_at_risk = sum(s["gmv_at_risk_7d"] for s in bb_lost)

    skus_by_id = {sku["sku_id"]: sku for sku in skus}
    working_capital_at_risk = sum(
        skus_by_id[s["sku_id"]]["cost"] * skus_by_id[s["sku_id"]]["units_on_hand"]
        for s in high_doc
    )
    most_urgent = max(all_signals.values(), key=lambda s: s["impact_score"])
    most_urgent_sku = skus_by_id[most_urgent["sku_id"]]
    most_urgent_action, most_urgent_reason = _derive_most_urgent_action(
        most_urgent_sku, most_urgent, competitors.get(most_urgent["sku_id"])
    )

    critical_alerts = []
    if phantom_stockout:
        critical_alerts.append(
            f"{len(phantom_stockout)} SKUs have fewer than 8 days of stock at current velocity"
        )
    high_doc_120 = [s for s in all_signals.values() if s["doc_current"] > 120]
    if high_doc_120:
        critical_alerts.append(
            f"{len(high_doc_120)} SKUs have DOC exceeding 120 days - storage accrual is raising margin floors"
        )

    previous_lost = [
        sku for sku in skus if sku["previous_buy_box_state"] in ("losing_narrowly", "losing_substantially")
    ]
    previous_gmv_at_risk = sum(
        all_signals[sku["sku_id"]]["gmv_at_risk_7d"] for sku in previous_lost
    )
    gmv_delta_pct = None
    if previous_gmv_at_risk:
        gmv_delta_pct = (gmv_at_risk - previous_gmv_at_risk) / previous_gmv_at_risk

    previous_working_capital = 0.0
    for sku in skus:
        doc_prev = max(all_signals[sku["sku_id"]]["doc_current"] - 7, 0)
        if doc_prev > 90:
            previous_working_capital += sku["cost"] * sku["units_on_hand"]
    working_capital_delta_pct = None
    if previous_working_capital:
        working_capital_delta_pct = (
            working_capital_at_risk - previous_working_capital
        ) / previous_working_capital

    return {
        "total_skus": len(skus),
        "buy_box_lost_count": len(bb_lost),
        "buy_box_lost_delta": len(bb_lost) - len(previous_lost),
        "buy_box_at_risk_count": len(bb_at_risk),
        "gmv_at_risk_7d_inr": round(gmv_at_risk),
        "gmv_at_risk_delta_pct": gmv_delta_pct,
        "working_capital_at_risk_inr": round(working_capital_at_risk),
        "working_capital_delta_pct": working_capital_delta_pct,
        "phantom_stockout_risk_count": len(phantom_stockout),
        "most_urgent_sku_id": most_urgent["sku_id"],
        "most_urgent_sku_name": most_urgent_sku["sku_name"],
        "most_urgent_action": most_urgent_action,
        "most_urgent_reason": most_urgent_reason,
        "narrative": build_narrative(bb_lost, gmv_at_risk),
        "critical_alerts": critical_alerts,
        "signals": all_signals,
    }


def _derive_most_urgent_action(sku: dict, signals: dict, competitor_data: Optional[dict]) -> tuple[str, str]:
    margin_floor = signals["margin_floor"]
    competitor_price = None
    if competitor_data and competitor_data.get("buy_box_winner"):
        competitor_price = competitor_data["buy_box_winner"].get("price")

    if competitor_price is not None and competitor_price < margin_floor:
        return "escalate_to_human", "Competitor below margin floor - cannot reprice without destroying margin"
    if sku.get("map_enforced") and sku.get("map_price") and competitor_price is not None:
        if competitor_price < sku["map_price"]:
            return "escalate_to_human", "Competitor below MAP - brand policy violation"
    if signals["state_6"] in ("losing_narrowly", "losing_substantially"):
        return "reduce_price", "Buy Box lost - price gap present"
    if signals["doc_current"] > 90:
        return "reduce_price", "Critical DOC - margin floor rising from storage accrual"
    return "hold_price", "No immediate pricing action required"


def build_narrative(bb_lost: list, gmv_at_risk: float) -> str:
    lakhs = gmv_at_risk / 100_000
    return (
        f"{len(bb_lost)} SKUs are actively losing Buy Box today. "
        f"{lakhs:.1f}L in GMV has flowed to competitors this week."
    )
