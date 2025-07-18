<script lang="ts">
// Minimalist, shadcn-svelte-based battles page
import { onMount, onDestroy } from 'svelte';
import { goto } from '$app/navigation';
import BattleCard from '$lib/components/battle-card-ongoing.svelte';
import BattleChip from '$lib/components/battle-card-finished.svelte';
import { user, loading } from '$lib/stores/auth';
import { supabase } from '$lib/auth/supabase';

export let data: { battles: any[] };
let battles = data.battles;
let ws: WebSocket | null = null;
let unsubscribe: (() => void) | null = null;

function recalcBattles() {
	const ongoingStatuses = ["pending", "queued", "running"];
	const pastStatuses = ["finished", "error"];
	ongoingBattles = battles.filter(b => ongoingStatuses.includes((b.state || '').toLowerCase()));
	pastBattles = battles.filter(b => pastStatuses.includes((b.state || '').toLowerCase()));
	const finishedIds = new Set(pastBattles.map(b => b.battle_id));
	ongoingBattles = ongoingBattles.filter(b => !finishedIds.has(b.battle_id));
	
	// Sort ongoingBattles by created_at descending (most recent first)
	ongoingBattles.sort((a, b) => {
		const aTime = new Date(a.created_at || 0).getTime();
		const bTime = new Date(b.created_at || 0).getTime();
		return bTime - aTime;
	});
	
	// Sort pastBattles by finish_time or created_at descending (most recent first)
	pastBattles.sort((a, b) => {
		function getTime(battle: any) {
			let dt = battle.result?.finish_time || battle.created_at || 0;
			if (typeof dt === 'string' && dt && !dt.endsWith('Z')) dt = dt + 'Z';
			const t = new Date(dt).getTime();
			return isNaN(t) ? 0 : t;
		}
		return getTime(b) - getTime(a);
	});
}

onMount(async () => {
  // Check authentication using user store (works with dev login)
  const unsubscribeUser = user.subscribe(($user) => {
    if (!$user && !$loading) {
      console.log('Battles page: No user found, redirecting to login');
      goto('/login');
    }
  });
  
  // If no user in store, check Supabase session as fallback
  if (!$user) {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      console.log('Battles page: No session found, redirecting to login');
      goto('/login');
      return;
    }
  }
  
  // Subscribe to auth state changes for logout detection
  unsubscribe = user.subscribe(($user) => {
    if (!$user && !$loading) {
      console.log('Battles page: User logged out, redirecting to login');
      goto('/login');
    }
  });
  
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

onDestroy(() => { 
  if (ws) ws.close(); 
  if (unsubscribe) {
    unsubscribe();
  }
});

let ongoingBattles: any[] = [];
let pastBattles: any[] = [];
let ongoingToShow = 3;
let pastToShow = 10;

function showMoreOngoing() {
  ongoingToShow += 3;
}
function showMorePast() {
  pastToShow += 10;
}
</script>

<div class="w-full flex flex-col items-center justify-center mt-10 mb-8">
	<h1 class="text-2xl font-bold text-center mb-8">Battles</h1>
	<button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition cursor-pointer" onclick={() => goto('/battles/stage-battle')}>
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
						{#each ongoingBattles.slice(0, ongoingToShow) as battle (battle.battle_id)}
							<button type="button" class="cursor-pointer w-full" onclick={() => goto(`/battles/${battle.battle_id}`)} onkeydown={(e) => e.key === 'Enter' && goto(`/battles/${battle.battle_id}`)}>
								<BattleCard battleId={battle.battle_id} />
							</button>
						{/each}
						{#if ongoingBattles.length > ongoingToShow}
							<button type="button" class="mt-2 px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium" onclick={showMoreOngoing}>
								View More
							</button>
						{/if}
					</div>
				</div>
			{/if}
			{#if pastBattles.length > 0}
				<div class="w-full max-w-4xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-8 mt-8">Past Battles</h2>
					<div class="flex flex-col gap-4 w-full">
						{#each pastBattles.slice(0, pastToShow) as battle (battle.battle_id)}
							<button type="button" class="cursor-pointer w-full" onclick={() => goto(`/battles/${battle.battle_id}`)} onkeydown={(e) => e.key === 'Enter' && goto(`/battles/${battle.battle_id}`)}>
								<BattleChip battleId={battle.battle_id} />
							</button>
						{/each}
						{#if pastBattles.length > pastToShow}
							<button type="button" class="mt-2 px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium" onclick={showMorePast}>
								View More
							</button>
						{/if}
					</div>
				</div>
			{/if}
			{#if ongoingBattles.length === 0 && pastBattles.length === 0}
				<div class="text-center text-muted-foreground">No battles found.</div>
			{/if}
		</div>
	</div>
</div>


