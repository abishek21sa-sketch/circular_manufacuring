<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { money, mass, pct, spaced, clamp, num } from '$lib/format';
	import { postOptimize } from '$lib/api';

	const W = 1080,
		H = 560,
		L = 86,
		R = 35,
		T = 45,
		B = 72;

	const wb = $derived($workbenchState.wb);
	const pts = $derived((wb.frontier?.candidates || []) as any[]);
	const nondominatedNames = $derived(new Set((wb.frontier?.nondominated || []).map((x: any) => x.policy)));
	const isNondominated = (name: string) => nondominatedNames.has(name);
	const candidateByName = (name: string) => pts.find((x: any) => x.policy === name) || {};
	const stochasticValue = $derived(wb.stochastic_information_value || {});

	let selectedPolicy = $state('');
	$effect(() => {
		if (!selectedPolicy && pts.length) selectedPolicy = wb.decision?.recommended_policy || pts[0].policy;
	});

	const selected = $derived(candidateByName(selectedPolicy));
	const nondominated = $derived(isNondominated(selectedPolicy));

	const bounds = $derived.by(() => {
		if (!pts.length) return { xmin: 0, xmax: 1, ymin: 0, ymax: 1, cvarMin: 0, cvarMax: 1 };
		const xs = pts.map((p: any) => p.expected_total_cost);
		const ys = pts.map((p: any) => p.expected_carbon_kgco2e);
		const cvars = pts.map((p: any) => p.cvar_operating_cost);
		return {
			xmin: Math.min(...xs),
			xmax: Math.max(...xs),
			ymin: Math.min(...ys),
			ymax: Math.max(...ys),
			cvarMin: Math.min(...cvars),
			cvarMax: Math.max(...cvars)
		};
	});
	const xp = (x: number) => L + ((x - bounds.xmin) / (bounds.xmax - bounds.xmin || 1)) * (W - L - R);
	const yp = (y: number) => H - B - ((y - bounds.ymin) / (bounds.ymax - bounds.ymin || 1)) * (H - T - B);
	const gridLines = $derived.by(() => {
		const out: { x: number; xLabel: string; y: number; yLabel: string }[] = [];
		for (let i = 0; i <= 4; i++) {
			const x = L + ((W - L - R) * i) / 4;
			const val = bounds.xmin + ((bounds.xmax - bounds.xmin) * i) / 4;
			const y = T + ((H - T - B) * i) / 4;
			const yval = bounds.ymax - ((bounds.ymax - bounds.ymin) * i) / 4;
			out.push({ x, xLabel: money(val), y, yLabel: `${(yval / 1e6).toFixed(2)}M` });
		}
		return out;
	});

	function pointRadius(p: any) {
		const span = bounds.cvarMax - bounds.cvarMin || 1;
		return 7 + 8 * clamp((p.cvar_operating_cost - bounds.cvarMin) / span, 0, 1);
	}

	const actions = $derived.by(() => {
		const out: string[] = [];
		Object.entries(selected.open_facilities || {}).forEach(([k, v]) => {
			if (v) out.push(`Open ${k}`);
		});
		Object.entries(selected.expansion_units || {}).forEach(([k, v]) => {
			if (Number(v) > 0) out.push(`Add ${v} expansion unit(s) at ${k}`);
		});
		return out;
	});

	// Quick deterministic re-solve.
	let qCollection = $state(0.86);
	let qYield = $state(0.9);
	let qCarbon = $state(0.2);
	let solving = $state(false);
	let quickResult = $state('');
	let quickError = $state('');

	async function reSolve() {
		solving = true;
		quickError = '';
		try {
			const r = await postOptimize({
				scenario: { collection_rate: qCollection, recycle_yield: qYield },
				carbon_price_per_kg: qCarbon
			});
			quickResult = `OPTIMAL · ${money(r.solution.total_cost)} · ${mass(r.solution.virgin_kg)} virgin · ${pct(r.solution.recycled_content_rate)} recycled`;
		} catch (e: any) {
			quickError = e.message;
		} finally {
			solving = false;
		}
	}
</script>

