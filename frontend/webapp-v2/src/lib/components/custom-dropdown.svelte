<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { onMount } from 'svelte';
  import { fly, scale } from 'svelte/transition';
  import AgentChip from './agent-chip.svelte';
  import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
  import LockIcon from "@lucide/svelte/icons/lock";
  import UnlockIcon from "@lucide/svelte/icons/unlock";

  let { 
    options = [],
    value = '',
    placeholder = 'Select an option',
    label = ''
  } = $props<{
    options?: Array<{
      value: string;
      label: string;
      agent?: any;
      disabled?: boolean;
    }>;
    value?: string;
    placeholder?: string;
    label?: string;
  }>();

  const dispatch = createEventDispatcher();

  let isOpen = $state(false);
  let selectedOption = $derived(options.find((opt: any) => opt.value === value));

  function handleSelect(optionValue: string) {
    value = optionValue;
    isOpen = false;
    dispatch('change', { value: optionValue });
  }

  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.custom-dropdown')) {
      isOpen = false;
    }
  }

  function isAgentLocked(agent: any): boolean {
    return agent?.status === 'locked';
  }

  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<div class="custom-dropdown relative w-full">
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
      {#each options as option}
        {@const isLocked = option.agent && isAgentLocked(option.agent)}
        {@const isDisabled = option.disabled || isLocked}
        <button
          type="button"
          onclick={() => !isDisabled && handleSelect(option.value)}
          disabled={isDisabled}
          class="w-full p-2 text-left hover:bg-muted focus:bg-muted focus:outline-none transition-colors duration-150 {isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} {option.value === value ? 'bg-muted border-l-2 border-border' : ''}"
        >
          <div class="flex items-center">
            {#if option.agent}
              <div class="mr-2">
                {#if isLocked}
                  <LockIcon class="w-4 h-4 text-muted-foreground" />
                {:else}
                  <UnlockIcon class="w-4 h-4 text-muted-foreground" />
                {/if}
              </div>
            {/if}
            <div class="flex-1">
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
                <span class="text-foreground">{option.label}</span>
              {/if}
            </div>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div> 