import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { collect } from "./collect.ts";
import { FOCUS_PATH } from "./focus.ts";

const IDENTITY = {
  GIT_AUTHOR_NAME: "Ada Reviewer",
  GIT_AUTHOR_EMAIL: "ada@example.com",
  GIT_COMMITTER_NAME: "Ada Reviewer",
  GIT_COMMITTER_EMAIL: "ada@example.com",
};

const gitIn =
  (dir: string) =>
  (...args: string[]): string =>
    execFileSync("git", args, {
      cwd: dir,
      env: { ...process.env, ...IDENTITY },
      encoding: "utf8",
    }).trim();

function makeRepo(): { dir: string; commits: string[] } {
  const dir = mkdtempSync(join(tmpdir(), "collect-test-"));
  const git = gitIn(dir);
  const write = (path: string, content: string | Buffer) => {
    mkdirSync(dirname(join(dir, path)), { recursive: true });
    writeFileSync(join(dir, path), content);
  };
  const commit = (message: string) => {
    git("add", "-A");
    git("commit", "-q", "-m", message);
    return git("rev-parse", "HEAD");
  };

  const story =
    Array.from({ length: 12 }, (_, i) => `story line ${i}`).join("\n") + "\n";
  git("init", "-q", "-b", "main");
  write("keep.txt", "unchanged\n");
  write("mod.txt", "one\ntwo\n");
  write("src/ren.txt", story);
  write("gone.txt", "bye\n");
  const base = commit("base");

  git("checkout", "-q", "-b", "feature");
  write("added.txt", "fresh\n");
  write("copy.txt", "fresh\n");
  write("mod.txt", "one\ntwo\nthree\n");
  write("src/ren.txt", story.replace("story line 1", "story line one"));
  const first = commit("add and modify");

  write("mod.txt", "one\nTWO\nthree\n");
  git("mv", "src/ren.txt", "src/renamed.txt");
  write(
    "src/renamed.txt",
    story
      .replace("story line 1", "story line one")
      .replace("story line 3", "story line three"),
  );
  git("rm", "-q", "gone.txt");
  write("pic.bin", Buffer.from([0, 1, 2, 3, 255, 0]));
  const second = commit("modify again, rename, delete, binary");

  return { dir, commits: [base, first, second] };
}

function commitFocus(dir: string, entries: unknown): string {
  const file = join(dir, FOCUS_PATH);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, JSON.stringify(entries));
  const git = gitIn(dir);
  git("add", "-A");
  git("commit", "-q", "-m", "focus");
  return file;
}

