import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const res = await fetch('/api/battles');
		const rawData = await res.json();
		return { battles: rawData };
	} catch (error) {
		console.error('Failed to fetch battles:', error);
		return { battles: [] };
	}
}; 