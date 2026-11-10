export interface Stamped<V> {
  value: V;
  at: string;
}

export interface Synced<V> {
  get(): V;
  /** When the value was last stamped; "" for the initial one. */
  at(): string;
  /** A change made here: applied at once, persisted by a write that is queued. */
  set(next: V, at: string): void;
  /** What the store holds, or null for no document; ignored while a local change is unwritten. */
  receive(remote: Stamped<V> | null): void;
}

export interface SyncedOptions<V> {
  initial: V;
  equals(a: V, b: V): boolean;
  write(value: V, at: string): Promise<void>;
  changed(): void;
  failed(error: unknown): void;
}

/**
 * One persisted value. A write is issued only for a change, one at a time; a
 * change made while one is in flight replaces any queued behind it, so the
 * latest value is the last one written.
 */
export function synced<V>(options: SyncedOptions<V>): Synced<V> {
  let value = options.initial;
  let at = "";
  let dirty = false;
  let queued = false;
  let inFlight = false;

  async function drain(): Promise<void> {
    try {
      while (queued) {
        queued = false;
        await options.write(value, at);
      }
    } catch (error) {
      queued = false;
      options.failed(error);
    } finally {
      inFlight = false;
      dirty = queued;
    }
  }

  return {
    get: () => value,
    at: () => at,
    set(next, stamp) {
      if (options.equals(value, next)) return;
      value = next;
      at = stamp;
      dirty = true;
      options.changed();
      queued = true;
      if (!inFlight) {
        inFlight = true;
        void drain();
      }
    },
    receive(remote) {
      if (dirty) return;
      const next = remote?.value ?? options.initial;
      const nextAt = remote?.at ?? "";
      if (options.equals(value, next) && at === nextAt) return;
      value = next;
      at = nextAt;
      options.changed();
    },
  };
}
