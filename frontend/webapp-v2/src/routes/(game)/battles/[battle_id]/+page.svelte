<script lang="ts">
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { getBattleById } from "$lib/api/battles";
  import { getAgentById } from "$lib/api/agents";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import MoveLeftIcon from "@lucide/svelte/icons/move-left";

  let { data } = $props<{ data: { battle: any } }>();
  
  let battle = $state<any>(data.battle);
  let greenAgent = $state<any>(null);
  let opponentAgents = $state<any[]>([]);
  let loading = $state(true);
  let ws: WebSocket | null = null;
  let selectedLog = $state<any>(null);

  // Group logs by reported_by
  let logsByAgent = $derived(() => {
    console.log('Battle interact_history:', battle.interact_history);
    if (!battle.interact_history || !Array.isArray(battle.interact_history)) return {};
    
    const grouped: Record<string, any[]> = {};
    battle.interact_history.forEach((log: any, index: number) => {
      console.log(`Log ${index}:`, log);
      console.log(`Log ${index} keys:`, Object.keys(log));
      
      // Try different possible fields for reported_by
      const agent = log.reported_by || log.reportedBy || log.agent || log.agent_name || log.agentName || 'system';
      console.log(`Log ${index} agent:`, agent);
      
      if (!grouped[agent]) {
        grouped[agent] = [];
      }
      grouped[agent].push(log);
    });
    
    console.log('Grouped logs:', grouped);
    return grouped;
  });

  // Load agent data
  async function loadAgentData() {
    try {
      loading = true;
      
      // Load battle data if not already loaded
      if (!battle.interact_history) {
        console.log('Loading battle data...');
        const battleData = await getBattleById(battle.battle_id);
        battle = { ...battle, ...battleData };
        console.log('Loaded battle data:', battle);
      }
      
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

  // Setup WebSocket for real-time updates
  function setupWebSocket() {
    ws = new WebSocket(
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      window.location.host +
      '/ws/battles'
    );

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg && msg.type === 'battle_update' && msg.battle && msg.battle.battle_id === battle.battle_id) {
          // Update battle data
          battle = { ...battle, ...msg.battle };
        }
      } catch (e) {
        console.error('[WS] JSON parse error', e);
      }
    };
  }

  function getStatusColor(state: string) {
    switch (state?.toLowerCase()) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'queued':
        return 'bg-yellow-100 text-yellow-800';
      case 'pending':
        return 'bg-blue-100 text-blue-800';
      case 'finished':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  function getStatusText(state: string) {
    switch (state?.toLowerCase()) {
      case 'running':
        return 'Running';
      case 'queued':
        return battle.queue_position ? `Queued (#${battle.queue_position})` : 'Queued';
      case 'pending':
        return 'Pending';
      case 'finished':
        return 'Finished';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  }

  function formatTimestamp(timestamp: string) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  }

  function getLogIcon(log: any) {
    if (log.is_result) return '🏆';
    return '•';
  }

  onMount(() => {
    loadAgentData();
    setupWebSocket();
  });
</script>

<div class="h-screen flex flex-col">
  <!-- Header -->
  <div class="flex items-center justify-between p-4 border-b bg-white">
    <div>
      <h1 class="text-xl font-semibold">Battle {battle.battle_id?.slice(0, 8)}</h1>
      <p class="text-sm text-gray-600">Battle Details</p>
    </div>
    <Button onclick={() => goto('/battles')} variant="outline" size="sm">
      <MoveLeftIcon class="h-4 w-4" />
    </Button>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <span class="ml-3 text-lg">Loading battle details...</span>
    </div>
  {:else}
        <!-- Main Content -->
    <div class="flex-1 p-4">
      <div class="bg-white rounded-lg shadow-sm border h-full flex overflow-hidden">
        <!-- Left Side - Logs by Agent -->
        <div class="w-1/2 border-r bg-gray-50 overflow-y-auto">
          <div class="p-4">
            {#if battle.interact_history && battle.interact_history.length > 0}
              {#if Object.keys(logsByAgent).length > 0}
                {#each Object.entries(logsByAgent) as [agent, logs]}
                  <div class="mb-6">
                    <!-- Agent Header -->
                    <div class="font-medium text-sm text-gray-900 mb-3 px-3 py-2 bg-white rounded-lg shadow-sm">
                      {agent}
                    </div>
                    
                    <!-- Logs for this agent -->
                    <div class="space-y-1 ml-4">
                      {#each logs as log}
                        <div 
                          class="p-2 bg-white rounded cursor-pointer hover:bg-gray-50 transition-colors {selectedLog === log ? 'bg-blue-50 border border-blue-200' : ''}"
                          onclick={() => selectedLog = log}
                        >
                          <div class="text-xs font-medium text-gray-900">
                            {log.is_result ? 'Battle Result' : log.message || 'System Event'}
                          </div>
                        </div>
                      {/each}
                    </div>
                  </div>
                {/each}
              {:else}
                <!-- Fallback: show logs without grouping if they don't have reported_by -->
                <div class="mb-6">
                  <div class="mb-3">
                    <AgentChip
                      agent={{
                        identifier: "System Logs",
                        avatar_url: undefined,
                        description: "System events and logs"
                      }}
                      agent_id="system"
                      isOnline={false}
                    />
                  </div>
                  <div class="space-y-1 ml-4">
                    {#each battle.interact_history as log}
                      <div 
                        class="p-2 bg-white rounded cursor-pointer hover:bg-gray-50 transition-colors {selectedLog === log ? 'bg-blue-50 border border-blue-200' : ''}"
                        onclick={() => selectedLog = log}
                      >
                        <div class="text-xs font-medium text-gray-900">
                          {log.is_result ? 'Battle Result' : log.message || 'System Event'}
                        </div>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            {:else}
              <div class="text-center py-8">
                <p class="text-muted-foreground text-sm">No activity yet</p>
              </div>
            {/if}
          </div>
        </div>

        <!-- Right Side - Details -->
        <div class="w-1/2 overflow-y-auto">
          {#if selectedLog}
            <div class="p-6">
              <div class="bg-white rounded-lg shadow-sm border p-6">
                <h2 class="text-lg font-semibold mb-4">Log Details</h2>
                <div class="space-y-4">
                  <!-- Basic Info -->
                  <div>
                    <h3 class="text-sm font-medium text-gray-700 mb-1">Message</h3>
                    <p class="text-sm bg-gray-100 p-3 rounded">{selectedLog.message || 'No message'}</p>
                  </div>

                  <!-- Reported By -->
                  <div>
                    <h3 class="text-sm font-medium text-gray-700 mb-1">Reported By</h3>
                    <div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {selectedLog.reported_by || 'Unknown'}
                    </div>
                  </div>

                  <!-- Timestamp -->
                  {#if selectedLog.timestamp}
                    <div>
                      <h3 class="text-sm font-medium text-gray-700 mb-1">Timestamp</h3>
                      <p class="text-sm">{formatTimestamp(selectedLog.timestamp)}</p>
                    </div>
                  {/if}

                  <!-- Is Result -->
                  <div>
                    <h3 class="text-sm font-medium text-gray-700 mb-1">Type</h3>
                    <div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {selectedLog.is_result ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}">
                      {selectedLog.is_result ? 'Battle Result' : 'Log Entry'}
                    </div>
                  </div>

                  <!-- Winner (if result) -->
                  {#if selectedLog.is_result && selectedLog.winner}
                    <div>
                      <h3 class="text-sm font-medium text-gray-700 mb-1">Winner</h3>
                      <p class="text-sm font-medium">{selectedLog.winner}</p>
                    </div>
                  {/if}

                  <!-- Details -->
                  {#if selectedLog.detail}
                    <div>
                      <h3 class="text-sm font-medium text-gray-700 mb-1">Details</h3>
                      <pre class="text-xs bg-gray-100 p-3 rounded overflow-x-auto">{JSON.stringify(selectedLog.detail, null, 2)}</pre>
                    </div>
                  {/if}

                  <!-- Markdown Content -->
                  {#if selectedLog.markdown_content}
                    <div>
                      <h3 class="text-sm font-medium text-gray-700 mb-1">Content</h3>
                      <div class="text-sm bg-gray-100 p-3 rounded whitespace-pre-wrap">{selectedLog.markdown_content}</div>
                    </div>
                  {/if}

                  <!-- Raw JSON Data -->
                  <div>
                    <h3 class="text-sm font-medium text-gray-700 mb-1">Raw Data</h3>
                    <pre class="text-xs bg-gray-100 p-3 rounded overflow-x-auto">{JSON.stringify(selectedLog, null, 2)}</pre>
                  </div>
                </div>
              </div>
            </div>
          {:else}
            <div class="flex items-center justify-center h-full">
              <div class="text-center">
                <p class="text-gray-500 text-sm">Select a log entry to view details</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div> 