test("collects commits, files, revisions and deduplicated blobs", () => {
  const { dir, commits } = makeRepo();
  try {
    const [base, first, second] = commits;
    const data = collect({ cwd: dir, base: "main" });

    assert.equal(data.repo, null);
    assert.equal(data.branch, "feature");
    assert.equal(data.head, second);
    assert.deepEqual(data.base, { ref: "main", sha: base });
    assert.deepEqual(
      data.commits.map((c) => [c.sha, c.subject, c.author]),
      [
        [first, "add and modify", "Ada Reviewer"],
        [second, "modify again, rename, delete, binary", "Ada Reviewer"],
      ],
    );

    const byPath = new Map(data.files.map((file) => [file.path, file]));
    assert.deepEqual(
      [...byPath.keys()].sort(),
      [
        "added.txt",
        "copy.txt",
        "mod.txt",
        "pic.bin",
        "gone.txt",
        "src/renamed.txt",
      ].sort(),
    );

    const added = byPath.get("added.txt");
    assert.ok(added);
    assert.equal(added.status, "added");
    assert.deepEqual(
      added.revisions.map((r) => [r.commit, r.blob === null]),
      [
        [base, true],
        [first, false],
      ],
    );

    const mod = byPath.get("mod.txt");
    assert.ok(mod);
    assert.equal(mod.status, "modified");
    assert.deepEqual(
      mod.revisions.map((r) => r.commit),
      [base, first, second],
    );
    assert.equal(new Set(mod.revisions.map((r) => r.blob)).size, 3);
    assert.equal(mod.revisions[0]?.size, "one\ntwo\n".length);

    const renamed = byPath.get("src/renamed.txt");
    assert.ok(renamed);
    assert.equal(renamed.status, "renamed");
    assert.equal(renamed.oldPath, "src/ren.txt");
    assert.deepEqual(
      renamed.revisions.map((r) => r.commit),
      [base, first, second],
    );
    assert.deepEqual(
      renamed.revisions.map((r) => r.path),
      ["src/ren.txt", "src/ren.txt", "src/renamed.txt"],
    );
    assert.ok(renamed.revisions.every((r) => r.blob !== null));
    assert.notEqual(renamed.revisions[0]?.blob, renamed.revisions[1]?.blob);

    const gone = byPath.get("gone.txt");
    assert.ok(gone);
    assert.equal(gone.status, "deleted");
    assert.deepEqual(
      gone.revisions.map((r) => r.blob === null),
      [false, true],
    );
    assert.equal(gone.revisions[1]?.size, null);

    const pic = byPath.get("pic.bin");
    assert.ok(pic);
    assert.equal(pic.binary, true);
    assert.equal(pic.status, "added");
    assert.equal(pic.revisions[1]?.size, 6);
    assert.equal(mod.binary, false);

    // added.txt and copy.txt share one blob, stored once; binary content is not stored.
    assert.equal(
      added.revisions[1]?.blob,
      byPath.get("copy.txt")?.revisions[1]?.blob,
    );
    const textBlobIds = new Set(
      data.files
        .filter((file) => !file.binary)
        .flatMap((file) =>
          file.revisions.flatMap((r) => (r.blob === null ? [] : [r.blob])),
        ),
    );
    assert.deepEqual(new Set(Object.keys(data.blobs)), textBlobIds);
    assert.equal(data.blobs[added.revisions[1]?.blob ?? ""], "fresh\n");
    assert.equal(data.blobs[pic.revisions[1].blob ?? ""], undefined);
    assert.deepEqual(data.focus, []);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("reads the focus file from HEAD and leaves it off the board", () => {
  const { dir } = makeRepo();
  try {
    const focus = [
      { path: "src/renamed.txt", why: "the story's turn", lines: [[3, 5]] },
      { path: "pic.bin", why: "the new picture" },
    ];
    const file = commitFocus(dir, focus);
    // An uncommitted edit is not what the board shows.
    writeFileSync(file, "[]");

    const data = collect({ cwd: dir, base: "main" });
    assert.deepEqual(data.focus, focus);
    assert.ok(data.files.every((entry) => entry.path !== FOCUS_PATH));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a focus line past the file's end fails the collection", () => {
  const { dir } = makeRepo();
  try {
    commitFocus(dir, [{ path: "mod.txt", why: "x", lines: [[2, 4]] }]);
    assert.throws(
      () => collect({ cwd: dir, base: "main" }),
      /not within its 3 lines/,
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("marks the merges that bring the base in, and only those", () => {
  const { dir } = makeRepo();
  try {
    const git = gitIn(dir);
    git("checkout", "-q", "-b", "side");
    writeFileSync(join(dir, "side.txt"), "side\n");
    git("add", "-A");
    git("commit", "-q", "-m", "side work");
    git("checkout", "-q", "main");
    writeFileSync(join(dir, "keep.txt"), "changed on main\n");
    git("commit", "-q", "-am", "main moves");
    git("checkout", "-q", "feature");
    git("merge", "-q", "--no-edit", "side");
    const sideMerge = git("rev-parse", "HEAD");
    git("merge", "-q", "--no-edit", "main");
    const baseMerge = git("rev-parse", "HEAD");

    const data = collect({ cwd: dir, base: "main" });
    const flags = new Map(data.commits.map((c) => [c.sha, c.baseMerge]));
    assert.equal(flags.get(sideMerge), false);
    assert.equal(flags.get(baseMerge), true);
    assert.equal([...flags.values()].filter(Boolean).length, 1);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("the base falls back through origin/HEAD to main when no PR is found", () => {
  const { dir, commits } = makeRepo();
  try {
    const data = collect({ cwd: dir });
    assert.equal(data.base.ref, "main");
    assert.equal(data.base.sha, commits[0]);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
