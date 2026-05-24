from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class OverrideInsight(BaseModel):
    override_category: str
    missing_context_type: Optional[str] = None
    insight: str
    data_fix_possible: bool
    prompt_fix_needed: bool


class Decision(BaseModel):
    id: str
    sku_id: str
    recommendation_id: str
    decision: Literal["approved", "overridden", "snoozed"]
    original_recommended_price: float
    human_chosen_price: Optional[float] = None
    snooze_duration_hours: Optional[int] = None
    override_reason_category: Optional[str] = None
    override_reason_free_text: Optional[str] = None
    override_insight: Optional[str] = None
    decided_at: str
    resurfaced_at: Optional[str] = None
    outcome_check_due_at: Optional[str] = None
    buy_box_recovered: Optional[int] = None
    velocity_delta: Optional[float] = None
    outcome_note: Optional[str] = None
