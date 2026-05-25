'use client';

import { useState } from 'react';
import { Cluster, Recommendation } from '../../types';
import { postDecision } from '../../lib/api';
import SkuRow from './SkuRow';

interface ClusterCardProps {
  cluster: Cluster;
  recommendations: Recommendation[];
  onSkuClick: (skuId: string) => void;
  onDecisionApplied: () => void | Promise<void>;
}

export default function ClusterCard({
  cluster,
  recommendations,
  onSkuClick,
  onDecisionApplied,
}: ClusterCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApproveAll = async () => {
    setIsProcessing(true);
    try {
      const pendingRecs = recommendations.filter((rec) => rec.status === 'pending');
      const results = await Promise.allSettled(
        pendingRecs.map((rec) =>
          postDecision({
            recommendation_id: rec.id,
            sku_id: rec.sku_id,
            decision: 'approved',
          })
        )
      );

      const failed = results.filter((result) => result.status === 'rejected');
      if (failed.length > 0) {
        console.warn(`Approve all completed with ${failed.length} rejected updates.`);
      }
      await onDecisionApplied();
    } catch (error) {
      console.error('Failed to approve all:', error);
      alert('Failed to approve all recommendations. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSnoozeAll = async () => {
    setIsProcessing(true);
    try {
      const pendingRecs = recommendations.filter((rec) => rec.status === 'pending');
      const results = await Promise.allSettled(
        pendingRecs.map((rec) =>
          postDecision({
            recommendation_id: rec.id,
            sku_id: rec.sku_id,
            decision: 'snoozed',
            snooze_duration_hours: 24,
          })
        )
      );

      const failed = results.filter((result) => result.status === 'rejected');
      if (failed.length > 0) {
        console.warn(`Snooze all completed with ${failed.length} rejected updates.`);
      }
      await onDecisionApplied();
    } catch (error) {
      console.error('Failed to snooze all:', error);
      alert('Failed to snooze all recommendations. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="rounded-xl bg-bg-card p-4 shadow-soft lg:p-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-text-muted">{cluster.action_type}</div>
          <div className="text-lg font-semibold text-text-primary">{cluster.cluster_name}</div>
        </div>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="rounded-md border border-bg-elevated px-3 py-1 text-xs font-semibold text-accent-blue"
        >
          {expanded ? 'Hide SKUs' : 'Review SKUs'}
        </button>
      </div>
      <p className="mt-2 text-sm text-text-muted">{cluster.headline}</p>
      <div className="mt-4 grid gap-2 text-sm text-text-muted sm:grid-cols-3">
        <span>{cluster.sku_count} SKUs</span>
        <span>{cluster.combined_gmv_at_risk_inr.toFixed(0)} GMV at risk</span>
        <span>{cluster.combined_working_capital_inr.toFixed(0)} working capital</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        <button 
          type="button"
          className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white disabled:bg-bg-elevated disabled:text-text-muted"
          onClick={handleApproveAll}
          disabled={isProcessing || !recommendations.some(r => r.status === 'pending')}
        >
          {isProcessing ? 'Processing...' : 'Approve All'}
        </button>
        <button 
          type="button"
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Hide SKUs' : 'Review SKUs'}
        </button>
        <button 
          type="button"
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary disabled:bg-bg-elevated disabled:text-text-muted"
          onClick={handleSnoozeAll}
          disabled={isProcessing || !recommendations.some(r => r.status === 'pending')}
        >
          {isProcessing ? 'Processing...' : 'Snooze 24h'}
        </button>
      </div>
      {expanded && (
        <div className="mt-4 max-h-[28rem] space-y-2 overflow-y-auto pr-1">
          {recommendations.map((rec) => (
            <SkuRow 
              key={rec.id} 
              recommendation={rec} 
              onSkuClick={onSkuClick}
            />
          ))}
        </div>
      )}
    </div>
  );
}
