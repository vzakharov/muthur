import * as z from "zod/mini";

// The viewer's board settings, at `data/users/<uid>/<branchKey>`. `from` / `to`
// are commit SHAs; null is the base / the head. `hideViewed` defaults for docs
// saved before it existed.
export const boardDocSchema = z.object({
  whitespace: z.boolean(),
  hideViewed: z._default(z.boolean(), false),
  from: z.nullable(z.string()),
  to: z.nullable(z.string()),
  at: z.string(),
});

// The viewer's state for one file, at `.../<branchKey>/files/<fileKey>`.
// `viewedBlob` is the "to" blob the viewer marked viewed; `at` stamps the last
// range change, which is what a shift is weighed against.
export const fileDocSchema = z.object({
  viewedBlob: z.nullable(z.string()),
  from: z.nullable(z.string()),
  to: z.nullable(z.string()),
  at: z.string(),
});

// Shared, written by the agent at `shifts/<fileKey>`.
export const shiftDocSchema = z.object({
  path: z.string(),
  from: z.string(),
  at: z.string(),
});

export type BoardDoc = z.infer<typeof boardDocSchema>;
export type FileDoc = z.infer<typeof fileDocSchema>;
export type ShiftDoc = z.infer<typeof shiftDocSchema>;

/** The doc's data, or null with a warning naming `path` when it does not fit the schema. */
export function parseDoc<T>(
  schema: z.ZodMiniType<T>,
  data: unknown,
  path: string,
): T | null {
  const result = schema.safeParse(data);
  if (result.success) return result.data;
  console.warn(
    `ignoring malformed doc ${path}: ${z.prettifyError(result.error)}`,
  );
  return null;
}
