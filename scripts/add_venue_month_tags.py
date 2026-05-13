#!/usr/bin/env python3
"""
Rewrite paper bullet heads from (*Venue'YY*) to (*Venue'YY_MM*) using:
- arXiv new-style id YYMM → MM
- bioRxiv /10.1101/YYYY.MM.DD → calendar month
- medRxiv path containing YYYY.MM.DD → calendar month
- otherwise MM = ??

Skips fenced ``` blocks and lines already in (*...'YY_MM*) form.
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


def infer_mm(chunk: str) -> str:
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
    return "??"


def already_has_month_slot(tail: str) -> bool:
    """True if tail is YY_MM... or YY_??... (already transformed)."""
    return bool(re.match(r"^\d{2}_", tail.strip()))


def parse_yy_tail(tail: str) -> tuple[str, str] | None:
    t = tail.strip()
    if already_has_month_slot(t):
        return None
    if "'" in t:
        return None
    m = re.match(r"^(\d{2})(\s+.+)?$", t)
    if not m:
        return None
    return m.group(1), m.group(2) or ""


def transform_first_line(first: str, chunk: str) -> str | None:
    raw = first.rstrip("\n")
    m = HEAD_RE.match(raw)
    if not m:
        return None
    tail = m.group(4)
    if already_has_month_slot(tail):
        return None
    parsed = parse_yy_tail(tail)
    if not parsed:
        return None
    yy, suffix = parsed
    mm = infer_mm(chunk)
    new_tail = f"{yy}_{mm}{suffix}"
    new_line = f"{m.group(1)}{m.group(2)}{m.group(3)}{new_tail}{m.group(5)}{m.group(6)}"
    if first.endswith("\n"):
        new_line += "\n"
    return new_line if new_line != first else None


def refine_first_line(first: str, chunk: str) -> str | None:
    raw = first.rstrip("\n")
    m = re.match(r"^(-\s+\(\*)([^']+)(')(\d{2})_\?\?(\*\))(.*)$", raw)
    if not m:
        return None
    yy = m.group(4)
    mm = infer_mm(chunk)
    if mm == "??":
        return None
    new_line = f"{m.group(1)}{m.group(2)}{m.group(3)}{yy}_{mm}{m.group(5)}{m.group(6)}"
    if first.endswith("\n"):
        new_line += "\n"
    return new_line if new_line != first else None


def process_refine_unknown(text: str) -> tuple[str, int]:
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
        if in_fence or not line.startswith("- ") or "(*" not in line or "'" not in line:
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
        new_first = refine_first_line(first, chunk)
        if new_first is not None:
            changed += 1
            out.append(new_first)
            out.extend(rest.splitlines(keepends=True))
        else:
            out.extend(lines[i:j])
        i = j
    return "".join(out), changed


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
        help="Replace only _?? month tags when infer_mm can resolve a numeric month",
    )
    args = ap.parse_args()
    text = README.read_text(encoding="utf-8")
    if args.refine:
        new_text, n = process_refine_unknown(text)
    else:
        new_text, n = process_readme(text)
    print(f"Entries updated: {n}")
    if args.dry_run:
        return
    README.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
