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
export type CloudProps = typeof __propDef.props;
export type CloudEvents = typeof __propDef.events;
export type CloudSlots = typeof __propDef.slots;
export default class Cloud extends SvelteComponentTyped<CloudProps, CloudEvents, CloudSlots> {
}
export {};
