<script lang="ts">
	import { onMount } from 'svelte';
	import { workbenchState } from '$lib/workbench';
	import { getPublicReferenceSummary } from '$lib/api';

	const models = $derived(($workbenchState.wb.math_inventory || []) as any[]);
	const boundaries = $derived(($workbenchState.wb.known_model_boundaries || []) as string[]);

	let publicRef: any = $state(null);
	let publicRefError: string | null = $state(null);

	onMount(() => {
		getPublicReferenceSummary()
			.then((s) => (publicRef = s))
			.catch((e) => (publicRefError = e?.message || String(e)));
	});

	const topStates = $derived(
		(Object.entries(publicRef?.top_states_by_record_count || {}) as [string, number][]).slice(0, 8)
	);
	const topSectors = $derived(
		(Object.entries(publicRef?.top_sectors_by_record_count || {}) as [string, number][]).slice(0, 8)
	);
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">ENGINEERING EVIDENCE</p>
			<h1>The math should be visible enough to interrogate.</h1>
		</div>
		<p>Model size, solver class, verification route, integration status and known boundaries are exposed here instead of buried in documentation.</p>
	</div>
	<div class="evidence-grid-v12">
		<div class="panel">
			<div class="panel-label">MATHEMATICAL MODEL INVENTORY</div>
			<div class="math-row header">
				<span>MODEL</span><span>ROLE</span><span>VARS</span><span>CONSTRAINTS</span><span>SOLVER</span><span>VERIFICATION</span>
			</div>
			{#each models as m}
				<div class="math-row">
					<b>{m.model}</b>
					<span>{m.role}</span>
					<strong>{m.variables}{m.integer_variables ? ` / ${m.integer_variables} int` : ''}</strong>
					<strong>{m.constraints}{m.objectives ? ` / ${m.objectives} obj` : ''}</strong>
					<span>{m.solver}</span>
					<p>{m.verification}</p>
				</div>
			{/each}
		</div>
		<aside class="panel evidence-side">
			<div class="side-heading"><span>KNOWN MODEL BOUNDARIES</span><b>not hidden</b></div>
			<div>
				{#each boundaries as b, i}
					<div class="boundary"><b style="color:var(--orange);margin-right:8px">0{i + 1}</b>{b}</div>
				{/each}
			</div>
			<div class="divider"></div>
			<div class="side-heading"><span>ACCEPTANCE STATE</span><b>Windows + locked core</b></div>
			<div class="evidence-callout good">Phase 1–10 computational core accepted on Windows.</div>
			<div class="evidence-callout good">Licensed Gurobi hierarchical multi-objective pass accepted.</div>
			<div class="evidence-callout pending">External lifecycle calibration and realized operational benefits remain pending.</div>
		</aside>
		<div class="panel span-full">
			<div class="panel-label">PUBLIC REFERENCE DATA — EPA GHGRP FACILITY EMISSIONS</div>
			{#if publicRefError}
				<div class="public-ref-body"><div class="evidence-callout pending">Public reference data unavailable: {publicRefError}</div></div>
			{:else if publicRef}
				<div class="public-ref-body">
					<div class="public-ref-stats">
						<div class="public-ref-stat"><span>REPORTING YEAR</span><b>{publicRef.reporting_year}</b></div>
						<div class="public-ref-stat"><span>FACILITIES</span><b>{Number(publicRef.record_count || 0).toLocaleString()}</b></div>
						<div class="public-ref-stat"><span>TOTAL REPORTED DIRECT EMISSIONS</span><b>{(Number(publicRef.total_reported_direct_emissions_mtco2e || 0) / 1e6).toFixed(1)}M t CO2e</b></div>
						<div class="public-ref-stat"><span>RETRIEVED</span><b>{String(publicRef.retrieved_at_utc || '').slice(0, 10)}</b></div>
					</div>
					<div class="public-ref-columns">
						<div>
							<div class="side-heading"><span>TOP STATES BY FACILITY COUNT</span></div>
							<div class="public-ref-list">
								{#each topStates as [k, v]}
									<div class="public-ref-row"><span>{k}</span><b>{v}</b></div>
								{/each}
							</div>
						</div>
						<div>
							<div class="side-heading"><span>TOP SECTORS BY FACILITY COUNT</span></div>
							<div class="public-ref-list">
								{#each topSectors as [k, v]}
									<div class="public-ref-row"><span>{k}</span><b>{v}</b></div>
								{/each}
							</div>
						</div>
					</div>
					<div class="public-ref-note">{publicRef.evidence?.source_name} — {publicRef.evidence?.evidence_class}. {publicRef.evidence?.claim_boundary}</div>
				</div>
			{:else}
				<div class="public-ref-body"><div class="evidence-callout">Loading public reference data…</div></div>
			{/if}
		</div>
	</div>
</section>
