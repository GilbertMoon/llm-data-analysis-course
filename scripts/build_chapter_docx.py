#!/usr/bin/env python3
"""Build chapter-level DOCX files from the book Markdown sources.

The source Markdown files are never modified. Each chapter is converted with Pandoc
using a shared Word reference template. Local SVG images can be converted to PNG for
more reliable Word rendering.

Default input:
    book/chapters/ch00_*.md ... book/chapters/ch15_*.md

Default output:
    book/output/docx/chapters/ch00_*.docx ... ch15_*.docx

The script also writes a manual review gate file:
    book/output/docx/chapter_review_status.csv

After visually reviewing each DOCX, change its status from ``pending`` to
``approved``. The merge script refuses to build a combined DOCX unless the selected
chapter files are approved and their hashes still match.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOK_DIR = REPO_ROOT / "book"
CHAPTER_DIR = BOOK_DIR / "chapters"
DEFAULT_OUTPUT_DIR = BOOK_DIR / "output" / "docx" / "chapters"
DEFAULT_REVIEW_STATUS = BOOK_DIR / "output" / "docx" / "chapter_review_status.csv"
DEFAULT_REFERENCE_DOC = REPO_ROOT / "templates" / "llm_data_analysis_reference.docx"
ASSET_DIRS = [BOOK_DIR / "assets", REPO_ROOT / "images", REPO_ROOT]

CHAPTER_SOURCES: dict[int, str] = {
    0: "ch00_book_overview.md",
    1: "ch01_ai_data_analysis_intro.md",
    2: "ch02_environment_setup.md",
    3: "ch03_data_first_impression.md",
    4: "ch04_pandas_data_questions.md",
    5: "ch05_data_preprocessing.md",
    6: "ch06_eda_questions.md",
    7: "ch07_visualization.md",
    8: "ch08_midterm_project.md",
    9: "ch09_regression_analysis.md",
    10: "ch10_llm_code_generation.md",
    11: "ch11_llm_prompt_analysis.md",
    12: "ch12_report_generation.md",
    13: "ch13_external_data_collection.md",
    14: "ch14_airflow_pipeline.md",
    15: "ch15_final_project.md",
}

REVIEW_FIELDS = [
    "chapter",
    "source",
    "output",
    "source_sha256",
    "docx_sha256",
    "status",
    "reviewed_by",
    "reviewed_at",
    "notes",
]

FIGURE_RE = re.compile(r"<figure\b[^>]*>(.*?)</figure>", flags=re.IGNORECASE | re.DOTALL)
IMG_TAG_RE = re.compile(r"<img\b([^>]*)/?>", flags=re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(
    r"([:\w-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
    flags=re.IGNORECASE,
)
MARKDOWN_IMAGE_RE = re.compile(
    r"!\[([^\]]*)\]\((?:<([^>]+)>|([^\s\)]+))(?:\s+[\"']([^\"']*)[\"'])?\)",
    flags=re.IGNORECASE,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class PreparedMarkdown:
    path: Path
    converted_svg_count: int
    warnings: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Chapter 0-15 Markdown files to individually reviewable DOCX files."
    )
    parser.add_argument(
        "--chapters",
        type=int,
        nargs="+",
        choices=range(0, 16),
        metavar="0-15",
        help="Specific chapters to build. Default: all chapters 0 through 15.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Chapter DOCX output directory.",
    )
    parser.add_argument(
        "--reference-doc",
        type=Path,
        default=DEFAULT_REFERENCE_DOC,
        help="Pandoc Word reference template. Defaults to the repository common template.",
    )
    parser.add_argument(
        "--review-status",
        type=Path,
        default=DEFAULT_REVIEW_STATUS,
        help="CSV file used as the manual review approval gate.",
    )
    parser.add_argument(
        "--svg-mode",
        choices=["auto", "png", "keep"],
        default="auto",
        help=(
            "SVG handling: auto converts when CairoSVG/Inkscape is available, "
            "png requires conversion, keep leaves SVG unchanged. Default: auto."
        ),
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Keep existing DOCX files instead of rebuilding them.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without writing files.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep prepared Markdown and converted PNG files next to the output for debugging.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def selected_chapters(values: list[int] | None) -> list[int]:
    return sorted(values if values else CHAPTER_SOURCES.keys())


def source_path_for(chapter: int) -> Path:
    return CHAPTER_DIR / CHAPTER_SOURCES[chapter]


def output_path_for(chapter: int, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    return output_dir / Path(CHAPTER_SOURCES[chapter]).with_suffix(".docx").name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError(
            "Pandoc was not found in PATH. Install Pandoc first and reopen the terminal."
        )
    return pandoc


def resolve_reference_doc(path: Path) -> Path:
    resolved = resolve_repo_path(path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Word reference template was not found: {rel(resolved)}")
    if resolved.suffix.lower() != ".docx" or not zipfile.is_zipfile(resolved):
        raise RuntimeError(f"Invalid Word reference template: {rel(resolved)}")
    return resolved


def find_svg_converter() -> str | None:
    # Prefer desktop/vector renderers when available because they usually preserve
    # system Korean fonts more faithfully. CairoSVG is the portable fallback.
    for candidate in ("inkscape", "inkscape.exe", "rsvg-convert"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    try:
        import cairosvg  # noqa: F401

        return "cairosvg"
    except Exception:  # noqa: BLE001
        return None


def convert_svg_to_png(svg_path: Path, png_path: Path, converter: str) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if converter == "cairosvg":
        import cairosvg

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1800)
        return

    if Path(converter).name.lower().startswith("rsvg-convert"):
        subprocess.run(
            [converter, "--width", "1800", "--output", str(png_path), str(svg_path)],
            check=True,
        )
        return

    subprocess.run(
        [
            converter,
            str(svg_path),
            "--export-type=png",
            f"--export-filename={png_path}",
            "--export-width=1800",
        ],
        check=True,
    )


def is_external_ref(ref: str) -> bool:
    lowered = ref.lower().strip()
    return lowered.startswith(("http://", "https://", "data:", "mailto:"))


def resolve_local_ref(source_dir: Path, ref: str) -> Path:
    decoded = unquote(html.unescape(ref.strip()))
    candidate = Path(decoded)
    if candidate.is_absolute():
        return candidate
    return (source_dir / candidate).resolve()


def parse_html_attrs(raw_attrs: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(raw_attrs):
        value = next(group for group in match.groups()[1:] if group is not None)
        attrs[match.group(1).lower()] = html.unescape(value)
    return attrs


def plain_text(value: str) -> str:
    return " ".join(html.unescape(HTML_TAG_RE.sub("", value)).split())


def html_figures_to_markdown(content: str) -> str:
    def replace_figure(match: re.Match[str]) -> str:
        inner = match.group(1)
        image_match = IMG_TAG_RE.search(inner)
        if not image_match:
            return match.group(0)
        attrs = parse_html_attrs(image_match.group(1))
        src = attrs.get("src", "").strip()
        if not src:
            return match.group(0)
        alt = attrs.get("alt", "이미지").replace("[", "").replace("]", "")
        caption_match = re.search(
            r"<figcaption\b[^>]*>(.*?)</figcaption>",
            inner,
            flags=re.IGNORECASE | re.DOTALL,
        )
        caption = plain_text(caption_match.group(1)) if caption_match else ""
        result = f"![{alt}]({src})"
        if caption:
            result += f"\n\n*{caption}*"
        return f"\n\n{result}\n\n"

    content = FIGURE_RE.sub(replace_figure, content)

    def replace_img(match: re.Match[str]) -> str:
        attrs = parse_html_attrs(match.group(1))
        src = attrs.get("src", "").strip()
        if not src:
            return match.group(0)
        alt = attrs.get("alt", "이미지").replace("[", "").replace("]", "")
        return f"![{alt}]({src})"

    return IMG_TAG_RE.sub(replace_img, content)


def prepare_markdown(md_path: Path, temp_dir: Path, svg_mode: str) -> PreparedMarkdown:
    content = html_figures_to_markdown(md_path.read_text(encoding="utf-8"))
    warnings: list[str] = []
    converted_svg_count = 0
    converter = None if svg_mode == "keep" else find_svg_converter()

    if svg_mode == "png" and converter is None:
        raise RuntimeError(
            "SVG-to-PNG conversion was required but CairoSVG or Inkscape was not found."
        )
    if svg_mode == "auto" and converter is None:
        warnings.append(
            "No SVG converter was found; SVG files will be embedded as-is. "
            "Install CairoSVG or Inkscape if Word does not render them correctly."
        )

    def replace_image(match: re.Match[str]) -> str:
        nonlocal converted_svg_count
        alt = match.group(1)
        ref = match.group(2) or match.group(3) or ""
        title = match.group(4)

        if is_external_ref(ref):
            return match.group(0)

        local_path = resolve_local_ref(md_path.parent, ref)
        if not local_path.exists():
            warnings.append(f"Image not found; original reference kept: {ref}")
            return match.group(0)

        target = local_path
        if local_path.suffix.lower() == ".svg" and svg_mode != "keep" and converter:
            key = hashlib.sha1(str(local_path).encode("utf-8")).hexdigest()[:10]
            target = temp_dir / "images" / f"{local_path.stem}_{key}.png"
            convert_svg_to_png(local_path, target, converter)
            converted_svg_count += 1
            if svg_mode == "auto":
                try:
                    contains_korean_text = bool(
                        re.search(r"[가-힣]", local_path.read_text(encoding="utf-8", errors="ignore"))
                    )
                except OSError:
                    contains_korean_text = False
                if contains_korean_text:
                    warnings.append(
                        f"SVG with Korean text was converted to PNG; verify font rendering in Word: {ref}"
                    )

        safe_ref = target.resolve().as_posix()
        title_part = f' "{title}"' if title else ""
        return f"![{alt}](<{safe_ref}>{title_part})"

    content = MARKDOWN_IMAGE_RE.sub(replace_image, content)
    prepared = temp_dir / md_path.name
    prepared.write_text(content, encoding="utf-8", newline="\n")
    return PreparedMarkdown(prepared, converted_svg_count, warnings)


def build_resource_path(md_path: Path, temp_dir: Path) -> str:
    paths = [temp_dir, temp_dir / "images", md_path.parent, *ASSET_DIRS]
    return os.pathsep.join(str(path.resolve()) for path in paths if path.exists())


def build_pandoc_command(
    pandoc: str,
    prepared_md: Path,
    original_md: Path,
    output_docx: Path,
    reference_doc: Path,
    temp_dir: Path,
) -> list[str]:
    return [
        pandoc,
        str(prepared_md),
        "--from=gfm+raw_html",
        "--to=docx",
        "--standalone",
        f"--reference-doc={reference_doc}",
        f"--resource-path={build_resource_path(original_md, temp_dir)}",
        f"--output={output_docx}",
    ]


def validate_docx(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"DOCX was not created correctly: {rel(path)}")
    if not zipfile.is_zipfile(path):
        raise RuntimeError(f"Generated file is not a valid DOCX package: {rel(path)}")
    with zipfile.ZipFile(path) as archive:
        required = {"[Content_Types].xml", "word/document.xml", "word/styles.xml"}
        missing = required.difference(archive.namelist())
        if missing:
            raise RuntimeError(f"DOCX package is missing required parts: {sorted(missing)}")


def load_review_rows(path: Path) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                rows[int(row.get("chapter", ""))] = {field: row.get(field, "") for field in REVIEW_FIELDS}
            except ValueError:
                continue
    return rows


def write_review_rows(path: Path, rows: dict[int, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        for chapter in sorted(CHAPTER_SOURCES):
            row = rows.get(chapter, {})
            writer.writerow({field: row.get(field, "") for field in REVIEW_FIELDS})


def make_default_review_row(chapter: int, output_dir: Path) -> dict[str, str]:
    return {
        "chapter": str(chapter),
        "source": rel(source_path_for(chapter)),
        "output": rel(output_path_for(chapter, output_dir)),
        "source_sha256": "",
        "docx_sha256": "",
        "status": "pending",
        "reviewed_by": "",
        "reviewed_at": "",
        "notes": "",
    }


def update_review_row(
    rows: dict[int, dict[str, str]],
    chapter: int,
    source: Path,
    output: Path,
    output_dir: Path,
) -> None:
    row = rows.get(chapter, make_default_review_row(chapter, output_dir))
    row.update(
        {
            "chapter": str(chapter),
            "source": rel(source),
            "output": rel(output),
            "source_sha256": sha256_file(source),
            "docx_sha256": sha256_file(output),
            "status": "pending",
            "reviewed_by": "",
            "reviewed_at": "",
            "notes": "Rebuilt; manual visual review required.",
        }
    )
    rows[chapter] = row


def build_one(
    chapter: int,
    pandoc: str,
    reference_doc: Path,
    output_dir: Path,
    svg_mode: str,
    dry_run: bool,
    skip_existing: bool,
    keep_temp: bool,
) -> tuple[Path, bool]:
    source = source_path_for(chapter)
    output = output_path_for(chapter, output_dir)

    if not source.exists():
        raise FileNotFoundError(f"Missing chapter source: {rel(source)}")

    if dry_run:
        print(f"[DRY-RUN] Chapter {chapter:02d}: {rel(source)} -> {rel(output)}")
        return output, False

    if output.exists() and skip_existing:
        validate_docx(output)
        print(f"[SKIP] Existing chapter DOCX kept: {rel(output)}")
        return output, False

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ch{chapter:02d}_docx_") as temp_name:
        temp_dir = Path(temp_name)
        prepared = prepare_markdown(source, temp_dir, svg_mode)
        for warning in prepared.warnings:
            print(f"[WARN] Chapter {chapter:02d}: {warning}")

        temp_output = output.with_name(output.stem + ".tmp.docx")
        if temp_output.exists():
            temp_output.unlink()

        command = build_pandoc_command(
            pandoc=pandoc,
            prepared_md=prepared.path,
            original_md=source,
            output_docx=temp_output,
            reference_doc=reference_doc,
            temp_dir=temp_dir,
        )
        subprocess.run(command, cwd=REPO_ROOT, check=True)
        validate_docx(temp_output)
        temp_output.replace(output)
        validate_docx(output)

        if keep_temp:
            debug_dir = output.parent / f".{output.stem}_build_temp"
            if debug_dir.exists():
                shutil.rmtree(debug_dir)
            shutil.copytree(temp_dir, debug_dir)
            print(f"[INFO] Temp files kept: {rel(debug_dir)}")

        print(
            f"[OK] Chapter {chapter:02d}: {rel(output)} "
            f"(svg_to_png={prepared.converted_svg_count}, bytes={output.stat().st_size})"
        )
    return output, True


def main() -> int:
    args = parse_args()
    output_dir = resolve_repo_path(args.output_dir).resolve()
    review_status = resolve_repo_path(args.review_status).resolve()

    try:
        pandoc = ensure_pandoc()
        reference_doc = resolve_reference_doc(args.reference_doc)
        chapters = selected_chapters(args.chapters)
        review_rows = load_review_rows(review_status)
        for chapter in CHAPTER_SOURCES:
            review_rows.setdefault(chapter, make_default_review_row(chapter, output_dir))

        print(f"[INFO] Pandoc: {pandoc}")
        print(f"[INFO] Word template: {rel(reference_doc)}")
        print(f"[INFO] Output directory: {rel(output_dir)}")
        print(f"[INFO] Chapters: {', '.join(f'{number:02d}' for number in chapters)}")
        print()

        for chapter in chapters:
            output, rebuilt = build_one(
                chapter=chapter,
                pandoc=pandoc,
                reference_doc=reference_doc,
                output_dir=output_dir,
                svg_mode=args.svg_mode,
                dry_run=args.dry_run,
                skip_existing=args.skip_existing,
                keep_temp=args.keep_temp,
            )
            if rebuilt:
                update_review_row(
                    rows=review_rows,
                    chapter=chapter,
                    source=source_path_for(chapter),
                    output=output,
                    output_dir=output_dir,
                )

        if not args.dry_run:
            write_review_rows(review_status, review_rows)
            print()
            print(f"[OK] Review status file: {rel(review_status)}")
            print("[NEXT] Open every generated DOCX and visually inspect headings, tables, images, and code blocks.")
            print("[NEXT] In the CSV, change status to approved only after the chapter passes review.")
            print("[NEXT] Then run: python scripts/merge_chapter_docx.py")
        else:
            print("\n[OK] Dry run completed. No files were written.")

    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Pandoc failed with exit code {exc.returncode}.", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
