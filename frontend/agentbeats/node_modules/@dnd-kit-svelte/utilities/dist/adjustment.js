function createAdjustmentFn(modifier) {
    return (object, ...adjustments) => {
        return adjustments.reduce((accumulator, adjustment) => {
            const entries = Object.entries(adjustment);
            for (const [key, valueAdjustment] of entries) {
                const value = accumulator[key];
                if (value != null) {
                    accumulator[key] = (value + modifier * valueAdjustment);
                }
            }
            return accumulator;
        }, {
            ...object,
        });
    };
}
export const add = createAdjustmentFn(1);
export const subtract = createAdjustmentFn(-1);
