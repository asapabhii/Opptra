'use client';

import { useState } from 'react';
import { Cluster, Recommendation } from '../../types';
import { postDecision } from '../../lib/api';
import SkuRow from './SkuRow';

interface ClusterCardProps {
  cluster: Cluster;
  recommendations: Recommendation[];
  onSkuClick: (skuId: string) => void;
}

export default function ClusterCard({
  cluster,
  recommendations,
  onSkuClick,
}: ClusterCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApproveAll = async () => {
    setIsProcessing(true);
    try {
      // Approve each pending recommendation in the cluster
      const pendingRecs = recommendations.filter(rec => rec.status === 'pending');
      
      await Promise.all(
        pendingRecs.map(rec =>
          postDecision({
            recommendation_id: rec.id,
            sku_id: rec.sku_id,
            decision: 'approved',
          })
        )
      );

      // Refresh the page to show updated statuses
      window.location.reload();
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
      // Snooze each pending recommendation for 24 hours
      const pendingRecs = recommendations.filter(rec => rec.status === 'pending');
      
      await Promise.all(
        pendingRecs.map(rec =>
          postDecision({
            recommendation_id: rec.id,
            sku_id: rec.sku_id,
            decision: 'snoozed',
            snooze_duration_hours: 24,
          })
        )
      );

      // Refresh the page to show updated statuses
      window.location.reload();
    } catch (error) {
      console.error('Failed to snooze all:', error);
      alert('Failed to snooze all recommendations. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="rounded-xl bg-bg-card p-5 shadow-soft">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-text-muted">{cluster.action_type}</div>
          <div className="text-lg font-semibold text-text-primary">{cluster.cluster_name}</div>
        </div>
        <button
          onClick={() => setExpanded((prev) => !prev)}
          className="text-sm text-accent-blue"
        >
          {expanded ? 'Hide SKUs' : 'Review SKUs'}
        </button>
      </div>
      <p className="mt-2 text-sm text-text-muted">{cluster.headline}</p>
      <div className="mt-4 flex gap-6 text-sm text-text-muted">
        <span>{cluster.sku_count} SKUs</span>
        <span>{cluster.combined_gmv_at_risk_inr.toFixed(0)} GMV at risk</span>
        <span>{cluster.combined_working_capital_inr.toFixed(0)} working capital</span>
      </div>
      <div className="mt-4 flex gap-3">
        <button 
          className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white disabled:bg-bg-elevated disabled:text-text-muted"
          onClick={handleApproveAll}
          disabled={isProcessing || !recommendations.some(r => r.status === 'pending')}
        >
          {isProcessing ? 'Processing...' : 'Approve All'}
        </button>
        <button 
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Hide SKUs' : 'Review SKUs'}
        </button>
        <button 
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary disabled:bg-bg-elevated disabled:text-text-muted"
          onClick={handleSnoozeAll}
          disabled={isProcessing || !recommendations.some(r => r.status === 'pending')}
        >
          {isProcessing ? 'Processing...' : 'Snooze 24h'}
        </button>
      </div>
      {expanded && (
        <div className="mt-4 space-y-2">
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
