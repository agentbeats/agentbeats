<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar-left.svelte";
	import AppSidebarRight from "$lib/components/sidebar-right.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
</script>

<Sidebar.Provider
	open={false}
	style="--header-height: calc(var(--spacing) * 12); --sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16);"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<SiteHeader title={"Dashboard"}/>
		<main class="flex-1 p-6">
			<!-- Your dashboard content here -->
		</main>
	</Sidebar.Inset>
	<AppSidebarRight variant="inset" />
</Sidebar.Provider>
