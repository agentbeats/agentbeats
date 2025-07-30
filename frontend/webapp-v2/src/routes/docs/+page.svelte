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
    <div class="mx-auto mb-4">
      <Spinner size="lg" />
    </div>
    <p class="text-gray-600">Redirecting to Getting Started...</p>
  </div>
</div> 