import { F as derived, w as push, K as props_id, G as spread_attributes, J as bind_props, y as pop, N as copy_payload, O as assign_payload, M as spread_props } from "./index.js";
import { c as cn } from "./utils.js";
import { d as attachRef, a as createBitsAttrs, i as getDataOrientation, j as getAriaHidden, k as getAriaOrientation, e as createId, b as box, m as mergeProps } from "./create-id.js";
import "style-to-object";
import "clsx";
const separatorAttrs = createBitsAttrs({ component: "separator", parts: ["root"] });
class SeparatorRootState {
  static create(opts) {
    return new SeparatorRootState(opts);
  }
  opts;
  attachment;
  constructor(opts) {
    this.opts = opts;
    this.attachment = attachRef(opts.ref);
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    role: this.opts.decorative.current ? "none" : "separator",
    "aria-orientation": getAriaOrientation(this.opts.orientation.current),
    "aria-hidden": getAriaHidden(this.opts.decorative.current),
    "data-orientation": getDataOrientation(this.opts.orientation.current),
    [separatorAttrs.root]: "",
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
function Separator$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    child,
    children,
    decorative = false,
    orientation = "horizontal",
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const rootState = SeparatorRootState.create({
    ref: box.with(() => ref, (v) => ref = v),
    id: box.with(() => id),
    decorative: box.with(() => decorative),
    orientation: box.with(() => orientation)
  });
  const mergedProps = mergeProps(restProps, rootState.props);
  if (child) {
    $$payload.out += "<!--[-->";
    child($$payload, { props: mergedProps });
    $$payload.out += `<!---->`;
  } else {
    $$payload.out += "<!--[!-->";
    $$payload.out += `<div${spread_attributes({ ...mergedProps })}>`;
    children?.($$payload);
    $$payload.out += `<!----></div>`;
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { ref });
  pop();
}
function Separator($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    $$payload2.out += `<!---->`;
    Separator$1($$payload2, spread_props([
      {
        "data-slot": "separator",
        class: cn("bg-border shrink-0 data-[orientation=horizontal]:h-px data-[orientation=vertical]:h-full data-[orientation=horizontal]:w-full data-[orientation=vertical]:w-px", className)
      },
      restProps,
      {
        get ref() {
          return ref;
        },
        set ref($$value) {
          ref = $$value;
          $$settled = false;
        }
      }
    ]));
    $$payload2.out += `<!---->`;
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  bind_props($$props, { ref });
  pop();
}
export {
  Separator as S
};
