// ESLint configuration philosophy: every rule is either enabled as 'error' or
// disabled with a comment explaining why; severity is 'error' or 'off', never
// 'warn'. This file only orchestrates: the typescript-eslint presets, the
// boundaries config generated from `src/masd.json`, the three `masd/*` rules and
// the ignores.
//
// Type-aware linting runs through the project service over `tsconfig.json`.
// Formatting is Prettier's alone (`scripts/prettier.sh --check`).
//
// This config is TypeScript; ESLint loads it via jiti (a direct devDependency).

import { defineConfig, globalIgnores } from "eslint/config";
import tseslint from "typescript-eslint";

import { boundariesConfig } from "./eslint/masd-boundaries.ts";
import noPickOmit from "./eslint/rules/no-pick-omit.ts";
import noRelativeEscape from "./eslint/rules/no-relative-escape.ts";
import subSliceEntry from "./eslint/rules/sub-slice-entry.ts";

export default defineConfig([
  globalIgnores(["node_modules/", "types/"]),
  tseslint.configs.strictTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  {
    rules: {
      // A number in a template literal stringifies unambiguously.
      "@typescript-eslint/restrict-template-expressions": [
        "error",
        { allowNumber: true },
      ],
    },
  },
  {
    files: ["**/*.test.ts"],
    rules: {
      // node:test's `describe` and `it` register through side effects, and the
      // runner collects their promises itself.
      "@typescript-eslint/no-floating-promises": "off",
    },
  },
  boundariesConfig,
  {
    files: ["src/**/*.{ts,tsx}"],
    plugins: {
      masd: {
        rules: {
          "no-pick-omit": noPickOmit,
          "no-relative-escape": noRelativeEscape,
          "sub-slice-entry": subSliceEntry,
        },
      },
    },
    rules: {
      "masd/no-pick-omit": "error",
      "masd/no-relative-escape": "error",
      "masd/sub-slice-entry": "error",
    },
  },
]);
