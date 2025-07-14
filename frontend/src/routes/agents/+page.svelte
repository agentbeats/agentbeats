<script lang="ts">
import { onMount, onDestroy } from "svelte";
import { createSvelteTable, FlexRender, renderComponent } from "$lib/components/ui/data-table";
import { getCoreRowModel, getPaginationRowModel, getSortedRowModel, createColumnHelper } from "@tanstack/table-core";
import { Input } from "$lib/components/ui/input/index.js";
import { Button } from "$lib/components/ui/button/index.js";
import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
import * as Table from "$lib/components/ui/table/index.js";
import { registerAgent } from "$lib/api/agents.js";
import { goto } from "$app/navigation";
import { user, loading } from "$lib/stores/auth";
import { supabase } from "$lib/auth/supabase";

export const title = 'Agents';

const { data } = $props();

let isAuthChecking = $state(true);
let unsubscribe: (() => void) | null = null;

onMount(async () => {
  // Check authentication immediately
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    console.log('Agents page: No session found, redirecting to login');
    goto('/login');
    return;
  }
  
  isAuthChecking = false;
  
  // Subscribe to auth state changes for logout detection
  unsubscribe = user.subscribe(($user) => {
    if (!$user && !$loading) {
      console.log('Agents page: User logged out, redirecting to login');
      goto('/login');
    }
  });
});

onDestroy(() => {
  if (unsubscribe) {
    unsubscribe();
  }
});

function mapAgentData(raw: any): any {
  const regInfo = raw.registerInfo || raw.register_info || {};
  const agentCard = raw.agentCard || raw.agent_card || {};
  if (!raw) return { id: '', name: 'Agent Not Found', notFound: true };
  return {
    id: raw.id,
    name: regInfo.name || agentCard.name || 'Unknown Agent',
    agent_url: regInfo.agent_url || '',
    is_green: regInfo.is_green === true ? 'Yes' : 'No',
    description: agentCard.description || '',
    status: raw.status || '',
    created_at: raw.created_at || '',
    agent_id: raw.agent_id || '',
    notFound: false,
    raw
  };
}

type AgentRow = {
  id: string;
  name: string;
  agent_url: string;
  is_green: string;
  description: string;
  status: string;
  created_at: string;
  agent_id: string;
  notFound?: boolean;
  avatarUrl?: string;
  raw?: any;
};
let agents: AgentRow[] = data.agents.map(mapAgentData);
let filter = $state("");

