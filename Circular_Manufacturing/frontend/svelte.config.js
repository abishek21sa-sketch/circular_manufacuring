import adapter from '@sveltejs/adapter-vercel';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// Deploys to Vercel; the Python backend (circular_battery) stays on
		// Render. See README.md "Deployment" for the Render -> Vercel order.
		// `runtime` is pinned explicitly because adapter-vercel refuses to guess
		// a default when building locally on a Node version Vercel doesn't
		// offer yet (e.g. this repo's Node 24 dev machine) -- Vercel's own
		// build step ignores this mismatch and just uses the pinned runtime.
		adapter: adapter({ runtime: 'nodejs22.x' })
	}
};

export default config;
