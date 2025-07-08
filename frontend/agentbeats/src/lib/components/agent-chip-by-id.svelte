<script lang="ts">
import { onMount } from "svelte";
import AgentChip from "./agent-chip.svelte";
import { getAgentById } from "$lib/api/agents";

export let agentId: string;
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
  return {
    id: raw.id,
    name: raw.registerInfo?.name || raw.agentCard?.name || 'Unknown Agent',
    avatarUrl: undefined, // You can add logic for avatar if available
    type: raw.registerInfo?.meta?.type || 'unknown',
    description: raw.agentCard?.description || '',
    notFound: false,
    raw // pass the full object for debugging if needed
  };
}

onMount(async () => {
  loading = true;
  error = null;
  try {
    const raw = await getAgentById(agentId);
    agent = mapAgentData(raw);
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