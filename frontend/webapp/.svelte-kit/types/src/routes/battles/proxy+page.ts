// @ts-nocheck
import type { PageLoad } from './$types';

export const load = async ({ fetch }: Parameters<PageLoad>[0]) => {
	try {
		const res = await fetch('/api/battles');
		const rawData = await res.json();
		return { battles: rawData };
	} catch (error) {
		console.error('Failed to fetch battles:', error);
		return { battles: [] };
	}
}; 