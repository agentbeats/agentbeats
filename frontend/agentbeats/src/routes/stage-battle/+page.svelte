<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/app-sidebar.svelte";
	import AppSidebarRight from "$lib/components/app-sidebar-right.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
	import { goto } from "$app/navigation";
	import { createBattle } from "$lib/api/battles.js";

	let formData = {
		greenAgentId: "",
		opponents: "",
		timeout: 20,
		rounds: 3
	};

	let isSubmitting = false;
	let error = "";

	async function handleSubmit() {
		isSubmitting = true;
		error = "";

		try {
			// Parse opponents string into array (comma-separated)
			const opponentsArray = formData.opponents.split(',').map(id => id.trim()).filter(id => id);

			const battleInfo = {
				greenAgentId: formData.greenAgentId,
				opponents: opponentsArray,
				config: {
					timeout: formData.timeout,
					rounds: formData.rounds
				}
			};

			const result = await createBattle(battleInfo);
			console.log('Battle created successfully:', result);
			goto('/battles');
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<Sidebar.Provider
	open={false}
	style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<SiteHeader title={"Stage Battle"}/>
		<main class="flex-1 p-6">
			<div class="flex flex-1 flex-col">
				<div class="@container/main flex flex-1 flex-col gap-2">
					<div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6" style="max-width: calc(100vw - var(--sidebar-width) - 2rem);">
						<h1>Stage New Battle</h1>
						
						<form on:submit|preventDefault={handleSubmit} style="display: flex; flex-direction: column; gap: 20px;">
							<div>
								<label for="greenAgentId">Green Agent ID:</label>
								<input 
									id="greenAgentId" 
									type="text" 
									bind:value={formData.greenAgentId} 
									required
									style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
								/>
							</div>

							<div>
								<label for="opponents">Opponent Agent IDs (comma-separated):</label>
								<input 
									id="opponents" 
									type="text" 
									bind:value={formData.opponents} 
									placeholder="agent-id-1, agent-id-2, agent-id-3"
									required
									style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
								/>
							</div>

							<div>
								<label for="timeout">Timeout (seconds):</label>
								<input 
									id="timeout" 
									type="number" 
									bind:value={formData.timeout} 
									min="1"
									required
									style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
								/>
							</div>

							<div>
								<label for="rounds">Number of Rounds:</label>
								<input 
									id="rounds" 
									type="number" 
									bind:value={formData.rounds} 
									min="1"
									required
									style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
								/>
							</div>

							{#if error}
								<div style="color: red; font-size: 14px;">{error}</div>
							{/if}

							<div style="display: flex; gap: 10px;">
								<button 
									type="submit" 
									disabled={isSubmitting}
									style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;"
								>
									{isSubmitting ? 'Creating Battle...' : 'Create Battle'}
								</button>
								<button 
									type="button" 
									on:click={() => goto('/battles')}
									style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;"
								>
									Cancel
								</button>
							</div>
						</form>
					</div>
				</div>
			</div>
		</main>
	</Sidebar.Inset>
	<AppSidebarRight variant="inset" />
</Sidebar.Provider>
