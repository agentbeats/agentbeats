<script lang="ts">
  import { onMount } from 'svelte';
  import { getAllBattles } from '$lib/api/battles';
  import { goto } from '$app/navigation';
  import { Spinner } from '$lib/components/ui/spinner';

  let battles: any[] = [];
  let loading = true;
  let error = '';

  async function loadBattles() {
    loading = true;
    error = '';
    try {
      battles = await getAllBattles();
    } catch (e) {
      console.error('Failed to load battles', e);
      error = 'Failed to load battles';
      battles = [];
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadBattles();
  });
</script>

<div class="space-y-6">
  <div class="text-center">
    <h1 class="text-2xl font-bold">All Battles</h1>
    <p class="text-muted-foreground">Browse featured, ongoing and past battles</p>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <Spinner size="lg" />
      <span class="ml-3 text-lg">Loading battles...</span>
    </div>
  {:else if error}
    <div class="text-center py-12 text-red-500">{error}</div>
  {:else if battles.length === 0}
    <div class="text-center py-12 text-muted-foreground">No battles found.</div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each battles as battle}
        <div class="p-4 border rounded-lg hover:shadow cursor-pointer" on:click={() => goto(`/battles/${battle.battle_id}`)}>
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium">{battle.green_agent_id ? battle.green_agent_id.slice(0,8) : battle.battle_id.slice(0,8)}</div>
              <div class="text-xs text-muted-foreground">{battle.state || 'Unknown'}</div>
            </div>
            <div class="text-xs text-right">
              <div>{new Date(battle.created_at || Date.now()).toLocaleString()}</div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
