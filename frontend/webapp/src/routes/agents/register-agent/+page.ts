import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
  try {
    console.log('[register-agent/+page.ts] Loading agents for reference...');
    const res = await fetch('/api/agents');
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || 'Failed to fetch agents');
    }
    const agents = await res.json();
    console.log('[register-agent/+page.ts] Loaded agents:', agents);
    
    return {
      agents
    };
  } catch (error) {
    console.error('[register-agent/+page.ts] Error loading agents:', error);
    return {
      agents: [] as any[]
    };
  }
}; 