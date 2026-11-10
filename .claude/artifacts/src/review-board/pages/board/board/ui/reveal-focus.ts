/**
 * Scrolls `container` so its first focus-marked row sits mid-height. The
 * offset is measured on screen and divided by the container's own scale, since
 * a card sits inside the zoomed board while the panel does not.
 */
export function revealFocus(container: HTMLElement): void {
  const row = container.querySelector(".row.focus");
  if (row === null || container.offsetHeight === 0) return;
  const box = container.getBoundingClientRect();
  const scale = box.height / container.offsetHeight;
  const offset = (row.getBoundingClientRect().top - box.top) / scale;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  container.scrollTo({
    top: container.scrollTop + offset - container.clientHeight / 2,
    behavior: reduced ? "auto" : "smooth",
  });
}
