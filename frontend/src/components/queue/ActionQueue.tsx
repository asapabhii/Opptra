'use client';

import { useEffect, useState } from 'react';
import { APP_STATE_CHANGED_EVENT, getLatestRun, getRunStatus, runQueue } from '../../lib/api';
import { Cluster, Recommendation, QueueRun } from '../../types';
import QueueControls, { QueueFilterKey } from './QueueControls';
import ClusterCard from './ClusterCard';

interface ActionQueueProps {
  onSkuClick: (skuId: string) => void;
}

export default function ActionQueue({ onSkuClick }: ActionQueueProps) {
  const [run, setRun] = useState<QueueRun | null>(null);
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [status, setStatus] = useState<any>(null);
  const [activeFilter, setActiveFilter] = useState<QueueFilterKey>('all');
  const [loading, setLoading] = useState(false);
  const [autoRunPending, setAutoRunPending] = useState(false);
  const [bootstrapping, setBootstrapping] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const refreshLatestRun = async () => {
    try {
      const latest = await getLatestRun();
      setRun(latest.run);
      setClusters(latest.clusters ?? []);
      setRecommendations(latest.recommendations ?? []);
    } catch (error) {
      console.error('Failed to refresh queue state:', error);
    }
  };

  useEffect(() => {
    let cancelled = false;

    const initializeQueue = async () => {
      try {
        const latest = await getLatestRun();
        if (cancelled) return;

        setRun(latest.run);

        if (latest.run?.id === 'seed-run-001' && !window.sessionStorage.getItem('opptra:auto-run-once')) {
          window.sessionStorage.setItem('opptra:auto-run-once', 'true');
          setBootstrapping(true);
          setClusters([]);
          setRecommendations([]);
          setStatus({ status: 'running', skus_processed: 0, total_skus: 0, run_id: 'seed-bootstrap' });
          setAutoRunPending(true);
          return;
        }

        setBootstrapping(false);
        setClusters(latest.clusters ?? []);
        setRecommendations(latest.recommendations ?? []);
      } catch (error) {
        console.error('Failed to initialize queue state:', error);
      }
    };

    initializeQueue();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!autoRunPending) return;
    setAutoRunPending(false);
    void handleRun();
  }, [autoRunPending]);

  useEffect(() => {
    const handleRefresh = () => {
      refreshLatestRun();
    };

    window.addEventListener(APP_STATE_CHANGED_EVENT, handleRefresh as EventListener);
    return () => window.removeEventListener(APP_STATE_CHANGED_EVENT, handleRefresh as EventListener);
  }, []);

  const handleRun = async () => {
    if (loading) return;

    setLoading(true);
    setRunError(null);

    try {
      const started = await runQueue();
      setStatus({ status: 'running', skus_processed: 0, total_skus: 0, run_id: started.run_id });

      const interval = window.setInterval(async () => {
        try {
          const s = await getRunStatus(started.run_id);
          setStatus(s);

          if (s.status === 'complete' || s.status === 'failed') {
            window.clearInterval(interval);
            await refreshLatestRun();
            if (s.status === 'failed') {
              setRunError((s as any).error || 'Queue analysis failed while running live AI.');
            }
            setLoading(false);
            setBootstrapping(false);
          }
        } catch (error) {
          console.error('Failed to poll run status:', error);
          // If the run ID is not found (404), stop polling and refresh latest run
          const status = (error as any)?.status;
          if (status === 404) {
            window.clearInterval(interval);
            await refreshLatestRun();
            setRunError('Queue run not found on this server. Possible multi-instance DB mismatch.');
            setLoading(false);
            setBootstrapping(false);
          }
        }
      }, 2000);
    } catch (err) {
      console.error(err);
      setRunError(err instanceof Error ? err.message : 'Could not start the queue analysis.');
      setLoading(false);
      setBootstrapping(false);
    }
  };

  const getClusterRecommendations = (cluster: Cluster) =>
    recommendations.filter((rec) => cluster.sku_ids.includes(rec.sku_id));

  const isBuyBoxLostCluster = (cluster: Cluster) =>
    ['grey_market_flooding', 'authorized_competitor_direct', 'map_violation_escalation', 'bleeding_margin_clearance'].includes(
      cluster.root_cause
    );

  const isBloatedStaleCluster = (cluster: Cluster) =>
    ['critical_doc_clearance', 'bloated_stale_reduction'].includes(cluster.root_cause);

  const isStockoutRiskCluster = (cluster: Cluster) => cluster.root_cause === 'phantom_stockout_reorder';

  const isEscalateCluster = (cluster: Cluster) => cluster.root_cause === 'mixed_escalation';

  const clusterMatchesFilter = (cluster: Cluster) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'buy_box_lost') return isBuyBoxLostCluster(cluster);
    if (activeFilter === 'bloated_stale') return isBloatedStaleCluster(cluster);
    if (activeFilter === 'stockout_risk') return isStockoutRiskCluster(cluster);
    if (activeFilter === 'escalate') return isEscalateCluster(cluster);

    return true;
  };

  const visibleClusters = clusters.filter(clusterMatchesFilter);

  const filterCounts: Record<QueueFilterKey, number> = {
    all: clusters.length,
    buy_box_lost: clusters.filter(isBuyBoxLostCluster).length,
    bloated_stale: clusters.filter(isBloatedStaleCluster).length,
    stockout_risk: clusters.filter(isStockoutRiskCluster).length,
    escalate: clusters.filter(isEscalateCluster).length,
  };

  return (
    <section className="px-8 py-6">
      <QueueControls
        run={run}
        status={status}
        onRun={handleRun}
        onRefresh={refreshLatestRun}
        loading={loading}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        filterCounts={filterCounts}
      />

      {runError && (
        <div className="mt-4 rounded-xl border border-warning/30 bg-warning/10 px-4 py-3 text-sm text-warning">
          {runError}
        </div>
      )}

      <div className="mt-4 space-y-4">
        {visibleClusters.map((cluster) => (
          <ClusterCard
            key={cluster.id}
            cluster={cluster}
            recommendations={getClusterRecommendations(cluster)}
            onSkuClick={onSkuClick}
            onDecisionApplied={refreshLatestRun}
          />
        ))}

        {!clusters.length && !bootstrapping && (
          <div className="rounded-xl border border-bg-elevated bg-bg-card p-8 text-center text-text-muted">
            No analysis has been run yet. Click "Run AI Analysis" to begin.
          </div>
        )}

        {clusters.length > 0 && !visibleClusters.length && (
          <div className="rounded-xl border border-bg-elevated bg-bg-card p-8 text-center text-text-muted">
            No clusters match the current filter.
          </div>
        )}
      </div>
    </section>
  );
}