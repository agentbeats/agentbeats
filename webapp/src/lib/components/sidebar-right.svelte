<script lang="ts" module>
	import ContactIcon from "@lucide/svelte/icons/user-round-pen";
	import SendIcon from "@lucide/svelte/icons/send";
	import BugIcon from "@lucide/svelte/icons/bug";

	const data = {
		user: {
			name: "miaomiaogato",
			email: "miao@agentbeats.com",
			avatar: "",
		},
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
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import type { ComponentProps } from "svelte";

	let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
</script>

<Sidebar.Root
	bind:ref
	variant="inset"
	collapsible="icon"
	side="right"
	{...restProps}
>
	<Sidebar.Header>
	</Sidebar.Header>
	<Sidebar.Content>
	</Sidebar.Content>
</Sidebar.Root> 