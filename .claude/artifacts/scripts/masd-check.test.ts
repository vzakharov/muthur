// End-to-end tests for `pnpm check:masd` on slices and the app graph; the
// harness is masd-check.test-kit.ts.

import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { run, type Tree } from "./masd-check.test-kit.ts";

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
