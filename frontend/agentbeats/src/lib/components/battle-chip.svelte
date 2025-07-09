<script lang="ts">
import { onMount } from "svelte";
import AgentChipById from "./agent-chip-by-id.svelte";
import TrophyIcon from "@lucide/svelte/icons/trophy";
import XIcon from "@lucide/svelte/icons/x";
import HandshakeIcon from "@lucide/svelte/icons/handshake";
import HelpCircleIcon from "@lucide/svelte/icons/help-circle";
import * as Tooltip from "./ui/tooltip";

export let battle: any = null;
export let battleId: string | null = null;
export let compact: boolean = false;

let loading = false;
let error: string | null = null;

let showModal = false;
function openModal() { showModal = true; }
function closeModal() { showModal = false; }

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
});

function getResultIcon(result: any) {
  if (!result) return { icon: HelpCircleIcon, color: "text-muted-foreground", label: "Unknown" };
  const winner = result.winner;
  if (winner === "draw" || (result.score && result.score.reason === "mock")) {
    return { icon: HandshakeIcon, color: "text-yellow-500", label: "Draw" };
  }
  if (winner === "error" || result.error) {
    return { icon: XIcon, color: "text-red-500", label: "Error" };
  }
  // You can add more logic for win/loss if you have agent IDs
  return { icon: TrophyIcon, color: "text-green-500", label: "Victory" };
}

$: resultInfo = getResultIcon(battle?.result);
$: greenId = battle?.greenAgentId;
$: redId = battle?.opponents?.[0];
$: blueId = battle?.opponents?.[1];
</script>

{#if loading}
  <span class="inline-block px-3 py-1 text-xs text-muted-foreground bg-muted rounded-full animate-pulse">Loading...</span>
{:else if error}
  <span class="inline-block px-3 py-1 text-xs text-red-500 bg-muted rounded-full">{error}</span>
{:else if battle}
  <div class="battle-chip-hover {compact ? 'compact-battle-chip-hover' : 'battle-chip-main-hover'}">
    <Tooltip.Provider>
      <Tooltip.Root>
        <Tooltip.Trigger>
          <div class="flex flex-col gap-2 rounded-xl border bg-card shadow-md text-xs cursor-pointer transition select-text w-full battle-chip-bg" on:click={openModal} tabindex="0" role="button" style="background-image: url('/src/lib/assets/battle-card-background.png');">
            <div class="w-full mb-1">
              <div class="text-base font-semibold text-primary break-words whitespace-normal {compact ? 'text-sm' : ''}">{battle.topic ?? 'Battle Topic Placeholder'}</div>
              <div class="text-xs text-muted-foreground font-mono break-words whitespace-normal">{battle.id}</div>
            </div>
            <div class="flex flex-row items-center justify-between w-full h-full">
              <div class="flex flex-col items-start gap-2 {compact ? 'gap-1' : ''}">
                <AgentChipById agentId={redId} />
                <AgentChipById agentId={blueId} />
                <AgentChipById agentId={greenId} />
              </div>
              <span class="flex items-center justify-center ml-6 h-full">
                <svelte:component this={resultInfo.icon} class={`size-10 ${resultInfo.color}`} />
              </span>
            </div>
          </div>
        </Tooltip.Trigger>
        <Tooltip.Content side="top" class="z-50 select-text px-2 py-0.5 text-[10px] min-h-0 min-w-0">
          <span class="font-mono">{battle.id}</span>
        </Tooltip.Content>
      </Tooltip.Root>
    </Tooltip.Provider>
  </div>

  {#if showModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click={closeModal}>
      <div class="bg-background rounded-xl shadow-2xl p-4 max-w-md w-full relative {compact ? 'compact-battle-chip' : ''}" on:click|stopPropagation>
        <button class="absolute top-3 right-3 text-muted-foreground hover:text-foreground" on:click={closeModal} aria-label="Close">
          <XIcon class="size-5" />
        </button>
        <div class="mb-4">
          <div class="text-lg font-bold mb-1 break-words whitespace-normal {compact ? 'text-base' : ''}">{battle.topic ?? 'Battle Topic Placeholder'}</div>
          <div class="text-xs text-muted-foreground mb-2">Battle ID: <span class="font-mono">{battle.id}</span></div>
        </div>
        <div class="mb-4 flex flex-col gap-2 {compact ? 'gap-1' : ''}">
          <div class="flex flex-row items-start gap-2 {compact ? 'gap-1' : ''}">
            <AgentChipById agentId={redId} />
            <AgentChipById agentId={blueId} />
          </div>
          <div class="flex flex-row items-start gap-2 {compact ? 'gap-1' : ''}">
            <AgentChipById agentId={greenId} />
            <span class="ml-2 flex items-center gap-1">
              <svelte:component this={resultInfo.icon} class={`size-5 ${resultInfo.color}`} />
            </span>
          </div>
        </div>
        <pre class="bg-muted rounded p-2 text-xs overflow-x-auto max-h-60">{JSON.stringify(battle, null, 2)}</pre>
      </div>
    </div>
  {/if}
{/if} 

<style>
  .battle-chip-hover {
    position: relative;
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    width: 100%;
    max-width: 100%;
  }
  .battle-chip-main-hover {
    min-width: 20rem;
    max-width: 100%;
  }
  .compact-battle-chip-hover {
    min-width: 22rem;
    max-width: 100%;
  }
  .battle-chip-hover::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(45deg, #f44336, #2196f3, #4caf50);
    border-radius: inherit;
    opacity: 0;
    z-index: 1;
    transition: opacity 0.3s cubic-bezier(0.4,0,0.2,1);
    pointer-events: none;
  }
  .battle-chip-hover:hover::before {
    opacity: 0.3;
  }
  .battle-chip-hover:hover {
    transform: translateY(-5px);
    z-index: 2;
  }
  .battle-chip-bg {
    background-size: cover !important;
    background-position: center 40px !important;
    position: relative;
    overflow: hidden;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    width: 100%;
    max-width: 100%;
  }
  .battle-chip-main {
    padding: 2rem 1.25rem;
    min-height: 8.5rem;
  }
  .compact-battle-chip {
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem !important;
    min-height: 0;
    gap: 0.15rem !important;
  }
</style> 