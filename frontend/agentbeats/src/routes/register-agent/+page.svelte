<script lang="ts">
	import { goto } from "$app/navigation";
	import { registerAgent } from "$lib/api/agents.js";

	export const title = 'Register Agent';

	let formData = {
		name: "",
		endpoint: "",
		launcher: "",
		type: "green"
	};

	let isSubmitting = false;
	let error = "";

	async function handleSubmit() {
		isSubmitting = true;
		error = "";

		try {
			const registerInfo = {
				name: formData.name,
				endpoint: formData.endpoint,
				launcher: formData.launcher,
				meta: {
					type: formData.type
				}
			};

			const result = await registerAgent(registerInfo);
			console.log('Agent registered successfully:', result);
			goto('/agents');
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isSubmitting = false;
		}
	}
</script>

<main class="flex-1 p-6">
	<div class="flex flex-1 flex-col">
		<div class="@container/main flex flex-1 flex-col gap-2">
			<div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6" style="max-width: calc(100vw - var(--sidebar-width) - 2rem);">
				<h1>Register New Agent</h1>
				<form on:submit|preventDefault={handleSubmit} style="display: flex; flex-direction: column; gap: 20px;">
					<div>
						<label for="name">Agent Name:</label>
						<input 
							id="name" 
							type="text" 
							bind:value={formData.name} 
							required
							style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
						/>
					</div>

					<div>
						<label for="endpoint">Agent Endpoint:</label>
						<input 
							id="endpoint" 
							type="text" 
							bind:value={formData.endpoint} 
							placeholder="http://localhost:9999"
							required
							style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
						/>
					</div>

					<div>
						<label for="launcher">Launcher URL:</label>
						<input 
							id="launcher" 
							type="text" 
							bind:value={formData.launcher} 
							placeholder="http://launcher-url"
							required
							style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
						/>
					</div>

					<div>
						<label for="type">Agent Type:</label>
						<select 
							id="type" 
							bind:value={formData.type}
							style="width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
						>
							<option value="green">Green Team</option>
							<option value="red">Red Team</option>
							<option value="blue">Blue Team</option>
							<option value="purple">Purple Team</option>
						</select>
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
							{isSubmitting ? 'Registering...' : 'Register Agent'}
						</button>
						<button 
							type="button" 
							on:click={() => goto('/agents')}
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