<section class="view">
	<div class="strategy-layout">
		<div class="panel strategy-main">
			<div class="view-title embedded">
				<div>
					<p class="eyebrow">MULTI-OBJECTIVE POLICY SET</p>
					<h1>Every point has an economic, carbon, virgin and tail-risk price.</h1>
				</div>
				<p>All six explicit scalarization policies are shown. Nondominated points are highlighted; this is not presented as a continuous Pareto surface.</p>
			</div>
			<svg viewBox="0 0 {W} {H}">
				{#each gridLines as g}
					<line class="strategy-grid" x1={g.x} y1={T} x2={g.x} y2={H - B} />
					<text class="strategy-label" x={g.x} y={H - B + 22} text-anchor="middle">{g.xLabel}</text>
					<line class="strategy-grid" x1={L} y1={g.y} x2={W - R} y2={g.y} />
					<text class="strategy-label" x={L - 10} y={g.y + 3} text-anchor="end">{g.yLabel}</text>
				{/each}
				<line class="strategy-axis" x1={L} y1={H - B} x2={W - R} y2={H - B} />
				<line class="strategy-axis" x1={L} y1={T} x2={L} y2={H - B} />
				<text class="strategy-axis-label" x={(L + W - R) / 2} y={H - 18} text-anchor="middle">EXPECTED TOTAL COST</text>
				<text
					class="strategy-axis-label"
					transform="translate(22 {(T + H - B) / 2}) rotate(-90)"
					text-anchor="middle">EXPECTED CARBON (kg CO₂e)</text
				>
				{#each pts as p}
					<circle
						class="strategy-point"
						class:nd={isNondominated(p.policy)}
						class:selected={p.policy === selectedPolicy}
						role="button"
						tabindex="0"
						cx={xp(p.expected_total_cost)}
						cy={yp(p.expected_carbon_kgco2e)}
						r={pointRadius(p)}
						onclick={() => (selectedPolicy = p.policy)}
						onkeydown={(e) => e.key === 'Enter' && (selectedPolicy = p.policy)}
					>
						<title>{p.policy} · {money(p.expected_total_cost)} · {mass(p.expected_virgin_kg)} virgin</title>
					</circle>
					<text
						class="strategy-policy-label"
						x={xp(p.expected_total_cost)}
						y={yp(p.expected_carbon_kgco2e) - pointRadius(p) - 8}>{spaced(p.policy)}</text
					>
				{/each}
			</svg>
			<table class="data-table">
				<thead>
					<tr><th>POLICY</th><th>STATUS</th><th>COST</th><th>CARBON</th><th>VIRGIN</th><th>CVAR</th><th>SERVICE</th></tr>
				</thead>
				<tbody>
					{#each pts as p}
						<tr>
							<td><strong>{spaced(p.policy)}</strong></td>
							<td><span class="tag">{isNondominated(p.policy) ? 'NONDOMINATED' : 'FEASIBLE'}</span></td>
							<td>{money(p.expected_total_cost)}</td>
							<td>{mass(p.expected_carbon_kgco2e)}</td>
							<td>{mass(p.expected_virgin_kg)}</td>
							<td>{money(p.cvar_operating_cost)}</td>
							<td>{pct(p.expected_service_level)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<aside class="panel strategy-side">
			<p class="eyebrow">{nondominated ? 'NONDOMINATED POLICY' : 'FEASIBLE POLICY'}</p>
			<h2>{spaced(selected.policy || '')}</h2>
			<div class="policy-kpis">
				<div><small>Expected cost</small><b>{money(selected.expected_total_cost)}</b></div>
				<div><small>CVaR</small><b>{money(selected.cvar_operating_cost)}</b></div>
				<div><small>Carbon</small><b>{mass(selected.expected_carbon_kgco2e)} CO₂e</b></div>
				<div><small>Virgin</small><b>{mass(selected.expected_virgin_kg)}</b></div>
				<div><small>Service</small><b>{pct(selected.expected_service_level)}</b></div>
				<div>
					<small>N−1 reserve</small><b
						>{selected.settings?.n_minus_one_min_capacity_kg
							? mass(selected.settings.n_minus_one_min_capacity_kg)
							: 'OFF'}</b
					>
				</div>
			</div>
			<ul class="action-list">
				{#each actions as a}
					<li>{a}</li>
				{:else}
					<li>No facility activation required.</li>
				{/each}
			</ul>
			<div class="divider"></div>
			<div class="side-heading"><span>QUICK DETERMINISTIC RE-SOLVE</span><b>test one lever set</b></div>
			<div style="margin-top:12px">
				<label style="font-size:9px;color:var(--muted)"
					>Collection rate
					<input type="range" min=".60" max=".98" step=".01" bind:value={qCollection} style="width:100%;accent-color:var(--acid)" />
				</label>
				<label style="display:block;margin-top:10px;font-size:9px;color:var(--muted)"
					>Recycle yield
					<input type="range" min=".72" max=".98" step=".01" bind:value={qYield} style="width:100%;accent-color:var(--acid)" />
				</label>
				<label style="display:block;margin-top:10px;font-size:9px;color:var(--muted)"
					>Carbon price
					<input type="range" min="0" max="2" step=".1" bind:value={qCarbon} style="width:100%;accent-color:var(--acid)" />
				</label>
				<button
					disabled={solving}
					onclick={reSolve}
					style="margin-top:14px;width:100%;padding:10px;border:1px solid var(--acid);background:transparent;color:var(--acid);cursor:pointer;font-size:9px;letter-spacing:.08em"
				>
					{solving ? 'SOLVING…' : 'RE-SOLVE'}
				</button>
				<div style="margin-top:10px;color:var(--muted);font-size:10px;line-height:1.5">
					{#if quickError}<span class="error">{quickError}</span>{:else}{quickResult}{/if}
				</div>
			</div>
		</aside>
	</div>
	<div class="panel info-value-panel">
		<div class="panel-label">STOCHASTIC VALUE OF INFORMATION</div>
		<div class="stochastic-value-grid">
			<div class="value-card">
				<small>Risk-neutral stochastic program</small>
				<b>{money(stochasticValue.risk_neutral_stochastic_program_cost)}</b>
				<em>RP · optimize before uncertainty resolves</em>
			</div>
			<div class="value-card">
				<small>Expected-value policy in scenarios</small>
				<b>{money(stochasticValue.expected_result_of_expected_value_cost)}</b>
				<em>EEV · deterministic policy replayed</em>
			</div>
			<div class="value-card highlight">
				<small>Value of stochastic solution</small>
				<b>{money(stochasticValue.value_of_stochastic_solution)}</b>
				<em>{pct(stochasticValue.vss_percent_of_rp)} of RP cost</em>
			</div>
			<div class="value-card highlight">
				<small>Perfect-information ceiling</small>
				<b>{money(stochasticValue.expected_value_of_perfect_information)}</b>
				<em>EVPI · {pct(stochasticValue.evpi_percent_of_rp)} of RP cost</em>
			</div>
			<div class="value-explainer">
				<strong>Interpretation.</strong> VSS is the expected cost avoided by optimizing against the scenario distribution
				instead of using one average-future policy. EVPI is the maximum expected amount perfect advance information could
				be worth. {stochasticValue.scope || ''}
			</div>
		</div>
	</div>
</section>
