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

<Sidebar.Group>
	<Sidebar.GroupLabel>Games</Sidebar.GroupLabel>
	<Sidebar.Menu>
		{#each items as mainItem, index (mainItem.title)}
			<Sidebar.MenuItem>
				<Sidebar.MenuButton 
					tooltipContent={mainItem.title} 
					class="[&>svg]:size-4 group-data-[collapsible=icon]:[&>svg]:!size-7 group-data-[collapsible=icon]:!size-14 group-data-[collapsible=icon]:!p-3 group-data-[collapsible=icon]:!justify-center"
				>
					{#snippet child({ props })}
						<a href={mainItem.url} {...props}>
							<mainItem.icon />
							<span class="group-data-[collapsible=icon]:!hidden">{mainItem.title}</span>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
			
			<!-- Add divider after Agents (index 2) and Documentation (index 3) -->
			{#if index === 2 || index === 3}
				<Sidebar.MenuItem class="group-data-[collapsible=icon]:!block hidden">
					<div class="flex justify-center py-1">
						<div class="h-px w-8 bg-border" />
					</div>
				</Sidebar.MenuItem>
			{/if}
		{/each}
	</Sidebar.Menu>
</Sidebar.Group>
