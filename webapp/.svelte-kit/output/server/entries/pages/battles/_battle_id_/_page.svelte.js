import { T as store_get, U as unsubscribe_stores, y as pop, w as push } from "../../../../chunks/index.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import { p as page } from "../../../../chunks/stores.js";
function _page($$payload, $$props) {
  push();
  var $$store_subs;
  onDestroy(() => {
  });
  store_get($$store_subs ??= {}, "$page", page).params.battle_id;
  $$payload.out += `<main class="p-4 flex flex-col min-h-[60vh] max-w-xl mx-auto">`;
  {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div>Loading...</div>`;
  }
  $$payload.out += `<!--]--></main>`;
  if ($$store_subs) unsubscribe_stores($$store_subs);
  pop();
}
export {
  _page as default
};
