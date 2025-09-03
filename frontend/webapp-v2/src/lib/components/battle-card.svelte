<script lang="ts">
  import { goto } from "$app/navigation";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { getAgentById } from "$lib/api/agents";
  import { onMount } from "svelte";

  let { battle } = $props<{
    battle: {
      battle_id?: string;
      state?: string;
      green_agent_id?: string;
      opponents?: Array<{ name: string; agent_id: string }>;
      created_at?: string;
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
      loading = true;
      
      // Load green agent
      if (battle.green_agent_id) {
        try {
          greenAgent = await getAgentById(battle.green_agent_id);
        } catch (error) {
          console.error('Failed to load green agent:', error);
        }
      }

      // Load opponent agents
      if (battle.opponents && battle.opponents.length > 0) {
        opponentAgents = [];
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
    } catch (error) {
      console.error('Failed to load battle data:', error);
    } finally {
      loading = false;
    }
  }

  function handleCardClick() {
    if (battle.battle_id) {
      goto(`/battles/${battle.battle_id}`);
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleCardClick();
    }
  }

  function getStatusColor(state: string) {
    switch (state?.toLowerCase()) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-muted text-muted-foreground';
    }
  }

  function getStatusText(state: string) {
    switch (state?.toLowerCase()) {
      case 'running':
        return 'Running';
      case 'queued':
        return 'Queued';
      case 'pending':
        return 'Pending';
      default:
        return 'Unknown';
    }
  }

  function formatTimeSince(timestamp: string) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just started';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  }

  function shortId(id: string) {
    return id ? id.slice(0, 8) : '';
  }
</script>

<div class="bg-card border rounded-lg p-4 w-full shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer hover:-translate-y-1 hover:bg-muted" onclick={handleCardClick} onkeydown={handleKeyDown} tabindex="0" role="button" aria-label="View battle details">
  <div class="flex flex-col h-full space-y-3 text-center">
    <!-- Green Agent as Title -->
    {#if loading}
      <div class="flex items-center justify-center py-2">
        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-muted-foreground"></div>
      </div>
    {:else if greenAgent}
      <div class="space-y-2">
        <h3 class="text-sm font-semibold">
          {greenAgent.register_info?.alias || greenAgent.agent_card?.name || 'Unknown Agent'}
        </h3>
        <AgentChip 
          agent={{
            identifier: greenAgent.register_info?.alias || greenAgent.agent_card?.name || 'Unknown',
            avatar_url: greenAgent.register_info?.avatar_url,
            description: greenAgent.agent_card?.description
          }}
          agent_id={greenAgent.agent_id || greenAgent.id}
          isOnline={greenAgent.live || false}
          isLoading={greenAgent.livenessLoading || false}
        />
      </div>
    {/if}

    <!-- Opponent Agents -->
    {#if opponentAgents.length > 0}
      <div class="space-y-2">
        <div class="text-xs font-medium">Opponents</div>
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
              isLoading={agent.livenessLoading || false}
            />
          {/each}
        </div>
      </div>
    {/if}

    <!-- Time Since Start -->
    {#if battle.created_at}
      <div class="text-xs text-muted-foreground mt-auto">
        Started {formatTimeSince(battle.created_at)}
      </div>
    {/if}
  </div>
</div> 