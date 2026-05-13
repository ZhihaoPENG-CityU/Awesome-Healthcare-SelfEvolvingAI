#!/usr/bin/env python3
"""
Re-sort the 'Self-Evolving AI Papers' section in README.md.

- Groups each bullet entry (top-level `- ...` plus following indented lines).
- Uses arXiv new-style id (YYMM.NNNNN) from the first arxiv.org link for
  ordering: newest submission batch first within each calendar year.
- If the arXiv id implies a different calendar year than the ### heading,
  the entry is moved to the ### block for that year (so 25xx papers are
  not left under ### 2026).

Usage (from repo root):
  python scripts/sort_papers_readme.py
  python scripts/sort_papers_readme.py --dry-run
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

SECTION_START = "## 📝 Self-Evolving AI Papers"
SECTION_END = "## 📚 Survey Papers"

ARXIV_RE = re.compile(
    r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d+)(?:v\d+)?",
    re.IGNORECASE,
)
YEAR_HEADING_RE = re.compile(r"^### (\d{4})\s*$")
VENUE_TAIL_RE = re.compile(r"\(\*[^']*'(\d{2})(?:_(\d{2}))?\*\)")
BIORXIV_DATE_RE = re.compile(r"/10\.1101/(\d{4})\.(\d{2})\.(\d{2})")
TITLE_RE = re.compile(r"\*\*(.+?)\*\*")
VENUE_PREFIX_RE = re.compile(r"^-\s+\(\*([^']+)\*'")
INDEX_DIR = ROOT / "indexes"


def infer_calendar_year_from_arxiv(text: str) -> int | None:
    m = ARXIV_RE.search(text)
    if not m:
        return None
    base = m.group(1).split("v", 1)[0]
    yymm = int(base.split(".", 1)[0])
    yy = yymm // 100
    return 2000 + yy


def venue_tail_year(first_line: str) -> int | None:
    m = VENUE_TAIL_RE.search(first_line)
    if not m:
        return None
    return 2000 + int(m.group(1))


def sort_metric(chunk: str, section_year: int) -> float:
    """Larger = newer within a calendar-year bucket. arXiv YYMM.NNNNN sorts as float."""
    m = ARXIV_RE.search(chunk)
    if m:
        return float(m.group(1).lower().split("v", 1)[0])
    if m := BIORXIV_DATE_RE.search(chunk):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        yy = y % 100
        return yy * 100 + mo + d / 100.0
    fl = chunk.strip().split("\n", 1)[0]
    mtag = re.search(r"\(\*[^']*'(\d{2})_(\d{2})\*\)", fl)
    if mtag and mtag.group(2).isdigit():
        yy, mm = int(mtag.group(1)), int(mtag.group(2))
        return yy * 100 + mm + 0.001
    if venue_tail_year(fl) is not None:
        return (section_year % 100) * 100 - 1.0
    return (section_year % 100) * 100 - 1.0


def target_year_for_chunk(chunk: str, section_year: int) -> int:
    cy = infer_calendar_year_from_arxiv(chunk)
    if cy is not None:
        return cy
    vy = venue_tail_year(chunk.strip().split("\n", 1)[0])
    if vy is not None:
        return vy
    return section_year


def sort_key_for_chunk(chunk: str, section_year: int) -> tuple[float, str]:
    return (-sort_metric(chunk, section_year), chunk)


def split_entries(year_body: str) -> list[str]:
    lines = year_body.splitlines(keepends=True)
    chunks: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        if not lines[i].startswith("- "):
            i += 1
            continue
        start = i
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if nxt.startswith("- "):
                break
            i += 1
        chunks.append("".join(lines[start:i]))
    return chunks


def parse_entries_by_year(middle: str) -> dict[int, list[str]]:
    lines = middle.splitlines(keepends=True)
    header_end = 0
    for idx, line in enumerate(lines):
        if YEAR_HEADING_RE.match(line.rstrip("\n")):
            header_end = idx
            break
    rest = lines[header_end:]
    entries_by_year: dict[int, list[str]] = defaultdict(list)
    i = 0
    while i < len(rest):
        m = YEAR_HEADING_RE.match(rest[i].rstrip("\n"))
        if not m:
            i += 1
            continue
        section_year = int(m.group(1))
        i += 1
        body_start = i
        while i < len(rest) and not YEAR_HEADING_RE.match(rest[i].rstrip("\n")):
            i += 1
        body = "".join(rest[body_start:i])
        for chunk in split_entries(body):
            if not chunk.strip():
                continue
            ty = target_year_for_chunk(chunk, section_year)
            entries_by_year[ty].append(chunk)
    return entries_by_year


def rebuild_papers_section(middle: str) -> str:
    lines = middle.splitlines(keepends=True)
    header_end = 0
    for idx, line in enumerate(lines):
        if YEAR_HEADING_RE.match(line.rstrip("\n")):
            header_end = idx
            break
    header = "".join(lines[:header_end])

    entries_by_year = parse_entries_by_year(middle)
    out: list[str] = [header]
    for year in sorted(entries_by_year.keys(), reverse=True):
        blocks = entries_by_year[year]
        blocks.sort(key=lambda c: sort_key_for_chunk(c, year))
        out.append(f"### {year}\n\n")
        for chunk in blocks:
            c = chunk
            if not c.endswith("\n"):
                c += "\n"
            out.append(c)
            if not c.endswith("\n\n"):
                out.append("\n")

    return "".join(out)


def _first_line(chunk: str) -> str:
    return chunk.strip().split("\n", 1)[0]


def _title_and_venue(chunk: str) -> tuple[str, str]:
    fl = _first_line(chunk)
    tm = TITLE_RE.search(fl)
    vm = VENUE_PREFIX_RE.match(fl)
    title = tm.group(1).strip() if tm else fl
    venue = vm.group(1).strip() if vm else "Unknown"
    return title, venue


def write_alternate_indexes(entries_by_year: dict[int, list[str]]) -> None:
    """Write static companion lists (GitHub README cannot offer interactive sort)."""
    INDEX_DIR.mkdir(exist_ok=True)
    rows: list[tuple[int, str, str, str]] = []
    for year in sorted(entries_by_year.keys(), reverse=True):
        for chunk in entries_by_year[year]:
            title, venue = _title_and_venue(chunk)
            rows.append((year, venue, title, chunk))

    by_venue: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for year, venue, title, chunk in rows:
        by_venue[venue].append((year, title, chunk))

    venue_path = INDEX_DIR / "by-venue.md"
    lines_v = [
        "# Paper index by venue (generated)\n\n",
        "Regenerate with: `python scripts/sort_papers_readme.py --write-indexes`\n\n",
        "---\n\n",
    ]
    for venue in sorted(by_venue.keys(), key=str.lower):
        lines_v.append(f"## {venue}\n\n")
        for year, title, chunk in sorted(by_venue[venue], key=lambda r: (-r[0], r[1].lower())):
            lines_v.append(f"- ({year}) **{title}**\n")
            rest = chunk.strip().split("\n", 1)
            if len(rest) > 1 and rest[1].strip():
                lines_v.append(rest[1].strip() + "\n")
            lines_v.append("\n")
    venue_path.write_text("".join(lines_v), encoding="utf-8")

    title_path = INDEX_DIR / "by-title.md"
    lines_t = [
        "# Paper index by title A–Z (generated)\n\n",
        "Regenerate with: `python scripts/sort_papers_readme.py --write-indexes`\n\n",
        "---\n\n",
    ]
    for year, venue, title, chunk in sorted(rows, key=lambda r: (r[2].lower(), -r[0])):
        lines_t.append(f"- **{title}** — *{venue}* · **{year}**\n")
        rest = chunk.strip().split("\n", 1)
        if len(rest) > 1 and rest[1].strip():
            lines_t.append("  " + rest[1].strip().replace("\n", "\n  ") + "\n")
        lines_t.append("\n")
    title_path.write_text("".join(lines_t), encoding="utf-8")

    print(f"Wrote {venue_path.relative_to(ROOT)} and {title_path.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--write-indexes",
        action="store_true",
        help="Also write indexes/by-venue.md and indexes/by-title.md",
    )
    args = ap.parse_args()

    text = README.read_text(encoding="utf-8")
    s = text.index(SECTION_START)
    e = text.index(SECTION_END)

    before = text[:s]
    middle = text[s:e]
    after = text[e:]

    new_middle = rebuild_papers_section(middle)

    if args.dry_run:
        print(new_middle[:2500])
        print("\n... [truncated] ...\n")
        print(new_middle[-1500:])
        return

    README.write_text(before + new_middle + after, encoding="utf-8")
    print(f"Updated {README}")

    if args.write_indexes:
        entries = parse_entries_by_year(new_middle)
        for y, blocks in entries.items():
            blocks.sort(key=lambda c: sort_key_for_chunk(c, y))
        write_alternate_indexes(entries)


if __name__ == "__main__":
    main()
