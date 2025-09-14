import { writable, derived } from 'svelte/store';
import type { Battle, BattlesState, BattleFilters, WebSocketMessage } from '$lib/types';
import { battlesService } from '$lib/services/battles.service';

const initialState: BattlesState = {
  battles: [],
  ongoingBattles: [],
  pastBattles: [],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {},
  wsConnected: false
};

// Create the base store
const createBattlesStore = () => {
  const { subscribe, set, update } = writable<BattlesState>(initialState);
  let ws: WebSocket | null = null;

  const recalculateDerivedBattles = (battles: Battle[]) => {
    const ongoing = battlesService.getOngoingBattles(battles);
    const past = battlesService.getFinishedBattles(battles);
    
    // Sort ongoing by creation date (most recent first)
    const sortedOngoing = battlesService.sortBattlesByDate(ongoing, false);
    const sortedPast = battlesService.sortBattlesByDate(past, false);
    
    return {
      ongoingBattles: sortedOngoing,
      pastBattles: sortedPast
    };
  };

  const setupWebSocket = () => {
    if (typeof window === 'undefined') return;
    
    try {
      ws = new WebSocket(
        (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
        window.location.host +
        '/ws/battles'
      );

      ws.onopen = () => {
        update(state => ({ ...state, wsConnected: true }));
      };

      ws.onclose = () => {
        update(state => ({ ...state, wsConnected: false }));
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Connection error:', error);
        update(state => ({ ...state, wsConnected: false }));
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          update(state => {
            let newBattles = [...state.battles];
            
            if (message.type === 'battles_update' && message.battles) {
              newBattles = message.battles;
            } else if (message.type === 'battle_update' && message.battle) {
              const existingIndex = newBattles.findIndex(
                b => b.battle_id === message.battle!.battle_id
              );
              
              if (existingIndex !== -1) {
                newBattles[existingIndex] = message.battle;
              } else {
                newBattles = [message.battle, ...newBattles];
              }
            }
            
            const derived = recalculateDerivedBattles(newBattles);
            
            return {
              ...state,
              battles: newBattles,
              ...derived,
              lastUpdated: new Date()
            };
          });
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };
    } catch (error) {
      console.error('[WebSocket] Failed to create connection:', error);
    }
  };

  const closeWebSocket = () => {
    if (ws) {
      ws.close();
      ws = null;
      update(state => ({ ...state, wsConnected: false }));
    }
  };

  return {
    subscribe,
    
    // Actions
    setLoading: (isLoading: boolean) => {
      update(state => ({ ...state, isLoading }));
    },

    setError: (error: string | null) => {
      update(state => ({ ...state, error }));
    },

    setBattles: (battles: Battle[]) => {
      const derived = recalculateDerivedBattles(battles);
      update(state => ({
        ...state,
        battles,
        ...derived,
        lastUpdated: new Date(),
        error: null
      }));
    },

    updateBattle: (updatedBattle: Battle) => {
      update(state => {
        const newBattles = state.battles.map(battle =>
          battle.battle_id === updatedBattle.battle_id ? updatedBattle : battle
        );
        
        const derived = recalculateDerivedBattles(newBattles);
        
        return {
          ...state,
          battles: newBattles,
          ...derived,
          lastUpdated: new Date()
        };
      });
    },

    addBattle: (battle: Battle) => {
      update(state => {
        const newBattles = [battle, ...state.battles];
        const derived = recalculateDerivedBattles(newBattles);
        
        return {
          ...state,
          battles: newBattles,
          ...derived,
          lastUpdated: new Date()
        };
      });
    },

    setFilters: (filters: BattleFilters) => {
      update(state => ({ ...state, filters }));
    },

    reset: () => {
      closeWebSocket();
      set(initialState);
    },

    // WebSocket methods
    connectWebSocket: () => {
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        setupWebSocket();
      }
    },

    disconnectWebSocket: () => {
      closeWebSocket();
    },

    // Async actions
    loadBattles: async (userId?: string) => {
      update(state => ({ ...state, isLoading: true, error: null }));
      
      const result = await battlesService.getAllBattles(userId);
      
      if (result.success && result.data) {
        const derived = recalculateDerivedBattles(result.data);
        update(state => ({
          ...state,
          battles: result.data!,
          ...derived,
          isLoading: false,
          lastUpdated: new Date(),
          error: null
        }));
      } else {
        update(state => ({
          ...state,
          isLoading: false,
          error: result.error || 'Failed to load battles'
        }));
      }
    },

    createBattle: async (battleInfo: any) => {
      const result = await battlesService.createBattle(battleInfo);
      
      if (result.success && result.data) {
        update(state => {
          const newBattles = [result.data!, ...state.battles];
          const derived = recalculateDerivedBattles(newBattles);
          
          return {
            ...state,
            battles: newBattles,
            ...derived,
            lastUpdated: new Date()
          };
        });
      } else {
        update(state => ({
          ...state,
          error: result.error || 'Failed to create battle'
        }));
      }
      
      return result;
    }
  };
};

export const battlesStore = createBattlesStore();

// Derived stores for convenient data access
export const ongoingBattles = derived(
  battlesStore,
  $battlesStore => $battlesStore.ongoingBattles
);

export const pastBattles = derived(
  battlesStore,
  $battlesStore => $battlesStore.pastBattles
);

export const filteredBattles = derived(
  [battlesStore],
  ([$battlesStore]) => {
    let filtered = $battlesStore.battles;
    const { filters } = $battlesStore;
    
    if (filters.state && filters.state.length > 0) {
      filtered = filtered.filter(battle => filters.state!.includes(battle.state));
    }
    
    if (filters.agentId) {
      filtered = filtered.filter(battle =>
        battle.green_agent_id === filters.agentId ||
        battle.red_agent_id === filters.agentId ||
        battle.blue_agent_id === filters.agentId
      );
    }
    
    if (filters.scenario) {
      filtered = filtered.filter(battle =>
        battle.scenario?.toLowerCase().includes(filters.scenario!.toLowerCase())
      );
    }
    
    if (filters.dateRange) {
      filtered = filtered.filter(battle => {
        const battleDate = new Date(battle.created_at);
        return battleDate >= filters.dateRange!.from && battleDate <= filters.dateRange!.to;
      });
    }
    
    return filtered;
  }
);

// Cleanup when module is destroyed
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    battlesStore.disconnectWebSocket();
  });
}