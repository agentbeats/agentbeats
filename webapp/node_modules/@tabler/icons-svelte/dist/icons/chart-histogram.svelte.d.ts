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
export type ChartHistogramProps = typeof __propDef.props;
export type ChartHistogramEvents = typeof __propDef.events;
export type ChartHistogramSlots = typeof __propDef.slots;
export default class ChartHistogram extends SvelteComponentTyped<ChartHistogramProps, ChartHistogramEvents, ChartHistogramSlots> {
}
export {};
