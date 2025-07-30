<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { Spinner } from "$lib/components/ui/spinner";

  onMount(() => {
    goto('/agents/my-agents');
  });
</script>

<div class="flex items-center justify-center min-h-[50vh]">
  <div class="text-center">
    <div class="mx-auto mb-4">
      <Spinner size="lg" />
    </div>
    <p class="text-gray-600">Redirecting to My Agents...</p>
  </div>
</div>
