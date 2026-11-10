/**
 * The promotion check: a consumer taking from a slice or sub-slice only what
 * one of its sub-slices exports, and the layers that sub-slice may move to.
 */

import { readFileSync } from "node:fs";
import path from "node:path";
import ts from "typescript";

import {
  isPublicApi,
  isTest,
  LAYERS,
  SLICED_LAYERS,
} from "../../../eslint/masd-graph.ts";
import { resolveImport, sourceFile } from "../import-graph.ts";
import { carriesMarker } from "../masd-marker.ts";
import { sliceOf, subSlicesOf, unitsOf, within } from "../slice-graph.ts";
import { reaches, type Siblings } from "./siblings.ts";

/** The names a statement takes from its module, `*` standing for all of them. */
function namesTaken(statement: ts.Statement): string[] {
  if (ts.isImportDeclaration(statement)) {
    const clause = statement.importClause;
    if (clause === undefined) return ["*"];
    const bindings = clause.namedBindings;
    return [
      ...(clause.name === undefined ? [] : ["default"]),
      ...(bindings === undefined
        ? []
        : ts.isNamespaceImport(bindings)
          ? ["*"]
          : bindings.elements.map(
              (element) => (element.propertyName ?? element.name).text,
            )),
    ];
  }
  if (ts.isExportDeclaration(statement)) {
    const clause = statement.exportClause;
    return clause !== undefined && ts.isNamedExports(clause)
      ? clause.elements.map(
          (element) => (element.propertyName ?? element.name).text,
        )
      : ["*"];
  }
  return [];
}

/** Each import or re-export of `file`, as the file it loads and the names it takes. */
function takes(file: string): [string, string[]][] {
  const source = ts.createSourceFile(
    file,
    readFileSync(file, "utf8"),
    ts.ScriptTarget.Latest,
  );
  return source.statements.flatMap((statement) => {
    const specifier =
      ts.isImportDeclaration(statement) || ts.isExportDeclaration(statement)
        ? statement.moduleSpecifier
        : undefined;
    if (specifier === undefined || !ts.isStringLiteral(specifier)) return [];
    const resolved = resolveImport(file, specifier.text);
    const loaded = resolved === undefined ? undefined : sourceFile(resolved);
    return loaded === undefined
      ? []
      : [[loaded, namesTaken(statement)] as [string, string[]]];
  });
}

/** Where a shipped file consumes from: its slice or its segmented layer. */
function consumerOf(file: string): string | undefined {
  const parts = file.split(path.sep);
  if (parts[2] === "scripts" || isTest(file)) return undefined;
  return sliceOf(file) ?? parts.slice(0, 3).join(path.sep);
}

/**
 * Where `file` takes the barrel `loaded` from, when that barrel is a slice's or
 * a sub-slice's entered from outside it: for a slice, `consumerOf`; for a
 * sub-slice, the place in its parent the file sits in — a sibling sub-slice, or
 * the parent's own segments. `target` is the slice or sub-slice and `parent`
 * the one that holds it, `undefined` for a slice.
 */
function enteredFrom(
  file: string,
  loaded: string,
): { consumer: string; target: string; parent?: string } | undefined {
  const slice = sliceOf(loaded);
  const target = path.dirname(loaded);
  if (slice === undefined || !isPublicApi(loaded)) {
    return undefined;
  }
  if (target === slice) {
    const consumer = consumerOf(file);
    return consumer === undefined || consumer === slice
      ? undefined
      : { consumer, target };
  }
  const chain = unitsOf(loaded, slice);
  if (chain.at(-1) !== target || sliceOf(file) !== slice) return undefined;
  if (within(file, target)) return undefined;
  const parent = chain.at(-2) ?? slice;
  const consumer =
    subSlicesOf(file, slice).find((sub) => path.dirname(sub) === parent) ??
    parent;
  return { consumer, target, parent };
}

/** A file's FSD layer, for a file in one; an app's scripts and the like have none. */
function layerOf(file: string): string | undefined {
  const [root, , layer = ""] = file.split(path.sep);
  return root === "src" && LAYERS.includes(layer) ? layer : undefined;
}

/** A layer's height, highest first. */
const rank = (layer: string): number => LAYERS.indexOf(layer);

/** Whether a layer may be imported by `importer`'s, `shared` by `shared` included. */
const below = (importer: string) => (layer: string) =>
  rank(layer) > rank(importer) || (layer === "shared" && importer === "shared");

/** Whether a layer may import `imported`'s; every layer may import `shared`. */
const above = (imported: string) => (layer: string) =>
  imported === "shared" || rank(layer) < rank(imported);

