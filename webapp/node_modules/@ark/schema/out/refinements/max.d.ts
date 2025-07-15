import type { BaseRoot } from "../roots/root.js";
import type { BaseErrorContext, declareNode } from "../shared/declare.js";
import { type nodeImplementationOf } from "../shared/implement.js";
import type { JsonSchema } from "../shared/jsonSchema.js";
import type { TraverseAllows } from "../shared/traversal.js";
import { BaseRange, type BaseRangeInner, type UnknownExpandedRangeSchema } from "./range.js";
export declare namespace Max {
    interface Inner extends BaseRangeInner {
        rule: number;
        exclusive?: true;
    }
    interface NormalizedSchema extends UnknownExpandedRangeSchema {
        rule: number;
    }
    type Schema = NormalizedSchema | number;
    interface ErrorContext extends BaseErrorContext<"max">, Inner {
    }
    interface Declaration extends declareNode<{
        kind: "max";
        schema: Schema;
        normalizedSchema: NormalizedSchema;
        inner: Inner;
        prerequisite: number;
        errorContext: ErrorContext;
    }> {
    }
    type Node = MaxNode;
}
export declare class MaxNode extends BaseRange<Max.Declaration> {
    impliedBasis: BaseRoot;
    traverseAllows: TraverseAllows<number>;
    reduceJsonSchema(schema: JsonSchema.Numeric): JsonSchema.Numeric;
}
export declare const Max: {
    implementation: nodeImplementationOf<Max.Declaration>;
    Node: typeof MaxNode;
};
