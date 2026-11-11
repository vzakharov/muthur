import * as z from "zod/mini";

// The viewer's board settings, at `data/users/<uid>/<branchKey>`. `from` / `to`
// are commit SHAs; null is the base / the head. The filters default for docs
// saved before they existed.
// A doc's `at` is stamped on write, so what the viewer sets is the rest of it.
const boardPrefsSchema = z.object({
  whitespace: z.boolean(),
  hideViewed: z._default(z.boolean(), true),
  focusOnly: z._default(z.boolean(), false),
  from: z.nullable(z.string()),
  to: z.nullable(z.string()),
});
export const boardDocSchema = z.extend(boardPrefsSchema, { at: z.string() });

// The viewer's state for one file, at `.../<branchKey>/files/<fileKey>`.
// `viewed` lists the blobs the viewer marked viewed, each when; `at` stamps the
// last range change, which is what a shift is weighed against. A doc saved
// before the list existed carries the one `viewedBlob` instead, which
// `filePrefsOf` reads as a one-entry list.
const viewedMarkSchema = z.object({ blob: z.string(), at: z.string() });
const filePrefsSchema = z.object({
  viewed: z._default(z.array(viewedMarkSchema), []),
  from: z.nullable(z.string()),
  to: z.nullable(z.string()),
});
export const fileDocSchema = z.extend(filePrefsSchema, {
  viewedBlob: z.optional(z.nullable(z.string())),
  at: z.string(),
});

// Shared, written by the agent at `shifts/<fileKey>`.
export const shiftDocSchema = z.object({
  path: z.string(),
  from: z.string(),
  at: z.string(),
});

export type BoardPrefs = z.infer<typeof boardPrefsSchema>;
export type FilePrefs = z.infer<typeof filePrefsSchema>;
export type ViewedMark = z.infer<typeof viewedMarkSchema>;
export type FileDoc = z.infer<typeof fileDocSchema>;
export type ShiftDoc = z.infer<typeof shiftDocSchema>;

/** The doc's prefs with its stamp, a legacy `viewedBlob` carried over as the first mark when the doc has no list. */
export function filePrefsOf(doc: FileDoc): { value: FilePrefs; at: string } {
  const { at, viewedBlob, ...prefs } = doc;
  const legacy =
    prefs.viewed.length === 0 && viewedBlob !== undefined && viewedBlob !== null
      ? [{ blob: viewedBlob, at }]
      : prefs.viewed;
  return { value: { ...prefs, viewed: legacy }, at };
}

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
