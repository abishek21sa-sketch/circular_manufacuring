<script lang="ts">
	import { onMount } from 'svelte';
	import { listRuns, getRun, createRun, type AnyObj } from '$lib/api';
	import { titleCase, pct, num } from '$lib/format';

	let name = $state('Portfolio decision experiment');
	let seed = $state(20260817);
	let rawN = $state(24);
	let reducedK = $state(4);
	let executing = $state(false);
	let runMessage = $state('Registry ready. No run launched in this browser session.');
	let runStatusError = $state(false);
	let runResult = $state<{ runId: string; status: string; policy: string; runtimeSeconds: string } | null>(null);

	let rows = $state<AnyObj[]>([]);
	let tableError = $state('');
	let selectedRunId = $state('');
	let report = $state<AnyObj | null>(null);
	let reportError = $state('');

	async function refreshRuns() {
		try {
			rows = await listRuns(15);
			tableError = '';
		} catch (e: any) {
			tableError = e.message;
		}
	}

	async function inspectRun(runId: string) {
		selectedRunId = runId;
		reportError = '';
		try {
			report = await getRun(runId);
		} catch (e: any) {
			reportError = e.message;
			report = null;
		}
	}

	async function executeRun() {
		executing = true;
		runStatusError = false;
		runResult = null;
		runMessage = 'Running the complete AI → stochastic OR → routing → replay → recommendation chain. Keep this tab open.';
		try {
			const r = await createRun({ name, seed, raw_n: rawN, reduced_k: reducedK, include_sensitivity: false });
			runResult = {
				runId: r.run_id,
				status: r.status,
				policy: titleCase(r.report?.decision?.recommended_policy || '—'),
				runtimeSeconds: num(r.runtime_seconds, 1)
			};
			await refreshRuns();
			await inspectRun(r.run_id);
		} catch (e: any) {
			runStatusError = true;
			runMessage = e.message;
		} finally {
			executing = false;
		}
	}

	onMount(refreshRuns);

	const decision = $derived(report?.report?.decision || {});
	const provenance = $derived(report?.report?.platform_run || {});
	const actions = $derived((decision.action || []) as string[]);
</script>

<section class="view">
	<div class="view-title">
		<div>
			<p class="eyebrow">ENTERPRISE RUN REGISTRY</p>
			<h1>A decision experiment should be rerunnable and inspectable.</h1>
		</div>
		<p>Run records preserve scenario configuration, runtime provenance, code fingerprint and decision hash. Full runs can take around a minute on the local Windows target.</p>
	</div>
	<div class="panel run-composer-v12">
		<label>Run name<input bind:value={name} /></label>
		<label>Seed<input type="number" bind:value={seed} /></label>
		<label>Raw futures<input type="number" min="20" max="500" bind:value={rawN} /></label>
		<label>Reduced<input type="number" min="3" max="40" bind:value={reducedK} /></label>
		<button disabled={executing} onclick={executeRun}>{executing ? 'EXECUTING…' : 'EXECUTE + REGISTER'}</button>
	</div>
	<div class="run-status-v12">
		{#if runStatusError}
			<span class="error">{runMessage}</span>
		{:else if runResult}
			REGISTERED <strong>{runResult.runId}</strong> · {runResult.status} · policy {runResult.policy} · {runResult.runtimeSeconds} s
		{:else}
			{runMessage}
		{/if}
	</div>
	<div class="panel table-panel">
		<div class="panel-label">PERSISTED RUNS · CLICK A ROW TO INSPECT</div>
		{#if tableError}
			<div class="error" style="padding:15px">{tableError}</div>
		{:else if rows.length}
			<table class="data-table">
				<thead>
					<tr><th>RUN</th><th>SCENARIO</th><th>STATUS</th><th>RUNTIME</th><th>DECISION HASH</th></tr>
				</thead>
				<tbody>
					{#each rows as r}
						<tr
							class="run-row-click"
							class:active={r.run_id === selectedRunId}
							onclick={() => inspectRun(r.run_id)}
						>
							<td><strong>{r.run_id}</strong></td>
							<td>{r.scenario_id || '—'}</td>
							<td><span class="tag">{r.status}</span></td>
							<td>{r.runtime_seconds == null ? '—' : num(r.runtime_seconds, 1) + ' s'}</td>
							<td>{r.decision_hash_sha256 ? String(r.decision_hash_sha256).slice(0, 18) + '…' : '—'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{:else}
			<div style="padding:18px;color:var(--muted);font-size:11px">No persisted runs yet.</div>
		{/if}
	</div>
	<div class="panel run-report-panel">
		<div class="panel-label">RUN REPORT</div>
		{#if reportError}
			<div class="error">{reportError}</div>
		{:else if !report}
			<div class="run-report-empty">Select a persisted run to inspect its scenario, decision, provenance and runtime evidence.</div>
		{:else}
			<div class="run-report-grid">
				<div><small>Run</small><b>{report.run_id}</b></div>
				<div><small>Scenario</small><b>{report.scenario_id || '—'}</b></div>
				<div><small>Policy</small><b>{titleCase(decision.recommended_policy || '—')}</b></div>
				<div><small>Confidence</small><b>{pct(decision.confidence || 0)}</b></div>
				<div><small>Runtime</small><b>{report.runtime_seconds == null ? '—' : num(report.runtime_seconds, 2) + ' s'}</b></div>
				<div>
					<small>Decision hash</small><b
						>{String(report.decision_hash_sha256 || '—').slice(0, 24)}{report.decision_hash_sha256 ? '…' : ''}</b
					>
				</div>
				<div>
					<small>Code fingerprint</small><b
						>{String(report.code_fingerprint_sha256 || provenance.code_fingerprint_sha256 || '—').slice(0, 24)}{report.code_fingerprint_sha256 ||
						provenance.code_fingerprint_sha256
							? '…'
							: ''}</b
					>
				</div>
				<div><small>Status</small><b>{report.status}</b></div>
			</div>
			<div class="run-report-actions">
				<div class="report-box">
					<h3>Decision actions</h3>
					<ul>
						{#each actions as a}
							<li>{a}</li>
						{:else}
							<li>No explicit facility action recorded.</li>
						{/each}
					</ul>
				</div>
				<div class="report-box">
					<h3>Runtime provenance</h3>
					<pre>{JSON.stringify(provenance.runtime_environment || {}, null, 2)}</pre>
				</div>
			</div>
		{/if}
	</div>
</section>
