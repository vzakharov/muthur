// End-to-end tests for `pnpm check:masd` on sub-slices; the harness is
// masd-check.test-kit.ts.

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { run, type Tree } from "./masd-check.test-kit.ts";

// A card entity cut into `face` and `back`; both pages take `face`, documents
// `back` as well.
const CARD = "src/blog/entities/card";
const CARDS: Tree = {
  [`${CARD}/index.ts`]:
    "export { face } from './face/index.ts';\nexport { back } from './back/index.ts';",
  [`${CARD}/back/index.ts`]: "export { back } from './ui/back.ts';",
  [`${CARD}/back/ui/back.ts`]: "export { edge as back } from './edge.ts';",
  [`${CARD}/back/ui/edge.ts`]: "export const edge = 1;",
  [`${CARD}/face/index.ts`]: "export { face } from './ui/face.ts';",
  [`${CARD}/face/ui/face.ts`]: "export { lens as face } from './lens.ts';",
  [`${CARD}/face/ui/lens.ts`]: "export const lens = 1;",
  "src/site/pages/home/ui.ts":
    "import { face } from '#src/blog/entities/card/index.ts';\nexport const home = face;",
  "src/blog/pages/documents/ui.ts":
    "import { back, face } from '#src/blog/entities/card/index.ts';\nexport const documents = [back, face];",
};

const PROMOTE_FACE = `src/site/pages/home takes from ${CARD} only its sub-slice "face"`;

// The card with a third sub-slice, `bits`, that only `back` imports; both
// pages take the whole card, so no consumer is flagged.
const BITS: Tree = {
  ...CARDS,
  "src/site/pages/home/ui.ts":
    "import { back, face } from '#src/blog/entities/card/index.ts';\nexport const home = [back, face];",
  [`${CARD}/back/ui/back.ts`]:
    "import { bit } from '../../bits/index.ts';\nexport { edge as back } from './edge.ts';\nexport const b = bit;",
  [`${CARD}/back/ui/edge.ts`]:
    "import { bit } from '../../bits/index.ts';\nexport const edge = bit;",
  [`${CARD}/bits/index.ts`]: "export const bit = 1;",
};

