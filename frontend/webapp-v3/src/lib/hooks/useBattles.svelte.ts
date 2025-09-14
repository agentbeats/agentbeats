import { battlesStore } from '$lib/stores/battles.store';
import { battlesService } from '$lib/services/battles.service';
import type { Battle } from '$lib/types';

/**
 * Svelte 5 Runes-based useBattles hook
 * 
 * Usage in components:
 * 
 * <script>
 *   const battles = useBattles();
 *   
 *   // Reactive values - automatically update when data changes
 *   $effect(() => {
 *     console.log('Battles changed:', battles.data);
 *   });
 *   
 *   // Load data
 *   battles.loadBattles();
 * </script>
 * 
 * {#if battles.isLoading}Loading...{/if}
 * {#each battles.ongoingBattles as battle}...{/each}
 */
export function useBattles() {
  // Reactive state synced with battles store
  const state = $state({
    data: [] as Battle[],
    isLoading: false,
    error: null as string | null,
    wsConnected: false
  });

  // Computed values that automatically update when data changes
  const ongoingBattles = $derived(
    state.data.filter(battle => 
      ['pending', 'queued', 'running'].includes(battle.state?.toLowerCase() || '')
    )
  );
  
  const pastBattles = $derived(
    state.data.filter(battle => 
      ['finished', 'error'].includes(battle.state?.toLowerCase() || '')
    )
  );

  // Sync with battles store
  $effect(() => {
    const unsubscribe = battlesStore.subscribe(storeState => {
      state.data = storeState.battles;
      state.isLoading = storeState.isLoading;
      state.error = storeState.error;
      state.wsConnected = storeState.wsConnected;
    });
    return unsubscribe;
  });

  // Action methods
  const loadBattles = async () => {
    await battlesStore.loadBattles();
  };

  const getBattleById = async (battleId: string) => {
    const result = await battlesService.getBattleById(battleId);
    return result.success ? result.data : null;
  };

  const startBattle = async (battleData: any) => {
    const result = await battlesService.createBattle(battleData);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to create battle');
    }
    return result.data;
  };

  const updateBattle = async (battleId: string, update: any) => {
    const result = await battlesService.updateBattle(battleId, update);
    if (!result.success) {
      throw new Error(result.error || 'Failed to update battle');
    }
    return result.data;
  };

  const getAgentBattlesLast24Hours = async (agentId: string) => {
    const result = await battlesService.getAgentBattlesLast24Hours(agentId);
    return result.success ? result.data : [];
  };

  const connectWebSocket = () => {
    battlesStore.connectWebSocket();
  };

  const disconnectWebSocket = () => {
    battlesStore.disconnectWebSocket();
  };

  const refresh = () => loadBattles();

  return {
    // Reactive state - using getters to ensure current values
    get data() { return state.data; },
    get isLoading() { return state.isLoading; },
    get error() { return state.error; },
    get wsConnected() { return state.wsConnected; },
    
    // Computed values - using getters
    get ongoingBattles() { return ongoingBattles; },
    get pastBattles() { return pastBattles; },
    
    // Actions
    loadBattles,
    getBattleById,
    startBattle,
    updateBattle,
    getAgentBattlesLast24Hours,
    connectWebSocket,
    disconnectWebSocket,
    refresh,
    
    // Cleanup is handled automatically by $effect
  };
}