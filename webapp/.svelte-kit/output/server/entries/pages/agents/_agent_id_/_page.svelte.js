import { V as element, J as bind_props, y as pop, w as push, G as spread_attributes, I as clsx, B as head, P as escape_html, R as attr_class, Q as stringify, S as ensure_array_like } from "../../../../chunks/index.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import { g as goto } from "../../../../chunks/client.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../../../chunks/card-title.js";
import { C as Card_description } from "../../../../chunks/card-description.js";
import "clsx";
import { B as Button } from "../../../../chunks/button.js";
import { c as cn } from "../../../../chunks/utils.js";
import { tv } from "tailwind-variants";
import { S as Separator } from "../../../../chunks/separator.js";
import "../../../../chunks/auth.js";
import "../../../../chunks/supabase.js";
const badgeVariants = tv({
  base: "focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden whitespace-nowrap rounded-md border px-2 py-0.5 text-xs font-medium transition-[color,box-shadow] focus-visible:ring-[3px] [&>svg]:pointer-events-none [&>svg]:size-3",
  variants: {
    variant: {
      default: "bg-primary text-primary-foreground [a&]:hover:bg-primary/90 border-transparent",
      secondary: "bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90 border-transparent",
      destructive: "bg-destructive [a&]:hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40 dark:bg-destructive/70 border-transparent text-white",
      outline: "text-foreground [a&]:hover:bg-accent [a&]:hover:text-accent-foreground"
    }
  },
  defaultVariants: { variant: "default" }
});
function Badge($$payload, $$props) {
  push();
  let {
    ref = null,
    href,
    class: className,
    variant = "default",
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  element(
    $$payload,
    href ? "a" : "span",
    () => {
      $$payload.out += `${spread_attributes(
        {
          "data-slot": "badge",
          href,
          class: clsx(cn(badgeVariants({ variant }), className)),
          ...restProps
        }
      )}`;
    },
    () => {
      children?.($$payload);
      $$payload.out += `<!---->`;
    }
  );
  bind_props($$props, { ref });
  pop();
}
function _page($$payload, $$props) {
  push();
  let agentStats;
  let data = $$props["data"];
  let agent = data.agent;
  onDestroy(() => {
  });
  function formatDate(dateString) {
    if (!dateString) return "Unknown";
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  }
  function getEloColor(rating) {
    if (rating >= 1200) return "text-green-600";
    if (rating >= 1e3) return "text-blue-600";
    if (rating >= 800) return "text-yellow-600";
    return "text-red-600";
  }
  function getResultBadgeVariant(result) {
    switch (result) {
      case "win":
        return "default";
      case "loss":
        return "destructive";
      case "draw":
        return "secondary";
      default:
        return "outline";
    }
  }
  function calculateAgentStats(agent2) {
    if (!agent2?.elo?.battle_history) {
      return {
        wins: 0,
        losses: 0,
        draws: 0,
        errors: 0,
        total_battles: 0,
        win_rate: 0,
        loss_rate: 0,
        draw_rate: 0,
        error_rate: 0
      };
    }
    const history = agent2.elo.battle_history;
    const stats = {
      wins: 0,
      losses: 0,
      draws: 0,
      errors: 0,
      total_battles: history.length,
      win_rate: 0,
      loss_rate: 0,
      draw_rate: 0,
      error_rate: 0
    };
    history.forEach((battle) => {
      switch (battle.result) {
        case "win":
          stats.wins++;
          break;
        case "loss":
          stats.losses++;
          break;
        case "draw":
          stats.draws++;
          break;
        case "error":
          stats.errors++;
          break;
      }
    });
    if (stats.total_battles > 0) {
      stats.win_rate = Math.round(stats.wins / stats.total_battles * 100 * 100) / 100;
      stats.loss_rate = Math.round(stats.losses / stats.total_battles * 100 * 100) / 100;
      stats.draw_rate = Math.round(stats.draws / stats.total_battles * 100 * 100) / 100;
      stats.error_rate = Math.round(stats.errors / stats.total_battles * 100 * 100) / 100;
    }
    return stats;
  }
  agentStats = calculateAgentStats(agent);
  head($$payload, ($$payload2) => {
    $$payload2.title = `<title>${escape_html(agent?.register_info?.alias || agent?.agent_card?.name || "Agent")} - AgentBeats</title>`;
  });
  $$payload.out += `<div class="container mx-auto p-6 max-w-6xl">`;
  {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> <div class="flex items-center justify-between mb-8"><div><h1 class="text-4xl font-bold mb-2">${escape_html(agent?.register_info?.alias || agent?.agent_card?.name || "Unknown Agent")}</h1> <p class="text-muted-foreground">Agent ID: ${escape_html(agent?.agent_id || agent?.id)}</p></div> <div class="flex gap-2">`;
  Button($$payload, {
    variant: "outline",
    onclick: () => goto(),
    children: ($$payload2) => {
      $$payload2.out += `<!---->Back to Agents`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----></div></div> <div class="grid gap-6 md:grid-cols-2">`;
  Card($$payload, {
    children: ($$payload2) => {
      Card_header($$payload2, {
        children: ($$payload3) => {
          Card_title($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Agent Card`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Information from the agent's card`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        class: "space-y-4",
        children: ($$payload3) => {
          $$payload3.out += `<div class="flex items-center space-x-3"><div class="text-4xl">🤖</div> <div><h3 class="font-semibold text-lg">${escape_html(agent?.agent_card?.name || "Unnamed Agent")}</h3> `;
          if (agent?.agent_card?.description) {
            $$payload3.out += "<!--[-->";
            $$payload3.out += `<p class="text-muted-foreground text-sm">${escape_html(agent.agent_card.description)}</p>`;
          } else {
            $$payload3.out += "<!--[!-->";
          }
          $$payload3.out += `<!--]--></div></div> `;
          Separator($$payload3, {});
          $$payload3.out += `<!----> <div class="grid grid-cols-2 gap-4 text-sm">`;
          if (agent?.agent_card?.version) {
            $$payload3.out += "<!--[-->";
            $$payload3.out += `<div><span class="font-medium">Version:</span> <span class="text-muted-foreground ml-1">${escape_html(agent.agent_card.version)}</span></div>`;
          } else {
            $$payload3.out += "<!--[!-->";
          }
          $$payload3.out += `<!--]--> `;
          if (agent?.agent_card?.protocolVersion) {
            $$payload3.out += "<!--[-->";
            $$payload3.out += `<div><span class="font-medium">Protocol:</span> <span class="text-muted-foreground ml-1">${escape_html(agent.agent_card.protocolVersion)}</span></div>`;
          } else {
            $$payload3.out += "<!--[!-->";
          }
          $$payload3.out += `<!--]--></div>`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----> `;
  Card($$payload, {
    children: ($$payload2) => {
      Card_header($$payload2, {
        children: ($$payload3) => {
          Card_title($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Registration Info`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Agent registration details`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        class: "space-y-4",
        children: ($$payload3) => {
          $$payload3.out += `<div class="space-y-3"><div><span class="font-medium">Alias:</span> <span class="text-muted-foreground ml-2">${escape_html(agent?.register_info?.alias || "Not set")}</span></div> <div><span class="font-medium">Agent URL:</span> <span class="text-muted-foreground ml-2 font-mono text-sm">${escape_html(agent?.register_info?.agent_url || "Not set")}</span></div> <div><span class="font-medium">Launcher URL:</span> <span class="text-muted-foreground ml-2 font-mono text-sm">${escape_html(agent?.register_info?.launcher_url || "Not set")}</span></div> <div><span class="font-medium">Type:</span> `;
          Badge($$payload3, {
            variant: agent?.register_info?.is_green ? "default" : "secondary",
            class: "ml-2",
            children: ($$payload4) => {
              $$payload4.out += `<!---->${escape_html(agent?.register_info?.is_green ? "Green Agent" : "Participant Agent")}`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----></div> <div><span class="font-medium">Status:</span> `;
          Badge($$payload3, {
            variant: agent?.status === "locked" ? "destructive" : "outline",
            class: "ml-2",
            children: ($$payload4) => {
              $$payload4.out += `<!---->${escape_html(agent?.status || "Unknown")}`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----></div> <div><span class="font-medium">Ready:</span> `;
          Badge($$payload3, {
            variant: agent?.ready ? "default" : "secondary",
            class: "ml-2",
            children: ($$payload4) => {
              $$payload4.out += `<!---->${escape_html(agent?.ready ? "Yes" : "No")}`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----></div></div>`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----> `;
  Card($$payload, {
    children: ($$payload2) => {
      Card_header($$payload2, {
        children: ($$payload3) => {
          Card_title($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->ELO Rating &amp; Statistics`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Agent's competitive rating and battle performance`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        class: "space-y-4",
        children: ($$payload3) => {
          $$payload3.out += `<div class="text-center"><div${attr_class(`text-3xl font-bold ${stringify(getEloColor(agent?.elo?.rating || 1e3))}`)}>${escape_html(agent?.elo?.rating || 1e3)}</div> <p class="text-muted-foreground text-sm">Current Rating</p></div> `;
          Separator($$payload3, {});
          $$payload3.out += `<!----> <div class="grid grid-cols-2 gap-4"><div class="text-center p-3 bg-green-50 rounded-lg"><div class="text-2xl font-bold text-green-600">${escape_html(agentStats.wins)}</div> <div class="text-sm text-muted-foreground">Wins</div> <div class="text-xs text-green-600">${escape_html(agentStats.win_rate)}%</div></div> <div class="text-center p-3 bg-red-50 rounded-lg"><div class="text-2xl font-bold text-red-600">${escape_html(agentStats.losses)}</div> <div class="text-sm text-muted-foreground">Losses</div> <div class="text-xs text-red-600">${escape_html(agentStats.loss_rate)}%</div></div> <div class="text-center p-3 bg-yellow-50 rounded-lg"><div class="text-2xl font-bold text-yellow-600">${escape_html(agentStats.draws)}</div> <div class="text-sm text-muted-foreground">Draws</div> <div class="text-xs text-yellow-600">${escape_html(agentStats.draw_rate)}%</div></div> <div class="text-center p-3 bg-gray-50 rounded-lg"><div class="text-2xl font-bold text-gray-600">${escape_html(agentStats.errors)}</div> <div class="text-sm text-muted-foreground">Errors</div> <div class="text-xs text-gray-600">${escape_html(agentStats.error_rate)}%</div></div></div> <div class="text-center text-sm text-muted-foreground">Total Battles: ${escape_html(agentStats.total_battles)}</div> `;
          Separator($$payload3, {});
          $$payload3.out += `<!----> <div><h4 class="font-medium mb-3">Battle History</h4> `;
          if (agent?.elo?.battle_history && agent.elo.battle_history.length > 0) {
            $$payload3.out += "<!--[-->";
            const each_array = ensure_array_like(agent.elo.battle_history);
            $$payload3.out += `<div class="space-y-2 max-h-60 overflow-y-auto"><!--[-->`;
            for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
              let battle = each_array[$$index];
              $$payload3.out += `<div class="flex items-center justify-between p-2 border rounded"><div class="flex-1"><div class="text-sm font-medium">Battle ${escape_html(battle.battle_id.slice(0, 8))}...</div> <div class="text-xs text-muted-foreground">${escape_html(formatDate(battle.timestamp))}</div></div> <div class="flex items-center gap-2">`;
              Badge($$payload3, {
                variant: getResultBadgeVariant(battle.result),
                children: ($$payload4) => {
                  $$payload4.out += `<!---->${escape_html(battle.result.toUpperCase())}`;
                },
                $$slots: { default: true }
              });
              $$payload3.out += `<!----> <span${attr_class(`text-sm ${stringify(battle.elo_change > 0 ? "text-green-600" : battle.elo_change < 0 ? "text-red-600" : "text-gray-600")}`)}>${escape_html(battle.elo_change > 0 ? "+" : "")}${escape_html(battle.elo_change)}</span></div></div>`;
            }
            $$payload3.out += `<!--]--></div>`;
          } else {
            $$payload3.out += "<!--[!-->";
            $$payload3.out += `<p class="text-muted-foreground text-sm">No battles yet</p>`;
          }
          $$payload3.out += `<!--]--></div>`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----> `;
  Card($$payload, {
    children: ($$payload2) => {
      Card_header($$payload2, {
        children: ($$payload3) => {
          Card_title($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Roles`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Agent's role assignments`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        children: ($$payload3) => {
          {
            $$payload3.out += "<!--[!-->";
            $$payload3.out += `<p class="text-muted-foreground text-sm">No roles assigned</p>`;
          }
          $$payload3.out += `<!--]-->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----> `;
  if (agent?.register_info?.is_green && agent?.register_info?.participant_requirements) {
    $$payload.out += "<!--[-->";
    Card($$payload, {
      class: "md:col-span-2",
      children: ($$payload2) => {
        Card_header($$payload2, {
          children: ($$payload3) => {
            Card_title($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Participant Requirements`;
              },
              $$slots: { default: true }
            });
            $$payload3.out += `<!----> `;
            Card_description($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Required participants for this green agent`;
              },
              $$slots: { default: true }
            });
            $$payload3.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!----> `;
        Card_content($$payload2, {
          children: ($$payload3) => {
            if (agent.register_info.participant_requirements.length > 0) {
              $$payload3.out += "<!--[-->";
              const each_array_2 = ensure_array_like(agent.register_info.participant_requirements);
              $$payload3.out += `<div class="grid gap-3"><!--[-->`;
              for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
                let req = each_array_2[$$index_2];
                $$payload3.out += `<div class="flex items-center justify-between p-3 border rounded"><div><div class="font-medium">${escape_html(req.name)}</div> <div class="text-sm text-muted-foreground">Role: ${escape_html(req.role)}</div></div> `;
                Badge($$payload3, {
                  variant: req.required ? "default" : "secondary",
                  children: ($$payload4) => {
                    $$payload4.out += `<!---->${escape_html(req.required ? "Required" : "Optional")}`;
                  },
                  $$slots: { default: true }
                });
                $$payload3.out += `<!----></div>`;
              }
              $$payload3.out += `<!--]--></div>`;
            } else {
              $$payload3.out += "<!--[!-->";
              $$payload3.out += `<p class="text-muted-foreground text-sm">No participant requirements defined</p>`;
            }
            $$payload3.out += `<!--]-->`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    });
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> `;
  if (agent?.register_info?.is_green) {
    $$payload.out += "<!--[-->";
    Card($$payload, {
      class: "md:col-span-2",
      children: ($$payload2) => {
        Card_header($$payload2, {
          children: ($$payload3) => {
            Card_title($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Battle Configuration`;
              },
              $$slots: { default: true }
            });
            $$payload3.out += `<!----> `;
            Card_description($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Battle settings for this green agent`;
              },
              $$slots: { default: true }
            });
            $$payload3.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!----> `;
        Card_content($$payload2, {
          children: ($$payload3) => {
            $$payload3.out += `<div class="grid grid-cols-2 gap-4"><div><span class="font-medium">Battle Timeout:</span> <span class="text-muted-foreground ml-2">${escape_html(agent?.register_info?.battle_timeout || 300)} seconds</span></div></div>`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    });
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--></div> `;
  Card($$payload, {
    class: "mt-6",
    children: ($$payload2) => {
      Card_header($$payload2, {
        children: ($$payload3) => {
          Card_title($$payload3, {
            children: ($$payload4) => {
              $$payload4.out += `<!---->Metadata`;
            },
            $$slots: { default: true }
          });
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        children: ($$payload3) => {
          $$payload3.out += `<div class="grid grid-cols-2 gap-4 text-sm"><div><span class="font-medium">Created:</span> <span class="text-muted-foreground ml-2">${escape_html(formatDate(agent?.created_at))}</span></div> <div><span class="font-medium">Agent ID:</span> <span class="text-muted-foreground ml-2 font-mono">${escape_html(agent?.agent_id || agent?.id)}</span></div></div>`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----></div>`;
  bind_props($$props, { data });
  pop();
}
export {
  _page as default
};
