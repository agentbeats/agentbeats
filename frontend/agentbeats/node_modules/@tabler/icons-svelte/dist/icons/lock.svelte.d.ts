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
export type LockProps = typeof __propDef.props;
export type LockEvents = typeof __propDef.events;
export type LockSlots = typeof __propDef.slots;
export default class Lock extends SvelteComponentTyped<LockProps, LockEvents, LockSlots> {
}
export {};
