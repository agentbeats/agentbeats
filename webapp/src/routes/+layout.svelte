<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from "mode-watcher";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar-left.svelte";
	import AppSidebarRight from "$lib/components/sidebar-right.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
	import { page } from "$app/stores";
	let { children, data } = $props();
	
	function getPageTitle(routeId: string): string {
		if (routeId === '/') return 'Dashboard';
		if (routeId.includes('/agents')) return 'Agents';
		if (routeId.includes('/battles')) return 'Battles';
		if (routeId.includes('/users')) return 'Users';
		if (routeId.includes('/dashboard')) return 'Dashboard';
		if (routeId.includes('/register-agent')) return 'Register Agent';
		if (routeId.includes('/stage-battle')) return 'Stage Battle';
		return 'AgentBeats';
	}

	// Check if current page should show sidebars
	let shouldShowSidebars = $derived(
		!$page.route.id?.includes('/login') && 
		!$page.route.id?.includes('/auth') && 
		$page.route.id !== '/'
	);
</script>

<style>
  :global(html), :global(body) {
    height: 100%;
  }
  
  /* Only apply overflow hidden when sidebars are shown */
  :global(.sidebar-layout) {
    overflow: hidden;
  }
</style>

<ModeWatcher />

{#if shouldShowSidebars}
<Sidebar.Provider
	open={false}
	style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
		class="h-screen overflow-hidden sidebar-layout"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<div class="flex flex-col flex-1 min-h-0 rounded-t-xl">
			<SiteHeader title={getPageTitle($page.route.id || '')} class="sticky top-0 z-20" />
			<main class="flex-1 overflow-auto min-h-0">
				{@render children()}
			</main>
		</div>
	</Sidebar.Inset>
	<AppSidebarRight variant="inset" />
</Sidebar.Provider>
{:else}
	<!-- No sidebars for login/auth pages -->
	<div class="min-h-screen">
		{@render children()}
	</div>
{/if}
