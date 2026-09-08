<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { mass, num, money } from '$lib/format';

	const coords: Record<string, [number, number]> = {
		Chicago: [150, 160],
		Detroit: [190, 430],
		Columbus: [455, 475],
		Indianapolis: [410, 225],
		'R-Chicago': [760, 145],
		'R-Ohio': [935, 410],
		'M-Detroit': [755, 475],
		'M-Indiana': [720, 285]
	};
	const collectionNames = ['Chicago', 'Detroit', 'Columbus', 'Indianapolis'];
	const facilityNames = ['R-Chicago', 'R-Ohio', 'M-Detroit', 'M-Indiana'];

	const rl = $derived($workbenchState.reference.phase567?.phase6?.reverse_logistics || {});
	const flows = $derived((rl.flows || []) as any[]);
	const opened = $derived(rl.opened_facilities || {});
	const maxFlow = $derived(Math.max(1, ...flows.map((f: any) => Number(f.kg))));

	const kpis = $derived.by(() => [
		['Collected', mass(rl.collected_kg)],
		['Processed', mass(rl.processed_kg)],
		['Disposed', mass(rl.disposed_kg)],
		['Network CO₂e', mass(rl.total_kgco2e)]
	]);

	function throughputFor(name: string) {
		return flows.filter((f: any) => f.facility === name).reduce((a: number, b: any) => a + Number(b.kg), 0);
	}

	function edgePath(a: [number, number], b: [number, number]) {
		return `M${a[0]} ${a[1]} C${(a[0] + b[0]) / 2} ${a[1]},${(a[0] + b[0]) / 2} ${b[1]},${b[0]} ${b[1]}`;
	}

	const topFlows = $derived([...flows].sort((a: any, b: any) => b.kg - a.kg).slice(0, 8));
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">REVERSE NETWORK / FACILITY LOCATION</p>
			<h1>Where recovery capacity sits changes where material can go.</h1>
		</div>
		<p>Collection balance, reman eligibility, facility opening, throughput capacity and disposal limits are solved together.</p>
	</div>
	<div class="network-layout">
		<div class="panel">
			<svg viewBox="0 0 1080 570">
				<defs>
					<marker id="netA" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">
						<path d="M0 0L0 6L9 3z" fill="#9be5bd" />
					</marker>
				</defs>
				{#each flows as f}
					{@const a = coords[f.collection]}
					{@const b = coords[f.facility]}
					{#if a && b}
						{@const w = 1.4 + (8 * Number(f.kg)) / maxFlow}
						<path
							class="network-edge {f.pathway === 'reman' ? 'reman' : ''}"
							marker-end="url(#netA)"
							style="stroke-width:{w}px"
							d={edgePath(a, b)}
						>
							<title>{f.collection} → {f.facility} {mass(f.kg)}</title>
						</path>
					{/if}
				{/each}
				{#each collectionNames as n}
					{@const [x, y] = coords[n]}
					<g>
						<circle class="network-node" cx={x} cy={y} r="27" />
						<text class="svg-label" x={x} y={y - 39}>{n}</text>
						<text class="svg-sub" x={x} y={y + 4}>COLLECT</text>
					</g>
				{/each}
				{#each facilityNames as n}
					{@const [x, y] = coords[n]}
					{@const o = Number(opened[n] || 0) === 1}
					<g>
						<rect class="network-facility {o ? 'open' : 'closed'}" x={x - 36} y={y - 27} width="72" height="54" rx="5" />
						<text class="svg-label" x={x} y={y - 39}>{n}</text>
						<text class="svg-sub" x={x} y={y + 4}>{o ? 'OPEN' : 'CLOSED'}</text>
					</g>
				{/each}
			</svg>
		</div>
		<aside class="panel network-side">
			<div class="stacked-kpis">
				{#each kpis as k}
					<div><small>{k[0]}</small><b>{k[1]}</b></div>
				{/each}
			</div>
			<div class="divider"></div>
			<div class="side-heading"><span>FACILITY DECISIONS</span><b>open / closed</b></div>
			<div class="facility-list">
				{#each facilityNames as n}
					{@const o = Number(opened[n] || 0) === 1}
					<div class="facility-row">
						<div><b>{n}</b><small>{mass(throughputFor(n))} routed</small></div>
						<span class="facility-state {o ? 'open' : 'closed'}">{o ? 'OPEN' : 'CLOSED'}</span>
					</div>
				{/each}
			</div>
		</aside>
	</div>
	<div class="panel table-panel">
		<div class="panel-label">DOMINANT RECOVERY FLOWS</div>
		<table class="data-table">
			<thead>
				<tr><th>COLLECTION</th><th>FACILITY</th><th>PATHWAY</th><th>MASS</th><th>DISTANCE</th><th>TRANSPORT COST</th></tr>
			</thead>
			<tbody>
				{#each topFlows as f}
					<tr>
						<td>{f.collection}</td>
						<td><strong>{f.facility}</strong></td>
						<td><span class="tag">{String(f.pathway).toUpperCase()}</span></td>
						<td>{mass(f.kg)}</td>
						<td>{num(f.distance_km, 1)} km</td>
						<td>{money(f.transport_cost)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</section>
