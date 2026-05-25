'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSkuDetail, postDecision } from '../../lib/api';
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
  onDecisionApplied,
}: {
  skuId: string | null;
  open: boolean;
  onClose: () => void;
  onDecisionApplied?: () => void | Promise<void>;
}) {
  const [detail, setDetail] = useState<SkuDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [showOverride, setShowOverride] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !skuId) return;
    setLoading(true);
    setErrorMessage(null);
    getSkuDetail(skuId)
      .then((data) => setDetail(data))
      .catch((error) => {
        console.error('Failed to load SKU detail:', error);
        setErrorMessage('Unable to load this SKU right now. Please try again.');
      })
      .finally(() => setLoading(false));
  }, [open, skuId]);

  if (!open) return null;

  const recommendation = detail?.recommendation ?? null;

  return (
    <div className="fixed inset-0 z-30 flex">
      <div className="flex-1 bg-black/50" onClick={onClose} />
      <aside className="h-full w-full max-w-xl overflow-y-auto bg-bg-elevated p-4 text-text-primary shadow-soft lg:p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <Link href="/" onClick={onClose} className="rounded-md border border-bg-elevated px-3 py-2 text-xs font-semibold text-text-primary">
            Back to Queue
          </Link>
          <button type="button" onClick={onClose} className="text-xs text-text-muted">
            Close
          </button>
        </div>
        {loading && <div className="h-6 w-32 animate-pulse rounded bg-bg-card" />}
        {errorMessage && <div className="mb-4 rounded-lg border border-warning/40 bg-warning/10 p-3 text-sm text-warning">{errorMessage}</div>}
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
            disabled={submitting}
            onApprove={async () => {
              setSubmitting(true);
              setErrorMessage(null);
              try {
                await postDecision({
                  sku_id: recommendation.sku_id,
                  recommendation_id: recommendation.id,
                  decision: 'approved',
                });
                await onDecisionApplied?.();
                onClose();
              } catch (error: any) {
                console.error('Failed to approve recommendation:', error);
                setErrorMessage(error?.status === 409 ? 'This recommendation was already decided. Refreshing now.' : 'Approve failed. Please try again.');
                await onDecisionApplied?.();
              } finally {
                setSubmitting(false);
              }
            }}
            onSnooze={async (hours) => {
              setSubmitting(true);
              setErrorMessage(null);
              try {
                await postDecision({
                  sku_id: recommendation.sku_id,
                  recommendation_id: recommendation.id,
                  decision: 'snoozed',
                  snooze_duration_hours: hours,
                });
                await onDecisionApplied?.();
                onClose();
              } catch (error: any) {
                console.error('Failed to snooze recommendation:', error);
                setErrorMessage(error?.status === 409 ? 'This recommendation was already decided. Refreshing now.' : 'Snooze failed. Please try again.');
                await onDecisionApplied?.();
              } finally {
                setSubmitting(false);
              }
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
            setSubmitting(true);
            setErrorMessage(null);
            try {
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
              await onDecisionApplied?.();
              setShowOverride(false);
              onClose();
            } catch (error: any) {
              console.error('Failed to override recommendation:', error);
              setErrorMessage(error?.status === 409 ? 'This recommendation was already decided. Refreshing now.' : 'Override failed. Please try again.');
              await onDecisionApplied?.();
            } finally {
              setSubmitting(false);
            }
          }}
        />
      )}
    </div>
  );
}
