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
});

// `revisions[0]` is the base (`commit` = base sha); the rest are the commits in
// range that touched the file, oldest first. `blob` and `size` are null where
// the file does not exist at that commit.
const revisionSchema = z.object({
  commit: z.string(),
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

export const reviewDataSchema = z.object({
  repo: z.nullable(z.string()),
  branch: z.string(),
  head: z.string(),
  base: z.object({ ref: z.string(), sha: z.string() }),
  collectedAt: z.string(),
  commits: z.array(commitSchema),
  files: z.array(fileSchema),
  blobs: z.record(z.string(), z.string()),
});

export type ReviewData = z.infer<typeof reviewDataSchema>;
export type ReviewFile = ReviewData["files"][number];
export type ReviewCommit = ReviewData["commits"][number];
export type FileStatus = (typeof FILE_STATUSES)[number];

export function parseReviewData(json: unknown): ReviewData {
  return reviewDataSchema.parse(json);
}
