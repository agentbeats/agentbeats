<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import * as Popover from "$lib/components/ui/popover/index.js";
  import { cartStore } from '$lib/stores/cart';
  import { toast } from 'svelte-sonner';
  import SwordsIcon from "@lucide/svelte/icons/swords";
  import { getAgentMatches, getAllAgentsWithAsyncLiveness } from "$lib/api/agents";
  import { getAccessToken } from "$lib/auth/supabase";
  import { Spinner } from "$lib/components/ui/spinner";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { fly } from 'svelte/transition';

  const { agent, agentType = 'opponent', size = 'sm', variant = 'default' } = $props<{
    agent: any;
    agentType?: 'green' | 'opponent';
    size?: 'sm' | 'md' | 'lg';
    variant?: 'default' | 'outline';
  }>();

  let isOpen = $state(false);
  let topMatches = $state<Array<any>>([]);
  let loadingMatches = $state(false);
  let allAgents = $state<Array<any>>([]);

  async function loadTopMatches() {
    if (!agent.agent_id) {
      console.log('No agent_id found:', agent);
      return;
    }
    
    try {
      loadingMatches = true;
      console.log('Loading matches for agent:', agent.agent_id, 'type:', agentType);
      
      if (agentType === 'green') {
        // For green agents, get all matches and show top 3
        const accessToken = await getAccessToken();
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        
        if (accessToken) {
          headers['Authorization'] = `Bearer ${accessToken}`;
        }

        // First get all agents for liveness info using layered loading
        allAgents = await getAllAgentsWithAsyncLiveness((updatedAgents) => {
          // Update allAgents when liveness data is ready
          allAgents = updatedAgents;
          // Note: We don't need to update topMatches here since we already have the base match data
        });

        const res = await fetch(`/api/matches/green-agent/${agent.agent_id}`, {
          headers
        });

        if (!res.ok) {
          throw new Error('Failed to fetch green agent matches');
        }

        const matches = await res.json();
        console.log('Green agent matches from API:', matches);
        
        // Sort by confidence and take top 3
        topMatches = matches
          .sort((a: any, b: any) => b.confidence_score - a.confidence_score)
          .slice(0, 3);
      } else {
        // For opponent agents, get all green agents and check their matches with this opponent
        const accessToken = await getAccessToken();
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        
        if (accessToken) {
          headers['Authorization'] = `Bearer ${accessToken}`;
        }

        // Get all agents to find green agents using layered loading
        allAgents = await getAllAgentsWithAsyncLiveness((updatedAgents) => {
          // Update allAgents when liveness data is ready
          allAgents = updatedAgents;
          // Note: We don't need to update topMatches here since we already have the base match data
        });
        const greenAgents = allAgents.filter((a: any) => a.register_info?.is_green === true);
        
        console.log('Found green agents:', greenAgents.length);
        
        // Get matches for each green agent and find ones that match this opponent
        const allMatches: Array<any> = [];
        for (const greenAgent of greenAgents) {
          try {
            const greenMatchesRes = await fetch(`/api/matches/green-agent/${greenAgent.agent_id}`, {
              headers
            });
            
            if (greenMatchesRes.ok) {
              const greenMatches = await greenMatchesRes.json();
              // Find matches that include this opponent agent
              const opponentMatches = greenMatches.filter((match: any) => 
                match.other_agent_id === agent.agent_id
              );
              
              if (opponentMatches.length > 0) {
                // Add green agent info to the match
                opponentMatches.forEach((match: any) => {
                  allMatches.push({
                    ...match,
                    green_agent: {
                      agent_id: greenAgent.agent_id,
                      alias: greenAgent.register_info?.alias || greenAgent.agent_card?.name,
                      name: greenAgent.agent_card?.name,
                      description: greenAgent.agent_card?.description,
                      live: greenAgent.live || false
                    }
                  });
                });
              }
            }
          } catch (error) {
            console.error(`Failed to get matches for green agent ${greenAgent.agent_id}:`, error);
          }
        }
        
        console.log('Opponent agent matches:', allMatches);
        
        topMatches = allMatches
          .sort((a, b) => b.confidence_score - a.confidence_score)
          .slice(0, 3);
      }
      
      console.log('Final top matches:', topMatches);
    } catch (error) {
      console.error('Failed to load matches:', error);
      topMatches = [];
    } finally {
      loadingMatches = false;
    }
  }

  function handleAddToCart() {
    cartStore.addItem({
      agent: agent,
      type: agentType
    });
    
    const agentName = agent.register_info?.alias || agent.agent_card?.name || 'agent';
    const typeText = agentType === 'green' ? 'Green Agent' : 'Opponent';
    toast.success(`Added ${agentName} to cart as ${typeText}`);
  }

  async function handleAddMatchToCart(agentId: string) {
    try {
      // Get the full agent data
      const accessToken = await getAccessToken();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }

      const res = await fetch(`/api/agents/${agentId}`, {
        headers
      });

      if (!res.ok) {
        throw new Error('Failed to fetch agent details');
      }

      const agentData = await res.json();
      
      cartStore.addItem({
        agent: agentData,
        type: agentType === 'green' ? 'opponent' : 'green'
      });
      
      const agentName = agentData.register_info?.alias || agentData.agent_card?.name || 'agent';
      const typeText = agentType === 'green' ? 'Opponent' : 'Green Agent';
      toast.success(`Added ${agentName} to cart as ${typeText}`);
    } catch (error) {
      console.error('Failed to add agent to cart:', error);
      toast.error('Failed to add agent to cart');
    }
  }

  // Load matches when popover opens
  $effect(() => {
    console.log('Popover state changed:', isOpen);
    if (isOpen) {
      console.log('Popover opened, loading matches...');
      loadTopMatches();
    }
  });

  // Add agent to cart when popover opens (separate effect to prevent jitter)
  let hasAddedToCart = $state(false);
  $effect(() => {
    if (isOpen && !hasAddedToCart) {
      handleAddToCart();
      hasAddedToCart = true;
    } else if (!isOpen) {
      hasAddedToCart = false;
    }
  });

  const buttonClasses: Record<'sm' | 'md' | 'lg', string> = {
    sm: 'h-8 px-2 text-xs',
    md: 'h-10 px-3 text-sm',
    lg: 'h-12 px-4 text-base'
  };

  const buttonVariants: Record<'default' | 'outline', string> = {
    default: 'btn-primary',
    outline: 'btn-secondary'
  };
