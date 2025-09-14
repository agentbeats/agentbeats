import { writable, derived } from 'svelte/store';
import type { Agent, AgentsState, AgentFilters } from '$lib/types';
import { agentsService } from '$lib/services/agents.service';

const initialState: AgentsState = {
  agents: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {}
};

// Create the base store
const createAgentsStore = () => {
  const { subscribe, set, update } = writable<AgentsState>(initialState);

  return {
    subscribe,
    
    // Actions
    setLoading: (isLoading: boolean) => {
      update(state => ({ ...state, isLoading }));
    },

    setError: (error: string | null) => {
      update(state => ({ ...state, error }));
    },

    setAgents: (agents: Agent[]) => {
      update(state => ({
        ...state,
        agents,
        lastUpdated: new Date(),
        error: null
      }));
    },

    updateAgents: (updatedAgents: Agent[]) => {
      update(state => ({
        ...state,
        agents: updatedAgents,
        lastUpdated: new Date()
      }));
    },

    addAgent: (agent: Agent) => {
      update(state => ({
        ...state,
        agents: [...state.agents, agent],
        lastUpdated: new Date()
      }));
    },

    removeAgent: (agentId: string) => {
      update(state => ({
        ...state,
        agents: state.agents.filter(a => a.id !== agentId && a.agent_id !== agentId),
        lastUpdated: new Date()
      }));
    },

    updateAgent: (agentId: string, updates: Partial<Agent>) => {
      update(state => ({
        ...state,
        agents: state.agents.map(agent =>
          (agent.id === agentId || agent.agent_id === agentId)
            ? { ...agent, ...updates }
            : agent
        ),
        lastUpdated: new Date()
      }));
    },

    setFilters: (filters: AgentFilters) => {
      update(state => ({ ...state, filters }));
    },

    reset: () => {
      set(initialState);
    },

    // Async actions
    loadAgents: async (options: { scope?: 'all' | 'mine'; checkLiveness?: boolean } = {}) => {
      update(state => ({ ...state, isLoading: true, error: null }));
      
      const result = await agentsService.getAllAgents(options);
      
      if (result.success && result.data) {
        update(state => ({
          ...state,
          agents: result.data!,
          isLoading: false,
          lastUpdated: new Date(),
          error: null
        }));
      } else {
        update(state => ({
          ...state,
          isLoading: false,
          error: result.error || 'Failed to load agents'
        }));
      }
    },

    loadAgentsWithAsyncLiveness: async (
      options: { scope?: 'all' | 'mine' } = {},
      updateCallback?: (agents: Agent[]) => void
    ) => {
      update(state => ({ ...state, isLoading: true, error: null }));
      
      const result = await agentsService.getAgentsWithAsyncLiveness(
        options,
        (updatedAgents) => {
          update(state => ({
            ...state,
            agents: updatedAgents,
            lastUpdated: new Date()
          }));
          updateCallback?.(updatedAgents);
        }
      );
      
      if (result.success && result.data) {
        update(state => ({
          ...state,
          agents: result.data!,
          isLoading: false,
          lastUpdated: new Date(),
          error: null
        }));
      } else {
        update(state => ({
          ...state,
          isLoading: false,
          error: result.error || 'Failed to load agents with async liveness'
        }));
      }
    },

    deleteAgent: async (agentId: string) => {
      const result = await agentsService.deleteAgent(agentId);
      
      if (result.success) {
        update(state => ({
          ...state,
          agents: state.agents.filter(a => a.id !== agentId && a.agent_id !== agentId),
          lastUpdated: new Date()
        }));
      } else {
        update(state => ({
          ...state,
          error: result.error || 'Failed to delete agent'
        }));
      }
      
      return result.success;
    }
  };
};

export const agentsStore = createAgentsStore();

// Derived stores for convenient data access
export const greenAgents = derived(
  agentsStore,
  $agentsStore => $agentsStore.agents.filter(agent => agent.is_green === true)
);

export const opponentAgents = derived(
  agentsStore,
  $agentsStore => $agentsStore.agents.filter(agent => agent.is_green === false)
);

export const topAgents = derived(
  agentsStore,
  $agentsStore => {
    return $agentsStore.agents
      .sort((a, b) => {
        // Sort by ELO rating first, then by win rate, with fallback for agents without ratings
        const aRating = a.elo?.rating || 0;
        const bRating = b.elo?.rating || 0;
        const eloDiff = bRating - aRating;
        if (eloDiff !== 0) return eloDiff;
        
        const aWinRate = a.elo?.stats?.win_rate || 0;
        const bWinRate = b.elo?.stats?.win_rate || 0;
        const winRateDiff = bWinRate - aWinRate;
        if (winRateDiff !== 0) return winRateDiff;
        
        // Fallback to creation date (newer first)
        const aTime = new Date(a.created_at || 0).getTime();
        const bTime = new Date(b.created_at || 0).getTime();
        return bTime - aTime;
      })
      .slice(0, 6);
  }
);

export const liveAgents = derived(
  agentsStore,
  $agentsStore => $agentsStore.agents.filter(agent => agent.live === true)
);

export const filteredAgents = derived(
  [agentsStore],
  ([$agentsStore]) => {
    let filtered = $agentsStore.agents;
    const { filters } = $agentsStore;
    
    if (filters.isGreen !== undefined) {
      filtered = filtered.filter(agent => agent.is_green === filters.isGreen);
    }
    
    if (filters.isLive !== undefined) {
      filtered = filtered.filter(agent => agent.live === filters.isLive);
    }
    
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(agent =>
        agent.alias?.toLowerCase().includes(searchLower) ||
        agent.agent_card?.name?.toLowerCase().includes(searchLower) ||
        agent.agent_card?.description?.toLowerCase().includes(searchLower)
      );
    }
    
    return filtered;
  }
);