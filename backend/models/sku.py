from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


class BuyBoxWinner(BaseModel):
    seller_name: str
    seller_id: Optional[str] = None
    price: float
    listing_age_days: Optional[int] = None
    fulfillment_type: Literal["FBA", "FBF", "seller_fulfilled", "unknown"]
    seller_type_hint: Literal["grey_market", "authorized", "unknown"]


class CompetitorEntry(BaseModel):
    seller_name: str
    price: float
    fulfillment_type: Literal["FBA", "FBF", "seller_fulfilled", "unknown"]


class DecisionHistoryItem(BaseModel):
    date: str
    action: Literal["price_reduced", "price_raised", "held", "escalated"]
    from_price: float
    to_price: float
    outcome_velocity_delta: Optional[float] = None
    buy_box_recovered: Optional[bool] = None


class SkuRecord(BaseModel):
    sku_id: str
    sku_name: str
    brand: str
    sub_category: str
    current_price: float
    cost: float
    weight_kg: float
    target_margin_pct: float
    map_price: Optional[float] = None
    map_enforced: bool
    units_on_hand: int
    daily_velocity_7d: float
    daily_velocity_30d: float
    daily_velocity_90d: float
    velocity_trend: Literal["accelerating", "stable", "decelerating", "unknown"]
    doc_current: float
    seasonality_index: float
    festival_season: bool
    brand_notes: Optional[str] = None
    previous_buy_box_state: str


class SkuContextPayload(BaseModel):
    sku_id: str
    sku_name: str
    brand: str
    marketplace: Literal["amazon_india"]
    sub_category: str
    current_price: float
    cost: float
    marketplace_fee_pct: float
    fba_fee_inr: float
    returns_provision_pct: float
    storage_accrual_inr: float
    target_margin_pct: float
    computed_margin_floor: float
    map_price: Optional[float] = None
    map_enforced: bool
    buy_box_status: Literal["won", "lost", "no_buy_box"]
    buy_box_suppression_reason: Optional[str] = None
    buy_box_at_risk: bool
    buy_box_winner: Optional[BuyBoxWinner] = None
    price_gap_inr: float
    price_gap_pct: float
    units_on_hand: int
    daily_velocity_7d: float
    daily_velocity_30d: float
    daily_velocity_90d: float
    velocity_trend: Literal["accelerating", "stable", "decelerating", "unknown"]
    doc_current: float
    doc_urgency: Literal["critical", "high", "moderate", "low"]
    competitor_count: int
    all_competitor_prices: List[float]
    competitor_price_age_hours: Optional[float] = None
    competitor_price_stale: bool
    decision_history: List[DecisionHistoryItem]
    festival_season: bool
    brand_notes: Optional[str] = None
