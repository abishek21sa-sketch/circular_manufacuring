<script lang="ts">
	import { workbenchState } from '$lib/workbench';

	const models = $derived(($workbenchState.wb.math_inventory || []) as any[]);
	const boundaries = $derived(($workbenchState.wb.known_model_boundaries || []) as string[]);
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
	</div>
</section>
