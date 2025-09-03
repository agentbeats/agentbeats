<script lang="ts">
  let { data } = $props<{ data: { spec: any } }>();
</script>

<div class="max-w-none">
  
  {#if data.spec}
    <div class="bg-card text-card-foreground rounded-lg p-6 overflow-auto">
      <pre class="text-sm whitespace-pre-wrap font-mono">{data.spec}</pre>
    </div>
  {:else}
    <div class="text-center py-12">
      <div class="bg-destructive/10 border border-destructive/20 rounded-lg p-6">
        <p class="text-destructive font-medium">Failed to load API specification.</p>
        <p class="text-destructive/80 text-sm mt-2">Please check the console for more details.</p>
      </div>
    </div>
  {/if}
</div> 