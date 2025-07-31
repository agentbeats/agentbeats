<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import ArrowUpDownIcon from "@lucide/svelte/icons/arrow-up-down";

  let { onclick } = $props<{ onclick: () => void }>();
</script>

<Button variant="ghost" onclick={onclick}>
  ELO Rating
  <ArrowUpDownIcon class="ml-2 h-4 w-4" />
</Button>