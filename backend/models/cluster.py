from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel


class ActionCluster(BaseModel):
    id: str
    run_id: str
    cluster_name: str
    root_cause: str
    action_type: Literal["reduce_price", "hold_price", "escalate_to_human"]
    sku_ids: List[str]
    sku_count: int
    combined_gmv_at_risk_inr: float
    combined_working_capital_inr: float
    headline: str
    impact_score: float
    display_order: int
