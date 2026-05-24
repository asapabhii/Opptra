'use client';

import { useEffect, useState } from 'react';
import { APP_STATE_CHANGED_EVENT, getPortfolioSummary } from '../../lib/api';
import { formatInr } from '../../lib/formatters';
import { PortfolioSummary } from '../../types';

type PortfolioFocus = 'all' | 'buy_box_lost' | 'bloated_stale' | 'stockout_risk' | 'most_urgent';

const FOCUS_LABELS: Record<PortfolioFocus, string> = {
  all: 'Portfolio Overview',
  buy_box_lost: 'Buy Box Lost',
  bloated_stale: 'Bloated & Stale',
  stockout_risk: 'Stockout Risk',
  most_urgent: 'Most Urgent',
};

export default function PortfolioHeader() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [focus, setFocus] = useState<PortfolioFocus>('all');

  useEffect(() => {
    const loadSummary = () => getPortfolioSummary().then(setSummary).catch(() => setSummary(null));
    loadSummary();

    const handleStateChange = () => loadSummary();
    window.addEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
    return () => window.removeEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
  }, []);

  const loading = !summary;
  const focusItem = summary?.items?.slice().sort((a, b) => b.impact_score - a.impact_score)[0] ?? null;
  const selectedItems =
    summary?.items
      ? focus === 'all'
        ? summary.items
        : focus === 'most_urgent'
        ? focusItem
          ? [focusItem]
          : []
        : summary.items.filter((item) => item.tags.includes(focus)).sort((a, b) => b.impact_score - a.impact_score)
      : [];

  return (
    <section className="px-4 pt-4 lg:px-6 lg:pt-6">
      <div className="rounded-xl bg-bg-card p-4 shadow-soft lg:p-6">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            label="Buy Box Lost"
            value={summary ? `${summary.buy_box_lost_count} SKUs` : ''}
            delta={summary ? `${summary.buy_box_lost_delta >= 0 ? '↑' : '↓'} ${Math.abs(summary.buy_box_lost_delta)} vs last week` : ''}
            tone="critical"
            loading={loading}
            selected={focus === 'buy_box_lost'}
            onClick={() => setFocus('buy_box_lost')}
          />
          <MetricCard
            label="GMV at Risk (7d)"
            value={summary ? `${formatInr(summary.gmv_at_risk_7d_inr)}` : ''}
            delta={summary?.gmv_at_risk_delta_pct != null
              ? `${summary.gmv_at_risk_delta_pct >= 0 ? '↑' : '↓'} ${Math.abs(summary.gmv_at_risk_delta_pct * 100).toFixed(0)}% vs last`
              : ''}
            tone="critical"
            loading={loading}
            selected={focus === 'buy_box_lost'}
            onClick={() => setFocus('buy_box_lost')}
          />
          <MetricCard
            label="Working Capital"
            value={summary ? `${formatInr(summary.working_capital_at_risk_inr)}` : ''}
            delta={summary?.working_capital_delta_pct != null
              ? `${summary.working_capital_delta_pct >= 0 ? '↑' : '↓'} ${Math.abs(summary.working_capital_delta_pct * 100).toFixed(0)}% vs last`
              : ''}
            tone="warning"
            loading={loading}
            selected={focus === 'bloated_stale'}
            onClick={() => setFocus('bloated_stale')}
          />
          <MetricCard
            label="Stockout Risk"
            value={summary ? `${summary.phantom_stockout_risk_count} SKUs` : ''}
            tone="warning"
            loading={loading}
            selected={focus === 'stockout_risk'}
            onClick={() => setFocus('stockout_risk')}
          />
          <MetricCard
            label="Most Urgent"
            value={summary ? summary.most_urgent_sku_id : ''}
            delta={summary ? summary.most_urgent_action : ''}
            tone="accent"
            loading={loading}
            selected={focus === 'most_urgent'}
            onClick={() => setFocus('most_urgent')}
          />
        </div>
        <p className="mt-4 text-sm text-text-muted">
          {summary ? summary.narrative : 'Loading portfolio narrative...'}
        </p>
        {summary && (
          <div className="mt-5 rounded-lg border border-bg-elevated bg-bg-elevated p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-xs uppercase tracking-wide text-text-muted">{FOCUS_LABELS[focus]}</div>
                <div className="mt-1 text-sm text-text-primary">
                  {focus === 'all'
                    ? 'High-level portfolio context, with the most important alerts and the current risk mix.'
                    : focus === 'most_urgent'
                    ? `${summary.most_urgent_sku_id} - ${summary.most_urgent_reason}`
                    : `Showing the SKUs that match ${FOCUS_LABELS[focus].toLowerCase()}.`}
                </div>
              </div>
              <div className="text-xs text-text-muted">{selectedItems.length} SKUs shown</div>
            </div>

            {focus === 'most_urgent' && focusItem && (
              <div className="mt-4 rounded-md bg-bg-card p-4 text-sm text-text-muted">
                <div className="text-text-primary font-semibold">{summary.most_urgent_sku_name}</div>
                <div className="mt-1">Action: {summary.most_urgent_action}</div>
                <div className="mt-1">Reason: {summary.most_urgent_reason}</div>
                <div className="mt-1">Impact score: {focusItem.impact_score.toFixed(2)}</div>
                <div className="mt-1">DOC: {focusItem.doc_current.toFixed(0)} days</div>
              </div>
            )}

            {focus !== 'most_urgent' && selectedItems.length > 0 && (
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {selectedItems.slice(0, 6).map((item) => (
                  <div key={item.sku_id} className="rounded-md bg-bg-card p-4 text-sm text-text-muted">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-text-primary">{item.sku_name}</div>
                        <div>{item.sku_id} - {item.brand}</div>
                      </div>
                      <div className="text-right text-[11px] uppercase tracking-wide text-text-muted">
                        {item.tags.includes('buy_box_lost')
                          ? 'Buy Box Lost'
                          : item.tags.includes('stockout_risk')
                          ? 'Stockout Risk'
                          : item.tags.includes('bloated_stale')
                          ? 'Bloated & Stale'
                          : 'Escalate'}
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div>DOC {item.doc_current.toFixed(0)}d</div>
                      <div>GMV {formatInr(item.gmv_at_risk_7d_inr)}</div>
                      <div>Working capital {formatInr(item.working_capital_inr)}</div>
                      <div>Action {item.recommended_action}</div>
                    </div>
                    <div className="mt-2 text-xs text-text-primary">{item.recommended_reason}</div>
                  </div>
                ))}
              </div>
            )}

            {summary.critical_alerts.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-text-muted">
                {summary.critical_alerts.map((alert) => (
                  <span key={alert} className="rounded-full border border-bg-elevated px-3 py-1">
                    {alert}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function MetricCard({
  label,
  value,
  delta,
  tone,
  loading,
  selected,
  onClick,
}: {
  label: string;
  value: string;
  delta?: string;
  tone: string;
  loading: boolean;
  selected?: boolean;
  onClick?: () => void;
}) {
  const toneClass =
    tone === 'critical'
      ? 'text-critical'
      : tone === 'warning'
      ? 'text-warning'
      : tone === 'accent'
      ? 'text-accent-blue'
      : 'text-text-primary';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg bg-bg-elevated p-4 text-left transition-colors ${
        selected ? 'ring-1 ring-accent-blue' : 'hover:bg-[#243047]'
      }`}
    >
      <div className="text-xs uppercase tracking-wide text-text-muted">{label}</div>
      {loading ? (
        <div className="mt-2 h-6 w-24 animate-pulse rounded bg-bg-card" />
      ) : (
        <div className={`mt-2 text-xl font-semibold ${toneClass}`}>{value}</div>
      )}
      {delta && <div className="mt-1 text-xs text-text-muted">{delta}</div>}
    </button>
  );
}
