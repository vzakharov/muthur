/**
 * End-to-end tests for `pnpm check:masd`: each case writes a throwaway tree to
 * the OS temp directory and runs the real script there, which reads everything
 * from its working directory.
 */

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { describe, it } from "node:test";

const SCRIPT = path.resolve(import.meta.dirname, "masd-check.ts");

/** Fixture files, keyed by path relative to the tree's root. */
type Tree = Record<string, string>;

// kernel ← blog ← site, kernel ← game: `blog` has one child, so the graph is
// only clean with a second one — `other`.
const GRAPH = JSON.stringify({
  kernel: [],
  blog: ["kernel"],
  site: ["blog"],
  other: ["blog"],
  game: ["kernel"],
});

const BASE: Tree = {
  "src/masd.json": GRAPH,
  "src/kernel/shared/ui/index.ts": "export const ui = 1;",
  "src/blog/pages/documents/index.ts": "export const documents = 1;",
  "src/site/pages/home/index.ts": "export const home = 1;",
  "src/other/pages/about/index.ts": "export const about = 1;",
  "src/game/pages/play/index.ts": "export const play = 1;",
};

function run(tree: Tree): { status: number; stderr: string } {
  const dir = mkdtempSync(path.join(tmpdir(), "masd-check-"));
  for (const [file, text] of Object.entries({ ...BASE, ...tree })) {
    const full = path.join(dir, file);
    mkdirSync(path.dirname(full), { recursive: true });
    writeFileSync(full, text);
  }
  const { error, status, stderr } = spawnSync(process.execPath, [SCRIPT], {
    cwd: dir,
    encoding: "utf8",
  });
  assert.equal(error, undefined);
  return { status: status ?? -1, stderr };
}

const ENTITY = "src/blog/entities/card/index.ts";
const CARD_IMPORT = "import { card } from '#src/blog/entities/card/index.ts';";
const UNREFERENCED =
  "src/blog/entities/card: This slice has no references. Consider removing it.\n";
const MERGE_INTO_HOME =
  'src/blog/entities/card: This slice has only one reference in slice "pages/home". Consider merging them.\n';

