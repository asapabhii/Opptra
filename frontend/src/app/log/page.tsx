'use client';

import { useState } from 'react';
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
