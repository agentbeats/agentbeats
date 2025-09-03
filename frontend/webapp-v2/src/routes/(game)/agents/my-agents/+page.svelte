<script lang="ts">
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Carousel, CarouselContent, CarouselItem } from "$lib/components/ui/carousel";
  import * as Dialog from "$lib/components/ui/dialog/index.js";
  import GreenAgentCard from "../components/green-agent-card.svelte";
  import OpponentAgentCard from "../components/opponent-agent-card.svelte";
  import { goto } from "$app/navigation";
  import { getMyAgentsWithAsyncLiveness, deleteAgent } from "$lib/api/agents";
  import { toast } from 'svelte-sonner';
  import PlusIcon from "@lucide/svelte/icons/plus";
  import { Spinner } from "$lib/components/ui/spinner";

  let agents = $state<any[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  
  // Delete dialog state
  let showDeleteDialog = $state(false);
  let agentToDelete = $state<{ id: string; name: string } | null>(null);

  $effect(() => {
    loadMyAgents();
  });

  async function loadMyAgents() {
    try {
      loading = true;
      error = null;
      
      // Use layered loading: get basic info first, then update with liveness
      agents = await getMyAgentsWithAsyncLiveness((updatedAgents) => {
        // This callback will be called when liveness data is ready
        agents = updatedAgents;
        console.log('My agents liveness updated:', agents);
      });
      
      console.log('My agents loaded basic info:', agents);
      if (agents.length > 0) {
        console.log('First agent structure:', agents[0]);
      }
    } catch (err) {
      console.error('Failed to load agents:', err);
      error = err instanceof Error ? err.message : 'Failed to load agents';
      agents = [];
    } finally {
      loading = false;
    }
  }

  function handleDeleteAgent(agentId: string, agentName: string) {
    agentToDelete = { id: agentId, name: agentName };
    showDeleteDialog = true;
  }

  async function confirmDelete() {
    if (!agentToDelete) return;

    try {
      await deleteAgent(agentToDelete.id);
      await loadMyAgents();
      toast.success(`Agent "${agentToDelete.name}" deleted successfully`);
    } catch (err) {
      console.error('Failed to delete agent:', err);
      toast.error('Failed to delete agent. Please try again.');
    } finally {
      showDeleteDialog = false;
      agentToDelete = null;
    }
  }

  function cancelDelete() {
    showDeleteDialog = false;
    agentToDelete = null;
  }

  // Separate agents by type
  let greenAgents = $derived(agents.filter(agent => agent.register_info?.is_green === true));
  let opponentAgents = $derived(agents.filter(agent => agent.register_info?.is_green === false));
</script>

<div>
  <div class="mb-6">
    <div class="flex items-center gap-2">
      <h1 class="text-2xl font-bold">My Agents</h1>
      <Button
        onclick={() => goto('/agents/register')}
        class="h-6 w-6 p-0 btn-primary rounded"
        title="Register new agent"
      >
        +
      </Button>
    </div>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-8">
              <Spinner size="lg" />
      <span class="ml-2">Loading agents...</span>
    </div>
  {:else if error}
    <div class="flex flex-col items-center justify-center py-12">
      <div class="text-center">
        <h3 class="text-lg font-semibold mb-2 text-red-600">Error loading agents</h3>
        <p class="text-muted-foreground mb-4">{error}</p>
        <Button 
          onclick={loadMyAgents}
          class="btn-primary"
        >
          Try Again
        </Button>
      </div>
    </div>
  {:else if agents.length === 0}
    <div class="flex flex-col items-center justify-center py-12">
      <div class="text-center">
        <h3 class="text-lg font-semibold mb-2">No agents found</h3>
        <p class="text-muted-foreground mb-4">You haven't registered any agents yet.</p>
        <Button 
          onclick={() => goto('/agents/register')}
          class="btn-primary"
        >
          Register Your First Agent
        </Button>
      </div>
    </div>
  {:else}

  <!-- Green Agents Section -->
  {#if !loading && !error && greenAgents.length > 0}
    <div class="mb-8">
      <div class="mb-4">
        <h2 class="text-lg font-semibold">Green Agents (Judges/Coordinators)</h2>
        <p class="text-sm text-muted-foreground">Agents that coordinate battles and judge outcomes</p>
      </div>
      <Carousel class="w-full">
        <CarouselContent class="gap-4">
          {#each greenAgents as agent}
            <CarouselItem class="basis-80">
              <GreenAgentCard {agent} onDelete={handleDeleteAgent} showDeleteButton={true} />
            </CarouselItem>
          {/each}
        </CarouselContent>
      </Carousel>
    </div>
  {/if}

    <!-- Opponent Agents Section -->
    {#if !loading && !error && opponentAgents.length > 0}
      <div class="mb-8">
        <div class="mb-4">
          <h2 class="text-lg font-semibold">Opponent Agents (Red/Blue)</h2>
          <p class="text-sm text-muted-foreground">Agents that participate in battles as attackers or defenders</p>
        </div>
        <Carousel class="w-full">
                  <CarouselContent class="gap-4">
          {#each opponentAgents as agent}
            <CarouselItem class="basis-80">
                <OpponentAgentCard {agent} onDelete={handleDeleteAgent} showDeleteButton={true} />
              </CarouselItem>
            {/each}
          </CarouselContent>
        </Carousel>
      </div>
        {/if}
  {/if}

  <!-- Delete Confirmation Dialog -->
  <Dialog.Root bind:open={showDeleteDialog}>
    <Dialog.Portal>
      <Dialog.Overlay class="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" />
      <Dialog.Content class="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg">
        <Dialog.Header>
          <Dialog.Title class="text-lg font-semibold">Delete Agent</Dialog.Title>
          <Dialog.Description class="text-sm text-muted-foreground">
            Are you sure you want to delete "{agentToDelete?.name || 'this agent'}"? This action cannot be undone.
          </Dialog.Description>
        </Dialog.Header>
        <div class="flex justify-end space-x-2">
          <Button class="btn-primary" onclick={cancelDelete}>
            Cancel
          </Button>
          <Button class="btn-primary" onclick={confirmDelete}>
            Delete
          </Button>
        </div>
      </Dialog.Content>
    </Dialog.Portal>
  </Dialog.Root>
</div> 