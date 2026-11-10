const SCROLLING = /auto|scroll/;

function canScroll(el: Element, dx: number, dy: number): boolean {
  const style = getComputedStyle(el);
  if (Math.abs(dy) >= Math.abs(dx)) {
    if (!SCROLLING.test(style.overflowY)) return false;
    return dy < 0
      ? el.scrollTop > 0
      : el.scrollTop + el.clientHeight < el.scrollHeight - 1;
  }
  if (!SCROLLING.test(style.overflowX)) return false;
  return dx < 0
    ? el.scrollLeft > 0
    : el.scrollLeft + el.clientWidth < el.scrollWidth - 1;
}

/**
 * Whether a wheel over `target` would scroll an element inside `boundary`
 * (exclusive) that can still move in the wheel's direction.
 */
export function scrollsInside(
  target: EventTarget | null,
  boundary: Element,
  dx: number,
  dy: number,
): boolean {
  let el = target instanceof Element ? target : null;
  while (el !== null && el !== boundary) {
    if (canScroll(el, dx, dy)) return true;
    el = el.parentElement;
  }
  return false;
}
