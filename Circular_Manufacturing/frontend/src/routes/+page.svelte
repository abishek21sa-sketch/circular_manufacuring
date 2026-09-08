<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	// The legacy Studio opened on the MATERIALS tab by default. A client-side
	// redirect (rather than a load()-time `redirect()`) keeps this route a
	// plain prerenderable static page -- see +layout.ts for why every route
	// here is prerendered.
	onMount(() => {
		goto('/materials', { replaceState: true });
	});
</script>

<section class="view">
	<p style="color:var(--muted)">Opening MATERIALS…</p>
</section>
