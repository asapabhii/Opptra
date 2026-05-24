import { formatInr, formatPercent } from '../../lib/formatters';
import { SkuDetail } from '../../types';

export default function CompetitorPanel({ detail }: { detail: SkuDetail }) {
  const competitor = detail.signals.competitor;
  const age = detail.signals.competitor_price_age_hours;

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="text-sm font-semibold text-text-primary">Competitor</div>
      {competitor ? (
        <div className="mt-3 text-xs text-text-muted">
          <div className="flex items-center justify-between">
            <span className="text-text-primary">{competitor.seller_name}</span>
            <span>{formatInr(competitor.price)}</span>
          </div>
          <div className="mt-1">Type: {competitor.seller_type_hint}</div>
          <div>Fulfillment: {competitor.fulfillment_type}</div>
          {competitor.listing_age_days != null && (
            <div>Listing age: {competitor.listing_age_days} days</div>
          )}
          {age != null && (
            <div className="mt-2">Competitor data: {age}h ago</div>
          )}
        </div>
      ) : (
        <div className="mt-3 text-xs text-text-muted">No active competitor listed.</div>
      )}
    </section>
  );
}
