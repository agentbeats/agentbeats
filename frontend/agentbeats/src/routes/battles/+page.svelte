<script lang="ts">
	import * as Sidebar from "$lib/components/ui/sidebar/index.js";
	import AppSidebar from "$lib/components/sidebar-left.svelte";
	import SiteHeader from "$lib/components/site-header.svelte";
	import BattleCard from "$lib/components/battle-card.svelte";

	export let data: { battles: any[] };
	let battles = data.battles;
</script>

<Sidebar.Provider
	open={false}
	style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
>
	<AppSidebar variant="inset" />
	<Sidebar.Inset>
		<SiteHeader title={"Battles"}/>
		<div class="flex flex-1 flex-col">
			<div class="@container/main flex flex-1 flex-col gap-2">
				<div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6" style="max-width: calc(100vw - var(--sidebar-width) - 2rem);">
					<div class="grid grid-cols-1 gap-4 px-4 lg:px-6">
						{#each battles as battle (battle.id)}
							<BattleCard battleId={battle.id} />
						{/each}
					</div>
				</div>
			</div>
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>
