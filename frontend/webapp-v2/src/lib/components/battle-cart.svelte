<script lang="ts">
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { Button } from "$lib/components/ui/button/index.js";
  import { ScrollArea } from "$lib/components/ui/scroll-area/index.js";
  import AgentChip from './agent-chip.svelte';
  import SwordsIcon from "@lucide/svelte/icons/swords";
  import XIcon from "@lucide/svelte/icons/x";
  import { goto } from "$app/navigation";
  import { cartStore } from '$lib/stores/cart';
  import { participantSlotsStore } from '$lib/stores/participant-slots';
  import { toast } from 'svelte-sonner';
  import { supabase } from '$lib/auth/supabase';

  let isOpen = $state(false);
  let cartItems = $state<Array<{agent: any; type: 'green' | 'opponent'}>>([]);
  
  // Drag and drop state
  let draggedAgent = $state<{agent: any; type: 'opponent'} | null>(null);
  let draggedOverIndex = $state<number | null>(null);
  let draggedOverSlot = $state<number | null>(null);

  // Participant slots for green agent - dynamic based on requirements
  let participantSlots = $state<Array<{agent: any; type: 'opponent'} | null>>([]);
  
  // Cart count includes both cart items and participant slots
  let cartCount = $derived(cartItems.length + participantSlots.filter(slot => slot !== null).length);

  // Computed values
  let greenAgent = $derived(cartItems.find(item => item.type === 'green'));
  let opponentAgents = $derived(cartItems.filter(item => item.type === 'opponent'));
  
  // Dynamic participant requirements based on green agent
  let participantRequirements = $state<Array<{role?: string; [key: string]: any}>>([]);

  // Subscribe to cart store
  let previousGreenAgentId: string | null = null;
  
  onMount(() => {
    const unsubscribeCart = cartStore.subscribe(items => {
      cartItems = items;
      
      // Check if green agent changed
      const currentGreenAgent = items.find(item => item.type === 'green');
      const currentGreenAgentId = currentGreenAgent?.agent.agent_id || currentGreenAgent?.agent.id;
      
      // If green agent changed and we had participants, return them to cart
      if (previousGreenAgentId && previousGreenAgentId !== currentGreenAgentId) {
        // Return all participants back to cart
        participantSlots.forEach(slot => {
          if (slot) {
            cartStore.addItem(slot);
          }
        });
        participantSlots = [];
      }
      
      previousGreenAgentId = currentGreenAgentId;
      
      // Update participant requirements and slots when green agent changes
      if (greenAgent?.agent?.register_info?.participant_requirements) {
        participantRequirements = greenAgent.agent.register_info.participant_requirements as Array<{role?: string; [key: string]: any}>;
        // Initialize slots based on requirements
        if (participantSlots.length !== participantRequirements.length) {
          participantSlots = new Array(participantRequirements.length).fill(null);
        }
      } else {
        participantRequirements = [];
        participantSlots = [];
      }
    });

    const unsubscribeSlots = participantSlotsStore.subscribe(slots => {
      participantSlots = slots;
    });

    return () => {
      unsubscribeCart();
      unsubscribeSlots();
    };
  });

  function toggleCart() {
    isOpen = !isOpen;
  }

  function removeFromCart(index: number) {
    cartStore.removeItem(index);
    // Reset drag state when removing from cart
    draggedAgent = null;
    draggedOverIndex = null;
    draggedOverSlot = null;
  }

  function clearCart() {
    cartStore.clearCart();
    participantSlots = [];
    // Reset all drag state
    draggedAgent = null;
    draggedOverIndex = null;
    draggedOverSlot = null;
  }

  function handleDragStart(event: DragEvent, agent: any) {
    draggedAgent = { agent, type: 'opponent' };
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', 'agent');
    }
  }

  function handleDragOver(event: DragEvent, index: number) {
    event.preventDefault();
    if (draggedAgent !== null) {
      draggedOverIndex = index;
    }
  }

  function handleDragLeave() {
    draggedOverIndex = null;
    draggedOverSlot = null;
  }

  function handleDrop(event: DragEvent, index: number) {
    event.preventDefault();
    if (draggedAgent !== null) {
      // Reorder the items
      const newItems = [...cartItems];
      const draggedIndex = newItems.findIndex(item => 
        item.agent.agent_id === draggedAgent!.agent.agent_id || 
        item.agent.id === draggedAgent!.agent.id
      );
      if (draggedIndex !== -1 && draggedIndex !== index) {
        const [draggedItem] = newItems.splice(draggedIndex, 1);
        newItems.splice(index, 0, draggedItem);
        
        // Update the store
        cartStore.reorderItems(newItems);
      }
    }
    draggedAgent = null;
    draggedOverIndex = null;
  }

  function handleDragEnd() {
    draggedAgent = null;
    draggedOverIndex = null;
    draggedOverSlot = null;
  }

  function handleParticipantDragOver(event: DragEvent, slotIndex: number) {
    event.preventDefault();
    draggedOverSlot = slotIndex;
  }

  function handleParticipantDrop(event: DragEvent, slotIndex: number) {
    event.preventDefault();
    if (draggedAgent !== null && draggedAgent.type === 'opponent') {
      // Move opponent agent to participant slot
      participantSlots[slotIndex] = { agent: draggedAgent.agent, type: 'opponent' };
      
      // Remove from cart by finding the agent (but only if it's an opponent, not the green agent)
      const cartIndex = cartItems.findIndex(item => 
        item.type === 'opponent' && 
        (item.agent.agent_id === draggedAgent!.agent.agent_id || 
         item.agent.id === draggedAgent!.agent.id)
      );
      if (cartIndex !== -1) {
        cartStore.removeItem(cartIndex);
      }
    }
    // Reset all drag state
    draggedOverSlot = null;
    draggedAgent = null;
    draggedOverIndex = null;
  }

  function handleParticipantDragLeave() {
    draggedOverSlot = null;
  }

  function removeParticipant(slotIndex: number) {
    if (participantSlots[slotIndex]) {
      // Add back to cart
      cartStore.addItem(participantSlots[slotIndex]!);
      participantSlots[slotIndex] = null;
      // Reset drag state when removing participants
      draggedAgent = null;
      draggedOverIndex = null;
      draggedOverSlot = null;
    }
  }

  async function goToBattle() {
    // Check if there's a green agent
    if (!greenAgent) {
      toast.error('Please add a green agent to start a battle');
      return;
    }
    
    // Check if all participant requirements are filled
    const filledSlots = participantSlots.filter(slot => slot !== null);
    const totalRequirements = participantRequirements.length;
    
    if (filledSlots.length === 0) {
      toast.error('Please add at least one opponent agent to start a battle');
      return;
    }
    
    if (filledSlots.length < totalRequirements) {
      const missingCount = totalRequirements - filledSlots.length;
      toast.error(`Please fill all participant requirements. Missing ${missingCount} opponent${missingCount > 1 ? 's' : ''}.`);
      return;
    }
    
    // Build opponents array with { name, agent_id } using participant requirements
    const opponents = participantRequirements
      .map((req, index) => {
        const slot = filledSlots[index];
        return slot ? { name: req.role || req.name || `participant_${index}`, agent_id: slot.agent.agent_id || slot.agent.id } : null;
      })
      .filter(opponent => opponent !== null);

    console.log('Sending battle request to backend:', {
      green_agent_id: greenAgent.agent.agent_id || greenAgent.agent.id,
      opponents
    });

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token;

      const response = await fetch('/api/battles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          green_agent_id: greenAgent.agent.agent_id || greenAgent.agent.id,
          opponents,
          created_by: session?.user?.email || 'Unknown User'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start battle');
      }

      const result = await response.json();
      
      toast.success('Battle started successfully!', {
        position: 'top-center'
      });
      
      // Clear the cart and participant slots after successful battle creation
      cartStore.clearCart();
      participantSlots = [];
      participantRequirements = [];
      
      // Redirect to the specific battle page
      setTimeout(() => {
        goto(`/battles/${result.battle_id}`);
      }, 1500);
      
    } catch (error) {
      console.error('Error starting battle:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to start battle', {
        position: 'top-center'
      });
    }
  }

  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    // Don't close if clicking on agent cards or buttons that add to cart
    if (target.closest('.battle-cart') || 
        target.closest('[data-add-to-cart]') || 
        target.closest('.agent-card') ||
        target.closest('.btn-primary')) {
      return;
    }
    isOpen = false;
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<div class="battle-cart fixed bottom-8 right-8 z-50">
  <!-- Cart Toggle Button -->
  <Button
    onclick={toggleCart}
    class="relative h-16 w-16 rounded-full btn-primary shadow-lg hover:shadow-xl transition-all duration-200"
    title="Battle Cart"
  >
    <SwordsIcon class="w-8 h-8" />
    {#if cartCount > 0}
      <div class="absolute -top-1 -right-1 bg-white text-black text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold border border-gray-300">
        {cartCount}
      </div>
    {/if}
  </Button>

  <!-- Cart Popup -->
  {#if isOpen}
    <div 
      class="absolute bottom-20 right-0 w-[500px] h-[700px] bg-white border border-gray-200 rounded-lg shadow-xl flex flex-col"
      transition:fly={{ y: 10, duration: 200 }}
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b flex-shrink-0">
        <h3 class="text-lg font-semibold">Battle Cart</h3>
        <Button
          onclick={toggleCart}
          variant="ghost"
          size="sm"
          class="h-6 w-6 p-0"
        >
          <XIcon class="w-4 h-4" />
        </Button>
      </div>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto p-4">
        {#if cartItems.length === 0}
          <div class="text-center py-8 text-muted-foreground">
            <SwordsIcon class="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p class="text-sm">Your battle cart is empty</p>
            <p class="text-xs">Add agents to start a battle</p>
          </div>
        {:else}
          <!-- Green Agent Section -->
          {#if greenAgent}
            <div class="mb-6">
              <h3 class="text-lg font-semibold mb-3">Green Agent (Coordinator)</h3>
              <div class="bg-gray-50 border-2 border-gray-200 rounded-lg p-4">
                <AgentChip
                  agent={{
                    identifier: greenAgent.agent.register_info?.alias || greenAgent.agent.agent_card?.name || 'Unknown Agent',
                    avatar_url: greenAgent.agent.register_info?.avatar_url,
                    description: greenAgent.agent.agent_card?.description
                  }}
                  agent_id={greenAgent.agent.agent_id || greenAgent.agent.id}
                  isOnline={greenAgent.agent.live || false}
                />
                
                <!-- Participant Requirements -->
                <div class="mt-4">
                  <h4 class="text-sm font-medium text-gray-700 mb-2">
                    Participant Requirements ({participantRequirements.length})
                  </h4>
                  {#if participantRequirements.length > 0}
                    <div class="space-y-2">
                      {#each participantRequirements as requirement, index}
                        <div 
                          class="h-20 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 transition-all duration-200 {participantSlots[index] ? 'border-gray-400 bg-gray-100' : 'hover:border-gray-400'} {draggedOverSlot === index && draggedAgent !== null ? 'border-blue-400 bg-blue-50' : ''}"
                          ondragover={(e) => handleParticipantDragOver(e, index)}
                          ondrop={(e) => handleParticipantDrop(e, index)}
                          ondragleave={handleParticipantDragLeave}
                        >
                          {#if participantSlots[index]}
                            <div class="flex items-center space-x-2">
                              <div class="pointer-events-none">
                                <AgentChip
                                  agent={{
                                    identifier: participantSlots[index]!.agent.register_info?.alias || participantSlots[index]!.agent.agent_card?.name || 'Unknown Agent',
                                    avatar_url: participantSlots[index]!.agent.register_info?.avatar_url,
                                    description: participantSlots[index]!.agent.agent_card?.description
                                  }}
                                  agent_id={participantSlots[index]!.agent.agent_id || participantSlots[index]!.agent.id}
                                  isOnline={participantSlots[index]!.agent.live || false}
                                />
                              </div>
                                                              <Button
                                  onclick={(e) => {
                                    e.stopPropagation();
                                    removeParticipant(index);
                                  }}
                                  variant="ghost"
                                  size="sm"
                                  class="h-6 w-6 p-0"
                                >
                                  <XIcon class="w-3 h-3" />
                                </Button>
                            </div>
                          {:else}
                            <div class="text-center">
                              <span class="text-xs text-gray-500 block">Drop opponent here</span>
                              <span class="text-xs text-gray-400 block">{requirement.role || 'Participant'}</span>
                            </div>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {:else}
                    <div class="text-center py-4 text-gray-500">
                      <span class="text-sm">No participant requirements defined</span>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/if}

          <!-- Available Opponents -->
          {#if opponentAgents.length > 0}
            <div class="flex-1 min-h-0">
              <h3 class="text-sm font-medium text-gray-700 mb-2">Available Opponents</h3>
              <ScrollArea class="h-full">
                <div class="space-y-2 pr-4">
                  {#each opponentAgents as item, index}
                    <div 
                      class="flex items-center justify-between p-2 border rounded-lg bg-gray-50 transition-all duration-200 cursor-grab active:cursor-grabbing {draggedAgent && (draggedAgent.agent.agent_id === item.agent.agent_id || draggedAgent.agent.id === item.agent.id) ? 'opacity-50 scale-95' : ''}"
                      draggable="true"
                      ondragstart={(e) => handleDragStart(e, item.agent)}
                      ondragend={handleDragEnd}
                    >
                      <div class="flex-1">
                        <AgentChip
                          agent={{
                            identifier: item.agent.register_info?.alias || item.agent.agent_card?.name || 'Unknown Agent',
                            avatar_url: item.agent.register_info?.avatar_url,
                            description: item.agent.agent_card?.description
                          }}
                          agent_id={item.agent.agent_id || item.agent.id}
                          isOnline={item.agent.live || false}
                        />
                      </div>
                                              <Button
                          onclick={(e) => {
                            e.stopPropagation();
                            removeFromCart(index);
                          }}
                          variant="ghost"
                          size="sm"
                          class="h-6 w-6 p-0 ml-2"
                        >
                          <XIcon class="w-3 h-3" />
                        </Button>
                    </div>
                  {/each}
                </div>
              </ScrollArea>
            </div>
          {/if}
        {/if}
      </div>

      <!-- Fixed Buttons at Bottom -->
      {#if cartItems.length > 0}
        <div class="p-4 border-t bg-white flex-shrink-0">
          <div class="flex gap-2">
            <Button
              onclick={clearCart}
              class="btn-primary flex-1"
              size="sm"
            >
              Clear Cart
            </Button>
            <Button
              onclick={goToBattle}
              class="btn-primary flex-1"
              size="sm"
              disabled={!greenAgent || participantSlots.filter(slot => slot).length === 0}
            >
              Start Battle
            </Button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div> 