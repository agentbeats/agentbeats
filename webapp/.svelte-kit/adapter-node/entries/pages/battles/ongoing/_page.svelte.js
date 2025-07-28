import { S as ensure_array_like, y as pop, w as push } from "../../../../chunks/index.js";
import { B as Battle_card_ongoing } from "../../../../chunks/battle-card-ongoing.js";
import "../../../../chunks/client.js";
function _page($$payload, $$props) {
  push();
  let ongoingBattles = [];
  const each_array = ensure_array_like(ongoingBattles);
  $$payload.out += `<div class="flex flex-1 flex-col items-center justify-center min-h-[80vh]"><div class="w-full max-w-5xl flex flex-col items-center"><div class="grid grid-cols-1 gap-4 px-4 lg:px-6 w-full"><!--[-->`;
  for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
    let battle = each_array[$$index];
    $$payload.out += `<button type="button" class="cursor-pointer">`;
    Battle_card_ongoing($$payload, { battleId: battle.id });
    $$payload.out += `<!----></button>`;
  }
  $$payload.out += `<!--]--></div> `;
  if (ongoingBattles.length === 0) {
    $$payload.out += "<!--[-->";
    $$payload.out += `<div class="text-center text-muted-foreground mt-10">No ongoing battles found.</div>`;
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]--></div></div>`;
  pop();
}
export {
  _page as default
};
