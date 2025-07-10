import type { PageLoad } from './$types';
import { getAllAgents, type Agent } from '$lib/api/agents';

export const load: PageLoad = async () => {
  try {
    console.log('[register-agent/+page.ts] Loading agents for reference...');
    const agents = await getAllAgents();
    console.log('[register-agent/+page.ts] Loaded agents:', agents);
    
    return {
      agents
    };
  } catch (error) {
    console.error('[register-agent/+page.ts] Error loading agents:', error);
    return {
      agents: [] as Agent[]
    };
  }
}; 