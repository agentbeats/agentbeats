import { SvelteComponentTyped } from "svelte";
import type { IconProps } from '../types.js';
declare const __propDef: {
    props: IconProps;
    events: {
        [evt: string]: CustomEvent<any>;
    };
    slots: {
        default: {};
    };
};
export type QuoteProps = typeof __propDef.props;
export type QuoteEvents = typeof __propDef.events;
export type QuoteSlots = typeof __propDef.slots;
export default class Quote extends SvelteComponentTyped<QuoteProps, QuoteEvents, QuoteSlots> {
}
export {};
