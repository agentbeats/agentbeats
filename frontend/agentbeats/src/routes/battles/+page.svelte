<script lang="ts">
	import BattleCard from "$lib/components/battle-card.svelte";
	import BattleChip from "$lib/components/battle-chip.svelte";
	import * as Sheet from "$lib/components/ui/sheet";
	import { createBattle } from "$lib/api/battles.js";
	import { getAllAgents } from "$lib/api/agents";
	import { goto } from "$app/navigation";
	import { onMount } from "svelte";

	export let data: { battles: any[] };
	let battles = data.battles;

	export const title = 'Battles';

	// Split battles into ongoing and past
	const ongoingStatuses = ["pending", "active", "in_progress", "started"];
	const pastStatuses = ["completed", "finished"];

	let ongoingBattles = battles.filter(
		b => !pastStatuses.includes((b.status || '').toLowerCase()) && (b.status || '').toLowerCase() !== 'error'
	);
	let pastBattles = battles.filter(
		b => pastStatuses.includes((b.status || '').toLowerCase()) || (b.status || '').toLowerCase() === 'error'
	);

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
	<h1 class="text-2xl font-bold text-center mb-4">Stage a Battle</h1>
	<button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition" on:click={() => showSheet = true}>
		<span class="text-xl font-bold">+</span>
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
						{#each agents.filter(a => (a.registerInfo?.meta?.type || '').toLowerCase() === 'green') as agent}
							<option value={agent.id}>{agent.registerInfo?.name || agent.agentCard?.name || agent.id} ({agent.registerInfo?.meta?.type || 'unknown'})</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="opponents" class="block mb-1 font-medium">Opponent Agents:</label>
					<select id="opponents" multiple bind:value={formData.opponents} required class="w-full px-3 py-2 border rounded-md min-h-[4rem]">
						{#each agents.filter(a => ['red','blue'].includes((a.registerInfo?.meta?.type || '').toLowerCase())) as agent}
							<option value={agent.id}>{agent.registerInfo?.name || agent.agentCard?.name || agent.id} ({agent.registerInfo?.meta?.type || 'unknown'})</option>
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
						{#each ongoingBattles as battle (battle.id)}
							<BattleCard battleId={battle.id} />
						{/each}
					</div>
				</div>
			{/if}
			<!-- Past Battles -->
			{#if pastBattles.length > 0}
				<div class="w-full max-w-5xl flex flex-col items-center">
					<h2 class="text-2xl font-bold text-center mb-10 mt-10">Past Battles</h2>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-8 px-4 lg:px-6 w-full">
						{#each pastBattles as battle (battle.id)}
							<BattleChip battleId={battle.id} />
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
