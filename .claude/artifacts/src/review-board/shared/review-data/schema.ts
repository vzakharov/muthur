import * as z from "zod/mini";

export const FILE_STATUSES = [
  "added",
  "modified",
  "renamed",
  "deleted",
] as const;

const commitSchema = z.object({
  sha: z.string(),
  subject: z.string(),
  author: z.string(),
  date: z.string(),
  // A merge bringing the base branch in: what it changes is the base's work.
  baseMerge: z.boolean(),
});

// `revisions[0]` is the base (`commit` = base sha); the rest are the commits in
// range that touched the file, oldest first. `path` is where the file lives at
// that commit — a rename's old path before it. `blob` and `size` are null where
// the file does not exist at that commit.
const revisionSchema = z.object({
  commit: z.string(),
  path: z.string(),
  blob: z.nullable(z.string()),
  size: z.nullable(z.number()),
});

const fileSchema = z.object({
  path: z.string(),
  oldPath: z.nullable(z.string()),
  status: z.enum(FILE_STATUSES),
  binary: z.boolean(),
  revisions: z.array(revisionSchema),
});

const lineSpanSchema = z.tuple([z.number(), z.number()]);

// A file the branch's author marked as where review matters most, with why;
// `lines` are spans of the file at HEAD, first and last line inclusive.
export const focusSchema = z.object({
  path: z.string(),
  why: z.string(),
  lines: z.optional(z.array(lineSpanSchema)),
});

// What the commit order is read from: the base and the commits since it.
const branchSchema = z.object({
  base: z.object({ ref: z.string(), sha: z.string() }),
  commits: z.array(commitSchema),
});

export const reviewDataSchema = z.extend(branchSchema, {
  repo: z.nullable(z.string()),
  branch: z.string(),
  // The number of the branch's PR; null when there is none or `gh` cannot say.
  pr: z.nullable(z.number()),
  head: z.string(),
  collectedAt: z.string(),
  files: z.array(fileSchema),
  focus: z.array(focusSchema),
  blobs: z.record(z.string(), z.string()),
});

export type ReviewBranch = z.infer<typeof branchSchema>;
export type ReviewData = z.infer<typeof reviewDataSchema>;
export type Focus = z.infer<typeof focusSchema>;
export type LineSpan = z.infer<typeof lineSpanSchema>;
export type ReviewFile = ReviewData["files"][number];
export type ReviewCommit = ReviewData["commits"][number];
export type FileStatus = (typeof FILE_STATUSES)[number];

export function parseReviewData(json: unknown): ReviewData {
  return reviewDataSchema.parse(json);
}
