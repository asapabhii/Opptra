'use client';

import { useEffect, useState } from 'react';
import { getDecisionLog } from '../../lib/api';
import { Decision } from '../../types';
import { formatRelativeDate } from '../../lib/formatters';

export default function DecisionLogTable() {
  const [decisions, setDecisions] = useState<Decision[]>([]);

  useEffect(() => {
    getDecisionLog().then((data) => setDecisions(data.decisions ?? [])).catch(() => null);
  }, []);

  return (
    <div className="rounded-xl bg-bg-card p-4">
      <table className="w-full text-left text-sm">
        <thead className="text-text-muted">
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
          {decisions.map((decision) => (
            <tr key={decision.id} className="border-t border-bg-elevated">
              <td className="py-2">{formatRelativeDate(decision.decided_at)}</td>
              <td className="py-2">{decision.sku_id}</td>
              <td className="py-2">{decision.brand ?? '-'}</td>
              <td className="py-2">{decision.original_recommended_price}</td>
              <td className="py-2">{decision.decision}</td>
              <td className="py-2">{decision.override_reason_category ?? '-'}</td>
              <td className="py-2">{decision.outcome_note ?? '-'}</td>
              <td className="py-2">{decision.override_insight ? 'Insight' : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
