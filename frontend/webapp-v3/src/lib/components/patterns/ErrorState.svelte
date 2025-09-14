<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import type { ErrorStateProps } from "$lib/types";

  let {
    error,
    onRetry,
    showRetry = true
  }: ErrorStateProps = $props();

  const errorMessage = typeof error === 'string' ? error : error.message || 'An error occurred';
</script>

<div class="flex flex-col items-center justify-center py-12">
  <div class="text-center">
    <h3 class="text-lg font-semibold mb-2 text-red-600">Error</h3>
    <p class="text-muted-foreground mb-4">{errorMessage}</p>
    {#if showRetry && onRetry}
      <Button onclick={onRetry} class="btn-primary">
        Try Again
      </Button>
    {/if}
  </div>
</div>