import { derived } from 'svelte/store';
import { battlesStore, ongoingBattles, pastBattles } from '$lib/stores/battles.store';
import { battlesService } from '$lib/services/battles.service';
import type { UseBattlesReturn, Battle } from '$lib/types';

/**
 * Hook for managing battles data and operations
 * Provides centralized access to battles state, WebSocket connection, and actions
 */
export function useBattles(): UseBattlesReturn {
  // Derived store that combines all battle data and computed values
  const battlesData = derived(
    [battlesStore, ongoingBattles, pastBattles],
    ([$battlesStore, $ongoingBattles, $pastBattles]) => ({
      battles: $battlesStore.battles,
      ongoingBattles: $ongoingBattles,
      pastBattles: $pastBattles,
      isLoading: $battlesStore.isLoading,
      error: $battlesStore.error,
      lastUpdated: $battlesStore.lastUpdated,
      wsConnected: $battlesStore.wsConnected
    })
  );

  // Actions
  const refresh = async (): Promise<void> => {
    await battlesStore.loadBattles();
  };

  const loadBattles = async (userId?: string): Promise<void> => {
    await battlesStore.loadBattles(userId);
  };

  const loadMyBattles = async (userId: string): Promise<void> => {
    await battlesStore.loadBattles(userId);
  };

  const createBattle = async (battleInfo: any): Promise<Battle> => {
    const result = await battlesStore.createBattle(battleInfo);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to create battle');
    }
    return result.data;
  };

  const startBattle = async (battleInfo: any): Promise<Battle> => {
    // Alias for createBattle with stage-battle specific logic
    const battleData = {
      green_agent_id: battleInfo.green_agent_id,
      opponents: battleInfo.opponents,
      config: {
        battle_timeout: battleInfo.battle_timeout || 300
      }
    };
    
    return await createBattle(battleData);
  };

  const updateBattle = async (battleId: string, updates: any): Promise<Battle> => {
    const result = await battlesService.updateBattle(battleId, updates);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to update battle');
    }
    
    // Update the battle in the store
    battlesStore.updateBattle(result.data);
    return result.data;
  };

  const getBattleById = async (battleId: string): Promise<Battle> => {
    const result = await battlesService.getBattleById(battleId);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to get battle');
    }
    return result.data;
  };

  const getAgentBattlesLast24Hours = async (agentId: string): Promise<Battle[]> => {
    const result = await battlesService.getAgentBattlesLast24Hours(agentId);
    if (!result.success || !result.data) {
      throw new Error(result.error || 'Failed to get agent battles');
    }
    return result.data;
  };

  const connectWebSocket = (): void => {
    battlesStore.connectWebSocket();
  };

  const disconnectWebSocket = (): void => {
    battlesStore.disconnectWebSocket();
  };

  // Filter helpers
  const filterOngoingBattles = (battles: Battle[]): Battle[] => {
    return battlesService.getOngoingBattles(battles);
  };

  const filterFinishedBattles = (battles: Battle[]): Battle[] => {
    return battlesService.getFinishedBattles(battles);
  };

  const sortBattlesByDate = (battles: Battle[], ascending = false): Battle[] => {
    return battlesService.sortBattlesByDate(battles, ascending);
  };

  // Return the hook interface
  return {
    // Reactive data - use derived store for automatic reactivity
    subscribe: battlesData.subscribe,
    
    // Computed getters that work with current state
    get battles() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.battles || [];
    },
    
    get ongoingBattles() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.ongoingBattles || [];
    },
    
    get pastBattles() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.pastBattles || [];
    },
    
    get isLoading() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.isLoading || false;
    },
    
    get error() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.error || null;
    },
    
    get wsConnected() {
      let current: any;
      battlesData.subscribe(value => current = value)();
      return current?.wsConnected || false;
    },

    // Actions
    refresh,
    loadBattles,
    loadMyBattles,
    createBattle,
    startBattle,
    updateBattle,
    getBattleById,
    getAgentBattlesLast24Hours,
    connectWebSocket,
    disconnectWebSocket,
    
    // Filter helpers
    filterOngoingBattles,
    filterFinishedBattles,
    sortBattlesByDate
  };
}