import { writable } from 'svelte/store';

export interface CartItem {
  agent: any;
  type: 'green' | 'opponent';
}

function createCartStore() {
  const { subscribe, set, update } = writable<CartItem[]>([]);

  return {
    subscribe,
    addItem: (item: CartItem) => {
      update(items => {
        // If adding a green agent, replace any existing green agent
        if (item.type === 'green') {
          // Remove existing green agent
          const filteredItems = items.filter(existingItem => existingItem.type !== 'green');
          return [...filteredItems, item];
        }
        
        // For opponent agents, check if the exact same agent is already in cart (prevent duplicates)
        const exists = items.some(existingItem => {
          const existingId = existingItem.agent.agent_id || existingItem.agent.id;
          const newId = item.agent.agent_id || item.agent.id;
          return existingId === newId;
        });
        
        if (exists) {
          return items; // Don't add the same agent twice
        }
        
        return [...items, item];
      });
    },
    removeItem: (index: number) => {
      update(items => items.filter((_, i) => i !== index));
    },
    reorderItems: (newItems: CartItem[]) => {
      set(newItems);
    },
    clearCart: () => set([]),
    getGreenAgent: () => {
      let items: CartItem[] = [];
      subscribe(value => items = value)();
      return items.find(item => item.type === 'green');
    },
    getOpponentAgents: () => {
      let items: CartItem[] = [];
      subscribe(value => items = value)();
      return items.filter(item => item.type === 'opponent');
    },
    addBattleWithRequirements: (greenAgent: any, opponents: Array<{ name: string; agent_id: string }>) => {
      update(items => {
        // Clear existing items
        const newItems: CartItem[] = [];
        
        // Add green agent
        newItems.push({
          type: 'green',
          agent: greenAgent
        });
        
        // Add opponent agents
        opponents.forEach(opponent => {
          newItems.push({
            type: 'opponent',
            agent: {
              agent_id: opponent.agent_id,
              register_info: { alias: opponent.name },
              agent_card: { name: opponent.name, description: 'Opponent from past battle' }
            }
          });
        });
        
        return newItems;
      });
    }
  };
}

export const cartStore = createCartStore(); 