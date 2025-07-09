<script lang="ts">
import { onMount, onDestroy } from 'svelte';
import { page } from '$app/stores';
import * as Drawer from "$lib/components/ui/drawer/index.js";
import { Button, buttonVariants } from "$lib/components/ui/button/index.js";
import { Avatar, AvatarImage, AvatarFallback } from "$lib/components/ui/avatar/index.js";
import AgentChipById from "$lib/components/agent-chip-by-id.svelte";
import SwordsIcon from '@lucide/svelte/icons/swords';
import TrophyIcon from '@lucide/svelte/icons/trophy';
import CrownIcon from '@lucide/svelte/icons/crown';
import XIcon from '@lucide/svelte/icons/x';
import HandshakeIcon from '@lucide/svelte/icons/handshake';

let logs: any[] = [];
let ws: WebSocket | null = null;
let battle: any = null;
let loading = true;
let error = '';

// Use Svelte's reactivity for the battleId
$: battleId = $page.params.battle_id;

const ongoingStates = ['pending', 'queued', 'running'];

async function fetchBattle() {
  loading = true;
  error = '';
  try {
    const res = await fetch(`http://localhost:9000/battles/${battleId}`);
    if (!res.ok) throw new Error('Failed to fetch battle');
    battle = await res.json();
    logs = battle.logs || [];
  } catch (e) {
    error = e instanceof Error ? e.message : 'Unknown error';
  } finally {
    loading = false;
  }
}

onMount(async () => {
  if (!battleId) return;
  await fetchBattle();
  if (battle && ongoingStates.includes((battle.state || '').toLowerCase())) {
    ws = new WebSocket(`ws://localhost:9000/ws/battles/${battleId}/logs`);
    ws.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        logs = [...logs, log];
      } catch (e) {
        logs = [...logs, event.data];
      }
    };
    ws.onerror = (e) => {
      logs = [...logs, { message: 'WebSocket error', detail: e }];
    };
    ws.onclose = () => {
      logs = [...logs, { message: 'WebSocket closed' }];
    };
  }
});

onDestroy(() => {
  if (ws) ws.close();
});

$: mostRecentLog = logs && logs.length > 0 ? logs[logs.length - 1] : null;
$: redId = battle?.opponents?.[0];
$: blueId = battle?.opponents?.[1];
$: winnerIdx = (battle && (battle.state ?? '').toLowerCase() === 'finished')
  ? (battle.result?.winner === redId ? 0 : battle.result?.winner === blueId ? 1 : null)
  : null;
$: isDraw = (battle && (battle.state ?? '').toLowerCase() === 'finished' && battle.result?.winner === 'draw');
$: winnerLabel = (battle && (battle.state ?? '').toLowerCase() === 'finished' && !isDraw)
  ? (battle.result?.winner === redId ? 'Red wins!' : battle.result?.winner === blueId ? 'Blue wins!' : null)
  : null;
</script>

