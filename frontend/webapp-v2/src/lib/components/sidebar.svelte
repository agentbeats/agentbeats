<script lang="ts">
	import HouseIcon from "@lucide/svelte/icons/house";
	import SwordsIcon from "@lucide/svelte/icons/swords";
	import BotIcon from "@lucide/svelte/icons/bot";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import { page } from '$app/stores';

	// Menu items.
	const items = [
		{
			title: "Dashboard",
			url: "/dashboard",
			icon: HouseIcon,
		},
		{
			title: "Battles",
			url: "/battles",
			icon: SwordsIcon,
		},
		{
			title: "Agents",
			url: "/agents",
			icon: BotIcon,
		},
	];

	function isActive(url: string): boolean {
		return $page.url.pathname === url || $page.url.pathname.startsWith(url + '/');
	}
</script>

<style>
	:global([data-slot="sidebar-menu-button"]:hover) {
		background-color: transparent !important;
	}
	
	:global([data-slot="sidebar-menu-button"]:focus) {
		background-color: transparent !important;
	}
	
	:global([data-slot="sidebar-menu-button"]:active) {
		background-color: transparent !important;
	}
</style>

<Sidebar.Root
    variant="floating" 
    collapsible="none"
    class="ml-8 h-48 bg-background border rounded-full flex items-center shadow-sm relative"
    style="width: 60px; z-index: 10; position: fixed; top: 50%; transform: translateY(-50%);"
>
	<!-- Active indicator -->
	<div class="absolute left-0 w-1 h-3 bg-primary rounded-r-full transition-all duration-300 ease-in-out"
		 style="top: {(() => {
			 const activeIndex = items.findIndex(item => isActive(item.url));
			 return activeIndex >= 0 ? `${(activeIndex * 48) + 39}px` : '26px';
		 })()};">
	</div>
	
	<div class="rounded-full h-full flex items-center justify-center">
		<Sidebar.Content class="p-0">
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each items as item (item.title)}
						<Sidebar.MenuItem class="mb-1">
							<Sidebar.MenuButton 
								class="[&>svg]:size-5 !size-10 !p-2 !justify-center"
							>
								{#snippet child({ props })}
									<a href={item.url} {...props}>
										<item.icon class="text-muted-foreground hover:text-foreground" />
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
		</Sidebar.Content>
	</div>
</Sidebar.Root>