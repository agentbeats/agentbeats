import { N as copy_payload, O as assign_payload, J as bind_props, y as pop, w as push } from "../../../chunks/index.js";
import { o as onDestroy } from "../../../chunks/index-server.js";
import "clsx";
import { createTable, createColumnHelper, getSortedRowModel, getPaginationRowModel, getCoreRowModel } from "@tanstack/table-core";
import "../../../chunks/button.js";
import "../../../chunks/client.js";
import "../../../chunks/auth.js";
import "../../../chunks/supabase.js";
function createSvelteTable(options) {
  const resolvedOptions = mergeObjects(
    {
      state: {},
      onStateChange() {
      },
      renderFallbackValue: null,
      mergeOptions: (defaultOptions, options2) => {
        return mergeObjects(defaultOptions, options2);
      }
    },
    options
  );
  const table = createTable(resolvedOptions);
  let state = table.initialState;
  function updateOptions() {
    table.setOptions((prev) => {
      return mergeObjects(prev, options, {
        state: mergeObjects(state, options.state || {}),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onStateChange: (updater) => {
          if (updater instanceof Function) state = updater(state);
          else state = mergeObjects(state, updater);
          options.onStateChange?.(updater);
        }
      });
    });
  }
  updateOptions();
  return table;
}
function mergeObjects(...sources) {
  const resolve = (src) => typeof src === "function" ? src() ?? void 0 : src;
  const findSourceWithKey = (key) => {
    for (let i = sources.length - 1; i >= 0; i--) {
      const obj = resolve(sources[i]);
      if (obj && key in obj) return obj;
    }
    return void 0;
  };
  return new Proxy(/* @__PURE__ */ Object.create(null), {
    get(_, key) {
      const src = findSourceWithKey(key);
      return src?.[key];
    },
    has(_, key) {
      return !!findSourceWithKey(key);
    },
    ownKeys() {
      const all = /* @__PURE__ */ new Set();
      for (const s of sources) {
        const obj = resolve(s);
        if (obj) {
          for (const k of Reflect.ownKeys(obj)) {
            all.add(k);
          }
        }
      }
      return [...all];
    },
    getOwnPropertyDescriptor(_, key) {
      const src = findSourceWithKey(key);
      if (!src) return void 0;
      return {
        configurable: true,
        enumerable: true,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        value: src[key],
        writable: true
      };
    }
  });
}
function _page($$payload, $$props) {
  push();
  const title = "Agents";
  const { data } = $$props;
  onDestroy(() => {
  });
  function mapAgentData(raw) {
    const regInfo = raw.registerInfo || raw.register_info || {};
    const agentCard = raw.agentCard || raw.agent_card || {};
    if (!raw) return { id: "", name: "Agent Not Found", notFound: true };
    return {
      id: raw.id,
      name: regInfo.name || agentCard.name || "Unknown Agent",
      agent_url: regInfo.agent_url || "",
      is_green: regInfo.is_green === true ? "Yes" : "No",
      description: agentCard.description || "",
      status: raw.status || "",
      created_at: raw.created_at || "",
      agent_id: raw.agent_id || "",
      notFound: false,
      raw
    };
  }
  let agents = data.agents.map(mapAgentData);
  let filter = "";
  const columnHelper = createColumnHelper();
  function getAgentAge(created_at) {
    if (!created_at) return "";
    const created = new Date(created_at);
    const now = /* @__PURE__ */ new Date();
    const utcCreated = Date.UTC(created.getUTCFullYear(), created.getUTCMonth(), created.getUTCDate());
    const utcNow = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    const diffMs = utcNow - utcCreated;
    const diffDays = Math.floor(diffMs / (1e3 * 60 * 60 * 24));
    return `${Math.max(0, diffDays)}d`;
  }
  const columns = [
    columnHelper.accessor("name", {
      id: "name",
      header: "Name",
      cell: (cell) => cell.getValue() || "Unknown Agent"
    }),
    columnHelper.accessor("agent_url", {
      id: "agent_url",
      header: "Agent URL",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("launcher_url", {
      id: "launcher_url",
      header: "Launcher URL",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("is_green", {
      id: "is_green",
      header: "Is Green",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("status", {
      id: "status",
      header: "Status",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("description", {
      id: "description",
      header: "Description",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("age", {
      id: "age",
      header: "Age",
      cell: (cell) => getAgentAge(cell.row.original.created_at)
    }),
    columnHelper.accessor("created_at", {
      id: "created_at",
      header: "Created At",
      cell: (cell) => cell.getValue() || ""
    }),
    columnHelper.accessor("agent_id", {
      id: "agent_id",
      header: "Agent ID",
      cell: (cell) => cell.getValue() || ""
    })
  ];
  let pagination = { pageIndex: 0, pageSize: 10 };
  let sorting = [];
  let columnVisibility = { launcher_url: false, agent_id: false, created_at: false };
  createSvelteTable({
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
      if (columnId !== "name") return true;
      const value = row.getValue("name");
      const valueStr = typeof value === "string" ? value : "";
      return valueStr.toLowerCase().includes((filterValue || "").toLowerCase());
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
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    {
      $$payload2.out += "<!--[-->";
      $$payload2.out += `<div class="flex items-center justify-center h-64"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div> <span class="ml-2">Checking authentication...</span></div>`;
    }
    $$payload2.out += `<!--]-->`;
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  bind_props($$props, { title });
  pop();
}
export {
  _page as default
};
