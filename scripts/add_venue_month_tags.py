#!/usr/bin/env python3
"""
Normalize paper bullet heads:

- When a month can be inferred: (*Venue'YY_MM*) using arXiv YYMM, bioRxiv
  /10.1101/YYYY.MM.DD, or medRxiv/biorxiv.org path dates.
- When month is unknown: keep legacy (*Venue'YY*) — never write (*Venue'YY_??*).

Collapses any legacy (*Venue'YY_??*) to (*Venue'YY*) or (*Venue'YY_MM*) depending on infer_mm.

Skips fenced ``` blocks.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

ARXIV_RE = re.compile(
    r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d+)(?:v\d+)?",
    re.IGNORECASE,
)
BIORXIV_DATE_RE = re.compile(r"/10\.1101/(\d{4})\.(\d{2})\.(\d{2})")
HEAD_RE = re.compile(r"^(-\s+\(\*)([^']+)(')(.+?)(\*\))(.*)$")


def infer_mm(chunk: str) -> str | None:
    """Two-digit month string, or None if unknown."""
    if m := ARXIV_RE.search(chunk):
        left = m.group(1).lower().split("v", 1)[0].split(".", 1)[0]
        yymm = int(left)
        return f"{yymm % 100:02d}"
    if m := BIORXIV_DATE_RE.search(chunk):
        return f"{int(m.group(2)):02d}"
    if "medrxiv.org" in chunk.lower() or "biorxiv.org" in chunk.lower():
        m = re.search(r"/(\d{4})\.(\d{2})\.(\d{2})(?:\.|v|\b)", chunk)
        if m:
            return f"{int(m.group(2)):02d}"
    return None


def has_numeric_month_tail(tail: str) -> bool:
    return bool(re.match(r"^\d{2}_\d{2}(?:\s|$)", tail.strip()))


def parse_yy_plain_tail(tail: str) -> tuple[str, str] | None:
    """Parse YY or YY + suffix (no underscore month)."""
    t = tail.strip()
    if has_numeric_month_tail(t):
        return None
    if re.match(r"^\d{2}_", t):
        return None
    if "'" in t:
        return None
    m = re.match(r"^(\d{2})(\s+.+)?$", t)
    if not m:
        return None
    return m.group(1), m.group(2) or ""


def parse_yy_question_tail(tail: str) -> tuple[str, str] | None:
    """Parse YY_?? optional suffix."""
    t = tail.strip()
    m = re.match(r"^(\d{2})_\?\?((?:\s+.+)?)$", t)
    if not m:
        return None
    return m.group(1), m.group(2) or ""


def transform_first_line(first: str, chunk: str) -> str | None:
    raw = first.rstrip("\n")
    m = HEAD_RE.match(raw)
    if not m:
        return None
    tail_raw = m.group(4).strip()

    if has_numeric_month_tail(tail_raw):
        return None

    yy: str
    suffix: str
    q = parse_yy_question_tail(tail_raw)
    if q:
        yy, suffix = q
    else:
        p = parse_yy_plain_tail(tail_raw)
        if not p:
            return None
        yy, suffix = p

    mm = infer_mm(chunk)
    if mm is None:
        new_tail = f"{yy}{suffix}"
    else:
        new_tail = f"{yy}_{mm}{suffix}"

    new_line = f"{m.group(1)}{m.group(2)}{m.group(3)}{new_tail}{m.group(5)}{m.group(6)}"
    if first.endswith("\n"):
        new_line += "\n"
    return new_line if new_line != first else None


def process_readme(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    changed = 0
    in_fence = False
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if (
            in_fence
            or not line.startswith("- ")
            or "(*" not in line
            or "'" not in line
        ):
            out.append(line)
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not lines[j].startswith("- "):
            j += 1
        chunk = "".join(lines[i:j])
        parts = chunk.splitlines(keepends=True)
        first = parts[0]
        rest = "".join(parts[1:])
        new_first = transform_first_line(first, chunk)
        if new_first is not None:
            changed += 1
            out.append(new_first)
            out.extend(rest.splitlines(keepends=True))
        else:
            out.extend(lines[i:j])
        i = j
    return "".join(out), changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--refine",
        action="store_true",
        help="Deprecated: same as default (re-normalize all bullets)",
    )
    args = ap.parse_args()
    text = README.read_text(encoding="utf-8")
    new_text, n = process_readme(text)
    print(f"Entries updated: {n}")
    if args.dry_run:
        return
    README.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
