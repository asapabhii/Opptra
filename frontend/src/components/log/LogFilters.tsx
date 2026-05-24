'use client';

export default function LogFilters() {
  return (
    <div className="mb-6 rounded-xl bg-bg-card p-4 text-sm text-text-muted">
      <div className="flex flex-wrap gap-3">
        <span className="rounded-full border border-bg-elevated px-3 py-1">All Brands</span>
        <span className="rounded-full border border-bg-elevated px-3 py-1">All Decisions</span>
        <span className="rounded-full border border-bg-elevated px-3 py-1">Last 30 days</span>
        <span className="rounded-full border border-bg-elevated px-3 py-1">SKU ID...</span>
      </div>
    </div>
  );
}
