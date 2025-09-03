<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { Spinner } from "$lib/components/ui/spinner";

  onMount(() => {
    // Redirect to ongoing battles by default
    goto("/battles/ongoing");
  });
</script>

<div class="flex items-center justify-center min-h-[400px]">
  <div class="text-center">
    <Spinner size="lg" centered />
    <p class="text-muted-foreground">Redirecting to ongoing battles...</p>
  </div>
</div> 