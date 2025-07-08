<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from "mode-watcher";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar-left.svelte";
	import AppSidebarRight from "$lib/components/sidebar-right.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
	let { children, data } = $props();
</script>

<style>
  html, body {
    overflow: hidden;
    height: 100%;
  }
</style>

<ModeWatcher />
<Sidebar.Provider
	open={false}
	style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<div class="flex flex-col h-full min-h-0">
			<SiteHeader title={data.title ?? 'AgentBeats'} class="sticky top-0 z-20" />
			<main class="flex-1 overflow-auto min-h-0">
				{@render children()}
			</main>
		</div>
	</Sidebar.Inset>
	<AppSidebarRight variant="inset" />
</Sidebar.Provider>
