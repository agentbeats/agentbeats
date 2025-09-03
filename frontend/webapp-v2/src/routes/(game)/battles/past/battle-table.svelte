<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import * as Carousel from "$lib/components/ui/carousel";
  import BattleTableActions from "./battle-table-actions.svelte";

  // Define the Battle type
  export type Battle = {
    battle_id: string;
    green_agent_id: string;
    opponents: Array<{ name: string; agent_id: string }>;
    created_by: string;
    created_at: string;
    state: string;
    green_agent?: any;
    opponent_agents?: any[];
    result?: { winner: string };
    error?: string;
  };

  const { battles } = $props<{ battles: Battle[] }>();

  let searchTerm = $state("");
  let currentPage = $state(1);
  let pageSize = $state(10);
  let sortColumn = $state("created_at");
  let sortDirection = $state("desc");

  // Computed values
  let filteredBattles = $derived.by(() => {
    if (!searchTerm) return battles;
    return battles.filter((battle: Battle) => 
      battle.green_agent?.register_info?.alias?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      battle.green_agent?.agent_card?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      battle.created_by.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  let sortedBattles = $derived.by(() => {
    const sorted = [...filteredBattles].sort((a, b) => {
      let aVal = a[sortColumn as keyof Battle];
      let bVal = b[sortColumn as keyof Battle];
      
      // Handle undefined values
      if (aVal === undefined) aVal = '';
      if (bVal === undefined) bVal = '';
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    
    return sorted;
  });

  let paginatedBattles = $derived.by(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return sortedBattles.slice(start, end);
  });

  let totalPages = $derived.by(() => Math.ceil(sortedBattles.length / pageSize));

  function handleSort(column: string) {
    if (sortColumn === column) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn = column;
      sortDirection = 'asc';
    }
    currentPage = 1; // Reset to first page when sorting
  }

  function handleSearch(value: string) {
    searchTerm = value;
    currentPage = 1; // Reset to first page when searching
  }

  function formatTimestamp(timestamp: string) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

    function getBattleResult(battle: Battle) {
    if (battle.state === 'finished') {
      if (battle.result?.winner) {
        return battle.result.winner === 'draw' ? 'Draw' : `${battle.result.winner} Victory`;
      }
      return 'Finished';
    } else if (battle.state === 'error') {
      return battle.error ? `Error: ${battle.error}` : 'Error';
    } else {
      return battle.state || 'Unknown';
    }
  }
</script>

<div>
  <div class="flex items-center py-4">
    <Input
      placeholder="Filter battles..."
      value={searchTerm}
      onchange={(e) => handleSearch(e.currentTarget.value)}
      oninput={(e) => handleSearch(e.currentTarget.value)}
      class="max-w-sm"
    />
  </div>
  
  <div class="rounded-md border">
    <Table.Root>
      <Table.Header>
        <Table.Row>
          <Table.Head 
            class="cursor-pointer select-none"
            onclick={() => handleSort('state')}
          >
            Result
            {#if sortColumn === 'state'}
              <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
            {/if}
          </Table.Head>
          <Table.Head 
            class="cursor-pointer select-none"
            onclick={() => handleSort('green_agent_id')}
          >
            Green Agent (Host)
            {#if sortColumn === 'green_agent_id'}
              <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
            {/if}
          </Table.Head>
          <Table.Head>Opponents</Table.Head>

          <Table.Head 
            class="cursor-pointer select-none"
            onclick={() => handleSort('created_at')}
          >
            Timestamp
            {#if sortColumn === 'created_at'}
              <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
            {/if}
          </Table.Head>
          <Table.Head>Actions</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {#if paginatedBattles.length > 0}
          {#each paginatedBattles as battle}
            <Table.Row>
              <Table.Cell>
                <div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                  {getBattleResult(battle)}
                </div>
              </Table.Cell>
              <Table.Cell>
                {#if battle.green_agent}
                  <AgentChip 
                    agent={{
                      identifier: battle.green_agent.register_info?.alias || battle.green_agent.agent_card?.name || 'Unknown',
                      description: battle.green_agent.agent_card?.description
                    }}
                    agent_id={battle.green_agent.agent_id || battle.green_agent.id}
                    isOnline={battle.green_agent.live || false}
                    isLoading={battle.green_agent.livenessLoading || false}
                  />
                {:else}
                  <span class="text-muted-foreground">Loading...</span>
                {/if}
              </Table.Cell>
              <Table.Cell>
                {#if battle.opponent_agents && battle.opponent_agents.length > 0}
                  <div class="w-96">
                    <Carousel.Root 
                      class="w-full"
                      opts={{
                        align: "start",
                        loop: battle.opponent_agents.length > 3,
                      }}
                    >
                      <Carousel.Content class="gap-16">
                        {#each battle.opponent_agents as agent}
                          <Carousel.Item class="basis-35/100">
                            <div class="p-4">
                              <AgentChip 
                                agent={{
                                  identifier: agent.register_info?.alias || agent.agent_card?.name || 'Unknown',
                                  description: agent.agent_card?.description
                                }} 
                                agent_id={agent.agent_id || agent.id}
                                isOnline={agent.live || false}
                                isLoading={agent.livenessLoading || false}
                              />
                            </div>
                          </Carousel.Item>
                        {/each}
                      </Carousel.Content>
                    </Carousel.Root>
                  </div>
                {:else}
                  <span class="text-muted-foreground">No opponents</span>
                {/if}
              </Table.Cell>

              <Table.Cell class="text-sm text-muted-foreground">{formatTimestamp(battle.created_at)}</Table.Cell>
              <Table.Cell>
                <BattleTableActions 
                  battleId={battle.battle_id} 
                  greenAgent={battle.green_agent}
                  opponents={battle.opponents}
                />
              </Table.Cell>
            </Table.Row>
          {/each}
        {:else}
          <Table.Row>
            <Table.Cell colspan={5} class="h-24 text-center">
              No past battles found.
            </Table.Cell>
          </Table.Row>
        {/if}
      </Table.Body>
    </Table.Root>
  </div>
  
  <div class="flex items-center justify-end space-x-2 py-4">
    <div class="flex-1 text-sm text-muted-foreground">
      Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedBattles.length)} of {sortedBattles.length} results.
    </div>
    <div class="space-x-2">
      <Button
        variant="outline"
        size="sm"
        onclick={() => currentPage = Math.max(1, currentPage - 1)}
        disabled={currentPage === 1}
      >
        Previous
      </Button>
      <span class="px-2 py-1 text-sm">
        Page {currentPage} of {totalPages}
      </span>
      <Button
        variant="outline"
        size="sm"
        onclick={() => currentPage = Math.min(totalPages, currentPage + 1)}
        disabled={currentPage === totalPages}
      >
        Next
      </Button>
    </div>
  </div>
</div> 