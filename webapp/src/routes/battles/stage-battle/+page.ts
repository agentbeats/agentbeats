import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  try {
    console.log('[stage-battle/+page.ts] Loading agents for battle staging...');
    const res = await fetch('/api/agents');
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch agents');
    }
    const agents = await res.json();
    console.log('[stage-battle/+page.ts] Loaded agents:', agents);
    
    // Filter agents by type for easier selection
    const greenAgents = agents.filter((agent: any) => agent.register_info.is_green);
    const opponentAgents = agents.filter((agent: any) => !agent.register_info.is_green);
    
    return {
      agents,
      greenAgents,
      opponentAgents
    };
  } catch (error) {
    console.error('[stage-battle/+page.ts] Error loading agents:', error);
    return {
      agents: [] as any[],
      greenAgents: [] as any[],
      opponentAgents: [] as any[]
    };
  }
}; 