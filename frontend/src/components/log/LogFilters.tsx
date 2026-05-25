'use client';

import type { ReactNode } from 'react';

export type DecisionLogFilters = {
  brand: string;
  decisionType: string;
  skuId: string;
  dateRange: '7' | '30' | '90';
};

export default function LogFilters({
  filters,
  onChange,
  onRefresh,
  onReset,
}: {
  filters: DecisionLogFilters;
  onChange: (filters: DecisionLogFilters) => void;
  onRefresh: () => void;
  onReset: () => void;
}) {
  return (
    <div className="rounded-xl bg-bg-card p-4 text-sm text-text-muted shadow-soft">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4 xl:flex-1">
          <LabelField label="Brand">
            <input
              value={filters.brand}
              onChange={(event) => onChange({ ...filters, brand: event.target.value })}
              placeholder="All brands"
              className="w-full rounded-md border border-bg-elevated bg-bg-elevated px-3 py-2 text-text-primary outline-none"
            />
          </LabelField>
          <LabelField label="Decision">
            <select
              value={filters.decisionType}
              onChange={(event) => onChange({ ...filters, decisionType: event.target.value })}
              className="w-full rounded-md border border-bg-elevated bg-bg-elevated px-3 py-2 text-text-primary outline-none"
            >
              <option value="">All decisions</option>
              <option value="approved">Approved</option>
              <option value="overridden">Overridden</option>
              <option value="snoozed">Snoozed</option>
            </select>
          </LabelField>
          <LabelField label="Date range">
            <select
              value={filters.dateRange}
              onChange={(event) => onChange({ ...filters, dateRange: event.target.value as DecisionLogFilters['dateRange'] })}
              className="w-full rounded-md border border-bg-elevated bg-bg-elevated px-3 py-2 text-text-primary outline-none"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </LabelField>
          <LabelField label="SKU ID">
            <input
              value={filters.skuId}
              onChange={(event) => onChange({ ...filters, skuId: event.target.value })}
              placeholder="Search SKU"
              className="w-full rounded-md border border-bg-elevated bg-bg-elevated px-3 py-2 text-text-primary outline-none"
            />
          </LabelField>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={onReset} className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary">
            Reset View
          </button>
          <button type="button" onClick={onRefresh} className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white">
            Refresh Log
          </button>
        </div>
      </div>
    </div>
  );
}

function LabelField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="space-y-2 text-xs uppercase tracking-wide text-text-muted">
      <div>{label}</div>
      {children}
    </label>
  );
}
