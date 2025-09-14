<script lang="ts">
  let { data } = $props<{ data: { content: any } }>();
</script>

<div class="markdown-body prose prose-lg max-w-none">
  <svelte:component this={data.content} />
</div> 