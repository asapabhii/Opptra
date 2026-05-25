'use client';

import { QueueRun } from '../../types';

export type QueueFilterKey = 'all' | 'buy_box_lost' | 'bloated_stale' | 'stockout_risk' | 'escalate';

const FILTER_LABELS: Record<QueueFilterKey, string> = {
  all: 'All',
  buy_box_lost: 'Buy Box Lost',
  bloated_stale: 'Bloated & Stale',
  stockout_risk: 'Stockout Risk',
  escalate: 'Escalate',
};

export default function QueueControls({
  run,
  status,
  onRun,
  onRefresh,
  loading,
  activeFilter,
  onFilterChange,
  filterCounts,
}: {
  run: QueueRun | null;
  status: any;
  onRun: () => void;
  onRefresh: () => void;
  loading: boolean;
  activeFilter: QueueFilterKey;
  onFilterChange: (filter: QueueFilterKey) => void;
  filterCounts: Record<QueueFilterKey, number>;
}) {
  const lastAnalysed = run?.completed_at ?? run?.triggered_at ?? null;
  const isRunning = status?.status === 'running';
  const progressText = isRunning
    ? status?.total_skus > 0
      ? `Processing SKU ${status.skus_processed} of ${status.total_skus}`
      : 'Preparing analysis...'
    : lastAnalysed
      ? `Last analysed: ${new Date(lastAnalysed).toLocaleTimeString()}`
      : 'Not analysed yet';

  return (
    <div className="flex flex-col gap-4 rounded-xl bg-bg-card p-4 shadow-soft">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-wrap items-center gap-2 text-sm text-text-muted">
          <span className="rounded-full border border-bg-elevated bg-bg-elevated px-3 py-1 text-xs font-semibold uppercase tracking-wide text-text-muted">
            {progressText}
          </span>
          {isRunning && (
            <span className="rounded-full bg-accent-blue/15 px-3 py-1 text-xs font-semibold text-accent-blue">
              Live analysis
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-md border border-bg-elevated px-4 py-2 text-sm font-semibold text-text-primary transition-colors hover:bg-bg-elevated"
          >
            Refresh Queue
          </button>
          <button
            type="button"
            onClick={onRun}
            disabled={loading}
            className="rounded-md bg-accent-blue px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-accent-blue/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? 'Analyzing...' : 'Run AI Analysis'}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-sm text-text-muted">
        {(Object.keys(FILTER_LABELS) as QueueFilterKey[]).map((filter) => {
          const selected = activeFilter === filter;
          return (
            <button
              key={filter}
              type="button"
              onClick={() => onFilterChange(filter)}
              className={`rounded-full px-3 py-1 transition-colors ${
                selected
                  ? 'bg-bg-elevated text-text-primary'
                  : 'border border-bg-elevated text-text-muted hover:text-text-primary'
              }`}
            >
              {FILTER_LABELS[filter]}
              <span className="ml-2 text-[11px] opacity-70">{filterCounts[filter] ?? 0}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
