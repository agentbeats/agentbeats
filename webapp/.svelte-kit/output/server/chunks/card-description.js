import { G as spread_attributes, I as clsx, J as bind_props, y as pop, w as push } from "./index.js";
import { c as cn } from "./utils.js";
function Card_description($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  $$payload.out += `<p${spread_attributes(
    {
      "data-slot": "card-description",
      class: clsx(cn("text-muted-foreground text-sm", className)),
      ...restProps
    }
  )}>`;
  children?.($$payload);
  $$payload.out += `<!----></p>`;
  bind_props($$props, { ref });
  pop();
}
export {
  Card_description as C
};
