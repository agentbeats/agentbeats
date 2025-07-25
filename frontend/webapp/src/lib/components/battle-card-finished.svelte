<script lang="ts">
import { onMount } from "svelte";
import * as Card from "./ui/card/index.js";

export let battle: any = null;
export let battleId: string | null = null;

let loading = false;
let error: string | null = null;
let greenAgentName = '';
let opponentNames: string[] = [];
let durationStr = '';

onMount(async () => {
  await loadBattleData();
});

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

async function loadBattleData() {
  // If we don't have battle data, fetch it using battleId
  if (!battle && battleId) {
    loading = true;
    error = null;
    try {
      const res = await fetch(`/api/battles/${battleId}`);
      if (!res.ok) throw new Error('Failed to fetch battle');
      battle = await res.json();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load battle';
      loading = false;
      return;
    } finally {
      loading = false;
    }
  }

  if (battle) {
    // Load green agent name
    if (battle.green_agent_id || battle.greenAgentId) {
      greenAgentName = await fetchAgentName(battle.green_agent_id || battle.greenAgentId);
    }
    // Build a new array for Svelte reactivity
    let names: string[] = [];
    if (battle.opponents && Array.isArray(battle.opponents)) {
      for (const op of battle.opponents) {
        if (op && typeof op === 'object' && op.agent_id) {
          const agentName = await fetchAgentName(op.agent_id);
          names.push(`${agentName} (${op.name || 'Unknown Role'})`);
        } else if (typeof op === 'string') {
          names.push(await fetchAgentName(op));
        } else {
          names.push('Unknown');
        }
      }
    }
    opponentNames = names;

    if (battle.created_at && battle.result?.finish_time) {
      const created = new Date(battle.created_at);
      const finished = new Date(battle.result.finish_time);
      if (!isNaN(created.getTime()) && !isNaN(finished.getTime())) {
        const seconds = Math.round((finished.getTime() - created.getTime()) / 1000);
        durationStr = seconds < 0 ? 'err' : seconds + 's';
      } else {
        durationStr = '';
      }
    }
  }
}

function shortId(id: string) {
  return id ? id.slice(0, 8) : '';
}

function timeAgo(dt: string) {
  if (!dt) return '';
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

function displayTime(battle: any) {
  let dt = '';
  if (battle?.result?.finish_time) {
    dt = battle.result.finish_time;
  } else if (battle?.created_at || battle?.createdAt) {
    dt = battle.created_at || battle.createdAt;
  }
  if (dt && !dt.endsWith('Z')) dt = dt + 'Z';
  if (dt) {
    const d = new Date(dt);
    return d.toLocaleString();
  }
  return '';
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
  if (battle?.state === 'error') return battle?.error ? `Error: ${battle.error}` : 'Error';
  return '';
}

function getOpponentParts(name: string): [string, string] | null {
  const m = name.match(/^(.*?) \((.*?)\)$/);
  return m ? [m[1], m[2]] : null;
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
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4">
    <Card.Header class="pb-2 px-2">
      <div class="flex flex-row items-center justify-between w-full gap-1 mt-3">
        <div class="flex flex-col items-start gap-2">
          <!-- Green Agent -->
          <span class="font-bold text-sm">{greenAgentName || 'Loading...'}</span>
          <span class="text-xs text-muted-foreground font-mono select-all">
            {battle.green_agent_id || battle.greenAgentId || 'Unknown'}
          </span>
          <span class="text-xs text-muted-foreground">Host / Green Agent</span>

          <!-- Opponents List -->
          {#if opponentNames.length > 0}
            <div class="mt-3">
              <span class="text-xs text-muted-foreground">Opponents:</span>
              <ul class="ml-4 mt-2 list-disc space-y-1">
                {#each opponentNames as opponentName}
                  <li class="flex flex-col gap-0.5">
                    {#if getOpponentParts(opponentName)}
                      <span>
                        <span class="text-xs text-muted-foreground">{getOpponentParts(opponentName)?.[0]}</span>
                        <span class="text-xs text-muted-foreground"> ({getOpponentParts(opponentName)?.[1]})</span>
                      </span>
                    {:else}
                      <span class="text-xs text-muted-foreground">{opponentName}</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            </div>
          {:else if battle.opponents && battle.opponents.length > 0}
            <div class="mt-2">
              <span class="text-xs text-muted-foreground">Opponents: Loading...</span>
            </div>
          {:else}
            <div class="mt-2">
              <span class="text-xs text-muted-foreground">No opponents found</span>
            </div>
          {/if}
        </div>

        <div class="flex flex-col items-end gap-1">
          <span class="text-xs font-mono text-muted-foreground select-all" title={battle.battle_id || battle.id}>
            Battle #{shortId(battle.battle_id || battle.id)}
          </span>
          <span class="text-xs text-muted-foreground">{displayTime(battle)}</span>
          <span class="text-xs text-muted-foreground italic">{timeAgo(getEndTime(battle))}</span>
        </div>
      </div>
    </Card.Header>

    <Card.Footer class="pt-4 flex flex-row items-between justify-between w-full mb-0 px-2">
      <div class="flex flex-row items-center gap-3">
        <span class="text-xs font-semibold {stateColor(battle.state)}">{battle.state}</span>
        <span class="text-xs text-muted-foreground">{winnerText(battle)}</span>
        {#if battle.result && battle.result.finish_time}
          <span class="text-xs text-muted-foreground">
            Duration: {durationStr}
          </span>
        {/if}
      </div>
      <span class="text-[10px] text-muted-foreground font-mono select-all">
        Battle ID: {battle.battle_id || battle.id}
      </span>
    </Card.Footer>
  </Card.Root>
{/if} 