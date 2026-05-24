import { formatInr } from '../../lib/formatters';
import { SkuDetail } from '../../types';

export default function SellerMetricsPanel({ detail }: { detail: SkuDetail }) {
  const { sku, signals } = detail;
  const workingCapital = sku.cost * sku.units_on_hand;

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="text-sm font-semibold text-text-primary">Our Position</div>
      <div className="mt-3 text-xs text-text-muted">
        <div>Fulfillment: FBA</div>
        <div>Units on hand: {sku.units_on_hand}</div>
        <div>Working capital: {formatInr(workingCapital)}</div>
        {signals.storage_accrual_per_unit > 0 && (
          <div className="mt-2 rounded bg-bg-elevated p-2 text-warning">
            Storage accrual active: {formatInr(signals.storage_accrual_per_unit)} / unit per month
          </div>
        )}
      </div>
    </section>
  );
}
