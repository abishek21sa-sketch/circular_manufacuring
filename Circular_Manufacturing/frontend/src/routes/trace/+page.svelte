<script lang="ts">
	import { workbenchState } from '$lib/workbench';

	const summaryMap: Record<string, string> = {
		DemandForecaster: 'Forecast monthly battery demand.',
		ReturnHazardModel: 'Estimate probability-weighted EOL returns.',
		ScrapPredictor: 'Estimate manufacturing scrap fraction.',
		RecoveryPathwayClassifier: 'Estimate second-life / reman / recycle / disposal shares.',
		ScenarioBridge: 'Convert predictions into correlated uncertain futures.',
		TwoStageStochasticMILP: 'Choose first-stage recovery capacity with scenario recourse and CVaR.',
		CriticalMaterialPlanner: 'Optimize Li/Ni/Co/graphite recovered and virgin sourcing.',
		CVRP: 'Build exact capacity-feasible collection tours.',
		StrategicSensitivity: 'Stress decision levers and observe policy changes.',
		PolicyReplay: 'Replay fixed policies on unreduced futures.',
		DecisionEngine: 'Score feasible nondominated strategies and retain human approval.'
	};
	const traceSummary = (component: string) => summaryMap[component] || 'Computational decision stage.';

	const trace = $derived(($workbenchState.wb.decision_trace || []) as any[]);
	const contract = $derived(($workbenchState.wb.integration_contract || []) as any[]);

	let selected = $state(0);
	const step = $derived(trace[selected]);
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">DECISION PROVENANCE</p>
			<h1>Eleven stages, one readable chain.</h1>
		</div>
		<p>Select a stage to inspect its role, evidence class and output. Raw payloads are kept behind the inspector instead of squeezed into eleven columns.</p>
	</div>
	<div class="trace-layout-v12">
		<div class="panel trace-list">
			{#each trace as t, i}
				<div class="trace-step" class:active={i === selected} onclick={() => (selected = i)} role="button" tabindex="0" onkeydown={(e) => e.key === 'Enter' && (selected = i)}>
					<div class="num">{String(t.step).padStart(2, '0')}</div>
					<div><b>{t.component}</b><small>{traceSummary(t.component)}</small></div>
					<div class="trace-evidence">{t.evidence}</div>
				</div>
			{/each}
		</div>
		<aside class="panel trace-inspector">
			{#if step}
				<p class="eyebrow">STEP {String(step.step).padStart(2, '0')} · {step.evidence}</p>
				<h2>{step.component}</h2>
				<p>{traceSummary(step.component)}</p>
				<div class="inspector-grid">
					<div><small>Evidence class</small><b>{step.evidence}</b></div>
					<div><small>Unit</small><b>{step.unit}</b></div>
				</div>
				<div class="trace-output"><pre>{JSON.stringify(step.output, null, 2)}</pre></div>
			{/if}
		</aside>
	</div>
	<div class="panel integration-panel">
		<div class="panel-label">COUPLING CONTRACT</div>
		{#each contract as r}
			<div class="integration-row">
				<b>{r.from}</b><span class="arrow">→</span><b>{r.to}</b><span class="integration-status">{r.status}</span>
				<p>{r.detail}</p>
			</div>
		{/each}
	</div>
</section>