</script>

<Popover.Root bind:open={isOpen}>
  <Popover.Trigger>
    <Button 
      class="{buttonVariants[variant as keyof typeof buttonVariants]} {buttonClasses[size as keyof typeof buttonClasses]}"
      title="Add to battle cart and view matches"
      data-add-to-cart="true"
    >
      <SwordsIcon class="w-4 h-4" />
    </Button>
  </Popover.Trigger>
  
  <Popover.Content class="w-80" side="top" align="center" style="transition: all 0.3s ease;">
    <div class="grid gap-4" transition:fly={{ y: 10, duration: 300, delay: 50 }}>
      <div class="space-y-2">
        <h4 class="font-medium leading-none">Top Matches</h4>
      </div>
      
      <div class="grid gap-3">
        {#if loadingMatches}
          <div class="flex items-center justify-center py-4">
            <Spinner size="sm" />
            <span class="ml-2 text-sm">Loading matches...</span>
          </div>
        {:else if topMatches.length === 0}
          <div class="text-center py-4 text-sm text-muted-foreground">
            No matches found for this agent.
          </div>
        {:else}
          {#each topMatches as match}
            <div class="flex items-center gap-3 p-2 border rounded-lg">
              <div class="flex-1 min-w-0">
                <AgentChip 
                  agent={{
                    identifier: agentType === 'green' ? match.other_agent?.alias : match.green_agent?.alias,
                    avatar_url: agentType === 'green' ? match.other_agent?.avatar_url : match.green_agent?.avatar_url,
                    description: agentType === 'green' ? match.other_agent?.description : match.green_agent?.description
                  }} 
                  agent_id={agentType === 'green' ? match.other_agent_id : match.green_agent?.agent_id}
                  isOnline={true}
                />
              </div>
              <div class="text-xs text-blue-600 font-medium whitespace-nowrap">
                {Math.round(match.confidence_score * 100)}%
              </div>
              <Button 
                onclick={() => handleAddMatchToCart(agentType === 'green' ? match.other_agent_id : match.green_agent_id)}
                class="btn-primary flex-shrink-0"
                size="sm"
              >
                <SwordsIcon class="w-4 h-4" />
              </Button>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </Popover.Content>
</Popover.Root> 