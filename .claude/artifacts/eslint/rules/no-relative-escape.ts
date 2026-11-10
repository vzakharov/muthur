import type { Rule } from "eslint";
import type * as ESTree from "estree";
import path from "node:path";

import { SLICED_LAYERS, SRC_ALIAS } from "../masd-graph.ts";

// A relative import under `src/` stays inside the importer's home — its slice,
// its segmented layer (`app` and `shared` overlay as one unit), or its app's
// `scripts/` — and anything past it is reached by its `#src/` path, so an import
// says which app and layer it enters.

/** The directory, relative to `src/`, a file under it may reach relatively. */
function relativeHome(fromSrc: string): string | undefined {
  const [app, layer, unit, ...rest] = fromSrc.split(path.sep);
  if (app === undefined || layer === undefined || unit === undefined) {
    return undefined;
  }
  return SLICED_LAYERS.includes(layer) && rest.length > 0
    ? path.join(app, layer, unit)
    : path.join(app, layer);
}

const rule: Rule.RuleModule = {
  meta: {
    type: "suggestion",
    docs: {
      description:
        "Disallow a relative import under src/ that leaves its slice, segmented layer or app scripts",
    },
    schema: [],
    messages: {
      escapes:
        "This relative import leaves `src/{{home}}`: import it as `{{alias}}`.",
    },
  },

  create(context) {
    const src = path.join(context.cwd, "src");
    const fromSrc = path.relative(src, context.filename);
    const home = fromSrc.startsWith("..") ? undefined : relativeHome(fromSrc);
    if (home === undefined) return {};

    const check = (source: ESTree.Node | null | undefined): void => {
      if (
        source?.type !== "Literal" ||
        typeof source.value !== "string" ||
        !source.value.startsWith(".")
      ) {
        return;
      }
      const target = path.relative(
        src,
        path.resolve(path.dirname(context.filename), source.value),
      );
      if (target === home || target.startsWith(home + path.sep)) return;

      const alias = `${SRC_ALIAS}${target.split(path.sep).join("/")}`;
      context.report({
        node: source,
        messageId: "escapes",
        data: { home, alias },
      });
    };

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
