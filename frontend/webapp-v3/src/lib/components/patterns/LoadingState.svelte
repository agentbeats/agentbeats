<script lang="ts">
  import { Spinner } from "$lib/components/ui/spinner";
  import type { LoadingStateProps } from "$lib/types";

  let {
    size = 'md',
    message = 'Loading...',
    centered = false
  }: LoadingStateProps = $props();
</script>

<div class="flex items-center justify-center {centered ? 'min-h-[50vh]' : 'py-8'}">
  <div class="text-center">
    <Spinner {size} />
    <span class="ml-2 text-sm text-muted-foreground">{message}</span>
  </div>
</div>