import { claudeRuntime } from "#src/review-board/shared/lib/runtime.ts";
import type { ReviewData } from "#src/review-board/shared/review-data/index.ts";
import { fileKey } from "./keys.ts";

/** What the page reaches the artifact's store through, for one branch. */
export interface Connection {
  db: DB;
  /** The viewer's id; null leaves them no private subtree. */
  uid: string | null;
  boardPath: string;
  filesPath: string;
  shiftsPath: string;
  /** File path → its key, and back. */
  keyOf: ReadonlyMap<string, string>;
  pathOf: ReadonlyMap<string, string>;
}

export const SHIFTS = "shifts";

/**
 * The `db` and `user` capabilities, or null when this view has no `db` (no
 * runtime, signed out, outside the organization). Signed in without an id, the
 * connection reads shifts and keeps the viewer's own state for the visit.
 */
export async function connect(data: ReviewData): Promise<Connection | null> {
  const runtime = claudeRuntime();
  if (runtime === null) return null;
  const db = await runtime.use("db");
  if (db === null) return null;
  const user = await runtime.use("user");
  const uid = user === null ? null : await user.id();

  const branchKey = await fileKey(data.branch);
  const keyOf = new Map<string, string>();
  const pathOf = new Map<string, string>();
  await Promise.all(
    data.files.map(async (file) => {
      const key = await fileKey(file.path);
      keyOf.set(file.path, key);
      pathOf.set(key, file.path);
    }),
  );
  const boardPath = `data/users/${uid ?? "-"}/${branchKey}`;
  return {
    db,
    uid,
    boardPath,
    filesPath: `${boardPath}/files`,
    shiftsPath: SHIFTS,
    keyOf,
    pathOf,
  };
}