<main class="p-4 flex flex-col min-h-[90vh]">
  {#if !loading && !error && battle}
    <div class="flex flex-col items-center justify-center mt-6 mb-8">
      <h1 class="text-3xl font-bold text-center mb-2">{battle.topic ?? 'Battle Topic'}</h1>
      <div class="text-sm text-muted-foreground text-center font-mono">{battleId}</div>
    </div>
    {#if (battle.state ?? '').toLowerCase() === 'finished' && isDraw}
      <div class="flex flex-row items-end justify-center gap-40 mb-16">
        <div class="flex flex-col items-center transition-all duration-300 translate-y-[32px] opacity-60 grayscale">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[0]?.avatarUrl} alt={battle?.agents?.[0]?.name} />
            <AvatarFallback>{battle?.agents?.[0]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={redId} />
        </div>
        <div class="flex flex-col items-center">
          <HandshakeIcon class="w-24 h-24 text-yellow-400 mb-4" />
          <div class="text-xl font-semibold mt-2">Current state: <span class="font-mono">Draw</span></div>
        </div>
        <div class="flex flex-col items-center transition-all duration-300 translate-y-[32px] opacity-60 grayscale">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[1]?.avatarUrl} alt={battle?.agents?.[1]?.name} />
            <AvatarFallback>{battle?.agents?.[1]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={blueId} />
        </div>
      </div>
    {:else if (battle.state ?? '').toLowerCase() === 'error'}
      <div class="flex flex-row items-end justify-center gap-40 mb-16">
        <div class="flex flex-col items-center transition-all duration-300 translate-y-[32px] opacity-60 grayscale">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[0]?.avatarUrl} alt={battle?.agents?.[0]?.name} />
            <AvatarFallback>{battle?.agents?.[0]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={redId} />
        </div>
        <div class="flex flex-col items-center">
          <XIcon class="w-24 h-24 text-red-500 mb-4" />
          <div class="text-xl font-semibold mt-2">Current state: <span class="font-mono">Error</span></div>
        </div>
        <div class="flex flex-col items-center transition-all duration-300 translate-y-[32px] opacity-60 grayscale">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[1]?.avatarUrl} alt={battle?.agents?.[1]?.name} />
            <AvatarFallback>{battle?.agents?.[1]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={blueId} />
        </div>
      </div>
    {:else if (battle.state ?? '').toLowerCase() === 'finished'}
      <div class="flex flex-row items-end justify-center gap-40 mb-16">
        <div class="flex flex-col items-center transition-all duration-300 {winnerIdx === 0 ? 'translate-y-[-32px]' : 'translate-y-[32px] opacity-60 grayscale'}">
          {#if winnerIdx === 0}
            <CrownIcon class="w-14 h-14 text-yellow-400 mb-2" />
          {/if}
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[0]?.avatarUrl} alt={battle?.agents?.[0]?.name} />
            <AvatarFallback>{battle?.agents?.[0]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={redId} />
        </div>
        <div class="flex flex-col items-center">
          <TrophyIcon class="w-24 h-24 text-yellow-400 mb-4" />
          <div class="text-xl font-semibold mt-2">Current state: <span class="font-mono">{winnerLabel ?? (battle?.state ?? 'unknown')}</span></div>
        </div>
        <div class="flex flex-col items-center transition-all duration-300 {winnerIdx === 1 ? 'translate-y-[-32px]' : 'translate-y-[32px] opacity-60 grayscale'}">
          {#if winnerIdx === 1}
            <CrownIcon class="w-14 h-14 text-yellow-400 mb-2" />
          {/if}
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[1]?.avatarUrl} alt={battle?.agents?.[1]?.name} />
            <AvatarFallback>{battle?.agents?.[1]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={blueId} />
        </div>
      </div>
    {:else}
      <div class="flex flex-row items-end justify-center gap-40 mb-16">
        <!-- Left Agent -->
        <div class="flex flex-col items-center">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[0]?.avatarUrl} alt={battle?.agents?.[0]?.name} />
            <AvatarFallback>{battle?.agents?.[0]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={redId} />
        </div>
        <!-- Center Icon -->
        <div class="flex flex-col items-center">
          <SwordsIcon class="w-20 h-20 text-primary mb-4" />
          <div class="text-xl font-semibold mt-2">Current state: <span class="font-mono">{battle?.state ?? 'unknown'}</span></div>
        </div>
        <!-- Right Agent -->
        <div class="flex flex-col items-center">
          <Avatar class="w-64 h-64 mb-4">
            <AvatarImage src={battle?.agents?.[1]?.avatarUrl} alt={battle?.agents?.[1]?.name} />
            <AvatarFallback>{battle?.agents?.[1]?.name?.[0] ?? '?'}</AvatarFallback>
          </Avatar>
          <AgentChipById agentId={blueId} />
        </div>
      </div>
    {/if}
  {/if}
  {#if loading}
    <div>Loading...</div>
  {:else if error}
    <div class="text-red-500">{error}</div>
  {:else}
     <Drawer.Root>
       <Drawer.Content>
         <div class="w-full h-full flex flex-col">
           <div class="flex-1 p-4 overflow-y-auto">
             <pre class="bg-muted rounded p-2 text-sm h-full min-h-[60vh] max-h-[80vh] w-full whitespace-pre-wrap overflow-y-auto">
{#each logs as log}
  {typeof log === 'string' ? log : log.timestamp ? `[${log.timestamp}] ${log.message}` : JSON.stringify(log)}
{/each}
             </pre>
           </div>
           <Drawer.Footer>
             <Drawer.Close class={buttonVariants({ variant: "outline" })}>
               Close
             </Drawer.Close>
           </Drawer.Footer>
         </div>
       </Drawer.Content>
      <div class="fixed left-1/2 bottom-10 -translate-x-1/2 flex flex-col items-center z-40">
        <div class="bg-muted rounded-lg shadow px-4 py-2 text-sm max-w-lg min-w-[16rem] text-center border border-border mb-2">
          {#if mostRecentLog}
            {typeof mostRecentLog === 'string' ? mostRecentLog : mostRecentLog.timestamp ? `[${mostRecentLog.timestamp}] ${mostRecentLog.message}` : JSON.stringify(mostRecentLog)}
          {:else}
            <span class="text-muted-foreground">No logs yet.</span>
          {/if}
        </div>
        <Drawer.Trigger class={buttonVariants({ variant: "outline" })}>
          View Logs
        </Drawer.Trigger>
      </div>
    </Drawer.Root>
  {/if}
</main> 