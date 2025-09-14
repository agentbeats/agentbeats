<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import type { EmptyStateProps } from "$lib/types";

  let {
    title,
    description,
    actionLabel,
    onAction,
    icon
  }: EmptyStateProps = $props();
</script>

<div class="flex flex-col items-center justify-center py-12">
  <div class="text-center">
    {#if icon}
      <div class="mb-4 text-4xl text-muted-foreground">
        <svelte:component this={icon} />
      </div>
    {/if}
    <h3 class="text-lg font-semibold mb-2">{title}</h3>
    {#if description}
      <p class="text-muted-foreground mb-4">{description}</p>
    {/if}
    {#if actionLabel && onAction}
      <Button onclick={onAction} class="btn-primary">
        {actionLabel}
      </Button>
    {/if}
  </div>
</div>