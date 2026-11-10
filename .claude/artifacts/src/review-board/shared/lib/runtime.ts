/** The claude.ai runtime, or null for a page opened off disk, where the declared `window.claude` is absent. */
export function claudeRuntime(): Claude | null {
  return "claude" in window ? window.claude : null;
}
