<script lang="ts">
import Avatar from "./ui/avatar/avatar.svelte";
import AvatarImage from "./ui/avatar/avatar-image.svelte";
import AvatarFallback from "./ui/avatar/avatar-fallback.svelte";
import * as Sheet from "./ui/sheet";
import UserIcon from "@lucide/svelte/icons/user";
import * as Tooltip from "./ui/tooltip";

export let agent: {
  id: string;
  name: string;
  avatarUrl?: string;
  type?: string;
  description?: string;
  notFound?: boolean;
  [key: string]: any;
};

function fallbackColor(type?: string) {
  switch ((type || '').toLowerCase()) {
    case 'blue': return 'bg-blue-500 text-white';
    case 'red': return 'bg-red-500 text-white';
    case 'green': return 'bg-green-500 text-white';
    case 'purple': return 'bg-purple-500 text-white';
    default: return 'bg-muted text-muted-foreground';
  }
}
</script>

<Tooltip.Provider delayDuration={1000}>
  <Tooltip.Root>
    <Tooltip.Trigger>
      <Sheet.Root>
        <Sheet.Trigger class="inline-flex items-center gap-2 rounded-full border bg-card px-2 py-0.5 shadow-sm hover:bg-accent cursor-pointer transition text-xs min-h-6 min-w-0">
          <Avatar class="size-5">
            {#if agent.notFound}
              <AvatarFallback class="bg-muted text-muted-foreground"><UserIcon class="size-3" /></AvatarFallback>
            {:else if agent.avatarUrl}
              <AvatarImage src={agent.avatarUrl} alt={agent.name} />
            {:else}
              <AvatarFallback class={fallbackColor(agent.type)}>{agent.name?.[0] ?? '?'}</AvatarFallback>
            {/if}
          </Avatar>
          <span class="font-medium truncate max-w-[6rem]">{agent.notFound ? 'Agent Not Found' : agent.name}</span>
        </Sheet.Trigger>
        <Sheet.Content side="right">
          <div class="p-6 min-w-[300px] max-w-[90vw]">
            <div class="flex items-center gap-4 mb-4">
              <Avatar class="size-12">
                {#if agent.notFound}
                  <AvatarFallback class="bg-muted text-muted-foreground"><UserIcon class="size-8" /></AvatarFallback>
                {:else if agent.avatarUrl}
                  <AvatarImage src={agent.avatarUrl} alt={agent.name} />
                {:else}
                  <AvatarFallback class={fallbackColor(agent.type)}>{agent.name?.[0] ?? '?'}</AvatarFallback>
                {/if}
              </Avatar>
              <div>
                <div class="text-lg font-bold">{agent.notFound ? 'Agent Not Found' : agent.name}</div>
                {#if agent.type && !agent.notFound}
                  <div class="text-xs text-muted-foreground">{agent.type}</div>
                {/if}
              </div>
            </div>
            {#if agent.description && !agent.notFound}
              <div class="mb-2 text-sm">{agent.description}</div>
            {/if}
            <pre class="bg-muted rounded p-2 text-xs overflow-x-auto">{JSON.stringify(agent, null, 2)}</pre>
          </div>
        </Sheet.Content>
      </Sheet.Root>
    </Tooltip.Trigger>
    <Tooltip.Content side="top" class="z-50 select-text px-2 py-0.5 text-[10px] min-h-0 min-w-0">
      <span class="font-mono">{agent.id}</span>
    </Tooltip.Content>
  </Tooltip.Root>
</Tooltip.Provider> 