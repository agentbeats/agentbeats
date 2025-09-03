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
    <Spinner size="lg" centered />
    <p class="text-muted-foreground">Redirecting to My Agents...</p>
  </div>
</div>
