"""Convert Markdown chapter manuscripts in book/chapters to HTML.

Usage:
    python scripts/build_book_html.py

The script uses the optional ``markdown`` package when it is installed.
If it is not installed, a small built-in converter handles the Markdown
patterns used in this course manuscript: headings, paragraphs, tables,
bullet lists, numbered lists, inline code, fenced code blocks, and raw
placeholder div blocks.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import shutil


ROOT_DIR = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT_DIR / "book" / "chapters"
ASSETS_DIR = ROOT_DIR / "book" / "assets"
TEMPLATE_CSS = ROOT_DIR / "book" / "templates" / "ebook.css"
OUTPUT_DIR = ROOT_DIR / "book" / "output" / "html"
OUTPUT_ASSETS_DIR = ROOT_DIR / "book" / "output" / "assets"


TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
ORDERED_LIST_RE = re.compile(r"^(\s*)\d+\.\s+(.+)$")
UNORDERED_LIST_RE = re.compile(r"^(\s*)-\s+(.+)$")
BLOCKQUOTE_RE = re.compile(r"^\s*>\s?(.*)$")


def parse_inline(text: str) -> str:
    """Convert inline Markdown code spans while escaping other text."""
    parts = re.split(r"(`[^`]+`)", text)
    html_parts: list[str] = []

    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            html_parts.append(f"<code>{escape(part[1:-1])}</code>")
        else:
            html_parts.append(escape(part))

    return "".join(html_parts)


def split_table_row(line: str) -> list[str]:
    """Split a simple Markdown table row into cells."""
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def table_to_html(lines: list[str]) -> str:
    """Convert a simple Markdown table block to HTML."""
    header = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]

    thead = "<thead><tr>" + "".join(
        f"<th>{parse_inline(cell)}</th>" for cell in header
    ) + "</tr></thead>"
    tbody_rows = []
    for row in rows:
        tbody_rows.append(
            "<tr>" + "".join(f"<td>{parse_inline(cell)}</td>" for cell in row) + "</tr>"
        )

    tbody = "<tbody>" + "\n".join(tbody_rows) + "</tbody>"
    return f"<table>\n{thead}\n{tbody}\n</table>"


def unordered_list_to_html(items: list[str]) -> str:
    """Convert unordered list item text values to HTML."""
    lis = [f"<li>{parse_inline(item.strip())}</li>" for item in items]
    return "<ul>\n" + "\n".join(lis) + "\n</ul>"


def parse_ordered_list(lines: list[str], start_index: int) -> tuple[str, int]:
    """Convert an ordered list and indented bullet children to HTML.

    This keeps structures such as:

        1. Question
           - Submit as Markdown

        2. Question
           - Submit as a table

    inside one <ol>, so numbering continues correctly in the browser.
    """
    items: list[tuple[str, list[str]]] = []
    current_text: str | None = None
    current_children: list[str] = []
    i = start_index

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if ORDERED_LIST_RE.match(next_line):
                i += 1
                continue
            break

        ordered_match = ORDERED_LIST_RE.match(line)
        if ordered_match and not ordered_match.group(1):
            if current_text is not None:
                items.append((current_text, current_children))
            current_text = ordered_match.group(2).strip()
            current_children = []
            i += 1
            continue

        unordered_match = UNORDERED_LIST_RE.match(line)
        if unordered_match and unordered_match.group(1) and current_text is not None:
            current_children.append(unordered_match.group(2).strip())
            i += 1
            continue

        break

    if current_text is not None:
        items.append((current_text, current_children))

    html_items = []
    for text, children in items:
        child_html = "\n" + unordered_list_to_html(children) if children else ""
        html_items.append(f"<li>{parse_inline(text)}{child_html}</li>")

    return "<ol>\n" + "\n".join(html_items) + "\n</ol>", i


def parse_unordered_list(lines: list[str], start_index: int) -> tuple[str, int]:
    """Convert a top-level unordered list to HTML."""
    items: list[str] = []
    i = start_index

    while i < len(lines):
        match = UNORDERED_LIST_RE.match(lines[i])
        if not match or match.group(1):
            break
        items.append(match.group(2).strip())
        i += 1

    return unordered_list_to_html(items), i


def parse_blockquote(lines: list[str], start_index: int) -> tuple[str, int]:
    """Convert consecutive Markdown blockquote lines to HTML."""
    quote_lines: list[str] = []
    i = start_index

    while i < len(lines):
        match = BLOCKQUOTE_RE.match(lines[i])
        if not match:
            break
        quote_lines.append(match.group(1).strip())
        i += 1

    quote_text = " ".join(part for part in quote_lines if part)
    return f"<blockquote>{parse_inline(quote_text)}</blockquote>", i


def simple_markdown_to_html(markdown_text: str) -> str:
    """Convert the course manuscript's core Markdown syntax to HTML."""
    lines = markdown_text.splitlines()
    html_blocks: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            class_attr = f' class="language-{escape(language)}"' if language else ""
            html_blocks.append(
                f"<pre><code{class_attr}>{escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        if stripped.startswith('<div class="placeholder"'):
            raw_lines = [line]
            i += 1
            while i < len(lines):
                raw_lines.append(lines[i])
                if "</div>" in lines[i]:
                    i += 1
                    break
                i += 1
            html_blocks.append("\n".join(raw_lines))
            continue

        if stripped.startswith('<figure class="figure"'):
            raw_lines = [line]
            i += 1
            while i < len(lines):
                raw_lines.append(lines[i])
                if "</figure>" in lines[i]:
                    i += 1
                    break
                i += 1
            html_blocks.append("\n".join(raw_lines))
            continue

        if BLOCKQUOTE_RE.match(line):
            html, i = parse_blockquote(lines, i)
            html_blocks.append(html)
            continue

        if i + 1 < len(lines) and "|" in line and TABLE_SEPARATOR_RE.match(lines[i + 1]):
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            html_blocks.append(table_to_html(table_lines))
            continue

        ordered_match = ORDERED_LIST_RE.match(line)
        if ordered_match and not ordered_match.group(1):
            html, i = parse_ordered_list(lines, i)
            html_blocks.append(html)
            continue

        unordered_match = UNORDERED_LIST_RE.match(line)
        if unordered_match and not unordered_match.group(1):
            html, i = parse_unordered_list(lines, i)
            html_blocks.append(html)
            continue

        if stripped.startswith("# "):
            html_blocks.append(f"<h1>{parse_inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            html_blocks.append(f"<h2>{parse_inline(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            html_blocks.append(f"<h3>{parse_inline(stripped[4:])}</h3>")
        elif stripped.startswith("#### "):
            html_blocks.append(f"<h4>{parse_inline(stripped[5:])}</h4>")
        else:
            html_blocks.append(f"<p>{parse_inline(stripped)}</p>")

        i += 1

    return "\n".join(html_blocks)


def markdown_to_html(markdown_text: str) -> str:
    """Use Python-Markdown when available, otherwise use the built-in converter."""
    try:
        import markdown  # type: ignore
    except ImportError:
        return simple_markdown_to_html(markdown_text)

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


def extract_title(markdown_text: str, fallback: str) -> str:
    """Use the first H1 heading as the HTML document title."""
    match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def build_all_chapters() -> None:
    """Convert all chapter Markdown files to HTML."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copy_assets()
    css_text = TEMPLATE_CSS.read_text(encoding="utf-8")

    for chapter_path in sorted(CHAPTERS_DIR.glob("*.md")):
        markdown_text = chapter_path.read_text(encoding="utf-8")
        title = extract_title(markdown_text, chapter_path.stem)
        body_html = markdown_to_html(markdown_text)
        output_path = OUTPUT_DIR / f"{chapter_path.stem}.html"
        output_path.write_text(build_page(title, body_html, css_text), encoding="utf-8")
        print(f"HTML 생성: {output_path}")


def copy_assets() -> None:
    """Copy book/assets to book/output/assets so relative image paths work."""
    if not ASSETS_DIR.exists():
        return

    if OUTPUT_ASSETS_DIR.exists():
        shutil.rmtree(OUTPUT_ASSETS_DIR)
    shutil.copytree(ASSETS_DIR, OUTPUT_ASSETS_DIR)


if __name__ == "__main__":
    build_all_chapters()
