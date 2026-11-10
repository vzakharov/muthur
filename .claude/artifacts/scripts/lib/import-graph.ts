/**
 * The file walk and import resolution the import-graph scripts share, so no two
 * of them disagree on where an import lands. Every path is relative to the
 * working directory, which is `.claude/artifacts` or a test's tree.
 */

import { existsSync, readdirSync } from "node:fs";
import path from "node:path";

import { SRC_ALIAS } from "../../eslint/masd-graph.ts";

export const SOURCE = /\.tsx?$/;

/** Every `.ts`/`.tsx` file under `directory`, at any depth. */
export const walk = (directory: string): string[] =>
  readdirSync(directory, { withFileTypes: true, recursive: true })
    .filter((entry) => entry.isFile() && SOURCE.test(entry.name))
    .map((entry) =>
      path.relative(process.cwd(), path.join(entry.parentPath, entry.name)),
    );

export const subdirectories = (directory: string): string[] =>
  readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);

/** Every source file of the apps under `src/`. */
export const appFiles = (): string[] => walk("src");

/** The path a specifier names; a package specifier names none. */
export function resolveImport(
  from: string,
  specifier: string,
): string | undefined {
  if (specifier.startsWith(SRC_ALIAS)) {
    return path.join("src", specifier.slice(SRC_ALIAS.length));
  }
  if (specifier.startsWith(".")) {
    return path.join(path.dirname(from), specifier);
  }
  return undefined;
}

/**
 * The source file a resolved path loads, if it exists. Imports spell their
 * extension, so the path is the file.
 */
export const sourceFile = (resolved: string): string | undefined =>
  SOURCE.test(resolved) && existsSync(resolved) ? resolved : undefined;
