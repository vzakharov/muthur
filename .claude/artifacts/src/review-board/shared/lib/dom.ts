export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Sets a `<select>`'s options and selected `value`, leaving the option nodes in place when they are unchanged. */
export function setOptions(
  select: HTMLSelectElement,
  options: readonly { value: string; label: string }[],
  value: string,
): void {
  const same =
    select.options.length === options.length &&
    options.every(
      (option, index) =>
        select.options[index]?.value === option.value &&
        select.options[index].textContent === option.label,
    );
  if (!same) {
    select.replaceChildren(
      ...options.map((option) => {
        const node = document.createElement("option");
        node.value = option.value;
        node.textContent = option.label;
        return node;
      }),
    );
  }
  if (select.value !== value) select.value = value;
}
