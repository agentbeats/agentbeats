import { T as store_get, N as copy_payload, O as assign_payload, U as unsubscribe_stores, y as pop, w as push, P as escape_html, J as bind_props } from "../../../chunks/index.js";
import { o as onDestroy } from "../../../chunks/index-server.js";
import "../../../chunks/client.js";
import "../../../chunks/auth.js";
import { u as user, e as error, l as loading } from "../../../chunks/supabase.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../../chunks/card-title.js";
import { C as Card_description } from "../../../chunks/card-description.js";
import "clsx";
function User_profile($$payload, $$props) {
  push();
  var $$store_subs;
  if (store_get($$store_subs ??= {}, "$user", user) && true) {
    store_get($$store_subs ??= {}, "$user", user).email || "";
    store_get($$store_subs ??= {}, "$user", user).user_metadata?.name || "";
  }
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    Card($$payload2, {
      children: ($$payload3) => {
        Card_header($$payload3, {
          children: ($$payload4) => {
            Card_title($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->User Profile`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Manage your account settings and preferences`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!---->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!----> `;
        Card_content($$payload3, {
          class: "space-y-4",
          children: ($$payload4) => {
            if (store_get($$store_subs ??= {}, "$user", user)) {
              $$payload4.out += "<!--[-->";
              $$payload4.out += `<div class="space-y-4">`;
              {
                $$payload4.out += "<!--[-->";
                $$payload4.out += `<div class="space-y-3"><div class="flex justify-between items-center"><div><p class="text-sm font-medium">Email</p> <p class="text-sm text-gray-600">${escape_html(store_get($$store_subs ??= {}, "$user", user).email)}</p></div></div> `;
                if (store_get($$store_subs ??= {}, "$user", user).user_metadata?.name) {
                  $$payload4.out += "<!--[-->";
                  $$payload4.out += `<div class="flex justify-between items-center"><div><p class="text-sm font-medium">Name</p> <p class="text-sm text-gray-600">${escape_html(store_get($$store_subs ??= {}, "$user", user).user_metadata.name)}</p></div></div>`;
                } else {
                  $$payload4.out += "<!--[!-->";
                }
                $$payload4.out += `<!--]--> <div class="flex justify-between items-center"><div><p class="text-sm font-medium">Provider</p> <p class="text-sm text-gray-600">${escape_html(store_get($$store_subs ??= {}, "$user", user).app_metadata?.provider || "Email")}</p></div></div> <div class="flex justify-between items-center"><div><p class="text-sm font-medium">Member Since</p> <p class="text-sm text-gray-600">${escape_html(new Date(store_get($$store_subs ??= {}, "$user", user).created_at).toLocaleDateString())}</p></div></div> <div class="flex gap-2 pt-2"><button class="px-3 py-1 bg-primary text-primary-foreground text-sm rounded-md hover:bg-primary/90">Edit Profile</button> <button class="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-md hover:bg-secondary/80">Reset Password</button></div></div>`;
              }
              $$payload4.out += `<!--]--> `;
              if (store_get($$store_subs ??= {}, "$authError", error)) {
                $$payload4.out += "<!--[-->";
                $$payload4.out += `<div class="text-red-600 text-sm">${escape_html(store_get($$store_subs ??= {}, "$authError", error)?.message)}</div>`;
              } else {
                $$payload4.out += "<!--[!-->";
              }
              $$payload4.out += `<!--]--> `;
              {
                $$payload4.out += "<!--[!-->";
              }
              $$payload4.out += `<!--]--></div>`;
            } else {
              $$payload4.out += "<!--[!-->";
              $$payload4.out += `<div class="text-center text-gray-600"><p>No user data available</p></div>`;
            }
            $$payload4.out += `<!--]-->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!---->`;
      },
      $$slots: { default: true }
    });
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  if ($$store_subs) unsubscribe_stores($$store_subs);
  pop();
}
function _page($$payload, $$props) {
  push();
  var $$store_subs;
  const title = "Dashboard";
  onDestroy(() => {
  });
  $$payload.out += `<main class="flex-1 p-6 flex flex-col items-center justify-start">`;
  if (store_get($$store_subs ??= {}, "$loading", loading)) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="flex items-center justify-center h-64"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div> <span class="ml-2">Loading...</span></div>`;
  } else {
    $$payload.out += "<!--[!-->";
    $$payload.out += `<div class="w-full max-w-6xl mx-auto"><div class="flex justify-between items-center mb-6"><h2 class="text-2xl font-bold">Dashboard</h2> <div class="flex items-center gap-4">`;
    if (store_get($$store_subs ??= {}, "$user", user)) {
      $$payload.out += "<!--[-->";
      $$payload.out += `<span class="text-sm text-gray-600">Welcome, ${escape_html(store_get($$store_subs ??= {}, "$user", user).user_metadata?.name || store_get($$store_subs ??= {}, "$user", user).email)}</span> <button class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">Logout</button>`;
    } else {
      $$payload.out += "<!--[!-->";
      $$payload.out += `<button class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">Sign In</button>`;
    }
    $$payload.out += `<!--]--></div></div> <div class="grid grid-cols-1 lg:grid-cols-3 gap-6"><div class="lg:col-span-1">`;
    if (store_get($$store_subs ??= {}, "$user", user)) {
      $$payload.out += "<!--[-->";
      User_profile($$payload);
    } else {
      $$payload.out += "<!--[!-->";
      Card($$payload, {
        children: ($$payload2) => {
          Card_header($$payload2, {
            children: ($$payload3) => {
              Card_title($$payload3, {
                children: ($$payload4) => {
                  $$payload4.out += `<!---->Get Started`;
                },
                $$slots: { default: true }
              });
              $$payload3.out += `<!----> `;
              Card_description($$payload3, {
                children: ($$payload4) => {
                  $$payload4.out += `<!---->Sign in to access your profile and battle stats!`;
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
              $$payload3.out += `<button class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">Sign In to Continue!</button>`;
            },
            $$slots: { default: true }
          });
          $$payload2.out += `<!---->`;
        },
        $$slots: { default: true }
      });
    }
    $$payload.out += `<!--]--></div> <div class="lg:col-span-2 space-y-6">`;
    Card($$payload, {
      children: ($$payload2) => {
        Card_header($$payload2, {
          children: ($$payload3) => {
            Card_title($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Welcome to AgentBeats!`;
              },
              $$slots: { default: true }
            });
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!----> `;
        Card_content($$payload2, {
          children: ($$payload3) => {
            if (store_get($$store_subs ??= {}, "$user", user)) {
              $$payload3.out += "<!--[-->";
              $$payload3.out += `<p class="text-muted-foreground">Here's your dashboard! Here, you'll see your battle history, agents, and ranking (do later).</p>`;
            } else {
              $$payload3.out += "<!--[!-->";
              $$payload3.out += `<p class="text-muted-foreground">Sign in to start battling AI agents, track your performance, and climb the leaderboard.</p>`;
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
    Card($$payload, {
      children: ($$payload2) => {
        Card_header($$payload2, {
          children: ($$payload3) => {
            Card_title($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Quick Actions`;
              },
              $$slots: { default: true }
            });
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!----> `;
        Card_content($$payload2, {
          class: "grid grid-cols-2 gap-4",
          children: ($$payload3) => {
            $$payload3.out += `<button class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">Manage Agents</button> <button class="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">View Battles</button>`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    });
    $$payload.out += `<!----></div></div></div>`;
  }
  $$payload.out += `<!--]--></main>`;
  if ($$store_subs) unsubscribe_stores($$store_subs);
  bind_props($$props, { title });
  pop();
}
export {
  _page as default
};
