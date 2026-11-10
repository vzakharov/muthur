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

/** A checkbox inside a `.check` label, reporting each change's checked state. */
export function checkbox(
  text: string,
  onChange: (checked: boolean) => void,
  labelClass = "",
): { box: HTMLInputElement; label: HTMLLabelElement } {
  const box = el("input", "");
  box.type = "checkbox";
  box.addEventListener("change", () => {
    onChange(box.checked);
  });
  const label = el("label", `check ${labelClass}`.trim());
  label.append(box, text);
  return { box, label };
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
