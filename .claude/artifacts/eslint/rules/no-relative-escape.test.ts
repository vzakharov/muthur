import * as parser from "@typescript-eslint/parser";
import { Linter } from "eslint";
import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

import rule from "./no-relative-escape.ts";

const root = path.join(tmpdir(), "no-relative-escape");

const linter = new Linter({ configType: "flat", cwd: root });

function reports(file: string, code: string): string[] {
  return linter
    .verify(
      code,
      [
        {
          files: ["**/*.ts"],
          languageOptions: { parser },
          plugins: { masd: { rules: { "no-relative-escape": rule } } },
          rules: { "masd/no-relative-escape": "error" },
        },
      ],
      path.join(root, file),
    )
    .map(({ message, ruleId }) => {
      assert.equal(ruleId, "masd/no-relative-escape", message);
      return message;
    });
}

describe("no-relative-escape", () => {
  for (const [name, file, code] of [
    [
      "a sibling segment of the same slice",
      "src/blog/pages/documents/ui/page.ts",
      "import { x } from '../lib/x.ts';",
    ],
    [
      "a nested file reaching its slice root",
      "src/mushrooms/pages/mushrooms/ui/scene/sky.ts",
      "import { x } from '../../model/x.ts';",
    ],
    [
      "another segment of a segmented layer",
      "src/shell/app/ui/root-layout.ts",
      "import '../styles/globals.ts';",
    ],
    [
      "a script inside its app scripts",
      "src/music/scripts/lib/cards.ts",
      "import { x } from '../masters.ts';",
    ],
    [
      "a file outside src",
      "scripts/check.ts",
      "import '../src/kernel/shared/content/paths.ts';",
    ],
    [
      "a package import",
      "src/blog/pages/documents/ui/page.ts",
      "import { z } from 'zod';",
    ],
  ] as const) {
    it(`allows ${name}`, () => {
      assert.deepEqual(reports(file, code), []);
    });
  }

  for (const [name, file, code, alias] of [
    [
      "another slice of the same layer",
      "src/blog/pages/documents/ui/page.ts",
      "import { x } from '../../feed/ui/x.ts';",
      "#src/blog/pages/feed/ui/x.ts",
    ],
    [
      "an ancestor app",
      "src/basilisk/shared/content/frontmatter.ts",
      "import { x } from '../../../kernel/shared/content/frontmatter.ts';",
      "#src/kernel/shared/content/frontmatter.ts",
    ],
    [
      "a script reaching another app",
      "src/basilisk/scripts/lib/docket.ts",
      "import type { X } from '../../../kernel/scripts/lib/read-collection.ts';",
      "#src/kernel/scripts/lib/read-collection.ts",
    ],
    [
      "a script reaching its own app layers",
      "src/kernel/scripts/lib/walk.ts",
      "import '../../shared/content/paths.ts';",
      "#src/kernel/shared/content/paths.ts",
    ],
    [
      "a dynamic import of its own app layers",
      "src/music/scripts/masters.ts",
      "const m = await import('../shared/catalogue/index.ts');",
      "#src/music/shared/catalogue/index.ts",
    ],
  ] as const) {
    it(`flags ${name}`, () => {
      const [message] = reports(file, code);
      assert.ok(
        message?.includes(`\`${alias}\``) === true,
        `${message ?? "no report"} should name ${alias}`,
      );
    });
  }
});
