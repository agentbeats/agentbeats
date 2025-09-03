<script lang="ts">
  import { page } from "$app/stores";
  import { type CarouselAPI } from "$lib/components/ui/carousel/context.js";
  import * as Carousel from "$lib/components/ui/carousel/index.js";

  let { children } = $props();

  // Get the current tab from the URL
  let currentTab = $derived($page.url.pathname.split('/').pop() || 'my-agents');
  let api = $state<CarouselAPI>();

  // Map tab names to carousel indices
  const tabToIndex = { 'my-agents': 0, 'directory': 1, 'register': 2 };

  // Check if we're on an agent detail page
  let isAgentDetailsPage = $derived($page.url.pathname.match(/\/agents\/[^\/]+\/?$/) && !$page.url.pathname.includes('/my-agents') && !$page.url.pathname.includes('/directory') && !$page.url.pathname.includes('/register'));

  $effect(() => {
    if (api) {
      // Set initial position based on current tab
      const targetIndex = tabToIndex[currentTab as keyof typeof tabToIndex] || 0;
      api.scrollTo(targetIndex);
    }
  });
</script>

<div class="flex flex-col min-h-screen">
  <!-- Tab Switcher Carousel -->
  {#if !isAgentDetailsPage}
    <div class="flex justify-center items-center py-3 bg-background">
      <nav class="flex space-x-8">
        <a 
          href="/agents/my-agents" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/agents/my-agents' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          My Agents
        </a>
        <a 
          href="/agents/directory" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/agents/directory' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          Agent Directory
        </a>
        <a 
          href="/agents/register" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/agents/register' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          Register Agent
        </a>
      </nav>
    </div>
  {/if}

  <!-- Page Content -->
  <main class="flex-1 p-6">
    <div class="w-full max-w-7xl mx-auto">
      {@render children()}
    </div>
  </main>
</div> 