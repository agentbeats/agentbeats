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
    <div class="flex justify-center items-center py-3 bg-white">
      <Carousel.Root 
        setApi={(emblaApi) => (api = emblaApi)}
        opts={{
          align: "center"
        }}
        class="w-full max-w-md"
      >
        <Carousel.Content class="flex items-center justify-center">
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/agents/my-agents"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'my-agents' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                My Agents
              </a>
            </div>
          </Carousel.Item>
          
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/agents/directory"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'directory' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                Directory
              </a>
            </div>
          </Carousel.Item>
          
          <Carousel.Item class="basis-1/3 flex justify-center">
            <div class="p-1">
              <a 
                href="/agents/register"
                class="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-colors duration-200 rounded-md {currentTab === 'register' ? 'text-black font-medium' : 'text-gray-500 hover:text-gray-700'}"
              >
                Register
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