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
export type EditProps = typeof __propDef.props;
export type EditEvents = typeof __propDef.events;
export type EditSlots = typeof __propDef.slots;
export default class Edit extends SvelteComponentTyped<EditProps, EditEvents, EditSlots> {
}
export {};
