import { agentsStore } from '$lib/stores/agents.store';
import { agentsService } from '$lib/services/agents.service';
import type { Agent } from '$lib/types';

/**
 * Svelte 5 Runes-based useAgents hook
 * 
 * Usage in components:
 * 
 * <script>
 *   const agents = useAgents();
 *   
 *   // Reactive values - automatically update when data changes
 *   $effect(() => {
 *     console.log('Agents changed:', agents.data);
 *   });
 *   
 *   // Load data
 *   agents.loadMyAgents();
 * </script>
 * 
 * {#if agents.isLoading}Loading...{/if}
 * {#each agents.data as agent}...{/each}
 */
export function useAgents() {
  // Reactive state synced with agents store
  const state = $state({
    data: [] as Agent[],
    isLoading: false,
    error: null as string | null
  });

  // Computed values that automatically update when data changes
  const greenAgents = $derived(state.data.filter(a => a.is_green));
  const opponentAgents = $derived(state.data.filter(a => !a.is_green));
  const topAgents = $derived(
    state.data
      .sort((a, b) => {
        const aRating = a.elo?.rating || 0;
        const bRating = b.elo?.rating || 0;
        return bRating - aRating;
      })
      .slice(0, 6)
  );

  // Sync with agents store
  $effect(() => {
    const unsubscribe = agentsStore.subscribe(storeState => {
      state.data = storeState.agents;
      state.isLoading = storeState.isLoading;
      state.error = storeState.error;
    });
    return unsubscribe;
  });

  // Action methods
  const loadMyAgents = async () => {
    await agentsStore.loadAgents({ scope: 'mine', checkLiveness: false });
  };

  const loadMyAgentsWithLiveness = async (callback?: (agents: Agent[]) => void) => {
    await agentsStore.loadAgentsWithAsyncLiveness({ scope: 'mine' }, callback);
  };

  const loadAllAgents = async () => {
    await agentsStore.loadAgents({ scope: 'all', checkLiveness: false });
  };

  const loadAllAgentsWithLiveness = async (callback?: (agents: Agent[]) => void) => {
    await agentsStore.loadAgentsWithAsyncLiveness({ scope: 'all' }, callback);
  };

  const deleteAgent = async (agentId: string) => {
    const success = await agentsStore.deleteAgent(agentId);
    if (!success) throw new Error('Failed to delete agent');
  };

  const registerAgent = async (registerInfo: any) => {
    const result = await agentsService.registerAgent(registerInfo);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to register agent');
    }
    agentsStore.addAgent(result.data);
    return result.data;
  };

  const getAgentById = async (agentId: string) => {
    const result = await agentsService.getAgentById(agentId);
    return result.success ? result.data : null;
  };

  const refresh = () => loadMyAgents();

  return {
    // Reactive state - using getters to ensure current values
    get data() { return state.data; },
    get isLoading() { return state.isLoading; },
    get error() { return state.error; },
    
    // Computed values - using getters
    get greenAgents() { return greenAgents; },
    get opponentAgents() { return opponentAgents; },
    get topAgents() { return topAgents; },
    
    // Actions
    loadMyAgents,
    loadMyAgentsWithLiveness,
    loadAllAgents,
    loadAllAgentsWithLiveness,
    deleteAgent,
    registerAgent,
    getAgentById,
    refresh,
  };
}