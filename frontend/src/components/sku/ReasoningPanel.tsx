import { SkuDetail } from '../../types';

export default function ReasoningPanel({ detail }: { detail: SkuDetail }) {
  const rec = detail.recommendation;
  if (!rec) return null;

  const isLocalDemoReasoning = rec.source === 'rule_engine_fallback';

  return (
    <section className="rounded-xl bg-bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-text-primary">AI Reasoning</div>
        <span className={`rounded-full px-2 py-1 text-[11px] uppercase tracking-wide ${isLocalDemoReasoning ? 'bg-accent-blue/10 text-accent-blue' : 'bg-bg-elevated text-text-muted'}`}>
          {isLocalDemoReasoning ? 'Demo AI' : 'Live AI'}
        </span>
      </div>
      <blockquote className="mt-3 border-l-2 border-bg-elevated pl-3 text-sm text-text-muted">
        {rec.reasoning || 'Reasoning not available yet.'}
      </blockquote>
      {isLocalDemoReasoning && (
        <div className="mt-3 rounded-lg border border-bg-elevated bg-bg-elevated px-3 py-2 text-xs text-text-muted">
          External AI credentials are not configured here, so the app is using the built-in demo analysis path.
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
