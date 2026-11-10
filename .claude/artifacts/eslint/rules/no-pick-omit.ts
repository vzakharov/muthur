import type { Rule, Scope, SourceCode } from "eslint";
import type * as ESTree from "estree";

import { SRC_ALIAS } from "../masd-graph.ts";

// Flags `Pick<X, …>` and `Omit<X, …>` where X is a type this repo declares. The
// narrow type is declared first and the wide one intersects it; carving the
// subset back out of the wide type names it without giving it a home. A type
// `z.infer`red from a schema follows the same order through a narrow schema the
// full one `z.extend`s, and is caught by the `typeof` in its target.
//
// X is the repo's when a name inside it — a type reference's root, or a
// `typeof` query's — resolves to a declaration in the file or an import from a
// relative or `#src/` path. A package import or a lib global (`Location`)
// cannot be declared narrow first, nor can a type parameter, so neither is
// flagged. Resolution is the scope manager's alone: no type information is
// read.

const UTILITIES = new Set(["Pick", "Omit"]);

/** Loosely-typed AST node: the TS-specific node kinds are not in @types/estree. */
type AstNode = ESTree.Node & Record<string, unknown>;

type Reference = AstNode & {
  typeName?: AstNode;
  exprName?: AstNode;
  typeArguments?: { params: AstNode[] };
  argument?: { literal?: ESTree.Literal };
};

/** A TS-only node `type` string, which @types/estree's union does not include. */
const tsType = (name: string): ESTree.Node["type"] =>
  name as ESTree.Node["type"];

/** The leftmost identifier of a dotted name (`Ns.Type`, `typeof value.key`). */
function rootOf(name: AstNode | undefined): ESTree.Identifier | undefined {
  let node = name;
  while (node?.type === tsType("TSQualifiedName")) {
    node = (node as { left?: AstNode }).left;
  }
  return node?.type === "Identifier" ? node : undefined;
}

function resolve(
  sourceCode: SourceCode,
  identifier: ESTree.Identifier,
): Scope.Variable | undefined {
  for (
    let scope: Scope.Scope | null = sourceCode.getScope(identifier);
    scope !== null;
    scope = scope.upper
  ) {
    const variable = scope.set.get(identifier.name);
    if (variable !== undefined) return variable;
  }
  return undefined;
}

function isRepoPath(source: unknown): boolean {
  return (
    typeof source === "string" &&
    (source.startsWith(".") || source.startsWith(SRC_ALIAS))
  );
}

/** A lib global carries no definitions; a type parameter is the caller's. */
function isRepoDeclared(variable: Scope.Variable | undefined): boolean {
  const definition = variable?.defs[0];
  if (definition === undefined) return false;
  if (definition.type === "ImportBinding") {
    return isRepoPath(definition.parent.source.value);
  }
  // The scope manager types a TS-only definition's node as `any`.
  return (definition.node as ESTree.Node).type !== tsType("TSTypeParameter");
}

/** Whether any name inside `root` — or an `import('…')` of it — is the repo's. */
function isRepoOwned(sourceCode: SourceCode, root: AstNode): boolean {
  const pending: AstNode[] = [root];
  for (let node = pending.pop(); node !== undefined; node = pending.pop()) {
    const reference = node as Reference;
    if (
      node.type === tsType("TSImportType") &&
      isRepoPath(reference.argument?.literal?.value)
    ) {
      return true;
    }
    const name =
      node.type === tsType("TSTypeReference")
        ? rootOf(reference.typeName)
        : node.type === tsType("TSTypeQuery")
          ? rootOf(reference.exprName)
          : undefined;
    if (name !== undefined && isRepoDeclared(resolve(sourceCode, name))) {
      return true;
    }
    for (const key of sourceCode.visitorKeys[node.type] ?? []) {
      const child = (node as Record<string, unknown>)[key];
      for (const each of Array.isArray(child) ? child : [child]) {
        if (typeof each === "object" && each !== null && "type" in each) {
          pending.push(each as AstNode);
        }
      }
    }
  }
  return false;
}

const rule: Rule.RuleModule = {
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Disallow Pick and Omit over the repo's own types — declare the narrow type first and build the wide one from it",
    },
    schema: [],
    messages: {
      carved:
        "`{{utility}}<{{target}}, …>` carves a subset out of a type this repo declares. Declare the narrow type first and build the wide one from it (`type Wide = Narrow & { … }`); for a schema-inferred type, declare the narrow schema and `z.extend` it.",
    },
  },

  create(context) {
    const { sourceCode } = context;

    return {
      [tsType("TSTypeReference")](node: ESTree.Node) {
        const reference = node as unknown as Reference;
        const utility = reference.typeName;
        if (utility?.type !== "Identifier") return;
        const { name } = utility as unknown as ESTree.Identifier;
        if (!UTILITIES.has(name)) return;
        // A local binding named `Pick` is someone else's type.
        if (resolve(sourceCode, utility)?.defs[0] !== undefined) return;
        const target = reference.typeArguments?.params[0];
        if (target === undefined || !isRepoOwned(sourceCode, target)) return;
        context.report({
          node,
          messageId: "carved",
          data: { utility: name, target: sourceCode.getText(target) },
        });
      },
    };
  },
};

export default rule;
