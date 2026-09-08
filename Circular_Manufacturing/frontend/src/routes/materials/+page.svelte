<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { money, mass, pct, num, clamp } from '$lib/format';

	type Node = { id: string; x: number; y: number; r: number; title: string; sub: string };
	type Edge = { x1: number; y1: number; x2: number; y2: number; cls: 'return' | ''; label: string };

	let selected = $state('recovered');

	const nodes: Node[] = [
		{ id: 'virgin', x: 120, y: 245, r: 66, title: 'Virgin', sub: 'PRIMARY' },
		{ id: 'manufacturing', x: 340, y: 245, r: 78, title: 'Manufacturing', sub: 'PRODUCTION' },
		{ id: 'use', x: 570, y: 245, r: 64, title: 'Use', sub: 'COHORT' },
		{ id: 'returns', x: 790, y: 245, r: 66, title: 'Returns', sub: 'EOL' },
		{ id: 'recovery', x: 790, y: 420, r: 78, title: 'Recovery', sub: 'SORT / PROCESS' },
		{ id: 'recovered', x: 340, y: 420, r: 76, title: 'Recovered', sub: 'SECONDARY FEED' }
	];

	const p5 = $derived($workbenchState.reference.phase567?.phase5 || {});
	const plan = $derived($workbenchState.wb.coupled_planning?.solution || {});
	const wb = $derived($workbenchState.wb);

	const edges = $derived.by<Edge[]>(() => [
		{ x1: 186, y1: 245, x2: 260, y2: 245, cls: '', label: mass(plan.total_virgin_kg) },
		{
			x1: 418,
			y1: 245,
			x2: 506,
			y2: 245,
			cls: '',
			label: `${Math.round((plan.total_regular_packs || 0) + (plan.total_overtime_packs || 0))} packs`
		},
		{
			x1: 634,
			y1: 245,
			x2: 724,
			y2: 245,
			cls: 'return',
			label: `${Math.round(wb.bridge?.return_prediction_packs || 0)} forecast returns`
		},
		{ x1: 790, y1: 311, x2: 790, y2: 342, cls: 'return', label: 'collection + grading' },
		{ x1: 712, y1: 420, x2: 416, y2: 420, cls: '', label: mass(plan.total_recovered_use_kg) },
		{ x1: 340, y1: 344, x2: 340, y2: 323, cls: '', label: 'scrap recirculation' }
	]);

	const lookup = $derived.by(() => {
		const circ = p5.circularity_metrics || {};
		const chosen = wb.chosen_stochastic_policy || {};
		return {
			virgin: {
				title: 'Virgin material',
				text: 'Primary feed closes the material balance after recovered output, internal scrap recovery and inventory are applied.',
				facts: [
					['Expected virgin', mass(chosen.expected_virgin_kg)],
					['Plan virgin', mass(plan.total_virgin_kg)],
					[
						'Dependency',
						pct(
							plan.ie_metrics?.virgin_material_dependency ||
								plan.total_virgin_kg / (plan.total_virgin_kg + plan.total_recovered_use_kg || 1)
						)
					],
					['Evidence', 'OPTIMIZED']
				]
			},
			manufacturing: {
				title: 'Manufacturing',
				text: 'Production converts virgin and recovered material into battery packs while manufacturing scrap re-enters the circular feed contract.',
				facts: [
					['Pack mass', `${p5.design?.pack_mass_kg || 400} kg`],
					['Scrap rate', pct(p5.design?.manufacturing_scrap_rate || 0)],
					['Plan service', pct(plan.service_level)],
					['Evidence', 'IE + MATERIAL BALANCE']
				]
			},
			use: {
				title: 'Use cohort',
				text: 'Installed batteries create the future return pool. The return-hazard model translates cohort state into expected EOL feedstock.',
				facts: [
					['Demand forecast', `${Math.round(wb.bridge?.demand_prediction_packs || 0)} packs`],
					['Return forecast', `${Math.round(wb.bridge?.return_prediction_packs || 0)} packs`],
					['Second-life share', pct(wb.bridge?.derived_second_life_share || 0)],
					['Evidence', 'PREDICTED']
				]
			},
			returns: {
				title: 'End-of-life returns',
				text: 'Returns are filtered by collection and second-life allocation before becoming recovery-system feed.',
				facts: [
					['Base returns', mass(wb.bridge?.derived_base_returns_kg?.[0] || 0)],
					['Collection design', '87.0%'],
					['Routing batch', mass(wb.coupled_routing?.routing_input?.collected_batch_kg || 0)],
					['Evidence', 'PREDICTED → OPTIMIZED']
				]
			},
			recovery: {
				title: 'Recovery system',
				text: 'Facility activation, processing yields, reman eligibility, disposal policy and N−1 resilience constrain usable recovery output.',
				facts: [
					['Technical recovery', pct(circ.technical_recovery_rate || 0)],
					['Circular pathway', pct(circ.circular_pathway_rate || 0)],
					[
						'Open facilities',
						Object.entries(chosen.open_facilities || {})
							.filter(([, v]) => v)
							.map(([k]) => k)
							.join(', ') || '—'
					],
					['Evidence', 'OPTIMIZED']
				]
			},
			recovered: {
				title: 'Recovered feed',
				text: 'Expected recovery output and recovered manufacturing scrap become the material availability consumed by the coupled IE production plan.',
				facts: [
					['Recovered plan use', mass(plan.total_recovered_use_kg)],
					['Recycled content', pct(plan.recycled_content_rate)],
					['Critical recovered share', pct(wb.coupled_critical_materials?.recovered_share || 0)],
					['Evidence', 'COUPLED V1.2']
				]
			}
		} as Record<string, { title: string; text: string; facts: [string, string][] }>;
	});

	const current = $derived(lookup[selected] || lookup.recovered);
	const materials = $derived((p5.design?.materials || []).filter((m: any) => m.critical));

	const footer = $derived.by(() => {
		const circ = p5.circularity_metrics || {};
		return [
			['Material productivity', pct(circ.material_productivity)],
			['Collection efficiency', pct(circ.collection_efficiency)],
			['Technical recovery', pct(circ.technical_recovery_rate)],
			['Critical recovery', pct(circ.critical_material_recovery_rate)],
			['Plan recycled content', pct(plan.recycled_content_rate)],
			['Max balance residual', `${Number(p5.max_material_balance_error_kg || 0).toExponential(1)} kg`]
		];
	});
