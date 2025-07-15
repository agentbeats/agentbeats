<script lang="ts">
import { onMount, onDestroy } from "svelte";
import * as Card from "./ui/card/index.js";
import { getAgentById } from "$lib/api/agents";

export let battleId: string;
let battle: any = null;
let loading = true;
let error: string | null = null;
let greenAgent: any = null;
let opponentAgents: { name: string; role: string }[] = [];
let duration = '';
let timer: any = null;

function shortId(id: string) {
  return id ? id.slice(0, 8) : '';
}
function formatDate(dt: string) {
  if (!dt) return 'N/A';
  let dtFixed = dt;
  if (dt && !dt.endsWith('Z')) dtFixed = dt + 'Z';
  const d = new Date(dtFixed);
  return d.toLocaleString();
}
function stateColor(state: string) {
  switch ((state||'').toLowerCase()) {
    case 'pending': return 'text-yellow-600';
    case 'queued': return 'text-yellow-600';
    case 'running': return 'text-blue-600';
    default: return 'text-muted-foreground';
  }
}
function calcDuration(start: string) {
  if (!start) return '';
  const s = new Date(start).getTime();
  const now = Date.now();
  if (isNaN(s)) return '';
  let sec = Math.round((now - s) / 1000);
  if (sec < 0) sec = 0;
  if (sec < 60) return `${sec}s`;
  if (sec < 3600) return `${Math.floor(sec/60)}m ${sec%60}s`;
  return `${Math.floor(sec/3600)}h ${Math.floor((sec%3600)/60)}m`;
}

onMount(async () => {
  loading = true;
  error = null;
  try {
    const res = await fetch(`/api/battles/${battleId}`);
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
        let role = typeof op === 'object' && op.name ? op.name : '';
        if (id) {
          try {
            const agent = await getAgentById(id);
            opponentAgents.push({ name: agent.register_info?.name || agent.agent_card?.name || 'Unknown', role });
          } catch {
            opponentAgents.push({ name: 'Unknown', role });
          }
        }
      }
    }
    // Start duration timer
    updateDuration();
    timer = setInterval(updateDuration, 1000);
  } catch (e) {
    error = e instanceof Error ? e.message : 'Failed to load battle';
  } finally {
    loading = false;
  }
});

onDestroy(() => {
  if (timer) clearInterval(timer);
});

function updateDuration() {
  if (battle && (battle.created_at || battle.createdAt)) {
    duration = calcDuration(battle.created_at || battle.createdAt);
  } else {
    duration = '';
  }
}
</script>

{#if loading}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4">
    <Card.Header>
      <Card.Title>Loading battle...</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="animate-pulse text-muted-foreground">Please wait…</div>
    </Card.Content>
  </Card.Root>
{:else if error}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4">
    <Card.Header>
      <Card.Title>Error loading battle</Card.Title>
    </Card.Header>
    <Card.Content>
      <div class="text-destructive">{error}</div>
    </Card.Content>
  </Card.Root>
{:else}
  <Card.Root class="w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4">
    <Card.Header class="pb-2 px-2">
      <div class="flex flex-row items-center justify-between w-full gap-1 mt-3">
        <div class="flex flex-col items-start gap-2">
          <!-- Green Agent -->
          <span class="font-bold text-sm">{greenAgent ? (greenAgent.register_info?.name || greenAgent.agent_card?.name || 'Unknown') : 'Not Found'}</span>
          <span class="text-xs text-muted-foreground font-mono select-all">{greenAgent ? (greenAgent.agent_id || greenAgent.id) : (battle.green_agent_id || battle.greenAgentId)}</span>
          <span class="text-xs text-muted-foreground">Host / Green Agent</span>

          <!-- Opponents List -->
          {#if opponentAgents.length > 0}
            <div class="mt-3">
              <span class="text-xs text-muted-foreground">Opponents:</span>
              <ul class="ml-4 mt-2 list-disc space-y-1">
                {#each opponentAgents as op}
                  <li class="flex flex-col gap-0.5">
                    <span>
                      <span class="text-xs text-muted-foreground">{op.name}</span>
                      {#if op.role}
                        <span class="text-xs text-muted-foreground"> ({op.role})</span>
                      {/if}
                    </span>
                  </li>
                {/each}
              </ul>
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
          <span class="text-xs text-muted-foreground">{formatDate(battle.created_at || battle.createdAt)}</span>
          <!-- No 'Ongoing' or 'XXs ago' label here -->
        </div>
      </div>
    </Card.Header>

    <Card.Footer class="pt-4 flex flex-row items-between justify-between w-full mb-0 px-2">
      <div class="flex flex-row items-center gap-3">
        <span class="text-xs font-semibold {stateColor(battle.state)}">{battle.state}</span>
        <!-- Removed duration display -->
      </div>
      <span class="text-[10px] text-muted-foreground font-mono select-all">
        Battle ID: {battle.battle_id || battle.id}
      </span>
    </Card.Footer>
  </Card.Root>
{/if} 