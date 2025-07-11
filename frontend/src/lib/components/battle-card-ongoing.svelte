<script lang="ts">
import { onMount } from "svelte";
import * as Card from "./ui/card/index.js";
import { getAgentById } from "$lib/api/agents";

export let battleId: string;
let battle: any = null;
let loading = true;
let error: string | null = null;

let greenAgent: any = null;
let opponentAgents: any[] = [];

onMount(async () => {
  loading = true;
  error = null;
  try {
    const res = await fetch(`http://localhost:9000/battles/${battleId}`);
    if (!res.ok) throw new Error('Failed to fetch battle');
    battle = await res.json();
    // Fetch green agent
    if (battle.green_agent_id || battle.greenAgentId) {
      try {
        greenAgent = await getAgentById(battle.green_agent_id || battle.greenAgentId);
      } catch { greenAgent = null; }
    }
    // Fetch all opponent agents
    opponentAgents = [];
    if (Array.isArray(battle.opponents)) {
      for (const op of battle.opponents) {
        let id = typeof op === 'object' && op.agent_id ? op.agent_id : (typeof op === 'string' ? op : null);
        if (id) {
          try {
            const agent = await getAgentById(id);
            opponentAgents.push({ agent, role: op.name || '' });
          } catch {
            opponentAgents.push({ agent: null, id, role: op.name || '' });
          }
        }
      }
    }
  } catch (e) {
    error = e instanceof Error ? e.message : 'Failed to load battle';
  } finally {
    loading = false;
  }
});

function shortId(id: string) {
  return id ? id.slice(0, 8) : '';
}
function formatDate(dt: string) {
  if (!dt) return 'N/A';
  const d = new Date(dt);
  return d.toLocaleString();
}
function duration(start: string, end: string) {
  if (!start || !end) return '';
  const s = new Date(start).getTime();
  const e = new Date(end).getTime();
  if (isNaN(s) || isNaN(e)) return '';
  const sec = Math.round((e - s) / 1000);
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m ${sec%60}s`;
  return `${Math.floor(sec/3600)}h ${Math.floor((sec%3600)/60)}m`;
}
function stateColor(state: string) {
  switch ((state||'').toLowerCase()) {
    case 'pending': return 'text-yellow-600';
    case 'queued': return 'text-yellow-600';
    case 'running': return 'text-blue-600';
    case 'finished': return 'text-green-600';
    case 'error': return 'text-red-600';
    default: return 'text-muted-foreground';
  }
}
</script>

{#if loading}
  <Card.Root>
    <Card.Header>
      <Card.Title>Loading battle...</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="animate-pulse text-muted-foreground">Please wait…</div>
    </Card.Content>
  </Card.Root>
{:else if error}
  <Card.Root>
    <Card.Header>
      <Card.Title>Error loading battle</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="text-destructive">{error}</div>
    </Card.Content>
  </Card.Root>
{:else}
  <Card.Root class="w-full max-w-2xl border shadow-sm bg-background">
    <Card.Header class="pb-2">
      <div class="flex items-center justify-between">
        <Card.Title class="text-lg font-bold">Battle #{shortId(battle.battle_id || battle.id)}</Card.Title>
        <span class="text-xs font-mono text-muted-foreground select-all" title={battle.battle_id || battle.id}>{battle.battle_id || battle.id}</span>
      </div>
      <div class="flex items-center gap-2 mt-1">
        <span class={`text-xs font-semibold uppercase ${stateColor(battle.state)}`}>{battle.state}</span>
        {#if battle.result && battle.state === 'finished'}
          <span class="ml-2 text-xs text-green-700 font-semibold">Winner: {battle.result.winner}</span>
        {/if}
        {#if battle.error && battle.state === 'error'}
          <span class="ml-2 text-xs text-red-700 font-semibold">Error: {battle.error}</span>
        {/if}
      </div>
    </Card.Header>
    <Card.Content class="space-y-2">
      <div class="flex flex-col gap-1">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-sm">Green Agent:</span>
          {#if greenAgent}
            <span class="font-bold text-sm">{greenAgent.register_info?.name || greenAgent.agent_card?.name || 'Unknown'}</span>
            <span class="text-[10px] text-muted-foreground font-mono select-all">{greenAgent.agent_id || greenAgent.id}</span>
            {#if greenAgent.register_info?.role}
              <span class="text-[10px] text-muted-foreground">({greenAgent.register_info.role})</span>
            {/if}
          {:else}
            <span class="text-muted-foreground">Not Found</span>
            <span class="text-[10px] text-muted-foreground font-mono select-all">{battle.green_agent_id || battle.greenAgentId}</span>
          {/if}
        </div>
        <div class="flex flex-col gap-1">
          <span class="font-semibold text-sm">Opponents:</span>
          <ul class="ml-2 list-disc text-xs">
            {#each opponentAgents as op}
              <li class="flex flex-col gap-0.5">
                <span class="font-bold text-xs">{op.agent ? (op.agent.register_info?.name || op.agent.agent_card?.name || 'Unknown') : 'Not Found'}</span>
                <span class="text-[10px] text-muted-foreground font-mono select-all">{op.agent ? (op.agent.agent_id || op.agent.id) : op.id}</span>
                {#if op.role}
                  <span class="text-[10px] text-muted-foreground">({op.role})</span>
                {/if}
              </li>
            {/each}
          </ul>
        </div>
      </div>
      <div class="flex flex-wrap gap-4 mt-2 text-xs">
        <div>Started: <span class="font-mono">{formatDate(battle.created_at || battle.createdAt)}</span></div>
        {#if battle.result && battle.result.finish_time}
          <div>Ended: <span class="font-mono">{formatDate(battle.result.finish_time)}</span></div>
          <div>Duration: <span class="font-mono">{duration(battle.created_at || battle.createdAt, battle.result.finish_time)}</span></div>
        {/if}
      </div>
      {#if battle.result && battle.result.detail}
        <div class="mt-2 text-xs">
          <span class="font-semibold">Result Details:</span>
          <pre class="bg-muted rounded p-2 text-xs overflow-x-auto max-h-32 mt-1">{JSON.stringify(battle.result.detail, null, 2)}</pre>
        </div>
      {/if}
      {#if battle.interact_history && battle.interact_history.length > 0}
        <div class="mt-2 text-xs">
          <span class="font-semibold">Interaction History:</span>
          <pre class="bg-muted rounded p-2 text-xs overflow-x-auto max-h-32 mt-1">{JSON.stringify(battle.interact_history, null, 2)}</pre>
        </div>
      {/if}
    </Card.Content>
    <Card.Footer class="pt-2 flex flex-col items-end">
      <span class="text-[10px] text-muted-foreground select-all">Battle ID: {battle.battle_id || battle.id}</span>
    </Card.Footer>
  </Card.Root>
{/if} 