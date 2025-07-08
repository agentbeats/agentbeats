<script lang="ts">
import { createSvelteTable, FlexRender } from "$lib/components/ui/data-table";
import { getCoreRowModel, getPaginationRowModel, getSortedRowModel, createColumnHelper } from "@tanstack/table-core";
import { Input } from "$lib/components/ui/input/index.js";
import { Button } from "$lib/components/ui/button/index.js";
import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
import * as Table from "$lib/components/ui/table/index.js";
import AgentChipById from "$lib/components/agent-chip-by-id.svelte";

export const title = 'Users';

const { data } = $props();

function mapUserData(raw: any): any {
  if (!raw) return { userid: '', username: 'User Not Found', notFound: true };
  return {
    userid: raw.id || raw.userid || '',
    username: raw.username || '',
    email: raw.email || '',
    full_name: raw.full_name || '',
    elo: raw.elo ?? '',
    agentIds: raw.agents ? Object.keys(raw.agents) : [],
    notFound: false,
    raw
  };
}

type UserRow = {
  userid: string;
  username: string;
  email: string;
  full_name: string;
  elo: number;
  agentIds: string[];
  notFound?: boolean;
  raw?: any;
};
let users: UserRow[] = data.users.map(mapUserData);
let filter = "";

const getFilteredUsers = $derived((): any[] =>
  users.filter((user: any) => {
    const username = user.username || '';
    return username.toLowerCase().includes(filter.toLowerCase());
  })
);
const filteredUsers: any[] = getFilteredUsers();

const columnHelper = createColumnHelper<any>();
const columns = [
  columnHelper.accessor('username', {
    id: 'username',
    header: 'Username',
    cell: cell => cell.getValue() || 'Unknown User',
  }),
  columnHelper.accessor('email', {
    id: 'email',
    header: 'Email',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('full_name', {
    id: 'full_name',
    header: 'Full Name',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('elo', {
    id: 'elo',
    header: 'ELO',
    cell: cell => cell.getValue() ?? '',
  }),
  columnHelper.accessor('userid', {
    id: 'userid',
    header: 'User ID',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.accessor('agentIds', {
    id: 'agentChips',
    header: 'Agent Chips',
    cell: cell => cell.getValue() ?? [],
  })
];

let pagination = $state({ pageIndex: 0, pageSize: 10 });
let sorting: import("@tanstack/table-core").SortingState = $state([]);
let columnVisibility = $state({});

const table = createSvelteTable({
  get data() {
    return filteredUsers;
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
    }
  },
  getCoreRowModel: getCoreRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  getSortedRowModel: getSortedRowModel(),
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
  }
});
</script>

<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh]">
  <div class="@container/main flex flex-1 flex-col gap-2 items-center justify-center w-full">
    <div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6 w-full items-center justify-center">
      <div class="w-full max-w-5xl">
        <h2 class="text-2xl font-bold text-center mb-6">Users</h2>
        <div class="flex items-center py-4">
          <Input
            placeholder="Filter users by username..."
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
                    <Table.Cell class="px-4 py-2 align-middle">
                      {#if cell.column.id === 'agentChips'}
                        <div class="flex flex-wrap gap-1">
                          {#each cell.getValue() as string[] as agentId (agentId)}
                            <AgentChipById agentId={agentId} />
                          {/each}
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