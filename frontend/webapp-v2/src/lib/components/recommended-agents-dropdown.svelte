<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import { fly, scale } from 'svelte/transition';
  import AgentChip from './agent-chip.svelte';
  import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
  import LockIcon from "@lucide/svelte/icons/lock";
  import UnlockIcon from "@lucide/svelte/icons/unlock";
  import StarIcon from "@lucide/svelte/icons/star";
  import { getMatchesForGreenAgentRole } from '$lib/api/agents';

  let { 
    greenAgentId = '',
    roleName = '',
    value = '',
    placeholder = 'Select an agent',
    label = '',
    allAgents = [],
    assignedAgents = []
  } = $props<{
    greenAgentId?: string;
    roleName?: string;
    value?: string;
    placeholder?: string;
    label?: string;
    allAgents?: Array<any>;
    assignedAgents?: Array<string>;
  }>();

  const dispatch = createEventDispatcher();

  let isOpen = $state(false);
  let roleMatches = $state<Array<any>>([]);
  let loadingMatches = $state(false);
  let selectedOption = $derived(getSelectedOption());

  // High confidence threshold for "recommended" tag
  const HIGH_CONFIDENCE_THRESHOLD = 0.85;

  function getSelectedOption() {
    if (!value) return null;
    
    // First check if it's in role matches
    const matchOption = roleMatches.find((match: any) => match.other_agent.agent_id === value);
    if (matchOption) {
      return {
        value: matchOption.other_agent.agent_id,
        label: matchOption.other_agent.alias,
        agent: allAgents.find((a: any) => a.agent_id === matchOption.other_agent.agent_id),
        confidence: matchOption.confidence_score,
        isRecommended: matchOption.confidence_score >= HIGH_CONFIDENCE_THRESHOLD
      };
    }
    
    // Fallback to all agents
    const agent = allAgents.find((a: any) => a.agent_id === value);
    if (agent) {
      return {
        value: agent.agent_id,
        label: agent.register_info?.alias || agent.agent_card?.name || 'Unknown Agent',
        agent: agent,
        confidence: 0,
        isRecommended: false
      };
    }
    
    return null;
  }

  async function loadRoleMatches() {
    if (!greenAgentId || !roleName) return;
    
    try {
      loadingMatches = true;
      roleMatches = await getMatchesForGreenAgentRole(greenAgentId, roleName);
    } catch (error) {
      console.error('Failed to load role matches:', error);
      roleMatches = [];
      // Don't show error to user - just show all agents without recommendations
    } finally {
      loadingMatches = false;
    }
  }

  function handleSelect(optionValue: string) {
    value = optionValue;
    isOpen = false;
    dispatch('change', { value: optionValue });
  }

  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.recommended-agents-dropdown')) {
      isOpen = false;
    }
  }

  function isAgentLocked(agent: any): boolean {
    return agent?.status === 'locked';
  }

  function getSortedOptions() {
    const options: Array<{
      value: string;
      label: string;
      agent: any;
      confidence: number;
      isRecommended: boolean;
      isMatch: boolean;
      disabled: boolean;
    }> = [];
    
    // Add role matches first (sorted by confidence)
    roleMatches.forEach((match: any) => {
      const agent = allAgents.find((a: any) => a.agent_id === match.other_agent.agent_id);
      if (agent) {
        const isAssignedToOtherRole = assignedAgents.includes(match.other_agent.agent_id) && value !== match.other_agent.agent_id;
        options.push({
          value: match.other_agent.agent_id,
          label: match.other_agent.alias,
          agent: agent,
          confidence: match.confidence_score,
          isRecommended: match.confidence_score >= HIGH_CONFIDENCE_THRESHOLD,
          isMatch: true,
          disabled: isAssignedToOtherRole
        });
      }
    });
    
    // Add other agents that don't have matches for this role
    allAgents.forEach((agent: any) => {
      const hasMatch = roleMatches.some((match: any) => match.other_agent.agent_id === agent.agent_id);
      if (!hasMatch) {
        const isAssignedToOtherRole = assignedAgents.includes(agent.agent_id) && value !== agent.agent_id;
        options.push({
          value: agent.agent_id,
          label: agent.register_info?.alias || agent.agent_card?.name || 'Unknown Agent',
          agent: agent,
          confidence: 0,
          isRecommended: false,
          isMatch: false,
          disabled: isAssignedToOtherRole
        });
      }
    });
    
    return options;
  }

  // Load matches when green agent or role changes
  $effect(() => {
    if (greenAgentId && roleName) {
      loadRoleMatches();
    } else {
      // Clear matches when green agent or role is not available
      roleMatches = [];
    }
  });

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<div class="recommended-agents-dropdown relative w-full">
  {#if label}
    <label class="block text-sm font-medium text-foreground mb-2">{label}</label>
  {/if}
  
  <button
    type="button"
    onclick={() => isOpen = !isOpen}
    class="w-full p-3 border border-border bg-background rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 hover:border-border hover:bg-muted flex items-center justify-between"
  >
    <div class="flex-1 text-left">
      {#if selectedOption && selectedOption.agent}
        <div class="flex items-center gap-2">
          <AgentChip 
            agent={{
              identifier: selectedOption.agent.register_info?.alias || selectedOption.agent.agent_card?.name || selectedOption.label,
              avatar_url: selectedOption.agent.register_info?.avatar_url,
              description: selectedOption.agent.agent_card?.description
            }}
            agent_id={selectedOption.value}
            isOnline={selectedOption.agent.live || false}
            isLoading={selectedOption.agent.livenessLoading || false}
          />
          {#if selectedOption.confidence > 0}
            <span class="text-xs text-muted-foreground">({Math.round(selectedOption.confidence * 100)}%)</span>
          {/if}
          {#if selectedOption.isRecommended}
            <div class="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
              <StarIcon class="w-3 h-3" />
              <span>Recommended</span>
            </div>
          {/if}
        </div>
      {:else if selectedOption}
        <span class="text-foreground">{selectedOption.label}</span>
      {:else}
        <span class="text-muted-foreground text-xs">{placeholder}</span>
      {/if}
    </div>
    <ChevronDownIcon class="w-4 h-4 text-muted-foreground ml-2 transition-transform duration-200 {isOpen ? 'rotate-180' : ''}" />
  </button>

  {#if isOpen}
    <div 
      class="absolute z-50 w-full mt-1 bg-background border border-border rounded-lg shadow-lg max-h-60 overflow-y-auto"
      transition:fly={{ y: -10, duration: 200 }}
    >
      {#if loadingMatches}
        <div class="p-3 text-center text-sm text-muted-foreground">
          Loading recommendations...
        </div>
      {:else}
        {@const sortedOptions = getSortedOptions()}
        {#each sortedOptions as option}
          {@const isLocked = option.agent && isAgentLocked(option.agent)}
          {@const isDisabled = option.disabled || isLocked}
          <button
            type="button"
            onclick={() => !isDisabled && handleSelect(option.value)}
            disabled={isDisabled}
            class="w-full p-3 text-left transition-colors duration-150 {isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} {option.value === value ? 'bg-muted border-l-2 border-border' : ''} {!option.isMatch ? 'text-muted-foreground hover:bg-muted' : 'hover:bg-muted focus:bg-muted focus:outline-none'}"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center flex-1">
                {#if option.agent}
                  <div class="mr-2">
                    {#if isLocked}
                      <LockIcon class="w-4 h-4 text-muted-foreground" />
                    {:else}
                      <UnlockIcon class="w-4 h-4 text-muted-foreground" />
                    {/if}
                  </div>
                {/if}
                <div class="flex-1 {!option.isMatch ? 'opacity-60' : ''}">
                  {#if option.agent}
                    <AgentChip
                      agent={{
                        identifier: option.agent.register_info?.alias || option.agent.agent_card?.name || option.label,
                        avatar_url: option.agent.register_info?.avatar_url,
                        description: option.agent.agent_card?.description
                      }}
                      agent_id={option.value}
                      isOnline={option.agent.live || false}
                      isLoading={option.agent.livenessLoading || false}
                    />
                  {:else}
                    <span class="{!option.isMatch ? 'text-muted-foreground' : 'text-foreground'}">{option.label}</span>
                  {/if}
                </div>
              </div>
              
              <div class="flex items-center gap-2 ml-2">
                {#if option.confidence > 0}
                  <span class="text-xs text-muted-foreground font-medium">
                    {Math.round(option.confidence * 100)}%
                  </span>
                {/if}
                {#if option.isRecommended}
                  <div class="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                    <StarIcon class="w-3 h-3" />
                    <span>Recommended</span>
                  </div>
                {:else if option.isMatch}
                  <div class="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                    <span>Match</span>
                  </div>
                {:else}
                  <div class="flex items-center gap-1 px-2 py-1 bg-muted text-muted-foreground text-xs rounded-full">
                    <span>No match</span>
                  </div>
                {/if}
              </div>
            </div>
          </button>
        {/each}
        
        {#if sortedOptions.length === 0}
          <div class="p-3 text-center text-sm text-muted-foreground">
            No agents available
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</div> 