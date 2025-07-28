import { G as spread_attributes, I as clsx, J as bind_props, y as pop, w as push, W as fallback, P as escape_html, S as ensure_array_like, A as attr, R as attr_class, Q as stringify } from "../../../chunks/index.js";
import { o as onDestroy } from "../../../chunks/index-server.js";
import "../../../chunks/client.js";
import { B as Battle_card_ongoing } from "../../../chunks/battle-card-ongoing.js";
import { C as Card, a as Card_header } from "../../../chunks/card-title.js";
import "clsx";
import { c as cn } from "../../../chunks/utils.js";
import "../../../chunks/auth.js";
import "../../../chunks/supabase.js";
function Card_footer($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  $$payload.out += `<div${spread_attributes(
    {
      "data-slot": "card-footer",
      class: clsx(cn("[.border-t]:pt-6 flex items-center px-6", className)),
      ...restProps
    }
  )}>`;
  children?.($$payload);
  $$payload.out += `<!----></div>`;
  bind_props($$props, { ref });
  pop();
}
function Battle_card_finished($$payload, $$props) {
  push();
  let battle = fallback($$props["battle"], null);
  let battleId = fallback($$props["battleId"], null);
  let opponentNames = [];
  let durationStr = "";
  function shortId(id) {
    return id ? id.slice(0, 8) : "";
  }
  function timeAgo(dt) {
    if (!dt) return "";
    let dtFixed = dt;
    if (dt && !dt.endsWith("Z")) {
      dtFixed = dt + "Z";
    }
    const now = Date.now();
    const then = new Date(dtFixed).getTime();
    const diff = Math.floor((now - then) / 1e3);
    if (diff < 0) {
      const abs = Math.abs(diff);
      if (abs < 60) return `in ${abs}s`;
      if (abs < 3600) return `in ${Math.floor(abs / 60)}m`;
      if (abs < 86400) return `in ${Math.floor(abs / 3600)}h`;
      return `in ${Math.floor(abs / 86400)}d`;
    }
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }
  function displayTime(battle2) {
    let dt = "";
    if (battle2?.result?.finish_time) {
      dt = battle2.result.finish_time;
    } else if (battle2?.created_at || battle2?.createdAt) {
      dt = battle2.created_at || battle2.createdAt;
    }
    if (dt && !dt.endsWith("Z")) dt = dt + "Z";
    if (dt) {
      const d = new Date(dt);
      return d.toLocaleString();
    }
    return "";
  }
  function getEndTime(battle2) {
    return battle2?.result?.finish_time || battle2?.created_at || battle2?.createdAt || "";
  }
  function stateColor(state) {
    switch ((state || "").toLowerCase()) {
      case "pending":
        return "text-yellow-600";
      case "queued":
        return "text-yellow-600";
      case "running":
        return "text-blue-600";
      case "finished":
        return "text-green-600";
      case "error":
        return "text-red-600";
      default:
        return "text-muted-foreground";
    }
  }
  function winnerText(battle2) {
    if (battle2?.result?.winner === "draw") return "Draw";
    if (battle2?.result?.winner) return `${battle2.result.winner} Victory`;
    if (battle2?.state === "error") return battle2?.error ? `Error: ${battle2.error}` : "Error";
    return "";
  }
  function getOpponentParts(name) {
    const m = name.match(/^(.*?) \((.*?)\)$/);
    return m ? [m[1], m[2]] : null;
  }
  {
    $$payload.out += "<!--[!-->";
    {
      $$payload.out += "<!--[!-->";
      if (battle) {
        $$payload.out += "<!--[-->";
        Card($$payload, {
          class: "w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4",
          children: ($$payload2) => {
            Card_header($$payload2, {
              class: "pb-2 px-2",
              children: ($$payload3) => {
                $$payload3.out += `<div class="flex flex-row items-center justify-between w-full gap-1 mt-3"><div class="flex flex-col items-start gap-2"><span class="font-bold text-sm">${escape_html("Loading...")}</span> <span class="text-xs text-muted-foreground font-mono select-all">${escape_html(battle.green_agent_id || battle.greenAgentId || "Unknown")}</span> <span class="text-xs text-muted-foreground">Host / Green Agent</span> `;
                if (opponentNames.length > 0) {
                  $$payload3.out += "<!--[-->";
                  const each_array = ensure_array_like(opponentNames);
                  $$payload3.out += `<div class="mt-3"><span class="text-xs text-muted-foreground">Opponents:</span> <ul class="ml-4 mt-2 list-disc space-y-1"><!--[-->`;
                  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                    let opponentName = each_array[$$index];
                    $$payload3.out += `<li class="flex flex-col gap-0.5">`;
                    if (getOpponentParts(opponentName)) {
                      $$payload3.out += "<!--[-->";
                      $$payload3.out += `<span><span class="text-xs text-muted-foreground">${escape_html(getOpponentParts(opponentName)?.[0])}</span> <span class="text-xs text-muted-foreground">(${escape_html(getOpponentParts(opponentName)?.[1])})</span></span>`;
                    } else {
                      $$payload3.out += "<!--[!-->";
                      $$payload3.out += `<span class="text-xs text-muted-foreground">${escape_html(opponentName)}</span>`;
                    }
                    $$payload3.out += `<!--]--></li>`;
                  }
                  $$payload3.out += `<!--]--></ul></div>`;
                } else {
                  $$payload3.out += "<!--[!-->";
                  if (battle.opponents && battle.opponents.length > 0) {
                    $$payload3.out += "<!--[-->";
                    $$payload3.out += `<div class="mt-2"><span class="text-xs text-muted-foreground">Opponents: Loading...</span></div>`;
                  } else {
                    $$payload3.out += "<!--[!-->";
                    $$payload3.out += `<div class="mt-2"><span class="text-xs text-muted-foreground">No opponents found</span></div>`;
                  }
                  $$payload3.out += `<!--]-->`;
                }
                $$payload3.out += `<!--]--></div> <div class="flex flex-col items-end gap-1"><span class="text-xs font-mono text-muted-foreground select-all"${attr("title", battle.battle_id || battle.id)}>Battle #${escape_html(shortId(battle.battle_id || battle.id))}</span> <span class="text-xs text-muted-foreground">${escape_html(displayTime(battle))}</span> <span class="text-xs text-muted-foreground italic">${escape_html(timeAgo(getEndTime(battle)))}</span></div></div>`;
              },
              $$slots: { default: true }
            });
            $$payload2.out += `<!----> `;
            Card_footer($$payload2, {
              class: "pt-4 flex flex-row items-between justify-between w-full mb-0 px-2",
              children: ($$payload3) => {
                $$payload3.out += `<div class="flex flex-row items-center gap-3"><span${attr_class(`text-xs font-semibold ${stringify(stateColor(battle.state))}`)}>${escape_html(battle.state)}</span> <span class="text-xs text-muted-foreground">${escape_html(winnerText(battle))}</span> `;
                if (battle.result && battle.result.finish_time) {
                  $$payload3.out += "<!--[-->";
                  $$payload3.out += `<span class="text-xs text-muted-foreground">Duration: ${escape_html(durationStr)}</span>`;
                } else {
                  $$payload3.out += "<!--[!-->";
                }
                $$payload3.out += `<!--]--></div> <span class="text-[10px] text-muted-foreground font-mono select-all">Battle ID: ${escape_html(battle.battle_id || battle.id)}</span>`;
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
      $$payload.out += `<!--]-->`;
    }
    $$payload.out += `<!--]-->`;
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { battle, battleId });
  pop();
}
function _page($$payload, $$props) {
  push();
  let data = $$props["data"];
  data.battles;
  onDestroy(() => {
  });
  let ongoingBattles = [];
  let pastBattles = [];
  let ongoingToShow = 3;
  let pastToShow = 10;
  $$payload.out += `<div class="w-full flex flex-col items-center justify-center mt-10 mb-8"><h1 class="text-2xl font-bold text-center mb-8">Battles</h1> <button type="button" class="flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-base font-semibold shadow hover:bg-primary/90 transition cursor-pointer">Stage a Battle</button></div> <div class="flex flex-1 flex-col items-center justify-center min-h-[80vh] w-full"><div class="flex flex-1 flex-col gap-2 items-center justify-center w-full"><div class="flex flex-col gap-10 py-4 md:gap-12 md:py-6 w-full items-center justify-center">`;
  if (ongoingBattles.length > 0) {
    $$payload.out += "<!--[-->";
    const each_array = ensure_array_like(ongoingBattles.slice(0, ongoingToShow));
    $$payload.out += `<div class="w-full max-w-4xl flex flex-col items-center"><h2 class="text-2xl font-bold text-center mb-10 mt-10">Ongoing Battles</h2> <div class="flex flex-col gap-4 w-full"><!--[-->`;
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let battle = each_array[$$index];
      $$payload.out += `<button type="button" class="cursor-pointer w-full">`;
      Battle_card_ongoing($$payload, { battleId: battle.battle_id });
      $$payload.out += `<!----></button>`;
    }
    $$payload.out += `<!--]--> `;
    if (ongoingBattles.length > ongoingToShow) {
      $$payload.out += "<!--[-->";
      $$payload.out += `<button type="button" class="mt-2 px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium">View More</button>`;
    } else {
      $$payload.out += "<!--[!-->";
    }
    $$payload.out += `<!--]--></div></div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> `;
  if (pastBattles.length > 0) {
    $$payload.out += "<!--[-->";
    const each_array_1 = ensure_array_like(pastBattles.slice(0, pastToShow));
    $$payload.out += `<div class="w-full max-w-4xl flex flex-col items-center"><h2 class="text-2xl font-bold text-center mb-8 mt-8">Past Battles</h2> <div class="flex flex-col gap-4 w-full"><!--[-->`;
    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
      let battle = each_array_1[$$index_1];
      $$payload.out += `<button type="button" class="cursor-pointer w-full">`;
      Battle_card_finished($$payload, { battleId: battle.battle_id });
      $$payload.out += `<!----></button>`;
    }
    $$payload.out += `<!--]--> `;
    if (pastBattles.length > pastToShow) {
      $$payload.out += "<!--[-->";
      $$payload.out += `<button type="button" class="mt-2 px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium">View More</button>`;
    } else {
      $$payload.out += "<!--[!-->";
    }
    $$payload.out += `<!--]--></div></div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--> `;
  if (ongoingBattles.length === 0 && pastBattles.length === 0) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="text-center text-muted-foreground">No battles found.</div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--></div></div></div>`;
  bind_props($$props, { data });
  pop();
}
export {
  _page as default
};
