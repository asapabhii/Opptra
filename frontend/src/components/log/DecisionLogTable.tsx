'use client';

import { useEffect, useMemo, useState } from 'react';
import { APP_STATE_CHANGED_EVENT, getDecisionLog } from '../../lib/api';
import { Decision } from '../../types';
import { formatRelativeDate } from '../../lib/formatters';
import type { DecisionLogFilters } from './LogFilters';

export default function DecisionLogTable({ filters, refreshToken = 0 }: { filters: DecisionLogFilters; refreshToken?: number }) {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastLoadedAt, setLastLoadedAt] = useState<string | null>(null);

  const query = useMemo(() => {
    const params: Record<string, string> = {};
    if (filters.brand) params.brand = filters.brand;
    if (filters.decisionType) params.decision_type = filters.decisionType;
    if (filters.skuId) params.sku_id = filters.skuId;
    if (filters.dateRange) {
      const days = Number(filters.dateRange);
      const from = new Date();
      from.setDate(from.getDate() - days);
      params.date_from = from.toISOString();
    }
    return params;
  }, [filters]);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await getDecisionLog(query);
      setDecisions(data.decisions ?? []);
      setLastLoadedAt(new Date().toISOString());
    } catch (error) {
      console.error('Failed to load decision log:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [query, refreshToken]);

  useEffect(() => {
    const handleStateChange = () => refresh();
    window.addEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
    const interval = window.setInterval(handleStateChange, 15000);
    return () => {
      window.removeEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
      window.clearInterval(interval);
    };
  }, [query]);

  return (
    <div className="rounded-xl bg-bg-card p-4 shadow-soft">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-text-primary">Decision Log</div>
          <div className="text-xs text-text-muted">
            {loading ? 'Refreshing...' : `Showing ${decisions.length} records${lastLoadedAt ? ` • updated ${formatRelativeDate(lastLoadedAt)}` : ''}`}
          </div>
        </div>
        <button onClick={refresh} className="rounded-md border border-bg-elevated px-3 py-2 text-xs font-semibold text-text-primary">
          Refresh Now
        </button>
      </div>
      <div className="max-h-[34rem] overflow-auto rounded-lg border border-bg-elevated">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-bg-card text-text-muted">
            <tr>
              <th className="py-2">When</th>
              <th className="py-2">SKU</th>
              <th className="py-2">Brand</th>
              <th className="py-2">AI Said</th>
              <th className="py-2">You Decided</th>
              <th className="py-2">Reason</th>
              <th className="py-2">Outcome</th>
              <th className="py-2">Insight</th>
            </tr>
          </thead>
          <tbody className="text-text-primary">
            {decisions.length === 0 ? (
              <tr>
                <td className="py-6 text-center text-text-muted" colSpan={8}>
                  No decisions match the current filters.
                </td>
              </tr>
            ) : (
              decisions.map((decision) => (
                <tr key={decision.id} className="border-t border-bg-elevated align-top">
                  <td className="whitespace-nowrap py-2 pr-3">{formatRelativeDate(decision.decided_at)}</td>
                  <td className="whitespace-nowrap py-2 pr-3 font-medium">{decision.sku_id}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{decision.brand ?? '-'}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{decision.original_recommended_price}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{decision.decision}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{decision.override_reason_category ?? '-'}</td>
                  <td className="max-w-[18rem] py-2 pr-3">{decision.outcome_note ?? '-'}</td>
                  <td className="whitespace-nowrap py-2 pr-3">{decision.override_insight ? 'Insight' : '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
