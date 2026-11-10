/**
 * The focus item after `at` to step to: the next one not yet viewed, wrapping
 * around, or simply the next one once every item is viewed. Null with no items.
 */
export function nextFocus(
  at: number | null,
  viewed: readonly boolean[],
): number | null {
  const count = viewed.length;
  if (count === 0) return null;
  const start = at === null ? 0 : (at + 1) % count;
  for (let step = 0; step < count; step++) {
    const index = (start + step) % count;
    if (viewed[index] !== true) return index;
  }
  return start;
}
