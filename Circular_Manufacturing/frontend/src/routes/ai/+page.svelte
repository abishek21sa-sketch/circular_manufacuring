<script lang="ts">
	import { workbenchState } from '$lib/workbench';
	import { pct, clamp } from '$lib/format';

	type Spec = [string, string, string, string];
	const specs: Spec[] = [
		['demand', 'Demand forecast', 'MAE', 'mae'],
		['returns', 'EOL return hazard', 'Brier', 'brier'],
		['recovery', 'Recovery pathway', 'Macro-F1', 'macro_f1'],
		['scrap', 'Scrap-rate model', 'MAE', 'mae']
	];
	const lowerIsBetter = (key: string) => key !== 'recovery';

	const wb = $derived($workbenchState.wb);
	const ev = $derived(wb.ai_evidence || {});
	const xai = $derived(wb.ai_explainability || {});

	const cards = $derived.by(() =>
		specs.map(([k, title, label, key]) => {
			const e = ev[k] || {};
			const m = Number(e.metrics?.[key] || 0);
			const b = Number(e.baseline_metrics?.[key] || 0);
			const lower = lowerIsBetter(k);
			const improvement = lower ? (b ? 1 - m / b : 0) : b < 1 ? (m - b) / (1 - b) : 0;
			const score = lower ? clamp((1 - m / (b || 1)) * 100, 0, 100) : clamp(improvement * 100, 0, 100);
			const fmt = (x: number) => (k === 'demand' ? x.toFixed(1) : x.toFixed(4));
			return { k, title, label, m: fmt(m), b: fmt(b), score, evidenceClass: e.evidence_class || '' };
		})
	);

	const stateBars = $derived.by(() => {
		const vals: [string, number, string][] = [
			['Demand', Number(wb.bridge?.demand_prediction_packs || 0), ''],
			['Returns', Number(wb.bridge?.return_prediction_packs || 0), 'returns'],
			['Routed batch', Number(wb.coupled_routing?.routing_input?.collected_batch_kg || 0) / 400, 'recovered']
		];
		const max = Math.max(1, ...vals.map((v) => v[1]));
		return vals.map(([label, value, cls], i) => {
			const x = 100 + i * 215;
			const h = (210 * value) / max;
			return { label, value: Math.round(value), cls, x, h, y: 260 - h };
		});
	});

	const driverEntries = $derived.by(() => {
		const imp = xai.recovery?.feature_importance_permutation_macro_f1 || {};
		const entries = Object.entries(imp).sort((a: any, b: any) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 6);
		const maxImp = Math.max(0.0001, ...entries.map(([, v]: any) => Math.abs(Number(v))));
		return entries.map(([k, v]: any) => ({ k, v: Number(v), width: (100 * Math.abs(Number(v))) / maxImp }));
	});
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">PREDICTIVE LAYER</p>
			<h1>Four models earn the right to influence the decision.</h1>
		</div>
		<p>Held-out performance is shown against explicit baselines, with calibration/uncertainty and model-driver evidence beside it.</p>
	</div>
	<div class="ai-model-grid-v12">
		{#each cards as c}
			<article class="ai-card">
				<h3>{c.title}</h3>
				<div class="ai-score">{c.m} <small>{c.label}</small></div>
				<div class="comparison-track"><i style="width:{c.score}%"></i><em style="left:72%"></em></div>
				<p>Baseline {c.b} · held-out improvement signal {c.score.toFixed(1)}% · {c.evidenceClass}</p>
			</article>
		{/each}
	</div>
	<div class="ai-detail-grid">
		<div class="panel">
			<div class="panel-label">FORECAST / RETURN STATE</div>
			<svg viewBox="0 0 760 330">
				{#each stateBars as b}
					<rect class="ai-state-bar {b.cls}" x={b.x} y={b.y} width="105" height={b.h} />
					<text x={b.x + 52} y="285" fill="#9db0a5" font-size="10" text-anchor="middle">{b.label}</text>
					<text x={b.x + 52} y={b.y - 15} fill="#f0f4f1" font-size="16" text-anchor="middle">{b.value}</text>
				{/each}
			</svg>
		</div>
		<div class="panel" id="ai-explain-panel">
			<div class="panel-label">RECOVERY MODEL DRIVERS</div>
			<div class="xai-list">
				{#each driverEntries as d}
					<div class="xai-row">
						<span>{d.k.replaceAll('_', ' ')}</span>
						<div class="xai-track"><i style="width:{d.width}%"></i></div>
						<b>{d.v.toFixed(3)}</b>
					</div>
				{/each}
			</div>
			<div class="divider"></div>
			<div class="inspector-grid">
				<div><small>Demand interval coverage</small><b>{pct(xai.demand?.empirical_holdout_coverage || 0)}</b></div>
				<div><small>Return calibration ECE</small><b>{Number(xai.returns?.expected_calibration_error || 0).toFixed(4)}</b></div>
				<div>
					<small>Recovery confidence gap</small><b
						>{Number(xai.recovery?.mean_confidence_gap || xai.recovery?.confidence_gap || 0).toFixed(3)}</b
					>
				</div>
				<div><small>Scrap top driver</small><b>{Object.keys(xai.scrap?.feature_importance || {})[0] || '—'}</b></div>
			</div>
		</div>
	</div>
</section>