describe("masd-check", () => {
  it("passes a clean tree", () => {
    assert.deepEqual(run({}), { status: 0, stderr: "" });
  });

  it("counts a slice used by two descendants as significant", () => {
    assert.deepEqual(
      run({
        [ENTITY]: "export const card = 1;",
        "src/site/pages/home/ui.ts": CARD_IMPORT,
        "src/blog/pages/documents/ui.ts": CARD_IMPORT,
      }).status,
      0,
    );
  });

  it("flags a slice used from one slice, though that slice is in a descendant", () => {
    const { status, stderr } = run({
      [ENTITY]: "export const card = 1;",
      "src/site/pages/home/ui.ts": CARD_IMPORT,
    });
    assert.equal(status, 1);
    assert.equal(stderr, MERGE_INTO_HOME);
  });

  describe("a slice with one reference, by modularity over its own app", () => {
    const CONSUMER: Tree = {
      "src/site/pages/home/ui.ts":
        "import { a } from '#src/blog/entities/card/index.ts';",
    };
    // Three edges inside the card: the barrel to each file, and `a` to `b`.
    const COHESIVE: Tree = {
      ...CONSUMER,
      [ENTITY]: "export * from './a.ts';\nexport * from './b.ts';",
      "src/blog/entities/card/a.ts":
        "import { b } from './b.ts';\nexport const a = b;",
      "src/blog/entities/card/b.ts": "export const b = 1;",
    };
    // Two edges elsewhere in blog, so the card is not the whole graph.
    const REST_OF_BLOG: Tree = {
      "src/blog/pages/documents/index.ts": "export * from './ui.ts';",
      "src/blog/pages/documents/ui.ts":
        "import { x } from '#src/blog/shared/x/index.ts';",
      "src/blog/shared/x/index.ts": "export const x = 1;",
    };
    const shared = (names: string[]): Tree =>
      Object.fromEntries(
        names.map((name) => [
          `src/blog/shared/${name}/index.ts`,
          `export const ${name} = 1;`,
        ]),
      );

    it("passes a slice holding more of its edges than chance", () => {
      assert.deepEqual(run({ ...COHESIVE, ...REST_OF_BLOG }), {
        status: 0,
        stderr: "",
      });
    });

    it("flags one whose files mostly import outside it", () => {
      assert.equal(
        run({
          ...CONSUMER,
          ...REST_OF_BLOG,
          ...shared(["p", "q", "r", "s", "t"]),
          [ENTITY]: "export * from './a.ts';\nexport * from './b.ts';",
          "src/blog/entities/card/a.ts": [
            "import { p } from '#src/blog/shared/p/index.ts';",
            "import { q } from '#src/blog/shared/q/index.ts';",
            "import { r } from '#src/blog/shared/r/index.ts';",
            "export const a = p + q + r;",
          ].join("\n"),
          "src/blog/entities/card/b.ts": [
            "import { s } from '#src/blog/shared/s/index.ts';",
            "import { t } from '#src/blog/shared/t/index.ts';",
            "export const b = s + t;",
          ].join("\n"),
        }).stderr,
        MERGE_INTO_HOME,
      );
    });

    it("flags a one-file slice, which has no edge inside it", () => {
      assert.equal(
        run({
          ...CONSUMER,
          ...REST_OF_BLOG,
          [ENTITY]:
            "import { x } from '#src/blog/shared/x/index.ts';\nexport const a = x;",
        }).stderr,
        MERGE_INTO_HOME,
      );
    });

    it("counts no descendant edge, however many", () => {
      // The card is the whole of blog, so it holds exactly its share by chance;
      // the site's edges would lower that share if they counted.
      const site = Object.fromEntries(
        ["a", "b", "c", "d"].map((name) => [
          `src/site/pages/home/${name}.ts`,
          "import './ui.ts';\nexport const y = 1;",
        ]),
      );
      assert.equal(run({ ...COHESIVE, ...site }).stderr, MERGE_INTO_HOME);
    });

    it("still flags it with no references", () => {
      assert.equal(
        run({
          ...COHESIVE,
          ...REST_OF_BLOG,
          "src/site/pages/home/ui.ts": "",
        }).stderr,
        UNREFERENCED,
      );
    });
  });

  it("flags a slice nothing uses", () => {
    assert.equal(
      run({ [ENTITY]: "export const card = 1;" }).stderr,
      UNREFERENCED,
    );
  });

  it("spares a slice whose barrel says why it stays", () => {
    assert.equal(
      run({
        [ENTITY]:
          "// masd-disable insignificant -- its page is coming\nexport const card = 1;",
      }).stderr,
      "",
    );
  });

  it("flags a slice whose marker gives no reason", () => {
    assert.equal(
      run({
        [ENTITY]: "// masd-disable insignificant -- \nexport const card = 1;",
      }).stderr,
      UNREFERENCED,
    );
  });

  it("does not count an app script as a reference", () => {
    assert.equal(
      run({
        [ENTITY]: "export const card = 1;",
        "src/blog/scripts/render.ts": CARD_IMPORT,
      }).stderr,
      UNREFERENCED,
    );
  });

  it("does not count a test as a reference", () => {
    assert.equal(
      run({
        [ENTITY]: "export const card = 1;",
        "src/blog/pages/documents/ui.test.ts": CARD_IMPORT,
      }).stderr,
      UNREFERENCED,
    );
  });

  it("does not count a test kit as a reference", () => {
    assert.equal(
      run({
        [ENTITY]: "export const card = 1;",
        "src/blog/pages/documents/ui.test-kit.ts": CARD_IMPORT,
      }).stderr,
      UNREFERENCED,
    );
  });

  it("flags a slice only one shared layer uses, and spares one the app layer uses", () => {
    assert.equal(
      run({
        [ENTITY]: "export const card = 1;",
        "src/blog/shared/x/index.ts":
          "export * from '../../entities/card/index.ts';",
      }).stderr,
      'src/blog/entities/card: This slice has only one reference on layer "shared". Consider moving this code to "shared".\n',
    );
    assert.equal(
      run({
        [ENTITY]: "export const card = 1;",
        "src/blog/app/ui/index.ts":
          "export * from '#src/blog/entities/card/index.ts';",
      }).status,
      0,
    );
  });

  it("flags an app with exactly one child", () => {
    const { status, stderr } = run({
      "src/masd.json": JSON.stringify({
        kernel: [],
        solo: ["kernel"],
        leaf: ["solo"],
        game: ["kernel"],
      }),
      "src/solo/pages/home/index.ts": "export const solo = 1;",
      "src/leaf/pages/home/index.ts": "export const leaf = 1;",
    });
    assert.equal(status, 1);
    assert.match(
      stderr,
      /^masd: solo has exactly one child; fold it into its child$/m,
    );
  });

  it("names a directory the graph lacks", () => {
    assert.equal(
      run({ "src/stray/pages/x/index.ts": "export {};" }).stderr,
      "masd: src/stray is not in the graph\n",
    );
  });

  it("reports a graph that does not parse", () => {
    const { status, stderr } = run({
      "src/masd.json": JSON.stringify({ blog: ["kernel"], kernel: [] }),
    });
    assert.equal(status, 1);
    assert.match(stderr, /blog is declared above its parent kernel/);
  });
});

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
