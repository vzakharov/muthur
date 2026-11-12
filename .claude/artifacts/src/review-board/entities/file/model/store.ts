import type {
  ReviewData,
  ReviewFile,
} from "#src/review-board/shared/review-data/index.ts";
import { connect, type Connection } from "./connection.ts";
import {
  boardDocSchema,
  boardPrefsOf,
  fileDocSchema,
  FILTERS_OFF,
  filePrefsOf,
  parseDoc,
  shiftDocSchema,
  type BoardPrefs,
  type FilePrefs,
  type ViewedMark,
} from "./docs.ts";
import {
  baseMerges,
  commitOrder,
  effectiveRange,
  viewedToken,
  type BoardRange,
  type EffectiveRange,
  type Shift,
} from "./range.ts";
import { synced, type Synced } from "./synced-value.ts";

/**
 * `connecting` until the capabilities answer; `loading` / `slow` / `ready`
 * while saved state is being read; `visit` when nothing is saved beyond this
 * page load (no `db`, no id, or a write was refused).
 */
export type StoreStatus = "connecting" | "loading" | "slow" | "ready" | "visit";

export interface FileStore {
  status(): StoreStatus;
  board(): BoardPrefs;
  setBoard(patch: Partial<BoardPrefs>): void;
  effective(path: string): EffectiveRange;
  isViewed(path: string): boolean;
  /** Marks or unmarks the blob the file's `to` shows, unmarking a mark base merges carried to it too; other revisions' marks stay. */
  setViewed(path: string, viewed: boolean): void;
  /** When each blob of the file was marked viewed, by blob token. */
  viewedAt(path: string): ReadonlyMap<string, string>;
  /** Sets the file's own `from` / `to`; null clears that end back to the board. */
  setRange(path: string, patch: Partial<BoardRange>): void;
  subscribe(listener: () => void): () => void;
  destroy(): void;
}

const LOAD_TIMEOUT_MS = 10_000;

const sameBoard = (a: BoardPrefs, b: BoardPrefs): boolean =>
  a.showWhitespace === b.showWhitespace &&
  a.showViewed === b.showViewed &&
  a.focusOnly === b.focusOnly &&
  a.from === b.from &&
  a.to === b.to;
const sameMarks = (
  a: readonly ViewedMark[],
  b: readonly ViewedMark[],
): boolean =>
  a.length === b.length &&
  a.every((mark, i) => {
    const other = b[i];
    return other?.blob === mark.blob && other.at === mark.at;
  });
const sameFile = (a: FilePrefs, b: FilePrefs): boolean =>
  sameMarks(a.viewed, b.viewed) && a.from === b.from && a.to === b.to;

/**
 * The page's one access layer to the artifact's `db`: the viewer's board and
 * per-file state (private, written on change) and the agent's shifts
 * (shared, read-only here). It answers synchronously from memory, applies what
 * the store delivers as it arrives, and keeps working in memory alone when
 * there is no `db`.
 */
