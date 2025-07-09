<script lang="ts">
import { createSvelteTable, FlexRender, renderComponent } from "$lib/components/ui/data-table";
import AgentChip from "$lib/components/agent-chip.svelte";
import AgentChipById from "$lib/components/agent-chip-by-id.svelte";
import { getCoreRowModel, getPaginationRowModel, getSortedRowModel, createColumnHelper } from "@tanstack/table-core";
import { Input } from "$lib/components/ui/input/index.js";
import { Button } from "$lib/components/ui/button/index.js";
import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js";
import ChevronDownIcon from "@lucide/svelte/icons/chevron-down";
import * as Table from "$lib/components/ui/table/index.js";
import { registerAgent } from "$lib/api/agents.js";
import { goto } from "$app/navigation";

export const title = 'Agents';

const { data } = $props();

// Register Agent popup state
let showRegisterSheet = $state(false);
let registerFormData = $state({
	name: "",
	agent_url: "",
	launcher_url: "",
	type: "green"
});
let isRegistering = $state(false);
let registerError = $state("");

async function handleRegisterSubmit() {
	isRegistering = true;
	registerError = "";

	try {
		const registerInfo = {
			name: registerFormData.name,
			agent_url: registerFormData.agent_url,
			launcher_url: registerFormData.launcher_url,
			meta: {
				type: registerFormData.type
			}
		};

		const result = await registerAgent(registerInfo);
		console.log('Agent registered successfully:', result);
		showRegisterSheet = false;
		goto('/agents');
	} catch (err) {
		registerError = err instanceof Error ? err.message : 'An error occurred';
	} finally {
		isRegistering = false;
	}
}

function mapAgentData(raw: any): any {
  if (!raw) return { id: '', name: 'Agent Not Found', notFound: true };
  return {
    id: raw.id,
    name: raw.registerInfo?.name || raw.agentCard?.name || 'Unknown Agent',
    avatarUrl: undefined, // Add logic if you have avatar URLs
    type: raw.registerInfo?.meta?.type || 'unknown',
    description: raw.agentCard?.description || '',
    notFound: false,
    raw
  };
}

type AgentRow = {
  id: string;
  name: string;
  type: string;
  description: string;
  notFound?: boolean;
  avatarUrl?: string;
  raw?: any;
};
let agents: AgentRow[] = data.agents.map(mapAgentData);
let filter = $state("");

// Filter agents by name (registerInfo.name or agentCard.name)
const getFilteredAgents = $derived((): any[] =>
  agents.filter((agent: any) => {
    const name = agent.name || '';
    return name.toLowerCase().includes(filter.toLowerCase());
  })
);
const filteredAgents: any[] = getFilteredAgents();

const columnHelper = createColumnHelper<any>();
const columns = [
  columnHelper.accessor('name', {
    id: 'name',
    header: 'Name',
    cell: cell => cell.getValue() || 'Unknown Agent',
  }),
  columnHelper.accessor('type', {
    id: 'type',
    header: 'Type',
    cell: cell => cell.getValue() || 'unknown',
  }),
  columnHelper.accessor('description', {
    id: 'description',
    header: 'Description',
    cell: cell => cell.getValue() || '',
  }),
  columnHelper.display({
    id: 'chip',
    header: 'Chip',
    cell: cell => cell.row.original // pass the full agent object
  })
];

let pagination = $state({ pageIndex: 0, pageSize: 10 });
let sorting: import("@tanstack/table-core").SortingState = $state([]);
let columnVisibility = $state({});

const table = createSvelteTable({
  get data() {
    return filteredAgents;
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

<div class="w-full flex flex-col items-center justify-center mt-10 mb-8">
	<h1 class="text-2xl font-bold text-center mb-4">Register an Agent</h1>
	<button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition" onclick={() => showRegisterSheet = true}>
		<span class="text-xl font-bold">+</span>
		Register Agent
	</button>
</div>

{#if showRegisterSheet}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onclick={() => showRegisterSheet = false}>
		<div class="bg-background rounded-xl shadow-2xl p-6 max-w-lg w-full relative" onclick={(e) => e.stopPropagation()}>
			<button class="absolute top-3 right-3 text-muted-foreground hover:text-foreground" onclick={() => showRegisterSheet = false} aria-label="Close">
				<span class="text-xl">&times;</span>
			</button>
			<h2 class="text-xl font-bold mb-4">Register New Agent</h2>
			<form onsubmit={(e) => { e.preventDefault(); handleRegisterSubmit(); }} class="flex flex-col gap-4">
				<div>
					<label for="name" class="block mb-1 font-medium">Agent Name:</label>
					<input id="name" type="text" bind:value={registerFormData.name} required class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div>
					<label for="agent_url" class="block mb-1 font-medium">Agent URL:</label>
					<input id="agent_url" type="text" bind:value={registerFormData.agent_url} placeholder="http://localhost:9999" required class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div>
					<label for="launcher_url" class="block mb-1 font-medium">Launcher URL:</label>
					<input id="launcher_url" type="text" bind:value={registerFormData.launcher_url} placeholder="http://launcher-url" required class="w-full px-3 py-2 border rounded-md" />
				</div>
				<div>
					<label for="type" class="block mb-1 font-medium">Agent Type:</label>
					<select id="type" bind:value={registerFormData.type} class="w-full px-3 py-2 border rounded-md">
						<option value="green">Green Team</option>
						<option value="red">Red Team</option>
						<option value="blue">Blue Team</option>
						<option value="purple">Purple Team</option>
					</select>
				</div>
				{#if registerError}
					<div class="text-red-500 text-sm">{registerError}</div>
				{/if}
				<div class="flex gap-2 justify-end mt-2">
					<button type="submit" class="px-4 py-2 rounded-md bg-primary text-primary-foreground font-semibold shadow hover:bg-primary/90 transition disabled:opacity-60" disabled={isRegistering}>
						{isRegistering ? 'Registering...' : 'Register Agent'}
					</button>
					<button type="button" class="px-4 py-2 rounded-md bg-muted text-foreground font-semibold shadow hover:bg-accent transition" onclick={() => showRegisterSheet = false}>Cancel</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh]">
  <div class="@container/main flex flex-1 flex-col gap-2 items-center justify-center w-full">
    <div class="flex flex-col gap-4 py-4 md:gap-6 md:py-6 w-full items-center justify-center">
      <div class="w-full max-w-5xl">
        <h2 class="text-2xl font-bold text-center mb-6">Agents</h2>
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
                      {#if cell.column.id === 'chip'}
                        <AgentChipById agentId={cell.row.original.id} />
                      {:else if cell.column.id === 'description'}
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
