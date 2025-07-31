import type { ColumnDef } from "@tanstack/table-core";
import { createRawSnippet } from "svelte";
import { renderSnippet, renderComponent } from "$lib/components/ui/data-table/index.js";
import AgentTableActions from "./agent-table-actions.svelte";
import AgentTableEloButton from "./agent-table-elo-button.svelte";

export type Agent = {
  id: string;
  name: string;
  description: string;
  elo_rating: number;
  win_rate: number;
  battles: number;
  created_by: string;
  is_green: boolean;
};

export const columns: ColumnDef<Agent>[] = [
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => {
      const nameSnippet = createRawSnippet<[string]>((getName) => {
        const name = getName();
        return {
          render: () => `<div class="font-medium">${name}</div>`
        };
      });
      return renderSnippet(nameSnippet, row.getValue("name"));
    },
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const descSnippet = createRawSnippet<[string]>((getDesc) => {
        const desc = getDesc();
        return {
          render: () => `<div class="text-sm text-muted-foreground truncate max-w-xs">${desc}</div>`
        };
      });
      return renderSnippet(descSnippet, row.getValue("description"));
    },
  },
  {
    accessorKey: "elo_rating",
    header: ({ column }) =>
      renderComponent(AgentTableEloButton, {
        onclick: () => {
          const handler = column.getToggleSortingHandler();
          if (handler) handler({} as any);
        },
      }),
    cell: ({ row }) => {
      const eloSnippet = createRawSnippet<[string]>((getElo) => {
        const elo = getElo();
        return {
          render: () => `<div class="text-right font-medium">${elo}</div>`
        };
      });
      return renderSnippet(eloSnippet, (row.getValue("elo_rating") as number).toString());
    },
  },
  {
    accessorKey: "win_rate",
    header: "Win Rate",
    cell: ({ row }) => {
      const winRateSnippet = createRawSnippet<[string]>((getWinRate) => {
        const winRate = getWinRate();
        return {
          render: () => `<div class="text-right">${winRate}%</div>`
        };
      });
      return renderSnippet(winRateSnippet, ((row.getValue("win_rate") as number) * 100).toFixed(1));
    },
  },
  {
    accessorKey: "battles",
    header: "Battles",
    cell: ({ row }) => {
      const battlesSnippet = createRawSnippet<[string]>((getBattles) => {
        const battles = getBattles();
        return {
          render: () => `<div class="text-right">${battles}</div>`
        };
      });
      return renderSnippet(battlesSnippet, (row.getValue("battles") as number).toString());
    },
  },
  {
    accessorKey: "created_by",
    header: "Created By",
    cell: ({ row }) => {
      const creatorSnippet = createRawSnippet<[string]>((getCreator) => {
        const creator = getCreator();
        return {
          render: () => `<div class="text-sm text-muted-foreground">${creator}</div>`
        };
      });
      return renderSnippet(creatorSnippet, row.getValue("created_by"));
    },
  },
  {
    accessorKey: "is_green",
    header: "Type",
    cell: ({ row }) => {
      const isGreen = row.getValue("is_green");
      const typeSnippet = createRawSnippet<[string]>((getType) => {
        const type = getType();
        return {
          render: () => `<div class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${type === 'Green' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}">${type}</div>`
        };
      });
      return renderSnippet(typeSnippet, isGreen ? "Green" : "Opponent");
    },
  },
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }) =>
      renderComponent(AgentTableActions, { id: row.original.id })
  },
];