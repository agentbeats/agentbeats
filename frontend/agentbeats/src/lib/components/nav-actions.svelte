<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";

	let {
		projects,
	}: {
		projects: {
			name: string;
			url: string;
			// This should be `Component` after @lucide/svelte updates types
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			icon: any;
		}[];
	} = $props();
</script>

<Sidebar.Group class="group-data-[collapsible=icon]:hidden">
	<Sidebar.GroupLabel>Actions</Sidebar.GroupLabel>
	<Sidebar.Menu>
		{#each projects as item (item.name)}
			<Sidebar.MenuItem>
				<Sidebar.MenuButton class="[&>svg]:size-4 group-data-[collapsible=icon]:[&>svg]:!size-6 group-data-[collapsible=icon]:!size-12 group-data-[collapsible=icon]:!p-3">
					{#snippet child({ props })}
						<a href={item.url} {...props}>
							<item.icon />
							<span>{item.name}</span>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		{/each}
	</Sidebar.Menu>
</Sidebar.Group>
