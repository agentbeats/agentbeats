<script lang="ts">
  import BattleTable from './battle-table.svelte';
  import { useBattles, useAgents } from "$lib/hooks";
  import { onMount, onDestroy } from 'svelte';
  import { fade } from 'svelte/transition';
  import { Spinner } from "$lib/components/ui/spinner";

  // Define the Battle type
  type Battle = {
    battle_id: string;
    green_agent_id: string;
    opponents: Array<{ name: string; agent_id: string }>;
    created_by: string;
    created_at: string;
    state: string;
    green_agent?: any;
    opponent_agents?: any[];
  };

  // Use the new hooks
  const battlesHook = useBattles();
  const agentsHook = useAgents();

  let processedBattles = $state<Battle[]>([]);
  let totalBattles = $state(0);
  let loadedCount = $state(0);

  // Get reactive data from the hooks
  let battles = $derived(battlesHook.data);
  let pastBattles = $derived(battlesHook.pastBattles);
  let loading = $derived(battlesHook.isLoading || agentsHook.isLoading);
  let error = $derived(battlesHook.error || agentsHook.error);
  let allAgents = $derived(agentsHook.data);

  // Debug logging
  console.log('🎯 PAST BATTLES PAGE LOADED! 🎯');

  // Helper function to find agent by ID from the cached agents
  function findAgentById(agentId: string): any | null {
    return allAgents.find(agent => agent.agent_id === agentId) || null;
  }

  async function loadAgentData(battle: any): Promise<Battle> {
    try {
      // Load green agent
      let greenAgent = null;
      if (battle.green_agent_id) {
        greenAgent = findAgentById(battle.green_agent_id);
        if (!greenAgent) {
          // Create placeholder green agent if not found
          greenAgent = {
            agent_id: battle.green_agent_id,
            alias: `Unknown Agent (${battle.green_agent_id.slice(0, 8)})`,
            agent_card: { name: `Unknown Agent`, description: 'Agent data unavailable' }
          };
        }
      }

      // Load opponent agents from cache
      let opponentAgents = [];
      if (battle.opponents && battle.opponents.length > 0) {
        for (const opponent of battle.opponents) {
          const agent = findAgentById(opponent.agent_id);
          if (agent) {
            opponentAgents.push({
              ...agent,
              role: opponent.name
            });
          } else {
            // Add placeholder for missing agent
            opponentAgents.push({
              agent_id: opponent.agent_id,
              alias: `Unknown ${opponent.name}`,
              agent_card: { name: `Unknown ${opponent.name}`, description: 'Agent data unavailable' },
              role: opponent.name
            });
          }
        }
      }

      return {
        battle_id: battle.battle_id,
        green_agent_id: battle.green_agent_id,
        opponents: battle.opponents || [],
        created_by: battle.created_by || 'N/A',
        created_at: battle.created_at,
        state: battle.state,
        green_agent: greenAgent,
        opponent_agents: opponentAgents
      };
    } catch (error) {
      console.error('Error loading agent data for battle:', error);
      return {
        battle_id: battle.battle_id,
        green_agent_id: battle.green_agent_id,
        opponents: battle.opponents || [],
        created_by: battle.created_by || 'N/A',
        created_at: battle.created_at,
        state: battle.state
      };
    }
  }

  // Process battles with agent data when both are available
  $effect(() => {
    if (pastBattles.length > 0 && allAgents.length > 0) {
      processBattles();
    }
  });

  async function processBattles() {
    try {
      console.log('Processing battles with agent data...');
      
      // Load agent data for all battles
      const battlesWithAgents = [];
      for (let i = 0; i < pastBattles.length; i++) {
        const battle = pastBattles[i];
        console.log(`Processing battle ${i + 1}/${pastBattles.length}: ${battle.battle_id}`);
        
        const battleWithAgents = await loadAgentData(battle);
        battlesWithAgents.push(battleWithAgents);
      }
      
      processedBattles = battlesWithAgents;
      totalBattles = pastBattles.length;
      loadedCount = totalBattles;
      console.log('Processed battles with agent data:', processedBattles.length);
    } catch (err) {
      console.error('Failed to process battles:', err);
    }
  }

  async function loadBattles() {
    try {
      console.log('Loading battles and agents...');
      
      // Load both battles and agents using hooks
      await Promise.all([
        battlesHook.loadBattles(),
        agentsHook.loadAllAgents()
      ]);
      
      console.log('Battles and agents loaded');
    } catch (err) {
      console.error('Failed to load battles:', err);
    }
  }



  onMount(() => {
    loadBattles();
  });

</script>

<div class="space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold mb-2">Past Battles</h1>
    <p class="text-gray-600">Browse and search completed battles</p>
    {#if totalBattles > 0}
      <p class="text-sm text-muted-foreground mt-2">
        Showing {totalBattles} battles
      </p>
    {/if}
  </div>
  
  {#if loading}
    <div class="flex flex-col items-center justify-center py-12">
      <Spinner size="lg" centered />
      <span class="text-lg mb-2">Loading battles...</span>
    </div>
  {:else if error}
    <div class="text-center py-12">
      <p class="text-red-600 mb-4">Error loading battles: {error}</p>
      <button onclick={loadBattles} class="btn-primary">Retry</button>
    </div>
  {:else if processedBattles && processedBattles.length > 0}
    <div in:fade={{ duration: 300 }} out:fade={{ duration: 200 }}>
      <BattleTable battles={processedBattles} />
    </div>
  {:else}
    <div class="text-center py-12">
      <p class="text-gray-600">No past battles found.</p>
    </div>
  {/if}
</div> 