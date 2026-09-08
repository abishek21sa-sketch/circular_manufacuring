// The Studio's data comes from a Python backend that may live on a different
// origin (Render) than this SvelteKit app (Vercel). There is no benefit to
// server-side rendering pages whose content is entirely fetched client-side
// after boot, and doing so would require the Vercel server function itself to
// reach the backend at build/request time. The whole app is a client-rendered
// SPA, same as the legacy web/src/app.ts bundle it replaces.
export const ssr = false;

// Every route here is a static path (no [param] segments) whose content is
// fetched client-side after mount, so it can be prerendered to a plain HTML
// shell at build time -- no route needs per-request server logic. That keeps
// the whole app as static output on Vercel with zero serverless functions,
// which also sidesteps adapter-vercel's function-symlink step (it fails with
// EPERM on Windows dev machines without Developer Mode / elevated symlink
// rights -- see the frontend README note in this repo's top-level README).
export const prerender = true;
