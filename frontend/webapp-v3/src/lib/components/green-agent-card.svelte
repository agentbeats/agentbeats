<script lang="ts">
  import { Card, CardContent, CardHeader } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import AddToBattleCart from "$lib/components/add-to-battle-cart.svelte";
  import { useBattles } from '$lib/hooks';

  export let agent: any;
  export let onDelete: (agentId: string, agentName: string) => void;
  export let showDeleteButton: boolean = false;

  let battleCount = 0;
  let loadingBattles = true;

  const battles = useBattles();

  onMount(async () => {
    try {
      const agentBattles = await battles.getAgentBattlesLast24Hours(agent.agent_id || agent.id);
      battleCount = agentBattles.length;
    } catch (error) {
      console.error('Failed to load battle count:', error);
      battleCount = 0;
    } finally {
      loadingBattles = false;
    }
  });
</script>

<Card class="w-80 mr-8 agent-card">
  <CardHeader class="pb-3">
    <AgentChip 
      agent={{
        identifier: agent.alias || agent.alias || agent.agent_card?.name || 'Unknown',
        avatar_url: agent?.avatar_url,
        description: agent.agent_card?.description
      }} 
      agent_id={agent.agent_id || agent.id}
      isOnline={agent.live || false}
      isLoading={agent.livenessLoading || false}
    />
  </CardHeader>
  <CardContent class="pt-0 pb-3">
    <!-- Battle count for last 24 hours -->
    <div class="text-sm text-muted-foreground mb-4">
      {loadingBattles ? 'Loading...' : `${battleCount} battles in the past 24 hours`}
    </div>
    
    <div class="flex gap-1 pt-6">
      <AddToBattleCart {agent} agentType="green" size="sm" />
      {#if showDeleteButton}
        <Button 
          onclick={() => onDelete(agent.agent_id || agent.id, agent.alias || 'this agent')}
          class="btn-primary"
          size="sm"
        >
          Delete
        </Button>
      {/if}
    </div>
  </CardContent>
</Card>