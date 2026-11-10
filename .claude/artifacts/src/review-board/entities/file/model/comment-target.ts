/**
 * Where a comment attaches: a file (`side` and `line` null) or one line of its
 * diff. `R` is the new side of the range, `L` the old one.
 */
export interface CommentTarget {
  path: string;
  side: "R" | "L" | null;
  line: number | null;
}
