import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { boardTitle } from "#src/review-board/shared/review-data/index.ts";
import { collect } from "./collect.ts";
import { renderPage } from "./page.ts";
import { scss } from "./scss.ts";

const MB = 1024 * 1024;
const MAX_PAGE_BYTES = 8 * MB;
const entry = join(
  dirname(fileURLToPath(import.meta.url)),
  "..",
  "app",
  "entrypoint",
  "index.ts",
);

/** The browser bundle and its stylesheet; a `node:` import reaching the page fails here. */
async function bundle(): Promise<{ js: string; css: string }> {
  const result = await build({
    entryPoints: [entry],
    bundle: true,
    write: false,
    outdir: "out",
    format: "iife",
    platform: "browser",
    target: "es2022",
    minify: true,
    legalComments: "none",
    plugins: [scss],
  });
  let js = "";
  let css = "";
  for (const file of result.outputFiles) {
    if (file.path.endsWith(".js")) js = file.text;
    else if (file.path.endsWith(".css")) css = file.text;
  }
  if (js === "") throw new Error("esbuild produced no script");
  return { js, css };
}

const repoRoot = execFileSync("git", ["rev-parse", "--show-toplevel"], {
  encoding: "utf8",
}).trim();
const outDir = resolve(
  process.argv[2] ?? join(repoRoot, "tmp", "review-board"),
);

const [data, assets] = [collect({ cwd: process.cwd() }), await bundle()];
const page = renderPage({
  title: boardTitle(data.branch, data.pr),
  data,
  ...assets,
});

mkdirSync(outDir, { recursive: true });
const indexPath = join(outDir, "index.html");
const localPath = join(outDir, "local.html");
writeFileSync(indexPath, page.fragment);
writeFileSync(localPath, page.document);

const bytes = Buffer.byteLength(page.fragment);
const size = `${(bytes / MB).toFixed(2)} MB`;
console.log(`${indexPath}\n${localPath}\npage size: ${size}`);
if (bytes > MAX_PAGE_BYTES) {
  console.error(
    `the page is ${size}, over the ${MAX_PAGE_BYTES / MB} MB budget`,
  );
  process.exitCode = 1;
}
