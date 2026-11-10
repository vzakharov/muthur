import type {
  ReviewBranch,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";

type Revision = ReviewFile["revisions"][number];

/** The board's commit range; null is the base (`from`) or the head (`to`). */
export interface BoardRange {
  from: string | null;
  to: string | null;
}

/** The viewer's own range for one file and when they set it. */
export type RangeOverride = BoardRange & { at: string };

/** The agent's marker that a file's review resumes at `from`. */
export interface Shift {
  from: string;
  at: string;
}

/** Commit SHA → position in the branch; the base sits before every commit. */
export type CommitOrder = ReadonlyMap<string, number>;

export interface EffectiveRange {
  /** Commit SHAs, each one of the file's revisions. */
  from: string;
  to: string;
  fromBlob: string | null;
  toBlob: string | null;
  /** True when the file's own override or a shift, not the board, decided it. */
  fromExplicit: boolean;
  toExplicit: boolean;
  /** Whether what `to` shows is what the viewer marked viewed, base merges since aside. */
  viewed: boolean;
  /** The marked blob token that makes the file read as viewed — `to`'s own, or one base merges carried forward; null when not viewed. */
  viewedMark: string | null;
}

export function commitOrder(data: ReviewBranch): CommitOrder {
  const order = new Map<string, number>([[data.base.sha, -1]]);
  data.commits.forEach((commit, index) => order.set(commit.sha, index));
  return order;
}

export const baseMerges = (data: ReviewBranch): ReadonlySet<string> =>
  new Set(data.commits.filter((c) => c.baseMerge).map((c) => c.sha));

const EMPTY: ReadonlySet<string> = new Set();

/** The latest of `file`'s revisions at or before `commit`, or undefined for a commit outside the branch. */
export function snapToRevision(
  file: ReviewFile,
  order: CommitOrder,
  commit: string,
): Revision | undefined {
  const target = order.get(commit);
  if (target === undefined) return undefined;
  let found: Revision | undefined;
  for (const revision of file.revisions) {
    const position = order.get(revision.commit);
    if (position === undefined)
      throw new Error(`${file.path} has a revision outside the branch`);
    if (position <= target) found = revision;
  }
  return found;
}

const timeOf = (at: string): number => {
  const time = Date.parse(at);
  return Number.isNaN(time) ? 0 : time;
};

/** Whether the override constrains a range; one with both ends null is only a stamp. */
const isLive = (override: RangeOverride | undefined): boolean =>
  override !== undefined && (override.from !== null || override.to !== null);

/**
 * The range a file shows. The board's range, snapped to the file's revisions,
 * is the default. The viewer's override or the agent's shift replaces it for
 * this file, whichever is newer by `at`; a shift sets only `from`, so the
 * file's `to` then follows the board. Unless the override chose `from`, a file
 * the viewer marked viewed at earlier revisions than its `to` shows only what
 * changed since the latest of them. Base merges right after the viewed revision
 * count as viewed too: what they change is the base's, reviewed there, so a
 * file they alone changed stays viewed, and one changed after them shows only
 * what came after.
 */
export function effectiveRange(input: {
  file: ReviewFile;
  order: CommitOrder;
  board: BoardRange;
  override?: RangeOverride | undefined;
  shift?: Shift | undefined;
  viewedBlobs?: ReadonlySet<string> | undefined;
  merges?: ReadonlySet<string> | undefined;
}): EffectiveRange {
  const { file, order, board, override, shift } = input;
  const viewedBlobs = input.viewedBlobs ?? EMPTY;
  const merges = input.merges ?? EMPTY;
  const first = file.revisions[0];
  const last = file.revisions[file.revisions.length - 1];
  if (first === undefined || last === undefined)
    throw new Error(`${file.path} has no revisions`);
  const snap = (commit: string | null | undefined): Revision | undefined =>
    commit === null || commit === undefined
      ? undefined
      : snapToRevision(file, order, commit);

  const shiftRevision = snap(shift?.from);
  const shiftWins =
    shift !== undefined &&
    shiftRevision !== undefined &&
    (!isLive(override) || timeOf(shift.at) > timeOf(override?.at ?? ""));

  const boardFrom = snap(board.from) ?? first;
  const boardTo = snap(board.to) ?? last;
  let from = boardFrom;
  let to = boardTo;
  let fromExplicit = false;
  let toExplicit = false;
  let fromChosen = false;

  if (shiftWins) {
    from = shiftRevision;
    fromExplicit = true;
  } else if (override !== undefined && isLive(override)) {
    const ownFrom = snap(override.from);
    const ownTo = snap(override.to);
    if (ownFrom !== undefined) {
      from = ownFrom;
      fromExplicit = true;
      fromChosen = true;
    }
    if (ownTo !== undefined) {
      to = ownTo;
      toExplicit = true;
    }
  }

  const position = (revision: Revision): number =>
    order.get(revision.commit) ?? -1;
  const seenMark = seenRevision(file, position, merges, to, viewedBlobs);
  const seen = seenMark?.revision;
  const viewed = seen === to;
  if (
    !fromChosen &&
    seen !== undefined &&
    !viewed &&
    position(seen) > position(from)
  ) {
    from = seen;
    fromExplicit = true;
  }
  if (position(from) > position(to)) from = to;

  return {
    from: from.commit,
    to: to.commit,
    fromBlob: from.blob,
    toBlob: to.blob,
    fromExplicit,
    toExplicit,
    viewed,
    viewedMark: viewed ? (seenMark?.mark ?? null) : null,
  };
}

/**
 * The latest revision up to `to` holding a blob the viewer marked viewed,
 * carried past the base merges that follow it, with the marked blob's token;
 * `to` itself when `to` shows a marked blob.
 */
function seenRevision(
  file: ReviewFile,
  position: (revision: Revision) => number,
  merges: ReadonlySet<string>,
  to: Revision,
  viewedBlobs: ReadonlySet<string>,
): { revision: Revision; mark: string } | undefined {
  const toMark = viewedToken(to.blob);
  if (viewedBlobs.has(toMark)) return { revision: to, mark: toMark };
  const { revisions } = file;
  let at = revisions.findLastIndex(
    (revision) =>
      viewedBlobs.has(viewedToken(revision.blob)) &&
      position(revision) < position(to),
  );
  const marked = revisions[at];
  if (marked === undefined) return undefined;
  let revision = marked;
  for (;;) {
    const next = revisions[at + 1];
    if (
      next === undefined ||
      position(next) > position(to) ||
      !merges.has(next.commit)
    )
      break;
    revision = next;
    at++;
  }
  return { revision, mark: viewedToken(marked.blob) };
}

/** The blob a viewed mark holds for a file that is absent at its "to" commit. */
const ABSENT = "-";

export const viewedToken = (toBlob: string | null): string => toBlob ?? ABSENT;
