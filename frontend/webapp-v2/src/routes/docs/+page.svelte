<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Spinner } from "$lib/components/ui/spinner";

  onMount(() => {
    goto('/docs/getting-started/quick-start');
  });
</script>

<div class="flex items-center justify-center min-h-screen">
  <div class="text-center">
    <Spinner size="lg" centered />
    <p class="text-muted-foreground">Redirecting to Getting Started...</p>
  </div>
</div> 