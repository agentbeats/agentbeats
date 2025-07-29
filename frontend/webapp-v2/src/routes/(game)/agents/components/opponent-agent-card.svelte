<script lang="ts">
  import { Card, CardContent, CardHeader } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { LineChart } from "layerchart";
  import { curveLinear } from "d3-shape";
  import * as Chart from "$lib/components/ui/chart/index.js";
  import AgentChip from "$lib/components/agent-chip.svelte";
  import TrendingUpIcon from "@lucide/svelte/icons/trending-up";
  import TrendingDownIcon from "@lucide/svelte/icons/trending-down";
  import MoveRightIcon from "@lucide/svelte/icons/move-right";
  import ShoppingCartIcon from "@lucide/svelte/icons/shopping-cart";
  import { goto } from "$app/navigation";
  import { cartStore } from '$lib/stores/cart';
  import { toast } from 'svelte-sonner';

  export let agent: any;
  export let onDelete: (agentId: string, agentName: string) => void;
</script>

<Card class="w-80 mr-8 agent-card">
  <CardHeader class="pb-3">
    <AgentChip 
      agent={{
        identifier: agent.register_info?.alias || agent.agent_card?.name || 'Unknown',
        avatar_url: agent.register_info?.avatar_url,
        description: agent.agent_card?.description
      }} 
      agent_id={agent.agent_id || agent.id}
      isOnline={agent.live || false}
    />
  </CardHeader>
  <CardContent class="pt-0 pb-3">
    {#if agent.elo?.rating}
      {@const battleHistory = agent.elo.battle_history || []}
      {@const recentBattles = battleHistory.slice(-5)}
      {@const chartData = (() => {
        const data = [];
        const baseElo = 1000;
        
        // Add placeholders for missing battles (left side)
        const missingBattles = 5 - recentBattles.length;
        for (let i = 0; i < missingBattles; i++) {
          data.push({ battle: i + 1, elo: baseElo });
        }
        
        // Add actual battle data (most recent on the right)
        recentBattles.forEach((battle: any, index: number) => {
          data.push({ 
            battle: missingBattles + index + 1, 
            elo: battle.elo_after || battle.elo_before || baseElo 
          });
        });
        
        console.log('Chart data:', data);
        return data;
      })()}
      {@const chartConfig = {
        elo: { label: "ELO Rating", color: "#6b7280" }
      }}
      {@const _ = console.log('Chart config:', chartConfig)}
      {@const recentBattlesWithElo = recentBattles.filter((battle: any) => battle.elo_after && battle.elo_before)}
      {@const trendChange = recentBattlesWithElo.length > 0 
        ? recentBattlesWithElo.reduce((total: number, battle: any) => total + (battle.elo_after - battle.elo_before), 0)
        : 0
      }
      {@const trendIcon = trendChange > 0 ? TrendingUpIcon : trendChange < 0 ? TrendingDownIcon : MoveRightIcon}
            {@const trendColor = trendChange > 0 ? "text-green-600" : trendChange < 0 ? "text-red-600" : "text-gray-600"}
      
      <Chart.Container config={chartConfig} class="min-h-[120px] w-full">
        <LineChart
          data={chartData}
          x="battle"
          series={[
            {
              key: "elo",
              label: "ELO Rating",
              color: chartConfig.elo.color,
              props: {
                strokeWidth: 3,
              },
            },
          ]}
        >
          {#snippet tooltip()}
            <Chart.Tooltip hideLabel />
          {/snippet}
        </LineChart>
      </Chart.Container>
      
      <div class="flex items-center gap-1 mt-2 text-xs {trendColor}">
        <span>
          {trendChange > 0 ? "up" : trendChange < 0 ? "down" : "no change"} by {Math.abs(trendChange)} pts in recent battles
        </span>
        <svelte:component this={trendIcon} class="w-3 h-3" />
      </div>
    {/if}
    <div class="flex gap-1 pt-6">
      <Button 
        onclick={() => {
          cartStore.addItem({
            agent: agent,
            type: 'opponent'
          });
          toast.success(`Added ${agent.register_info?.alias || agent.agent_card?.name || 'agent'} to cart as Opponent`);
        }}
        class="btn-primary"
        size="sm"
        title="Add to cart as Opponent"
        data-add-to-cart="true"
      >
        <ShoppingCartIcon class="w-4 h-4" />
      </Button>
      <Button 
        onclick={() => onDelete(agent.agent_id || agent.id, agent.register_info?.alias || 'this agent')}
        class="btn-primary"
        size="sm"
      >
        Delete
      </Button>
    </div>
  </CardContent>
</Card> 