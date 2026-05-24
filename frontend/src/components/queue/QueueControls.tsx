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
  loading,
  activeFilter,
  onFilterChange,
  filterCounts,
}: {
  run: QueueRun | null;
  status: any;
  onRun: () => void;
  loading: boolean;
  activeFilter: QueueFilterKey;
  onFilterChange: (filter: QueueFilterKey) => void;
  filterCounts: Record<QueueFilterKey, number>;
}) {
  const lastAnalysed = run?.completed_at ?? run?.triggered_at ?? null;
  const isRunning = status?.status === 'running';

  return (
    <div className="flex flex-col gap-4 rounded-xl bg-bg-card p-4 md:flex-row md:items-center md:justify-between">
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
      <div className="flex items-center gap-4">
        <span className="text-xs text-text-muted">
          {lastAnalysed ? `Last analysed: ${new Date(lastAnalysed).toLocaleTimeString()}` : 'Not analysed yet'}
        </span>
        <button
          onClick={onRun}
          disabled={loading}
          className="rounded-md bg-accent-blue px-4 py-2 text-sm font-semibold text-white"
        >
          {loading ? 'Running AI Analysis...' : 'Run AI Analysis'}
        </button>
      </div>
      {isRunning && (
        <div className="text-xs text-text-muted">
          Processing SKU {status.skus_processed} of {status.total_skus}
        </div>
      )}
    </div>
  );
}
