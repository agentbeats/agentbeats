<script lang="ts">
  import BattleTable from './battle-table.svelte';
  import { getAllBattles } from "$lib/api/battles";
  import { getAllAgentsWithAsyncLiveness } from "$lib/api/agents";
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

  let battles = $state<Battle[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  let totalBattles = $state(0);
  let loadedCount = $state(0);
  let loadingMore = $state(false);
  let allAgents = $state<any[]>([]);

  // Pagination settings
  const BATTLES_PER_PAGE = 10; // Only load 10 battles at a time for performance

  // Debug logging
  console.log('🎯 PAST BATTLES PAGE LOADED! 🎯');

  // Helper function to find agent by ID from the cached agents
  function findAgentById(agentId: string): any | null {
    return allAgents.find(agent => agent.agent_id === agentId || agent.id === agentId) || null;
  }
  
  // Update agent data in battles when liveness info is ready
  function updateAgentDataInBattles(updatedAgents: any[]) {
    allAgents = updatedAgents;
    
    // Update battles with new agent liveness data
    battles = battles.map(battle => {
      const updatedBattle = { ...battle };
      
      // Update green agent if it exists
      if (battle.green_agent) {
        const updatedGreenAgent = findAgentById(battle.green_agent_id);
        if (updatedGreenAgent) {
          updatedBattle.green_agent = {
            ...battle.green_agent,
            live: updatedGreenAgent.live || false,
            livenessLoading: updatedGreenAgent.livenessLoading || false
          };
        }
      }
      
      // Update opponent agents if they exist
      if (battle.opponent_agents && battle.opponent_agents.length > 0) {
        updatedBattle.opponent_agents = battle.opponent_agents.map(opponentAgent => {
          const updatedOpponentAgent = findAgentById(opponentAgent.agent_id);
          if (updatedOpponentAgent) {
            return {
              ...opponentAgent,
              live: updatedOpponentAgent.live || false,
              livenessLoading: updatedOpponentAgent.livenessLoading || false
            };
          }
          return opponentAgent;
        });
      }
      
      return updatedBattle;
    });
    
    console.log('Updated battles with liveness data');
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
            register_info: { alias: `Unknown Agent (${battle.green_agent_id.slice(0, 8)})` },
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
      
      // First, load all agents once with layered loading
      console.log('Loading all agents...');
      allAgents = await getAllAgentsWithAsyncLiveness((updatedAgents) => {
        // Update agent data when liveness info is ready
        console.log('Past battles agents liveness updated:', updatedAgents);
        updateAgentDataInBattles(updatedAgents);
      });
      console.log('All agents loaded (basic info):', allAgents.length);
      
      const allBattles = await getAllBattles();
      console.log('All battles loaded:', allBattles.length);
      
      // Filter for finished battles
      const finishedBattles = allBattles.filter((battle: any) => 
        battle.state === 'finished' || battle.state === 'error'
      );
      console.log('Finished battles found:', finishedBattles.length);
      
      // Load all finished battles since we have efficient agent loading
      const battlesToLoad = finishedBattles;
      totalBattles = finishedBattles.length;
      loadedCount = totalBattles;
      
      console.log(`Loading all ${battlesToLoad.length} battles`);
      
      // Load agent data for all battles
      const battlesWithAgents = [];
      for (let i = 0; i < battlesToLoad.length; i++) {
        const battle = battlesToLoad[i];
        console.log(`Loading battle ${i + 1}/${battlesToLoad.length}: ${battle.battle_id}`);
        
        const battleWithAgents = await loadAgentData(battle);
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
      }
  }



  onMount(() => {
    loadBattles();
  });

</script>

<div class="space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold mb-2">Past Battles</h1>
    <p class="text-muted-foreground">Browse and search completed battles</p>
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
  {:else if battles && battles.length > 0}
    <div in:fade={{ duration: 300 }} out:fade={{ duration: 200 }}>
      <BattleTable battles={battles} />
    </div>
  {:else}
    <div class="text-center py-12">
      <p class="text-muted-foreground">No past battles found.</p>
    </div>
  {/if}
</div> 