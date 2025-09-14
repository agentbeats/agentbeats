<script lang="ts">
	import '../../app.css';
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar.svelte";
	import { Toaster } from 'svelte-sonner';
	import { fade } from 'svelte/transition';
	import { onNavigate } from '$app/navigation';
	import { ModeWatcher } from "mode-watcher";
	import BattleCart from "$lib/components/battle-cart.svelte";
	import { page } from '$app/stores';
	
	let { children } = $props();
	
	// Check if we're on a battle details page
	let isBattleDetailsPage = $derived($page.url.pathname.match(/\/battles\/[^\/]+\/?$/) && 
		!['ongoing', 'past', 'stage-battle'].includes($page.url.pathname.split('/').pop() || ''));
	
	onNavigate((navigation) => {
		if (!document.startViewTransition) return;
	
		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				resolve();
				await navigation.complete;
			});
		});
	});
</script>

<div class="min-h-screen">
	<!-- Dark/Light Mode Switcher -->
	<div class="fixed top-4 left-4 z-50">
		<ModeWatcher />
	</div>
	
	<Sidebar.Provider
		style="--sidebar-width: 5rem; --sidebar-width-mobile: 5rem;"
	>
		<AppSidebar />
		<main class="ml-16 mt-10 relative w-full">
			<div in:fade={{ duration: 200 }} out:fade={{ duration: 150 }}>
				{@render children()}
			</div>
		</main>
	</Sidebar.Provider>
	<Toaster position="top-center" />
	{#if !isBattleDetailsPage}
		<BattleCart />
	{/if}
</div>