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
  let loadingProgress = $state(0);
  let totalBattles = $state(0);

  // Pagination settings
  const BATTLES_PER_PAGE = 10; // Only load 10 battles at a time

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

      // Load opponent agents sequentially (not in parallel)
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
      loadingProgress = 0;
      console.log('Loading battles from client...');
      
      const allBattles = await getAllBattles();
      console.log('All battles loaded:', allBattles.length);
      
      // Filter for finished battles
      const finishedBattles = allBattles.filter((battle: any) => 
        battle.state === 'finished' || battle.state === 'error'
      );
      console.log('Finished battles found:', finishedBattles.length);
      
      // Only take the first BATTLES_PER_PAGE battles
      const battlesToLoad = finishedBattles.slice(0, BATTLES_PER_PAGE);
      totalBattles = finishedBattles.length;
      
      console.log(`Loading first ${battlesToLoad.length} battles out of ${totalBattles} total`);
      
      // Calculate total agent loads for accurate progress
      let totalAgentLoads = 0;
      let completedAgentLoads = 0;
      
      // Count total agent loads needed
      for (const battle of battlesToLoad) {
        totalAgentLoads++; // Green agent
        if (battle.opponents) {
          totalAgentLoads += battle.opponents.length; // Opponent agents
        }
      }
      
      console.log(`Total agent loads needed: ${totalAgentLoads}`);
      
      // Load agent data sequentially with accurate progress updates
      const battlesWithAgents = [];
      for (let i = 0; i < battlesToLoad.length; i++) {
        const battle = battlesToLoad[i];
        console.log(`Loading battle ${i + 1}/${battlesToLoad.length}: ${battle.battle_id}`);
        
        const battleWithAgents = await loadAgentDataWithProgress(battle, () => {
          completedAgentLoads++;
          loadingProgress = Math.round((completedAgentLoads / totalAgentLoads) * 100);
        });
        
        battlesWithAgents.push(battleWithAgents);
      }
      
      battles = battlesWithAgents;
      console.log('Loaded battles with agent data:', battles.length);
    } catch (err) {
      console.error('Failed to load battles:', err);
      error = err instanceof Error ? err.message : 'Failed to load battles';
      battles = [];
    } finally {
      loading = false;
      loadingProgress = 0;
    }
  }

  async function loadAgentDataWithProgress(battle: any, onAgentLoaded: () => void): Promise<Battle> {
    try {
      // Load green agent
      let greenAgent = null;
      if (battle.green_agent_id) {
        try {
          greenAgent = await getAgentById(battle.green_agent_id);
          onAgentLoaded(); // Update progress after green agent loads
        } catch (error) {
          console.error('Failed to load green agent:', error);
          // Create placeholder green agent
          greenAgent = {
            agent_id: battle.green_agent_id,
            register_info: { alias: `Unknown Agent (${battle.green_agent_id.slice(0, 8)})` },
            agent_card: { name: `Unknown Agent`, description: 'Agent data unavailable' }
          };
          onAgentLoaded(); // Still count as loaded even if it's a placeholder
        }
      }

      // Load opponent agents sequentially
      let opponentAgents = [];
      if (battle.opponents && battle.opponents.length > 0) {
        for (const opponent of battle.opponents) {
          try {
            const agent = await getAgentById(opponent.agent_id);
            opponentAgents.push({
              ...agent,
              role: opponent.name
            });
            onAgentLoaded(); // Update progress after each opponent loads
          } catch (error) {
            console.error(`Failed to load opponent agent ${opponent.agent_id}:`, error);
            // Add placeholder for failed agent
            opponentAgents.push({
              agent_id: opponent.agent_id,
              register_info: { alias: `Unknown ${opponent.name}` },
              agent_card: { name: `Unknown ${opponent.name}`, description: 'Agent data unavailable' },
              role: opponent.name
            });
            onAgentLoaded(); // Still count as loaded even if it's a placeholder
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

  onMount(() => {
    loadBattles();
  });

</script>

<div class="space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold mb-2">Past Battles</h1>
    <p class="text-gray-600">Browse and search completed battles</p>
    {#if totalBattles > BATTLES_PER_PAGE}
      <p class="text-sm text-muted-foreground mt-2">
        Showing first {BATTLES_PER_PAGE} of {totalBattles} battles
      </p>
    {/if}
  </div>
  
  {#if loading}
    <div class="flex flex-col items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
      <span class="text-lg mb-2">Loading battles...</span>
      {#if loadingProgress > 0}
        <div class="w-64 bg-gray-200 rounded-full h-2">
          <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" style="width: {loadingProgress}%"></div>
        </div>
        <span class="text-sm text-muted-foreground mt-2">{loadingProgress}% complete</span>
      {/if}
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