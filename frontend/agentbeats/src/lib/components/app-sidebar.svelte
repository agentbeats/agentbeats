<script lang="ts" module>
	import BookOpenIcon from "@lucide/svelte/icons/book-open";
	import BotIcon from "@lucide/svelte/icons/bot";
	import BattleIcon from "@lucide/svelte/icons/swords";
	import BugIcon from "@lucide/svelte/icons/bug";
	import TheaterIcon from "@lucide/svelte/icons/theater";
	import ContactIcon from "@lucide/svelte/icons/user-round-pen";
	import SendIcon from "@lucide/svelte/icons/send";
	import RegisterIcon from "@lucide/svelte/icons/smile-plus";
	import ShieldIcon from "@lucide/svelte/icons/shield-half";

	const data = {
		user: {
			name: "miaomiaogato",
			email: "miao@agentbeats.com",
			avatar: "",
		},
		navMain: [
			{
				title: "Dashboard",
				url: "/dashboard",
				icon: ShieldIcon,
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
				title: "Documentation",
				url: "#",
				icon: BookOpenIcon,
			},
			{
				title: "Stage Battle",
				url: "/stage-battle/",
				icon: TheaterIcon,
			},
			{
				title: "Register Agent",
				url: "/register-agent/",
				icon: RegisterIcon,
			},
		],
		navSecondary: [
			{
				title: "Contact Support",
				url: "/contact/",
				icon: ContactIcon,
			},
			{
				title: "Send Feedback",
				url: "/feedback/",
				icon: SendIcon,
			},
            {
				title: "Report A Bug",
				url: "/bug/",
				icon: BugIcon,
			},
		],
	};
</script>

<script lang="ts">
	import NavMain from "./nav-main.svelte";
	import NavSecondary from "./nav-contact.svelte";
	import NavUser from "./nav-user.svelte";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import CommandIcon from "@lucide/svelte/icons/command";
	import type { ComponentProps } from "svelte";

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref variant="inset" collapsible="icon" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg" class="group-data-[collapsible=icon]:!justify-center group-data-[collapsible=icon]:!size-14 group-data-[collapsible=icon]:!p-3">
					{#snippet child({ props })}
						<a href="/dashboard/" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg group-data-[collapsible=icon]:!size-12 group-data-[collapsible=icon]:!rounded-md"
							>
								<ShieldIcon class="size-4 group-data-[collapsible=icon]:!size-8" />
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
		<NavSecondary items={data.navSecondary} class="mt-auto" />
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser user={data.user} />
	</Sidebar.Footer>
</Sidebar.Root>
