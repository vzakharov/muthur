import type { Rule } from "eslint";
import type * as ESTree from "estree";
import path from "node:path";

import {
  isTest,
  PUBLIC_API,
  SLICED_LAYERS,
  SRC_ALIAS,
  subSlicePath,
  TEST_API,
} from "../masd-graph.ts";

// `boundaries` reads a slice as one element, so it lets a slice's files reach
// each other anywhere. A sub-slice is a wall inside it: what sits outside the
// sub-slice enters it by its barrel, just as other slices enter the slice.

/** A path under `src/` split into its slice root and the parts below it. */
function inSlice(fromSrc: string): [string, string[]] | undefined {
  const [app, layer, slice, ...rest] = fromSrc.split(path.sep);
  if (
    app === undefined ||
    layer === undefined ||
    slice === undefined ||
    !SLICED_LAYERS.includes(layer)
  ) {
    return undefined;
  }
  return [path.join(app, layer, slice), rest];
}

const rule: Rule.RuleModule = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Require an import into a sub-slice from outside it to go through its barrel",
    },
    schema: [],
    messages: {
      bypasses:
        "This import reaches inside sub-slice `{{subSlice}}`: import its barrel, `{{barrel}}`, instead.",
    },
  },

  create(context) {
    const src = path.join(context.cwd, "src");
    const fromSrc = path.relative(src, context.filename);
    const from = fromSrc.startsWith("..") ? undefined : inSlice(fromSrc);
    if (from === undefined) return {};
    const [root, fromParts] = from;
    const own = new Set(subSlicePath(fromParts.slice(0, -1)));
    const entries = isTest(context.filename)
      ? [...PUBLIC_API, TEST_API]
      : PUBLIC_API;

    function check(source: ESTree.Node | null | undefined): void {
      if (source?.type !== "Literal" || typeof source.value !== "string") {
        return;
      }
      const specifier = source.value;
      const target = specifier.startsWith(SRC_ALIAS)
        ? specifier.slice(SRC_ALIAS.length)
        : specifier.startsWith(".")
          ? path.relative(
              src,
              path.resolve(path.dirname(context.filename), specifier),
            )
          : undefined;
      const to = target === undefined ? undefined : inSlice(target);
      if (to?.[0] !== root) return;
      const toParts = to[1];
      const subSlice = subSlicePath(toParts.slice(0, -1)).find(
        (candidate) => !own.has(candidate),
      );
      if (subSlice === undefined) return;
      const entry = toParts.slice(subSlice.split("/").length).join("/");
      if (entries.includes(entry)) return;

      const barrel = path.relative(
        path.dirname(context.filename),
        path.join(src, root, subSlice, "index.ts"),
      );
      context.report({
        node: source,
        messageId: "bypasses",
        data: {
          subSlice,
          barrel: barrel.startsWith(".") ? barrel : `./${barrel}`,
        },
      });
    }

    return {
      ImportDeclaration(node) {
        check(node.source);
      },
      ExportNamedDeclaration(node) {
        check(node.source);
      },
      ExportAllDeclaration(node) {
        check(node.source);
      },
      ImportExpression(node) {
        check(node.source);
      },
    };
  },
};

export default rule;
