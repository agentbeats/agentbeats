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
      <div class="absolute -top-1 -right-1 bg-background text-foreground text-xs rounded-full h-5 w-5 flex items-center justify-center font-bold border border-border">
        {cartCount}
      </div>
    {/if}
  </Button>

  <!-- Cart Popup -->
  {#if isOpen}
    <div 
      class="absolute bottom-20 right-0 w-[500px] h-[700px] bg-background border border-border rounded-lg shadow-xl flex flex-col"
      transition:fly={{ y: 10, duration: 200 }}
    >
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-border">
        <h3 class="text-lg font-semibold">Battle Cart</h3>
        <button 
          onclick={toggleCart}
          class="text-muted-foreground hover:text-foreground transition-colors"
        >
          <XIcon class="h-5 w-5" />
        </button>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Green Agent Section -->
        <div class="bg-muted border-2 border-border rounded-lg p-4">
          <h4 class="text-sm font-medium mb-2">Green Agent (Coordinator)</h4>
          {#if greenAgent}
            <div class="flex items-center justify-between">
              <span class="text-sm">{greenAgent.agent.register_info?.alias || greenAgent.agent.agent_card?.name || 'Unknown Agent'}</span>
              <button 
                onclick={() => removeFromCart(cartItems.findIndex(item => item.agent.agent_id === greenAgent.agent.agent_id || item.agent.id === greenAgent.agent.id))}
                class="text-destructive hover:text-destructive/80 text-sm"
              >
                Remove
              </button>
            </div>
          {:else}
            <div 
              class="h-20 border-2 border-dashed border-border rounded-lg flex items-center justify-center bg-muted transition-all duration-200 {participantSlots[0] ? 'border-muted-foreground bg-muted/50' : 'hover:border-muted-foreground'} {draggedOverSlot === 0 && draggedAgent !== null ? 'border-primary bg-primary/10' : ''}"
              onclick={() => handleParticipantDrop(new DragEvent('dragover'), 0)}
              onmouseenter={() => handleParticipantDragOver(new DragEvent('dragover'), 0)}
              onmouseleave={() => handleParticipantDragLeave()}
              ondragover={(e) => e.preventDefault()}
              ondrop={(e) => handleParticipantDrop(e, 0)}
            >
              <span class="text-xs text-muted-foreground block">Drop green agent here</span>
            </div>
          {/if}
        </div>

        <!-- Opponent Slots -->
        {#each participantSlots as slot, index}
          {#if index > 0}
            <div class="bg-muted border-2 border-border rounded-lg p-4">
              <h4 class="text-sm font-medium mb-2">Opponent {index}</h4>
              {#if slot}
                <div class="flex items-center justify-between">
                  <span class="text-sm">{slot.agent.register_info?.alias || slot.agent.agent_card?.name || 'Unknown Agent'}</span>
                  <button 
                    onclick={() => removeParticipant(index)}
                    class="text-destructive hover:text-destructive/80 text-sm"
                  >
                    Remove
                  </button>
                </div>
              {:else}
                <div 
                  class="h-20 border-2 border-dashed border-border rounded-lg flex items-center justify-center bg-muted transition-all duration-200 {participantSlots[index] ? 'border-muted-foreground bg-muted/50' : 'hover:border-muted-foreground'} {draggedOverSlot === index && draggedAgent !== null ? 'border-primary bg-primary/10' : ''}"
                  onclick={() => handleParticipantDrop(new DragEvent('dragover'), index)}
                  onmouseenter={() => handleParticipantDragOver(new DragEvent('dragover'), index)}
                  onmouseleave={() => handleParticipantDragLeave()}
                  ondragover={(e) => e.preventDefault()}
                  ondrop={(e) => handleParticipantDrop(e, index)}
                >
                  <span class="text-xs text-muted-foreground block">Drop opponent here</span>
                  <span class="text-xs text-muted-foreground/70 block">{participantRequirements[index]?.role || 'Participant'}</span>
                </div>
              {/if}
            </div>
          {/if}
        {/each}

        <!-- No Items Message -->
        {#if cartItems.length === 0 && participantSlots.filter(slot => slot).length === 0}
          <div class="text-center py-4 text-muted-foreground">
            <p>No agents in cart. Drag agents here to start building your battle.</p>
          </div>
        {/if}
      </div>

      <!-- Available Opponents Section -->
      <div class="border-t border-border p-4">
        <h3 class="text-sm font-medium mb-2">Available Opponents</h3>
        <div class="space-y-2 max-h-32 overflow-y-auto">
          {#each opponentAgents as item, index}
            <div 
              class="flex items-center justify-between p-2 border rounded-lg bg-muted transition-all duration-200 cursor-grab active:cursor-grabbing {draggedAgent && (draggedAgent.agent.agent_id === item.agent.agent_id || draggedAgent.agent.id === item.agent.id) ? 'opacity-50' : 'hover:bg-muted/80'}"
              draggable="true"
              ondragstart={(e) => handleDragStart(e, item.agent)}
              ondragend={() => handleDragEnd()}
            >
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-red-500"></div>
                <span class="text-sm">{item.agent.register_info?.alias || item.agent.agent_card?.name || 'Unknown Agent'}</span>
              </div>
              <button 
                onclick={() => removeFromCart(index)}
                class="text-primary hover:text-primary/80 text-sm"
              >
                Add
              </button>
            </div>
          {/each}
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t bg-background flex-shrink-0">
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
    </div>
  {/if}
</div> 