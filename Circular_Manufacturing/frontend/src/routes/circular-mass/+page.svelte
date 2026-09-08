<script lang="ts">
	import { onMount } from 'svelte';
	import { getCircularMassReference, postCircularMassDecision, type AnyObj } from '$lib/api';
	import { money, mass, pct } from '$lib/format';

	let floor = $state(0.2);
	let riskAversion = $state(0.35);
	let maxVirgin = $state(0.72);
	let solving = $state(false);
	let statusMessage = $state('Loading the governed reference decision…');
	let blocked = $state(false);
	let reference = $state<AnyObj>({});
	let decision = $state<AnyObj>({});

	const solution = $derived(decision.solution || {});
	const kpis = $derived.by(() => [
		['Expected recovered', mass(solution.expected_recovered_kg)],
		['Recycled content', pct(solution.recycled_content_share)],
		['Expected shortage', mass(solution.expected_shortage_kg)],
		['CVaR shortage', mass(solution.cvar_shortage_kg)],
		['Objective', money(solution.objective)]
	]);
	const facilities = $derived((decision.facility_actions || []) as any[]);
	const checks = $derived(Object.entries(decision.checks || {}) as [string, boolean][]);
	const scenarios = $derived((reference.scenarios || []) as any[]);

	async function solve() {
		solving = true;
		try {
			decision = await postCircularMassDecision({
				min_recycled_content: floor,
				risk_aversion: riskAversion,
				max_virgin_share: maxVirgin
			});
			blocked = decision.decision_gate !== 'AUTHORIZED';
			statusMessage = '';
		} catch (e: any) {
			blocked = true;
			statusMessage = e.message;
		} finally {
			solving = false;
		}
	}

	onMount(async () => {
		try {
			reference = await getCircularMassReference();
			await solve();
		} catch (e: any) {
			blocked = true;
			statusMessage = e.message;
		}
	});
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">SIGNATURE DECISION WORKSPACE</p>
			<h1>CIRCULAR-MASS · traceable recovery before virgin fallback.</h1>
		</div>
		<p>Set the circularity policy, solve the stochastic mass-balance MILP, and inspect the evidence gate before any facility or sourcing recommendation is promoted.</p>
	</div>
	<div class="cmass-layout">
		<div class="panel cmass-main">
			<div class="panel-label">POLICY CONTROLS · ENGINEER REVIEW REQUIRED</div>
			<div class="cmass-controls">
				<label>Minimum recycled content <input type="number" min="0" max="0.75" step="0.05" bind:value={floor} /></label>
				<label>CVaR risk aversion <input type="number" min="0" max="2" step="0.05" bind:value={riskAversion} /></label>
				<label>Maximum virgin share <input type="number" min="0" max="1" step="0.05" bind:value={maxVirgin} /></label>
				<button disabled={solving} onclick={solve}>{solving ? 'SOLVING…' : 'SOLVE + GATE'}</button>
			</div>
			<div class="cmass-status" class:blocked>
				{#if statusMessage}
					{statusMessage}
				{:else}
					<strong>{decision.decision_id || '—'}</strong> · {decision.operator_message || ''}
				{/if}
			</div>
			<div class="cmass-kpis">
				{#each kpis as k}
					<div class="cmass-kpi"><small>{k[0]}</small><b>{k[1]}</b></div>
				{/each}
			</div>
			<div class="cmass-facility-grid">
				{#each facilities as f}
					<div class="cmass-facility" class:open={f.open}>
						<small>{f.open ? 'ACTIVE RECOVERY PATH' : 'NOT SELECTED'}</small>
						<h3>{f.facility}</h3>
						<b>{mass(f.route_kg)}</b>
						<p>{f.open ? 'Facility is used in the optimized first-stage recovery plan.' : 'No recovery mass routed through this option.'}</p>
					</div>
				{/each}
			</div>
		</div>
		<aside class="panel cmass-side">
			<div class="side-heading"><span>DECISION AUTHORIZATION</span><b>{decision.decision_gate || '—'}</b></div>
			<div>
				{#each checks as [k, v]}
					<div class="cmass-check"><span>{k.replaceAll('_', ' ')}</span><b class={v ? 'pass' : 'fail'}>{v ? 'PASS' : 'FAIL'}</b></div>
				{/each}
			</div>
			<div class="divider"></div>
			<div class="side-heading"><span>EVIDENCE BOUNDARY</span><b>bounded claims</b></div>
			<div>
				<div class="cmass-boundary-note">{decision.evidence?.class || ''}</div>
				<div class="cmass-boundary-note">{decision.tail_risk_note || ''}</div>
				<div class="cmass-boundary-note">
					Field calibration: <strong>{decision.evidence?.field_calibration || 'PENDING'}</strong><br />
					Realized operational benefits: <strong>{decision.evidence?.realized_operational_benefits || 'NOT CLAIMED'}</strong>
				</div>
				<div class="cmass-boundary-note">Human review required: <strong>{decision.human_review_required ? 'YES' : 'NO'}</strong></div>
			</div>
		</aside>
	</div>
	<div class="panel table-panel cmass-scenarios">
		<div class="panel-label">UNCERTAINTY SET · SCENARIO MASS BALANCE</div>
		<table class="data-table">
			<thead>
				<tr><th>SCENARIO</th><th>PROBABILITY</th><th>DEMAND</th><th>HYDRO YIELD</th><th>DIRECT YIELD</th><th>PYRO YIELD</th></tr>
			</thead>
			<tbody>
				{#each scenarios as s}
					<tr>
						<td><strong>{s.name}</strong></td>
						<td>{pct(s.probability)}</td>
						<td>{mass(s.demand_kg)}</td>
						{#each s.yields || [] as y}
							<td>{pct(y)}</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>
