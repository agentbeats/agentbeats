<script lang="ts">
  import { page } from '$app/stores';
  import { useAgents, useBattles } from "$lib/hooks";
  import { agentsService } from "$lib/services/agents.service";
  import { Button } from "$lib/components/ui/button/index.js";
  import { fly } from 'svelte/transition';
  import MoveLeftIcon from "@lucide/svelte/icons/move-left";
  import LoaderIcon from "@lucide/svelte/icons/loader";
  import AlertCircleIcon from "@lucide/svelte/icons/alert-circle";
  import CheckCircleIcon from "@lucide/svelte/icons/check-circle";
  import XCircleIcon from "@lucide/svelte/icons/x-circle";
  
  import type { Agent, AgentInstance, AgentCardStatus, AgentInstanceDockerStatus } from "$lib/types";

  // Use the new hooks
  const agentsHook = useAgents();
  const battlesHook = useBattles();

  let agent = $state<Agent>();
  let agentInstances = $state<AgentInstance[]>([]);
  let isLoading = $state(true);
  let isLoadingInstances = $state(false);
  let error = $state<string | null>(null);
  let instancesError = $state<string | null>(null);
  let battleCount = $state(0);
  let loadingBattles = $state(true);
  let isUpdatingCard = $state(false);

  $effect(() => {
    const agentId = $page.params.agent_id;
    if (agentId) {
      loadAgentData(agentId);
    }
  });

  async function loadAgentData(agentId: string) {
    try {
      isLoading = true;
      error = null;

      // Use the agentsHook to get agent by ID
      const foundAgent = await agentsHook.getAgentById(agentId);
      if (foundAgent) {
        agent = foundAgent;
        // Load battle count for the agent
        await loadBattleCount(foundAgent.agent_id);
        // Load agent instances
        await loadAgentInstances(foundAgent.agent_id);
      } else {
        error = 'Agent not found';
      }
    } catch (err) {
      console.error('Failed to load agent:', err);
      error = err instanceof Error ? err.message : 'Failed to load agent';
    } finally {
      isLoading = false;
    }
  }

  async function loadBattleCount(agentId: string) {
    try {
      const battles = await battlesHook.getAgentBattlesLast24Hours(agentId);
      if (battles) {
        battleCount = battles.length;
      } else {
        battleCount = 0;
      };
    } catch (error) {
      console.error('Failed to load battle count:', error);
      battleCount = 0;
    } finally {
      loadingBattles = false;
    }
  }

  async function loadAgentInstances(agentId: string) {
    try {
      isLoadingInstances = true;
      instancesError = null;
      
      const result = await agentsService.getAgentInstancesByAgentId(agentId);
      if (result.success && result.data) {
        agentInstances = result.data.instances;
      } else {
        instancesError = result.error || 'Failed to load agent instances';
        agentInstances = [];
      }
    } catch (err) {
      console.error('Failed to load agent instances:', err);
      instancesError = err instanceof Error ? err.message : 'Failed to load agent instances';
      agentInstances = [];
    } finally {
      isLoadingInstances = false;
    }
  }

  function getStatusIcon(status: AgentCardStatus) {
    switch (status) {
      case 'loading':
        return LoaderIcon;
      case 'ready':
        return CheckCircleIcon;
      case 'error':
        return XCircleIcon;
      default:
        return AlertCircleIcon;
    }
  }

  function getStatusColor(status: AgentCardStatus) {
    switch (status) {
      case 'loading':
        return 'text-blue-500';
      case 'ready':
        return 'text-green-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  }

  function getDockerStatusColor(status: AgentInstanceDockerStatus) {
    switch (status) {
      case 'running':
        return 'text-green-500 bg-green-50';
      case 'starting':
        return 'text-blue-500 bg-blue-50';
      case 'stopping':
        return 'text-orange-500 bg-orange-50';
      case 'stopped':
        return 'text-gray-500 bg-gray-50';
      default:
        return 'text-gray-500 bg-gray-50';
    }
  }

  async function updateAgentCard() {
    if (!agent) return;
    
    try {
      isUpdatingCard = true;
      
      const result = await agentsService.updateAgentCard(agent.agent_id);
      if (result.success) {
        // Reload agent data to get updated card status
        await loadAgentData(agent.agent_id);
      } else {
        console.error('Failed to update agent card:', result.error);
        // You could add a toast notification here
      }
    } catch (err) {
      console.error('Error updating agent card:', err);
    } finally {
      isUpdatingCard = false;
    }
  }
</script>

<div class="min-h-screen flex flex-col items-center p-4">
  <div class="w-full max-w-6xl mt-6">
    {#if isLoading}
      <div class="text-center">
        <LoaderIcon class="h-8 w-8 animate-spin mx-auto mb-4" />
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
            {agent.alias || agent.agent_card?.name || 'Unknown Agent'}
          </h1>
          <Button variant="outline" onclick={() => history.back()}>
            <MoveLeftIcon class="h-4 w-4" />
          </Button>
        </div>

        <!-- Main Grid Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Left Column -->
          <div class="space-y-8">
            <!-- Agent Card Section -->
            <div class="bg-white border rounded-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                  <h2 class="text-xl font-semibold">Agent Card</h2>
                  {#if agent.agent_card_status}
                    {@const StatusIcon = getStatusIcon(agent.agent_card_status)}
                    <StatusIcon class="h-5 w-5 {getStatusColor(agent.agent_card_status)} {agent.agent_card_status === 'loading' ? 'animate-spin' : ''}" />
                    <span class="text-sm {getStatusColor(agent.agent_card_status)} capitalize">
                      {agent.agent_card_status}
                    </span>
                  {/if}
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onclick={updateAgentCard}
                  disabled={isUpdatingCard || agent.agent_card_status === 'loading'}
                >
                  {#if isUpdatingCard}
                    <LoaderIcon class="h-4 w-4 animate-spin mr-2" />
                  {/if}
                  Update Card
                </Button>
              </div>

              {#if agent.agent_card_status === 'loading'}
                <div class="flex items-center justify-center py-8">
                  <div class="text-center">
                    <LoaderIcon class="h-8 w-8 animate-spin mx-auto mb-2 text-blue-500" />
                    <p class="text-muted-foreground">Loading agent card...</p>
                  </div>
                </div>
              {:else if agent.agent_card_status === 'error'}
                <div class="flex items-center justify-center py-8">
                  <div class="text-center">
                    <XCircleIcon class="h-8 w-8 mx-auto mb-2 text-red-500" />
                    <p class="text-red-600">Failed to load agent card</p>
                  </div>
                </div>
              {:else if agent.agent_card_status === 'ready' && agent.agent_card}
                <div class="space-y-3">
                  <div>
                    <span class="font-medium">Name:</span>
                    <span class="text-muted-foreground ml-2">{agent.agent_card.name || 'Not set'}</span>
                  </div>
                  <div>
                    <span class="font-medium">Description:</span>
                    <div class="mt-1 max-h-32 overflow-y-auto p-2 bg-gray-50 rounded">
                      <p class="text-muted-foreground text-sm">{agent.agent_card.description || 'No description available'}</p>
                    </div>
                  </div>
                  {#if agent.agent_card.version}
                    <div>
                      <span class="font-medium">Version:</span>
                      <span class="text-muted-foreground ml-2">{agent.agent_card.version}</span>
                    </div>
                  {/if}
                  {#if agent.agent_card.capabilities}
                    <div>
                      <span class="font-medium">Capabilities:</span>
                      <div class="mt-1 text-sm text-muted-foreground">
                        {Object.keys(agent.agent_card.capabilities).join(', ')}
                      </div>
                    </div>
                  {/if}
                </div>
              {:else}
                <div class="text-center py-8">
                  <p class="text-muted-foreground">No agent card available</p>
                </div>
              {/if}
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
                
                {#if agent.elo?.rating && agent.elo?.stats}
                  <div>
                    <span class="font-medium">ELO Rating:</span>
                    <span class="text-muted-foreground ml-2">{agent.elo.rating}</span>
                  </div>
                  <div>
                    <span class="font-medium">Win Rate:</span>
                    <span class="text-muted-foreground ml-2">{((agent.elo.stats.win_rate || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div>
                    <span class="font-medium">Total Battles:</span>
                    <span class="text-muted-foreground ml-2">{agent.elo.stats?.games_played || 0}</span>
                  </div>
                {/if}
              </div>
            </div>
          </div>

          <!-- Right Column -->
          <div class="space-y-8">
            <!-- Agent Instances Section -->
            <div class="bg-white border rounded-lg p-6">
              <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold">Agent Instances</h2>
                {#if isLoadingInstances}
                  <LoaderIcon class="h-4 w-4 animate-spin" />
                {/if}
              </div>

              {#if instancesError}
                <div class="text-center py-4">
                  <p class="text-red-600">{instancesError}</p>
                </div>
              {:else if agentInstances.length === 0 && !isLoadingInstances}
                <div class="text-center py-8">
                  <p class="text-muted-foreground">No instances found</p>
                </div>
              {:else}
                <div class="space-y-4">
                  {#each agentInstances as instance}
                    <div class="border rounded-lg p-4 space-y-3">
                      <div class="flex items-center justify-between">
                        <span class="font-medium text-sm">Instance ID:</span>
                        <span class="text-xs font-mono text-muted-foreground">{instance.agent_instance_id}</span>
                      </div>
                      
                      <div class="grid grid-cols-1 gap-2 text-sm">
                        <div>
                          <span class="font-medium">Agent URL:</span>
                          <p class="text-muted-foreground font-mono text-xs mt-1 break-all">{instance.agent_url}</p>
                        </div>
                        <div>
                          <span class="font-medium">Launcher URL:</span>
                          <p class="text-muted-foreground font-mono text-xs mt-1 break-all">{instance.launcher_url}</p>
                        </div>
                      </div>

                      <div class="flex items-center justify-between pt-2 border-t">
                        <div class="flex items-center gap-4">
                          <div class="flex items-center gap-2">
                            <span class="text-sm font-medium">Ready:</span>
                            <span class="text-sm {instance.ready ? 'text-green-600' : 'text-gray-500'}">
                              {instance.ready ? 'Yes' : 'No'}
                            </span>
                          </div>
                          <div class="flex items-center gap-2">
                            <span class="text-sm font-medium">Locked:</span>
                            <span class="text-sm {instance.is_locked ? 'text-orange-600' : 'text-gray-500'}">
                              {instance.is_locked ? 'Yes' : 'No'}
                            </span>
                          </div>
                        </div>
                        <div class="flex items-center gap-2">
                          <span class="text-xs px-2 py-1 rounded-full {getDockerStatusColor(instance.docker_status)}">
                            {instance.docker_status}
                          </span>
                        </div>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Participant Requirements -->
        {#if agent.participant_requirements && agent.participant_requirements?.length > 0}
          <div class="mt-8 bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Competitor Requirements</h2>
            <div class="grid gap-3">
              {#each agent.participant_requirements as req}
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
        {#if agent?.battle_timeout && agent?.participant_requirements}
          <div class="mt-8 bg-white border rounded-lg p-6">
            <h2 class="text-xl font-semibold mb-4">Battle Configuration</h2>
            <div class="space-y-3">
              <div>
                <span class="font-medium">Battle Timeout:</span>
                <span class="text-muted-foreground ml-2">{agent.battle_timeout} seconds</span>
              </div>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>
