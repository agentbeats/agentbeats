<script lang="ts">
  import { goto } from "$app/navigation";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { getBattleById } from "$lib/api/battles";
  import { getAllAgents } from "$lib/api/agents";
  import { onMount } from "svelte";

  let { exampleBattle } = $props<{
    exampleBattle: {
      battle_id: string;
      title: string;
      description: string;
      green_agent_id?: string;
      opponents?: Array<{ name: string; agent_id: string }>;
    };
  }>();

  let battleData = $state<any>(null);
  let greenAgent = $state<any>(null);
  let opponentAgents = $state<any[]>([]);
  let loading = $state(true);
  let allAgents = $state<any[]>([]);

  onMount(async () => {
    await loadBattleData();
  });

  // Helper function to find agent by ID from the cached agents
  function findAgentById(agentId: string): any | null {
    return allAgents.find(agent => agent.agent_id === agentId || agent.id === agentId) || null;
  }

  async function loadBattleData() {
    try {
      loading = true;
      
      // Load all agents first
      console.log('Loading all agents for example battle...');
      allAgents = await getAllAgents();
      console.log('All agents loaded:', allAgents.length);
      
      // Load the actual battle data using the battle ID
      if (exampleBattle.battle_id) {
        try {
          console.log('Loading battle data for ID:', exampleBattle.battle_id);
          battleData = await getBattleById(exampleBattle.battle_id);
          console.log('Loaded battle data:', battleData);
          
          // Load green agent
          if (battleData.green_agent_id) {
            greenAgent = findAgentById(battleData.green_agent_id);
            console.log('Green agent found:', greenAgent);
          }
          
          // Load opponent agents
          if (battleData.opponents && battleData.opponents.length > 0) {
            opponentAgents = [];
            for (const opponent of battleData.opponents) {
              const agent = findAgentById(opponent.agent_id);
              if (agent) {
                opponentAgents.push({
                  ...agent,
                  role: opponent.name
                });
              }
            }
            console.log('Opponent agents found:', opponentAgents.length);
          }
        } catch (error) {
          console.error('Failed to load battle data:', error);
          // Keep the example battle data as fallback
          battleData = exampleBattle;
        }
      }
    } catch (error) {
      console.error('Failed to load example battle data:', error);
      // Keep the example battle data as fallback
      battleData = exampleBattle;
    } finally {
      loading = false;
    }
  }

  function handleCardClick() {
    if (exampleBattle.battle_id) {
      try {
        goto(`/battles/${exampleBattle.battle_id}`);
      } catch (error) {
        console.error('Battle not found:', exampleBattle.battle_id);
        // Still display the card but show an error state
      }
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleCardClick();
    }
  }
</script>

<div class="bg-card border rounded-lg p-4 w-full h-80 shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer hover:-translate-y-1 hover:bg-muted" onclick={handleCardClick} onkeydown={handleKeyDown} tabindex="0" role="button" aria-label="View example battle details">
  <div class="flex flex-col h-full space-y-3 text-center">
    <!-- Battle Title -->
    <div class="space-y-2">
      <h3 class="text-sm font-semibold text-foreground">
        {exampleBattle.title}
      </h3>
      <p class="text-xs text-muted-foreground">
        {exampleBattle.description}
      </p>
    </div>

    <!-- Green Agent -->
    {#if loading}
      <div class="flex items-center justify-center py-2">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-muted-foreground"></div>
      </div>
    {:else if greenAgent}
      <div class="space-y-2">
        <div class="text-xs font-medium text-muted-foreground">Green Agent (Coordinator)</div>
        <AgentChip 
          agent={{
            identifier: greenAgent.register_info?.alias || greenAgent.agent_card?.name || 'Unknown',
            avatar_url: greenAgent.register_info?.avatar_url,
            description: greenAgent.agent_card?.description
          }}
          agent_id={greenAgent.agent_id || greenAgent.id}
          isOnline={greenAgent.live || false}
          clickable={false}
        />
      </div>
    {:else}
      <!-- No Green Agent Data -->
      <div class="space-y-2">
        <div class="text-xs font-medium text-muted-foreground">Green Agent (Coordinator)</div>
        <div class="text-xs text-muted-foreground">Agent data not available</div>
      </div>
    {/if}

    <!-- Opponent Agents -->
    {#if opponentAgents.length > 0}
      <div class="space-y-2 flex-1">
        <div class="text-xs font-medium text-muted-foreground">Opponents</div>
        <div class="space-y-1">
          {#each opponentAgents as agent}
            <AgentChip 
              agent={{
                identifier: agent.register_info?.alias || agent.agent_card?.name || 'Unknown',
                avatar_url: agent.register_info?.avatar_url,
                description: agent.agent_card?.description
              }}
              agent_id={agent.agent_id || agent.id}
              isOnline={agent.live || false}
              clickable={false}
            />
          {/each}
        </div>
      </div>
    {:else}
      <!-- No Opponent Agents Data -->
      <div class="space-y-2 flex-1">
        <div class="text-xs font-medium text-muted-foreground">Opponents</div>
        <div class="text-xs text-muted-foreground">No opponent data available</div>
      </div>
    {/if}

    <!-- Battle ID -->
    <div class="text-xs text-muted-foreground">
      ID: {exampleBattle.battle_id}
    </div>
  </div>
</div> 