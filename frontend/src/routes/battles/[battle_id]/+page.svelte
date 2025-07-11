<script lang="ts">
import { onMount } from 'svelte';
import { page } from '$app/stores';

let battle: any = null;
let loading = true;
let error = '';
let greenAgentName = '';
let opponentNames: string[] = [];
let ws: WebSocket | null = null;

$: battleId = $page.params.battle_id;

async function fetchAgentName(agentId: string): Promise<string> {
  try {
    const res = await fetch(`http://localhost:9000/agents/${agentId}`);
    if (!res.ok) return agentId;
    const agent = await res.json();
    return agent.register_info?.name || agent.registerInfo?.name || agent.agent_card?.name || agent.agentCard?.name || agentId;
  } catch {
    return agentId;
  }
}

onMount(async () => {
  loading = true;
  error = '';
  try {
    const res = await fetch(`http://localhost:9000/battles/${battleId}`);
    if (!res.ok) throw new Error('Failed to fetch battle');
    battle = await res.json();
    greenAgentName = await fetchAgentName(battle.green_agent_id || battle.greenAgentId);
    opponentNames = [];
    for (const op of (battle.opponents || [])) {
      if (op && typeof op === 'object' && op.agent_id) {
        const agentName = await fetchAgentName(op.agent_id);
        opponentNames.push(`${agentName} (${op.name})`);
      } else if (typeof op === 'string') {
        // fallback for string IDs
        opponentNames.push(await fetchAgentName(op));
      } else {
        opponentNames.push('Unknown');
      }
    }
    // --- WebSocket for live updates ---
    ws = new WebSocket('ws://localhost:9000/ws/battles');
    ws.onmessage = async (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg && msg.type === 'battle_update' && msg.battle && msg.battle.battle_id === battleId) {
          battle = msg.battle;
          greenAgentName = await fetchAgentName(battle.green_agent_id || battle.greenAgentId);
          opponentNames = [];
          for (const op of (battle.opponents || [])) {
            if (op && typeof op === 'object' && op.agent_id) {
              const agentName = await fetchAgentName(op.agent_id);
              opponentNames.push(`${agentName} (${op.name})`);
            } else if (typeof op === 'string') {
              opponentNames.push(await fetchAgentName(op));
            } else {
              opponentNames.push('Unknown');
            }
          }
        }
      } catch (e) {
        // ignore
      }
    };
  } catch (e) {
    error = e instanceof Error ? e.message : 'Unknown error';
  } finally {
    loading = false;
  }
});

import { onDestroy } from 'svelte';
onDestroy(() => { if (ws) ws.close(); });
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
      <div class="flex flex-col gap-3 mt-6">
        <h2 class="text-lg font-semibold mb-2">Interact History</h2>
        {#each battle.interact_history as entry, i (entry.timestamp + entry.message + i)}
          <div class="border rounded-lg p-3 bg-background/80">
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
      </div>
    {/if}
  {/if}
</main> 