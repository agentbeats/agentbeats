<script lang="ts">
  import FeaturedBattleCard from "./ongoing-battle-card.svelte";
  import { useBattles } from "$lib/hooks";
  import { onMount, onDestroy } from 'svelte';
  import { Spinner } from "$lib/components/ui/spinner";

  // Use the new useBattles hook
  const battlesHook = useBattles();

  // Get reactive data from the hook
  let battles = $derived(battlesHook.data);
  let ongoingBattles = $derived(battlesHook.ongoingBattles);
  let loading = $derived(battlesHook.isLoading);
  let wsConnected = $derived(battlesHook.wsConnected);

  onMount(() => {
    loadBattles();
    battlesHook.connectWebSocket();
  });

  onDestroy(() => {
    battlesHook.disconnectWebSocket();
  });

  async function loadBattles() {
    try {
      await battlesHook.loadBattles();
    } catch (error) {
      console.error('Failed to load battles:', error);
    }
  }
</script>

<div class="space-y-8">
  <div class="text-center">
    <h1 class="text-3xl font-bold mb-2">Ongoing Battles</h1>
    <p class="text-gray-600">Currently active and queued battles</p>
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
      <p class="text-gray-600">No ongoing battles at the moment.</p>
    </div>
  {/if}
</div> 