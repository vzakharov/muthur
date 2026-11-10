/**
 * The sub-slices' checks that read the folders alone: where a sub-slice is, and
 * what may sit beside one.
 */

import { existsSync, readdirSync } from "node:fs";
import path from "node:path";

import {
  isPublicApi,
  isTest,
  SEGMENTS,
  SLICED_LAYERS,
} from "../../../eslint/masd-graph.ts";
import { SOURCE, subdirectories } from "../import-graph.ts";

/** The paths of the slices in `apps`' sliced layers. */
const slicesIn = (apps: readonly string[]): string[] =>
  apps.flatMap((app) =>
    SLICED_LAYERS.flatMap((layer) => {
      const directory = path.join("src", app, layer);
      return existsSync(directory)
        ? subdirectories(directory).map((slice) => path.join(directory, slice))
        : [];
    }),
  );

/** The sub-slices directly in `unit`, as paths. */
function childSubSlices(unit: string): string[] {
  return (
    readdirSync(unit, { withFileTypes: true })
      // A folder holding no source, such as one of images, is no sub-slice.
      .filter(
        (entry) =>
          entry.isDirectory() &&
          !SEGMENTS.includes(entry.name) &&
          readdirSync(path.join(unit, entry.name), { recursive: true }).some(
            (file) => SOURCE.test(String(file)),
          ),
      )
      .map((entry) => path.join(unit, entry.name))
  );
}

/** The slices in `apps` cut into sub-slices. */
export const slicesWithSubSlices = (apps: readonly string[]): string[] =>
  slicesIn(apps).filter((slice) => childSubSlices(slice).length > 0);

/**
 * A segment's name below a segment, which Steiger's `no-reserved-folder-names`
 * would catch were it not off in the sliced layers for the sub-slices' sake.
 */
export function nestedSegments(apps: readonly string[]): string[] {
  return slicesIn(apps).flatMap((slice) =>
    readdirSync(slice, { recursive: true, withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .flatMap((entry) => {
        const folder = path.join(entry.parentPath, entry.name);
        const dirs = path.relative(slice, folder).split(path.sep);
        const segment = dirs.findIndex((dir) => SEGMENTS.includes(dir));
        return segment !== -1 &&
          segment < dirs.length - 1 &&
          SEGMENTS.includes(entry.name)
          ? [
              `${folder}: "${entry.name}" names a segment, inside segment "${dirs[segment] ?? ""}"; a folder in a segment takes a name of its own`,
            ]
          : [];
      }),
  );
}

/**
 * What sits at the root of a slice or sub-slice holding a sub-slice, other than
 * its sub-slices, its barrels and its tests: such a unit is cut all the way, so
 * the rest of it is a sub-slice of its own, named for its noun.
 */
export function mixed(apps: readonly string[]): string[] {
  const inUnit = (unit: string): string[] => {
    const subs = childSubSlices(unit);
    const below = subs.flatMap((sub) => inUnit(sub));
    if (subs.length === 0) return below;
    const loose = readdirSync(unit, { withFileTypes: true })
      .filter((entry) =>
        entry.isDirectory()
          ? SEGMENTS.includes(entry.name)
          : !isPublicApi(entry.name) && !isTest(path.join(unit, entry.name)),
      )
      .map((entry) => `"${entry.name}"`);
    return loose.length === 0
      ? below
      : [
          `${unit}: ${loose.join(", ")} beside its sub-slices; a unit holding a sub-slice holds only sub-slices and barrels, so move the rest into a sub-slice named for its noun`,
          ...below,
        ];
  };
  return slicesIn(apps).flatMap((slice) => inUnit(slice));
}
