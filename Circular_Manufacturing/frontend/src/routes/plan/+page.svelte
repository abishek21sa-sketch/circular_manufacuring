<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { money, mass, pct, num } from '$lib/format';

	const plan = $derived($workbenchState.wb.coupled_planning?.solution || {});
	const rows = $derived((plan.period_rows || []) as any[]);
	const sc = $derived($workbenchState.wb.coupled_planning?.scenario || {});
	const ie = $derived($workbenchState.wb.coupled_planning?.ie_metrics || {});

	const summary = $derived.by(() => [
		['Service', pct(plan.service_level)],
		['Recycled content', pct(plan.recycled_content_rate)],
		['Virgin input', mass(plan.total_virgin_kg)],
		['Recovered use', mass(plan.total_recovered_use_kg)],
		['Overtime', `${num(plan.total_overtime_packs, 0)} packs`],
		['Constraint residual', Number(plan.max_constraint_violation || 0).toExponential(1)]
	]);

	const maxDemand = $derived(Math.max(1, ...rows.map((r: any) => r.demand_packs)));

	const metrics = $derived.by(() => [
		['Aggregate capacity util.', pct(ie.aggregate_capacity_utilization)],
		['Regular capacity util.', pct(ie.regular_capacity_utilization)],
		['Overtime share', pct(ie.overtime_share)],
		['Virgin dependency', pct(ie.virgin_material_dependency)],
		['Demand source', 'AI → OR bridge']
	]);
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">COUPLED IE PRODUCTION PLAN</p>
			<h1>Recovery supply now feeds the production plan that follows it.</h1>
		</div>
		<p>V1.2 couples AI-derived demand and stochastic recovery output into regular capacity, safety stock, recovered inventory and virgin substitution.</p>
	</div>
	<div class="metric-strip top-strip">
		{#each summary as s}
			<div><small>{s[0]}</small><b>{s[1]}</b></div>
		{/each}
	</div>
	<div class="period-grid">
		{#each rows as r, i}
			<article class="period-card">
				<div class="period-card-head">
					<div><span>P{r.period}</span><b>{num(r.demand_packs, 0)} demand</b></div>
					<small>{pct(r.regular_capacity_utilization)} regular util.</small>
				</div>
				<div class="bar-group">
					<div class="bar-row">
						<span class="bar-row-label">Demand</span>
						<div class="bar-bg"><i style="width:{(100 * r.demand_packs) / maxDemand}%"></i></div>
						<b>{num(r.demand_packs, 0)}</b>
					</div>
					<div class="bar-row capacity">
						<span class="bar-row-label">Regular</span>
						<div class="bar-bg"><i style="width:{(100 * r.regular_packs) / maxDemand}%"></i></div>
						<b>{num(r.regular_packs, 0)}</b>
					</div>
					<div class="bar-row recovered">
						<span class="bar-row-label">Recovered</span>
						<div class="bar-bg"><i style="width:{100 * r.recycled_content_rate}%"></i></div>
						<b>{pct(r.recycled_content_rate)}</b>
					</div>
				</div>
				<div class="period-facts">
					<div><small>Virgin</small><b>{mass(r.virgin_kg)}</b></div>
					<div><small>Recovered</small><b>{mass(r.recovered_use_kg)}</b></div>
					<div><small>FG inventory</small><b>{num(r.closing_fg_inventory_packs, 0)} packs</b></div>
					<div><small>Recovery supply</small><b>{mass(sc.recovered_supply_kg?.[i] || 0)}</b></div>
				</div>
			</article>
		{/each}
	</div>
	<div class="panel planning-metrics">
		{#each metrics as m}
			<div><small>{m[0]}</small><b>{m[1]}</b></div>
		{/each}
	</div>
</section>