/**
 * The layers a sub-slice of `slice` promoted to a slice of its own may land
 * on, in its app: strictly below each layer importing it — `takers` through
 * the slice's barrels, its siblings directly — and strictly above each sliced
 * layer it imports, `shared` taking from `shared` as segments do. Which of them
 * fits is a call on what the piece is, so this only narrows it.
 */
function destinations(
  sub: string,
  slice: string,
  takers: ReadonlySet<string>,
  imports: ReadonlyMap<string, ReadonlySet<string>>,
): string[] {
  const bars = [...takers].flatMap((file) => {
    const layer = layerOf(file);
    return layer === undefined ? [] : [below(layer)];
  });
  const isBarrel = (file: string): boolean =>
    path.dirname(file) === slice && isPublicApi(file);
  for (const [from, targets] of imports) {
    const inside = within(from, sub);
    if (!inside && isBarrel(from)) continue;
    for (const to of targets) {
      if (within(to, sub) === inside) continue;
      const other = layerOf(inside ? to : from);
      if (other !== undefined) bars.push((inside ? above : below)(other));
    }
  }
  return [...SLICED_LAYERS, "shared"].filter((layer) =>
    bars.every((fits) => fits(layer)),
  );
}

/**
 * Consumers that take from a slice or a sub-slice only what one of its
 * sub-slices exports: that sub-slice belongs one level out, where both can
 * import it — a slice of its own, on a layer `destinations` lists, or a
 * sub-slice beside the one it sits in. One that imports every sibling,
 * directly or not, is the unit's head, and a consumer of the head needs the
 * whole unit.
 */
export function promotions(
  files: readonly string[],
  imports: ReadonlyMap<string, ReadonlySet<string>>,
  graphs: ReadonlyMap<string, Siblings>,
): string[] {
  const isHead = (sub: string, unit: string): boolean => {
    const graph = graphs.get(unit);
    if (graph === undefined) return false;
    const reached = reaches(graph, sub);
    return [...graph.keys()].every(
      (sibling) => sibling === sub || reached.has(sibling),
    );
  };

  // A barrel's every export name, as the sub-slice of `target` it comes from.
  const origins = new Map<string, Map<string, string | undefined>>();
  const originsOf = (barrel: string, target: string) => {
    const known = origins.get(barrel);
    if (known !== undefined) return known;
    const named = new Map<string, string | undefined>();
    for (const [loaded, names] of takes(barrel)) {
      const [sub] = subSlicesOf(loaded, target);
      for (const name of names) named.set(name, sub);
    }
    origins.set(barrel, named);
    return named;
  };

  const taken = new Map<
    string,
    { subs: Set<string | undefined>; parent?: string | undefined }
  >();
  // Each sub-slice, as the files taking its exports through a barrel.
  const takers = new Map<string, Set<string>>();
  for (const file of files) {
    if (isTest(file)) continue;
    for (const [loaded, names] of takes(file)) {
      const entry = enteredFrom(file, loaded);
      if (entry === undefined) continue;
      const { consumer, target, parent } = entry;
      const named = originsOf(loaded, target);
      const key = `${consumer}\n${target}`;
      const record = taken.get(key) ?? { subs: new Set(), parent };
      for (const name of names) {
        const sub = named.get(name);
        record.subs.add(sub);
        if (sub !== undefined) {
          takers.set(sub, (takers.get(sub) ?? new Set()).add(file));
        }
      }
      taken.set(key, record);
    }
  }

  return [...taken].flatMap(([key, { subs, parent }]) => {
    const [consumer = "", target = ""] = key.split("\n");
    const [sub, ...others] = subs;
    if (sub === undefined || others.length > 0 || isHead(sub, target)) {
      return [];
    }
    const barrel = path.join(sub, "index.ts");
    if (carriesMarker(barrel, "promotion")) {
      return [];
    }
    const layers =
      parent === undefined
        ? destinations(sub, target, takers.get(sub) ?? new Set(), imports)
        : [];
    const remedy =
      parent === undefined
        ? layers.length === 0
          ? "promote it to a slice of its own that both can import, though no layer of its app lies below what imports it and above what it imports"
          : `promote it to a slice of its own that both can import, on ${layers.map((layer) => `"${layer}"`).join(" or ")} — whichever names what it is`
        : `move it up into ${parent}, beside "${path.basename(target)}", so both import it from there`;
    return [
      `${consumer} takes from ${target} only its sub-slice "${path.basename(sub)}": ${remedy}. Where the import rules leave it nowhere to go, ask the operator, and on their yes put "// masd-disable promotion -- <why it cannot move>" in ${barrel}.`,
    ];
  });
}
