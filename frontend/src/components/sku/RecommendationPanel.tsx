import { formatInr } from '../../lib/formatters';
import { SkuDetail } from '../../types';

export default function RecommendationPanel({ detail }: { detail: SkuDetail }) {
  const rec = detail.recommendation;
  if (!rec) return null;

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="text-sm font-semibold text-text-primary">Recommendation</div>
      <div className="mt-3 text-2xl font-semibold text-accent-blue">
        {rec.action_type.replace('_', ' ').toUpperCase()} {formatInr(rec.recommended_price)}
      </div>
      <div className="mt-2 text-xs text-text-muted">
        Margin at this price: {formatInr(rec.margin_at_recommended)} ({(rec.margin_pct_at_recommended * 100).toFixed(1)}%)
      </div>
      <div className="mt-1 text-xs text-text-muted">Margin floor: {formatInr(rec.margin_floor)}</div>
      <div className="mt-2 text-xs text-text-muted">Confidence: {rec.confidence.toUpperCase()}</div>
    </section>
  );
}
