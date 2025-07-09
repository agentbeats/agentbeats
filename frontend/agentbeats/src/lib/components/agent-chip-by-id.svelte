<script lang="ts">
import { onMount } from "svelte";
import AgentChip from "./agent-chip.svelte";
import { getAgentById } from "$lib/api/agents";
import { createEventDispatcher } from "svelte";

export let agentId: string;
export let modalState = undefined;
const dispatch = createEventDispatcher();
let agent: any = null;
let loading = true;
let error: string | null = null;

const fallbackAgent = {
  id: agentId,
  name: "Agent Not Found",
  avatarUrl: undefined,
  type: undefined,
  description: undefined,
  notFound: true
};

function mapAgentData(raw: any) {
  if (!raw) return fallbackAgent;
  const regInfo = raw.registerInfo || raw.register_info || {};
  const agentCard = raw.agentCard || raw.agent_card || {};
  return {
    id: raw.id,
    name: regInfo.name || agentCard.name || 'Unknown Agent',
    avatarUrl: undefined, // You can add logic for avatar if available
    type: regInfo.meta?.type || 'unknown',
    description: agentCard.description || '',
    notFound: false,
    raw // pass the full object for debugging if needed
  };
}

onMount(async () => {
  loading = true;
  error = null;
  if (!agentId) {
    agent = fallbackAgent;
    loading = false;
    return;
  }
  try {
    const raw = await getAgentById(agentId);
    agent = mapAgentData(raw);
    if (!agent || agent.notFound) {
      agent = fallbackAgent;
    }
  } catch (e) {
    error = e instanceof Error ? e.message : 'Failed to load agent';
    agent = fallbackAgent;
  } finally {
    loading = false;
  }
});
</script>

{#if loading}
  <span class="inline-block px-3 py-1 text-xs text-muted-foreground bg-muted rounded-full animate-pulse">Loading...</span>
{:else}
  <AgentChip {agent} />
{/if} 