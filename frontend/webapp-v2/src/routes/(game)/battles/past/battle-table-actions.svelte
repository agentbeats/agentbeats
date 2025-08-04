<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import { goto } from "$app/navigation";
  import SwordsIcon from "@lucide/svelte/icons/swords";
  import { cartStore } from "$lib/stores/cart";
  import { participantSlotsStore } from "$lib/stores/participant-slots";
  import { toast } from "svelte-sonner";
  import { getAgentById } from "$lib/api/agents";

  export let battleId: string;
  export let greenAgent: any;
  export let opponents: Array<{ name: string; agent_id: string }>;

  async function addToCart() {
    try {
      toast.loading('Loading agent details...', {
        position: 'top-center'
      });

      // Clear existing cart and slots
      cartStore.clearCart();
      participantSlotsStore.clearSlots();

      // Add green agent first (if we have full data)
      let fullGreenAgent = greenAgent;
      if (greenAgent && greenAgent.agent_id) {
        try {
          fullGreenAgent = await getAgentById(greenAgent.agent_id);
          cartStore.addItem({
            type: 'green',
            agent: fullGreenAgent
          });
        } catch (error) {
          console.error('Failed to load green agent details:', error);
          // Fallback to existing data
          cartStore.addItem({
            type: 'green',
            agent: greenAgent
          });
        }
      }

      // Pre-fill participant slots with opponent agents
      if (opponents && opponents.length > 0) {
        const participantSlots: Array<{agent: any; type: 'opponent'} | null> = [];
        
        for (let i = 0; i < opponents.length; i++) {
          const opponent = opponents[i];
          try {
            const fullOpponentAgent = await getAgentById(opponent.agent_id);
            participantSlots.push({
              type: 'opponent',
              agent: fullOpponentAgent
            });
          } catch (error) {
            console.error(`Failed to load opponent agent ${opponent.agent_id}:`, error);
            // Fallback to basic info
            participantSlots.push({
              type: 'opponent',
              agent: {
                agent_id: opponent.agent_id,
                register_info: { alias: opponent.name },
                agent_card: { name: opponent.name, description: 'Opponent from past battle' }
              }
            });
          }
        }
        
        // Set the participant slots
        participantSlotsStore.setSlots(participantSlots);
      }

      toast.success('Battle agents added to cart with pre-filled requirements!', {
        position: 'top-center'
      });
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('Failed to add to cart', {
        position: 'top-center'
      });
    }
  }
</script>

<div class="flex gap-2">
  <Button 
    onclick={() => goto(`/battles/${battleId}`)}
    class="btn-primary"
    size="sm"
  >
    View
  </Button>
  <Button 
    onclick={addToCart}
    class="btn-primary"
    size="sm"
    title="Add battle agents to cart"
  >
    <SwordsIcon class="w-4 h-4" />
  </Button>
</div> 