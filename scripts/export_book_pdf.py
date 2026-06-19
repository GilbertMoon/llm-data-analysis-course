"""HTML 강의안을 PDF로 변환하기 위한 기본 구조입니다.

추후 Playwright를 설치한 뒤 사용할 수 있습니다.

설치 예시:
    python -m pip install playwright
    python -m playwright install chromium

실행 예시:
    python scripts/build_book_html.py
    python scripts/export_book_pdf.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT_DIR / "book" / "output" / "html"
PDF_DIR = ROOT_DIR / "book" / "output" / "pdf"


async def export_html_to_pdf() -> None:
    """book/output/html의 HTML 파일을 PDF로 변환합니다."""
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise SystemExit(
            "Playwright가 설치되어 있지 않습니다. "
            "python -m pip install playwright 실행 후 "
            "python -m playwright install chromium 명령을 실행하세요."
        ) from exc

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()

        for html_path in sorted(HTML_DIR.glob("*.html")):
            pdf_path = PDF_DIR / f"{html_path.stem}.pdf"
            await page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "18mm",
                    "right": "16mm",
                    "bottom": "18mm",
                    "left": "16mm",
                },
            )
            print(f"PDF 생성: {pdf_path}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(export_html_to_pdf())
