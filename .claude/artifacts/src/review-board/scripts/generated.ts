/**
 * `git check-attr` over paths fed NUL-separated on stdin, reading
 * `.gitattributes` from HEAD (git ≥ 2.40) so the board stays built from git
 * alone, whatever the working tree holds.
 */
export const CHECK_GENERATED = [
  "check-attr",
  "--source=HEAD",
  "-z",
  "--stdin",
  "linguist-generated",
];

/**
 * The paths `CHECK_GENERATED`'s output marks generated: its `<path>\0<attr>\0<value>\0`
 * triples whose value is `set` (a bare `linguist-generated`) or `true`.
 */
export function generatedPaths(output: string): Set<string> {
  const tokens = output.split("\0");
  const generated = new Set<string>();
  for (let i = 0; i + 2 < tokens.length; i += 3) {
    const path = tokens[i];
    const value = tokens[i + 2];
    if (path === undefined || value === undefined)
      throw new Error("truncated check-attr entry");
    if (value === "set" || value === "true") generated.add(path);
  }
  return generated;
}
