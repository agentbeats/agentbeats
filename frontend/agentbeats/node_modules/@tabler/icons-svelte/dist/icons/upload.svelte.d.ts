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
export type UploadProps = typeof __propDef.props;
export type UploadEvents = typeof __propDef.events;
export type UploadSlots = typeof __propDef.slots;
export default class Upload extends SvelteComponentTyped<UploadProps, UploadEvents, UploadSlots> {
}
export {};
