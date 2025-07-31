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
    <div class="flex justify-center items-center py-3 bg-white">
      <Carousel.Root 
        setApi={(emblaApi) => (api = emblaApi)}
        opts={{
          align: "center"
        }}
        class="w-full max-w-sm relative"
      >
        <Carousel.Content class="flex items-center justify-center">
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/battles/ongoing"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'ongoing' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                Ongoing
              </a>
            </div>
          </Carousel.Item>
          
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/battles/past"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'past' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                Past
              </a>
            </div>
          </Carousel.Item>
          
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/battles/stage-battle"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'stage-battle' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                Stage
              </a>
            </div>
          </Carousel.Item>
        </Carousel.Content>
      </Carousel.Root>
    </div>
  {/if}

  <!-- Page Content -->
  <main class="flex-1 p-6">
    <div class="w-full max-w-7xl mx-auto">
      {@render children()}
    </div>
  </main>
</div> 