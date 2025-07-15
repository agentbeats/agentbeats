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
export type ArrowUpProps = typeof __propDef.props;
export type ArrowUpEvents = typeof __propDef.events;
export type ArrowUpSlots = typeof __propDef.slots;
export default class ArrowUp extends SvelteComponentTyped<ArrowUpProps, ArrowUpEvents, ArrowUpSlots> {
}
export {};
