import * as parser from "@typescript-eslint/parser";
import { Linter } from "eslint";
import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

import rule from "./sub-slice-entry.ts";

const root = path.join(tmpdir(), "sub-slice-entry");

const linter = new Linter({ configType: "flat", cwd: root });

function reports(file: string, code: string): string[] {
  return linter
    .verify(
      code,
      [
        {
          files: ["**/*.ts"],
          languageOptions: { parser },
          plugins: { masd: { rules: { "sub-slice-entry": rule } } },
          rules: { "masd/sub-slice-entry": "error" },
        },
      ],
      path.join(root, file),
    )
    .map(({ message, ruleId }) => {
      assert.equal(ruleId, "masd/sub-slice-entry", message);
      return message;
    });
}

const DOCUMENT = "src/blog/entities/document";

describe("sub-slice-entry", () => {
  for (const [name, file, code] of [
    [
      "the slice entering a sub-slice by its barrel",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from '../prose/index.ts';",
    ],
    [
      "test code entering by the test-only barrel",
      `${DOCUMENT}/ui/source-list.test.ts`,
      "import { x } from '../prose/index.test-only.ts';",
    ],
    [
      "the slice’s test-only barrel entering the sub-slice’s",
      `${DOCUMENT}/index.test-only.ts`,
      "export { x } from './prose/index.test-only.ts';",
    ],
    [
      "a sub-slice’s files reaching each other",
      `${DOCUMENT}/prose/ui/content-link.ts`,
      "import { x } from '../model/link.ts';",
    ],
    [
      "a sub-slice reaching its parent",
      `${DOCUMENT}/prose/ui/content-link.ts`,
      "import { x } from '../../lib/x.ts';",
    ],
    [
      "a sub-slice entering its own nested one by its barrel",
      `${DOCUMENT}/prose/ui/content-link.ts`,
      "import { x } from '../inner/index.ts';",
    ],
    [
      "a folder inside a segment",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from './backdrop/x.ts';",
    ],
    [
      "another slice, which boundaries guards",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from '#src/blog/shared/content/prose/ui/x.ts';",
    ],
    [
      "a package import",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { z } from 'zod';",
    ],
  ] as const) {
    it(`allows ${name}`, () => {
      assert.deepEqual(reports(file, code), []);
    });
  }

  for (const [name, file, code, barrel] of [
    [
      "the slice reaching into a sub-slice",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from '../prose/ui/content-link.ts';",
      "../prose/index.ts",
    ],
    [
      "the slice reaching into a sub-slice by alias",
      `${DOCUMENT}/index.ts`,
      "export { x } from '#src/blog/entities/document/prose/ui/content-link.ts';",
      "./prose/index.ts",
    ],
    [
      "a sibling sub-slice reaching in",
      `${DOCUMENT}/cards/ui/document-cards.ts`,
      "import { x } from '../../prose/model/link.ts';",
      "../../prose/index.ts",
    ],
    [
      "a sub-slice reaching into its nested one",
      `${DOCUMENT}/prose/ui/content-link.ts`,
      "import { x } from '../inner/ui/x.ts';",
      "../inner/index.ts",
    ],
    [
      "shipped code taking the test-only barrel",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from '../prose/index.test-only.ts';",
      "../prose/index.ts",
    ],
    [
      "a sub-slice’s barrel under an unlisted suffix",
      `${DOCUMENT}/ui/source-list.ts`,
      "import { x } from '../prose/index.node-safe.ts';",
      "../prose/index.ts",
    ],
  ] as const) {
    it(`flags ${name}`, () => {
      const [message] = reports(file, code);
      assert.ok(
        message?.includes(`\`${barrel}\``) === true,
        `${message ?? "no report"} should name ${barrel}`,
      );
    });
  }
});
