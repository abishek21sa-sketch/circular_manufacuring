<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { mass, money, num, clamp } from '$lib/format';

	const coords: Record<string, [number, number]> = {
		'North-Collector': [480, 125],
		'West-Collector': [200, 285],
		'South-Collector': [410, 510],
		'East-Collector': [760, 355],
		'Northeast-Collector': [620, 100],
		'Southwest-Collector': [190, 490]
	};
	const depot: [number, number] = [470, 330];
	const colors = ['#9be5bd', '#ff9568', '#d7f56f', '#8fc8d8', '#c8a6ff', '#f1c27d'];

	const r = $derived($workbenchState.wb.coupled_routing || {});
	const routeList = $derived((r.routes || []) as string[][]);

	function segments(route: string[]) {
		const pts = route.map((name) => (name.includes('hub') ? depot : coords[name])).filter(Boolean) as [number, number][];
		const out: { x1: number; y1: number; x2: number; y2: number }[] = [];
		for (let i = 0; i < pts.length - 1; i++) {
			out.push({ x1: pts[i][0], y1: pts[i][1], x2: pts[i + 1][0], y2: pts[i + 1][1] });
		}
		return out;
	}
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">AI-COUPLED EXACT CVRP</p>
			<h1>The return forecast becomes pickup demand.</h1>
		</div>
		<p>V1.2 converts the predicted EOL return state into a representative collection batch, then solves exact capacity-feasible tours.</p>
	</div>
	<div class="route-layout-v12">
		<div class="panel">
			<svg viewBox="0 0 980 620">
				{#each routeList as route, ri}
					{#each segments(route) as s}
						<line x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} style="stroke:{colors[ri % colors.length]};stroke-width:3;opacity:.8" />
					{/each}
				{/each}
				<circle class="route-depot" cx={depot[0]} cy={depot[1]} r="25" />
				<text class="route-label" x={depot[0]} y={depot[1] - 38}>{r.routing_input?.primary_hub || 'hub'}</text>
				<text class="route-pickup" x={depot[0]} y={depot[1] + 4}>DEPOT</text>
				{#each Object.entries(coords) as [name, xy]}
					{@const q = r.routing_input?.customer_pickups_kg?.[name] || 0}
					<circle class="route-node" cx={xy[0]} cy={xy[1]} r="22" />
					<text class="route-label" x={xy[0]} y={xy[1] - 34}>{name.replace('-Collector', '')}</text>
					<text class="route-pickup" x={xy[0]} y={xy[1] + 4}>{mass(q)}</text>
				{/each}
			</svg>
		</div>
		<aside class="panel route-side">
			<p class="eyebrow">COUPLED ROUTING SOLUTION</p>
			<div class="policy-kpis">
				<div><small>Vehicles</small><b>{r.vehicles_used}</b></div>
				<div><small>Distance</small><b>{num(r.total_distance_km, 1)} km</b></div>
				<div><small>Route cost</small><b>{money(r.objective_cost)}</b></div>
				<div><small>GHG</small><b>{num(r.total_kgco2e, 1)} kgCO₂e</b></div>
			</div>
			<p style="color:var(--muted);font-size:10px;line-height:1.5;margin-top:14px">{r.routing_input?.source_contract || ''}</p>
			<div class="divider"></div>
			<div class="side-heading"><span>TOURS</span><b>{r.vehicles_used} exact tours</b></div>
			{#each routeList as route, i}
				{@const load = r.route_loads_kg?.[i] || 0}
				<div class="tour-card">
					<strong>TOUR {i + 1} · {mass(load)}</strong>
					<p>{route.map((x) => x.replace('-Collector', '')).join(' → ')} · {num(r.route_distances_km?.[i], 1)} km</p>
					<div class="capacity-track"><i style="width:{clamp((load / 40000) * 100, 0, 100)}%"></i></div>
				</div>
			{/each}
		</aside>
	</div>
</section>
