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
export type BugProps = typeof __propDef.props;
export type BugEvents = typeof __propDef.events;
export type BugSlots = typeof __propDef.slots;
export default class Bug extends SvelteComponentTyped<BugProps, BugEvents, BugSlots> {
}
export {};