</script>

<section class="view">
	<div class="view-grid materials-grid">
		<div class="panel canvas-panel">
			<div class="view-title compact-title">
				<p class="eyebrow">CLOSED-LOOP MATERIAL SYSTEM</p>
				<h1>Trace the kilogram, not just the KPI.</h1>
				<p>Material states, recovery losses and virgin displacement are shown as one closed-loop engineering balance.</p>
			</div>
			<svg viewBox="0 0 1040 540" aria-label="Closed-loop material flow">
				<defs>
					<marker id="mArr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
						<path d="M0 0L0 6L9 3z" fill="#9be5bd" />
					</marker>
					<marker id="rArr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
						<path d="M0 0L0 6L9 3z" fill="#ff9568" />
					</marker>
				</defs>
				{#each edges as e}
					<path
						class="lifecycle-edge {e.cls}"
						marker-end="url(#{e.cls ? 'rArr' : 'mArr'})"
						d="M{e.x1} {e.y1}L{e.x2} {e.y2}"
					/>
					<text class="edge-label" x={(e.x1 + e.x2) / 2} y={(e.y1 + e.y2) / 2 - 12}>{e.label}</text>
				{/each}
				{#each nodes as n}
					<g
						class="lifecycle-node"
						class:active={selected === n.id}
						role="button"
						tabindex="0"
						onclick={() => (selected = n.id)}
						onkeydown={(ev) => ev.key === 'Enter' && (selected = n.id)}
					>
						<circle cx={n.x} cy={n.y} r={n.r} />
						<text class="node-title" x={n.x} y={n.y - 3}>{n.title}</text>
						<text class="node-sub" x={n.x} y={n.y + 17}>{n.sub}</text>
					</g>
				{/each}
			</svg>
		</div>
		<aside class="panel side-panel">
			<div class="side-heading"><span>STATE INSPECTOR</span><b>{current.title}</b></div>
			<div class="inspector-body">
				<p>{current.text}</p>
				<div class="inspector-grid">
					{#each current.facts as f}
						<div><small>{f[0]}</small><b>{f[1]}</b></div>
					{/each}
				</div>
			</div>
			<div class="divider"></div>
			<div class="side-heading"><span>CRITICAL MATERIAL LEDGER</span><b>usable secondary feed</b></div>
			<div class="material-ledger-v12">
				{#each materials as m}
					<div class="material-row-v12">
						<div><strong>{m.name.toUpperCase()}</strong><small>{num(m.kg_per_pack, 1)} kg/pack</small></div>
						<div class="yield-track"><i style="width:{clamp(Number(m.recycling_yield) * 100, 0, 100)}%"></i></div>
						<em>{pct(m.recycling_yield)}</em>
					</div>
				{/each}
			</div>
		</aside>
	</div>
	<div class="metric-strip">
		{#each footer as f}
			<div><small>{f[0]}</small><b>{f[1]}</b></div>
		{/each}
	</div>
</section>
