<script lang="ts" module>
	import BookOpenIcon from "@lucide/svelte/icons/book-open";
	import BotIcon from "@lucide/svelte/icons/bot";
	import BattleIcon from "@lucide/svelte/icons/swords";
	import TheaterIcon from "@lucide/svelte/icons/theater";
	import RegisterIcon from "@lucide/svelte/icons/smile-plus";
	import LayoutDashboardIcon from "@lucide/svelte/icons/layout-dashboard";
	import BotMessageSquareIcon from "@lucide/svelte/icons/bot-message-square";
	import UserIcon from "@lucide/svelte/icons/user";

	const data = {
		navMain: [
			{
				title: "Dashboard",
				url: "/dashboard",
				icon: LayoutDashboardIcon,
			},
			{
				title: "Battles",
				url: "/battles",
				icon: BattleIcon,
			},
			{
				title: "Agents",
				url: "/agents",
				icon: BotIcon,
			},
			{
				title: "Users",
				url: "/users",
				icon: UserIcon,
			},
			{
				title: "Documentation",
				url: "#",
				icon: BookOpenIcon,
			},
		],
	};
</script>

<script lang="ts">
	import NavMain from "./nav-main.svelte";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import type { ComponentProps } from "svelte";

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root 
    bind:ref 
	variant="inset" 
	collapsible="icon" 
	class="border-r-0" 
	{...restProps}
>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg" class="group-data-[collapsible=icon]:!justify-center group-data-[collapsible=icon]:!size-14 group-data-[collapsible=icon]:!p-3">
					{#snippet child({ props })}
						<a href="/dashboard/" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg group-data-[collapsible=icon]:!size-12 group-data-[collapsible=icon]:!rounded-md"
							>
								<BotMessageSquareIcon class="size-4 group-data-[collapsible=icon]:!size-8" />
							</div>
							<div class="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:!hidden">
								<span class="truncate font-medium">AgentBeats</span>
							</div>
						</a>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<NavMain items={data.navMain} />
	</Sidebar.Content>
</Sidebar.Root>
