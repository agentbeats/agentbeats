<script lang="ts">
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import { goto } from "$app/navigation";

  export let agent: {
    identifier: string;
    avatar_url?: string;
    description?: string;
    name?: string;
    alias?: string;
    participant_requirements?: Array<any>;
    agent_id?: string;
  };

  function handleCardClick() {
    if (agent.agent_id) {
      goto(`/agents/${agent.agent_id}`);
    }
  }
</script>

<div class="bg-white border rounded-2xl p-4 w-64 h-64 shadow-sm hover:shadow-md transition-all duration-300 cursor-pointer hover:-translate-y-2 hover:bg-gray-50" onclick={handleCardClick}>
  <div class="flex flex-col items-center space-y-3">
    <!-- Avatar -->
    <Avatar.Root class="h-10 w-10">
      <Avatar.Image src={agent.avatar_url} alt={agent.identifier} />
      <Avatar.Fallback class="bg-gray-200 border border-gray-300 rounded-full flex items-center justify-center text-sm font-semibold">
        {agent.identifier.charAt(0).toUpperCase()}
      </Avatar.Fallback>
    </Avatar.Root>
    
    <!-- Agent Name/Alias -->
    <div class="text-center">
      <h3 class="text-xs font-bold text-gray-900 line-clamp-1">
        {agent.name || agent.alias || agent.identifier}
      </h3>
    </div>
    
    <!-- Agent Identifier -->
    <div class="text-center">
      <p class="text-xs text-gray-500 font-mono" style="font-size: 0.6rem;">
        @{agent.identifier}
      </p>
    </div>
    
    <!-- Description -->
    <div class="text-center">
      <p class="text-xs text-gray-600 leading-relaxed line-clamp-4" style="font-size: 0.65rem;">
        {agent.description || 'No description available'}
      </p>
    </div>
    
    <!-- Participant Requirements Count -->
    <div class="text-center">
      <p class="text-xs text-gray-400">
        {agent.participant_requirements?.length || 0} competitors
      </p>
    </div>
  </div>
</div> 