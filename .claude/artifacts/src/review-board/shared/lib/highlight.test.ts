import assert from "node:assert/strict";
import { test } from "node:test";
import { splitLines } from "./diff.ts";
import { highlightLines, languageOf, parseHighlighted } from "./highlight.ts";

test("language comes from the extension, case-insensitively", () => {
  assert.equal(languageOf("src/a/b.ts"), "typescript");
  assert.equal(languageOf("README.MD"), "markdown");
  assert.equal(languageOf("scripts/vet.sh"), "bash");
  assert.equal(languageOf("pnpm-lock.yaml"), "yaml");
});

test("well-known names win, and an unknown or bare name is plain", () => {
  assert.equal(languageOf("docker/Dockerfile"), "dockerfile");
  assert.equal(languageOf("Makefile"), "makefile");
  assert.equal(languageOf("LICENSE"), null);
  assert.equal(languageOf(".gitignore"), null);
  assert.equal(languageOf("notes.txt"), null);
});

test("scopes open across a newline carry onto the next line", () => {
  assert.deepEqual(
    parseHighlighted('a<span class="hljs-comment">/* x\ny */</span>b'),
    [
      [
        { text: "a", scope: null },
        { text: "/* x", scope: "hljs-comment" },
      ],
      [
        { text: "y */", scope: "hljs-comment" },
        { text: "b", scope: null },
      ],
    ],
  );
});

test("the innermost scope names a nested run", () => {
  assert.deepEqual(
    parseHighlighted(
      '<span class="hljs-string">`a<span class="hljs-subst">${b}</span>`</span>',
    ),
    [
      [
        { text: "`a", scope: "hljs-string" },
        { text: "${b}", scope: "hljs-subst" },
        { text: "`", scope: "hljs-string" },
      ],
    ],
  );
});

test("escaped characters come back as text, merged with their neighbours", () => {
  assert.deepEqual(
    parseHighlighted(
      'a &lt;&amp;&gt; &quot;&#x27;<span class="s">&quot;</span><span class="s">x</span>',
    ),
    [
      [
        { text: "a <&> \"'", scope: null },
        { text: '"x', scope: "s" },
      ],
    ],
  );
});

test("malformed markup fails loudly", () => {
  assert.throws(() => parseHighlighted("a</span>"), /unbalanced/);
  assert.throws(() => parseHighlighted('<span class="x">a'), /open/);
  assert.throws(() => parseHighlighted("&nbsp;"), /unknown entity/);
  assert.throws(() => parseHighlighted("<b>a</b>"), /unexpected/);
});

test("highlighted lines line up with the diff's lines and keep their text", () => {
  const text = [
    "/**",
    " * a <doc> & 'quote'",
    " */",
    "const s = `x ${y}",
    "z`;",
    "",
    '\tif (a < b) return "c";\r',
  ].join("\n");
  for (const source of [text, `${text}\n`]) {
    const lines = highlightLines(source, "typescript");
    const plain = splitLines(source);
    assert.ok(lines.length >= plain.length);
    plain.forEach((line, index) => {
      const tokens = lines[index] ?? [];
      assert.equal(tokens.map((token) => token.text).join(""), line);
    });
  }
});

test("a block comment's every line carries the comment scope", () => {
  const lines = highlightLines("/* a\nb\nc */\nx;", "typescript");
  for (const line of lines.slice(0, 3))
    assert.ok(line.every((token) => token.scope === "hljs-comment"));
});
