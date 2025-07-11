import type { PageLoad } from './$types';
import { getAllAgents, type Agent } from '$lib/api/agents';

export const load: PageLoad = async () => {
  try {
    console.log('[stage-battle/+page.ts] Loading agents for battle staging...');
    const agents = await getAllAgents();
    console.log('[stage-battle/+page.ts] Loaded agents:', agents);
    
    // Filter agents by type for easier selection
    const greenAgents = agents.filter(agent => agent.register_info.is_green);
    const opponentAgents = agents.filter(agent => !agent.register_info.is_green);
    
    return {
      agents,
      greenAgents,
      opponentAgents
    };
  } catch (error) {
    console.error('[stage-battle/+page.ts] Error loading agents:', error);
    return {
      agents: [] as Agent[],
      greenAgents: [] as Agent[],
      opponentAgents: [] as Agent[]
    };
  }
}; 