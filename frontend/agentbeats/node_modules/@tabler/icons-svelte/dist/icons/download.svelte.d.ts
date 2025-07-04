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
export type DownloadProps = typeof __propDef.props;
export type DownloadEvents = typeof __propDef.events;
export type DownloadSlots = typeof __propDef.slots;
export default class Download extends SvelteComponentTyped<DownloadProps, DownloadEvents, DownloadSlots> {
}
export {};
