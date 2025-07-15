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
export type RefreshProps = typeof __propDef.props;
export type RefreshEvents = typeof __propDef.events;
export type RefreshSlots = typeof __propDef.slots;
export default class Refresh extends SvelteComponentTyped<RefreshProps, RefreshEvents, RefreshSlots> {
}
export {};
