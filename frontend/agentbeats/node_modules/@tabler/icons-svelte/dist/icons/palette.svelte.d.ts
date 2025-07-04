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
export type PaletteProps = typeof __propDef.props;
export type PaletteEvents = typeof __propDef.events;
export type PaletteSlots = typeof __propDef.slots;
export default class Palette extends SvelteComponentTyped<PaletteProps, PaletteEvents, PaletteSlots> {
}
export {};
