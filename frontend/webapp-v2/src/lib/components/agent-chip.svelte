<script lang="ts">
  import * as HoverCard from "$lib/components/ui/hover-card/index.js";
  import * as Avatar from "$lib/components/ui/avatar/index.js";
  import { Card, CardContent } from "$lib/components/ui/card";
  import { fade, scale } from 'svelte/transition';
  import { goto } from "$app/navigation";

  let { 
    agent,
    agent_id,
    isOnline = false,
    isLoading = false,
    clickable = true,
    onDragStart = null,
    onDragOver = null,
    onDragLeave = null,
    onDrop = null,
    onDragEnd = null
  } = $props<{
    agent: {
      identifier: string;
      avatar_url?: string;
      description?: string;
    };
    agent_id: string;
    isOnline?: boolean;
    isLoading?: boolean;
    clickable?: boolean;
    onDragStart?: ((event: DragEvent) => void) | null;
    onDragOver?: ((event: DragEvent) => void) | null;
    onDragLeave?: ((event: DragEvent) => void) | null;
    onDrop?: ((event: DragEvent) => void) | null;
    onDragEnd?: ((event: DragEvent) => void) | null;
  }>();

  // Track if this chip is being dragged
  let isDragging = $state(false);

  function handleClick() {
    if (clickable) {
      goto(`/agents/${agent_id}`);
    }
  }

  function handleDragStart(event: DragEvent) {
    isDragging = true;
    if (onDragStart) {
      onDragStart(event);
    }
  }

  function handleDragEnd(event: DragEvent) {
    isDragging = false;
    if (onDragEnd) {
      onDragEnd(event);
    }
  }
</script>

<div
  draggable="true"
  ondragstart={handleDragStart}
  ondragover={onDragOver}
  ondragleave={onDragLeave}
  ondrop={onDrop}
  ondragend={handleDragEnd}
  class="inline-block"
>
  <HoverCard.Root openDelay={300} closeDelay={1000}>
    <HoverCard.Trigger 
      class="inline-flex items-center space-x-1.5 w-48 p-1 bg-background border rounded-full hover:bg-muted/50 hover:border-border hover:shadow-md transition-all duration-200 {clickable ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'}"
      onclick={handleClick}
    >
      <Avatar.Root class="h-5 w-5">
        <Avatar.Image src={agent.avatar_url} alt={agent.identifier} />
        <Avatar.Fallback class="text-xs bg-muted border border-border rounded-full flex items-center justify-center">
          {agent.identifier.charAt(0).toUpperCase()}
        </Avatar.Fallback>
      </Avatar.Root>
      <div class="flex-1 min-w-0">
        <p class="text-xs font-medium truncate">
          @{agent.identifier}
        </p>
      </div>
      <div class="flex items-center justify-center w-4 h-4 mr-1">
        {#if isLoading}
          <div class="w-2 h-2 border border-blue-500 border-t-transparent rounded-full animate-spin" title="Checking status..."></div>
        {:else}
          <div class="w-2 h-2 rounded-full {isOnline ? 'bg-green-500' : 'bg-red-500'}" title={isOnline ? 'Online' : 'Offline'}></div>
        {/if}
      </div>
    </HoverCard.Trigger>

    {#if !isDragging}
      <HoverCard.Content align="start" sideOffset={8} class="w-80 z-50 bg-background border shadow-lg rounded-xl hover:bg-muted" forceMount>
        {#snippet child({ wrapperProps, props, open })}
          {#if open}
            <div {...wrapperProps}>
              <div {...props} transition:scale={{ start: 0.95, duration: 180 }}>
                <div class="flex items-center space-x-3 mb-3">
                  <Avatar.Root>
                    <Avatar.Image src={agent.avatar_url} alt={agent.identifier} />
                    <Avatar.Fallback class="bg-muted border border-border rounded-full flex items-center justify-center">
                      {agent.identifier.charAt(0).toUpperCase()}
                    </Avatar.Fallback>
                  </Avatar.Root>
                  <div class="flex-1 min-w-0">
                    <h4 class="text-sm font-semibold truncate">@{agent.identifier}</h4>
                    <div class="flex items-center space-x-2 mt-1">
                      {#if isLoading}
                        <div class="w-2 h-2 border border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        <span class="text-xs text-blue-600">Checking status...</span>
                      {:else}
                        <div class="w-2 h-2 rounded-full {isOnline ? 'bg-green-500' : 'bg-red-500'}"></div>
                        <span class="text-xs text-muted-foreground">{isOnline ? 'Online' : 'Offline'}</span>
                      {/if}
                    </div>
                  </div>
                </div>
                <div class="w-full h-20 overflow-y-auto text-sm text-muted-foreground p-2">
                  {agent.description || 'No description available'}
                </div>
              </div>
            </div>
          {/if}
        {/snippet}
      </HoverCard.Content>
    {/if}
  </HoverCard.Root>
</div>