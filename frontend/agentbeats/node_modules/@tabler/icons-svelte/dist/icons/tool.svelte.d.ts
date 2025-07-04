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
export type ToolProps = typeof __propDef.props;
export type ToolEvents = typeof __propDef.events;
export type ToolSlots = typeof __propDef.slots;
export default class Tool extends SvelteComponentTyped<ToolProps, ToolEvents, ToolSlots> {
}
export {};
