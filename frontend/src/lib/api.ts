const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';
export const APP_STATE_CHANGED_EVENT = 'opptra:state-changed';

export function emitAppStateChanged(detail?: Record<string, unknown>) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent(APP_STATE_CHANGED_EVENT, { detail }));
}

export async function getPortfolioSummary() {
  const res = await fetch(`${API_BASE}/api/portfolio/summary`);
  if (!res.ok) throw new Error('Failed to fetch portfolio summary');
  return res.json();
}

export async function getLatestRun() {
  const res = await fetch(`${API_BASE}/api/queue/runs/latest`);
  if (!res.ok) throw new Error('Failed to fetch latest run');
  return res.json();
}

export async function runQueue() {
  const res = await fetch(`${API_BASE}/api/queue/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start queue run');
  return res.json();
}

export async function getRunStatus(runId: string) {
  const res = await fetch(`${API_BASE}/api/queue/runs/${runId}/status`);
  if (!res.ok) throw new Error('Failed to fetch run status');
  return res.json();
}

export async function getSkuDetail(skuId: string) {
  const res = await fetch(`${API_BASE}/api/sku/${skuId}`);
  if (!res.ok) throw new Error('Failed to fetch SKU detail');
  return res.json();
}

export async function postDecision(payload: any) {
  const res = await fetch(`${API_BASE}/api/decisions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to post decision');
  const data = await res.json();
  emitAppStateChanged({ type: 'decision-posted', skuId: payload?.sku_id });
  return data;
}

export async function getDecisionLog(params: Record<string, string> = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/api/decisions?${query}`);
  if (!res.ok) throw new Error('Failed to fetch decisions');
  return res.json();
}

export async function getPortfolioSynthesis() {
  const res = await fetch(`${API_BASE}/api/portfolio/synthesis`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to fetch portfolio synthesis');
  return res.json();
}
