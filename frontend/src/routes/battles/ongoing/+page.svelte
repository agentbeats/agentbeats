<script lang="ts">
import BattleCard from "$lib/components/battle-card-ongoing.svelte";
import { onMount } from "svelte";
import { goto } from "$app/navigation";
import { fade } from 'svelte/transition';

let battles: any[] = [];
let ongoingBattles: any[] = [];
let ws = null;

function recalcBattles() {
  const ongoingStatuses = ["pending", "queued", "running"];
  ongoingBattles = battles.filter(
    b => ongoingStatuses.includes((b.state || '').toLowerCase())
  );
}

onMount(() => {
  fetch("http://localhost:9000/battles")
    .then(res => res.json())
    .then(data => {
      battles = data;
      recalcBattles();
    });
  ws = new WebSocket("ws://localhost:9000/ws/battles");
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg && msg.type === "battles_update" && Array.isArray(msg.battles)) {
        battles = msg.battles;
        recalcBattles();
      }
      if (msg && msg.type === "battle_update" && msg.battle) {
        const idx = battles.findIndex(b => b.id === msg.battle.id);
        if (idx !== -1) {
          battles[idx] = msg.battle;
        } else {
          battles = [msg.battle, ...battles];
        }
        recalcBattles();
      }
    } catch (e) {
      // ignore
    }
  };
});
</script>

<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh]">
  <div class="w-full max-w-5xl flex flex-col items-center">
    <div class="grid grid-cols-1 gap-4 px-4 lg:px-6 w-full">
      {#each ongoingBattles as battle (battle.id)}
        <div role="button" tabindex="0" class="cursor-pointer" on:click={() => goto(`/battle/${battle.id}`)} transition:fade={{ duration: 220 }}>
          <BattleCard battleId={battle.id} />
        </div>
      {/each}
    </div>
    {#if ongoingBattles.length === 0}
      <div class="text-center text-muted-foreground mt-10">No ongoing battles found.</div>
    {/if}
  </div>
</div> 