describe("masd-check on sub-slices", () => {
  it("flags a segment named inside a segment", () => {
    const { status, stderr } = run({
      "src/blog/pages/documents/ui/model/x.ts": "export {};",
    });
    assert.equal(status, 1);
    assert.equal(
      stderr,
      'src/blog/pages/documents/ui/model: "model" names a segment, inside segment "ui"; a folder in a segment takes a name of its own\n',
    );
  });

  it("flags a consumer taking only one sub-slice", () => {
    const { status, stderr } = run(CARDS);
    assert.equal(status, 1);
    assert.equal(stderr.split("\n").length, 2);
    assert.ok(stderr.startsWith(PROMOTE_FACE), stderr);
    assert.match(
      stderr,
      /on "widgets" or "features" or "entities" or "shared" — whichever names what it is/,
    );
    assert.match(stderr, /masd-disable promotion -- <why it cannot move>/);
  });

  it("lists only the layers below what imports the sub-slice", () => {
    // `back` imports `face` too, so `face` has to sit below the card's layer.
    const { stderr } = run({
      ...CARDS,
      [`${CARD}/back/ui/back.ts`]:
        "import { face } from '../../face/index.ts';\nexport { edge as back } from './edge.ts';\nexport const faced = face;",
    });
    assert.match(
      stderr,
      new RegExp(String.raw`${PROMOTE_FACE}: [^\n]* on "shared" —`),
    );
  });

  it("says when no layer lies between what imports and what is imported", () => {
    // `face` takes a widget while pages take it: nothing sits strictly between.
    const { stderr } = run({
      ...CARDS,
      [`${CARD}/face/ui/lens.ts`]:
        "import { panel } from '#src/blog/widgets/panel/index.ts';\nexport const lens = panel;",
      "src/blog/widgets/panel/index.ts":
        "export { panel } from './ui/panel.ts';",
      "src/blog/widgets/panel/ui/panel.ts": "export const panel = 1;",
    });
    assert.match(stderr, /no layer of its app lies below what imports it/);
  });

  it("spares a sub-slice whose barrel says why it stays", () => {
    const { status, stderr } = run({
      ...CARDS,
      [`${CARD}/face/index.ts`]:
        "// masd-disable promotion -- nowhere both can import\nexport { face } from './ui/face.ts';",
    });
    assert.deepEqual({ status, stderr }, { status: 0, stderr: "" });
  });

  it("flags a sibling sub-slice taking only one sub-slice of another", () => {
    // `face` is cut into `look` and `glint`; the card's sibling `shine` takes
    // only `glint` through `face`'s barrel, so `glint` belongs beside `face`.
    const { stderr } = run({
      ...Object.fromEntries(
        Object.entries(CARDS).filter(
          ([file]) => !file.startsWith(`${CARD}/face/`),
        ),
      ),
      "src/site/pages/home/ui.ts":
        "import { back, face, shine } from '#src/blog/entities/card/index.ts';\nexport const home = [back, face, shine];",
      [`${CARD}/index.ts`]:
        "export { face } from './face/index.ts';\nexport { shine } from './shine/index.ts';\nexport { back } from './back/index.ts';",
      [`${CARD}/face/index.ts`]:
        "export { glint } from './glint/index.ts';\nexport { face } from './look/index.ts';",
      [`${CARD}/face/look/index.ts`]: "export { face } from './ui/face.ts';",
      [`${CARD}/face/look/ui/face.ts`]:
        "export { lens as face } from './lens.ts';",
      [`${CARD}/face/look/ui/lens.ts`]: "export const lens = 1;",
      [`${CARD}/face/glint/index.ts`]: "export { glint } from './ui/glint.ts';",
      [`${CARD}/face/glint/ui/glint.ts`]:
        "import { spark } from './spark.ts';\nexport const glint = spark;",
      [`${CARD}/face/glint/ui/spark.ts`]: "export const spark = 1;",
      [`${CARD}/shine/index.ts`]: "export { shine } from './ui/shine.ts';",
      [`${CARD}/shine/ui/shine.ts`]:
        "import { glint } from '../../face/index.ts';\nimport { ray } from './ray.ts';\nexport const shine = [glint, ray];",
      [`${CARD}/shine/ui/ray.ts`]: "export const ray = 1;",
    });
    const moveUp = `${CARD}/shine takes from ${CARD}/face only its sub-slice "glint": move it up into ${CARD}, beside "face", so both import it from there.`;
    assert.ok(
      stderr.split("\n").some((line) => line.startsWith(moveUp)),
      stderr,
    );
  });

  it("flags a sub-slice one sibling leans on throughout", () => {
    const { stderr } = run(BITS);
    assert.equal(
      stderr,
      `${CARD}/bits: This sub-slice neither raises the modularity of its parent's imports nor is imported by two of its siblings. Consider folding it into "${CARD}".\n`,
    );
  });

  it("spares a sub-slice two siblings share, modular or not", () => {
    const { status, stderr } = run({
      ...BITS,
      [`${CARD}/face/ui/lens.ts`]:
        "import { bit } from '../../bits/index.ts';\nexport const lens = bit;",
    });
    assert.deepEqual({ status, stderr }, { status: 0, stderr: "" });
  });

  it("spares a consumer taking only the sub-slice that imports every sibling", () => {
    // `face` imports `back`, so whoever takes `face` needs the whole card.
    const { status, stderr } = run({
      ...CARDS,
      [`${CARD}/face/ui/lens.ts`]:
        "import { back } from '../../back/index.ts';\nexport const lens = back;",
    });
    assert.deepEqual({ status, stderr }, { status: 0, stderr: "" });
  });

  it("flags a segment or a module beside a sub-slice", () => {
    const { status, stderr } = run({
      ...CARDS,
      [`${CARD}/ui/rim.ts`]: "export const rim = 1;",
      [`${CARD}/lib.ts`]: "export const lib = 1;",
    });
    assert.equal(status, 1);
    assert.ok(
      stderr.startsWith(
        `${CARD}: "lib.ts", "ui" beside its sub-slices; a unit holding a sub-slice holds only sub-slices and barrels, so move the rest into a sub-slice named for its noun\n`,
      ),
      stderr,
    );
  });

  it("flags sibling sub-slices importing one another in a cycle", () => {
    const { status, stderr } = run({
      ...CARDS,
      [`${CARD}/back/ui/edge.ts`]:
        "import { lens } from '../../face/ui/lens.ts';\nexport const edge = lens;",
      [`${CARD}/face/ui/face.ts`]:
        "import { back } from '../../back/index.ts';\nexport { lens as face } from './lens.ts';\nexport const f = back;",
    });
    assert.equal(status, 1);
    assert.ok(
      stderr.startsWith(
        `${CARD}: its sub-slices "back", "face" import one another in a cycle; siblings import in one direction only, so move what they share into a sub-slice of its own or merge them\n`,
      ),
      stderr,
    );
  });
});
