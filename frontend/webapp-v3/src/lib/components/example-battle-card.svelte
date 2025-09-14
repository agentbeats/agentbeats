<script lang="ts">
  import { goto } from "$app/navigation";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { onMount } from "svelte";
  import { useAgents } from "$lib/hooks";

  let { exampleBattle } = $props<{
    exampleBattle: {
      battle_id: string;
      title: string;
      description: string;
      green_agent_id?: string;
      opponents?: Array<{ name: string; agent_id: string }>;
    };
  }>();

  let greenAgent = $state<any>(null);
  let opponentAgents = $state<any[]>([]);
  let loading = $state(true);

  const agents = useAgents();

  onMount(async () => {
    await loadAgentData();
  });

  async function loadAgentData() {
    try {
      loading = true;
      
      // Load green agent
      if (exampleBattle.green_agent_id) {
        try {
          greenAgent = await agents.getAgentById(exampleBattle.green_agent_id);
        } catch (error) {
          console.error('Failed to load green agent:', error);
        }
      }

      // Load opponent agents
      if (exampleBattle.opponents && exampleBattle.opponents.length > 0) {
        opponentAgents = [];
        for (const opponent of exampleBattle.opponents) {
          try {
            const agent = await agents.getAgentById(opponent.agent_id);
            opponentAgents.push({
              ...agent,
              role: opponent.name
            });
          } catch (error) {
            console.error(`Failed to load opponent agent ${opponent.agent_id}:`, error);
            // Add placeholder for failed agent
            opponentAgents.push({
              agent_id: opponent.agent_id,
              alias: `Unknown ${opponent.name}`,
              agent_card: { name: `Unknown ${opponent.name}`, description: 'Agent data unavailable' },
              role: opponent.name
            });
          }
        }
      }
    } catch (error) {
      console.error('Failed to load example battle data:', error);
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

<div class="bg-white border rounded-lg p-4 w-full h-80 shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer hover:-translate-y-1 hover:bg-gray-50" onclick={handleCardClick} onkeydown={handleKeyDown} tabindex="0" role="button" aria-label="View example battle details">
  <div class="flex flex-col h-full space-y-3 text-center">
    <!-- Battle Title -->
    <div class="space-y-2">
      <h3 class="text-sm font-semibold text-gray-900">
        {exampleBattle.title}
      </h3>
      <p class="text-xs text-gray-600">
        {exampleBattle.description}
      </p>
    </div>

    <!-- Green Agent -->
    {#if loading}
      <div class="flex items-center justify-center py-2">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
      </div>
    {:else if greenAgent}
      <div class="space-y-2">
        <div class="text-xs font-medium text-gray-500">Green Agent (Coordinator)</div>
        <AgentChip 
          agent={{
            identifier: greenAgent.alias || greenAgent.agent_card?.name || 'Unknown',
            avatar_url: greenAgent?.avatar_url,
            description: greenAgent.agent_card?.description
          }}
          agent_id={greenAgent.agent_id || greenAgent.id}
          isOnline={greenAgent.live || false}
          clickable={false}
        />
      </div>
    {:else}
      <!-- Fallback Green Agent -->
      <div class="space-y-2">
        <div class="text-xs font-medium text-gray-500">Green Agent (Coordinator)</div>
        <AgentChip 
          agent={{
            identifier: "WASP Agent",
            description: "Advanced reasoning agent"
          }}
          agent_id="example-wasp"
          isOnline={true}
          clickable={false}
        />
      </div>
    {/if}

    <!-- Opponent Agents -->
    {#if opponentAgents.length > 0}
      <div class="space-y-2 flex-1">
        <div class="text-xs font-medium text-gray-500">Opponents</div>
        <div class="space-y-1">
          {#each opponentAgents as agent}
            <AgentChip 
              agent={{
                identifier: agent.alias || agent.agent_card?.name || 'Unknown',
                avatar_url: agent?.avatar_url,
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
      <!-- Fallback Opponent Agents -->
      <div class="space-y-2 flex-1">
        <div class="text-xs font-medium text-gray-500">Opponents</div>
        <div class="space-y-1">
          <AgentChip 
            agent={{
              identifier: "CyberGym Agent", 
              description: "Cybersecurity specialist"
            }}
            agent_id="example-cybergym"
            isOnline={true}
            clickable={false}
          />
          <AgentChip 
            agent={{
              identifier: "BountyBench Agent", 
              description: "Creative problem solver"
            }}
            agent_id="example-bountybench"
            isOnline={true}
            clickable={false}
          />
        </div>
      </div>
    {/if}

    <!-- Battle ID -->
    <div class="text-xs text-gray-500">
      ID: {exampleBattle.battle_id}
    </div>
  </div>
</div> 