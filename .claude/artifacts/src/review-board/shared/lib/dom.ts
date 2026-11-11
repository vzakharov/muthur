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
