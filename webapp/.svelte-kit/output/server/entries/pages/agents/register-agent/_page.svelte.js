import { N as copy_payload, O as assign_payload, J as bind_props, y as pop, w as push, B as head, P as escape_html, A as attr, S as ensure_array_like } from "../../../../chunks/index.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import { g as goto } from "../../../../chunks/client.js";
import { f as fetchAgentCard, a as analyzeAgentCard } from "../../../../chunks/agents.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../../../chunks/card-title.js";
import { C as Card_description } from "../../../../chunks/card-description.js";
import "clsx";
import { B as Button } from "../../../../chunks/button.js";
import { L as Label } from "../../../../chunks/label.js";
import { I as Input } from "../../../../chunks/input.js";
import "../../../../chunks/auth.js";
import "../../../../chunks/supabase.js";
function _page($$payload, $$props) {
  push();
  const { $$slots, $$events, ...data } = $$props;
  onDestroy(() => {
  });
  let formData = {
    alias: "",
    agent_url: "",
    launcher_url: "",
    is_green: false,
    participant_requirements: [],
    battle_timeout: 300,
    roles: {}
    // Add roles as required field
  };
  let isLoadingAgentCard = false;
  let agentCardError = null;
  let agentCard = null;
  let canRegister = true;
  let isAnalyzing = false;
  let analysisError = null;
  function addParticipantRequirement() {
    formData.participant_requirements = [
      ...formData.participant_requirements,
      { role: "", name: "", required: false }
    ];
  }
  function removeParticipantRequirement(index) {
    formData.participant_requirements = formData.participant_requirements.filter((_, i) => i !== index);
  }
  async function loadAgentCard() {
    if (!formData.agent_url.trim()) {
      agentCard = null;
      agentCardError = null;
      canRegister = true;
      return;
    }
    try {
      isLoadingAgentCard = true;
      agentCardError = null;
      agentCard = await fetchAgentCard(formData.agent_url);
      canRegister = true;
      if (!formData.alias.trim() && agentCard?.name) {
        formData.alias = agentCard.name;
      }
      await analyzeAgentCardAutomatically();
    } catch (err) {
      agentCardError = err instanceof Error ? err.message : "Failed to load agent card";
      agentCard = null;
      canRegister = false;
    } finally {
      isLoadingAgentCard = false;
    }
  }
  async function analyzeAgentCardAutomatically() {
    if (!agentCard) return;
    try {
      isAnalyzing = true;
      analysisError = null;
      const analysis = await analyzeAgentCard(agentCard);
      if (analysis.is_green) {
        formData.is_green = true;
        formData.participant_requirements = analysis.participant_requirements || [];
        formData.battle_timeout = analysis.battle_timeout || 300;
      }
    } catch (err) {
      analysisError = err instanceof Error ? err.message : "Failed to analyze agent card";
      console.error("Agent card analysis failed:", err);
    } finally {
      isAnalyzing = false;
    }
  }
  function handleAgentUrlBlur() {
    loadAgentCard();
  }
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    head($$payload2, ($$payload3) => {
      $$payload3.title = `<title>Register Agent - AgentBeats</title>`;
    });
    $$payload2.out += `<div class="container mx-auto p-6 max-w-6xl"><div class="text-center mb-8"><h1 class="text-4xl font-bold mb-6">Register New Agent</h1> <p class="text-muted-foreground">Register a new agent to participate in battles</p></div> `;
    {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]--> `;
    {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]--> `;
    Card($$payload2, {
      class: "mb-6",
      children: ($$payload3) => {
        Card_header($$payload3, {
          children: ($$payload4) => {
            Card_title($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Agent Card`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Preview of the agent information`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!----> `;
        Card_content($$payload3, {
          children: ($$payload4) => {
            if (isLoadingAgentCard) {
              $$payload4.out += "<!--[-->";
              $$payload4.out += `<div class="flex flex-col items-center justify-center py-8 space-y-4"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div> <div class="text-muted-foreground">Loading agent card...</div></div>`;
            } else {
              $$payload4.out += "<!--[!-->";
              if (agentCardError) {
                $$payload4.out += "<!--[-->";
                $$payload4.out += `<div class="flex flex-col items-center justify-center py-8 space-y-4"><div class="text-6xl">🤖</div> <div class="text-destructive text-center"><div class="font-medium">Agent Card Error</div> <div class="text-sm mt-1">${escape_html(agentCardError)}</div></div></div>`;
              } else {
                $$payload4.out += "<!--[!-->";
                if (agentCard) {
                  $$payload4.out += "<!--[-->";
                  $$payload4.out += `<div class="space-y-4"><div class="flex items-center space-x-3"><div class="text-4xl">🤖</div> <div><h3 class="font-semibold text-lg">${escape_html(agentCard.name || "Unnamed Agent")}</h3> `;
                  if (agentCard.description) {
                    $$payload4.out += "<!--[-->";
                    $$payload4.out += `<p class="text-muted-foreground text-sm">${escape_html(agentCard.description)}</p>`;
                  } else {
                    $$payload4.out += "<!--[!-->";
                  }
                  $$payload4.out += `<!--]--></div></div> <div class="grid grid-cols-1 md:grid-cols-2 gap-4">`;
                  if (agentCard.version) {
                    $$payload4.out += "<!--[-->";
                    $$payload4.out += `<div class="text-sm text-muted-foreground"><span class="font-medium">Version:</span> ${escape_html(agentCard.version)}</div>`;
                  } else {
                    $$payload4.out += "<!--[!-->";
                  }
                  $$payload4.out += `<!--]--> `;
                  if (agentCard.protocolVersion) {
                    $$payload4.out += "<!--[-->";
                    $$payload4.out += `<div class="text-sm text-muted-foreground"><span class="font-medium">Protocol:</span> ${escape_html(agentCard.protocolVersion)}</div>`;
                  } else {
                    $$payload4.out += "<!--[!-->";
                  }
                  $$payload4.out += `<!--]--></div> `;
                  if (agentCard.capabilities && typeof agentCard.capabilities === "object") {
                    $$payload4.out += "<!--[-->";
                    const each_array = ensure_array_like(Object.entries(agentCard.capabilities));
                    $$payload4.out += `<div><h4 class="font-medium text-sm mb-2">Capabilities:</h4> <div class="flex flex-wrap gap-1"><!--[-->`;
                    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                      let [key, value] = each_array[$$index];
                      $$payload4.out += `<span class="px-2 py-1 bg-secondary text-secondary-foreground rounded-md text-xs">${escape_html(key)}: ${escape_html(typeof value === "boolean" ? value ? "Yes" : "No" : value)}</span>`;
                    }
                    $$payload4.out += `<!--]--></div></div>`;
                  } else {
                    $$payload4.out += "<!--[!-->";
                  }
                  $$payload4.out += `<!--]--> `;
                  if (agentCard.skills && agentCard.skills.length > 0) {
                    $$payload4.out += "<!--[-->";
                    const each_array_1 = ensure_array_like(agentCard.skills);
                    $$payload4.out += `<div><h4 class="font-medium text-sm mb-2">Skills:</h4> <div class="flex flex-wrap gap-1"><!--[-->`;
                    for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
                      let skill = each_array_1[$$index_1];
                      $$payload4.out += `<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs">${escape_html(skill.name)}</span>`;
                    }
                    $$payload4.out += `<!--]--></div></div>`;
                  } else {
                    $$payload4.out += "<!--[!-->";
                  }
                  $$payload4.out += `<!--]--></div>`;
                } else {
                  $$payload4.out += "<!--[!-->";
                  $$payload4.out += `<div class="flex flex-col items-center justify-center py-8 space-y-4"><div class="text-6xl">🤖</div> <div class="text-muted-foreground text-center"><div class="font-medium">Agent Card</div> <div class="text-sm">Enter an agent URL to load the card</div></div></div>`;
                }
                $$payload4.out += `<!--]-->`;
              }
              $$payload4.out += `<!--]-->`;
            }
            $$payload4.out += `<!--]-->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!---->`;
      },
      $$slots: { default: true }
    });
    $$payload2.out += `<!----> <div class="grid gap-6 md:grid-cols-2">`;
    Card($$payload2, {
      children: ($$payload3) => {
        Card_header($$payload3, {
          children: ($$payload4) => {
            Card_title($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Agent Information`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Enter the details for your new agent`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!----> `;
        Card_content($$payload3, {
          children: ($$payload4) => {
            $$payload4.out += `<form class="space-y-4"><div class="space-y-2">`;
            Label($$payload4, {
              for: "agent_url",
              children: ($$payload5) => {
                $$payload5.out += `<!---->Agent URL`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Input($$payload4, {
              id: "agent_url",
              type: "text",
              placeholder: "http://localhost:6001",
              onblur: handleAgentUrlBlur,
              required: true,
              get value() {
                return formData.agent_url;
              },
              set value($$value) {
                formData.agent_url = $$value;
                $$settled = false;
              }
            });
            $$payload4.out += `<!----> `;
            if (isLoadingAgentCard) {
              $$payload4.out += "<!--[-->";
              $$payload4.out += `<div class="text-sm text-muted-foreground">Loading agent card...</div>`;
            } else {
              $$payload4.out += "<!--[!-->";
            }
            $$payload4.out += `<!--]--></div> <div class="space-y-2">`;
            Label($$payload4, {
              for: "launcher_url",
              children: ($$payload5) => {
                $$payload5.out += `<!---->Launcher URL`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Input($$payload4, {
              id: "launcher_url",
              type: "text",
              placeholder: "http://localhost:6001/launcher",
              required: true,
              get value() {
                return formData.launcher_url;
              },
              set value($$value) {
                formData.launcher_url = $$value;
                $$settled = false;
              }
            });
            $$payload4.out += `<!----></div> <div class="space-y-2">`;
            Label($$payload4, {
              for: "name",
              children: ($$payload5) => {
                $$payload5.out += `<!---->Agent Alias (Optional)`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Input($$payload4, {
              id: "name",
              type: "text",
              placeholder: agentCard?.name || "Will use agent card name if not provided",
              get value() {
                return formData.alias;
              },
              set value($$value) {
                formData.alias = $$value;
                $$settled = false;
              }
            });
            $$payload4.out += `<!----> <div class="text-xs text-muted-foreground">Leave empty to use the name from agent card: ${escape_html(agentCard?.name || "Not loaded yet")}</div></div> <div class="flex gap-2 pt-4">`;
            Button($$payload4, {
              type: "submit",
              disabled: !canRegister || false,
              children: ($$payload5) => {
                $$payload5.out += `<!---->${escape_html("Register Agent")}`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Button($$payload4, {
              variant: "outline",
              type: "button",
              onclick: () => goto(),
              children: ($$payload5) => {
                $$payload5.out += `<!---->Cancel`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----></div></form>`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!---->`;
      },
      $$slots: { default: true }
    });
    $$payload2.out += `<!----> `;
    Card($$payload2, {
      children: ($$payload3) => {
        Card_header($$payload3, {
          children: ($$payload4) => {
            Card_title($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Agent Type &amp; Requirements`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                if (isAnalyzing) {
                  $$payload5.out += "<!--[-->";
                  $$payload5.out += `Analyzing agent card and suggesting configuration...`;
                } else {
                  $$payload5.out += "<!--[!-->";
                  $$payload5.out += `Configure agent type and participant requirements`;
                }
                $$payload5.out += `<!--]-->`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!----> `;
        Card_content($$payload3, {
          class: "space-y-6",
          children: ($$payload4) => {
            if (isAnalyzing) {
              $$payload4.out += "<!--[-->";
              $$payload4.out += `<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div> <span class="ml-2 text-muted-foreground">Analyzing agent card...</span></div>`;
            } else {
              $$payload4.out += "<!--[!-->";
              $$payload4.out += `<div class="flex items-center gap-2"><input type="checkbox" id="is_green"${attr("checked", formData.is_green, true)}/> `;
              Label($$payload4, {
                for: "is_green",
                children: ($$payload5) => {
                  $$payload5.out += `<!---->Green Agent (Battle Initiator)`;
                },
                $$slots: { default: true }
              });
              $$payload4.out += `<!----></div> `;
              if (formData.is_green) {
                $$payload4.out += "<!--[-->";
                $$payload4.out += `<div class="border-t pt-4"><h4 class="font-medium mb-2">Participant Requirements</h4> `;
                Button($$payload4, {
                  variant: "outline",
                  onclick: addParticipantRequirement,
                  class: "mb-4",
                  children: ($$payload5) => {
                    $$payload5.out += `<!---->Add Requirement`;
                  },
                  $$slots: { default: true }
                });
                $$payload4.out += `<!----> `;
                if (formData.participant_requirements.length > 0) {
                  $$payload4.out += "<!--[-->";
                  const each_array_2 = ensure_array_like(formData.participant_requirements);
                  $$payload4.out += `<div class="space-y-4"><!--[-->`;
                  for (let index = 0, $$length = each_array_2.length; index < $$length; index++) {
                    let requirement = each_array_2[index];
                    $$payload4.out += `<div class="flex gap-2 items-center">`;
                    Input($$payload4, {
                      placeholder: "Role",
                      class: "w-1/3",
                      get value() {
                        return requirement.role;
                      },
                      set value($$value) {
                        requirement.role = $$value;
                        $$settled = false;
                      }
                    });
                    $$payload4.out += `<!----> `;
                    Input($$payload4, {
                      placeholder: "Name",
                      class: "w-1/3",
                      get value() {
                        return requirement.name;
                      },
                      set value($$value) {
                        requirement.name = $$value;
                        $$settled = false;
                      }
                    });
                    $$payload4.out += `<!----> <div class="flex items-center gap-1"><input type="checkbox"${attr("checked", requirement.required, true)}${attr("id", `required-${index}`)}/> `;
                    Label($$payload4, {
                      for: `required-${index}`,
                      children: ($$payload5) => {
                        $$payload5.out += `<!---->Required`;
                      },
                      $$slots: { default: true }
                    });
                    $$payload4.out += `<!----></div> `;
                    Button($$payload4, {
                      variant: "outline",
                      size: "sm",
                      onclick: () => removeParticipantRequirement(index),
                      children: ($$payload5) => {
                        $$payload5.out += `<!---->Remove`;
                      },
                      $$slots: { default: true }
                    });
                    $$payload4.out += `<!----></div>`;
                  }
                  $$payload4.out += `<!--]--></div>`;
                } else {
                  $$payload4.out += "<!--[!-->";
                  $$payload4.out += `<p class="text-muted-foreground text-sm">No participant requirements defined</p>`;
                }
                $$payload4.out += `<!--]--></div> <div class="border-t pt-4"><h4 class="font-medium mb-2">Battle Configuration</h4> <div class="space-y-2">`;
                Label($$payload4, {
                  for: "battle_timeout",
                  children: ($$payload5) => {
                    $$payload5.out += `<!---->Battle Timeout (seconds)`;
                  },
                  $$slots: { default: true }
                });
                $$payload4.out += `<!----> `;
                Input($$payload4, {
                  id: "battle_timeout",
                  type: "number",
                  placeholder: "300",
                  min: "1",
                  class: "w-full",
                  get value() {
                    return formData.battle_timeout;
                  },
                  set value($$value) {
                    formData.battle_timeout = $$value;
                    $$settled = false;
                  }
                });
                $$payload4.out += `<!----> <div class="text-xs text-muted-foreground">Maximum time allowed for the battle to complete</div></div></div>`;
              } else {
                $$payload4.out += "<!--[!-->";
                $$payload4.out += `<p class="text-muted-foreground text-sm">This will be a regular participant agent</p>`;
              }
              $$payload4.out += `<!--]--> `;
              if (analysisError) {
                $$payload4.out += "<!--[-->";
                $$payload4.out += `<div class="text-destructive text-sm">AI Analysis Error: ${escape_html(analysisError)}</div>`;
              } else {
                $$payload4.out += "<!--[!-->";
              }
              $$payload4.out += `<!--]-->`;
            }
            $$payload4.out += `<!--]-->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!---->`;
      },
      $$slots: { default: true }
    });
    $$payload2.out += `<!----></div> <details class="mt-8"><summary class="text-lg font-medium cursor-pointer">Debug: Form Data</summary> <div class="mt-4 p-4 bg-muted rounded-lg"><pre class="text-xs overflow-auto max-h-60">${escape_html(JSON.stringify(formData, null, 2))}</pre></div></details></div>`;
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  bind_props($$props, { data });
  pop();
}
export {
  _page as default
};
