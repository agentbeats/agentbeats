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
export type CrossProps = typeof __propDef.props;
export type CrossEvents = typeof __propDef.events;
export type CrossSlots = typeof __propDef.slots;
export default class Cross extends SvelteComponentTyped<CrossProps, CrossEvents, CrossSlots> {
}
export {};
