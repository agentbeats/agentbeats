<script lang="ts">
  import AgentChip from "./agent-chip.svelte";
  
  export let data: any;
</script>

<div class="w-full h-full flex items-center justify-center">
  <AgentChip 
    agent={data.agent}
    agent_id={data.agent_id}
    clickable={false}
  />
</div> 