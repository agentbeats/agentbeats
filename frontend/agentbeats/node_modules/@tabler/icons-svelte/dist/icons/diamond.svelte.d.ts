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
export type DiamondProps = typeof __propDef.props;
export type DiamondEvents = typeof __propDef.events;
export type DiamondSlots = typeof __propDef.slots;
export default class Diamond extends SvelteComponentTyped<DiamondProps, DiamondEvents, DiamondSlots> {
}
export {};
