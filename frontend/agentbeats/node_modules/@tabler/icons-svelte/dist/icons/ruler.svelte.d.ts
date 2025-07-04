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
export type RulerProps = typeof __propDef.props;
export type RulerEvents = typeof __propDef.events;
export type RulerSlots = typeof __propDef.slots;
export default class Ruler extends SvelteComponentTyped<RulerProps, RulerEvents, RulerSlots> {
}
export {};
