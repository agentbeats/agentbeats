import { w as push, G as spread_attributes, J as bind_props, y as pop, F as derived, N as copy_payload, O as assign_payload, M as spread_props, K as props_id, S as ensure_array_like, P as escape_html, B as head, A as attr } from "../../../../chunks/index.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import { g as goto } from "../../../../chunks/client.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../../../chunks/card-title.js";
import { C as Card_description } from "../../../../chunks/card-description.js";
import "clsx";
import { B as Button } from "../../../../chunks/button.js";
import { L as Label } from "../../../../chunks/label.js";
import { b as boxAutoReset, p as afterTick, f as DOMContext, q as Previous, r as isIOS, O as OpenChangeComplete, m as getFloatingContentCSSVars, e as afterSleep, k as Popper_layer_force_mount, l as Popper_layer, j as Floating_layer, n as Floating_layer_anchor, o as Portal } from "../../../../chunks/popper-layer-force-mount.js";
import { C as Context, A as ARROW_UP, a as ARROW_DOWN, E as ENTER, S as SPACE, T as TAB, P as PAGE_UP, H as HOME, b as PAGE_DOWN, c as END, n as noop, I as Icon } from "../../../../chunks/Icon.js";
import { m as mergeProps, s as srOnlyStylesString, w as watch, d as attachRef, b as box, a as createBitsAttrs, k as getDataDisabled, g as getDataOpenClosed, l as getAriaExpanded, n as getRequired, o as getDisabled, h as getAriaHidden, e as createId } from "../../../../chunks/create-id.js";
import "style-to-object";
import { o as on } from "../../../../chunks/events.js";
import "../../../../chunks/auth.js";
import "../../../../chunks/supabase.js";
import { c as cn } from "../../../../chunks/utils.js";
function next(array, index, loop = true) {
  if (array.length === 0 || index < 0 || index >= array.length)
    return;
  if (array.length === 1 && index === 0)
    return array[0];
  if (index === array.length - 1)
    return loop ? array[0] : void 0;
  return array[index + 1];
}
function prev(array, index, loop = true) {
  if (array.length === 0 || index < 0 || index >= array.length)
    return;
  if (array.length === 1 && index === 0)
    return array[0];
  if (index === 0)
    return loop ? array[array.length - 1] : void 0;
  return array[index - 1];
}
function forward(array, index, increment, loop = true) {
  if (array.length === 0 || index < 0 || index >= array.length)
    return;
  let targetIndex = index + increment;
  if (loop) {
    targetIndex = (targetIndex % array.length + array.length) % array.length;
  } else {
    targetIndex = Math.max(0, Math.min(targetIndex, array.length - 1));
  }
  return array[targetIndex];
}
function backward(array, index, decrement, loop = true) {
  if (array.length === 0 || index < 0 || index >= array.length)
    return;
  let targetIndex = index - decrement;
  if (loop) {
    targetIndex = (targetIndex % array.length + array.length) % array.length;
  } else {
    targetIndex = Math.max(0, Math.min(targetIndex, array.length - 1));
  }
  return array[targetIndex];
}
function getNextMatch(values, search, currentMatch) {
  const lowerSearch = search.toLowerCase();
  if (lowerSearch.endsWith(" ")) {
    const searchWithoutSpace = lowerSearch.slice(0, -1);
    const matchesWithoutSpace = values.filter((value) => value.toLowerCase().startsWith(searchWithoutSpace));
    if (matchesWithoutSpace.length <= 1) {
      return getNextMatch(values, searchWithoutSpace, currentMatch);
    }
    const currentMatchLowercase = currentMatch?.toLowerCase();
    if (currentMatchLowercase && currentMatchLowercase.startsWith(searchWithoutSpace) && currentMatchLowercase.charAt(searchWithoutSpace.length) === " " && search.trim() === searchWithoutSpace) {
      return currentMatch;
    }
    const spacedMatches = values.filter((value) => value.toLowerCase().startsWith(lowerSearch));
    if (spacedMatches.length > 0) {
      const currentMatchIndex2 = currentMatch ? values.indexOf(currentMatch) : -1;
      let wrappedMatches = wrapArray(spacedMatches, Math.max(currentMatchIndex2, 0));
      const nextMatch2 = wrappedMatches.find((match) => match !== currentMatch);
      return nextMatch2 || currentMatch;
    }
  }
  const isRepeated = search.length > 1 && Array.from(search).every((char) => char === search[0]);
  const normalizedSearch = isRepeated ? search[0] : search;
  const normalizedLowerSearch = normalizedSearch.toLowerCase();
  const currentMatchIndex = currentMatch ? values.indexOf(currentMatch) : -1;
  let wrappedValues = wrapArray(values, Math.max(currentMatchIndex, 0));
  const excludeCurrentMatch = normalizedSearch.length === 1;
  if (excludeCurrentMatch)
    wrappedValues = wrappedValues.filter((v) => v !== currentMatch);
  const nextMatch = wrappedValues.find((value) => value?.toLowerCase().startsWith(normalizedLowerSearch));
  return nextMatch !== currentMatch ? nextMatch : void 0;
}
function wrapArray(array, startIndex) {
  return array.map((_, index) => array[(startIndex + index) % array.length]);
}
function Hidden_input($$payload, $$props) {
  push();
  let { value = void 0, $$slots, $$events, ...restProps } = $$props;
  const mergedProps = mergeProps(restProps, {
    "aria-hidden": "true",
    tabindex: -1,
    style: srOnlyStylesString
  });
  if (mergedProps.type === "checkbox") {
    $$payload.out += "<!--[-->";
    $$payload.out += `<input${spread_attributes({ ...mergedProps, value })}/>`;
  } else {
    $$payload.out += "<!--[!-->";
    $$payload.out += `<input${spread_attributes({ value, ...mergedProps })}/>`;
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { value });
  pop();
}
class DataTypeahead {
  #opts;
  #candidateValues = derived(() => this.#opts.candidateValues());
  #search;
  constructor(opts) {
    this.#opts = opts;
    this.#search = boxAutoReset("", { afterMs: 1e3, getWindow: this.#opts.getWindow });
    this.handleTypeaheadSearch = this.handleTypeaheadSearch.bind(this);
    this.resetTypeahead = this.resetTypeahead.bind(this);
  }
  handleTypeaheadSearch(key) {
    if (!this.#opts.enabled() || !this.#candidateValues().length) return;
    this.#search.current = this.#search.current + key;
    const currentItem = this.#opts.getCurrentItem();
    const currentMatch = this.#candidateValues().find((item) => item === currentItem) ?? "";
    const values = this.#candidateValues().map((item) => item ?? "");
    const nextMatch = getNextMatch(values, this.#search.current, currentMatch);
    const newItem = this.#candidateValues().find((item) => item === nextMatch);
    if (newItem) {
      this.#opts.onMatch(newItem);
    }
    return newItem;
  }
  resetTypeahead() {
    this.#search.current = "";
  }
}
class DOMTypeahead {
  #opts;
  #search;
  #onMatch = derived(() => {
    if (this.#opts.onMatch) return this.#opts.onMatch;
    return (node) => node.focus();
  });
  #getCurrentItem = derived(() => {
    if (this.#opts.getCurrentItem) return this.#opts.getCurrentItem;
    return this.#opts.getActiveElement;
  });
  constructor(opts) {
    this.#opts = opts;
    this.#search = boxAutoReset("", { afterMs: 1e3, getWindow: opts.getWindow });
    this.handleTypeaheadSearch = this.handleTypeaheadSearch.bind(this);
    this.resetTypeahead = this.resetTypeahead.bind(this);
  }
  handleTypeaheadSearch(key, candidates) {
    if (!candidates.length) return;
    this.#search.current = this.#search.current + key;
    const currentItem = this.#getCurrentItem()();
    const currentMatch = candidates.find((item) => item === currentItem)?.textContent?.trim() ?? "";
    const values = candidates.map((item) => item.textContent?.trim() ?? "");
    const nextMatch = getNextMatch(values, this.#search.current, currentMatch);
    const newItem = candidates.find((item) => item.textContent?.trim() === nextMatch);
    if (newItem) this.#onMatch()(newItem);
    return newItem;
  }
  resetTypeahead() {
    this.#search.current = "";
  }
  get search() {
    return this.#search.current;
  }
}
const FIRST_KEYS = [ARROW_DOWN, PAGE_UP, HOME];
const LAST_KEYS = [ARROW_UP, PAGE_DOWN, END];
const FIRST_LAST_KEYS = [...FIRST_KEYS, ...LAST_KEYS];
const selectAttrs = createBitsAttrs({
  component: "select",
  parts: [
    "trigger",
    "content",
    "item",
    "viewport",
    "scroll-up-button",
    "scroll-down-button",
    "group",
    "group-label",
    "separator",
    "arrow",
    "input",
    "content-wrapper",
    "item-text",
    "value"
  ]
});
const SelectRootContext = new Context("Select.Root | Combobox.Root");
const SelectContentContext = new Context("Select.Content | Combobox.Content");
class SelectBaseRootState {
  opts;
  touchedInput = false;
  inputNode = null;
  contentNode = null;
  triggerNode = null;
  valueId = "";
  highlightedNode = null;
  #highlightedValue = derived(() => {
    if (!this.highlightedNode) return null;
    return this.highlightedNode.getAttribute("data-value");
  });
  get highlightedValue() {
    return this.#highlightedValue();
  }
  set highlightedValue($$value) {
    return this.#highlightedValue($$value);
  }
  #highlightedId = derived(() => {
    if (!this.highlightedNode) return void 0;
    return this.highlightedNode.id;
  });
  get highlightedId() {
    return this.#highlightedId();
  }
  set highlightedId($$value) {
    return this.#highlightedId($$value);
  }
  #highlightedLabel = derived(() => {
    if (!this.highlightedNode) return null;
    return this.highlightedNode.getAttribute("data-label");
  });
  get highlightedLabel() {
    return this.#highlightedLabel();
  }
  set highlightedLabel($$value) {
    return this.#highlightedLabel($$value);
  }
  isUsingKeyboard = false;
  isCombobox = false;
  domContext = new DOMContext(() => null);
  constructor(opts) {
    this.opts = opts;
    this.isCombobox = opts.isCombobox;
    new OpenChangeComplete({
      ref: box.with(() => this.contentNode),
      open: this.opts.open,
      onComplete: () => {
        this.opts.onOpenChangeComplete.current(this.opts.open.current);
      }
    });
  }
  setHighlightedNode(node, initial = false) {
    this.highlightedNode = node;
    if (node && (this.isUsingKeyboard || initial)) {
      node.scrollIntoView({ block: this.opts.scrollAlignment.current });
    }
  }
  getCandidateNodes() {
    const node = this.contentNode;
    if (!node) return [];
    return Array.from(node.querySelectorAll(`[${this.getBitsAttr("item")}]:not([data-disabled])`));
  }
  setHighlightedToFirstCandidate() {
    this.setHighlightedNode(null);
    const candidateNodes = this.getCandidateNodes();
    if (!candidateNodes.length) return;
    this.setHighlightedNode(candidateNodes[0]);
  }
  getNodeByValue(value) {
    const candidateNodes = this.getCandidateNodes();
    return candidateNodes.find((node) => node.dataset.value === value) ?? null;
  }
  setOpen(open) {
    this.opts.open.current = open;
  }
  toggleOpen() {
    this.opts.open.current = !this.opts.open.current;
  }
  handleOpen() {
    this.setOpen(true);
  }
  handleClose() {
    this.setHighlightedNode(null);
    this.setOpen(false);
  }
  toggleMenu() {
    this.toggleOpen();
  }
  getBitsAttr = (part) => {
    return selectAttrs.getAttr(part, this.isCombobox ? "combobox" : void 0);
  };
}
class SelectSingleRootState extends SelectBaseRootState {
  opts;
  isMulti = false;
  #hasValue = derived(() => this.opts.value.current !== "");
  get hasValue() {
    return this.#hasValue();
  }
  set hasValue($$value) {
    return this.#hasValue($$value);
  }
  #currentLabel = derived(() => {
    if (!this.opts.items.current.length) return "";
    const match = this.opts.items.current.find((item) => item.value === this.opts.value.current)?.label;
    return match ?? "";
  });
  get currentLabel() {
    return this.#currentLabel();
  }
  set currentLabel($$value) {
    return this.#currentLabel($$value);
  }
  #candidateLabels = derived(() => {
    if (!this.opts.items.current.length) return [];
    const filteredItems = this.opts.items.current.filter((item) => !item.disabled);
    return filteredItems.map((item) => item.label);
  });
  get candidateLabels() {
    return this.#candidateLabels();
  }
  set candidateLabels($$value) {
    return this.#candidateLabels($$value);
  }
  #dataTypeaheadEnabled = derived(() => {
    if (this.isMulti) return false;
    if (this.opts.items.current.length === 0) return false;
    return true;
  });
  get dataTypeaheadEnabled() {
    return this.#dataTypeaheadEnabled();
  }
  set dataTypeaheadEnabled($$value) {
    return this.#dataTypeaheadEnabled($$value);
  }
  constructor(opts) {
    super(opts);
    this.opts = opts;
    watch(() => this.opts.open.current, () => {
      if (!this.opts.open.current) return;
      this.setInitialHighlightedNode();
    });
  }
  includesItem(itemValue) {
    return this.opts.value.current === itemValue;
  }
  toggleItem(itemValue, itemLabel = itemValue) {
    this.opts.value.current = this.includesItem(itemValue) ? "" : itemValue;
    this.opts.inputValue.current = itemLabel;
  }
  setInitialHighlightedNode() {
    afterTick(() => {
      if (this.highlightedNode && this.domContext.getDocument().contains(this.highlightedNode)) return;
      if (this.opts.value.current !== "") {
        const node = this.getNodeByValue(this.opts.value.current);
        if (node) {
          this.setHighlightedNode(node, true);
          return;
        }
      }
      const firstCandidate = this.getCandidateNodes()[0];
      if (!firstCandidate) return;
      this.setHighlightedNode(firstCandidate, true);
    });
  }
}
class SelectMultipleRootState extends SelectBaseRootState {
  opts;
  isMulti = true;
  #hasValue = derived(() => this.opts.value.current.length > 0);
  get hasValue() {
    return this.#hasValue();
  }
  set hasValue($$value) {
    return this.#hasValue($$value);
  }
  constructor(opts) {
    super(opts);
    this.opts = opts;
    watch(() => this.opts.open.current, () => {
      if (!this.opts.open.current) return;
      this.setInitialHighlightedNode();
    });
  }
  includesItem(itemValue) {
    return this.opts.value.current.includes(itemValue);
  }
  toggleItem(itemValue, itemLabel = itemValue) {
    if (this.includesItem(itemValue)) {
      this.opts.value.current = this.opts.value.current.filter((v) => v !== itemValue);
    } else {
      this.opts.value.current = [...this.opts.value.current, itemValue];
    }
    this.opts.inputValue.current = itemLabel;
  }
  setInitialHighlightedNode() {
    afterTick(() => {
      if (!this.domContext) return;
      if (this.highlightedNode && this.domContext.getDocument().contains(this.highlightedNode)) return;
      if (this.opts.value.current.length && this.opts.value.current[0] !== "") {
        const node = this.getNodeByValue(this.opts.value.current[0]);
        if (node) {
          this.setHighlightedNode(node, true);
          return;
        }
      }
      const firstCandidate = this.getCandidateNodes()[0];
      if (!firstCandidate) return;
      this.setHighlightedNode(firstCandidate, true);
    });
  }
}
class SelectRootState {
  static create(props) {
    const { type, ...rest } = props;
    const rootState = type === "single" ? new SelectSingleRootState(rest) : new SelectMultipleRootState(rest);
    return SelectRootContext.set(rootState);
  }
}
class SelectTriggerState {
  static create(opts) {
    return new SelectTriggerState(opts, SelectRootContext.get());
  }
  opts;
  root;
  attachment;
  #domTypeahead;
  #dataTypeahead;
  constructor(opts, root) {
    this.opts = opts;
    this.root = root;
    this.attachment = attachRef(opts.ref, (v) => this.root.triggerNode = v);
    this.root.domContext = new DOMContext(opts.ref);
    this.#domTypeahead = new DOMTypeahead({
      getCurrentItem: () => this.root.highlightedNode,
      onMatch: (node) => {
        this.root.setHighlightedNode(node);
      },
      getActiveElement: () => this.root.domContext.getActiveElement(),
      getWindow: () => this.root.domContext.getWindow()
    });
    this.#dataTypeahead = new DataTypeahead({
      getCurrentItem: () => {
        if (this.root.isMulti) return "";
        return this.root.currentLabel;
      },
      onMatch: (label) => {
        if (this.root.isMulti) return;
        if (!this.root.opts.items.current) return;
        const matchedItem = this.root.opts.items.current.find((item) => item.label === label);
        if (!matchedItem) return;
        this.root.opts.value.current = matchedItem.value;
      },
      enabled: () => !this.root.isMulti && this.root.dataTypeaheadEnabled,
      candidateValues: () => this.root.isMulti ? [] : this.root.candidateLabels,
      getWindow: () => this.root.domContext.getWindow()
    });
    this.onkeydown = this.onkeydown.bind(this);
    this.onpointerdown = this.onpointerdown.bind(this);
    this.onpointerup = this.onpointerup.bind(this);
    this.onclick = this.onclick.bind(this);
  }
  #handleOpen() {
    this.root.opts.open.current = true;
    this.#dataTypeahead.resetTypeahead();
    this.#domTypeahead.resetTypeahead();
  }
  #handlePointerOpen(_) {
    this.#handleOpen();
  }
  /**
   * Logic used to handle keyboard selection/deselection.
   *
   * If it returns true, it means the item was selected and whatever is calling
   * this function should return early
   *
   */
  #handleKeyboardSelection() {
    const isCurrentSelectedValue = this.root.highlightedValue === this.root.opts.value.current;
    if (!this.root.opts.allowDeselect.current && isCurrentSelectedValue && !this.root.isMulti) {
      this.root.handleClose();
      return true;
    }
    if (this.root.highlightedValue !== null) {
      this.root.toggleItem(this.root.highlightedValue, this.root.highlightedLabel ?? void 0);
    }
    if (!this.root.isMulti && !isCurrentSelectedValue) {
      this.root.handleClose();
      return true;
    }
    return false;
  }
  onkeydown(e) {
    this.root.isUsingKeyboard = true;
    if (e.key === ARROW_UP || e.key === ARROW_DOWN) e.preventDefault();
    if (!this.root.opts.open.current) {
      if (e.key === ENTER || e.key === SPACE || e.key === ARROW_DOWN || e.key === ARROW_UP) {
        e.preventDefault();
        this.root.handleOpen();
      } else if (!this.root.isMulti && this.root.dataTypeaheadEnabled) {
        this.#dataTypeahead.handleTypeaheadSearch(e.key);
        return;
      }
      if (this.root.hasValue) return;
      const candidateNodes2 = this.root.getCandidateNodes();
      if (!candidateNodes2.length) return;
      if (e.key === ARROW_DOWN) {
        const firstCandidate = candidateNodes2[0];
        this.root.setHighlightedNode(firstCandidate);
      } else if (e.key === ARROW_UP) {
        const lastCandidate = candidateNodes2[candidateNodes2.length - 1];
        this.root.setHighlightedNode(lastCandidate);
      }
      return;
    }
    if (e.key === TAB) {
      this.root.handleClose();
      return;
    }
    if ((e.key === ENTER || // if we're currently "typing ahead", we don't want to select the item
    // just yet as the item the user is trying to get to may have a space in it,
    // so we defer handling the close for this case until further down
    e.key === SPACE && this.#domTypeahead.search === "") && !e.isComposing) {
      e.preventDefault();
      const shouldReturn = this.#handleKeyboardSelection();
      if (shouldReturn) return;
    }
    if (e.key === ARROW_UP && e.altKey) {
      this.root.handleClose();
    }
    if (FIRST_LAST_KEYS.includes(e.key)) {
      e.preventDefault();
      const candidateNodes2 = this.root.getCandidateNodes();
      const currHighlightedNode = this.root.highlightedNode;
      const currIndex = currHighlightedNode ? candidateNodes2.indexOf(currHighlightedNode) : -1;
      const loop = this.root.opts.loop.current;
      let nextItem;
      if (e.key === ARROW_DOWN) {
        nextItem = next(candidateNodes2, currIndex, loop);
      } else if (e.key === ARROW_UP) {
        nextItem = prev(candidateNodes2, currIndex, loop);
      } else if (e.key === PAGE_DOWN) {
        nextItem = forward(candidateNodes2, currIndex, 10, loop);
      } else if (e.key === PAGE_UP) {
        nextItem = backward(candidateNodes2, currIndex, 10, loop);
      } else if (e.key === HOME) {
        nextItem = candidateNodes2[0];
      } else if (e.key === END) {
        nextItem = candidateNodes2[candidateNodes2.length - 1];
      }
      if (!nextItem) return;
      this.root.setHighlightedNode(nextItem);
      return;
    }
    const isModifierKey = e.ctrlKey || e.altKey || e.metaKey;
    const isCharacterKey = e.key.length === 1;
    const isSpaceKey = e.key === SPACE;
    const candidateNodes = this.root.getCandidateNodes();
    if (e.key === TAB) return;
    if (!isModifierKey && (isCharacterKey || isSpaceKey)) {
      const matchedNode = this.#domTypeahead.handleTypeaheadSearch(e.key, candidateNodes);
      if (!matchedNode && isSpaceKey) {
        e.preventDefault();
        this.#handleKeyboardSelection();
      }
      return;
    }
    if (!this.root.highlightedNode) {
      this.root.setHighlightedToFirstCandidate();
    }
  }
  onclick(e) {
    const currTarget = e.currentTarget;
    currTarget.focus();
  }
  onpointerdown(e) {
    if (this.root.opts.disabled.current) return;
    if (e.pointerType === "touch") return e.preventDefault();
    const target = e.target;
    if (target?.hasPointerCapture(e.pointerId)) {
      target?.releasePointerCapture(e.pointerId);
    }
    if (e.button === 0 && e.ctrlKey === false) {
      if (this.root.opts.open.current === false) {
        this.#handlePointerOpen(e);
      } else {
        this.root.handleClose();
      }
    }
  }
  onpointerup(e) {
    if (this.root.opts.disabled.current) return;
    e.preventDefault();
    if (e.pointerType === "touch") {
      if (this.root.opts.open.current === false) {
        this.#handlePointerOpen(e);
      } else {
        this.root.handleClose();
      }
    }
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    disabled: this.root.opts.disabled.current ? true : void 0,
    "aria-haspopup": "listbox",
    "aria-expanded": getAriaExpanded(this.root.opts.open.current),
    "aria-activedescendant": this.root.highlightedId,
    "data-state": getDataOpenClosed(this.root.opts.open.current),
    "data-disabled": getDataDisabled(this.root.opts.disabled.current),
    "data-placeholder": this.root.hasValue ? void 0 : "",
    [this.root.getBitsAttr("trigger")]: "",
    onpointerdown: this.onpointerdown,
    onkeydown: this.onkeydown,
    onclick: this.onclick,
    onpointerup: this.onpointerup,
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectContentState {
  static create(opts) {
    return SelectContentContext.set(new SelectContentState(opts, SelectRootContext.get()));
  }
  opts;
  root;
  attachment;
  viewportNode = null;
  isPositioned = false;
  domContext;
  constructor(opts, root) {
    this.opts = opts;
    this.root = root;
    this.attachment = attachRef(opts.ref, (v) => this.root.contentNode = v);
    this.domContext = new DOMContext(this.opts.ref);
    if (this.root.domContext === null) {
      this.root.domContext = this.domContext;
    }
    watch(() => this.root.opts.open.current, () => {
      if (this.root.opts.open.current) return;
      this.isPositioned = false;
    });
    this.onpointermove = this.onpointermove.bind(this);
  }
  onpointermove(_) {
    this.root.isUsingKeyboard = false;
  }
  #styles = derived(() => {
    return getFloatingContentCSSVars(this.root.isCombobox ? "combobox" : "select");
  });
  onInteractOutside = (e) => {
    if (e.target === this.root.triggerNode || e.target === this.root.inputNode) {
      e.preventDefault();
      return;
    }
    this.opts.onInteractOutside.current(e);
    if (e.defaultPrevented) return;
    this.root.handleClose();
  };
  onEscapeKeydown = (e) => {
    this.opts.onEscapeKeydown.current(e);
    if (e.defaultPrevented) return;
    this.root.handleClose();
  };
  onOpenAutoFocus = (e) => {
    e.preventDefault();
  };
  onCloseAutoFocus = (e) => {
    e.preventDefault();
  };
  #snippetProps = derived(() => ({ open: this.root.opts.open.current }));
  get snippetProps() {
    return this.#snippetProps();
  }
  set snippetProps($$value) {
    return this.#snippetProps($$value);
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    role: "listbox",
    "aria-multiselectable": this.root.isMulti ? "true" : void 0,
    "data-state": getDataOpenClosed(this.root.opts.open.current),
    [this.root.getBitsAttr("content")]: "",
    style: {
      display: "flex",
      flexDirection: "column",
      outline: "none",
      boxSizing: "border-box",
      pointerEvents: "auto",
      ...this.#styles()
    },
    onpointermove: this.onpointermove,
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
  popperProps = {
    onInteractOutside: this.onInteractOutside,
    onEscapeKeydown: this.onEscapeKeydown,
    onOpenAutoFocus: this.onOpenAutoFocus,
    onCloseAutoFocus: this.onCloseAutoFocus,
    trapFocus: false,
    loop: false,
    onPlaced: () => {
      if (this.root.opts.open.current) {
        this.isPositioned = true;
      }
    }
  };
}
class SelectItemState {
  static create(opts) {
    return new SelectItemState(opts, SelectRootContext.get());
  }
  opts;
  root;
  attachment;
  #isSelected = derived(() => this.root.includesItem(this.opts.value.current));
  get isSelected() {
    return this.#isSelected();
  }
  set isSelected($$value) {
    return this.#isSelected($$value);
  }
  #isHighlighted = derived(() => this.root.highlightedValue === this.opts.value.current);
  get isHighlighted() {
    return this.#isHighlighted();
  }
  set isHighlighted($$value) {
    return this.#isHighlighted($$value);
  }
  prevHighlighted = new Previous(() => this.isHighlighted);
  mounted = false;
  constructor(opts, root) {
    this.opts = opts;
    this.root = root;
    this.attachment = attachRef(opts.ref);
    watch([() => this.isHighlighted, () => this.prevHighlighted.current], () => {
      if (this.isHighlighted) {
        this.opts.onHighlight.current();
      } else if (this.prevHighlighted.current) {
        this.opts.onUnhighlight.current();
      }
    });
    watch(() => this.mounted, () => {
      if (!this.mounted) return;
      this.root.setInitialHighlightedNode();
    });
    this.onpointerdown = this.onpointerdown.bind(this);
    this.onpointerup = this.onpointerup.bind(this);
    this.onpointermove = this.onpointermove.bind(this);
  }
  handleSelect() {
    if (this.opts.disabled.current) return;
    const isCurrentSelectedValue = this.opts.value.current === this.root.opts.value.current;
    if (!this.root.opts.allowDeselect.current && isCurrentSelectedValue && !this.root.isMulti) {
      this.root.handleClose();
      return;
    }
    this.root.toggleItem(this.opts.value.current, this.opts.label.current);
    if (!this.root.isMulti && !isCurrentSelectedValue) {
      this.root.handleClose();
    }
  }
  #snippetProps = derived(() => ({ selected: this.isSelected, highlighted: this.isHighlighted }));
  get snippetProps() {
    return this.#snippetProps();
  }
  set snippetProps($$value) {
    return this.#snippetProps($$value);
  }
  onpointerdown(e) {
    e.preventDefault();
  }
  /**
   * Using `pointerup` instead of `click` allows power users to pointerdown
   * the trigger, then release pointerup on an item to select it vs having to do
   * multiple clicks.
   */
  onpointerup(e) {
    if (e.defaultPrevented || !this.opts.ref.current) return;
    if (e.pointerType === "touch" && !isIOS) {
      on(
        this.opts.ref.current,
        "click",
        () => {
          this.handleSelect();
          this.root.setHighlightedNode(this.opts.ref.current);
        },
        { once: true }
      );
      return;
    }
    e.preventDefault();
    this.handleSelect();
    if (e.pointerType === "touch") {
      this.root.setHighlightedNode(this.opts.ref.current);
    }
  }
  onpointermove(e) {
    if (e.pointerType === "touch") return;
    if (this.root.highlightedNode !== this.opts.ref.current) {
      this.root.setHighlightedNode(this.opts.ref.current);
    }
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    role: "option",
    "aria-selected": this.root.includesItem(this.opts.value.current) ? "true" : void 0,
    "data-value": this.opts.value.current,
    "data-disabled": getDataDisabled(this.opts.disabled.current),
    "data-highlighted": this.root.highlightedValue === this.opts.value.current && !this.opts.disabled.current ? "" : void 0,
    "data-selected": this.root.includesItem(this.opts.value.current) ? "" : void 0,
    "data-label": this.opts.label.current,
    [this.root.getBitsAttr("item")]: "",
    onpointermove: this.onpointermove,
    onpointerdown: this.onpointerdown,
    onpointerup: this.onpointerup,
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectHiddenInputState {
  static create(opts) {
    return new SelectHiddenInputState(opts, SelectRootContext.get());
  }
  opts;
  root;
  #shouldRender = derived(() => this.root.opts.name.current !== "");
  get shouldRender() {
    return this.#shouldRender();
  }
  set shouldRender($$value) {
    return this.#shouldRender($$value);
  }
  constructor(opts, root) {
    this.opts = opts;
    this.root = root;
    this.onfocus = this.onfocus.bind(this);
  }
  onfocus(e) {
    e.preventDefault();
    if (!this.root.isCombobox) {
      this.root.triggerNode?.focus();
    } else {
      this.root.inputNode?.focus();
    }
  }
  #props = derived(() => ({
    disabled: getDisabled(this.root.opts.disabled.current),
    required: getRequired(this.root.opts.required.current),
    name: this.root.opts.name.current,
    value: this.opts.value.current,
    onfocus: this.onfocus
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectViewportState {
  static create(opts) {
    return new SelectViewportState(opts, SelectContentContext.get());
  }
  opts;
  content;
  root;
  attachment;
  prevScrollTop = 0;
  constructor(opts, content) {
    this.opts = opts;
    this.content = content;
    this.root = content.root;
    this.attachment = attachRef(opts.ref, (v) => this.content.viewportNode = v);
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    role: "presentation",
    [this.root.getBitsAttr("viewport")]: "",
    style: {
      // we use position: 'relative' here on the `viewport` so that when we call
      // `selectedItem.offsetTop` in calculations, the offset is relative to the viewport
      // (independent of the scrollUpButton).
      position: "relative",
      flex: 1,
      overflow: "auto"
    },
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectScrollButtonImplState {
  opts;
  content;
  root;
  attachment;
  autoScrollTimer = null;
  userScrollTimer = -1;
  isUserScrolling = false;
  onAutoScroll = noop;
  mounted = false;
  constructor(opts, content) {
    this.opts = opts;
    this.content = content;
    this.root = content.root;
    this.attachment = attachRef(opts.ref);
    watch([() => this.mounted], () => {
      if (!this.mounted) {
        this.isUserScrolling = false;
        return;
      }
      if (this.isUserScrolling) return;
    });
    this.onpointerdown = this.onpointerdown.bind(this);
    this.onpointermove = this.onpointermove.bind(this);
    this.onpointerleave = this.onpointerleave.bind(this);
  }
  handleUserScroll() {
    this.content.domContext.clearTimeout(this.userScrollTimer);
    this.isUserScrolling = true;
    this.userScrollTimer = this.content.domContext.setTimeout(
      () => {
        this.isUserScrolling = false;
      },
      200
    );
  }
  clearAutoScrollInterval() {
    if (this.autoScrollTimer === null) return;
    this.content.domContext.clearTimeout(this.autoScrollTimer);
    this.autoScrollTimer = null;
  }
  onpointerdown(_) {
    if (this.autoScrollTimer !== null) return;
    const autoScroll = (tick) => {
      this.onAutoScroll();
      this.autoScrollTimer = this.content.domContext.setTimeout(() => autoScroll(tick + 1), this.opts.delay.current(tick));
    };
    this.autoScrollTimer = this.content.domContext.setTimeout(() => autoScroll(1), this.opts.delay.current(0));
  }
  onpointermove(e) {
    this.onpointerdown(e);
  }
  onpointerleave(_) {
    this.clearAutoScrollInterval();
  }
  #props = derived(() => ({
    id: this.opts.id.current,
    "aria-hidden": getAriaHidden(true),
    style: { flexShrink: 0 },
    onpointerdown: this.onpointerdown,
    onpointermove: this.onpointermove,
    onpointerleave: this.onpointerleave,
    ...this.attachment
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectScrollDownButtonState {
  static create(opts) {
    return new SelectScrollDownButtonState(new SelectScrollButtonImplState(opts, SelectContentContext.get()));
  }
  scrollButtonState;
  content;
  root;
  canScrollDown = false;
  scrollIntoViewTimer = null;
  constructor(scrollButtonState) {
    this.scrollButtonState = scrollButtonState;
    this.content = scrollButtonState.content;
    this.root = scrollButtonState.root;
    this.scrollButtonState.onAutoScroll = this.handleAutoScroll;
    watch(
      [
        () => this.content.viewportNode,
        () => this.content.isPositioned
      ],
      () => {
        if (!this.content.viewportNode || !this.content.isPositioned) return;
        this.handleScroll(true);
        return on(this.content.viewportNode, "scroll", () => this.handleScroll());
      }
    );
    watch(() => this.scrollButtonState.mounted, () => {
      if (!this.scrollButtonState.mounted) return;
      if (this.scrollIntoViewTimer) {
        clearTimeout(this.scrollIntoViewTimer);
      }
      this.scrollIntoViewTimer = afterSleep(5, () => {
        const activeItem = this.root.highlightedNode;
        activeItem?.scrollIntoView({ block: this.root.opts.scrollAlignment.current });
      });
    });
  }
  /**
   * @param manual - if true, it means the function was invoked manually outside of an event
   * listener, so we don't call `handleUserScroll` to prevent the auto scroll from kicking in.
   */
  handleScroll = (manual = false) => {
    if (!manual) {
      this.scrollButtonState.handleUserScroll();
    }
    if (!this.content.viewportNode) return;
    const maxScroll = this.content.viewportNode.scrollHeight - this.content.viewportNode.clientHeight;
    const paddingTop = Number.parseInt(getComputedStyle(this.content.viewportNode).paddingTop, 10);
    this.canScrollDown = Math.ceil(this.content.viewportNode.scrollTop) < maxScroll - paddingTop;
  };
  handleAutoScroll = () => {
    const viewport = this.content.viewportNode;
    const selectedItem = this.root.highlightedNode;
    if (!viewport || !selectedItem) return;
    viewport.scrollTop = viewport.scrollTop + selectedItem.offsetHeight;
  };
  #props = derived(() => ({
    ...this.scrollButtonState.props,
    [this.root.getBitsAttr("scroll-down-button")]: ""
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
class SelectScrollUpButtonState {
  static create(opts) {
    return new SelectScrollUpButtonState(new SelectScrollButtonImplState(opts, SelectContentContext.get()));
  }
  scrollButtonState;
  content;
  root;
  canScrollUp = false;
  constructor(scrollButtonState) {
    this.scrollButtonState = scrollButtonState;
    this.content = scrollButtonState.content;
    this.root = scrollButtonState.root;
    this.scrollButtonState.onAutoScroll = this.handleAutoScroll;
    watch(
      [
        () => this.content.viewportNode,
        () => this.content.isPositioned
      ],
      () => {
        if (!this.content.viewportNode || !this.content.isPositioned) return;
        this.handleScroll(true);
        return on(this.content.viewportNode, "scroll", () => this.handleScroll());
      }
    );
  }
  /**
   * @param manual - if true, it means the function was invoked manually outside of an event
   * listener, so we don't call `handleUserScroll` to prevent the auto scroll from kicking in.
   */
  handleScroll = (manual = false) => {
    if (!manual) {
      this.scrollButtonState.handleUserScroll();
    }
    if (!this.content.viewportNode) return;
    const paddingTop = Number.parseInt(getComputedStyle(this.content.viewportNode).paddingTop, 10);
    this.canScrollUp = this.content.viewportNode.scrollTop - paddingTop > 0.1;
  };
  handleAutoScroll = () => {
    if (!this.content.viewportNode || !this.root.highlightedNode) return;
    this.content.viewportNode.scrollTop = this.content.viewportNode.scrollTop - this.root.highlightedNode.offsetHeight;
  };
  #props = derived(() => ({
    ...this.scrollButtonState.props,
    [this.root.getBitsAttr("scroll-up-button")]: ""
  }));
  get props() {
    return this.#props();
  }
  set props($$value) {
    return this.#props($$value);
  }
}
function Select_hidden_input($$payload, $$props) {
  push();
  let { value = "", autocomplete } = $$props;
  const hiddenInputState = SelectHiddenInputState.create({ value: box.with(() => value) });
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    if (hiddenInputState.shouldRender) {
      $$payload2.out += "<!--[-->";
      Hidden_input($$payload2, spread_props([
        hiddenInputState.props,
        {
          autocomplete,
          get value() {
            return value;
          },
          set value($$value) {
            value = $$value;
            $$settled = false;
          }
        }
      ]));
    } else {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]-->`;
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  bind_props($$props, { value });
  pop();
}
function Select_content$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    forceMount = false,
    side = "bottom",
    onInteractOutside = noop,
    onEscapeKeydown = noop,
    children,
    child,
    preventScroll = false,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const contentState = SelectContentState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v),
    onInteractOutside: box.with(() => onInteractOutside),
    onEscapeKeydown: box.with(() => onEscapeKeydown)
  });
  const mergedProps = mergeProps(restProps, contentState.props);
  if (forceMount) {
    $$payload.out += "<!--[-->";
    {
      let popper = function($$payload2, { props, wrapperProps }) {
        const finalProps = mergeProps(props, { style: contentState.props.style });
        if (child) {
          $$payload2.out += "<!--[-->";
          child($$payload2, {
            props: finalProps,
            wrapperProps,
            ...contentState.snippetProps
          });
          $$payload2.out += `<!---->`;
        } else {
          $$payload2.out += "<!--[!-->";
          $$payload2.out += `<div${spread_attributes({ ...wrapperProps })}><div${spread_attributes({ ...finalProps })}>`;
          children?.($$payload2);
          $$payload2.out += `<!----></div></div>`;
        }
        $$payload2.out += `<!--]-->`;
      };
      Popper_layer_force_mount($$payload, spread_props([
        mergedProps,
        contentState.popperProps,
        {
          ref: contentState.opts.ref,
          side,
          enabled: contentState.root.opts.open.current,
          id,
          preventScroll,
          forceMount: true,
          popper,
          $$slots: { popper: true }
        }
      ]));
    }
  } else if (!forceMount) {
    $$payload.out += "<!--[1-->";
    {
      let popper = function($$payload2, { props, wrapperProps }) {
        const finalProps = mergeProps(props, { style: contentState.props.style });
        if (child) {
          $$payload2.out += "<!--[-->";
          child($$payload2, {
            props: finalProps,
            wrapperProps,
            ...contentState.snippetProps
          });
          $$payload2.out += `<!---->`;
        } else {
          $$payload2.out += "<!--[!-->";
          $$payload2.out += `<div${spread_attributes({ ...wrapperProps })}><div${spread_attributes({ ...finalProps })}>`;
          children?.($$payload2);
          $$payload2.out += `<!----></div></div>`;
        }
        $$payload2.out += `<!--]-->`;
      };
      Popper_layer($$payload, spread_props([
        mergedProps,
        contentState.popperProps,
        {
          ref: contentState.opts.ref,
          side,
          open: contentState.root.opts.open.current,
          id,
          preventScroll,
          forceMount: false,
          popper,
          $$slots: { popper: true }
        }
      ]));
    }
  } else {
    $$payload.out += "<!--[!-->";
  }
  $$payload.out += `<!--]-->`;
  bind_props($$props, { ref });
  pop();
}
function Mounted($$payload, $$props) {
  push();
  let { mounted = false, onMountedChange = noop } = $$props;
  bind_props($$props, { mounted });
  pop();
}
function Select_item$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    value,
    label = value,
    disabled = false,
    children,
    child,
    onHighlight = noop,
    onUnhighlight = noop,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const itemState = SelectItemState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v),
    value: box.with(() => value),
    disabled: box.with(() => disabled),
    label: box.with(() => label),
    onHighlight: box.with(() => onHighlight),
    onUnhighlight: box.with(() => onUnhighlight)
  });
  const mergedProps = mergeProps(restProps, itemState.props);
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    if (child) {
      $$payload2.out += "<!--[-->";
      child($$payload2, { props: mergedProps, ...itemState.snippetProps });
      $$payload2.out += `<!---->`;
    } else {
      $$payload2.out += "<!--[!-->";
      $$payload2.out += `<div${spread_attributes({ ...mergedProps })}>`;
      children?.($$payload2, itemState.snippetProps);
      $$payload2.out += `<!----></div>`;
    }
    $$payload2.out += `<!--]--> `;
    Mounted($$payload2, {
      get mounted() {
        return itemState.mounted;
      },
      set mounted($$value) {
        itemState.mounted = $$value;
        $$settled = false;
      }
    });
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
function Select_viewport($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    children,
    child,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const viewportState = SelectViewportState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v)
  });
  const mergedProps = mergeProps(restProps, viewportState.props);
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
function Select_scroll_down_button$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    delay = () => 50,
    child,
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const scrollButtonState = SelectScrollDownButtonState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v),
    delay: box.with(() => delay)
  });
  const mergedProps = mergeProps(restProps, scrollButtonState.props);
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    if (scrollButtonState.canScrollDown) {
      $$payload2.out += "<!--[-->";
      Mounted($$payload2, {
        get mounted() {
          return scrollButtonState.scrollButtonState.mounted;
        },
        set mounted($$value) {
          scrollButtonState.scrollButtonState.mounted = $$value;
          $$settled = false;
        }
      });
      $$payload2.out += `<!----> `;
      if (child) {
        $$payload2.out += "<!--[-->";
        child($$payload2, { props: restProps });
        $$payload2.out += `<!---->`;
      } else {
        $$payload2.out += "<!--[!-->";
        $$payload2.out += `<div${spread_attributes({ ...mergedProps })}>`;
        children?.($$payload2);
        $$payload2.out += `<!----></div>`;
      }
      $$payload2.out += `<!--]-->`;
    } else {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]-->`;
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
function Select_scroll_up_button$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    delay = () => 50,
    child,
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const scrollButtonState = SelectScrollUpButtonState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v),
    delay: box.with(() => delay)
  });
  const mergedProps = mergeProps(restProps, scrollButtonState.props);
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    if (scrollButtonState.canScrollUp) {
      $$payload2.out += "<!--[-->";
      Mounted($$payload2, {
        get mounted() {
          return scrollButtonState.scrollButtonState.mounted;
        },
        set mounted($$value) {
          scrollButtonState.scrollButtonState.mounted = $$value;
          $$settled = false;
        }
      });
      $$payload2.out += `<!----> `;
      if (child) {
        $$payload2.out += "<!--[-->";
        child($$payload2, { props: restProps });
        $$payload2.out += `<!---->`;
      } else {
        $$payload2.out += "<!--[!-->";
        $$payload2.out += `<div${spread_attributes({ ...mergedProps })}>`;
        children?.($$payload2);
        $$payload2.out += `<!----></div>`;
      }
      $$payload2.out += `<!--]-->`;
    } else {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]-->`;
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
function Select($$payload, $$props) {
  push();
  let {
    value = void 0,
    onValueChange = noop,
    name = "",
    disabled = false,
    type,
    open = false,
    onOpenChange = noop,
    onOpenChangeComplete = noop,
    loop = false,
    scrollAlignment = "nearest",
    required = false,
    items = [],
    allowDeselect = false,
    autocomplete,
    children
  } = $$props;
  function handleDefaultValue() {
    if (value !== void 0) return;
    value = type === "single" ? "" : [];
  }
  handleDefaultValue();
  watch.pre(() => value, () => {
    handleDefaultValue();
  });
  let inputValue = "";
  const rootState = SelectRootState.create({
    type,
    value: box.with(() => value, (v) => {
      value = v;
      onValueChange(v);
    }),
    disabled: box.with(() => disabled),
    required: box.with(() => required),
    open: box.with(() => open, (v) => {
      open = v;
      onOpenChange(v);
    }),
    loop: box.with(() => loop),
    scrollAlignment: box.with(() => scrollAlignment),
    name: box.with(() => name),
    isCombobox: false,
    items: box.with(() => items),
    allowDeselect: box.with(() => allowDeselect),
    inputValue: box.with(() => inputValue, (v) => inputValue = v),
    onOpenChangeComplete: box.with(() => onOpenChangeComplete)
  });
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    Floating_layer($$payload2, {
      children: ($$payload3) => {
        children?.($$payload3);
        $$payload3.out += `<!---->`;
      }
    });
    $$payload2.out += `<!----> `;
    if (Array.isArray(rootState.opts.value.current)) {
      $$payload2.out += "<!--[-->";
      if (rootState.opts.value.current.length) {
        $$payload2.out += "<!--[-->";
        const each_array = ensure_array_like(rootState.opts.value.current);
        $$payload2.out += `<!--[-->`;
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let item = each_array[$$index];
          Select_hidden_input($$payload2, { value: item, autocomplete });
        }
        $$payload2.out += `<!--]-->`;
      } else {
        $$payload2.out += "<!--[!-->";
      }
      $$payload2.out += `<!--]-->`;
    } else {
      $$payload2.out += "<!--[!-->";
      Select_hidden_input($$payload2, {
        autocomplete,
        get value() {
          return rootState.opts.value.current;
        },
        set value($$value) {
          rootState.opts.value.current = $$value;
          $$settled = false;
        }
      });
    }
    $$payload2.out += `<!--]-->`;
  }
  do {
    $$settled = true;
    $$inner_payload = copy_payload($$payload);
    $$render_inner($$inner_payload);
  } while (!$$settled);
  assign_payload($$payload, $$inner_payload);
  bind_props($$props, { value, open });
  pop();
}
function Select_trigger$1($$payload, $$props) {
  push();
  const uid = props_id($$payload);
  let {
    id = createId(uid),
    ref = null,
    child,
    children,
    type = "button",
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  const triggerState = SelectTriggerState.create({
    id: box.with(() => id),
    ref: box.with(() => ref, (v) => ref = v)
  });
  const mergedProps = mergeProps(restProps, triggerState.props, { type });
  $$payload.out += `<!---->`;
  Floating_layer_anchor($$payload, {
    id,
    ref: triggerState.opts.ref,
    children: ($$payload2) => {
      if (child) {
        $$payload2.out += "<!--[-->";
        child($$payload2, { props: mergedProps });
        $$payload2.out += `<!---->`;
      } else {
        $$payload2.out += "<!--[!-->";
        $$payload2.out += `<button${spread_attributes({ ...mergedProps })}>`;
        children?.($$payload2);
        $$payload2.out += `<!----></button>`;
      }
      $$payload2.out += `<!--]-->`;
    }
  });
  $$payload.out += `<!---->`;
  bind_props($$props, { ref });
  pop();
}
function Check($$payload, $$props) {
  push();
  /**
   * @license @lucide/svelte v0.515.0 - ISC
   *
   * ISC License
   *
   * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
   *
   * Permission to use, copy, modify, and/or distribute this software for any
   * purpose with or without fee is hereby granted, provided that the above
   * copyright notice and this permission notice appear in all copies.
   *
   * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
   * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
   * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
   * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
   * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
   * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
   * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
   *
   */
  let { $$slots, $$events, ...props } = $$props;
  const iconNode = [["path", { "d": "M20 6 9 17l-5-5" }]];
  Icon($$payload, spread_props([
    { name: "check" },
    /**
     * @component @name Check
     * @description Lucide SVG icon component, renders SVG Element with children.
     *
     * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMjAgNiA5IDE3bC01LTUiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/check
     * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
     *
     * @param {Object} props - Lucide icons props and any valid SVG attribute
     * @returns {FunctionalComponent} Svelte component
     *
     */
    props,
    {
      iconNode,
      children: ($$payload2) => {
        props.children?.($$payload2);
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    }
  ]));
  pop();
}
function Chevron_down($$payload, $$props) {
  push();
  /**
   * @license @lucide/svelte v0.515.0 - ISC
   *
   * ISC License
   *
   * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
   *
   * Permission to use, copy, modify, and/or distribute this software for any
   * purpose with or without fee is hereby granted, provided that the above
   * copyright notice and this permission notice appear in all copies.
   *
   * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
   * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
   * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
   * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
   * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
   * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
   * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
   *
   */
  let { $$slots, $$events, ...props } = $$props;
  const iconNode = [["path", { "d": "m6 9 6 6 6-6" }]];
  Icon($$payload, spread_props([
    { name: "chevron-down" },
    /**
     * @component @name ChevronDown
     * @description Lucide SVG icon component, renders SVG Element with children.
     *
     * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJtNiA5IDYgNiA2LTYiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/chevron-down
     * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
     *
     * @param {Object} props - Lucide icons props and any valid SVG attribute
     * @returns {FunctionalComponent} Svelte component
     *
     */
    props,
    {
      iconNode,
      children: ($$payload2) => {
        props.children?.($$payload2);
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    }
  ]));
  pop();
}
function Select_item($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    value,
    label,
    children: childrenProp,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    $$payload2.out += `<!---->`;
    {
      let children = function($$payload3, { selected, highlighted }) {
        $$payload3.out += `<span class="absolute right-2 flex size-3.5 items-center justify-center">`;
        if (selected) {
          $$payload3.out += "<!--[-->";
          Check($$payload3, { class: "size-4" });
        } else {
          $$payload3.out += "<!--[!-->";
        }
        $$payload3.out += `<!--]--></span> `;
        if (childrenProp) {
          $$payload3.out += "<!--[-->";
          childrenProp($$payload3, { selected, highlighted });
          $$payload3.out += `<!---->`;
        } else {
          $$payload3.out += "<!--[!-->";
          $$payload3.out += `${escape_html(label || value)}`;
        }
        $$payload3.out += `<!--]-->`;
      };
      Select_item$1($$payload2, spread_props([
        {
          value,
          "data-slot": "select-item",
          class: cn("data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground [&_svg:not([class*='text-'])]:text-muted-foreground outline-hidden *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2 relative flex w-full cursor-default select-none items-center gap-2 rounded-sm py-1.5 pl-2 pr-8 text-sm data-[disabled]:pointer-events-none data-[disabled]:opacity-50 [&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0", className)
        },
        restProps,
        {
          get ref() {
            return ref;
          },
          set ref($$value) {
            ref = $$value;
            $$settled = false;
          },
          children,
          $$slots: { default: true }
        }
      ]));
    }
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
function Chevron_up($$payload, $$props) {
  push();
  /**
   * @license @lucide/svelte v0.515.0 - ISC
   *
   * ISC License
   *
   * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
   *
   * Permission to use, copy, modify, and/or distribute this software for any
   * purpose with or without fee is hereby granted, provided that the above
   * copyright notice and this permission notice appear in all copies.
   *
   * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
   * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
   * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
   * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
   * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
   * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
   * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
   *
   */
  let { $$slots, $$events, ...props } = $$props;
  const iconNode = [["path", { "d": "m18 15-6-6-6 6" }]];
  Icon($$payload, spread_props([
    { name: "chevron-up" },
    /**
     * @component @name ChevronUp
     * @description Lucide SVG icon component, renders SVG Element with children.
     *
     * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJtMTggMTUtNi02LTYgNiIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/chevron-up
     * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
     *
     * @param {Object} props - Lucide icons props and any valid SVG attribute
     * @returns {FunctionalComponent} Svelte component
     *
     */
    props,
    {
      iconNode,
      children: ($$payload2) => {
        props.children?.($$payload2);
        $$payload2.out += `<!---->`;
      },
      $$slots: { default: true }
    }
  ]));
  pop();
}
function Select_scroll_up_button($$payload, $$props) {
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
    Select_scroll_up_button$1($$payload2, spread_props([
      {
        "data-slot": "select-scroll-up-button",
        class: cn("flex cursor-default items-center justify-center py-1", className)
      },
      restProps,
      {
        get ref() {
          return ref;
        },
        set ref($$value) {
          ref = $$value;
          $$settled = false;
        },
        children: ($$payload3) => {
          Chevron_up($$payload3, { class: "size-4" });
        },
        $$slots: { default: true }
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
function Select_scroll_down_button($$payload, $$props) {
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
    Select_scroll_down_button$1($$payload2, spread_props([
      {
        "data-slot": "select-scroll-down-button",
        class: cn("flex cursor-default items-center justify-center py-1", className)
      },
      restProps,
      {
        get ref() {
          return ref;
        },
        set ref($$value) {
          ref = $$value;
          $$settled = false;
        },
        children: ($$payload3) => {
          Chevron_down($$payload3, { class: "size-4" });
        },
        $$slots: { default: true }
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
function Select_content($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    sideOffset = 4,
    portalProps,
    children,
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    $$payload2.out += `<!---->`;
    Portal($$payload2, spread_props([
      portalProps,
      {
        children: ($$payload3) => {
          $$payload3.out += `<!---->`;
          Select_content$1($$payload3, spread_props([
            {
              sideOffset,
              "data-slot": "select-content",
              class: cn("bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 max-h-(--bits-select-content-available-height) origin-(--bits-select-content-transform-origin) relative z-50 min-w-[8rem] overflow-y-auto overflow-x-hidden rounded-md border shadow-md data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1", className)
            },
            restProps,
            {
              get ref() {
                return ref;
              },
              set ref($$value) {
                ref = $$value;
                $$settled = false;
              },
              children: ($$payload4) => {
                Select_scroll_up_button($$payload4, {});
                $$payload4.out += `<!----> <!---->`;
                Select_viewport($$payload4, {
                  class: cn("h-(--bits-select-anchor-height) min-w-(--bits-select-anchor-width) w-full scroll-my-1 p-1"),
                  children: ($$payload5) => {
                    children?.($$payload5);
                    $$payload5.out += `<!---->`;
                  },
                  $$slots: { default: true }
                });
                $$payload4.out += `<!----> `;
                Select_scroll_down_button($$payload4, {});
                $$payload4.out += `<!---->`;
              },
              $$slots: { default: true }
            }
          ]));
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
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
function Select_trigger($$payload, $$props) {
  push();
  let {
    ref = null,
    class: className,
    children,
    size = "default",
    $$slots,
    $$events,
    ...restProps
  } = $$props;
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    $$payload2.out += `<!---->`;
    Select_trigger$1($$payload2, spread_props([
      {
        "data-slot": "select-trigger",
        "data-size": size,
        class: cn("border-input data-[placeholder]:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive dark:bg-input/30 dark:hover:bg-input/50 shadow-xs flex w-fit select-none items-center justify-between gap-2 whitespace-nowrap rounded-md border bg-transparent px-3 py-2 text-sm outline-none transition-[color,box-shadow] focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 data-[size=default]:h-9 data-[size=sm]:h-8 *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2 [&_svg:not([class*='size-'])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0", className)
      },
      restProps,
      {
        get ref() {
          return ref;
        },
        set ref($$value) {
          ref = $$value;
          $$settled = false;
        },
        children: ($$payload3) => {
          children?.($$payload3);
          $$payload3.out += `<!----> `;
          Chevron_down($$payload3, { class: "size-4 opacity-50" });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
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
const Root = Select;
function _page($$payload, $$props) {
  push();
  let debugPayload;
  let data = $$props["data"];
  onDestroy(() => {
  });
  let formData = { green_agent_id: "", config: {} };
  let configJsonInput = "";
  let isSubmitting = false;
  let roleAssignments = {};
  let participantRequirements = [];
  formData.green_agent_id = "";
  if (formData.green_agent_id) {
    const green = data.greenAgents.find((a) => a.agent_id === formData.green_agent_id);
    participantRequirements = green?.register_info?.participant_requirements || [];
    for (const req of participantRequirements) {
      if (!(req.name in roleAssignments)) {
        roleAssignments[req.name] = "";
      }
    }
    for (const key of Object.keys(roleAssignments)) {
      if (!participantRequirements.some((r) => r.name === key)) {
        delete roleAssignments[key];
      }
    }
  } else {
    participantRequirements = [];
    roleAssignments = {};
  }
  {
    if (Object.keys(formData.config).length === 0) {
      configJsonInput = "";
    } else {
      configJsonInput = JSON.stringify(formData.config, null, 2);
    }
  }
  debugPayload = {
    green_agent_id: formData.green_agent_id,
    config: formData.config,
    roleAssignments: { ...roleAssignments },
    opponents: participantRequirements.filter((req) => roleAssignments[req.name]).map((req) => ({ name: req.name, agent_id: roleAssignments[req.name] }))
  };
  let $$settled = true;
  let $$inner_payload;
  function $$render_inner($$payload2) {
    head($$payload2, ($$payload3) => {
      $$payload3.title = `<title>Stage Battle - AgentBeats</title>`;
    });
    $$payload2.out += `<div class="container mx-auto p-6 max-w-6xl"><div class="text-center mb-8"><h1 class="text-4xl font-bold mb-6">Stage a Battle</h1> <p class="text-muted-foreground">Create a new battle between agents</p></div> `;
    {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]--> `;
    {
      $$payload2.out += "<!--[!-->";
    }
    $$payload2.out += `<!--]--> <div class="grid gap-6 md:grid-cols-2">`;
    Card($$payload2, {
      children: ($$payload3) => {
        Card_header($$payload3, {
          children: ($$payload4) => {
            Card_title($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Battle Configuration`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Set up the battle parameters`;
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
              for: "green_agent",
              children: ($$payload5) => {
                $$payload5.out += `<!---->Green Agent (Battle Initiator)`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Root($$payload4, {
              type: "single",
              required: true,
              get value() {
                return formData.green_agent_id;
              },
              set value($$value) {
                formData.green_agent_id = $$value;
                $$settled = false;
              },
              children: ($$payload5) => {
                Select_trigger($$payload5, {
                  children: ($$payload6) => {
                    $$payload6.out += `<span>${escape_html(formData.green_agent_id ? data.greenAgents.find((a) => a.agent_id === formData.green_agent_id)?.register_info.name : "Select a green agent")}</span>`;
                  },
                  $$slots: { default: true }
                });
                $$payload5.out += `<!----> `;
                Select_content($$payload5, {
                  children: ($$payload6) => {
                    const each_array = ensure_array_like(data.greenAgents);
                    $$payload6.out += `<!--[-->`;
                    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
                      let agent = each_array[$$index];
                      Select_item($$payload6, {
                        value: agent.agent_id,
                        children: ($$payload7) => {
                          $$payload7.out += `<!---->${escape_html(agent.register_info.name)}`;
                        },
                        $$slots: { default: true }
                      });
                    }
                    $$payload6.out += `<!--]-->`;
                  },
                  $$slots: { default: true }
                });
                $$payload5.out += `<!---->`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----></div>   <div class="space-y-2">`;
            Label($$payload4, {
              for: "config_json",
              children: ($$payload5) => {
                $$payload5.out += `<!---->Custom Configuration (JSON)`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> <textarea id="config_json"${attr("placeholder", JSON.stringify({ battle_config: "content", max_rounds: 10, debug_mode: true }))} class="w-full px-3 py-2 border border-input rounded-md text-sm font-mono resize-vertical min-h-[80px]" rows="4">`;
            const $$body = escape_html(configJsonInput);
            if ($$body) {
              $$payload4.out += `${$$body}`;
            }
            $$payload4.out += `</textarea> `;
            {
              $$payload4.out += "<!--[!-->";
              $$payload4.out += `<div class="text-muted-foreground text-sm">Enter a valid JSON object for battle configuration</div>`;
            }
            $$payload4.out += `<!--]--></div> <div class="flex gap-2 pt-4">`;
            Button($$payload4, {
              type: "submit",
              disabled: isSubmitting,
              children: ($$payload5) => {
                $$payload5.out += `<!---->${escape_html("Create Battle")}`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Button($$payload4, {
              type: "button",
              variant: "outline",
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
                $$payload5.out += `<!---->Assign Agents to Roles`;
              },
              $$slots: { default: true }
            });
            $$payload4.out += `<!----> `;
            Card_description($$payload4, {
              children: ($$payload5) => {
                $$payload5.out += `<!---->Assign an agent to each required role for this battle`;
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
            if (participantRequirements.length > 0) {
              $$payload4.out += "<!--[-->";
              const each_array_1 = ensure_array_like(participantRequirements);
              $$payload4.out += `<div class="space-y-4"><!--[-->`;
              for (let $$index_2 = 0, $$length = each_array_1.length; $$index_2 < $$length; $$index_2++) {
                let req = each_array_1[$$index_2];
                $$payload4.out += `<div class="flex flex-col gap-2 p-3 border rounded-lg"><div class="font-medium">${escape_html(req.name)} <span class="text-xs text-muted-foreground">(${escape_html(req.role)})</span> ${escape_html(req.required ? "*" : "")}</div> `;
                Root($$payload4, {
                  type: "single",
                  required: true,
                  get value() {
                    return roleAssignments[req.name];
                  },
                  set value($$value) {
                    roleAssignments[req.name] = $$value;
                    $$settled = false;
                  },
                  children: ($$payload5) => {
                    Select_trigger($$payload5, {
                      children: ($$payload6) => {
                        $$payload6.out += `<span>${escape_html(roleAssignments[req.name] ? data.opponentAgents.find((a) => a.agent_id === roleAssignments[req.name])?.register_info.name : "Select agent")}</span>`;
                      },
                      $$slots: { default: true }
                    });
                    $$payload5.out += `<!----> `;
                    Select_content($$payload5, {
                      children: ($$payload6) => {
                        const each_array_2 = ensure_array_like(data.opponentAgents);
                        $$payload6.out += `<!--[-->`;
                        for (let $$index_1 = 0, $$length2 = each_array_2.length; $$index_1 < $$length2; $$index_1++) {
                          let agent = each_array_2[$$index_1];
                          if (!Object.entries(roleAssignments).some(([role, id]) => role !== req.name && id === agent.agent_id) || roleAssignments[req.name] === agent.agent_id) {
                            $$payload6.out += "<!--[-->";
                            Select_item($$payload6, {
                              value: agent.agent_id,
                              children: ($$payload7) => {
                                $$payload7.out += `<!---->${escape_html(agent.register_info.name)}`;
                              },
                              $$slots: { default: true }
                            });
                          } else {
                            $$payload6.out += "<!--[!-->";
                          }
                          $$payload6.out += `<!--]-->`;
                        }
                        $$payload6.out += `<!--]-->`;
                      },
                      $$slots: { default: true }
                    });
                    $$payload5.out += `<!---->`;
                  },
                  $$slots: { default: true }
                });
                $$payload4.out += `<!----></div>`;
              }
              $$payload4.out += `<!--]--></div>`;
            } else {
              $$payload4.out += "<!--[!-->";
              $$payload4.out += `<div class="text-muted-foreground">Select a green agent to see required roles.</div>`;
            }
            $$payload4.out += `<!--]-->`;
          },
          $$slots: { default: true }
        });
        $$payload3.out += `<!---->`;
      },
      $$slots: { default: true }
    });
    $$payload2.out += `<!----></div> <details class="mt-8"><summary class="text-lg font-medium cursor-pointer">Debug: Form Data</summary> <div class="mt-4 p-4 bg-muted rounded-lg"><pre class="text-xs overflow-auto max-h-60">${escape_html(JSON.stringify(debugPayload, null, 2))}</pre></div></details></div>`;
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
