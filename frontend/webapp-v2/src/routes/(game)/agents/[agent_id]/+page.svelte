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
          <div class="bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Agent Information</h2>
            <div class="space-y-3">
              <div>
                <span class="font-medium">Name:</span>
                <span class="text-muted-foreground ml-2">{agent.agent_card?.name || 'Not set'}</span>
              </div>
              <div>
                <span class="font-medium">Description:</span>
                <div class="mt-1 max-h-32 overflow-y-auto p-2">
                  <p class="text-muted-foreground text-sm">{agent.agent_card?.description || 'No description available'}</p>
                </div>
              </div>
              <div>
                <span class="font-medium">Agent URL:</span>
                <p class="text-muted-foreground font-mono text-sm mt-1">{agent.register_info?.agent_url || 'Not set'}</p>
              </div>
              <div>
                <span class="font-medium">Launcher URL:</span>
                <p class="text-muted-foreground font-mono text-sm mt-1">{agent.register_info?.launcher_url || 'Not set'}</p>
              </div>
              <div>
                <span class="font-medium">Status:</span>
                <span class="text-muted-foreground ml-2 capitalize">{agent.status || 'Unknown'}</span>
              </div>
              <div>
                <span class="font-medium">Ready:</span>
                <span class="text-muted-foreground ml-2">{agent.ready ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </div>

          <!-- Performance Info -->
          <div class="bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Performance</h2>
            <div class="space-y-4">
              <!-- Battle count for last 24 hours -->
              <div>
                <span class="font-medium">Battles (24h):</span>
                <span class="text-muted-foreground ml-2">
                  {loadingBattles ? 'Loading...' : battleCount}
                </span>
              </div>
              
              {#if agent.elo?.rating}
                <div>
                  <span class="font-medium">ELO Rating:</span>
                  <span class="text-muted-foreground ml-2">{agent.elo.rating}</span>
                </div>
                <div>
                  <span class="font-medium">Win Rate:</span>
                  <span class="text-muted-foreground ml-2">{((agent.elo.win_rate || 0) * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span class="font-medium">Total Battles:</span>
                  <span class="text-muted-foreground ml-2">{agent.elo.battles || 0}</span>
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Participant Requirements -->
        {#if agent.register_info?.participant_requirements?.length > 0}
          <div class="mt-8 bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Competitor Requirements</h2>
            <div class="grid gap-3">
              {#each agent.register_info.participant_requirements as req}
                <div class="flex items-center justify-between p-3 border rounded">
                  <div>
                    <div class="font-medium">{req.name}</div>
                    <div class="text-sm text-muted-foreground">Role: {req.role}</div>
                  </div>
                  <span class="text-sm px-2 py-1 rounded bg-gray-100">
                    {req.required ? 'Required' : 'Optional'}
                  </span>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Battle Configuration - Only for Green Agents -->
        {#if agent.register_info?.battle_timeout && agent.register_info?.participant_requirements}
          <div class="mt-8 bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Battle Configuration</h2>
            <div class="space-y-3">
              <div>
                <span class="font-medium">Battle Timeout:</span>
                <span class="text-muted-foreground ml-2">{agent.register_info.battle_timeout} seconds</span>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div> 