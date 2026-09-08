<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { ensureWorkbenchLoaded, workbenchState } from '$lib/workbench';
	import { titleCase, pct, money } from '$lib/format';

	let { children } = $props();

	const tabs: { href: string; label: string }[] = [
		{ href: '/materials', label: 'MATERIALS' },
		{ href: '/network', label: 'NETWORK' },
		{ href: '/plan', label: 'PLAN' },
		{ href: '/strategy', label: 'STRATEGY' },
		{ href: '/routes', label: 'ROUTES' },
		{ href: '/ai', label: 'AI' },
		{ href: '/risk', label: 'RISK' },
		{ href: '/circular-mass', label: 'CIRCULAR-MASS' },
		{ href: '/trace', label: 'TRACE' },
		{ href: '/runs', label: 'RUNS' },
		{ href: '/evidence', label: 'EVIDENCE' }
	];

	onMount(() => {
		ensureWorkbenchLoaded().catch(() => {
			/* surfaced via workbenchState.error below */
		});
	});

	const ribbon = $derived.by(() => {
		const wb = $workbenchState.wb ?? {};
		const d = wb.decision || {};
		const chosen = wb.chosen_stochastic_policy || {};
		const plan = wb.coupled_planning?.solution || {};
		const cm = wb.coupled_critical_materials || {};
		return [
			{ label: 'Recommended policy', value: titleCase(d.recommended_policy || '—'), primary: true },
			{ label: 'Decision confidence', value: pct(d.confidence) },
			{ label: 'Expected total cost', value: money(chosen.expected_total_cost) },
			{ label: 'CVaR operating cost', value: money(chosen.cvar_operating_cost) },
			{ label: 'Coupled plan service', value: pct(plan.service_level) },
			{ label: 'Critical recovered share', value: pct(cm.recovered_share) }
		];
	});
</script>

<div id="app-shell">
	<header class="topbar">
		<div class="brand-block">
			<span class="brand-mark">CM</span>
			<div><strong>Material Circularity Studio</strong><small>closed-loop battery decision intelligence</small></div>
		</div>
		<nav class="tabs" aria-label="Studio modes">
			{#each tabs as tab}
				<a
					class="tab"
					class:active={$page.url.pathname.startsWith(tab.href)}
					href={tab.href}
					data-sveltekit-preload-data="hover"
				>
					{tab.label}
				</a>
			{/each}
		</nav>
		<div class="evidence-pill"><i></i>SYNTHETIC VALIDATION</div>
	</header>

	{#if $workbenchState.error}
		<div class="error" style="padding:12px 28px;background:#2a1715">{$workbenchState.error}</div>
	{:else if !$workbenchState.loaded}
		<div class="global-ribbon" style="display:flex;align-items:center;color:var(--muted);font-size:11px;padding:0 28px">
			Loading the coupled workbench…
		</div>
	{:else}
		<div class="global-ribbon">
			{#each ribbon as cell}
				<div class="ribbon-cell" class:primary={cell.primary}><span>{cell.label}</span><b>{cell.value}</b></div>
			{/each}
		</div>
	{/if}

	<main>
		{#if $workbenchState.loaded}
			{@render children()}
		{:else if $workbenchState.error}
			<div class="view"><p class="error">Could not reach the backend at the configured VITE_API_BASE. {$workbenchState.error}</p></div>
		{:else}
			<div class="view"><p style="color:var(--muted)">Loading…</p></div>
		{/if}
	</main>
</div>

<style>
	a.tab {
		text-decoration: none;
		display: flex;
		align-items: center;
	}
</style>
