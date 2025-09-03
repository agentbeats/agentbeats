<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { goto } from "$app/navigation";
  import { getAllBattles } from "$lib/api/battles";
  import { getAllAgents } from "$lib/api/agents";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import * as ScrollArea from "$lib/components/ui/scroll-area";
  import { onMount, onDestroy } from 'svelte';
  import { Spinner } from "$lib/components/ui/spinner";

  let { battle } = $props<{
    battle: {
      battle_id?: string;
      state?: string;
      green_agent_id?: string;
      opponents?: Array<{ name: string; agent_id: string }>;
      interact_history?: Array<any>;
      created_at?: string;
      queue_position?: number;
    };
  }>();

  let allAgents = $state<any[]>([]);
  let greenAgent = $state<any>(null);
  let opponentAgents = $state<any[]>([]);
  let battleLogs = $state<any[]>([]);
  let loading = $state(true);
  let ws: WebSocket | null = null;

  // Load agent data
  async function loadAgentData() {
    try {
      loading = true;
      
      // Load all agents - use the same approach as my-agents page
      allAgents = await getAllAgents();
      console.log('Ongoing battle card - loaded agents:', allAgents);
      console.log('Ongoing battle card - battle:', battle);
      
      // Find green agent
      if (battle.green_agent_id) {
        greenAgent = allAgents.find((agent: any) => 
          agent.agent_id === battle.green_agent_id || agent.id === battle.green_agent_id
        );
        console.log('Ongoing battle card - found green agent:', greenAgent);
        if (greenAgent) {
          console.log('Green agent structure:', {
            register_info: greenAgent.register_info,
            agent_card: greenAgent.agent_card,
            agent_id: greenAgent.agent_id,
            id: greenAgent.id
          });
        }
      }

      // Find opponent agents
      if (battle.opponents && battle.opponents.length > 0) {
        opponentAgents = [];
        for (const opponent of battle.opponents) {
          console.log('Ongoing battle card - looking for opponent:', opponent);
          const agent = allAgents.find((a: any) => 
            a.agent_id === opponent.agent_id || a.id === opponent.agent_id
          );
          console.log('Ongoing battle card - found opponent agent:', agent);
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
        console.log('Ongoing battle card - final opponent agents:', opponentAgents);
      }

      // Load initial battle logs
      if (battle.interact_history) {
        battleLogs = battle.interact_history.slice(-5); // Get last 5 logs
      }

    } catch (error) {
      console.error('Failed to load battle data:', error);
      allAgents = [];
    } finally {
      loading = false;
    }
  }

  // Setup WebSocket connections
  function setupWebSockets() {
    if (!battle.battle_id) return;

    // Main battles WebSocket for battle updates
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
          // Update logs if available
          if (msg.battle.interact_history) {
            battleLogs = msg.battle.interact_history.slice(-5);
          }
        }
      } catch (e) {
        console.error('[WS] JSON parse error', e);
      }
    };
  }

  function handleCardClick() {
    if (battle.battle_id) {
      goto(`/battles/${battle.battle_id}`);
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
      case 'finished':
        return 'bg-muted text-muted-foreground';
      case 'error':
        return 'bg-destructive/10 text-destructive';
      default:
        return 'bg-muted text-muted-foreground';
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

  function shortId(id: string) {
    return id ? id.slice(0, 8) : '';
  }

  function formatTimestamp(timestamp: string) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  }

  function getLogIcon(log: any) {
    if (log.is_result) return '🏆';
    return '•';
  }

  onMount(() => {
    loadAgentData();
    setupWebSockets();
  });

  onDestroy(() => {
    if (ws) ws.close();
  });
</script>

<div class="w-full space-y-6">
  <!-- Simple top card with green agent chip -->
  <button 
    onclick={handleCardClick}
    class="w-full p-6 border rounded-lg bg-card hover:bg-muted hover:border-border transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 cursor-pointer"
  >
    <div class="flex flex-col items-center space-y-3">
      {#if greenAgent && (greenAgent.register_info || greenAgent.agent_card)}
        <div class="text-foreground">
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
      {:else if greenAgent}
        <p class="text-sm text-muted-foreground">Agent data incomplete</p>
      {:else}
        <p class="text-sm text-muted-foreground">Loading...</p>
      {/if}
      
      <div class="text-center space-y-1">
        <div class="text-sm text-foreground font-mono">
          #{shortId(battle.battle_id || '')}
        </div>
        {#if battle.created_at}
          <div class="text-xs text-foreground">
            {formatTimestamp(battle.created_at)}
          </div>
        {/if}
      </div>
    </div>
  </button>

  <!-- Two cards below -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Competitor Information Card -->
    <Card.Root class="border shadow-sm bg-background">
      <Card.Header>
        <Card.Title class="text-lg font-semibold">Competitors</Card.Title>
        <Card.Description>
          Opponent agents in this battle
        </Card.Description>
      </Card.Header>
      <Card.Content>
        <div class="space-y-4">
          {#if loading}
                          <div class="flex items-center justify-center py-8">
                <Spinner size="md" />
                <span class="ml-2 text-sm">Loading agents...</span>
              </div>
          {:else if opponentAgents.length > 0}
            <!-- Opponent Agents - one per row -->
            <ScrollArea.Root class="h-[300px]">
              <div class="space-y-3">
                {#each opponentAgents as agent}
                  <div class="w-full flex items-center justify-between">
                    {#if agent.register_info || agent.agent_card}
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
                    {:else}
                      <span class="text-sm text-muted-foreground">Agent data incomplete</span>
                    {/if}
                    <span class="text-xs text-muted-foreground font-medium">
                      {agent.role || 'Unknown Role'}
                    </span>
                  </div>
                {/each}
              </div>
            </ScrollArea.Root>
          {:else}
            <div class="text-center py-8">
              <p class="text-muted-foreground text-sm">No opponent information available</p>
            </div>
          {/if}
        </div>
      </Card.Content>
    </Card.Root>

    <!-- Recent Logs Card -->
    <Card.Root class="border shadow-sm bg-background lg:col-span-2">
      <Card.Header>
        <Card.Title class="text-lg font-semibold">Recent Activity</Card.Title>
        <Card.Description>
          Latest battle events and interactions
        </Card.Description>
      </Card.Header>
      <Card.Content>
        <ScrollArea.Root class="h-[300px]">
          <div class="space-y-3">
            {#if battleLogs.length > 0}
                          {#each battleLogs as log}
              <div class="flex items-start space-x-3 p-3 border rounded-lg">
                <div class="text-lg flex-shrink-0">
                  {getLogIcon(log)}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium">
                    {log.is_result ? 'Battle Result' : log.message || 'System Event'}
                  </p>
                  {#if log.detail}
                    <p class="text-xs text-muted-foreground">
                      {typeof log.detail === 'string' ? log.detail : JSON.stringify(log.detail)}
                    </p>
                  {/if}
                  {#if log.timestamp}
                    <p class="text-xs text-muted-foreground">
                      {formatTimestamp(log.timestamp)}
                    </p>
                  {/if}
                </div>
                {#if log.reported_by}
                  <div class="flex-shrink-0">
                    <div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                      {log.reported_by}
                    </div>
                  </div>
                {/if}
              </div>
            {/each}
            {:else}
              <div class="text-center py-8">
                <p class="text-muted-foreground text-sm">No recent activity</p>
              </div>
            {/if}
          </div>
        </ScrollArea.Root>
      </Card.Content>
    </Card.Root>
  </div>
</div>
