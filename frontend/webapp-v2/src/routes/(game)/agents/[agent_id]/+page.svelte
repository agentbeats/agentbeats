<script lang="ts">
  import { page } from '$app/stores';
  import { getAgentById } from "$lib/api/agents";
  import { getAgentBattlesLast24Hours } from "$lib/api/battles";
  import { Button } from "$lib/components/ui/button/index.js";
  import { goto } from "$app/navigation";
  import { fly } from 'svelte/transition';
  import MoveLeftIcon from "@lucide/svelte/icons/move-left";


  let agent = $state<any>(null);
  let isLoading = $state(true);
  let error = $state<string | null>(null);
  let battleCount = $state(0);
  let loadingBattles = $state(true);

  $effect(() => {
    const agentId = $page.params.agent_id;
    if (agentId) {
      getAgentById(agentId).then(foundAgent => {
        agent = foundAgent;
        isLoading = false;
        // Load battle count for the agent
        loadBattleCount(foundAgent.agent_id || foundAgent.id);
      }).catch(err => {
        console.error('Failed to load agent:', err);
        error = err instanceof Error ? err.message : 'Failed to load agent';
        isLoading = false;
      });
    }
  });

  async function loadBattleCount(agentId: string) {
    try {
      const battles = await getAgentBattlesLast24Hours(agentId);
      battleCount = battles.length;
    } catch (error) {
      console.error('Failed to load battle count:', error);
      battleCount = 0;
    } finally {
      loadingBattles = false;
    }
  }
</script>

<div class="min-h-screen flex flex-col items-center p-4">
  <div class="w-full max-w-4xl mt-6">
    {#if isLoading}
      <div class="text-center">
        <p class="text-muted-foreground">Loading agent...</p>
      </div>
    {:else if error}
      <div class="text-center">
        <p class="text-destructive">{error}</p>
        <Button onclick={() => history.back()} class="mt-4">Back</Button>
      </div>
    {:else if agent}
      <div in:fly={{ y: 20, duration: 300 }}>
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
          <h1 class="text-4xl font-bold">
            {agent.register_info?.alias || agent.agent_card?.name || 'Unknown Agent'}
          </h1>
          <Button variant="outline" onclick={() => history.back()}>
            <MoveLeftIcon class="h-4 w-4" />
          </Button>
        </div>

        <!-- Agent Info Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- Agent Card Info -->
          <div class="bg-card border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Agent Information</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1">Name</label>
                <p class="text-sm">{agent?.agent_card?.name || 'Unnamed Agent'}</p>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Identifier</label>
                <p class="text-sm">{agent?.identifier || 'Unknown'}</p>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Description</label>
                <p class="text-sm">{agent?.agent_card?.description || 'No description available'}</p>
              </div>
              <div>
                <label class="block text-sm font-medium mb-1">Status</label>
                <div class="flex items-center gap-2">
                  <div class="w-3 h-3 rounded-full {agent?.live ? 'bg-green-500' : 'bg-red-500'}"></div>
                  <span class="text-sm">{agent?.live ? 'Online' : 'Offline'}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Performance Info -->
          <div class="bg-card border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Performance</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="text-center">
                <div class="text-2xl font-bold text-primary">{agent?.stats?.total_battles || 0}</div>
                <div class="text-sm text-muted-foreground">Total Battles</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-primary">{agent?.stats?.wins || 0}</div>
                <div class="text-sm text-muted-foreground">Wins</div>
              </div>
              <div class="text-center">
                <div class="text-2xl font-bold text-primary">{agent?.stats?.win_rate || 0}%</div>
                <div class="text-sm text-muted-foreground">Win Rate</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Participant Requirements -->
        <div class="bg-card border rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">Competitor Requirements</h2>
          {#if agent?.agent_card?.participant_requirements && agent.agent_card.participant_requirements.length > 0}
            <div class="space-y-3">
              {#each agent.agent_card.participant_requirements as requirement, index}
                <div class="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <span class="text-sm font-medium">{requirement.role || 'Participant'}</span>
                    {#if requirement.description}
                      <p class="text-xs text-muted-foreground">{requirement.description}</p>
                    {/if}
                  </div>
                  <span class="text-xs px-2 py-1 rounded bg-muted">
                    {requirement.required ? 'Required' : 'Optional'}
                  </span>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-muted-foreground">No specific requirements defined</p>
          {/if}
        </div>

        <!-- Battle Configuration - Only for Green Agents -->
        <div class="bg-card border rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">Battle Configuration</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">Agent Type</label>
              <p class="text-sm">{agent?.agent_card?.agent_type || 'Unknown'}</p>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Capabilities</label>
              <div class="flex flex-wrap gap-2">
                {#if agent?.agent_card?.capabilities}
                  {#each agent.agent_card.capabilities as capability}
                    <span class="text-xs px-2 py-1 rounded bg-muted">{capability}</span>
                  {/each}
                {:else}
                  <span class="text-muted-foreground">No capabilities listed</span>
                {/if}
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div> 