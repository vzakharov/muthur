import assert from "node:assert/strict";
import { test } from "node:test";
import { escapeJson, escapeScript, renderPage } from "./page.ts";

const hostile = {
  text: "</script><script>alert(1)</script><!-- x -->",
  other: "a < b",
};

test("escaped JSON has no angle bracket and round-trips", () => {
  const json = escapeJson(hostile);
  assert.ok(!json.includes("<"));
  assert.ok(json.includes("\\u003c/script"));
  assert.deepEqual(JSON.parse(json), hostile);
});

test("a bundle cannot close its own script element", () => {
  const js = escapeScript('const s = "</script>"; // </SCRIPT is not matched');
  assert.ok(!js.includes("</script"));
});

test("the payload survives the page and is the only data script", () => {
  const page = renderPage({
    title: "Review board",
    data: hostile,
    js: "console.log(1)",
    css: "body{}",
  });
  for (const html of [page.fragment, page.document]) {
    const match =
      /<script type="application\/json" id="review-data">(.*?)<\/script>/s.exec(
        html,
      );
    assert.ok(match?.[1] !== undefined);
    assert.deepEqual(JSON.parse(match[1]), hostile);
    assert.equal(html.match(/<\/script>/g)?.length, 2);
    assert.ok(html.includes("<title>Review board</title>"));
    assert.ok(html.includes('<div id="root"></div>'));
  }
});

test("the title is escaped as text", () => {
  const page = renderPage({
    title: "Review #3 · a&b<c>",
    data: {},
    js: "",
    css: "",
  });
  for (const html of [page.fragment, page.document]) {
    assert.ok(html.includes("<title>Review #3 · a&amp;b&lt;c&gt;</title>"));
  }
});

test("only the document carries a skeleton", () => {
  const page = renderPage({ title: "t", data: {}, js: "", css: "" });
  assert.ok(!page.fragment.includes("<!doctype"));
  assert.ok(page.document.startsWith("<!doctype html>"));
  assert.ok(page.document.includes('name="viewport"'));
});
