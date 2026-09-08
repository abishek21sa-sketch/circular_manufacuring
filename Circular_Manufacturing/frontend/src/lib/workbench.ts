// Shared boot state for the Studio: every tab in the legacy app read off the
// same two module-level objects (`wb`, `reference`) fetched once in boot().
// This store reproduces that -- one fetch, shared across every route -- rather
// than having each +page.svelte re-fetch the whole workbench independently.

import { writable } from 'svelte/store';
import { getReference, getWorkbench, type AnyObj } from './api';

export interface WorkbenchState {
	loading: boolean;
	loaded: boolean;
	error: string | null;
	wb: AnyObj;
	reference: AnyObj;
}

export const workbenchState = writable<WorkbenchState>({
	loading: false,
	loaded: false,
	error: null,
	wb: {},
	reference: {}
});

let inflight: Promise<void> | null = null;

/** Fetch /api/v1/workbench + /api/reference exactly once; safe to call from every page's onMount. */
export function ensureWorkbenchLoaded(): Promise<void> {
	if (inflight) return inflight;
	inflight = (async () => {
		workbenchState.update((s) => ({ ...s, loading: true, error: null }));
		try {
			const [wb, reference] = await Promise.all([getWorkbench(), getReference()]);
			workbenchState.set({ loading: false, loaded: true, error: null, wb, reference });
		} catch (e: any) {
			workbenchState.update((s) => ({ ...s, loading: false, error: e?.message || String(e) }));
			inflight = null; // allow retry
			throw e;
		}
	})();
	return inflight;
}

export function reloadWorkbench(): Promise<void> {
	inflight = null;
	return ensureWorkbenchLoaded();
}
