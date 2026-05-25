from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class RecommendationFlag(str, Enum):
    AT_FLOOR = "at_floor"
    AT_MAP = "at_map"
    COMPETITOR_BELOW_FLOOR = "competitor_below_floor"
    MAP_VIOLATION_DETECTED = "map_violation_detected"
    BUY_BOX_AT_RISK = "buy_box_at_risk"
    NO_COMPETITOR_DATA = "no_competitor_data"
    DATA_QUALITY_STALE_COMPETITOR_PRICE = "data_quality_stale_competitor_price"
    ZERO_VELOCITY_30D = "zero_velocity_30d"
    MARGIN_SQUEEZE_CRITICAL = "margin_squeeze_critical"
    FESTIVAL_SEASON_ACTIVE = "festival_season_active"
    GREY_MARKET_LIKELY_CLEARING = "grey_market_likely_clearing"
    DECISION_HISTORY_INEFFECTIVE = "decision_history_ineffective"
    PHANTOM_STOCKOUT_IMMINENT = "phantom_stockout_imminent"
    REORDER_TRIGGER = "reorder_trigger"
    BUSINESS_RULE_VIOLATION_DETECTED = "business_rule_violation_detected"


class AiRecommendation(BaseModel):
    recommended_price: float = Field(gt=0)
    action_type: Literal["reduce_price", "raise_price", "hold_price", "escalate_to_human"]
    confidence: Literal["high", "medium", "low"]
    margin_floor: float = Field(gt=0)
    margin_at_recommended_price: float
    margin_pct_at_recommended_price: float
    competitor_classification: Literal["grey_market", "authorized", "unknown", "none"]
    temporal_persistence: Literal["short_cycle", "medium_cycle", "structural", "unknown", "none"]
    competitor_price_gap: float
    revenue_at_risk_7d: float = Field(ge=0)
    days_to_stockout_current: Optional[int] = None
    days_to_stockout_recommended: Optional[int] = None
    projected_velocity_change: Literal[
        "significant_increase", "moderate_increase", "minimal_change", "decrease", "unknown"
    ]
    reasoning: str = Field(min_length=10, max_length=300)
    flags: List[str]
    model_used: Optional[str] = None
    source: Optional[Literal["ai_claude_sonnet", "ai_gpt4o_fallback", "ai_grok_fallback", "rule_engine_fallback"]] = None
    generated_at: Optional[str] = None
