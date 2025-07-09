<script lang="ts">
	import BattleCard from "$lib/components/battle-card.svelte";
	import BattleChip from "$lib/components/battle-chip.svelte";
	import * as Sheet from "$lib/components/ui/sheet";
	import { createBattle } from "$lib/api/battles.js";
	import { getAllAgents } from "$lib/api/agents";
	import { goto } from "$app/navigation";
	import { onMount, onDestroy } from "svelte";
	import SwordsIcon from '@lucide/svelte/icons/swords';
	import { fade } from 'svelte/transition';

	export let data: { battles: any[] };
	let battles = data.battles;

	let ws: WebSocket | null = null;

	function recalcBattles() {
		const ongoingStatuses = ["pending", "queued", "running"];
		const pastStatuses = ["finished", "error"];
		ongoingBattles = battles.filter(
			b => ongoingStatuses.includes((b.state || '').toLowerCase())
		);
		pastBattles = battles.filter(
			b => pastStatuses.includes((b.state || '').toLowerCase())
		);
		// Ensure finished battles are always in pastBattles, not ongoingBattles
		const finishedIds = new Set(pastBattles.map(b => b.id));
		ongoingBattles = ongoingBattles.filter(b => !finishedIds.has(b.id));
	}

	onMount(() => {
		recalcBattles();
		console.log('[WS] Connecting to ws://localhost:9000/ws/battles');
		ws = new WebSocket("ws://localhost:9000/ws/battles");
		ws.onopen = () => console.log('[WS] Connected');
		ws.onclose = (e) => console.log('[WS] Closed', e);
		ws.onerror = (e) => console.error('[WS] Error', e);
		ws.onmessage = (event) => {
			console.log('[WS] Message', event.data);
			try {
				const msg = JSON.parse(event.data);
				if (msg && msg.type === "battles_update" && Array.isArray(msg.battles)) {
					battles = msg.battles;
					recalcBattles();
				}
				// Optionally: handle single battle updates
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
				console.error('[WS] JSON parse error', e);
			}
		};
	});

	onDestroy(() => {
		if (ws) ws.close();
	});

	export const title = 'Battles';

	// Split battles into ongoing and past
	const ongoingStatuses = ["pending", "queued", "running"];
	const pastStatuses = ["finished", "error"];

	let ongoingBattles = battles.filter(
		b => ongoingStatuses.includes((b.state || '').toLowerCase())
	);
	let pastBattles = battles.filter(
		b => pastStatuses.includes((b.state || '').toLowerCase())
	);
	// Ensure finished battles are always in pastBattles, not ongoingBattles
	const finishedIds = new Set(pastBattles.map(b => b.id));
	ongoingBattles = ongoingBattles.filter(b => !finishedIds.has(b.id));

	let showSheet = false;
	let formData = {
		greenAgentId: "",
		opponents: "",
		timeout: 20,
		rounds: 3,
		topic: ""
	};
	let isSubmitting = false;
	let error = "";
	let agents: any[] = [];
	let agentsLoading = true;
	let agentsError = "";
	onMount(async () => {
		agentsLoading = true;
		try {
			agents = await getAllAgents();
		} catch (e) {
			agentsError = e instanceof Error ? e.message : 'Failed to load agents';
		} finally {
			agentsLoading = false;
		}
	});

	async function handleSubmit() {
		isSubmitting = true;
		error = "";
		try {
			const opponentsArray = Array.isArray(formData.opponents) ? formData.opponents : [formData.opponents].filter(Boolean);
			const battleInfo = {
				greenAgentId: formData.greenAgentId,
				opponents: opponentsArray,
				topic: formData.topic,
				config: {
					timeout: formData.timeout,
					rounds: formData.rounds
				}
			};
			await createBattle(battleInfo);
			showSheet = false;
			goto('/battles');
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="w-full flex flex-col items-center justify-center mt-10 mb-8">
	<h1 class="text-2xl font-bold text-center mb-8">Stage a Battle</h1>
	<button type="button" class="stage-battle-btn flex items-center gap-2" on:click={() => showSheet = true}>
		<SwordsIcon class="w-6 h-6" />
		Stage a Battle
	</button>
</div>
{#if showSheet}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click={() => showSheet = false}>
		<div class="bg-background rounded-xl shadow-2xl p-6 max-w-lg w-full relative" on:click|stopPropagation>
			<button class="absolute top-3 right-3 text-muted-foreground hover:text-foreground" on:click={() => showSheet = false} aria-label="Close">
				<span class="text-xl">&times;</span>
			</button>
			<h2 class="text-xl font-bold mb-4">Stage a Battle</h2>
			<form on:submit|preventDefault={handleSubmit} class="flex flex-col gap-4">
				<div>
					<label for="greenAgentId" class="block mb-1 font-medium">Green Agent:</label>
					<select id="greenAgentId" bind:value={formData.greenAgentId} required class="w-full px-3 py-2 border rounded-md">
						<option value="" disabled selected>Select a green agent</option>
						{#each agents.filter(a => ((a.registerInfo?.meta?.type || a.register_info?.meta?.type || '').toLowerCase() === 'green')) as agent}
							<option value={agent.id}>{agent.registerInfo?.name || agent.register_info?.name || agent.agentCard?.name || agent.agent_card?.name || agent.id} ({agent.registerInfo?.meta?.type || agent.register_info?.meta?.type || 'unknown'})</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="opponents" class="block mb-1 font-medium">Opponent Agents:</label>
					<select id="opponents" multiple bind:value={formData.opponents} required class="w-full px-3 py-2 border rounded-md min-h-[4rem]">
						{#each agents.filter(a => ['red','blue'].includes((a.registerInfo?.meta?.type || a.register_info?.meta?.type || '').toLowerCase())) as agent}
							<option value={agent.id}>{agent.registerInfo?.name || agent.register_info?.name || agent.agentCard?.name || agent.agent_card?.name || agent.id} ({agent.registerInfo?.meta?.type || agent.register_info?.meta?.type || 'unknown'})</option>
						{/each}
					</select>
					<div class="text-xs text-muted-foreground mt-1">Hold Ctrl (Cmd on Mac) to select multiple opponents.</div>
				</div>
				<div>
					<label for="topic" class="block mb-1 font-medium">Battle Topic:</label>
					<input id="topic" type="text" bind:value={formData.topic} placeholder="Enter a topic or name for this battle" class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div class="flex gap-4">
					<div class="flex-1">
						<label for="timeout" class="block mb-1 font-medium">Timeout (seconds):</label>
						<input id="timeout" type="number" bind:value={formData.timeout} min="1" required class="w-full px-3 py-2 border rounded-md" />
					</div>
					<div class="flex-1">
						<label for="rounds" class="block mb-1 font-medium">Rounds:</label>
						<input id="rounds" type="number" bind:value={formData.rounds} min="1" required class="w-full px-3 py-2 border rounded-md" />
					</div>
				</div>
				{#if error}
					<div class="text-red-500 text-sm">{error}</div>
				{/if}
				<div class="flex gap-2 justify-end mt-2">
					<button type="submit" class="px-4 py-2 rounded-md bg-primary text-primary-foreground font-semibold shadow hover:bg-primary/90 transition disabled:opacity-60" disabled={isSubmitting}>
						{isSubmitting ? 'Creating...' : 'Create Battle'}
					</button>
					<button type="button" class="px-4 py-2 rounded-md bg-muted text-foreground font-semibold shadow hover:bg-accent transition" on:click={() => showSheet = false}>Cancel</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh]">
	<div class="@container/main flex flex-1 flex-col gap-2 items-center justify-center w-full">
		<div class="flex flex-col gap-10 py-4 md:gap-12 md:py-6 w-full items-center justify-center">
			<!-- Ongoing Battles -->
			{#if ongoingBattles.length > 0}
				<div class="w-full max-w-5xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-10 mt-10">Ongoing Battles</h2>
					<div class="grid grid-cols-1 gap-4 px-4 lg:px-6 w-full">
						{#each ongoingBattles.slice(0, 3) as battle (battle.id)}
							<div role="button" tabindex="0" class="cursor-pointer" on:click={() => goto(`/battle/${battle.id}`)} transition:fade={{ duration: 220 }}>
								<BattleCard battleId={battle.id} />
							</div>
						{/each}
					</div>
					{#if ongoingBattles.length > 3}
						<button class="view-all-btn mt-6 px-6 py-2 rounded-lg bg-accent text-accent-foreground font-semibold shadow hover:bg-accent/80 transition" on:click={() => goto('/battles/ongoing')}>
							View All
						</button>
					{/if}
				</div>
			{/if}
			<!-- Past Battles -->
			{#if pastBattles.length > 0}
				<div class="w-full max-w-5xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-8 mt-8">Past Battles</h2>
					<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 px-2 md:px-4 w-full">
						{#each pastBattles as battle (battle.id)}
							<div role="button" tabindex="0" class="cursor-pointer p-1 md:p-2" on:click={() => goto(`/battle/${battle.id}`)} transition:fade={{ duration: 220 }}>
								<BattleChip battleId={battle.id} compact={true} />
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
.past-battle-chip {
	font-size: 0.85rem;
	padding: 0.5rem 0.75rem;
	line-height: 1.2;
	gap: 0.25rem;
}
.stage-battle-btn {
	font-size: 1.1rem;
	padding: 15px 40px;
	background: linear-gradient(45deg, #256d3a, #1b4332);
	color: #fff;
	border: none;
	border-radius: 8px;
	font-weight: 600;
	cursor: pointer;
	box-shadow: 0 4px 12px rgba(76, 175, 80, 0.18);
	transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
	margin-bottom: 1rem;
}
.stage-battle-btn:hover {
	background: linear-gradient(45deg, #388e3c, #14532d);
	transform: translateY(-2px) scale(1.03);
	box-shadow: 0 10px 30px rgba(33, 209, 80, 0.18);
}
.stage-battle-btn:active {
	transform: scale(0.98);
}
.view-all-btn {
	font-size: 1rem;
	background: linear-gradient(45deg, #256d3a, #1b4332);
	color: #fff;
	border: none;
	border-radius: 8px;
	font-weight: 600;
	cursor: pointer;
	box-shadow: 0 2px 8px rgba(76, 175, 80, 0.12);
	transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
}
.view-all-btn:hover {
	background: linear-gradient(45deg, #388e3c, #14532d);
	transform: translateY(-2px) scale(1.03);
	box-shadow: 0 6px 18px rgba(33, 209, 80, 0.14);
}
</style>
