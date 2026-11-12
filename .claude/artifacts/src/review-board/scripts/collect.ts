import { spawnSync } from "node:child_process";
import * as z from "zod/mini";
import type {
  FileStatus,
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { FOCUS_PATH, lineCount, parseFocus } from "./focus.ts";

interface CollectOptions {
  cwd: string;
  /** The branch the review is against; resolved from the PR, then the repo default, when omitted. */
  base?: string;
}

const MAX_BUFFER = 1 << 30;
const FIELD = "\x1f";
const RECORD = "\x1e";

type Outcome =
  | { ok: true; stdout: Buffer }
  | { ok: false; status: number | null; reason: string };

function run(
  cwd: string,
  command: string,
  args: string[],
  input?: string,
): Outcome {
  const result = spawnSync(command, args, {
    cwd,
    maxBuffer: MAX_BUFFER,
    ...(input === undefined ? {} : { input }),
  });
  if (result.error)
    return { ok: false, status: null, reason: result.error.message };
  if (result.status !== 0)
    return {
      ok: false,
      status: result.status,
      reason: result.stderr.toString("utf8").trim(),
    };
  return { ok: true, stdout: result.stdout };
}

function git(cwd: string, args: string[], input?: string): Buffer {
  const outcome = run(cwd, "git", args, input);
  if (!outcome.ok)
    throw new Error(`git ${args.join(" ")} failed: ${outcome.reason}`);
  return outcome.stdout;
}

function gitText(cwd: string, args: string[], input?: string): string {
  return git(cwd, args, input).toString("utf8");
}

/** The command's trimmed stdout, or null when it is unavailable or exits non-zero. */
function tryText(cwd: string, command: string, args: string[]): string | null {
  const outcome = run(cwd, command, args);
  if (!outcome.ok) return null;
  return outcome.stdout.toString("utf8").trim() || null;
}

const prSchema = z.object({ number: z.number(), baseRefName: z.string() });
type Pr = z.infer<typeof prSchema>;

function readPr(cwd: string): Pr | null {
  const json = tryText(cwd, "gh", [
    "pr",
    "view",
    "--json",
    "number,baseRefName",
  ]);
  return json === null ? null : prSchema.parse(JSON.parse(json));
}

function resolveBaseRef(
  cwd: string,
  base: string | undefined,
  pr: Pr | null,
): string {
  if (base !== undefined) return base;
  if (pr !== null) return pr.baseRefName;
  const head = tryText(cwd, "git", [
    "symbolic-ref",
    "refs/remotes/origin/HEAD",
  ]);
  return head?.replace(/^refs\/remotes\/origin\//, "") ?? "main";
}

function resolveBaseSha(cwd: string, baseRef: string): string {
  const remoteRef = `origin/${baseRef}`;
  const hasRemote = run(cwd, "git", [
    "rev-parse",
    "--verify",
    "--quiet",
    remoteRef,
  ]).ok;
  const target = hasRemote ? remoteRef : baseRef;
  return gitText(cwd, ["merge-base", target, "HEAD"]).trim();
}

function parseRepo(url: string | null): string | null {
  const match = url?.match(/[:/]([^/:]+)\/([^/]+?)(?:\.git)?\/?$/);
  return match ? `${match[1]}/${match[2]}` : null;
}

function readCommits(cwd: string, baseSha: string): ReviewData["commits"] {
  const format = ["%H", "%P", "%s", "%an", "%aI"].join(FIELD) + RECORD;
  const out = gitText(cwd, [
    "log",
    "--first-parent",
    "--reverse",
    `--format=${format}`,
    `${baseSha}..HEAD`,
  ]);
  return out
    .split(RECORD)
    .map((record) => record.replace(/^\n/, ""))
    .filter((record) => record !== "")
    .map((record) => {
      const [sha, parents, subject, author, date] = record.split(FIELD);
      if (
        sha === undefined ||
        parents === undefined ||
        subject === undefined ||
        author === undefined ||
        date === undefined
      ) {
        throw new Error(
          `unparseable git log record: ${JSON.stringify(record)}`,
        );
      }
      const merged = parents.split(" ").slice(1);
      const baseMerge =
        merged.length > 0 &&
        merged.every((parent) => isAncestor(cwd, parent, baseSha));
      return { sha, subject, author, date, baseMerge };
    });
}

function isAncestor(cwd: string, commit: string, of: string): boolean {
  const outcome = run(cwd, "git", ["merge-base", "--is-ancestor", commit, of]);
  if (outcome.ok) return true;
  if (outcome.status === 1) return false;
  throw new Error(`git merge-base --is-ancestor failed: ${outcome.reason}`);
}

interface Change {
  path: string;
  oldPath: string | null;
  status: FileStatus;
}

function statusOf(code: string): FileStatus {
  switch (code[0]) {
    case "A":
      return "added";
    case "M":
    case "T":
      return "modified";
    case "D":
      return "deleted";
    case "R":
      return "renamed";
    default:
      throw new Error(`unsupported git status ${JSON.stringify(code)}`);
  }
}

/** The NUL-split base..HEAD diff in `format`; both formats share `-M`, so a rename keys both by its new path. */
function diffTokens(
  cwd: string,
  baseSha: string,
  format: "--name-status" | "--numstat",
): string[] {
  return gitText(cwd, ["diff", format, "-M", "-z", baseSha, "HEAD"]).split(
    "\0",
  );
}

function readChanges(cwd: string, baseSha: string): Change[] {
  const tokens = diffTokens(cwd, baseSha, "--name-status");
  const changes: Change[] = [];
  for (let i = 0; i < tokens.length - 1; ) {
    const code = tokens[i++] ?? "";
    const status = statusOf(code);
    if (status === "renamed") {
      const oldPath = tokens[i++];
      const path = tokens[i++];
      if (oldPath === undefined || path === undefined)
        throw new Error("truncated rename entry");
      changes.push({ path, oldPath, status });
    } else {
      const path = tokens[i++];
      if (path === undefined) throw new Error("truncated name-status entry");
      changes.push({ path, oldPath: null, status });
    }
  }
  return changes;
}

/** Paths git reports as binary (`-\t-` in numstat), keyed by their new path. */
function readBinaryPaths(cwd: string, baseSha: string): Set<string> {
  const tokens = diffTokens(cwd, baseSha, "--numstat");
  const binary = new Set<string>();
  for (let i = 0; i < tokens.length - 1; ) {
    const entry = tokens[i++] ?? "";
    const [added, , inlinePath] = entry.split("\t");
    let path = inlinePath;
    if (path === "") {
      i++; // a rename lists the old path, then the new one, as separate tokens
      path = tokens[i++];
    }
    if (path === undefined) throw new Error("truncated numstat entry");
    if (added === "-") binary.add(path);
  }
  return binary;
}

interface Located {
  blob: string | null;
  size: number | null;
}

/** Resolves `<commit>:<path>` specs to blob ids and sizes in one `cat-file` run. */
function locate(cwd: string, specs: string[]): Located[] {
  if (specs.length === 0) return [];
  for (const spec of specs) {
    if (spec.includes("\n"))
      throw new Error(`path with a newline is unsupported: ${spec}`);
  }
  const lines = gitText(
    cwd,
    ["cat-file", "--batch-check"],
    `${specs.join("\n")}\n`,
  ).split("\n");
  return specs.map((spec, index) => {
    const line = lines[index];
    if (line === undefined)
      throw new Error(`cat-file gave no answer for ${spec}`);
    if (line.endsWith(" missing")) return { blob: null, size: null };
    const [oid, type, size] = line.split(" ");
    if (oid === undefined || type === undefined || size === undefined) {
      throw new Error(`unparseable cat-file line: ${line}`);
    }
    return type === "blob"
      ? { blob: oid, size: Number(size) }
      : { blob: null, size: null };
  });
}

function readRevisions(
  cwd: string,
  baseSha: string,
  changes: Change[],
): ReviewFile["revisions"][] {
  const commitLists = changes.map((change) =>
    gitText(cwd, [
      "log",
      "--first-parent",
      "--reverse",
      "--format=%H",
      `${baseSha}..HEAD`,
      "--",
      ...(change.oldPath === null
        ? [change.path]
        : [change.path, change.oldPath]),
    ])
      .split("\n")
      .filter((sha) => sha !== ""),
  );

  // Each revision asks for the file under its current path and, for a rename,
  // under its old one; the first that exists wins.
  const queries = changes.flatMap((change, index) => {
    const baseCommit = {
      commit: baseSha,
      path: change.oldPath ?? change.path,
      alt: null,
    };
    const rest = (commitLists[index] ?? []).map((commit) => ({
      commit,
      path: change.path,
      alt: change.oldPath,
    }));
    return [baseCommit, ...rest];
  });
  const specs = queries.flatMap((q) =>
    q.alt === null
      ? [`${q.commit}:${q.path}`]
      : [`${q.commit}:${q.path}`, `${q.commit}:${q.alt}`],
  );
  const located = locate(cwd, specs);

  let cursor = 0;
  const resolved = queries.map((q) => {
    const primary = located[cursor++];
    const fallback = q.alt === null ? undefined : located[cursor++];
    if (primary === undefined) throw new Error("revision lookup ran short");
    const [hit, path] =
      primary.blob === null && fallback !== undefined && q.alt !== null
        ? [fallback, q.alt]
        : [primary, q.path];
    return { commit: q.commit, path, ...hit };
  });

  let offset = 0;
  return changes.map((_, index) => {
    const count = 1 + (commitLists[index]?.length ?? 0);
    const revisions = resolved.slice(offset, offset + count);
    offset += count;
    return revisions;
  });
}

/** Blob id → text, one `cat-file --batch` run over the distinct ids. */
function readBlobs(cwd: string, ids: string[]): Record<string, string> {
  if (ids.length === 0) return {};
  const out = git(cwd, ["cat-file", "--batch"], `${ids.join("\n")}\n`);
  const blobs: Record<string, string> = {};
  let pos = 0;
  for (const id of ids) {
    const headerEnd = out.indexOf("\n", pos);
    const [oid, type, size] = out.toString("utf8", pos, headerEnd).split(" ");
    if (oid !== id || type !== "blob" || size === undefined) {
      throw new Error(`unexpected cat-file header for ${id}`);
    }
    const start = headerEnd + 1;
    const end = start + Number(size);
    blobs[id] = out.toString("utf8", start, end);
    pos = end + 1;
  }
  return blobs;
}

/** The focus file as committed at HEAD, checked against the files' text there; empty when there is none. */
function readFocus(
  cwd: string,
  files: ReviewFile[],
  blobs: Record<string, string>,
): ReviewData["focus"] {
  const listed = gitText(cwd, [
    "ls-tree",
    "--name-only",
    "HEAD",
    "--",
    FOCUS_PATH,
  ]);
  if (listed.trim() === "") return [];
  const counts = new Map(
    files.map((file) => {
      const blob = file.binary ? null : (file.revisions.at(-1)?.blob ?? null);
      const text = blob === null ? undefined : blobs[blob];
      return [file.path, text === undefined ? null : lineCount(text)];
    }),
  );
  return parseFocus(gitText(cwd, ["show", `HEAD:${FOCUS_PATH}`]), counts);
}

export function collect({ cwd, base }: CollectOptions): ReviewData {
  const pr = readPr(cwd);
  const baseRef = resolveBaseRef(cwd, base, pr);
  const baseSha = resolveBaseSha(cwd, baseRef);
  // The focus file is about the review, not part of it.
  const changes = readChanges(cwd, baseSha).filter(
    (change) => change.path !== FOCUS_PATH,
  );
  const binary = readBinaryPaths(cwd, baseSha);
  const revisions = readRevisions(cwd, baseSha, changes);

  const files = changes.map((change, index) => ({
    path: change.path,
    oldPath: change.oldPath,
    status: change.status,
    binary: binary.has(change.path),
    revisions: revisions[index] ?? [],
  }));

  const textBlobs = new Set<string>();
  for (const file of files) {
    if (file.binary) continue;
    for (const revision of file.revisions) {
      if (revision.blob !== null) textBlobs.add(revision.blob);
    }
  }

  const blobs = readBlobs(cwd, [...textBlobs]);
  return {
    repo: parseRepo(tryText(cwd, "git", ["remote", "get-url", "origin"])),
    branch: gitText(cwd, ["branch", "--show-current"]).trim(),
    pr: pr?.number ?? null,
    head: gitText(cwd, ["rev-parse", "HEAD"]).trim(),
    base: { ref: baseRef, sha: baseSha },
    collectedAt: new Date().toISOString(),
    commits: readCommits(cwd, baseSha),
    files,
    focus: readFocus(cwd, files, blobs),
    blobs,
  };
}
