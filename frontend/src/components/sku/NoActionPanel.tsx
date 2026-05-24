import { formatInr } from '../../lib/formatters';
import { SkuDetail } from '../../types';

export default function NoActionPanel({ detail }: { detail: SkuDetail }) {
  const { signals } = detail;
  return (
    <section className="rounded-xl bg-bg-card p-4 text-xs text-text-muted">
      <div className="text-sm font-semibold text-text-primary">If you do nothing for 7 days...</div>
      <div className="mt-3 grid grid-cols-2 gap-4">
        <div>
          <div>Buy Box</div>
          <div className="text-text-primary">{signals.buy_box_state_6.replace('_', ' ')}</div>
        </div>
        <div>
          <div>GMV lost</div>
          <div className="text-text-primary">{formatInr(signals.gmv_at_risk_7d_inr)}</div>
        </div>
        <div>
          <div>DOC</div>
          <div className="text-text-primary">{signals.doc_current.toFixed(0)} days</div>
        </div>
        <div>
          <div>Margin floor</div>
          <div className="text-text-primary">{formatInr(signals.margin_floor)}</div>
        </div>
      </div>
    </section>
  );
}
