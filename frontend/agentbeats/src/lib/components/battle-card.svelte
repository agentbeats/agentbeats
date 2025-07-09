<script lang="ts">
import { onMount } from "svelte";
import * as Card from "./ui/card/index.js";
import AgentChipById from "./agent-chip-by-id.svelte";
import battleCardBg from '$lib/assets/battle-card-background.png';

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
  <div class="battle-card-hover">
    <Card.Root class="relative flex flex-col items-center justify-between min-h-[400px] p-8 w-full min-w-[36rem] max-w-6xl battle-card-bg" style={`background-image: url('${battleCardBg}');`}>
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
      <!-- Battle ID and timestamp at the very bottom in small font -->
      <div class="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-muted-foreground select-text">
        id: {battle.id} |
        timestamp: {battle.timestamp ?? battle.createdAt ?? 'N/A'}
      </div>
    </Card.Root>
  </div>
{/if} 

<style>
  .battle-card-hover {
    position: relative;
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  }
  .battle-card-hover::before {
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
  .battle-card-hover:hover::before {
    opacity: 0.3;
  }
  .battle-card-hover:hover {
    transform: translateY(-5px);
    z-index: 2;
  }
  .battle-card-bg {
    background-size: cover !important;
    background-position: center 40px !important;
    position: relative;
    overflow: hidden;
    border-radius: 12px !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  }
  .battle-card-bg > * {
    position: relative;
    z-index: 2;
  }
</style> 