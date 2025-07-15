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
export type UserProps = typeof __propDef.props;
export type UserEvents = typeof __propDef.events;
export type UserSlots = typeof __propDef.slots;
export default class User extends SvelteComponentTyped<UserProps, UserEvents, UserSlots> {
}
export {};
