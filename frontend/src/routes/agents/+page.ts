import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const res = await fetch('http://nuggets.puppy9.com:9000/agents');
		const rawData = await res.json();
		return { agents: rawData };
	} catch (error) {
		console.error('Failed to fetch agents:', error);
		return { agents: [] };
	}
}; 