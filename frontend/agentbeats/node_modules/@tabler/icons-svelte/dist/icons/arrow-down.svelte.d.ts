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
export type ArrowDownProps = typeof __propDef.props;
export type ArrowDownEvents = typeof __propDef.events;
export type ArrowDownSlots = typeof __propDef.slots;
export default class ArrowDown extends SvelteComponentTyped<ArrowDownProps, ArrowDownEvents, ArrowDownSlots> {
}
export {};
