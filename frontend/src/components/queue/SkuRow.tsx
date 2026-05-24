import { Recommendation } from '../../types';
import { formatPercent } from '../../lib/formatters';

interface SkuRowProps {
  recommendation: Recommendation;
  onSkuClick: (skuId: string) => void;
}

export default function SkuRow({ recommendation, onSkuClick }: SkuRowProps) {
  return (
    <div 
      className="rounded-lg border border-bg-elevated p-3 text-sm text-text-primary hover:bg-bg-elevated hover:border-accent-blue cursor-pointer transition-colors"
      onClick={() => onSkuClick(recommendation.sku_id)}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{recommendation.sku_id}</span>
        <span className="text-text-muted">{recommendation.confidence}</span>
      </div>
      <div className="mt-2 flex items-center gap-4 text-xs text-text-muted">
        <span>
          {recommendation.recommended_price} (gap {formatPercent(recommendation.competitor_price_gap / recommendation.recommended_price)})
        </span>
        <span>DOC {recommendation.days_to_stockout_current ?? '-'}d</span>
      </div>
    </div>
  );
}
