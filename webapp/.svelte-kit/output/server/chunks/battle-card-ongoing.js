import { J as bind_props, y as pop, w as push } from "./index.js";
import { o as onDestroy } from "./index-server.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "./card-title.js";
import "clsx";
function Battle_card_ongoing($$payload, $$props) {
  push();
  let battleId = $$props["battleId"];
  onDestroy(() => {
  });
  {
    $$payload.out += "<!--[-->";
    Card($$payload, {
      class: "w-full max-w-4xl border shadow-sm bg-background my-4 px-6 py-4",
      children: ($$payload2) => {
        Card_header($$payload2, {
          children: ($$payload3) => {
            Card_title($$payload3, {
              children: ($$payload4) => {
                $$payload4.out += `<!---->Loading battle...`;
              },
              $$slots: { default: true }
            });
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!----> `;
        Card_content($$payload2, {
          children: ($$payload3) => {
            $$payload3.out += `<div class="animate-pulse text-muted-foreground">Please wait…</div>`;
          },
          $$slots: { default: true }
        });
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    });
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { battleId });
  pop();
}
export {
  Battle_card_ongoing as B
};
