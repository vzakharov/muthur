#!/usr/bin/env node

/**
 * Steiger over every app root in `src/masd.json`, one run each:
 *
 *   pnpm lint:fsd
 *
 * Steiger finds no FSD root above several of them, and each app is an FSD tree
 * of its own, so a root is the unit it can check. What crosses roots —
 * imports between apps, and a slice earned only by its descendants' use — is
 * `eslint-plugin-boundaries` and `scripts/masd-check.ts`.
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

import { loadGraph } from "../eslint/masd-graph.ts";

const ARTIFACTS_ROOT = path.join(import.meta.dirname, "..");

// Run from `.claude/artifacts/`, where `steiger.config.ts` resolves. An app
// with no directory is `check:masd`'s to report: Steiger would answer a missing
// path with an interactive prompt.
const failed = [...loadGraph().keys()].filter(
  (app) =>
    existsSync(path.join(ARTIFACTS_ROOT, "src", app)) &&
    spawnSync("pnpm", ["exec", "steiger", `src/${app}`], {
      cwd: ARTIFACTS_ROOT,
      stdio: "inherit",
    }).status !== 0,
);

if (failed.length > 0) {
  process.stderr.write(`lint:fsd: Steiger failed on ${failed.join(", ")}\n`);
  process.exitCode = 1;
}
