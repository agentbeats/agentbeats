<script lang="ts">
  import { useAgents, useBattles, useAuth } from "$lib/hooks";
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Spinner } from "$lib/components/ui/spinner";
  import { Button } from "$lib/components/ui/button";
  import { ScrollArea } from "$lib/components/ui/scroll-area";
  import { goto } from "$app/navigation";
  import * as Carousel from "$lib/components/ui/carousel";
  import Autoplay from "embla-carousel-autoplay";
  import BattleCard from "$lib/components/battle-card.svelte";
  import ExampleBattleCard from "$lib/components/example-battle-card.svelte";
  import AgentChip from "$lib/components/agent-chip.svelte";

  // Use the new simplified hooks
  const agentsHook = useAgents();
  const battlesHook = useBattles();
  const authHook = useAuth();
  
  let exampleBattles = $state<any[]>([]);
  let exampleBattlesLoading = $state(true);

  // Get user data from the layout
  let { data } = $props<{ data: { user: any } }>();

  $effect(() => {
    loadData();
    loadExampleBattles();
  });

  async function loadData() {
    try {
      // Load both battles and agents
      await Promise.all([
        battlesHook.loadBattles(),
        agentsHook.loadMyAgentsWithLiveness()
      ]);
      
      console.log('Dashboard loaded agents:', agentsHook.data.length);
      console.log('Dashboard loaded battles:', battlesHook.data.length);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  }

  async function loadExampleBattles() {
    try {
      exampleBattlesLoading = true;
      console.log('Loading example battles...');
      const response = await fetch('/example-battles.json');
      console.log('Response status:', response.status);
      if (!response.ok) {
        throw new Error(`Failed to load example battles: ${response.statusText}`);
      }
      const data = await response.json();
      console.log('Raw data:', data);
      exampleBattles = data.example_battles || [];
      console.log('Loaded example battles:', exampleBattles);
    } catch (error) {
      console.error('Failed to load example battles:', error);
      exampleBattles = [];
    } finally {
      exampleBattlesLoading = false;
      console.log('Example battles loading finished. Count:', exampleBattles.length);
    }
  }


</script>

<main class="flex-1 p-6">
  <div class="w-full max-w-7xl mx-auto">
    <!-- Welcome Message and Logout -->
    <div class="mb-6 flex justify-between items-center">
      <h1 class="text-xl">
        <span class="text-gray-500">Welcome, </span>
        <span class="font-bold text-black">{authHook.getUsername()}</span>
      </h1>
      <Button 
        onclick={async () => {
          await authHook.signOut();
          goto('/');
        }}
        class="btn-primary"
        size="sm"
      >
        Sign Out
      </Button>
    </div>

    <!-- Example Battles Carousel -->
    <!-- Temporarily commented out
    <Card class="mb-6">
      <CardHeader>
        <CardTitle>Example Battles</CardTitle>
        <CardDescription>Pre-configured battle scenarios for demonstration</CardDescription>
      </CardHeader>
      <CardContent>
        {#if exampleBattlesLoading}
          <div class="flex items-center justify-center py-8">
            <Spinner size="md" />
            <span class="ml-2 text-sm">Loading example battles... (Count: {exampleBattles.length})</span>
          </div>
        {:else if exampleBattles.length === 0}
          <div class="text-center py-8">
            <p class="text-muted-foreground text-sm">No example battles found</p>
            <p class="text-xs text-gray-500 mt-1">Debug: Loading state was {exampleBattlesLoading}</p>
            <Button 
              onclick={() => goto('/battles/stage-battle')}
              class="mt-2 btn-primary"
              size="sm"
            >
              Create Your Own Battle
            </Button>
          </div>
        {:else}
          <Carousel.Root 
            class="w-full max-w-6xl mx-auto"
            opts={{
              align: "start",
              loop: exampleBattles.length > 4,
            }}
            plugins={[
              Autoplay({
                delay: 6000,
              }),
            ]}
          >
            <Carousel.Content class="gap-2 md:gap-4">
              {#each exampleBattles as exampleBattle}
                <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                  <div class="p-1">
                    <ExampleBattleCard {exampleBattle} />
                  </div>
                </Carousel.Item>
              {/each}
            </Carousel.Content>
          </Carousel.Root>
        {/if}
      </CardContent>
    </Card>
    -->

    <!-- Two Cards Layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- User Info Card (Wider) -->
      <div class="lg:col-span-2">
        <Card>
          <CardHeader>
            <CardTitle>User Information</CardTitle>
            <CardDescription>Your profile and account details</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div class="flex items-center space-x-4">
                <div class="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                  <span class="text-lg font-semibold text-gray-600">{authHook.getUsername().charAt(0).toUpperCase()}</span>
                </div>
                <div>
                  <h3 class="font-medium">{authHook.getUsername()}</h3>
                  <p class="text-sm text-muted-foreground">Active User</p>
                </div>
              </div>
              
              <!-- Top Agents Section -->
              <div class="pt-4">
                <Card>
                  <CardHeader>
                    <CardTitle class="text-sm">My Agents</CardTitle>
                    <CardDescription>Your registered agents</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {#if agentsHook.isLoading}
                      <div class="flex items-center justify-center py-4">
                        <Spinner size="md" />
                        <span class="ml-2 text-sm">Loading agents...</span>
                      </div>
                    {:else if agentsHook.data.length === 0}
                      <div class="text-center py-4">
                        <p class="text-muted-foreground text-sm">No agents found</p>
                        <Button 
                          onclick={() => goto('/agents/register')}
                          class="mt-2 btn-primary"
                          size="sm"
                        >
                          Register Agent
                        </Button>
                      </div>
                    {:else}
                      <Carousel.Root 
                        class="w-full"
                        opts={{
                          align: "start",
                          loop: true,
                          dragFree: true,
                        }}
                        plugins={[
                          Autoplay({
                            delay: 8000,
                          }),
                        ]}
                      >
                        <Carousel.Content class="gap-13">
                          {#each agentsHook.data.slice(0, 6) as agent}
                            <Carousel.Item class="basis-1/4 md:basis-1/5">
                              <div class="p-3">
                                <AgentChip 
                                  agent={{
                                    identifier: agent.alias || agent.agent_card?.name || 'Unknown',
                                    avatar_url: agent.avatar_url,
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
                    {/if}
                  </CardContent>
                </Card>
              </div>
              
              <div class="pt-4">
                <Button 
                  onclick={() => goto('/agents/my-agents')}
                  class="btn-primary"
                >
                  Manage Agents
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Past Battles Card -->
      <div class="lg:col-span-1">
        <Card class="h-full">
          <CardHeader>
            <CardTitle>Past Battles</CardTitle>
            <CardDescription>Your recent battle history</CardDescription>
          </CardHeader>
          <CardContent class="h-full">
            {#if battlesHook.isLoading}
              <div class="flex items-center justify-center py-4">
                <Spinner size="md" />
                <span class="ml-2 text-sm">Loading...</span>
              </div>
            {:else if battlesHook.data.length === 0}
              <div class="text-center py-4">
                <p class="text-muted-foreground text-sm">No battles found</p>
                <Button 
                  onclick={() => goto('/battles/stage-battle')}
                  class="mt-2 btn-primary"
                  size="sm"
                >
                  Start a Battle
                </Button>
              </div>
            {:else}
              <ScrollArea class="h-[300px]">
                <div class="space-y-3 pr-4">
                  {#each battlesHook.data.slice(0, 10) as battle}
                    <div class="flex items-center justify-between p-3 border rounded-lg">
                      <div class="flex-1">
                        {#if battle.green_agent_id}
                          {#if agentsHook.data.length > 0}
                            {@const greenAgent = agentsHook.data.find(agent => agent.agent_id === battle.green_agent_id || agent.id === battle.green_agent_id)}
                            {#if greenAgent}
                              <AgentChip 
                                agent={{
                                  identifier: greenAgent.alias || greenAgent.agent_card?.name || 'Unknown',
                                  avatar_url: greenAgent?.avatar_url,
                                  description: greenAgent.agent_card?.description
                                }} 
                                agent_id={greenAgent.agent_id || greenAgent.id}
                                isOnline={greenAgent.live || false}
                                isLoading={greenAgent.livenessLoading || false}
                              />
                            {:else}
                              <p class="font-medium text-sm">Green Agent (ID: {battle.green_agent_id?.slice(0, 8)})</p>
                            {/if}
                          {:else}
                            <p class="font-medium text-sm">Green Agent (ID: {battle.green_agent_id?.slice(0, 8)})</p>
                          {/if}
                        {:else}
                          <p class="font-medium text-sm">{battle.battle_id?.slice(0, 8) || 'Unknown'}</p>
                        {/if}
                        <p class="text-xs text-muted-foreground mt-1">
                          {battle.state || 'Unknown Status'}
                        </p>
                      </div>
                      <Button 
                        onclick={() => goto(`/battles/${battle.battle_id}`)}
                        class="btn-primary"
                        size="sm"
                      >
                        View
                      </Button>
                    </div>
                  {/each}
                  {#if battlesHook.data.length > 10}
                    <Button 
                      onclick={() => goto('/battles/featured')}
                      class="w-full btn-primary"
                      size="sm"
                    >
                      View All Battles
                    </Button>
                  {/if}
                </div>
              </ScrollArea>
            {/if}
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Ongoing Battles Carousel -->
    <Card>
      <CardHeader>
        <CardTitle>Ongoing Battles</CardTitle>
        <CardDescription>Currently running and queued battles</CardDescription>
      </CardHeader>
      <CardContent>
        {#if battlesHook.isLoading}
          <div class="flex items-center justify-center py-8">
            <Spinner size="md" />
            <span class="ml-2 text-sm">Loading ongoing battles...</span>
          </div>
        {:else if battlesHook.ongoingBattles.length === 0}
          <div class="text-center py-8">
            <p class="text-muted-foreground text-sm">No ongoing battles</p>
            <Button 
              onclick={() => goto('/battles/stage-battle')}
              class="mt-2 btn-primary"
              size="sm"
            >
              Start a Battle
            </Button>
          </div>
        {:else}
          <Carousel.Root 
            class="w-full max-w-6xl mx-auto"
            opts={{
              align: "start",
              loop: battlesHook.ongoingBattles.length > 4,
            }}
            plugins={[
              Autoplay({
                delay: 5000,
              }),
            ]}
          >
            <Carousel.Content class="gap-2 md:gap-4">
              {#each battlesHook.ongoingBattles as battle}
                <Carousel.Item class="basis-1/2 md:basis-1/3 lg:basis-1/4">
                  <div class="p-1">
                    <BattleCard battle={battle} />
                  </div>
                </Carousel.Item>
              {/each}
            </Carousel.Content>

          </Carousel.Root>
        {/if}
      </CardContent>
    </Card>
  </div>
</main>
