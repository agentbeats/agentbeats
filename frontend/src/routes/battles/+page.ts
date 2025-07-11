import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	try {
		const res = await fetch('/api/battles');
		const rawData = await res.json();
		
		const battles = rawData.map((item: any) => ({
			id: item.id || 'Unknown Battle',
			green_agent: item.greenAgentId || 'Unknown Green Agent',
			red_agent: item.opponents?.[0] || 'Unknown Red Agent',
			blue_agent: item.opponents?.[1] || 'Unknown Blue Agent',
			status: item.state || item.result?.eventType || 'Unknown Status'
		}));
	
		return { battles };
	} catch (error) {
		console.error('Failed to fetch battles:', error);
		return { battles: [] };
	}
}; 