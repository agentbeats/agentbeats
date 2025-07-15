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
export type FolderOpenProps = typeof __propDef.props;
export type FolderOpenEvents = typeof __propDef.events;
export type FolderOpenSlots = typeof __propDef.slots;
export default class FolderOpen extends SvelteComponentTyped<FolderOpenProps, FolderOpenEvents, FolderOpenSlots> {
}
export {};
