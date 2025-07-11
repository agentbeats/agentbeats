<script lang="ts">
import { onMount } from "svelte";
import * as Card from "./ui/card/index.js";
import { getAgentById } from "$lib/api/agents";

export let battle: any = null;
export let battleId: string | null = null;

let loading = false;
let error: string | null = null;

let greenAgent: any = null;
let opponentAgents: any[] = [];

onMount(async () => {
  if (!battle && battleId) {
    loading = true;
    error = null;
    try {
      const res = await fetch(`http://localhost:9000/battles/${battleId}`);
      if (!res.ok) throw new Error('Failed to fetch battle');
      battle = await res.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load battle';
    } finally {
      loading = false;
    }
  }
  // Fetch green agent
  if (battle && (battle.green_agent_id || battle.greenAgentId)) {
    try {
      greenAgent = await getAgentById(battle.green_agent_id || battle.greenAgentId);
    } catch { greenAgent = null; }
  }
  // Fetch all opponent agents
  opponentAgents = [];
  if (battle && Array.isArray(battle.opponents)) {
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
});

function shortId(id: string) {
  return id ? id.slice(0, 8) : '';
}
function timeAgo(dt: string) {
  if (!dt) return '';
  // Ensure the date string is treated as UTC
  let dtFixed = dt;
  if (dt && !dt.endsWith('Z')) {
    dtFixed = dt + 'Z';
  }
  const now = Date.now();
  const then = new Date(dtFixed).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 0) {
    const abs = Math.abs(diff);
    if (abs < 60) return `in ${abs}s`;
    if (abs < 3600) return `in ${Math.floor(abs/60)}m`;
    if (abs < 86400) return `in ${Math.floor(abs/3600)}h`;
    return `in ${Math.floor(abs/86400)}d`;
  }
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}
function getEndTime(battle: any) {
  return battle?.result?.finish_time || battle?.created_at || battle?.createdAt || '';
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
function winnerText(battle: any) {
  if (battle?.result?.winner === 'draw') return 'Draw';
  if (battle?.result?.winner) return `${battle.result.winner} Victory`;
  if (battle?.state === 'error') return 'Error';
  return '';
}
function displayTime(battle: any) {
  // For finished/error battles, show finish_time if available, else started time
  if (battle?.result?.finish_time) {
    const d = new Date(battle.result.finish_time);
    return d.toLocaleString();
  }
  if (battle?.created_at || battle?.createdAt) {
    const d = new Date(battle.created_at || battle.createdAt);
    return d.toLocaleString();
  }
  return '';
}
</script>

{#if loading}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-2">
    <Card.Header>
      <Card.Title>Loading battle...</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="animate-pulse text-muted-foreground">Please wait…</div>
    </Card.Content>
  </Card.Root>
{:else if error}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-2">
    <Card.Header>
      <Card.Title>Error loading battle</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="text-destructive">{error}</div>
    </Card.Content>
  </Card.Root>
{:else if battle}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-1 px-2 py-1">
    <Card.Header class="pb-0 px-2">
      <div class="flex flex-row items-center justify-between w-full gap-1 mt-5">
        <div class="flex flex-col items-start gap-0">
          <span class="font-bold text-sm">{greenAgent ? (greenAgent.register_info?.name || greenAgent.agent_card?.name || 'Unknown') : 'Not Found'}</span>
          <span class="text-[11px] text-muted-foreground font-mono select-all">{greenAgent ? (greenAgent.agent_id || greenAgent.id) : (battle.green_agent_id || battle.greenAgentId)}</span>
          <span class="text-[11px] text-muted-foreground">Host / Green Agent</span>
          <!-- Opponents List -->
          <div class="mt-0">
            <span class="text-[11px] text-muted-foreground">Opponents:</span>
            <ul class="ml-2 mt-0 list-disc text-[11px]">
              {#each opponentAgents as op}
                <li class="flex flex-row gap-1 items-center">
                  <span class="font-bold text-[11px]">{op.agent ? (op.agent.register_info?.name || op.agent.agent_card?.name || 'Unknown') : 'Not Found'}</span>
                  <span class="font-mono text-[11px] text-muted-foreground select-all">{op.agent ? (op.agent.agent_id || op.agent.id) : op.id}</span>
                  {#if op.role}
                    <span class="text-[11px] text-muted-foreground">({op.role})</span>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        </div>
        <div class="flex flex-col items-end gap-0">
          <span class="text-[11px] font-mono text-muted-foreground select-all" title={battle.battle_id || battle.id}>Battle #{shortId(battle.battle_id || battle.id)}</span>
          <span class="text-[11px] text-muted-foreground">{displayTime(battle)}</span>
          <span class="text-[11px] text-muted-foreground italic">{timeAgo(getEndTime(battle))}</span>
        </div>
      </div>
    </Card.Header>
    <Card.Footer class="pt-0 flex flex-row items-between justify-between w-full mb-0 px-2">
      <div class="flex flex-row items-center gap-2">
        <span class="text-[11px] font-semibold {stateColor(battle.state)}">{battle.state}</span>
        <span class="text-[11px] text-muted-foreground">{winnerText(battle)}</span>
        {#if battle.result && battle.result.finish_time}
          <span class="text-[11px] text-muted-foreground">Duration: {duration(battle.created_at || battle.createdAt, battle.result.finish_time)}</span>
        {/if}
      </div>
      <span class="text-[10px] text-muted-foreground font-mono select-all">Battle ID: {battle.battle_id || battle.id}</span>
    </Card.Footer>
  </Card.Root>
{/if} 