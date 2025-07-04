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
export type LogoutProps = typeof __propDef.props;
export type LogoutEvents = typeof __propDef.events;
export type LogoutSlots = typeof __propDef.slots;
export default class Logout extends SvelteComponentTyped<LogoutProps, LogoutEvents, LogoutSlots> {
}
export {};
