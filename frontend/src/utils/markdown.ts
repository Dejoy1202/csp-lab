import { marked } from "marked";
import DOMPurify from "dompurify";
marked.setOptions({ gfm: true, breaks: false });
export function renderMarkdown(md: string): string {
  if (!md) return "";
  const escape = (v: string) =>
    v.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const chunks = md.split(/(```[\s\S]*?```|`[^`\n]+`)/g);
  const prepared = chunks
    .map((part, i) => {
      if (i % 2) {
        const inline = part.match(/^`([A-Za-z]_(?:[A-Za-z0-9]+|\{[^}]+\}))`$/);
        return inline
          ? '<span class="math-source">$' + escape(inline[1]) + "$</span>"
          : part;
      }
      return part.replace(
        /\$\$([\s\S]*?)\$\$|\\\[([\s\S]*?)\\\]|\\\(([^\n]*?)\\\)|\$([^$\n]+?)\$/g,
        (all) => '<span class="math-source">' + escape(all) + "</span>",
      );
    })
    .join("");
  const raw = marked.parse(prepared, { async: false }) as string;
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: [
      "h1",
      "h2",
      "h3",
      "h4",
      "h5",
      "h6",
      "p",
      "br",
      "hr",
      "ul",
      "ol",
      "li",
      "blockquote",
      "pre",
      "code",
      "em",
      "strong",
      "del",
      "a",
      "table",
      "thead",
      "tbody",
      "tr",
      "th",
      "td",
      "sup",
      "sub",
      "span",
      "div",
    ],
    ALLOWED_ATTR: ["href", "title", "class"],
    ALLOW_DATA_ATTR: false,
  });
}
