import { formatInr } from '../../lib/formatters';
import { SkuDetail } from '../../types';

export default function StatePanel({ detail }: { detail: SkuDetail }) {
  const { sku, signals, recommendation } = detail;
  const marginFloor = recommendation?.margin_floor ?? signals.margin_floor;
  const recommendedPrice = recommendation?.recommended_price ?? sku.current_price;
  const headroom = recommendedPrice - marginFloor;

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="text-lg font-semibold">{sku.sku_name}</div>
      <div className="mt-1 text-xs uppercase text-text-muted">{sku.brand}</div>
      <div className="mt-3 grid grid-cols-3 gap-3 text-xs text-text-muted">
        <div>
          <div>Current Price</div>
          <div className="text-text-primary">{formatInr(sku.current_price)}</div>
        </div>
        <div>
          <div>Recommended</div>
          <div className="text-accent-blue">{formatInr(recommendedPrice)}</div>
        </div>
        <div>
          <div>Margin Floor</div>
          <div className="text-text-primary">{formatInr(marginFloor)}</div>
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between text-xs">
        <span className="rounded-full bg-bg-elevated px-2 py-1 text-text-primary">
          {signals.buy_box_state_6.replace('_', ' ').toUpperCase()}
        </span>
        <span className="text-text-muted">DOC: {signals.doc_current.toFixed(0)} days</span>
      </div>
      <div className="mt-3 text-xs text-text-muted">
        Margin headroom: {formatInr(headroom)}
      </div>
    </section>
  );
}
