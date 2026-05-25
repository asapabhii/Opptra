'use client';

import { useState } from 'react';
import Link from 'next/link';
import DecisionLogTable from '../../components/log/DecisionLogTable';
import LogFilters, { DecisionLogFilters } from '../../components/log/LogFilters';
import PortfolioInsightsPanel from '../../components/log/PortfolioInsightsPanel';

export default function LogPage() {
  const [filters, setFilters] = useState<DecisionLogFilters>({
    brand: '',
    decisionType: '',
    skuId: '',
    dateRange: '30',
  });

  return (
    <main className="min-h-screen bg-bg-base px-4 py-4 text-text-primary lg:px-6 lg:py-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-4">
        <div className="flex items-center justify-between gap-3 rounded-xl bg-bg-card px-4 py-3 shadow-soft">
          <div>
            <div className="text-sm font-semibold text-text-primary">Decision Log</div>
            <div className="text-xs text-text-muted">Review decisions, refresh the log, or jump back to the queue.</div>
          </div>
          <Link href="/" className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary">
            Back to Queue
          </Link>
        </div>
        <LogFilters
          filters={filters}
          onChange={setFilters}
          onRefresh={() => setFilters((current) => ({ ...current }))}
          onReset={() => setFilters({ brand: '', decisionType: '', skuId: '', dateRange: '30' })}
        />
        <DecisionLogTable filters={filters} />
        <PortfolioInsightsPanel />
      </div>
    </main>
  );
}
