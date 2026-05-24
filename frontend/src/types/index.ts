export interface PortfolioSummary {
  total_skus: number;
  buy_box_lost_count: number;
  buy_box_lost_delta: number;
  buy_box_at_risk_count: number;
  gmv_at_risk_7d_inr: number;
  gmv_at_risk_delta_pct: number | null;
  working_capital_at_risk_inr: number;
  working_capital_delta_pct: number | null;
  phantom_stockout_risk_count: number;
  most_urgent_sku_id: string;
  most_urgent_sku_name: string;
  most_urgent_action: string;
  most_urgent_reason: string;
  narrative: string;
  critical_alerts: string[];
  items: PortfolioItem[];
}

export interface PortfolioItem {
  sku_id: string;
  sku_name: string;
  brand: string;
  buy_box_state_6: string;
  doc_current: number;
  doc_urgency: string;
  gmv_at_risk_7d_inr: number;
  working_capital_inr: number;
  impact_score: number;
  recommended_action: string;
  recommended_reason: string;
  tags: string[];
}

export interface QueueRun {
  id: string;
  triggered_at: string;
  status: string;
  sku_count: number;
  completed_at: string | null;
  cost_usd: number | null;
  prompt_version: string;
}

export interface Cluster {
  id: string;
  cluster_name: string;
  root_cause: string;
  action_type: string;
  sku_ids: string[];
  sku_count: number;
  combined_gmv_at_risk_inr: number;
  combined_working_capital_inr: number;
  headline: string;
  impact_score: number;
  display_order: number;
}

export interface Recommendation {
  id: string;
  sku_id: string;
  recommended_price: number;
  action_type: string;
  confidence: string;
  margin_floor: number;
  margin_at_recommended: number;
  margin_pct_at_recommended: number;
  competitor_classification: string;
  temporal_persistence: string;
  competitor_price_gap: number;
  revenue_at_risk_7d: number;
  days_to_stockout_current: number | null;
  days_to_stockout_recommended: number | null;
  projected_velocity_change: string;
  reasoning: string;
  flags: string[];
  model_used: string;
  source: string;
  prompt_version: string;
  generated_at: string;
  status: string;
}

export interface Decision {
  id: string;
  sku_id: string;
  sku_name?: string;
  brand?: string;
  decision: string;
  original_recommended_price: number;
  human_chosen_price: number | null;
  override_reason_category: string | null;
  override_insight: string | null;
  decided_at: string;
  buy_box_recovered: number | null;
  velocity_delta: number | null;
  outcome_note: string | null;
}

export interface SkuDetail {
  sku: {
    sku_id: string;
    sku_name: string;
    brand: string;
    sub_category: string;
    current_price: number;
    cost: number;
    units_on_hand: number;
    daily_velocity_30d: number;
    velocity_trend: string;
    map_price: number | null;
    map_enforced: boolean;
    festival_season: boolean;
  };
  signals: {
    buy_box_state_6: string;
    buy_box_state_3: string;
    doc_current: number;
    doc_urgency: string;
    margin_floor: number;
    storage_accrual_per_unit: number;
    gmv_at_risk_7d_inr: number;
    impact_score: number;
    competitor: any;
    competitor_price_age_hours: number | null;
    all_competitors: any[];
  };
  recommendation: Recommendation | null;
  decision_history: Decision[];
}
