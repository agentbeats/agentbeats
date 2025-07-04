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
export type HeartProps = typeof __propDef.props;
export type HeartEvents = typeof __propDef.events;
export type HeartSlots = typeof __propDef.slots;
export default class Heart extends SvelteComponentTyped<HeartProps, HeartEvents, HeartSlots> {
}
export {};
