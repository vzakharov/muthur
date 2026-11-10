import type {
  ReviewBranch,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { commitOrder } from "./range.ts";

/** Branch commits closer together than this belong to one working session and share a shade. */
const SESSION_GAP_MS = 15 * 60_000;
/** Shades from the newest session (0) to the oldest (`SHADE_LEVELS`). */
export const SHADE_LEVELS = 5;

export interface AgeShade {
  /** 0 for the newest session of changes, `SHADE_LEVELS` for the oldest. */
  level: number;
  /** The commit that last changed the file at or before the board's `to`. */
  commit: string;
  date: string;
}

const timeOf = (date: string): number => {
  const time = Date.parse(date);
  return Number.isNaN(time) ? 0 : time;
};

/**
 * Each file's shade by how long before the board's `to` the file last changed.
 * Base merges are skipped, since they bring in someone else's work. Commits
 * form sessions, a gap over `SESSION_GAP_MS` starting a new one, and a session
 * is aged by its newest commit; the age is log-scaled across the sessions, so
 * "an hour ago" and "three days ago" stay apart while a run of follow-ups
 * minutes apart shares one shade. A file with no change of its own up to `to`
 * has no entry.
 */
export function ageShades(
  data: ReviewBranch,
  files: readonly ReviewFile[],
  to: string | null,
): ReadonlyMap<string, AgeShade> {
  const order = commitOrder(data);
  const end = to === null ? data.commits.length - 1 : (order.get(to) ?? -1);
  const own = data.commits.filter(
    (commit, index) => index <= end && !commit.baseMerge,
  );
  const dates = new Map(own.map((commit) => [commit.sha, commit.date]));
  const times = new Map(own.map((commit) => [commit.sha, timeOf(commit.date)]));

  // A session's anchor is its newest commit's time.
  const anchors: number[] = [];
  const sessionOf = new Map<string, number>();
  let previous: number | null = null;
  for (const commit of own) {
    const time = times.get(commit.sha) ?? 0;
    if (previous === null || time - previous > SESSION_GAP_MS)
      anchors.push(time);
    else anchors[anchors.length - 1] = Math.max(time, anchors.at(-1) ?? 0);
    sessionOf.set(commit.sha, anchors.length - 1);
    previous = time;
  }

  const now = Math.max(0, ...times.values());
  const ageOf = (anchor: number): number =>
    Math.log1p(Math.max(0, now - anchor) / SESSION_GAP_MS);
  const oldest = Math.max(0, ...anchors.map(ageOf));

  const shades = new Map<string, AgeShade>();
  for (const file of files) {
    const last = file.revisions.findLast((revision) =>
      times.has(revision.commit),
    );
    if (last === undefined) continue;
    const session = sessionOf.get(last.commit);
    const anchor = session === undefined ? undefined : anchors[session];
    if (anchor === undefined) continue;
    const level =
      oldest === 0 ? 0 : Math.round((ageOf(anchor) / oldest) * SHADE_LEVELS);
    shades.set(file.path, {
      level,
      commit: last.commit,
      date: dates.get(last.commit) ?? "",
    });
  }
  return shades;
}
