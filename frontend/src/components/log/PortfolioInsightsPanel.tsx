'use client';

import { useEffect, useState } from 'react';
import { APP_STATE_CHANGED_EVENT, getPortfolioSynthesis } from '../../lib/api';

export default function PortfolioInsightsPanel() {
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await getPortfolioSynthesis();
      setInsights(data);
    } catch (error) {
      console.error('Failed to generate portfolio insights:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleStateChange = () => refresh();
    window.addEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
    return () => window.removeEventListener(APP_STATE_CHANGED_EVENT, handleStateChange as EventListener);
  }, []);

  const handleGenerate = async () => {
    await refresh();
  };

  return (
    <div className="rounded-xl bg-bg-card p-4 shadow-soft">
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
        <div className="mt-4 grid gap-3 text-sm text-text-muted xl:grid-cols-2">
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
