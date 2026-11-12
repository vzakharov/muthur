import * as z from "zod/mini";

// The viewer's board settings, at `data/users/<uid>/<branchKey>`. `from` / `to`
// are commit SHAs; null is the base / the head.
// A doc's `at` is stamped on write, so what the viewer sets is the rest of it.
const boardPrefsSchema = z.object({
  showWhitespace: z.boolean(),
  showViewed: z.boolean(),
  focusOnly: z.boolean(),
  from: z.nullable(z.string()),
  to: z.nullable(z.string()),
});
// A doc saved before a filter existed lacks it, and one saved before the
// filters were named for what they show carries the inverted `whitespace` /
// `hideViewed` instead, both of which `boardPrefsOf` resolves.
export const boardDocSchema = z.extend(
  z.partial(boardPrefsSchema, {
    showWhitespace: true,
    showViewed: true,
    focusOnly: true,
  }),
  {
    whitespace: z.optional(z.boolean()),
    hideViewed: z.optional(z.boolean()),
    at: z.string(),
  },
);

/** Every filter starts off, on a fresh board and in a doc that never set it. */
export const FILTERS_OFF = {
  showWhitespace: false,
  showViewed: false,
  focusOnly: false,
} satisfies Partial<BoardPrefs>;

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
export type BoardDoc = z.infer<typeof boardDocSchema>;
export type FilePrefs = z.infer<typeof filePrefsSchema>;
export type ViewedMark = z.infer<typeof viewedMarkSchema>;
export type FileDoc = z.infer<typeof fileDocSchema>;
export type ShiftDoc = z.infer<typeof shiftDocSchema>;

/** The doc's prefs with its stamp, a legacy hide-side flag read inverted where the doc has no show-side one. */
export function boardPrefsOf(doc: BoardDoc): { value: BoardPrefs; at: string } {
  const { at, whitespace, hideViewed, ...prefs } = doc;
  const shown = (
    show: boolean | undefined,
    hide: boolean | undefined,
    off: boolean,
  ): boolean => show ?? (hide === undefined ? off : !hide);
  return {
    value: {
      ...prefs,
      showWhitespace: shown(
        prefs.showWhitespace,
        whitespace,
        FILTERS_OFF.showWhitespace,
      ),
      showViewed: shown(prefs.showViewed, hideViewed, FILTERS_OFF.showViewed),
      focusOnly: prefs.focusOnly ?? FILTERS_OFF.focusOnly,
    },
    at,
  };
}

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
