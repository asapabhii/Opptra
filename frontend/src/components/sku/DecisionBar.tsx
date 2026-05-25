'use client';

import { useState } from 'react';
import { Recommendation } from '../../types';
import { formatInr } from '../../lib/formatters';

export default function DecisionBar({
  recommendation,
  onApprove,
  onSnooze,
  onOverride,
  disabled = false,
}: {
  recommendation: Recommendation;
  onApprove: () => void;
  onSnooze: (hours: number) => void;
  onOverride: () => void;
  disabled?: boolean;
}) {
  const [snoozeOpen, setSnoozeOpen] = useState(false);

  return (
    <div className="sticky bottom-0 mt-6 rounded-xl bg-bg-card p-4 shadow-soft">
      <div className="text-xs text-text-muted">Ready to decide?</div>
      <div className="mt-2 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onApprove}
          disabled={disabled}
          className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-bg-elevated disabled:text-text-muted"
        >
          Approve {formatInr(recommendation.recommended_price)}
        </button>
        <div className="relative">
          <button
            type="button"
            onClick={() => setSnoozeOpen((prev) => !prev)}
            disabled={disabled}
            className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
          >
            Snooze
          </button>
          {snoozeOpen && (
            <div className="absolute left-0 z-10 mt-2 w-36 rounded-md bg-bg-elevated p-2 text-xs shadow-soft">
              <button type="button" onClick={() => { setSnoozeOpen(false); onSnooze(6); }} className="block w-full rounded px-2 py-1 text-left hover:bg-bg-card">Snooze 6h</button>
              <button type="button" onClick={() => { setSnoozeOpen(false); onSnooze(24); }} className="block w-full rounded px-2 py-1 text-left hover:bg-bg-card">Snooze 24h</button>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onOverride}
          disabled={disabled}
          className="rounded-md border border-bg-elevated px-4 py-2 text-xs font-semibold text-text-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          Override
        </button>
      </div>
    </div>
  );
}
