<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";

	let {
		items,
	}: {
		items: {
			title: string;
			url: string;
			// This should be `Component` after @lucide/svelte updates types
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			icon: any;
			isActive?: boolean;
			items?: {
				title: string;
				url: string;
			}[];
		}[];
	} = $props();
</script>

<style>
  :global(.sidebar-nav-hover) {
    transition: transform 0.18s cubic-bezier(0.4,0,0.2,1);
  }
  :global(.sidebar-nav-hover:hover) {
    transform: translateY(-2px);
  }
  :global(.sidebar-nav-hover svg) {
    transition: color 0.25s ease, stroke 0.25s ease;
  }
  :global(.sidebar-nav-hover:hover svg) {
    color: #4caf50 !important;
    stroke: #4caf50 !important;
  }
</style>

<Sidebar.Group>
	<Sidebar.GroupLabel>Games</Sidebar.GroupLabel>
	<Sidebar.Menu>
		{#each items as mainItem, index (mainItem.title)}
			<Sidebar.MenuItem>
				<Sidebar.MenuButton 
					tooltipContent={mainItem.title} 
					class="sidebar-nav-hover [&>svg]:size-4 group-data-[collapsible=icon]:[&>svg]:!size-6 group-data-[collapsible=icon]:!size-14 group-data-[collapsible=icon]:!p-3 group-data-[collapsible=icon]:!justify-center"
				>
					{#snippet child({ props })}
						<a href={mainItem.url} {...props}>
							<mainItem.icon />
							<span class="group-data-[collapsible=icon]:!hidden">{mainItem.title}</span>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		{/each}
	</Sidebar.Menu>
</Sidebar.Group>
