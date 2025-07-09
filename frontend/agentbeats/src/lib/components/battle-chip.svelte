<script lang="ts">
import { onMount } from "svelte";
import AgentChipById from "./agent-chip-by-id.svelte";
import CheckIcon from "@lucide/svelte/icons/check";
import XIcon from "@lucide/svelte/icons/x";
import MinusIcon from "@lucide/svelte/icons/minus";
import HelpCircleIcon from "@lucide/svelte/icons/help-circle";
import * as Tooltip from "./ui/tooltip";

export let battle: any = null;
export let battleId: string | null = null;

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
    return { icon: MinusIcon, color: "text-yellow-500", label: "Draw" };
  }
  // You can add more logic for win/loss if you have agent IDs
  return { icon: CheckIcon, color: "text-green-500", label: "Finished" };
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
  <Tooltip.Provider>
    <Tooltip.Root>
      <Tooltip.Trigger>
        <div class="flex flex-col gap-2 rounded-xl border bg-card px-6 py-4 shadow-md text-xs min-h-24 min-w-[22rem] max-w-full hover:bg-accent cursor-pointer transition select-text w-full" on:click={openModal} tabindex="0" role="button">
          <div class="w-full mb-1">
            <div class="text-base font-semibold text-primary break-words whitespace-normal">{battle.topic ?? 'Battle Topic Placeholder'}</div>
            <div class="text-xs text-muted-foreground font-mono break-words whitespace-normal">{battle.id}</div>
          </div>
          <div class="flex flex-row items-center justify-between w-full h-full">
            <div class="flex flex-col items-start gap-2">
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

  {#if showModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click={closeModal}>
      <div class="bg-background rounded-xl shadow-2xl p-6 max-w-lg w-full relative" on:click|stopPropagation>
        <button class="absolute top-3 right-3 text-muted-foreground hover:text-foreground" on:click={closeModal} aria-label="Close">
          <XIcon class="size-5" />
        </button>
        <div class="mb-4">
          <div class="text-lg font-bold mb-1 break-words whitespace-normal">{battle.topic ?? 'Battle Topic Placeholder'}</div>
          <div class="text-xs text-muted-foreground mb-2">Battle ID: <span class="font-mono">{battle.id}</span></div>
        </div>
        <div class="mb-4 flex flex-col gap-2">
          <div class="flex flex-row items-start gap-2">
            <AgentChipById agentId={redId} />
            <AgentChipById agentId={blueId} />
          </div>
          <div class="flex flex-row items-start gap-2">
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