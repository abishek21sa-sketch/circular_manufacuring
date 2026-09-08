// Formatting helpers ported 1:1 from web/src/app.ts so every view shows the
// same numbers in the same shape as the legacy Studio (money/mass/pct/num).

export function money(v: number | undefined | null): string {
	const n = Number(v || 0);
	if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
	if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(1)}k`;
	return `$${n.toFixed(0)}`;
}

export function mass(v: number | undefined | null): string {
	const n = Number(v || 0);
	if (Math.abs(n) >= 1e6) return `${(n / 1e6).toFixed(2)}M kg`;
	if (Math.abs(n) >= 1000) return `${(n / 1000).toFixed(1)} t`;
	return `${n.toFixed(0)} kg`;
}

export function pct(v: number | undefined | null): string {
	return `${(Number(v || 0) * 100).toFixed(1)}%`;
}

export function num(v: number | undefined | null, d = 1): string {
	return Number(v || 0).toFixed(d);
}

export function clamp(x: number, a: number, b: number): number {
	return Math.max(a, Math.min(b, x));
}

export function titleCase(s: string | undefined | null): string {
	return String(s ?? '')
		.replaceAll('_', ' ')
		.toUpperCase();
}

export function spaced(s: string | undefined | null): string {
	return String(s ?? '').replaceAll('_', ' ');
}
