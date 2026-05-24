'use client';

import { useState } from 'react';
import { getPortfolioSynthesis } from '../../lib/api';

export default function PortfolioInsightsPanel() {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    const data = await getPortfolioSynthesis();
    setInsights(data);
    setLoading(false);
  };

  return (
    <div className="mt-6 rounded-xl bg-bg-card p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Portfolio Insights</h3>
        <button
          onClick={handleGenerate}
          className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white"
        >
          {loading ? 'Analyzing...' : 'Generate Portfolio Insights'}
        </button>
      </div>
      {insights && (
        <div className="mt-4 space-y-3 text-sm text-text-muted">
          {insights.patterns?.map((pattern: any) => (
            <div key={pattern.pattern_name} className="rounded-lg bg-bg-elevated p-3">
              <div className="text-text-primary font-semibold">{pattern.pattern_name}</div>
              <div>{pattern.description}</div>
              <div className="mt-2">{pattern.actionable_recommendation}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
