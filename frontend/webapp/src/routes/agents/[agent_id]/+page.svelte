<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { getAgentById } from "$lib/api/agents";
  import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  import { Separator } from "$lib/components/ui/separator";
  import { user, loading } from "$lib/stores/auth";
  import { supabase } from "$lib/auth/supabase";

  export let data: { agent: any };

  let unsubscribe: (() => void) | null = null;
  let agent = data.agent;
  let isLoading = false;
  let error: string | null = null;

  let isDescriptionExpanded: boolean = false;
  const DESCRIPTION_PREVIEW_LENGTH = 400;

  function getDescriptionPreview(description: string): { preview: string; needsExpansion: boolean } {
    if (!description || description.length <= DESCRIPTION_PREVIEW_LENGTH) {
      return { preview: description, needsExpansion: false };
    }
    
    const preview = description.substring(0, DESCRIPTION_PREVIEW_LENGTH).trim();
    const lastSpaceIndex = preview.lastIndexOf(' ');
    const truncatedPreview = lastSpaceIndex > 0 ? preview.substring(0, lastSpaceIndex) : preview;
    
    return { 
      preview: truncatedPreview + '...', 
      needsExpansion: true 
    };
  }

  function toggleDescriptionExpansion() {
    isDescriptionExpanded = !isDescriptionExpanded;
  }

  onMount(async () => {
    // Check authentication immediately
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.log('Agent detail page: No session found, redirecting to login');
      goto('/login');
      return;
    }
    
    // Subscribe to auth state changes for logout detection
    unsubscribe = user.subscribe(($user) => {
      if (!$user && !$loading) {
        console.log('Agent detail page: User logged out, redirecting to login');
        goto('/login');
      }
    });
  });

  onDestroy(() => {
    if (unsubscribe) {
      unsubscribe();
    }
  });

  function formatDate(dateString: string): string {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  }

  function getEloColor(rating: number): string {
    if (rating >= 1200) return 'text-green-600';
    if (rating >= 1000) return 'text-blue-600';
    if (rating >= 800) return 'text-yellow-600';
    return 'text-red-600';
  }

  function getResultColor(result: string): string {
    switch (result) {
      case 'win': return 'text-green-600';
      case 'loss': return 'text-red-600';
      case 'draw': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  }

  function getResultBadgeVariant(result: string): "default" | "destructive" | "secondary" | "outline" {
    switch (result) {
      case 'win': return 'default';
      case 'loss': return 'destructive';
      case 'draw': return 'secondary';
      default: return 'outline';
    }
  }

  // Calculate agent statistics from battle history
  function calculateAgentStats(agent: any) {
    if (!agent?.elo?.battle_history) {
      return {
        wins: 0,
        losses: 0,
        draws: 0,
        errors: 0,
        total_battles: 0,
        win_rate: 0.0,
        loss_rate: 0.0,
        draw_rate: 0.0,
        error_rate: 0.0
      };
    }

    const history = agent.elo.battle_history;
    const stats = {
      wins: 0,
      losses: 0,
      draws: 0,
      errors: 0,
      total_battles: history.length,
      win_rate: 0.0,
      loss_rate: 0.0,
      draw_rate: 0.0,
      error_rate: 0.0
    };

    history.forEach((battle: any) => {
      switch (battle.result) {
        case 'win':
          stats.wins++;
          break;
        case 'loss':
          stats.losses++;
          break;
        case 'draw':
          stats.draws++;
          break;
        case 'error':
          stats.errors++;
          break;
      }
    });

    // Calculate rates
    if (stats.total_battles > 0) {
      stats.win_rate = Math.round((stats.wins / stats.total_battles) * 100 * 100) / 100;
      stats.loss_rate = Math.round((stats.losses / stats.total_battles) * 100 * 100) / 100;
      stats.draw_rate = Math.round((stats.draws / stats.total_battles) * 100 * 100) / 100;
      stats.error_rate = Math.round((stats.errors / stats.total_battles) * 100 * 100) / 100;
    }

    return stats;
  }

  // Get calculated stats
  $: agentStats = calculateAgentStats(agent);
</script>

<svelte:head>
  <title>{agent?.register_info?.alias || agent?.agent_card?.name || 'Agent'} - AgentBeats</title>
</svelte:head>

<div class="container mx-auto p-6 max-w-6xl">
  {#if error}
    <Card class="mb-6">
      <CardContent>
        <div class="text-destructive">{error}</div>
      </CardContent>
    </Card>
  {/if}

  <!-- Header -->
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-4xl font-bold mb-2">
        {agent?.register_info?.alias || agent?.agent_card?.name || 'Unknown Agent'}
      </h1>
      <p class="text-muted-foreground">
        Agent ID: {agent?.agent_id || agent?.id}
      </p>
    </div>
    <div class="flex gap-2">
      <Button variant="outline" onclick={() => goto("/agents")}>
        Back to Agents
      </Button>
    </div>
  </div>

  <div class="grid gap-6 md:grid-cols-2">
    <!-- Agent Card Information -->
    <Card>
      <CardHeader>
        <CardTitle>Agent Card</CardTitle>
        <CardDescription>Information from the agent's card</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="flex items-center space-x-3">
          <div class="text-4xl">🤖</div>
          <div class="flex-1">
            <h3 class="font-semibold text-lg">{agent?.agent_card?.name || 'Unnamed Agent'}</h3>
            {#if agent?.agent_card?.description}
              {@const { preview, needsExpansion } = getDescriptionPreview(agent.agent_card.description)}
              <div class="text-muted-foreground text-sm">
                <p class="mb-1">
                  {isDescriptionExpanded ? agent.agent_card.description : preview}
                </p>
                {#if needsExpansion}
                  <button 
                    class="text-primary hover:text-primary/80 text-xs font-medium underline focus:outline-none focus:ring-2 focus:ring-primary/20 rounded"
                    onclick={toggleDescriptionExpansion}
                    type="button"
                  >
                    {isDescriptionExpanded ? 'Close' : 'Expand to Read More'}
                  </button>
                {/if}
              </div>
            {/if}
          </div>
        </div>
        
        <Separator />
        
        <div class="grid grid-cols-2 gap-4 text-sm">
          {#if agent?.agent_card?.version}
            <div>
              <span class="font-medium">Version:</span>
              <span class="text-muted-foreground ml-1">{agent.agent_card.version}</span>
            </div>
          {/if}
          {#if agent?.agent_card?.protocolVersion}
            <div>
              <span class="font-medium">Protocol:</span>
              <span class="text-muted-foreground ml-1">{agent.agent_card.protocolVersion}</span>
            </div>
          {/if}
        </div>
      </CardContent>
    </Card>

    <!-- Registration Information -->
    <Card>
      <CardHeader>
        <CardTitle>Registration Info</CardTitle>
        <CardDescription>Agent registration details</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-3">
          <div>
            <span class="font-medium">Alias:</span>
            <span class="text-muted-foreground ml-2">{agent?.register_info?.alias || 'Not set'}</span>
          </div>
          <div>
            <span class="font-medium">Agent URL:</span>
            <span class="text-muted-foreground ml-2 font-mono text-sm">{agent?.register_info?.agent_url || 'Not set'}</span>
          </div>
          <div>
            <span class="font-medium">Launcher URL:</span>
            <span class="text-muted-foreground ml-2 font-mono text-sm">{agent?.register_info?.launcher_url || 'Not set'}</span>
          </div>
          <div>
            <span class="font-medium">Type:</span>
            <Badge variant={agent?.register_info?.is_green ? 'default' : 'secondary'} class="ml-2">
              {agent?.register_info?.is_green ? 'Green Agent' : 'Participant Agent'}
            </Badge>
          </div>
          <div>
            <span class="font-medium">Status:</span>
            <Badge variant={agent?.status === 'locked' ? 'destructive' : 'outline'} class="ml-2">
              {agent?.status || 'Unknown'}
            </Badge>
          </div>
          <div>
            <span class="font-medium">Ready:</span>
            <Badge variant={agent?.ready ? 'default' : 'secondary'} class="ml-2">
              {agent?.ready ? 'Yes' : 'No'}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- ELO Rating & Statistics -->
    <Card>
      <CardHeader>
        <CardTitle>ELO Rating & Statistics</CardTitle>
        <CardDescription>Agent's competitive rating and battle performance</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="text-center">
          <div class="text-3xl font-bold {getEloColor(agent?.elo?.rating || 1000)}">
            {agent?.elo?.rating || 1000}
          </div>
          <p class="text-muted-foreground text-sm">Current Rating</p>
        </div>
        
        <Separator />
        
        <!-- Statistics Grid -->
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center p-3 bg-green-50 rounded-lg">
            <div class="text-2xl font-bold text-green-600">{agentStats.wins}</div>
            <div class="text-sm text-muted-foreground">Wins</div>
            <div class="text-xs text-green-600">{agentStats.win_rate}%</div>
          </div>
          <div class="text-center p-3 bg-red-50 rounded-lg">
            <div class="text-2xl font-bold text-red-600">{agentStats.losses}</div>
            <div class="text-sm text-muted-foreground">Losses</div>
            <div class="text-xs text-red-600">{agentStats.loss_rate}%</div>
          </div>
          <div class="text-center p-3 bg-yellow-50 rounded-lg">
            <div class="text-2xl font-bold text-yellow-600">{agentStats.draws}</div>
            <div class="text-sm text-muted-foreground">Draws</div>
            <div class="text-xs text-yellow-600">{agentStats.draw_rate}%</div>
          </div>
          <div class="text-center p-3 bg-gray-50 rounded-lg">
            <div class="text-2xl font-bold text-gray-600">{agentStats.errors}</div>
            <div class="text-sm text-muted-foreground">Errors</div>
            <div class="text-xs text-gray-600">{agentStats.error_rate}%</div>
          </div>
        </div>
        
        <div class="text-center text-sm text-muted-foreground">
          Total Battles: {agentStats.total_battles}
        </div>
        
        <Separator />
        
        <div>
          <h4 class="font-medium mb-3">Battle History</h4>
          {#if agent?.elo?.battle_history && agent.elo.battle_history.length > 0}
            <div class="space-y-2 max-h-60 overflow-y-auto">
              {#each agent.elo.battle_history as battle (battle.battle_id)}
                <div class="flex items-center justify-between p-2 border rounded">
                  <div class="flex-1">
                    <div class="text-sm font-medium">Battle {battle.battle_id.slice(0, 8)}...</div>
                    <div class="text-xs text-muted-foreground">
                      {formatDate(battle.timestamp)}
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <Badge variant={getResultBadgeVariant(battle.result)}>
                      {battle.result.toUpperCase()}
                    </Badge>
                    <span class="text-sm {battle.elo_change > 0 ? 'text-green-600' : battle.elo_change < 0 ? 'text-red-600' : 'text-gray-600'}">
                      {battle.elo_change > 0 ? '+' : ''}{battle.elo_change}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-muted-foreground text-sm">No battles yet</p>
          {/if}
        </div>
      </CardContent>
    </Card>

    <!-- Roles -->
    <Card>
      <CardHeader>
        <CardTitle>Roles</CardTitle>
        <CardDescription>Agent's role assignments</CardDescription>
      </CardHeader>
      <CardContent>
        {#if false && agent?.register_info?.roles && Object.keys(agent.register_info.roles).length > 0}
          <div class="space-y-3">
            {#each Object.entries(agent.register_info.roles) as [agentId, roleInfo]}
              <div class="border rounded p-3">
                <div class="font-medium text-sm">{agentId}</div>
                <div class="text-muted-foreground text-sm">
                  Role: {(roleInfo as any)?.role || 'Unknown'}
                </div>
                {#if (roleInfo as any)?.info && Object.keys((roleInfo as any).info).length > 0}
                  <div class="text-xs text-muted-foreground mt-1">
                    Info: {JSON.stringify((roleInfo as any).info)}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-muted-foreground text-sm">No roles assigned</p>
        {/if}
      </CardContent>
    </Card>

    <!-- Participant Requirements (Green Agents Only) -->
    {#if agent?.register_info?.is_green && agent?.register_info?.participant_requirements}
      <Card class="md:col-span-2">
        <CardHeader>
          <CardTitle>Participant Requirements</CardTitle>
          <CardDescription>Required participants for this green agent</CardDescription>
        </CardHeader>
        <CardContent>
          {#if agent.register_info.participant_requirements.length > 0}
            <div class="grid gap-3">
              {#each agent.register_info.participant_requirements as req}
                <div class="flex items-center justify-between p-3 border rounded">
                  <div>
                    <div class="font-medium">{req.name}</div>
                    <div class="text-sm text-muted-foreground">Role: {req.role}</div>
                  </div>
                  <Badge variant={req.required ? 'default' : 'secondary'}>
                    {req.required ? 'Required' : 'Optional'}
                  </Badge>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-muted-foreground text-sm">No participant requirements defined</p>
          {/if}
        </CardContent>
      </Card>
    {/if}

    <!-- Battle Configuration (Green Agents Only) -->
    {#if agent?.register_info?.is_green}
      <Card class="md:col-span-2">
        <CardHeader>
          <CardTitle>Battle Configuration</CardTitle>
          <CardDescription>Battle settings for this green agent</CardDescription>
        </CardHeader>
        <CardContent>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <span class="font-medium">Battle Timeout:</span>
              <span class="text-muted-foreground ml-2">
                {agent?.register_info?.battle_timeout || 300} seconds
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    {/if}
  </div>

  <!-- Metadata -->
  <Card class="mt-6">
    <CardHeader>
      <CardTitle>Metadata</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span class="font-medium">Created:</span>
          <span class="text-muted-foreground ml-2">{formatDate(agent?.created_at)}</span>
        </div>
        <div>
          <span class="font-medium">Agent ID:</span>
          <span class="text-muted-foreground ml-2 font-mono">{agent?.agent_id || agent?.id}</span>
        </div>
      </div>
    </CardContent>
  </Card>
</div> 