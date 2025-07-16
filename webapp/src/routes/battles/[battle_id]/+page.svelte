<script lang="ts">
import { onMount } from 'svelte';
import { page } from '$app/stores';

let battle: any = null;
let loading = true;
let error = '';
let greenAgentName = '';
let opponentNames: string[] = [];
let ws: WebSocket | null = null;
let greenAgentInfo: any = null;
let opponentRoleMap = new Map<string, string>(); // name -> role mapping
let interactHistoryContainer: HTMLDivElement | null = null;

$: battleId = $page.params.battle_id;

$: battleInProgress = battle ? isBattleInProgress() : false;

async function fetchAgentName(agentId: string): Promise<string> {
  try {
    const res = await fetch(`/api/agents/${agentId}`);
    if (!res.ok) return agentId;
    const agent = await res.json();
    return agent.register_info?.name || agent.registerInfo?.name || agent.agent_card?.name || agent.agentCard?.name || agentId;
  } catch {
    return agentId;
  }
}

async function fetchGreenAgentInfo(agentId: string): Promise<any> {
  try {
    const res = await fetch(`/api/agents/${agentId}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function buildOpponentRoleMap(greenAgentInfo: any, battleOpponents: any[]): Map<string, string> {
  const roleMap = new Map<string, string>();
  
  if (!greenAgentInfo.register_info?.participant_requirements || !Array.isArray(battleOpponents)) {
    return roleMap;
  }
  
  const participantReqs = greenAgentInfo.register_info.participant_requirements;
  
  for (const opponent of battleOpponents) {
    const matchedReq = participantReqs.find((req: any) => req.name === opponent.name);
    if (matchedReq && matchedReq.role) {
      roleMap.set(opponent.name, matchedReq.role);
    }
  }
  
  // in case reported_by is simplified
  for (const req of participantReqs) {
    if (req.name && req.role) {
      roleMap.set(req.name, req.role);
      const simpleName = req.name.split(' (')[0].trim();
      if (simpleName !== req.name) {
        roleMap.set(simpleName, req.role);
      }
    }
  }
  
  return roleMap;
}

function getEntryBackgroundClass(reportedBy: string): string {
  if (reportedBy === 'system') {
    return 'bg-gray-50 border-gray-200';
  } else if (reportedBy === 'green_agent') {
    return 'bg-green-50 border-green-200';
  } else if (opponentRoleMap.has(reportedBy)) {
    const role = opponentRoleMap.get(reportedBy);
    if (role === 'blue_agent') {
      return 'bg-blue-50 border-blue-200';
    } else if (role === 'red_agent') {
      return 'bg-red-50 border-red-200';
    }
  }
  // Default background for unknown reported_by
  return 'bg-yellow-50 border-yellow-200';
}

function scrollToBottom() {
  if (interactHistoryContainer) {
    setTimeout(() => {
      interactHistoryContainer?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end' 
      });
    }, 100);
  }
}

function isBattleInProgress(): boolean {
  if (!battle) return false;
  
  if (battle.state === 'finished' || battle.state === 'error') {
    return false;
  }
  
  if (battle.interact_history && Array.isArray(battle.interact_history)) {
    return !battle.interact_history.some((entry: any) => entry.is_result);
  }
  
  return true;
}

onMount(async () => {
  loading = true;
  error = '';
  try {
    const res = await fetch(`/api/battles/${battleId}`);
    if (!res.ok) {
      error = 'Failed to load battle';
      return;
    }
    battle = await res.json();
    
    // Fetch agent names
    if (battle.green_agent_id) {
      greenAgentName = await fetchAgentName(battle.green_agent_id);
      greenAgentInfo = await fetchGreenAgentInfo(battle.green_agent_id);
    }
    if (battle.opponents && Array.isArray(battle.opponents)) {
      opponentNames = await Promise.all(
        battle.opponents.map(async (opponent: any) => {
          const agentName = await fetchAgentName(opponent.agent_id);
          return `${agentName} (${opponent.name})`;
        })
      );
      
      if (greenAgentInfo) {
        opponentRoleMap = buildOpponentRoleMap(greenAgentInfo, battle.opponents);
      }
    }
    
    // Connect to WebSocket for real-time updates
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/battles`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Connected to battles WebSocket');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'battle_update' && data.battle.battle_id === battleId) {
        const previousHistoryLength = battle?.interact_history?.length || 0;
        
        // create a new battle object to trigger Svelte's reactivity
        battle = { ...data.battle };
        
        // Update agent names if needed
        if (battle.green_agent_id && !greenAgentName) {
          fetchAgentName(battle.green_agent_id).then(name => greenAgentName = name);
        }
        if (battle.opponents && Array.isArray(battle.opponents)) {
          Promise.all(battle.opponents.map(async (opponent: any) => {
            const agentName = await fetchAgentName(opponent.agent_id);
            return `${agentName} (${opponent.name})`;
          })).then(names => opponentNames = names);
        }
        
        // Auto-scroll if new interact history entries were added
        const currentHistoryLength = battle?.interact_history?.length || 0;
        if (currentHistoryLength > previousHistoryLength) {
          scrollToBottom();
        }
        
        // Also scroll when battle state changes (for loading indicator updates)
        if (battle.state === 'finished' || battle.state === 'error') {
          console.log('Battle finished, triggering scroll');
          scrollToBottom();
        }
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket connection closed');
    };
    
  } catch (err) {
    error = 'Failed to load battle';
    console.error(err);
  } finally {
    loading = false;
  }
});

