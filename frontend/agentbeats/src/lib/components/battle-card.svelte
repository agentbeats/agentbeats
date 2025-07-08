<script lang="ts">
import { onMount } from "svelte";
import * as Card from "./ui/card/index.js";
import AgentChipById from "./agent-chip-by-id.svelte";

export let battleId: string;
let battle: any = null;
let loading = true;
let error: string | null = null;

onMount(async () => {
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
});
</script>

{#if loading}
  <Card.Root class="@container/card">
    <Card.Header>
      <Card.Description>Loading battle...</Card.Description>
    </Card.Header>
  </Card.Root>
{:else if error}
  <Card.Root class="@container/card">
    <Card.Header>
      <Card.Description>Error: {error}</Card.Description>
    </Card.Header>
  </Card.Root>
{:else}
  <Card.Root class="relative flex flex-col items-center justify-between min-h-[220px] p-4">
    <!-- Battle topic/title at top center -->
    <div class="absolute top-2 left-1/2 -translate-x-1/2 text-center text-base font-semibold text-primary">
      Battle Topic (TBD)
    </div>
    <div class="flex flex-1 w-full items-center justify-between">
      <!-- Opponent 1 (left, center vertically) -->
      <div class="flex-1 flex justify-start items-center h-full">
        <div class="flex flex-col items-center justify-center h-full">
          <AgentChipById agentId={battle.opponents?.[0]} />
        </div>
      </div>
      <!-- Green Agent (center, center vertically) -->
      <div class="flex-1 flex flex-col items-center justify-center h-full">
        <AgentChipById agentId={battle.greenAgentId} />
      </div>
      <!-- Opponent 2 (right, center vertically) -->
      <div class="flex-1 flex justify-end items-center h-full">
        <div class="flex flex-col items-center justify-center h-full">
          <AgentChipById agentId={battle.opponents?.[1]} />
        </div>
      </div>
    </div>
    <!-- Battle ID at the very bottom in small font -->
    <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground select-text">
      id: {battle.id}
    </div>
  </Card.Root>
{/if} 