export function createFileStore(data: ReviewData): FileStore {
  const order = commitOrder(data);
  const merges = baseMerges(data);
  const filesByPath = new Map<string, ReviewFile>(
    data.files.map((file) => [file.path, file]),
  );
  const listeners = new Set<() => void>();
  const unsubscribes: (() => void)[] = [];
  const shifts = new Map<string, Shift>();

  let phase: "pending" | "none" | "on" = "pending";
  let degraded = false;
  let unsettled = 0;
  let timedOut = 0;
  let destroyed = false;

  const notify = (): void => {
    for (const listener of [...listeners]) listener();
  };

  const connection: Promise<Connection | null> = connect(data).catch(
    (error: unknown) => {
      console.error("review board: could not reach the artifact store", error);
      return null;
    },
  );

  const failed = (error: unknown): void => {
    console.error("review board: a write was refused", error);
    degraded = true;
    notify();
  };

  async function writable(): Promise<Connection | null> {
    const conn = await connection;
    return (conn?.uid ?? null) === null || degraded ? null : conn;
  }

  const boardValue = synced<BoardPrefs>({
    initial: { ...FILTERS_OFF, from: null, to: null },
    equals: sameBoard,
    changed: notify,
    failed,
    async write(value, at) {
      const conn = await writable();
      if (conn === null) return;
      await conn.db.doc(conn.boardPath).set({ ...value, at });
    },
  });

  const fileValues = new Map<string, Synced<FilePrefs>>();
  for (const path of filesByPath.keys()) {
    fileValues.set(
      path,
      synced<FilePrefs>({
        initial: { viewed: [], from: null, to: null },
        equals: sameFile,
        changed: notify,
        failed,
        async write(value, at) {
          const conn = await writable();
          const key = conn?.keyOf.get(path);
          if (conn === null || key === undefined) return;
          await conn.db.doc(`${conn.filesPath}/${key}`).set({ ...value, at });
        },
      }),
    );
  }

  function fileValue(path: string): Synced<FilePrefs> {
    const value = fileValues.get(path);
    if (value === undefined) throw new Error(`unknown file ${path}`);
    return value;
  }
  function fileOf(path: string): ReviewFile {
    const file = filesByPath.get(path);
    if (file === undefined) throw new Error(`unknown file ${path}`);
    return file;
  }

  function effective(path: string): EffectiveRange {
    const own = fileValue(path);
    const { from, to, viewed } = own.get();
    return effectiveRange({
      file: fileOf(path),
      order,
      board: boardValue.get(),
      override: { from, to, at: own.at() },
      shift: shifts.get(path),
      viewedBlobs: new Set(viewed.map((mark) => mark.blob)),
      merges,
    });
  }

  /** Subscribes once; the first definitive snapshot (or an error) ends loading, and a silent store is flagged after a timeout. */
  function watch<S extends { metadata: SnapshotMetadata }>(
    label: string,
    subscribe: (
      next: (snap: S) => void,
      error: (e: DbError) => void,
    ) => () => void,
    apply: (snap: S) => void,
  ): void {
    let settled = false;
    let late = false;
    unsettled++;
    const timer = setTimeout(() => {
      if (settled) return;
      late = true;
      timedOut++;
      notify();
    }, LOAD_TIMEOUT_MS);
    const settle = (): void => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      unsettled--;
      if (late) timedOut--;
    };
    unsubscribes.push(
      () => {
        clearTimeout(timer);
      },
      subscribe(
        (snap) => {
          apply(snap);
          if (!snap.metadata.fromCache) settle();
          notify();
        },
        (error) => {
          console.warn(
            `review board: watching ${label} failed (${error.code}): ${error.message}`,
          );
          degraded = true;
          settle();
          notify();
        },
      ),
    );
  }

  function start(conn: Connection): void {
    watch<QuerySnapshot>(
      conn.shiftsPath,
      (next, error) =>
        conn.db.collection(conn.shiftsPath).onSnapshot(next, error),
      (snap) => {
        shifts.clear();
        for (const doc of snap.docs) {
          const path = conn.pathOf.get(doc.id);
          if (path === undefined) continue;
          const parsed = parseDoc(
            shiftDocSchema,
            doc.data(),
            `${conn.shiftsPath}/${doc.id}`,
          );
          if (parsed !== null) shifts.set(path, parsed);
        }
      },
    );
    if (conn.uid === null) return;

    watch<DocumentSnapshot>(
      conn.boardPath,
      (next, error) => conn.db.doc(conn.boardPath).onSnapshot(next, error),
      (snap) => {
        if (!snap.exists) {
          boardValue.receive(null);
          return;
        }
        const doc = parseDoc(boardDocSchema, snap.data(), conn.boardPath);
        if (doc !== null) boardValue.receive(boardPrefsOf(doc));
      },
    );
    watch<QuerySnapshot>(
      conn.filesPath,
      (next, error) =>
        conn.db.collection(conn.filesPath).onSnapshot(next, error),
      (snap) => {
        const docs = new Map(snap.docs.map((doc) => [doc.id, doc]));
        for (const [path, value] of fileValues) {
          const key = conn.keyOf.get(path);
          const doc = key === undefined ? undefined : docs.get(key);
          if (doc === undefined) {
            value.receive(null);
            continue;
          }
          const parsed = parseDoc(
            fileDocSchema,
            doc.data(),
            `${conn.filesPath}/${doc.id}`,
          );
          if (parsed === null) continue;
          const { value: prefs, at } = filePrefsOf(parsed);
          value.receive({ value: prefs, at });
        }
      },
    );
  }

  void connection.then((conn) => {
    if (destroyed) return;
    phase = (conn?.uid ?? null) === null ? "none" : "on";
    if (conn !== null) start(conn);
    notify();
  });

  const now = (): string => new Date().toISOString();

  return {
    status() {
      if (phase === "pending") return "connecting";
      if (phase === "none" || degraded) return "visit";
      if (unsettled === 0) return "ready";
      return timedOut > 0 ? "slow" : "loading";
    },
    board: () => boardValue.get(),
    setBoard(patch) {
      boardValue.set({ ...boardValue.get(), ...patch }, now());
    },
    effective,
    isViewed(path) {
      return effective(path).viewed;
    },
    setViewed(path, viewed) {
      const own = fileValue(path);
      const range = effective(path);
      const blob = viewedToken(range.toBlob);
      // Unticking drops the mark base merges carried forward too, or the file would stay viewed.
      const others = own
        .get()
        .viewed.filter(
          (mark) => mark.blob !== blob && mark.blob !== range.viewedMark,
        );
      const marks = viewed ? [...others, { blob, at: now() }] : others;
      own.set({ ...own.get(), viewed: marks }, own.at() || now());
    },
    viewedAt: (path) =>
      new Map(
        fileValue(path)
          .get()
          .viewed.map((mark) => [mark.blob, mark.at]),
      ),
    setRange(path, patch) {
      const own = fileValue(path);
      own.set({ ...own.get(), ...patch }, now());
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    destroy() {
      destroyed = true;
      for (const unsubscribe of unsubscribes) unsubscribe();
      listeners.clear();
    },
  };
}
