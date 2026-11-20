/**
 * `git check-attr` for `linguist-generated`, the `.gitattributes` mark GitHub
 * reads to hide a file by default in diffs, over paths fed NUL-separated on
 * stdin. It reads the attributes from HEAD (git ≥ 2.40) so the board stays
 * built from git alone, whatever the working tree holds.
 */
export const CHECK_HIDDEN_IN_DIFFS = [
  "check-attr",
  "--source=HEAD",
  "-z",
  "--stdin",
  "linguist-generated",
];

/**
 * The paths `CHECK_HIDDEN_IN_DIFFS`'s output marks: its
 * `<path>\0<attr>\0<value>\0` triples whose value is `set` (a bare
 * `linguist-generated`) or `true`.
 */
export function hiddenInDiffs(output: string): Set<string> {
  const tokens = output.split("\0");
  const hidden = new Set<string>();
  for (let i = 0; i + 2 < tokens.length; i += 3) {
    const path = tokens[i];
    const value = tokens[i + 2];
    if (path === undefined || value === undefined)
      throw new Error("truncated check-attr entry");
    if (value === "set" || value === "true") hidden.add(path);
  }
  return hidden;
}
