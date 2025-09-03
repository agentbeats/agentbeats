<script lang="ts">
  import { Button } from "$lib/components/ui/button";
  import { page } from "$app/stores";
  import { type CarouselAPI } from "$lib/components/ui/carousel/context.js";
  import * as Carousel from "$lib/components/ui/carousel/index.js";

  let { children } = $props();

  // Get the current tab from the URL
  let currentTab = $derived($page.url.pathname.split('/').pop() || 'ongoing');
  let api = $state<CarouselAPI>();

  // Check if we're on a battle details page (URL contains a battle ID)
  let isBattleDetailsPage = $derived($page.url.pathname.match(/\/battles\/[^\/]+\/?$/) && 
    !['ongoing', 'past', 'stage-battle'].includes($page.url.pathname.split('/').pop() || ''));

  // Map tab names to carousel indices
  const tabToIndex = { ongoing: 0, past: 1, 'stage-battle': 2 };

  $effect(() => {
    if (api) {
      // Set initial position based on current tab
      const targetIndex = tabToIndex[currentTab as keyof typeof tabToIndex] || 0;
      api.scrollTo(targetIndex);
    }
  });
</script>

<div class="flex flex-col min-h-screen">
  <!-- Tab Switcher Carousel - Only show if not on battle details page -->
  {#if !isBattleDetailsPage}
    <div class="flex justify-center items-center py-3 bg-background">
      <nav class="flex space-x-8">
        <a 
          href="/battles/ongoing" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/battles/ongoing' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          Ongoing
        </a>
        <a 
          href="/battles/past" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/battles/past' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          Past
        </a>
        <a 
          href="/battles/stage-battle" 
          class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 {$page.url.pathname === '/battles/stage-battle' ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}"
        >
          Stage Battle
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