// Cleanup function
import { onDestroy } from 'svelte';
onDestroy(() => {
  if (ws) {
    ws.close();
  }
});
</script>

<main class="p-4 flex flex-col min-h-[60vh] max-w-xl mx-auto">
  {#if loading}
    <div>Loading...</div>
  {:else if error}
    <div class="text-red-500">{error}</div>
  {:else if battle}
    <div class="mb-8 space-y-2 border-b pb-4">
      <h1 class="text-2xl font-bold">Battle #{battle.battle_id?.slice(0, 8)}</h1>
      <div class="text-sm text-muted-foreground font-mono break-all">ID: {battle.battle_id}</div>
      <div class="text-sm text-muted-foreground">State: <span class="font-mono">{battle.state}</span></div>
      <div class="text-sm text-muted-foreground">Green Agent: <span class="font-mono">{greenAgentName}</span></div>
      <div class="text-sm text-muted-foreground">Opponents: <span class="font-mono">{opponentNames.join(', ')}</span></div>
      {#if battle.result && battle.state === 'finished'}
        <div class="text-green-700">Winner: <span class="font-mono">{battle.result.winner}</span></div>
      {/if}
      {#if battle.error && battle.state === 'error'}
        <div class="text-red-700">Error: <span class="font-mono">{battle.error}</span></div>
      {/if}
    </div>
    <!-- Interact History -->
    {#if battle.interact_history && battle.interact_history.length > 0}
      <div class="flex flex-col gap-3 mt-6" bind:this={interactHistoryContainer}>
        <h2 class="text-lg font-semibold mb-2">Interact History</h2>
        {#each battle.interact_history as entry, i (entry.timestamp + entry.message + i)}
          <div class="border rounded-lg p-3 {getEntryBackgroundClass(entry.reported_by)}">
            <div class="flex flex-row justify-between items-center mb-1">
              <span class="font-mono text-xs text-muted-foreground">{new Date(entry.timestamp).toLocaleString()}</span>
              <span class="text-xs px-2 py-0.5 rounded bg-muted text-muted-foreground">{entry.reported_by}</span>
              {#if entry.is_result}
                <span class="text-xs font-bold text-green-700 ml-2">Result</span>
              {/if}
            </div>
            <div class="text-sm font-medium mb-1">{entry.message}</div>
            {#if entry.detail}
              <pre class="text-xs bg-muted p-2 rounded overflow-x-auto mt-1">{JSON.stringify(entry.detail, null, 2)}</pre>
            {/if}
            {#if entry.winner}
              <div class="text-xs text-green-700 mt-1">Winner: <span class="font-mono">{entry.winner}</span></div>
            {/if}
          </div>
        {/each}
        
        <!-- Loading indicator for battles in progress -->
        {#if battleInProgress}
          <div class="border rounded-lg p-4 bg-purple-50 border-purple-200 flex items-center justify-center space-x-3">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
            <span class="text-sm text-purple-700 font-medium">Battle in progress...</span>
          </div>
        {/if}
      </div>
    {:else if battle && battleInProgress}
      <!-- Show loading if no history yet but battle is starting -->
      <div class="flex flex-col gap-3 mt-6" bind:this={interactHistoryContainer}>
        <h2 class="text-lg font-semibold mb-2">Interact History</h2>
        <div class="border rounded-lg p-4 bg-purple-50 border-purple-200 flex items-center justify-center space-x-3">
          <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600"></div>
          <span class="text-sm text-purple-700 font-medium">Waiting for battle to start...</span>
        </div>
      </div>
    {/if}
  {/if}
</main> 