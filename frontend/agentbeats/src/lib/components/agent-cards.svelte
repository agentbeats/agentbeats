<script lang="ts">
	import TrendingDownIcon from "@tabler/icons-svelte/icons/trending-down";
	import TrendingUpIcon from "@tabler/icons-svelte/icons/trending-up";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import * as Card from "$lib/components/ui/card/index.js";

	let {
		agents,
	}: {
		agents: {
			name: string;
			trainer: string;
			elo: string;
			type: string;
			description: string;
		}[];
	} = $props();
</script>

<div
	class="grid grid-cols-1 gap-4 px-4 lg:px-6"
>
	{#each agents as agent (agent.name)}
		<Card.Root class="w-full">
			<Card.Header>
				<Card.Description>{agent.trainer}</Card.Description>
				<Card.Title class="text-2xl font-semibold tabular-nums">
					{agent.name}
				</Card.Title>
				<Card.Action>
					<Badge variant="outline">
						{agent.elo}
					</Badge>
				</Card.Action>
			</Card.Header>
			<Card.Footer class="flex-col items-start gap-1.5 text-sm">
				<div class="line-clamp-1 flex gap-2 font-medium">
					Agent Type: {agent.type}
				</div>
				<div class="text-muted-foreground">Description: {agent.description}</div>
			</Card.Footer>
		</Card.Root>
	{/each}
</div>
