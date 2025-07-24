import { error } from '@sveltejs/kit';
import { getAgentById } from '$lib/api/agents';

export const load = async ({ params }: { params: { agent_id: string } }) => {
  try {
    const agentId = params.agent_id;
    if (!agentId) {
      throw error(400, 'Agent ID is required');
    }

    console.log(`[agents/[agent_id]/+page.ts] Loading agent: ${agentId}`);
    const agent = await getAgentById(agentId);
    
    if (!agent) {
      throw error(404, 'Agent not found');
    }

    console.log(`[agents/[agent_id]/+page.ts] Loaded agent:`, agent);
    
    return {
      agent
    };
  } catch (err) {
    console.error(`[agents/[agent_id]/+page.ts] Error loading agent:`, err);
    
    if (err instanceof Error && err.message.includes('404')) {
      throw error(404, 'Agent not found');
    }
    
    throw error(500, 'Failed to load agent');
  }
}; 