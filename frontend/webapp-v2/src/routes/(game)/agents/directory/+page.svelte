<script lang="ts">
  import { getAllAgentsWithAsyncLiveness } from "$lib/api/agents";
  import { Button } from "$lib/components/ui/button/index.js";
  import { Spinner } from "$lib/components/ui/spinner";
  import { Input } from "$lib/components/ui/input/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import * as Table from "$lib/components/ui/table/index.js";
  import { goto } from "$app/navigation";
  import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import * as Carousel from "$lib/components/ui/carousel";
  import Autoplay from "embla-carousel-autoplay";
  import OpponentAgentCard from "../components/opponent-agent-card.svelte";
  import GreenAgentCard from "../components/green-agent-card.svelte";
  import AddToBattleCart from "$lib/components/add-to-battle-cart.svelte";
  
  // Define the Agent type
  type Agent = {
    id: string;
    name: string;
    description: string;
    elo_rating: number;
    win_rate: number;
    battles: number;
    created_by: string;
    is_green: boolean;
    live?: boolean;
  };
  
  let rawAgents = $state<any[]>([]);
  let agents = $state<Agent[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let searchTerm = $state("");
  let currentPage = $state(1);
  let pageSize = $state(10);
  let sortColumn = $state("elo_rating");
  let sortDirection = $state("desc");

  // Computed values
  let filteredAgents = $derived.by(() => {
    if (!searchTerm) return agents;
    return agents.filter(agent => 
      agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  let sortedAgents = $derived.by(() => {
    const sorted = [...filteredAgents].sort((a, b) => {
      let aVal = a[sortColumn as keyof Agent];
      let bVal = b[sortColumn as keyof Agent];
      
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

  let paginatedAgents = $derived.by(() => {
    const start = (currentPage - 1) * pageSize;
    const end = start + pageSize;
    return sortedAgents.slice(start, end);
  });

  let totalPages = $derived.by(() => Math.ceil(sortedAgents.length / pageSize));

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

  $effect(() => {
    loadAgents();
  });

  async function loadAgents() {
    try {
      loading = true;
      error = null;
      console.log('Loading agents...');
      
      // Use layered loading: get basic info first, then update with liveness
      const apiAgents = await getAllAgentsWithAsyncLiveness((updatedAgents) => {
        // This callback will be called when liveness data is ready
        console.log('Directory agents liveness updated:', updatedAgents);
        updateAgentsData(updatedAgents);
      });
      
      console.log('Directory loaded basic agent info:', apiAgents);
      updateAgentsData(apiAgents);
    } catch (err) {
      console.error('Failed to load agents:', err);
      error = err instanceof Error ? err.message : 'Failed to load agents';
      agents = [];
      rawAgents = [];
    } finally {
      loading = false;
      console.log('Loading finished. Loading state:', loading);
    }
  }
  
  function updateAgentsData(apiAgents: any[]) {
    // Store raw agents for carousels
    rawAgents = apiAgents;
    
    // Transform the data for the table
    agents = apiAgents.map((agent: any) => ({
      id: agent.agent_id || agent.id || 'unknown',
      name: agent.register_info?.alias || agent.agent_card?.name || 'Unnamed Agent',
      description: agent.agent_card?.description || 'No description available',
      elo_rating: agent.elo?.rating || 0,
      win_rate: agent.elo?.stats?.win_rate || 0,
      battles: agent.elo?.battle_history?.length || 0,
      created_by: agent.created_by || 'Unknown',
      is_green: agent.register_info?.is_green || false,
      live: agent.live || false
    }));
    
    console.log('Updated agents data:', agents);
  }
</script>

<div class="mb-6 text-center">
  <h1 class="text-2xl font-bold">Agent Directory</h1>
  <p class="text-muted-foreground">Browse all available agents in the system</p>
</div>

{#if loading}
  <div class="flex items-center justify-center py-8">
            <Spinner size="lg" />
    <span class="ml-2">Loading agents...</span>
  </div>
{/if}

{#if error}
  <div class="flex flex-col items-center justify-center py-4 mb-4">
    <div class="text-center">
      <h3 class="text-lg font-semibold mb-2 text-red-600">Error loading agents</h3>
      <p class="text-muted-foreground mb-4">{error}</p>
      <Button onclick={loadAgents} class="btn-primary">
        Try Again
      </Button>
    </div>
  </div>
{/if}

            <!-- Trending Green Agents Carousel -->
            {#if !loading && !error && rawAgents.length > 0}
              <div class="mb-8">
                <div class="mb-4">
                  <h2 class="text-lg font-semibold">Trending Green Agents</h2>
                  <p class="text-sm text-muted-foreground">Top performing green agents in the system</p>
                </div>
                <Carousel.Root 
                  class="w-full"
                  opts={{
                    align: "start",
                    loop: false,
                  }}
                  plugins={[
                    Autoplay({
                      delay: 6000,
                    }),
                  ]}
                >
                  <Carousel.Content class="gap-4">
                    {#each rawAgents.filter(agent => agent.register_info?.is_green === true).slice(0, 8) as agent}
                      <Carousel.Item class="basis-80">
                        <GreenAgentCard
                          agent={agent}
                          onDelete={() => {}}
                        />
                      </Carousel.Item>
                    {/each}
                  </Carousel.Content>
                </Carousel.Root>
              </div>
            {/if}

            <!-- Trending Opponent Agents Carousel -->
            {#if !loading && !error && rawAgents.length > 0}
              <div class="mb-8">
                <div class="mb-4">
                  <h2 class="text-lg font-semibold">Trending Opponent Agents</h2>
                  <p class="text-sm text-muted-foreground">Top performing opponent agents in the system</p>
                </div>
                <Carousel.Root 
                  class="w-full"
                  opts={{
                    align: "start",
                    loop: false,
                  }}
                  plugins={[
                    Autoplay({
                      delay: 6000,
                    }),
                  ]}
                >
                  <Carousel.Content class="gap-4">
                    {#each rawAgents.filter(agent => agent.register_info?.is_green === false).slice(0, 8) as agent}
                      <Carousel.Item class="basis-80">
                        <OpponentAgentCard
                          agent={agent}
                          onDelete={() => {}}
                        />
                      </Carousel.Item>
                    {/each}
                  </Carousel.Content>
                </Carousel.Root>
              </div>
            {/if}

{#if !loading}
  <div>
    <div class="mb-4">
      <h2 class="text-lg font-semibold">All Agents</h2>
      <p class="text-sm text-muted-foreground">Browse and search all agents in the system</p>
    </div>
    <div class="flex items-center py-4">
      <Input
        placeholder="Filter agents..."
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
              onclick={() => handleSort('name')}
            >
              Agent
              {#if sortColumn === 'name'}
                <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
              {/if}
            </Table.Head>
            <Table.Head 
              class="text-right cursor-pointer select-none"
              onclick={() => handleSort('elo_rating')}
            >
              ELO Rating
              {#if sortColumn === 'elo_rating'}
                <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
              {/if}
            </Table.Head>
            <Table.Head 
              class="text-right cursor-pointer select-none"
              onclick={() => handleSort('win_rate')}
            >
              Win Rate
              {#if sortColumn === 'win_rate'}
                <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
              {/if}
            </Table.Head>
            <Table.Head 
              class="text-right cursor-pointer select-none"
              onclick={() => handleSort('battles')}
            >
              Battles
              {#if sortColumn === 'battles'}
                <span class="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
              {/if}
            </Table.Head>

            <Table.Head>Type</Table.Head>
            <Table.Head>Actions</Table.Head>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {#if paginatedAgents.length > 0}
            {#each paginatedAgents as agent}
              <Table.Row>
                <Table.Cell>
                  <AgentChip 
                    agent={{
                      identifier: agent.name,
                      description: agent.description
                    }}
                    agent_id={agent.id}
                    isOnline={agent.live || false}
                  />
                </Table.Cell>
                <Table.Cell class="text-right font-medium">{agent.elo_rating}</Table.Cell>
                <Table.Cell class="text-right">{(agent.win_rate * 100).toFixed(1)}%</Table.Cell>
                <Table.Cell class="text-right">{agent.battles}</Table.Cell>

                <Table.Cell>
                  <div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground">
                    {agent.is_green ? 'Green' : 'Opponent'}
                  </div>
                </Table.Cell>
                <Table.Cell>
                  <div class="flex gap-2">
                    <AddToBattleCart 
                      agent={rawAgents.find(rawAgent => (rawAgent.agent_id || rawAgent.id) === agent.id)} 
                      agentType={agent.is_green ? 'green' : 'opponent'} 
                      size="sm" 
                    />
                  </div>
                </Table.Cell>
              </Table.Row>
            {/each}
          {:else}
            <Table.Row>
              <Table.Cell class="h-24 text-center">
                No results.
              </Table.Cell>
            </Table.Row>
          {/if}
        </Table.Body>
      </Table.Root>
    </div>
    
    <div class="flex items-center justify-end space-x-2 py-4">
      <div class="flex-1 text-sm text-muted-foreground">
        Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedAgents.length)} of {sortedAgents.length} results.
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
{/if}