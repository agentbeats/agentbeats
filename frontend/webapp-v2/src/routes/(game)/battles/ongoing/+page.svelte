<script lang="ts">
  import FeaturedBattleCard from "./ongoing-battle-card.svelte";
  import { getAllBattles } from "$lib/api/battles";
  import { onMount, onDestroy } from 'svelte';
  import { Spinner } from "$lib/components/ui/spinner";

  let battles = $state<any[]>([]);
  let ongoingBattles = $state<any[]>([]);
  let loading = $state(true);
  let ws: WebSocket | null = null;

  function recalcBattles() {
    const ongoingStatuses = ["pending", "queued", "running"];
    ongoingBattles = battles.filter(b => ongoingStatuses.includes((b.state || '').toLowerCase()));
    
    // Sort by created_at descending (most recent first)
    ongoingBattles.sort((a, b) => {
      const aTime = new Date(a.created_at || 0).getTime();
      const bTime = new Date(b.created_at || 0).getTime();
      return bTime - aTime;
    });
  }

  async function loadBattles() {
    try {
      loading = true;
      battles = await getAllBattles();
      recalcBattles();
    } catch (error) {
      console.error('Failed to load battles:', error);
      battles = [];
      ongoingBattles = [];
    } finally {
      loading = false;
    }
  }

  function setupWebSocket() {
    ws = new WebSocket(
      (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
      window.location.host +
      '/ws/battles'
    );

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg && msg.type === 'battles_update' && Array.isArray(msg.battles)) {
          battles = msg.battles;
          recalcBattles();
        }
        if (msg && msg.type === 'battle_update' && msg.battle) {
          const idx = battles.findIndex(b => b.battle_id === msg.battle.battle_id);
          if (idx !== -1) {
            battles[idx] = msg.battle;
          } else {
            battles = [msg.battle, ...battles];
          }
          recalcBattles();
        }
      } catch (e) {
        console.error('[WS] JSON parse error', e);
      }
    };
  }

  onMount(() => {
    loadBattles();
    setupWebSocket();
  });

  onDestroy(() => {
    if (ws) ws.close();
  });
</script>

<div class="space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold mb-2">Ongoing Battles</h1>
    <p class="text-muted-foreground">Currently active and queued battles</p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <Spinner size="lg" />
      <span class="ml-3 text-lg">Loading battles...</span>
    </div>
  {:else if ongoingBattles.length > 0}
    <div class="space-y-12">
      {#each ongoingBattles as battle}
        <FeaturedBattleCard {battle} />
      {/each}
    </div>
  {:else}
    <div class="text-center py-12">
      <p class="text-muted-foreground">No ongoing battles at the moment.</p>
    </div>
  {/if}
</div> 