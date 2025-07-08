<script lang="ts">
import * as Sidebar from "$lib/components/ui/sidebar/index.js";
import AppSidebar from "$lib/components/sidebar-left.svelte";
import SiteHeader from "$lib/components/site-header.svelte";
import { createSvelteTable } from "$lib/components/ui/data-table/data-table.svelte";
import { FlexRender, renderComponent } from "$lib/components/ui/data-table";
import AgentChip from "$lib/components/agent-chip.svelte";
import { getCoreRowModel, createColumnHelper } from "@tanstack/table-core";

export let data: { agents: any[] };
let agents = data.agents.map(raw => ({
  id: raw.id,
  name: raw.registerInfo?.name || raw.agentCard?.name || 'Unknown Agent',
  type: raw.registerInfo?.meta?.type || 'unknown',
  description: raw.agentCard?.description || '',
  raw
}));

const columnHelper = createColumnHelper<typeof agents[0]>();
const columns = [
  columnHelper.accessor('name', {
    header: 'Name',
  }),
  columnHelper.accessor('type', {
    header: 'Type',
  }),
  columnHelper.accessor('description', {
    header: 'Description',
  }),
  columnHelper.display({
    id: 'chip',
    header: 'Chip',
    cell: cell => renderComponent(AgentChip, { agent: cell.row.original })
  })
];

const table = createSvelteTable({
  data: agents,
  columns,
  getCoreRowModel: getCoreRowModel(),
});
</script>

<Sidebar.Provider
  open={false}
  style="--sidebar-width: calc(var(--spacing) * 94); --sidebar-width-icon: calc(var(--spacing) * 16); --header-height: calc(var(--spacing) * 12);"
>
  <AppSidebar variant="inset" />
  <Sidebar.Inset>
    <SiteHeader title={"Agents"}/>
    <div class="flex flex-1 flex-col">
      <div class="@container/main flex flex-1 flex-col gap-2">
        <div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6 items-center justify-center" style="max-width: calc(100vw - var(--sidebar-width) - 2rem);">
          <div class="rounded-lg border bg-card shadow-sm w-full max-w-4xl">
            <div class="flex items-center justify-between px-4 py-3 border-b">
              <h2 class="text-lg font-semibold">Agents</h2>
              <!-- Optional: Add a filter input here if desired -->
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-border text-sm">
                <thead class="bg-muted/50">
                  {#each table.getHeaderGroups() as headerGroup}
                    <tr>
                      {#each headerGroup.headers as header}
                        <th colspan={header.colSpan} class="px-4 py-2 text-left font-semibold text-muted-foreground">
                          <FlexRender content={header.column.columnDef.header} context={header.getContext()} />
                        </th>
                      {/each}
                    </tr>
                  {/each}
                </thead>
                <tbody>
                  {#each table.getRowModel().rows as row, i}
                    <tr class={i % 2 === 0 ? 'bg-background' : 'bg-muted/30'}>
                      {#each row.getVisibleCells() as cell}
                        <td class="px-4 py-2 align-middle">
                          <FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
                        </td>
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Sidebar.Inset>
</Sidebar.Provider>
