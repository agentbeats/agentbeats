import { derived } from 'svelte/store';
import { agentsStore, greenAgents, opponentAgents, topAgents } from '$lib/stores/agents.store';
import { agentsService } from '$lib/services/agents.service';
import type { UseAgentsReturn, Agent } from '$lib/types';

/**
 * Hook for managing agents data and operations
 * Provides centralized access to agents state and actions
 */
export function useAgents(): UseAgentsReturn {
  // Derived store that combines all agent data and computed values
  const agentsData = derived(
    [agentsStore, greenAgents, opponentAgents, topAgents],
    ([$agentsStore, $greenAgents, $opponentAgents, $topAgents]) => ({
      agents: $agentsStore.agents,
      greenAgents: $greenAgents,
      opponentAgents: $opponentAgents,
      topAgents: $topAgents,
      isLoading: $agentsStore.isLoading,
      error: $agentsStore.error,
      lastUpdated: $agentsStore.lastUpdated
    })
  );

  // Actions
  const refresh = async (): Promise<void> => {
    await agentsStore.loadAgents({ scope: 'mine', checkLiveness: true });
  };

  const loadMyAgents = async (): Promise<void> => {
    await agentsStore.loadAgents({ scope: 'mine', checkLiveness: false });
  };

  const loadMyAgentsWithLiveness = async (
    updateCallback?: (agents: Agent[]) => void
  ): Promise<void> => {
    await agentsStore.loadAgentsWithAsyncLiveness(
      { scope: 'mine' },
      updateCallback
    );
  };

  const loadAllAgents = async (): Promise<void> => {
    await agentsStore.loadAgents({ scope: 'all', checkLiveness: false });
  };

  const loadAllAgentsWithLiveness = async (
    updateCallback?: (agents: Agent[]) => void
  ): Promise<void> => {
    await agentsStore.loadAgentsWithAsyncLiveness(
      { scope: 'all' },
      updateCallback
    );
  };

  const deleteAgent = async (agentId: string): Promise<void> => {
    const success = await agentsStore.deleteAgent(agentId);
    if (!success) {
      throw new Error('Failed to delete agent');
    }
  };

  const registerAgent = async (registerInfo: any): Promise<Agent> => {
    const result = await agentsService.registerAgent(registerInfo);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to register agent');
    }
    
    // Add the new agent to the store
    agentsStore.addAgent(result.data);
    return result.data;
  };

  const updateAgent = async (agentId: string, updates: Partial<Agent>): Promise<void> => {
    const result = await agentsService.updateAgent(agentId, updates);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to update agent');
    }
    
    // Update the agent in the store
    agentsStore.updateAgent(agentId, updates);
  };

  const getAgentById = async (agentId: string): Promise<Agent | null> => {
    try {
      const result = await agentsService.getAgentById(agentId);
      if (result.success && result.data) {
        return result.data;
      }
      return null;
    } catch (error) {
      console.error('Failed to get agent by ID:', error);
      return null;
    }
  };

  // Return the hook interface
  return {
    // Reactive data - use derived store for automatic reactivity
    subscribe: agentsData.subscribe,
    
    // Computed getters that work with current state
    get agents() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.agents || [];
    },
    
    get greenAgents() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.greenAgents || [];
    },
    
    get opponentAgents() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.opponentAgents || [];
    },
    
    get topAgents() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.topAgents || [];
    },
    
    get isLoading() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.isLoading || false;
    },
    
    get error() {
      let current: any;
      agentsData.subscribe(value => current = value)();
      return current?.error || null;
    },

    // Actions
    refresh,
    loadMyAgents,
    loadMyAgentsWithLiveness,
    loadAllAgents,
    loadAllAgentsWithLiveness,
    deleteAgent,
    registerAgent,
    updateAgent,
    getAgentById
  };
}