// @ts-nocheck
import type { PageLoad } from './$types';

export const load = async ({ fetch }: Parameters<PageLoad>[0]) => {
	try {
		const res = await fetch('http://localhost:3001/agents');
		const rawData = await res.json();
		
		const agents = rawData.map((item: any) => ({
			name: item.agentCard?.name || item.registerInfo?.name || 'Unknown Agent',
			trainer: item.registerInfo?.name || 'Unknown Trainer',
			elo: '9999', // Default ELO since it's not in the JSON
			type: item.registerInfo?.meta?.type || item.agentCard?.name?.toLowerCase() || 'unknown',
			description: item.agentCard?.description || 'No description available'
		}));

		console.log('Agents data:', agents);
		
		return { agents };
	} catch (error) {
		console.error('Failed to fetch agents:', error);
		return { agents: [] };
	}
}; 