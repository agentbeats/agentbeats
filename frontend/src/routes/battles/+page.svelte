<script lang="ts">
// Minimalist, shadcn-svelte-based battles page
import { onMount, onDestroy } from 'svelte';
import { goto } from '$app/navigation';
import BattleCard from '$lib/components/battle-card-ongoing.svelte';
import BattleChip from '$lib/components/battle-card-finished.svelte';

export let data: { battles: any[] };
let battles = data.battles;
let ws: WebSocket | null = null;

function recalcBattles() {
	const ongoingStatuses = ["pending", "queued", "running"];
	const pastStatuses = ["finished", "error"];
	ongoingBattles = battles.filter(b => ongoingStatuses.includes((b.state || '').toLowerCase()));
	pastBattles = battles.filter(b => pastStatuses.includes((b.state || '').toLowerCase()));
	const finishedIds = new Set(pastBattles.map(b => b.battle_id));
	ongoingBattles = ongoingBattles.filter(b => !finishedIds.has(b.battle_id));
	// Sort pastBattles by finish_time or created_at descending (most recent first)
	pastBattles.sort((a, b) => {
		const aTime = new Date(a.result?.finish_time || a.created_at || 0).getTime();
		const bTime = new Date(b.result?.finish_time || b.created_at || 0).getTime();
		return bTime - aTime;
	});
}

onMount(() => {
	recalcBattles();
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
});

onDestroy(() => { if (ws) ws.close(); });

let ongoingBattles: any[] = [];
let pastBattles: any[] = [];
</script>

<div class="w-full flex flex-col items-center justify-center mt-10 mb-8">
	<h1 class="text-2xl font-bold text-center mb-8">Battles</h1>
	<button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition" on:click={() => goto('/battles/stage-battle')}>
		Stage a Battle
	</button>
</div>

<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh] w-full">
	<div class="flex flex-1 flex-col gap-2 items-center justify-center w-full">
		<div class="flex flex-col gap-10 py-4 md:gap-12 md:py-6 w-full items-center justify-center">
			{#if ongoingBattles.length > 0}
				<div class="w-full max-w-4xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-10 mt-10">Ongoing Battles</h2>
					<div class="flex flex-col gap-4 w-full">
						{#each ongoingBattles as battle (battle.battle_id)}
							<div role="button" tabindex="0" class="cursor-pointer w-full" on:click={() => goto(`/battles/${battle.battle_id}`)}>
								<BattleCard battleId={battle.battle_id} />
							</div>
						{/each}
					</div>
				</div>
			{/if}
			{#if pastBattles.length > 0}
				<div class="w-full max-w-4xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-8 mt-8">Past Battles</h2>
					<div class="flex flex-col gap-4 w-full">
						{#each pastBattles as battle (battle.battle_id)}
							<div role="button" tabindex="0" class="cursor-pointer w-full" on:click={() => goto(`/battles/${battle.battle_id}`)}>
								<BattleChip battleId={battle.battle_id} />
							</div>
						{/each}
					</div>
				</div>
			{/if}
			{#if ongoingBattles.length === 0 && pastBattles.length === 0}
				<div class="text-center text-muted-foreground">No battles found.</div>
			{/if}
		</div>
	</div>
</div>

<style>
</style>
