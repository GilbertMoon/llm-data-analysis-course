"""Build chapter HTML files from Markdown manuscripts.

Usage:
    python scripts/build_book_html.py

This builder is the source of truth for the distributable HTML files under
``book/output/html``. It normalizes chapter Markdown, renders HTML, adds stable
heading IDs, creates a table of contents for every chapter, and copies image
assets to the output folder.
"""

from __future__ import annotations

from html import escape, unescape
from pathlib import Path
import re
import shutil

import markdown


ROOT_DIR = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT_DIR / "book" / "chapters"
ASSETS_DIR = ROOT_DIR / "book" / "assets"
TEMPLATE_CSS = ROOT_DIR / "book" / "templates" / "ebook.css"
OUTPUT_DIR = ROOT_DIR / "book" / "output" / "html"
OUTPUT_ASSETS_DIR = ROOT_DIR / "book" / "output" / "assets"


def normalize_markdown_text(markdown_text: str) -> str:
    """Normalize manuscript text before conversion."""
    markdown_text = markdown_text.lstrip("\ufeff")
    markdown_text = re.sub(
        r"^(```|~~~)([A-Za-z0-9_-]+)[^\S\r\n]+.*$",
        r"\1\2",
        markdown_text,
        flags=re.MULTILINE,
    )
    markdown_text = re.sub(
        r"&lt;strong&gt;(.*?)&lt;/strong&gt;",
        r"**\1**",
        markdown_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    markdown_text = re.sub(
        r"<strong>(.*?)</strong>",
        r"**\1**",
        markdown_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return re.sub(r"^(\s*)\*\s+", r"\1- ", markdown_text, flags=re.MULTILINE)


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown text to HTML using Python-Markdown."""
    return markdown.markdown(
        markdown_text,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
            "attr_list",
            "md_in_html",
        ],
        output_format="html5",
    )


def plain_text_from_html(html_text: str) -> str:
    """Return readable text from a small heading HTML fragment."""
    text = re.sub(r"<[^>]+>", "", html_text)
    return unescape(text).strip()


def add_heading_ids_and_toc(body_html: str) -> str:
    """Add stable heading IDs and a compact table of contents after H1."""
    heading_counts: dict[str, int] = {}
    used_ids: set[str] = set()
    toc_items: list[tuple[str, str]] = []

    def unique_id(base_id: str) -> str:
        candidate = base_id
        suffix = 2
        while candidate in used_ids:
            candidate = f"{base_id}-{suffix}"
            suffix += 1
        used_ids.add(candidate)
        return candidate

    def heading_repl(match: re.Match[str]) -> str:
        level = match.group(1)
        attrs = match.group(2) or ""
        inner = match.group(3)

        if " id=" in attrs:
            id_match = re.search(r'id="([^"]+)"', attrs)
            heading_id = unique_id(id_match.group(1) if id_match else f"h{level}")
            attrs = re.sub(r'\s*id="[^"]+"', "", attrs)
        elif level == "1":
            heading_id = unique_id("chapter-title")
        else:
            heading_counts[level] = heading_counts.get(level, 0) + 1
            heading_id = unique_id(f"h{level}-{heading_counts[level]}")

        attrs = f'{attrs} id="{heading_id}"'

        if level == "2":
            toc_items.append((heading_id, plain_text_from_html(inner)))

        return f"<h{level}{attrs}>{inner}</h{level}>"

    body_with_ids = re.sub(r"<h([1-4])([^>]*)>(.*?)</h\1>", heading_repl, body_html)

    if not toc_items or 'class="toc"' in body_with_ids:
        return body_with_ids

    toc_html = [
        '<nav class="toc" aria-label="목차">',
        '<p class="toc-title">목차</p>',
        "<ol>",
    ]
    toc_html.extend(
        f'<li><a href="#{heading_id}">{escape(text)}</a></li>'
        for heading_id, text in toc_items
    )
    toc_html.extend(["</ol>", "</nav>"])
    toc_block = "\n".join(toc_html)

    return re.sub(r"(</h1>)", r"\1\n" + toc_block, body_with_ids, count=1)


def css_for_body(css_text: str, body_html: str) -> str:
    """Keep placeholder styles only for chapters that still use placeholders."""
    if 'class="placeholder"' in body_html:
        return css_text

    css_text = re.sub(r"\n\.placeholder\s*\{[^}]*\}\n", "\n", css_text, flags=re.DOTALL)
    css_text = re.sub(r"\n\s*\.placeholder,\n", "\n", css_text)
    return css_text


def extract_title(markdown_text: str, fallback: str) -> str:
    """Use the first H1 heading as the HTML document title."""
    match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def build_page(title: str, body_html: str, css_text: str) -> str:
    """Build one complete HTML document for a chapter."""
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
{css_text}
  </style>
</head>
<body>
  <main class="chapter">
{body_html}
  </main>
</body>
</html>
"""


def copy_assets() -> None:
    """Copy book/assets to book/output/assets so relative image paths work."""
    if not ASSETS_DIR.exists():
        return

    if OUTPUT_ASSETS_DIR.exists():
        shutil.rmtree(OUTPUT_ASSETS_DIR)
    shutil.copytree(ASSETS_DIR, OUTPUT_ASSETS_DIR)


def build_all_chapters() -> None:
    """Convert all chapter Markdown files to HTML."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    css_text = TEMPLATE_CSS.read_text(encoding="utf-8")

    for chapter_path in sorted(CHAPTERS_DIR.glob("*.md")):
        if chapter_path.stem.endswith("_images"):
            continue

        markdown_text = normalize_markdown_text(chapter_path.read_text(encoding="utf-8"))
        title = extract_title(markdown_text, chapter_path.stem)
        body_html = add_heading_ids_and_toc(markdown_to_html(markdown_text))
        chapter_css = css_for_body(css_text, body_html)
        output_path = OUTPUT_DIR / f"{chapter_path.stem}.html"
        output_path.write_text(build_page(title, body_html, chapter_css), encoding="utf-8")
        print(f"HTML 생성: {output_path}")


if __name__ == "__main__":
    build_all_chapters()
