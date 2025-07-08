<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import type { Component, ComponentProps } from "svelte";

	let {
		ref = $bindable(null),
		items,
		...restProps
	}: {
		items: {
			title: string;
			url: string;
			icon: Component;
		}[];
	} & ComponentProps<typeof Sidebar.Group> = $props();
</script>

<Sidebar.Group bind:ref {...restProps}>
	<Sidebar.GroupContent>
		<Sidebar.Menu>
			{#each items as item, i (item.title)}
				<Sidebar.MenuItem class={i !== items.length - 1 ? 'mb-2' : ''}>
					<Sidebar.MenuButton 
						tooltipContent={item.title} 
						class="[&>svg]:size-4 group-data-[collapsible=icon]:[&>svg]:!size-6 group-data-[collapsible=icon]:!size-10 group-data-[collapsible=icon]:!p-3 group-data-[collapsible=icon]:!justify-center"
					>
						{#snippet child({ props })}
							<a href={item.url} {...props}>
								<item.icon />
								<span>{item.title}</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>
	</Sidebar.GroupContent>
</Sidebar.Group>
