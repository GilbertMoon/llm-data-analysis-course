"""book/chapters의 Markdown 원고를 HTML 파일로 변환합니다.

기본 사용법:
    python scripts/build_book_html.py

선택 패키지:
    더 완성도 높은 Markdown 변환이 필요하면 markdown 패키지를 설치하세요.
    python -m pip install markdown
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import re


ROOT_DIR = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT_DIR / "book" / "chapters"
TEMPLATE_CSS = ROOT_DIR / "book" / "templates" / "ebook.css"
OUTPUT_DIR = ROOT_DIR / "book" / "output" / "html"


def simple_markdown_to_html(markdown_text: str) -> str:
    """외부 패키지 없이 기본 Markdown 문법 일부를 HTML로 변환합니다."""
    html_lines: list[str] = []
    in_code_block = False
    code_lines: list[str] = []

    for line in markdown_text.splitlines():
        if line.startswith("```"):
            if in_code_block:
                html_lines.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            html_lines.append("")
        elif stripped.startswith("# "):
            html_lines.append(f"<h1>{escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{escape(stripped[3:])}</h2>")
        elif stripped.startswith("### "):
            html_lines.append(f"<h3>{escape(stripped[4:])}</h3>")
        elif stripped.startswith("- "):
            html_lines.append(f"<p>{escape(stripped)}</p>")
        else:
            html_lines.append(f"<p>{escape(stripped)}</p>")

    if in_code_block:
        html_lines.append("<pre><code>" + escape("\n".join(code_lines)) + "</code></pre>")

    return "\n".join(html_lines)


def markdown_to_html(markdown_text: str) -> str:
    """markdown 패키지가 있으면 사용하고, 없으면 단순 변환기를 사용합니다."""
    try:
        import markdown  # type: ignore
    except ImportError:
        return simple_markdown_to_html(markdown_text)

    return markdown.markdown(
        markdown_text,
        extensions=["fenced_code", "tables", "toc"],
        output_format="html5",
    )


def build_page(title: str, body_html: str, css_text: str) -> str:
    """챕터 HTML 문서 하나를 만듭니다."""
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
    """첫 번째 H1 제목을 문서 제목으로 사용합니다."""
    match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def build_all_chapters() -> None:
    """모든 챕터 Markdown 파일을 HTML로 변환합니다."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    css_text = TEMPLATE_CSS.read_text(encoding="utf-8")

    for chapter_path in sorted(CHAPTERS_DIR.glob("*.md")):
        markdown_text = chapter_path.read_text(encoding="utf-8")
        title = extract_title(markdown_text, chapter_path.stem)
        body_html = markdown_to_html(markdown_text)
        output_path = OUTPUT_DIR / f"{chapter_path.stem}.html"
        output_path.write_text(build_page(title, body_html, css_text), encoding="utf-8")
        print(f"HTML 생성: {output_path}")


if __name__ == "__main__":
    build_all_chapters()
