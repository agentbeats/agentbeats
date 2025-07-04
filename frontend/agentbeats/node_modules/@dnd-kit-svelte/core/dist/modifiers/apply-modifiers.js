export function applyModifiers(modifiers, { transform, ...args }) {
    return modifiers?.length
        ? modifiers.reduce((accumulator, modifier) => {
            return modifier({
                transform: accumulator,
                ...args,
            });
        }, transform)
        : transform;
}
