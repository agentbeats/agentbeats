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
				title: "Battles",
				url: "#",
				icon: BattleIcon,
				items: [
					{
						title: "Battle Directory",
						url: "/battles",
					},
				],
			},
			{
				title: "Agents",
				url: "#",
				icon: BotIcon,
				items: [
					{
						title: "Agent Directory",
						url: "/agents",
					},
				],
			},
			{
				title: "Documentation",
				url: "#",
				icon: BookOpenIcon,
				items: [
					{
						title: "Rules",
						url: "/documentation/rules",
					},
					{
						title: "Tutorials",
						url: "/documentation/tutorials",
					},
				],
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
		projects: [
			{
				name: "Stage Battle",
				url: "/stage-battle/",
				icon: TheaterIcon,
			},
			{
				name: "Register Agent",
				url: "/register-agent/",
				icon: RegisterIcon,
			},
		],
	};
</script>

<script lang="ts">
	import NavMain from "./nav-main.svelte";
	import NavProjects from "./nav-projects.svelte";
	import NavSecondary from "./nav-secondary.svelte";
	import NavUser from "./nav-user.svelte";
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import CommandIcon from "@lucide/svelte/icons/command";
	import type { ComponentProps } from "svelte";

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root bind:ref variant="inset" {...restProps}>
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					{#snippet child({ props })}
						<a href="/dashboard/" {...props}>
							<div
								class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
							>
								<ShieldIcon class="size-4" />
							</div>
							<div class="grid flex-1 text-left text-sm leading-tight">
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
		<NavProjects projects={data.projects} />
		<NavSecondary items={data.navSecondary} class="mt-auto" />
	</Sidebar.Content>
	<Sidebar.Footer>
		<NavUser user={data.user} />
	</Sidebar.Footer>
</Sidebar.Root>
