<script lang="ts">
  import { Button } from "$lib/components/ui/button/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
  import MoreHorizontalIcon from "@lucide/svelte/icons/more-horizontal";
  import EyeIcon from "@lucide/svelte/icons/eye";
  import SwordIcon from "@lucide/svelte/icons/sword";
  import { goto } from "$app/navigation";

  let { id } = $props<{ id: string }>();
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger>
    {#snippet child({ props })}
      <Button {...props} variant="ghost" class="h-8 w-8 p-0">
        <span class="sr-only">Open menu</span>
        <MoreHorizontalIcon class="h-4 w-4" />
      </Button>
    {/snippet}
  </DropdownMenu.Trigger>
  <DropdownMenu.Content align="end">
    <DropdownMenu.Item onclick={() => goto(`/agents/${id}`)}>
      <EyeIcon class="mr-2 h-4 w-4" />
      View Details
    </DropdownMenu.Item>
    <DropdownMenu.Item onclick={() => goto(`/battles/stage-battle?agent=${id}`)}>
      <SwordIcon class="mr-2 h-4 w-4" />
      Battle
    </DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu.Root>