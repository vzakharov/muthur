import { DATA_ID, ROOT_ID } from "../shared/lib/page-ids.ts";

/** JSON for a `<script type="application/json">` body: `<` is escaped so no `</script` or `<!--` can occur. */
export function escapeJson(value: unknown): string {
  return JSON.stringify(value).replaceAll("<", "\\u003c");
}

/** A bundle for a classic `<script>` body, where `</script` would end the element early. */
export function escapeScript(js: string): string {
  return js.replaceAll("</script", "<\\/script");
}

export interface PageParts {
  data: unknown;
  js: string;
  css: string;
}

export interface Page {
  /** The page content the Artifact tool publishes; it adds the document skeleton. */
  fragment: string;
  /** The same content as a complete document, for opening off disk. */
  document: string;
}

const TITLE = "<title>Review board</title>";

export function renderPage({ data, js, css }: PageParts): Page {
  const head = `${TITLE}\n<style>${css}</style>`;
  const body = [
    `<div id="${ROOT_ID}"></div>`,
    `<script type="application/json" id="${DATA_ID}">${escapeJson(data)}</script>`,
    `<script>${escapeScript(js)}</script>`,
  ].join("\n");
  return {
    fragment: `${head}\n${body}\n`,
    document: [
      "<!doctype html>",
      '<html lang="en">',
      '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
      head,
      "</head>",
      `<body>\n${body}\n</body>`,
      "</html>",
      "",
    ].join("\n"),
  };
}
