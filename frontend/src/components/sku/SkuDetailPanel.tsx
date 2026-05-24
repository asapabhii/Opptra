'use client';

import { useEffect, useState } from 'react';
import { getSkuDetail, postDecision } from '../../lib/api';
import { formatInr, formatPercent } from '../../lib/formatters';
import { SkuDetail } from '../../types';
import StatePanel from './StatePanel';
import CompetitorPanel from './CompetitorPanel';
import SellerMetricsPanel from './SellerMetricsPanel';
import RecommendationPanel from './RecommendationPanel';
import ReasoningPanel from './ReasoningPanel';
import NoActionPanel from './NoActionPanel';
import DecisionBar from './DecisionBar';
import OverrideModal from '../modals/OverrideModal';

export default function SkuDetailPanel({
  skuId,
  open,
  onClose,
}: {
  skuId: string | null;
  open: boolean;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<SkuDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [showOverride, setShowOverride] = useState(false);

  useEffect(() => {
    if (!open || !skuId) return;
    setLoading(true);
    getSkuDetail(skuId)
      .then((data) => setDetail(data))
      .finally(() => setLoading(false));
  }, [open, skuId]);

  if (!open) return null;

  const recommendation = detail?.recommendation ?? null;

  return (
    <div className="fixed inset-0 z-30 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />
      <aside className="h-full w-full max-w-xl overflow-y-auto bg-bg-elevated p-6 text-text-primary shadow-soft">
        <button onClick={onClose} className="mb-4 text-xs text-text-muted">Close</button>
        {loading && <div className="h-6 w-32 animate-pulse rounded bg-bg-card" />}
        {!loading && detail && (
          <div className="space-y-5">
            <StatePanel detail={detail} />
            <CompetitorPanel detail={detail} />
            <SellerMetricsPanel detail={detail} />
            <RecommendationPanel detail={detail} />
            <ReasoningPanel detail={detail} />
            <NoActionPanel detail={detail} />
          </div>
        )}
        {recommendation && (
          <DecisionBar
            recommendation={recommendation}
            onApprove={async () => {
              await postDecision({
                sku_id: recommendation.sku_id,
                recommendation_id: recommendation.id,
                decision: 'approved',
              });
            }}
            onSnooze={async (hours) => {
              await postDecision({
                sku_id: recommendation.sku_id,
                recommendation_id: recommendation.id,
                decision: 'snoozed',
                snooze_duration_hours: hours,
              });
            }}
            onOverride={() => setShowOverride(true)}
          />
        )}
      </aside>
      {showOverride && recommendation && detail && (
        <OverrideModal
          detail={detail}
          recommendation={recommendation}
          onClose={() => setShowOverride(false)}
          onSubmit={async (payload) => {
            await postDecision({
              sku_id: recommendation.sku_id,
              recommendation_id: recommendation.id,
              decision: 'overridden',
              human_chosen_price: payload.human_price,
              override_reason_category: payload.reason_category,
              override_reason_free_text: payload.notes,
              sku_context_summary: `${detail.sku.sku_name} DOC ${detail.signals.doc_current.toFixed(0)} days`,
              ai_recommendation_summary: recommendation.reasoning,
            });
            setShowOverride(false);
          }}
        />
      )}
    </div>
  );
}
