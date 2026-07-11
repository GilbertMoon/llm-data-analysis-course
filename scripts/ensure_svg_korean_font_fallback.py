from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SVG_ROOTS = [ROOT / "book" / "assets" / "images", ROOT / "images"]
KOREAN_RE = re.compile(r"[가-힣]")
TEXT_TAG_RE = re.compile(r"<(?:text|tspan)\b", re.IGNORECASE)
MALGUN_RE = re.compile(r"Malgun Gothic|맑은 고딕", re.IGNORECASE)
FONT_FAMILY_PROP_RE = re.compile(
    r"(?P<prefix>\bfont-family\s*:\s*)(?P<value>[^;}]+)(?P<suffix>[;}])",
    re.IGNORECASE | re.DOTALL,
)
FONT_FAMILY_ATTR_RE = re.compile(
    r"(?P<prefix>\bfont-family\s*=\s*\")(?P<value>[^\"]+)(?P<suffix>\")"
    r"|(?P<prefix_sq>\bfont-family\s*=\s*')(?P<value_sq>[^']+)(?P<suffix_sq>')",
    re.IGNORECASE,
)
FONT_SHORTHAND_RE = re.compile(
    r"(?P<prefix>(?<!-)\bfont\s*:\s*)(?P<value>[^;}]+)(?P<suffix>[;}])",
    re.IGNORECASE | re.DOTALL,
)
FONT_SHORTHAND_FAMILY_RE = re.compile(
    r"(?P<head>.*?\b(?:\d+(?:\.\d+)?px|\d+(?:\.\d+)?pt|small|medium|large|x-large|xx-large)\s+)(?P<families>.+)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class Result:
    scanned: int = 0
    korean: int = 0
    no_korean: int = 0
    updated: int = 0
    already: int = 0
    no_font_declaration: int = 0
    parse_errors: int = 0
    missing_fallback: int = 0
    duplicate_malgun: int = 0
    geometry_changes: int = 0


def iter_svg_files() -> list[Path]:
    files: list[Path] = []
    for root in SVG_ROOTS:
        if root.exists():
            files.extend(root.rglob("*.svg"))
    return sorted(set(files))


def root_geometry(svg_text: str) -> tuple[str | None, str | None, str | None]:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return (None, None, None)
    return (root.get("width"), root.get("height"), root.get("viewBox"))


def parse_ok(svg_text: str) -> bool:
    try:
        ET.fromstring(svg_text)
    except ET.ParseError:
        return False
    return True


def has_korean_text(svg_text: str) -> bool:
    return bool(TEXT_TAG_RE.search(svg_text) and KOREAN_RE.search(svg_text))


def has_font_declaration(svg_text: str) -> bool:
    return bool(
        FONT_FAMILY_PROP_RE.search(svg_text)
        or FONT_FAMILY_ATTR_RE.search(svg_text)
        or FONT_SHORTHAND_RE.search(svg_text)
    )


def split_font_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    for char in value:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char == ",":
            tokens.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    tokens.append("".join(current).strip())
    return tokens


def normalize_token(token: str) -> str:
    return token.strip().strip("'\"").lower()


def insert_fallback(value: str) -> str:
    tokens = split_font_tokens(value)
    if not tokens:
        return value

    fallback = ["'Malgun Gothic'", "'맑은 고딕'"]
    original_tokens = tokens[:]
    tokens = [
        token
        for token in tokens
        if normalize_token(token) not in {"malgun gothic", "맑은 고딕"}
    ]
    insert_at: int | None = None

    # CairoSVG on Windows can stop at the first family even when that family
    # cannot render Korean. Keep Noto Korean fonts ahead when they are already
    # first, otherwise make the Windows Korean fallback the first family.
    leading_noto_count = 0
    for token in tokens:
        if normalize_token(token) in {"noto sans kr", "noto sans cjk kr"}:
            leading_noto_count += 1
            continue
        break
    insert_at = leading_noto_count

    tokens[insert_at:insert_at] = fallback
    if tokens == original_tokens:
        return value

    if "\n" in value:
        indent_match = re.search(r"\n([ \t]*)", value)
        indent = indent_match.group(1) if indent_match else "    "
        return (",\n" + indent).join(tokens)
    return ",".join(tokens)


def insert_fallback_in_font_shorthand(value: str) -> str:
    match = FONT_SHORTHAND_FAMILY_RE.match(value.strip())
    if not match:
        return insert_fallback(value)

    head = match.group("head")
    families = match.group("families")
    return f"{head}{insert_fallback(families)}"


def match_part(match: re.Match[str], name: str) -> str:
    groups = match.groupdict()
    if name in groups and groups[name] is not None:
        return groups[name]
    alternate = f"{name}_sq"
    if alternate in groups and groups[alternate] is not None:
        return groups[alternate]
    raise KeyError(name)


def add_fallbacks(svg_text: str) -> tuple[str, bool]:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        value = match_part(match, "value")
        prefix = match_part(match, "prefix")
        suffix = match_part(match, "suffix")
        new_value = insert_fallback(value)
        if new_value != value:
            changed = True
        return f"{prefix}{new_value}{suffix}"

    def replace_shorthand(match: re.Match[str]) -> str:
        nonlocal changed
        value = match_part(match, "value")
        prefix = match_part(match, "prefix")
        suffix = match_part(match, "suffix")
        new_value = insert_fallback_in_font_shorthand(value)
        if new_value != value:
            changed = True
        return f"{prefix}{new_value}{suffix}"

    updated = FONT_FAMILY_PROP_RE.sub(replace, svg_text)
    updated = FONT_FAMILY_ATTR_RE.sub(replace, updated)
    updated = FONT_SHORTHAND_RE.sub(replace_shorthand, updated)
    return updated, changed


def duplicate_malgun_entries(svg_text: str) -> int:
    count = 0
    for regex in (FONT_FAMILY_PROP_RE, FONT_FAMILY_ATTR_RE, FONT_SHORTHAND_RE):
        for match in regex.finditer(svg_text):
            value = match_part(match, "value")
            if len(re.findall(r"Malgun Gothic", value, re.IGNORECASE)) > 1:
                count += 1
    return count


def missing_fallback(svg_text: str) -> bool:
    if not has_korean_text(svg_text) or not has_font_declaration(svg_text):
        return False
    font_values = [
        match_part(match, "value")
        for regex in (FONT_FAMILY_PROP_RE, FONT_FAMILY_ATTR_RE, FONT_SHORTHAND_RE)
        for match in regex.finditer(svg_text)
    ]
    return any(not MALGUN_RE.search(value) for value in font_values)


def process_file(path: Path, write: bool) -> tuple[bool, bool, bool, bool, bool]:
    original = path.read_text(encoding="utf-8")
    before_geometry = root_geometry(original)

    if not parse_ok(original):
        return (False, False, False, False, False)

    korean = has_korean_text(original)
    font_declared = has_font_declaration(original)
    already = False
    changed = False
    geometry_changed = False

    if korean and font_declared:
        updated, changed = add_fallbacks(original)
        if changed and write:
            path.write_text(updated, encoding="utf-8", newline="")
            after_geometry = root_geometry(updated)
            geometry_changed = before_geometry != after_geometry
        already = bool(not changed and MALGUN_RE.search(original))

    return (korean, font_declared, already, changed, geometry_changed)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add Windows Korean font fallbacks to SVG font declarations."
    )
    parser.add_argument("--check", action="store_true", help="Only verify; do not modify files.")
    args = parser.parse_args()

    result = Result()
    for path in iter_svg_files():
        result.scanned += 1
        text = path.read_text(encoding="utf-8")
        if not parse_ok(text):
            result.parse_errors += 1
            continue

        korean, font_declared, already, changed, geometry_changed = process_file(
            path, write=not args.check
        )

        if korean:
            result.korean += 1
        else:
            result.no_korean += 1
        if korean and not font_declared:
            result.no_font_declaration += 1
        if already:
            result.already += 1
        if changed:
            result.updated += 1
        if geometry_changed:
            result.geometry_changes += 1

    for path in iter_svg_files():
        text = path.read_text(encoding="utf-8")
        if parse_ok(text):
            if missing_fallback(text):
                result.missing_fallback += 1
            result.duplicate_malgun += duplicate_malgun_entries(text)

    print(f"SVG files scanned: {result.scanned}")
    print(f"SVG files containing Korean text: {result.korean}")
    print(f"SVG files updated: {result.updated}")
    print(f"SVG files already containing Malgun Gothic: {result.already}")
    print(f"SVG files excluded because no Korean text: {result.no_korean}")
    print(f"SVG files with Korean text but no font declaration: {result.no_font_declaration}")
    print(f"XML parse errors: {result.parse_errors}")
    print(f"Missing Korean fallback fonts: {result.missing_fallback}")
    print(f"Duplicate Malgun Gothic entries: {result.duplicate_malgun}")
    print(f"Geometry changes: {result.geometry_changes}")

    if (
        result.parse_errors
        or result.missing_fallback
        or result.duplicate_malgun
        or result.geometry_changes
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
