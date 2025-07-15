import { F as derived, w as push, K as props_id, G as spread_attributes, J as bind_props, y as pop, N as copy_payload, O as assign_payload, M as spread_props } from "./index.js";
import { c as cn } from "./utils.js";
import { d as attachRef, a as createBitsAttrs, e as createId, b as box, m as mergeProps } from "./create-id.js";
import "style-to-object";
import "clsx";
const labelAttrs = createBitsAttrs({ component: "label", parts: ["root"] });
class LabelRootState {
  static create(opts) {
    return new LabelRootState(opts);
  }
  opts;
  attachment;
  constructor(opts) {
    this.opts = opts;
    this.attachment = attachRef(this.opts.ref);
    this.onmousedown = this.onmousedown.bind(this);
  }
  onmousedown(e) {
    if (e.detail > 1) e.preventDefault();
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    [labelAttrs.root]: "",
    onmousedown: this.onmousedown,
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
function Label$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    children,
    child,
    id = createId(uid),
    ref = null,
    for: forProp,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const rootState = LabelRootState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v)
  });
  const mergedProps = mergeProps(restProps, rootState.props, { for: forProp });
  if (child) {
    $$payload.out += "<!--[-->";
    child($$payload, { props: mergedProps });
    $$payload.out += `<!---->`;
  } else {
    $$payload.out += "<!--[!-->";
    $$payload.out += `<label${spread_attributes({ ...mergedProps, for: forProp })}>`;
    children?.($$payload);
    $$payload.out += `<!----></label>`;
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { ref });
  pop();
}
function Label($$payload, $$props) {
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
    Label$1($$payload2, spread_props([
      {
        "data-slot": "label",
        class: cn("flex select-none items-center gap-2 text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-50 group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50", className)
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
  Label as L
};
