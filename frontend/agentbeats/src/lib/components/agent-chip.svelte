<script lang="ts">
import Avatar from "./ui/avatar/avatar.svelte";
import AvatarImage from "./ui/avatar/avatar-image.svelte";
import AvatarFallback from "./ui/avatar/avatar-fallback.svelte";
import * as Sheet from "./ui/sheet";
import UserIcon from "@lucide/svelte/icons/user";
import * as Tooltip from "./ui/tooltip";
import XIcon from "@lucide/svelte/icons/x";

export let agent: {
  id: string;
  name: string;
  avatarUrl?: string;
  type?: string;
  description?: string;
  notFound?: boolean;
  [key: string]: any;
};

let showModal = false;
let clickTimeout: number | null = null;

function openModal() { 
  if (clickTimeout) {
    clearTimeout(clickTimeout);
    clickTimeout = null;
  }
  showModal = true; 
}

function closeModal() { showModal = false; }

function handleClick() {
  // Small delay to allow text selection
  clickTimeout = setTimeout(() => {
    openModal();
  }, 150);
}

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

{#if !agent}
  <span class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1.5 shadow-sm text-xs min-h-7 min-w-[6.5rem] bg-muted text-muted-foreground">
    <UserIcon class="size-3 mr-2" />
    <span class="font-medium truncate max-w-[7rem]">Agent Not Found</span>
  </span>
{:else}
  <Tooltip.Provider delayDuration={1000}>
    <Tooltip.Root>
      <Tooltip.Trigger>
        <div class="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1.5 shadow-sm hover:bg-accent cursor-pointer transition text-xs min-h-7 min-w-[6.5rem] select-text" on:click={handleClick} tabindex="0" role="button">
          <Avatar class="size-6">
            {#if agent.notFound}
              <AvatarFallback class="bg-muted text-muted-foreground"><UserIcon class="size-3" /></AvatarFallback>
            {:else if agent.avatarUrl}
              <AvatarImage src={agent.avatarUrl} alt={agent.name} />
            {:else}
              <AvatarFallback class={fallbackColor(agent.type)}>{agent.name?.[0] ?? '?'}</AvatarFallback>
            {/if}
          </Avatar>
          <span class="font-medium break-words whitespace-normal max-w-[7rem] select-text">{agent.notFound ? 'Agent Not Found' : agent.name}</span>
        </div>
        {#if showModal}
          <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" on:click={closeModal}>
            <div class="bg-background rounded-xl shadow-2xl p-6 max-w-lg w-full relative max-h-[90vh] overflow-y-auto" on:click|stopPropagation>
              <button class="absolute top-3 right-3 text-muted-foreground hover:text-foreground" on:click={closeModal} aria-label="Close">
                <XIcon class="size-5" />
              </button>
              <div class="flex items-center gap-4 mb-4">
                <Avatar class="size-11">
                  {#if agent.notFound}
                    <AvatarFallback class="bg-muted text-muted-foreground"><UserIcon class="size-7" /></AvatarFallback>
                  {:else if agent.avatarUrl}
                    <AvatarImage src={agent.avatarUrl} alt={agent.name} />
                  {:else}
                    <AvatarFallback class={fallbackColor(agent.type)}>{agent.name?.[0] ?? '?'}</AvatarFallback>
                  {/if}
                </Avatar>
                <div>
                  <div class="text-base font-bold">{agent.notFound ? 'Agent Not Found' : agent.name}</div>
                  {#if agent.type && !agent.notFound}
                    <div class="text-xs text-muted-foreground">{agent.type}</div>
                  {/if}
                </div>
              </div>
              {#if agent.description && !agent.notFound}
                <div class="mb-2 text-sm break-words whitespace-normal max-w-full">{agent.description}</div>
              {/if}
              <pre class="bg-muted rounded p-2 text-xs overflow-x-auto max-h-60 overflow-y-auto text-left">{JSON.stringify(agent, null, 2)}</pre>
            </div>
          </div>
        {/if}
      </Tooltip.Trigger>
      <Tooltip.Content side="top" class="z-50 select-text px-2 py-0.5 text-[10px] min-h-0 min-w-0">
        <span class="font-mono">{agent.id}</span>
      </Tooltip.Content>
    </Tooltip.Root>
  </Tooltip.Provider>
{/if} 