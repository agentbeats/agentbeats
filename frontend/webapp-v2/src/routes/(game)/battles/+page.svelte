<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";

  onMount(() => {
    // Redirect to ongoing battles by default
    goto("/battles/ongoing");
  });
</script>

<div class="flex items-center justify-center min-h-[400px]">
  <div class="text-center">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
    <p class="text-gray-600">Redirecting to ongoing battles...</p>
  </div>
</div> 