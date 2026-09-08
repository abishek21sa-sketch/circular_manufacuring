<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { money, mass, pct, spaced } from '$lib/format';

	const W = 1100,
		H = 520,
		L = 70,
		R = 30,
		T = 45,
		B = 65,
		BINS = 12;

	const policies = $derived(($workbenchState.wb.policy_replay || []) as any[]);

	let selectedRiskPolicy = $state('');
	$effect(() => {
		if (!selectedRiskPolicy && policies.length) selectedRiskPolicy = policies[0].policy;
	});

	const policy = $derived(policies.find((x: any) => x.policy === selectedRiskPolicy) || {});

	const histogram = $derived.by(() => {
		const rows = (policy.scenario_rows || []) as any[];
		const costs = rows.map((r) => Number(r.total_cost)).filter((x) => Number.isFinite(x));
		const probs = rows.map((r) => Number(r.probability || 0));
		if (!costs.length) return { bars: [], p90x: 0, min: 0, max: 1 };
		const min = Math.min(...costs);
		const max = Math.max(...costs);
		const counts = new Array(BINS).fill(0);
		costs.forEach((x, i) => {
			const b = Math.min(BINS - 1, Math.floor(((x - min) / (max - min || 1)) * BINS));
			counts[b] += probs[i] || 1 / costs.length;
		});
		const maxC = Math.max(0.001, ...counts);
		const p90 = Number(policy.p90_total_cost || 0);
		const xp = (x: number) => L + ((x - min) / (max - min || 1)) * (W - L - R);
		const bars = counts.map((c, i) => {
			const x = L + ((W - L - R) * i) / BINS + 4;
			const bw = (W - L - R) / BINS - 8;
			const bh = ((H - T - B) * c) / maxC;
			const center = min + ((max - min) * (i + 0.5)) / BINS;
			return { x, y: H - B - bh, bw, bh, label: i % 2 === 0 ? money(center) : '', tail: center >= p90 };
		});
		return { bars, p90x: xp(p90), min, max };
	});

	const stats = $derived.by(() => [
		['Expected cost', money(policy.expected_total_cost)],
		['P90 cost', money(policy.p90_total_cost)],
		['CVaR95', money(policy.cvar95_total_cost)],
		['Expected carbon', mass(policy.expected_carbon_kgco2e)],
		['Expected virgin', mass(policy.expected_virgin_kg)],
		['Service', pct(policy.expected_service_level)],
		['Emergency probability', pct(policy.emergency_recovery_probability)]
	]);
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">POLICY DIGITAL EXPERIMENTS</p>
			<h1>Tail risk should look like a distribution, not a wall of circles.</h1>
		</div>
		<p>Policies are replayed on the same unreduced futures. The distribution below exposes expected cost, P90 and CVaR95 directly.</p>
	</div>
	<div class="risk-layout-v12">
		<div class="panel risk-main">
			<div class="risk-toolbar">
				<div class="risk-tabs">
					{#each policies as p}
						<button
							class="risk-tab"
							class:active={p.policy === selectedRiskPolicy}
							onclick={() => (selectedRiskPolicy = p.policy)}>{spaced(p.policy)}</button
						>
					{/each}
				</div>
				<span class="risk-quantile"
					>tail threshold {money(policy.p90_total_cost)} · CVaR95 {money(policy.cvar95_total_cost)}</span
				>
			</div>
			<svg viewBox="0 0 {W} {H}">
				<line class="risk-axis" x1={L} y1={H - B} x2={W - R} y2={H - B} />
				{#each histogram.bars as bar}
					<rect class="hist-bar" class:tail={bar.tail} x={bar.x} y={bar.y} width={bar.bw} height={bar.bh} />
					<text class="risk-text" x={bar.x + bar.bw / 2} y={H - B + 18} text-anchor="middle">{bar.label}</text>
				{/each}
				<line class="risk-line" x1={histogram.p90x} y1={T} x2={histogram.p90x} y2={H - B} />
				<text class="risk-text" x={histogram.p90x + 5} y={T + 15}>P90 {money(policy.p90_total_cost)}</text>
				<text class="risk-text" x={L} y={H - 18}>SCENARIO TOTAL COST →</text>
			</svg>
		</div>
		<aside class="panel risk-side">
			<p class="eyebrow">{String(policy.policy || '').replaceAll('_', ' ').toUpperCase()}</p>
			<h2>Policy replay</h2>
			{#each stats as s}
				<div class="risk-stat"><span>{s[0]}</span><b>{s[1]}</b></div>
			{/each}
		</aside>
	</div>
	<div class="panel table-panel">
		<div class="panel-label">SAME-SCENARIO POLICY COMPARISON</div>
		<table class="data-table">
			<thead>
				<tr><th>POLICY</th><th>EXPECTED COST</th><th>P90</th><th>CVAR95</th><th>CARBON</th><th>VIRGIN</th><th>EMERGENCY</th></tr>
			</thead>
			<tbody>
				{#each policies as x}
					<tr>
						<td><strong>{spaced(x.policy)}</strong></td>
						<td>{money(x.expected_total_cost)}</td>
						<td>{money(x.p90_total_cost)}</td>
						<td>{money(x.cvar95_total_cost)}</td>
						<td>{mass(x.expected_carbon_kgco2e)}</td>
						<td>{mass(x.expected_virgin_kg)}</td>
						<td>{pct(x.emergency_recovery_probability)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>
