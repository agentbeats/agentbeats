<script lang="ts">
	import CalendarIcon from "@lucide/svelte/icons/calendar";
	import HouseIcon from "@lucide/svelte/icons/house";
	import InboxIcon from "@lucide/svelte/icons/inbox";
	import SearchIcon from "@lucide/svelte/icons/search";
	import SettingsIcon from "@lucide/svelte/icons/settings";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import * as Tooltip from "$lib/components/ui/tooltip/index.js";
	
	// Menu items.
	const items = [
		{
			title: "Home",
			url: "#",
			icon: HouseIcon,
		},
		{
			title: "Inbox",
			url: "#",
			icon: InboxIcon,
		},
		{
			title: "Calendar",
			url: "#",
			icon: CalendarIcon,
		},
		{
			title: "Search",
			url: "#",
			icon: SearchIcon,
		},
		{
			title: "Settings",
			url: "#",
			icon: SettingsIcon,
		},
	];
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
    class="mt-8 ml-10 mb-8 h-[calc(100vh-4rem)] bg-[#323232] rounded-2xl"
>
	<div class="rounded-2xl h-full">
		<Sidebar.Content class="p-1">
		<Sidebar.Group>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each items as item (item.title)}
						<Sidebar.MenuItem class="mb-2">
							<Sidebar.MenuButton 
								class="[&>svg]:size-6 !size-14 !p-3 !justify-center"
							>
								{#snippet child({ props })}
									<Tooltip.Root>
										<Tooltip.Trigger>
											<a href={item.url} {...props}>
												<item.icon class="text-[#f5f4fb]" />
											</a>
										</Tooltip.Trigger>
										<Tooltip.Content side="right">
											{item.title}
										</Tooltip.Content>
									</Tooltip.Root>
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