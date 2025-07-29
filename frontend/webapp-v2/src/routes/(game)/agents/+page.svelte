<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";

  onMount(() => {
    goto('/agents/my-agents');
  });
</script>

<div class="flex items-center justify-center min-h-[50vh]">
  <div class="text-center">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
    <p class="text-gray-600">Redirecting to My Agents...</p>
  </div>
</div>
