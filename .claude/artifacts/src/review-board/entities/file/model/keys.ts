/**
 * Lowercase hex SHA-256 of the UTF-8 text. The agent derives the same key with
 * `printf %s "$path" | sha256sum`, so a path and its `shifts/<key>` doc agree.
 */
export async function fileKey(text: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(text),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
