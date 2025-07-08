<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar-left.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
	import AgentCards from "$lib/components/agent-cards.svelte";

	export let data: { agents: any[] };
	let agents = data.agents;
</script>

<Sidebar.Provider
	open={false}
	style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<SiteHeader title={"Agents"}/>
		<div class="flex flex-1 flex-col">
			<div class="@container/main flex flex-1 flex-col gap-2">
			<div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6" style="max-width: calc(100vw - var(--sidebar-width) - 2rem);">
				<AgentCards agents={agents}/>
				</div>
			</div>
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>
