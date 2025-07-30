<script lang="ts">
  let { data } = $props<{ data: { spec: any } }>();
</script>

<div class="max-w-none">
  
  {#if data.spec}
    <div class="bg-gray-900 text-gray-100 rounded-lg p-6 overflow-auto">
      <pre class="text-sm whitespace-pre-wrap font-mono">{data.spec}</pre>
    </div>
  {:else}
    <div class="text-center py-12">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 font-medium">Failed to load API specification.</p>
        <p class="text-red-600 text-sm mt-2">Please check the console for more details.</p>
      </div>
    </div>
  {/if}
</div> 