<script lang="ts">
	import TrendingDownIcon from "@tabler/icons-svelte/icons/trending-down";
	import TrendingUpIcon from "@tabler/icons-svelte/icons/trending-up";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import * as Card from "$lib/components/ui/card/index.js";

	let {
		battles,
	}: {
		battles: {
			id: string;
			green_agent: string;
			red_agent: string;
			blue_agent: string;
			status: string;
		}[];
	} = $props();
</script>

<div
	class="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card *:data-[slot=card]:shadow-xs grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t lg:px-6"
>
	{#each battles as battle (battle.id)}
		<Card.Root class="@container/card">
			<Card.Header>
				<Card.Description>{battle.id}</Card.Description>
				<Card.Title class="@[250px]/card:text-3xl text-2xl font-semibold tabular-nums">
					{battle.green_agent}
				</Card.Title>
			</Card.Header>
			<Card.Footer class="flex-col items-start gap-1.5 text-sm">
				<div class="line-clamp-1 flex gap-2 font-medium">
					Blue Agent: {battle.blue_agent}
				</div>
				<div class="line-clamp-1 flex gap-2 font-medium">
					Red Agent: {battle.red_agent}
				</div>
				<div class="text-muted-foreground">Status: {battle.status}</div>
			</Card.Footer>
		</Card.Root>
	{/each}
</div>