const columnHelper = createColumnHelper<any>();
function getAgentAge(created_at: string): string {
  if (!created_at) return '';
  const created = new Date(created_at);
  const now = new Date();
  // Use UTC to avoid timezone issues
  const utcCreated = Date.UTC(created.getUTCFullYear(), created.getUTCMonth(), created.getUTCDate());
  const utcNow = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
  const diffMs = utcNow - utcCreated;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return `${Math.max(0, diffDays)}d`;
}
const columns = [
  columnHelper.accessor('name', {
    id: 'name',
    header: 'Name',
    cell: cell => cell.getValue() || 'Unknown Agent',
  }),
  columnHelper.accessor('agent_url', {
    id: 'agent_url',
    header: 'Agent URL',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('launcher_url', {
    id: 'launcher_url',
    header: 'Launcher URL',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('is_green', {
    id: 'is_green',
    header: 'Is Green',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('status', {
    id: 'status',
    header: 'Status',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('description', {
    id: 'description',
    header: 'Description',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('age', {
    id: 'age',
    header: 'Age',
    cell: cell => getAgentAge(cell.row.original.created_at),
  }),
  columnHelper.accessor('created_at', {
    id: 'created_at',
    header: 'Created At',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('agent_id', {
    id: 'agent_id',
    header: 'Agent ID',
    cell: cell => cell.getValue() || '',
  })
];

let pagination = $state({ pageIndex: 0, pageSize: 10 });
let sorting: import("@tanstack/table-core").SortingState = $state([]);
let columnVisibility: { [key: string]: boolean } = $state({
  launcher_url: false,
  agent_id: false,
  created_at: false
});

const table = createSvelteTable({
  get data() {
    return agents;
  },
  columns,
  state: {
    get pagination() {
      return pagination;
    },
    get sorting() {
      return sorting;
    },
    get columnVisibility() {
      return columnVisibility;
    },
    get globalFilter() {
      return filter;
    }
  },
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
  globalFilterFn: (row, columnId, filterValue) => {
    if (columnId !== 'name') return true;
    const value = row.getValue('name');
    const valueStr = typeof value === 'string' ? value : '';
    return valueStr.toLowerCase().includes((filterValue || '').toLowerCase());
  },
  onPaginationChange: (updater) => {
    if (typeof updater === "function") {
      pagination = updater(pagination);
    } else {
      pagination = updater;
    }
  },
  onSortingChange: (updater) => {
    if (typeof updater === "function") {
      sorting = updater(sorting);
    } else {
      sorting = updater;
    }
  },
  onColumnVisibilityChange: (updater) => {
    if (typeof updater === "function") {
      columnVisibility = updater(columnVisibility);
    } else {
      columnVisibility = updater;
    }
  },
  onGlobalFilterChange: (updater) => {
    if (typeof updater === "function") {
      filter = updater(filter);
    } else {
      filter = updater;
    }
  }
});
</script>

{#if isAuthChecking}
  <div class="flex items-center justify-center h-64">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    <span class="ml-2">Checking authentication...</span>
  </div>
{:else}
  <div class="w-full flex flex-col items-center justify-center mt-10 mb-8">
    <h1 class="text-2xl font-bold text-center mb-8">Agents</h1>
    <button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition cursor-pointer" onclick={() => goto('/agents/register-agent')}>
      Register Agent
    </button>
  </div>

  <div class="flex flex-1 flex-col items-center justify-center min-h-[80vh] w-full">
    <div class="flex flex-1 flex-col gap-2 items-center justify-center w-full">
      <div class="flex flex-col gap-2 py-2 w-full items-center justify-center">
        <div class="w-full max-w-5xl">
          <div class="flex items-center py-4">
            <Input
              placeholder="Filter agents by name..."
              bind:value={filter}
              class="max-w-sm"
            />
            <DropdownMenu.Root>
              <DropdownMenu.Trigger>
                {#snippet child({ props })}
                  <Button {...props} variant="outline" class="ml-auto">
                    Columns <ChevronDownIcon class="ml-2 size-4" />
                  </Button>
                {/snippet}
              </DropdownMenu.Trigger>
              <DropdownMenu.Content align="end">
                {#each table.getAllColumns().filter((col) => col.getCanHide()) as column (column.id)}
                  <DropdownMenu.CheckboxItem
                    class="capitalize"
                    bind:checked={() => column.getIsVisible(), (v) => column.toggleVisibility(!!v)}
                  >
                    {column.id}
                  </DropdownMenu.CheckboxItem>
                {/each}
              </DropdownMenu.Content>
            </DropdownMenu.Root>
          </div>
          <div class="rounded-md border">
            <Table.Root>
              <Table.Header>
                {#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
                  <Table.Row>
                    {#each headerGroup.headers as header (header.id)}
                      <Table.Head class="px-4 py-2 text-left font-semibold text-muted-foreground">
                        {#if !header.isPlaceholder}
                          <FlexRender content={header.column.columnDef.header} context={header.getContext()} />
                        {/if}
                      </Table.Head>
                    {/each}
                  </Table.Row>
                {/each}
              </Table.Header>
              <Table.Body>
                {#each table.getRowModel().rows as row (row.id)}
                  <Table.Row>
                    {#each row.getVisibleCells() as cell (cell.id)}
                      <Table.Cell class="px-4 py-2 align-middle {cell.column.id === 'description' ? 'max-w-xs break-words' : ''}">
                        {#if cell.column.id === 'description'}
                          <div class="break-words whitespace-normal">
                            <FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
                          </div>
                        {:else}
                          <FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
                        {/if}
                      </Table.Cell>
                    {/each}
                  </Table.Row>
                {:else}
                  <Table.Row>
                    <Table.Cell colspan={columns.length} class="h-24 text-center">
                      No results.
                    </Table.Cell>
                  </Table.Row>
                {/each}
              </Table.Body>
            </Table.Root>
          </div>
          <div class="flex items-center justify-end space-x-2 pt-4">
            <div class="space-x-2">
              <Button
                variant="outline"
                size="sm"
                onclick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onclick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}
