<script lang="ts">
  import BattleTable from './battle-table.svelte';
  import { getAllBattles } from "$lib/api/battles";
  import { getAgentById } from "$lib/api/agents";
  import { onMount, onDestroy } from 'svelte';

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

  let battles = $state<Battle[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);


  // Debug logging
  console.log('🎯 PAST BATTLES PAGE LOADED! 🎯');

  async function loadAgentData(battle: any): Promise<Battle> {
    try {
      // Load green agent
      let greenAgent = null;
      if (battle.green_agent_id) {
        try {
          greenAgent = await getAgentById(battle.green_agent_id);
        } catch (error) {
          console.error('Failed to load green agent:', error);
          // Create placeholder green agent
          greenAgent = {
            agent_id: battle.green_agent_id,
            register_info: { alias: `Unknown Agent (${battle.green_agent_id.slice(0, 8)})` },
            agent_card: { name: `Unknown Agent`, description: 'Agent data unavailable' }
          };
        }
      }

      // Load opponent agents
      let opponentAgents = [];
      if (battle.opponents && battle.opponents.length > 0) {
        for (const opponent of battle.opponents) {
          try {
            const agent = await getAgentById(opponent.agent_id);
            opponentAgents.push({
              ...agent,
              role: opponent.name
            });
          } catch (error) {
            console.error(`Failed to load opponent agent ${opponent.agent_id}:`, error);
            // Add placeholder for failed agent
            opponentAgents.push({
              agent_id: opponent.agent_id,
              register_info: { alias: `Unknown ${opponent.name}` },
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

  async function loadBattles() {
    try {
      loading = true;
      error = null;
      console.log('Loading battles from client...');
      
      const allBattles = await getAllBattles();
      console.log('All battles loaded:', allBattles.length);
      
      // Filter for finished battles
      const finishedBattles = allBattles.filter((battle: any) => 
        battle.state === 'finished' || battle.state === 'error'
      );
      console.log('Finished battles found:', finishedBattles.length);
      
      // Load agent data for each battle
      const battlesWithAgents = await Promise.all(
        finishedBattles.map((battle: any) => loadAgentData(battle))
      );
      
      battles = battlesWithAgents;
      console.log('Loaded battles with agent data:', battles.length);
    } catch (err) {
      console.error('Failed to load battles:', err);
      error = err instanceof Error ? err.message : 'Failed to load battles';
      battles = [];
    } finally {
      loading = false;
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
  </div>
  
  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span class="ml-3 text-lg">Loading battles...</span>
    </div>
  {:else if error}
    <div class="text-center py-12">
      <p class="text-red-600 mb-4">Error loading battles: {error}</p>
      <button onclick={loadBattles} class="btn-primary">Retry</button>
    </div>
  {:else if battles && battles.length > 0}
    <BattleTable battles={battles} />
  {:else}
    <div class="text-center py-12">
      <p class="text-gray-600 mb-4">No past battles found.</p>
      <p class="text-sm text-muted-foreground mb-6">
        This could mean:
      </p>
      <ul class="text-sm text-muted-foreground space-y-1 mb-6">
        <li>• No battles have been completed yet</li>
        <li>• All battles are still running or queued</li>
        <li>• There are no battles in the database</li>
      </ul>
      <a href="/battles/stage-battle" class="btn-primary">
        Start Your First Battle
      </a>
    </div>
  {/if}
</div> 