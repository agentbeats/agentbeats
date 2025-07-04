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
export type CopyProps = typeof __propDef.props;
export type CopyEvents = typeof __propDef.events;
export type CopySlots = typeof __propDef.slots;
export default class Copy extends SvelteComponentTyped<CopyProps, CopyEvents, CopySlots> {
}
export {};
