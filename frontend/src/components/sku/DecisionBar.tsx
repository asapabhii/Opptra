'use client';

import { useState } from 'react';
import { Recommendation } from '../../types';
import { formatInr } from '../../lib/formatters';

export default function DecisionBar({
  recommendation,
  onApprove,
  onSnooze,
  onOverride,
}: {
  recommendation: Recommendation;
  onApprove: () => void;
  onSnooze: (hours: number) => void;
  onOverride: () => void;
}) {
  const [snoozeOpen, setSnoozeOpen] = useState(false);

  return (
    <div className="sticky bottom-0 mt-6 rounded-xl bg-bg-card p-4">
      <div className="text-xs text-text-muted">Ready to decide?</div>
      <div className="mt-2 flex gap-3">
        <button
          onClick={onApprove}
          className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white"
        >
          Approve {formatInr(recommendation.recommended_price)}
        </button>
        <div className="relative">
          <button
            onClick={() => setSnoozeOpen((prev) => !prev)}
            className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary"
          >
            Snooze
          </button>
          {snoozeOpen && (
            <div className="absolute left-0 mt-2 w-32 rounded-md bg-bg-elevated p-2 text-xs">
              <button onClick={() => onSnooze(6)} className="block w-full py-1 text-left">Snooze 6h</button>
              <button onClick={() => onSnooze(24)} className="block w-full py-1 text-left">Snooze 24h</button>
            </div>
          )}
        </div>
        <button
          onClick={onOverride}
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary"
        >
          Override
        </button>
      </div>
    </div>
  );
}
