<script lang="ts" module>
    // AgentBeats documentation structure
    const data = {
      navMain: [
        {
          title: "Getting Started",
          items: [
            {
              title: "Quick Start",
              url: "/docs/getting-started/quick-start",
            },
            {
              title: "Making New Docs",
              url: "/docs/getting-started/making-new-docs",
            },
          ],
        },
        {
          title: "CLI",
          items: [
            {
              title: "CLI Reference",
              url: "/docs/cli/cli-reference",
            },
          ],
        },
        {
          title: "API",
          items: [
            {
              title: "API Reference",
              url: "/docs/api/api-reference",
            },
          ],
        },
      ],
    };
  </script>
  <script lang="ts">
    import * as Sidebar from "$lib/components/ui/sidebar/index.js";
    import GalleryVerticalEndIcon from "@lucide/svelte/icons/gallery-vertical-end";
    import type { ComponentProps } from "svelte";
    let { ref = $bindable(null), ...restProps }: ComponentProps<typeof Sidebar.Root> = $props();
  </script>
  <Sidebar.Root variant="floating" {...restProps}>
    <Sidebar.Header>
      <Sidebar.Menu>
        <Sidebar.MenuItem>
          <Sidebar.MenuButton size="lg">
            {#snippet child({ props })}
              <a href="/" {...props}>
                <div
                  class="bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg"
                >
                  <GalleryVerticalEndIcon class="size-4" />
                </div>
                <div class="flex flex-col gap-0.5 leading-none">
                  <span class="font-medium">AgentBeats</span>
                </div>
              </a>
            {/snippet}
          </Sidebar.MenuButton>
        </Sidebar.MenuItem>
      </Sidebar.Menu>
    </Sidebar.Header>
    <Sidebar.Content>
      {#each data.navMain as group (group.title)}
        <Sidebar.Group>
          <Sidebar.GroupLabel>{group.title}</Sidebar.GroupLabel>
          <Sidebar.GroupContent>
            <Sidebar.Menu>
              {#each group.items as item (item.title)}
                <Sidebar.MenuItem>
                  <Sidebar.MenuButton>
                    {#snippet child({ props })}
                      <a href={item.url} {...props}>{item.title}</a>
                    {/snippet}
                  </Sidebar.MenuButton>
                </Sidebar.MenuItem>
              {/each}
            </Sidebar.Menu>
          </Sidebar.GroupContent>
        </Sidebar.Group>
      {/each}
    </Sidebar.Content>
  </Sidebar.Root>
  