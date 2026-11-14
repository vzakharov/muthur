import MarkdownIt from "markdown-it";
import { el } from "#src/review-board/shared/lib/dom.ts";

// Raw HTML in the source stays escaped text (`html: false`), and images are off
// so that rendering a file never fetches anything.
const markdown = new MarkdownIt({ html: false, linkify: false }).disable(
  "image",
);

const renderLink = markdown.renderer.rules["link_open"];
markdown.renderer.rules["link_open"] = (tokens, index, options, env, self) => {
  const token = tokens[index];
  if (token !== undefined) {
    token.attrSet("target", "_blank");
    token.attrSet("rel", "noopener noreferrer");
  }
  return renderLink === undefined
    ? self.renderToken(tokens, index, options)
    : renderLink(tokens, index, options, env, self);
};

/** The Markdown `text` as a document; it carries no comment anchors. */
export function renderMarkdown(text: string): HTMLElement {
  const root = el("div", "markdown");
  // markdown-it escapes raw HTML and refuses `javascript:` links, so its output is safe markup.
  root.innerHTML = markdown.render(text);
  return root;
}
