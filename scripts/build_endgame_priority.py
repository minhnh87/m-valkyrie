#!/usr/bin/env python3
"""Convert the raw Endgame Priority List CSV + images.json into clean JSON.

Run:
    python3 scripts/build_endgame_priority.py

Output:
    data/endgame-priority.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "endgame-priority.csv"
IMAGES = ROOT / "data" / "images.json"
INLINE_IMAGES = ROOT / "data" / "inline_images.json"
OUT = ROOT / "data" / "endgame-priority.json"
SHEETS = ROOT / "data" / "sheets.json"

# Local hash-named portraits from the workbook XLSX, used when Fandom has no
# avatar for a hero (e.g. Victoria/Asmodeus). Same source the rune pages use.
LOCAL_AVATAR_PREFIX = "assets/runes/"

# Sheet layout (1-indexed col letter shown in comment, 0-indexed array below):
#   A (0): empty
#   B (1): Avatar (image embedded in sheet, we use our own cache)
#   C (2): Name
#   D (3): Important Ordering — tier label (Top Priority / High / Middle - High / Middle / Low)
#   E (4): Summary
#   F (5): Source
#   G (6): Fair ⭐ level (free text like "12 > 10 > 9 > 8")

# Display order for priority tiers — drives section ordering in the UI.
TIER_ORDER = ["Top Priority", "High", "Middle - High", "Middle", "Low"]

# endgame name → name to look up in data/images.json (which uses tier-list spelling).
NAME_TO_IMAGE: dict[str, str] = {}


def clean(s: str) -> str:
    return (s or "").strip()


def collapse_ws(s: str) -> str:
    return re.sub(r"[ \t]+", " ", (s or "").strip())


def normalize_name(raw: str) -> str:
    """Strip trailing newlines/whitespace; collapse internal whitespace."""
    return re.sub(r"\s+", " ", (raw or "").strip())


def normalize_tier(raw: str) -> str:
    """Collapse whitespace around the dash in 'Middle - High' etc."""
    return re.sub(r"\s+", " ", (raw or "").strip())


def resolve_image(name: str, images: dict[str, dict], hero_to_hash: dict[str, str]) -> str | None:
    """Prefer the mirrored Fandom avatar; fall back to the local hash-named PNG
    in assets/runes/ so Fandom-missing heroes still show a face."""
    img = images.get(NAME_TO_IMAGE.get(name, name))
    if img and img.get("local"):
        return img["local"]
    h = hero_to_hash.get(name)
    if h:
        return f"{LOCAL_AVATAR_PREFIX}{h}.png"
    return None


def build_sections(images: dict[str, dict], hero_to_hash: dict[str, str]) -> list[dict]:
    rows: list[list[str]] = []
    with RAW_CSV.open(newline="") as f:
        for row in csv.reader(f):
            row = list(row) + [""] * (7 - len(row))
            rows.append(row)

    # Skip empty row 0 and header row 1.
    body = rows[2:]

    by_tier: dict[str, list[dict]] = {t: [] for t in TIER_ORDER}
    unknown_tiers: list[str] = []

    for row in body:
        if not any(clean(c) for c in row):
            continue

        name = normalize_name(row[2])
        if not name:
            continue

        tier = normalize_tier(row[3]) or "Low"
        if tier not in by_tier:
            unknown_tiers.append(tier)
            by_tier[tier] = []

        by_tier[tier].append(
            {
                "rank": len(by_tier[tier]) + 1,
                "name": name,
                "summary": collapse_ws(row[4]),
                "source": clean(row[5]),
                "fair_stars": collapse_ws(row[6]),
                "image": resolve_image(name, images, hero_to_hash),
            }
        )

    if unknown_tiers:
        print(f"  warning: unrecognised tiers (appended to end): {set(unknown_tiers)}")

    # Preserve TIER_ORDER first, then any unknowns at the end.
    ordered_tiers = TIER_ORDER + [t for t in by_tier if t not in TIER_ORDER]
    sections = []
    for tier in ordered_tiers:
        heroes = by_tier.get(tier, [])
        if not heroes:
            continue
        sections.append({"title": tier, "heroes": heroes})
    return sections


def main() -> int:
    images_data = json.loads(IMAGES.read_text()) if IMAGES.exists() else {"heroes": {}}
    inline_data = json.loads(INLINE_IMAGES.read_text()) if INLINE_IMAGES.exists() else {}
    hero_to_hash = inline_data.get("hero_to_hash", {})
    sheets = json.loads(SHEETS.read_text())
    tab = next(t for t in sheets["tabs"] if t["slug"] == "endgame-priority")

    sections = build_sections(images_data.get("heroes", {}), hero_to_hash)
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
    print(f"Wrote {OUT.relative_to(ROOT)} with {total} heroes across {len(sections)} tiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
