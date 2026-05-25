import { SkuDetail } from '../../types';

export default function ReasoningPanel({ detail }: { detail: SkuDetail }) {
  const rec = detail.recommendation;
  if (!rec) return null;

  const isFallbackReasoning = rec.source === 'rule_engine_fallback';

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-text-primary">AI Reasoning</div>
        <span className={`rounded-full px-2 py-1 text-[11px] uppercase tracking-wide ${isFallbackReasoning ? 'bg-warning/10 text-warning' : 'bg-bg-elevated text-text-muted'}`}>
          {isFallbackReasoning ? 'Fallback' : 'Live AI'}
        </span>
      </div>
      <blockquote className="mt-3 border-l-2 border-bg-elevated pl-3 text-sm text-text-muted">
        {rec.reasoning || 'Reasoning not available yet.'}
      </blockquote>
      {isFallbackReasoning && (
        <div className="mt-3 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2 text-xs text-warning">
          Live AI could not be reached, so this recommendation used the fallback reasoning path.
        </div>
      )}
      {rec.flags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-text-muted">
          {rec.flags.map((flag) => (
            <span key={flag} className="rounded-full bg-bg-elevated px-2 py-1">
              {flag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
    </section>
  );
}
