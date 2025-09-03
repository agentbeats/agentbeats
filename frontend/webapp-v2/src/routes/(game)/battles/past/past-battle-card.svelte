<script lang="ts">
  import { goto } from "$app/navigation";
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { getAgentById } from "$lib/api/agents";
  import { onMount } from "svelte";

  let { battle } = $props<{
    battle: {
      battle_id: string;
      green_agent_id: string;
      opponents: Array<{ name: string; agent_id: string }>;
      state: string;
      created_at: string;
      finished_at?: string;
    };
  }>();

  let greenAgent = $state<any>(null);
  let opponentAgents = $state<any[]>([]);
  let loading = $state(true);

  onMount(async () => {
    await loadAgentData();
  });

  async function loadAgentData() {
    try {
      // Load green agent
      greenAgent = await getAgentById(battle.green_agent_id);
      
      // Load opponent agents
      opponentAgents = await Promise.all(
        battle.opponents.map(async (opponent: { name: string; agent_id: string }) => {
          return await getAgentById(opponent.agent_id);
        })
      );
    } catch (error) {
      console.error('Failed to load agent data:', error);
    } finally {
      loading = false;
    }
  }

  function getStatusColor(state: string): string {
    switch (state) {
      case 'finished':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-muted text-muted-foreground';
    }
  }

  function getStatusText(state: string): string {
    switch (state) {
      case 'finished':
        return 'Finished';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  }

  function formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleDateString();
  }

  function handleViewBattle() {
    goto(`/battles/${battle.battle_id}`);
  }
</script>

<Card.Root class="w-full">
  <Card.Header class="pb-3">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <h3 class="text-lg font-semibold">Battle #{battle.battle_id.slice(-8)}</h3>
        <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(battle.state)}">
          {getStatusText(battle.state)}
        </span>
      </div>
      <div class="text-sm text-muted-foreground">
        {formatTimestamp(battle.created_at)}
      </div>
    </div>
  </Card.Header>

  <Card.Content class="space-y-4">
    <!-- Participants -->
    <div class="space-y-2">
      <h4 class="text-sm font-medium text-foreground">Participants</h4>
      <div class="flex flex-wrap gap-2">
        {#if loading}
          <div class="animate-pulse bg-muted h-6 w-20 rounded-full"></div>
        {:else if greenAgent}
          <AgentChip 
            agent={{
              identifier: greenAgent.register_info?.alias || greenAgent.agent_card?.name || 'Unknown',
              avatar_url: greenAgent.register_info?.avatar_url,
              description: greenAgent.agent_card?.description
            }}
            agent_id={greenAgent.agent_id || greenAgent.id}
          />
        {/if}
        
        {#if loading}
          <div class="animate-pulse bg-muted h-6 w-20 rounded-full"></div>
          <div class="animate-pulse bg-muted h-6 w-20 rounded-full"></div>
        {:else}
          {#each opponentAgents as agent, i}
            {#if agent}
              <AgentChip 
                agent={{
                  identifier: agent.register_info?.alias || agent.agent_card?.name || 'Unknown',
                  avatar_url: agent.register_info?.avatar_url,
                  description: agent.agent_card?.description
                }}
                agent_id={agent.agent_id || agent.id}
              />
            {/if}
          {/each}
        {/if}
      </div>
    </div>

    <!-- Action -->
    <div class="flex justify-end pt-2">
      <Button variant="outline" size="sm" onclick={handleViewBattle}>
        View Details
      </Button>
    </div>
  </Card.Content>
</Card.Root> 