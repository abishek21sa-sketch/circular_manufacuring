// Typed client for the circular_battery Python backend (src/circular_battery/web/server.py).
// Every endpoint here is used by the legacy web/src/app.ts bundle this frontend
// replaces -- see docs/API.md for the full V1 contract.
//
// The base URL is configurable so the same build can point at a local
// `python scripts/run_workbench.py` (default) or the deployed Render backend
// once VITE_API_BASE is set in Vercel's project settings.

export type AnyObj = Record<string, any>;

const RAW_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765';
export const API_BASE = RAW_BASE.replace(/\/+$/, '');

function url(path: string): string {
	return `${API_BASE}${path}`;
}

/** Legacy (unenveloped) Phase API + /api/optimize: parses JSON, throws on !ok. */
export async function fetchJSON<T = AnyObj>(path: string, options?: RequestInit): Promise<T> {
	const r = await fetch(url(path), options);
	const payload = await r.json();
	if (!r.ok) {
		throw new Error(payload?.error?.message || payload?.error || `HTTP ${r.status}`);
	}
	return payload as T;
}

/** V1 enveloped API ({ ok, data, ... }): unwraps `data`. */
export async function fetchV1<T = AnyObj>(path: string, options?: RequestInit): Promise<T> {
	const payload = await fetchJSON<AnyObj>(path, options);
	return (payload?.data ?? payload) as T;
}

const jsonPost = (body: unknown): RequestInit => ({
	method: 'POST',
	headers: { 'Content-Type': 'application/json' },
	body: JSON.stringify(body)
});

// ---- Reference / workbench (boot payload for every tab) ----
export const getWorkbench = () => fetchV1<AnyObj>('/api/v1/workbench');
export const getReference = () => fetchJSON<AnyObj>('/api/reference');

// ---- Strategy tab: quick deterministic re-solve ----
export interface OptimizeRequest {
	scenario: { collection_rate: number; recycle_yield: number };
	carbon_price_per_kg: number;
}
export const postOptimize = (body: OptimizeRequest) => fetchJSON<AnyObj>('/api/optimize', jsonPost(body));

// ---- Circular-mass signature workspace ----
export const getCircularMassReference = () => fetchV1<AnyObj>('/api/v1/circular-mass/reference');
export interface CircularMassRequest {
	min_recycled_content: number;
	risk_aversion: number;
	max_virgin_share: number;
}
export const postCircularMassDecision = (body: CircularMassRequest) =>
	fetchV1<AnyObj>('/api/v1/circular-mass/decision', jsonPost(body));

// ---- Enterprise run registry ----
export const listRuns = (limit = 15) => fetchV1<AnyObj[]>(`/api/v1/runs?limit=${limit}`);
export const getRun = (runId: string) => fetchV1<AnyObj>(`/api/v1/runs/${encodeURIComponent(runId)}`);
export interface CreateRunRequest {
	name: string;
	seed: number;
	raw_n: number;
	reduced_k: number;
	include_sensitivity: boolean;
}
export const createRun = (body: CreateRunRequest) => fetchV1<AnyObj>('/api/v1/runs', jsonPost(body));
