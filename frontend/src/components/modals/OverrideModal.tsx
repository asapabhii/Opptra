'use client';

import { useState } from 'react';
import { formatInr } from '../../lib/formatters';
import { Recommendation, SkuDetail } from '../../types';

const REASONS = [
  { id: 'map_constraint', label: 'MAP constraint - staying above MAP' },
  { id: 'competitor_context', label: 'Competitor context - I know something the system does not' },
  { id: 'festival_season', label: 'Festival / demand event - holding for upcoming demand' },
  { id: 'brand_instruction', label: 'Brand instruction - do not change price' },
  { id: 'price_direction_wrong', label: 'Price direction wrong' },
  { id: 'price_magnitude_wrong', label: 'Price magnitude wrong' },
  { id: 'data_quality_doubt', label: 'Data quality doubt' },
  { id: 'other', label: 'Other' },
];

export default function OverrideModal({
  detail,
  recommendation,
  onClose,
  onSubmit,
}: {
  detail: SkuDetail;
  recommendation: Recommendation;
  onClose: () => void;
  onSubmit: (payload: { human_price: number; reason_category: string; notes: string }) => void;
}) {
  const [price, setPrice] = useState(recommendation.recommended_price);
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');
  const marginFloor = recommendation.margin_floor;
  const marginAtPrice = price - marginFloor;
  const marginPct = price > 0 ? (marginAtPrice / price) * 100 : 0;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-2xl rounded-xl bg-bg-card p-6">
        <div className="text-lg font-semibold text-text-primary">Override Recommendation</div>
        <div className="mt-2 text-xs text-text-muted">
          AI recommended: {recommendation.action_type.replace('_', ' ')} to {formatInr(recommendation.recommended_price)}
        </div>
        <div className="mt-4">
          <label className="text-xs text-text-muted">Your price</label>
          <input
            type="number"
            value={price}
            onChange={(event) => setPrice(Number(event.target.value))}
            className="mt-1 w-full rounded-md bg-bg-elevated p-2 text-sm text-text-primary"
          />
          <div className="mt-2 text-xs text-text-muted">
            Margin at this price: {formatInr(marginAtPrice)} ({marginPct.toFixed(1)}%)
          </div>
          {price < marginFloor && (
            <div className="mt-2 text-xs text-warning">
              {formatInr(price)} is below the margin floor ({formatInr(marginFloor)}). This will destroy margin.
            </div>
          )}
        </div>
        <div className="mt-4">
          <div className="text-xs text-text-muted">Why are you overriding?</div>
          <div className="mt-2 space-y-2 text-xs text-text-primary">
            {REASONS.map((item) => (
              <label key={item.id} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="override-reason"
                  value={item.id}
                  checked={reason === item.id}
                  onChange={() => setReason(item.id)}
                />
                {item.label}
              </label>
            ))}
          </div>
        </div>
        <div className="mt-4">
          <label className="text-xs text-text-muted">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            className="mt-1 h-20 w-full rounded-md bg-bg-elevated p-2 text-sm text-text-primary"
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="rounded-md border border-bg-elevated px-4 py-2 text-xs">
            Cancel
          </button>
          <button
            onClick={() => reason && onSubmit({ human_price: price, reason_category: reason, notes })}
            className="rounded-md bg-accent-blue px-4 py-2 text-xs font-semibold text-white"
          >
            Submit Override
          </button>
        </div>
      </div>
    </div>
  );
}
