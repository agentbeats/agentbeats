<script lang="ts">
	import '../../app.css';
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar.svelte";
	
	let { children } = $props();
</script>

<style>
	@import url('https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300..800;1,300..800&display=swap');
	
	.open-sans {
		font-family: "Open Sans", sans-serif;
		color: #f5f4fb;
	}
	
	.game-background {
		min-block-size: 100vb;
		background-color: #1b1b1b;
	}
</style>

<div class="min-h-screen open-sans game-background">
	<Sidebar.Provider
		style="--sidebar-width: 5rem; --sidebar-width-mobile: 5rem;"
	>
		<AppSidebar />
		<main class="ml-16 mt-10 relative">
			{@render children()}
		</main>
	</Sidebar.Provider>
</div>