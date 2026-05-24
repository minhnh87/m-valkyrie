#!/usr/bin/env python3
"""Convert the raw Beginners Priority List CSV + images.json into clean JSON.

Run:
    python3 scripts/build_beginners_priority.py

Output:
    data/beginners-priority.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "beginners-priority.csv"
IMAGES = ROOT / "data" / "images.json"
OUT = ROOT / "data" / "beginners-priority.json"
SHEETS = ROOT / "data" / "sheets.json"

# Sheet layout (1-indexed col letter shown in comment, 0-indexed array below):
#   A (0): empty
#   B (1): Avatar (image embedded in sheet, we use our own cache)
#   C (2): Name — may have a leading tag like "Event Start\nTsuki"
#   D (3): Minimal ⭐
#   E (4): Summary
#   F-H (5-7): merged / empty
#   I (8): Source
#   J (9): Ideal ⭐ Before Moving To [Endgame Priority List]
#   K (10): Additional Notes

# tier-list name → name to look up in data/images.json
NAME_TO_IMAGE = {
    "Tsuki": "Tsukuyomi",
    "Jorm": "Jormungand",
    "Arc. Dorabella": "Arcane Dorabella",
    "S. Aiush": "Sovereign Aiushtha",
}


def clean(s: str) -> str:
    return (s or "").strip()


def collapse_ws(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "").strip())


def parse_name_cell(raw: str) -> tuple[str, str]:
    """Return (tag, name). Sheet uses 'Event Start\\nTsuki' to label starter alts."""
    raw = clean(raw)
    if "\n" in raw:
        head, _, tail = raw.partition("\n")
        head = clean(head)
        tail = clean(tail)
        if tail:
            return head, tail
    return "", raw


def parse_stars(raw: str) -> int | None:
    raw = clean(raw)
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def is_section_header(row: list[str]) -> bool:
    """A section divider row has text in the Name column but nothing else meaningful."""
    name = clean(row[2])
    others = [clean(row[i]) for i in (3, 4, 8, 9, 10)]
    return bool(name) and not any(others)


def build_sections(images: dict[str, dict]) -> list[dict]:
    rows: list[list[str]] = []
    with RAW_CSV.open(newline="") as f:
        for row in csv.reader(f):
            row = list(row) + [""] * (11 - len(row))
            rows.append(row)

    # Skip the empty row 0 and the header row 1.
    body = rows[2:]

    sections: list[dict] = [
        {
            "title": "Priority Heroes",
            "intro": "First complete the minimal PVE requirement before going to the [Endgame Priority List].",
            "heroes": [],
        }
    ]

    for row in body:
        if not any(clean(c) for c in row):
            continue
        if is_section_header(row):
            sections.append({"title": clean(row[2]), "intro": "", "heroes": []})
            continue

        tag, name = parse_name_cell(row[2])
        if not name:
            continue

        image_key = NAME_TO_IMAGE.get(name, name)
        img = images.get(image_key)

        sections[-1]["heroes"].append(
            {
                "rank": len(sections[-1]["heroes"]) + 1,
                "name": name,
                "tag": tag,
                "minimal_stars": parse_stars(row[3]),
                "summary": collapse_ws(row[4]),
                "source": clean(row[8]),
                "ideal_stars": parse_stars(row[9]),
                "notes": clean(row[10]),
                "image": img.get("local") if img else None,
            }
        )

    return [s for s in sections if s["heroes"]]


def main() -> int:
    images_data = json.loads(IMAGES.read_text()) if IMAGES.exists() else {"heroes": {}}
    sheets = json.loads(SHEETS.read_text())
    tab = next(t for t in sheets["tabs"] if t["slug"] == "beginners-priority")

    sections = build_sections(images_data.get("heroes", {}))
    total = sum(len(s["heroes"]) for s in sections)

    source = (
        f"https://docs.google.com/spreadsheets/d/{sheets['spreadsheetId']}"
        f"/edit?gid={tab['gid']}"
    )
    payload = {
        "source": source,
        "fetched_at": images_data.get("fetched_at"),
        "sections": sections,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)} with {total} heroes across {len(sections)} sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
