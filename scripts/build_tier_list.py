#!/usr/bin/env python3
"""Convert the raw tier-list CSV + images.json into a clean JSON the page consumes.

Run:
    python3 scripts/build_tier_list.py

Output:
    data/tier-list.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "tier-list.csv"
IMAGES = ROOT / "data" / "images.json"
INLINE_IMAGES = ROOT / "data" / "inline_images.json"
OUT = ROOT / "data" / "tier-list.json"

# Browser-side asset path for hashes extracted from the workbook XLSX, used as a
# fallback for heroes Fandom has no avatar for (e.g. Victoria — wrong Fandom
# upload — and Asmodeus). Same source the rune pages use.
LOCAL_AVATAR_PREFIX = "assets/runes/"

# Column layout in the CSV (after the empty col A and empty col B):
#   C: Name
#   D: Seasonal PVP (WA + Foggy)
#   E: Rift Odyssey
#   F: Non-Seasonal PVP (Arena + Ygg)
#   G: PVE Missions + POP + LC
#   H–K: Forgotten Lands (Wailing Mines, Corrupt Spring, Crystal Woods, Crimson Town)
#   L–Q: Celestial Trials (Dungeon Maniac, Graveyard Witch, Bloodhell Queen,
#                          Northern Duke, Woodland Sage, Sacred Guardian)
#   R: Overall Rating
#   S: Additional Notes
COLUMNS = [
    {"key": "wa_foggy",     "label": "WA + Foggy",       "group": "Seasonal Content", "subgroup": "PVP"},
    {"key": "rift_odyssey", "label": "Rift Odyssey",     "group": "Seasonal Content", "subgroup": ""},
    {"key": "arena_ygg",    "label": "Arena + Ygg",      "group": "Non-Seasonal",     "subgroup": "PVP"},
    {"key": "missions",     "label": "Missions/POP/LC",  "group": "Non-Seasonal",     "subgroup": "PVE"},
    {"key": "wailing",      "label": "Wailing Mines",    "group": "Forgotten Lands",  "subgroup": ""},
    {"key": "corrupt",      "label": "Corrupt Spring",   "group": "Forgotten Lands",  "subgroup": ""},
    {"key": "crystal",      "label": "Crystal Woods",    "group": "Forgotten Lands",  "subgroup": ""},
    {"key": "crimson",      "label": "Crimson Town",     "group": "Forgotten Lands",  "subgroup": ""},
    {"key": "dungeon",      "label": "Dungeon Maniac",   "group": "Celestial Trials", "subgroup": ""},
    {"key": "graveyard",    "label": "Graveyard Witch",  "group": "Celestial Trials", "subgroup": ""},
    {"key": "bloodhell",    "label": "Bloodhell Queen",  "group": "Celestial Trials", "subgroup": ""},
    {"key": "northern",     "label": "Northern Duke",    "group": "Celestial Trials", "subgroup": ""},
    {"key": "woodland",     "label": "Woodland Sage",    "group": "Celestial Trials", "subgroup": ""},
    {"key": "sacred",       "label": "Sacred Guardian",  "group": "Celestial Trials", "subgroup": ""},
]

TIER_ORDER = ["SS", "S+", "S", "S-", "A+", "A", "A-", "B", "C", "D", ""]
TIER_RANK = {t: i for i, t in enumerate(TIER_ORDER)}


def overall_band(score: float | None) -> str:
    """Bucket the overall numeric rating into a tier badge for the page."""
    if score is None:
        return ""
    if score >= 10.0:
        return "SS"
    if score >= 9.0:
        return "S+"
    if score >= 8.0:
        return "S"
    if score >= 7.0:
        return "A+"
    if score >= 6.0:
        return "A"
    if score >= 5.0:
        return "B"
    if score >= 3.0:
        return "C"
    return "D"


def clean_cell(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def resolve_image(name: str, images: dict[str, dict], hero_to_hash: dict[str, str]) -> str | None:
    """Prefer the mirrored Fandom avatar; fall back to the local hash-named PNG
    extract_sheet_images.py wrote into assets/runes/ (the same portraits the
    rune sheets display), so Fandom-missing heroes still show a face."""
    img = images.get(name)
    if img and img.get("local"):
        return img["local"]
    h = hero_to_hash.get(name)
    if h:
        return f"{LOCAL_AVATAR_PREFIX}{h}.png"
    return None


def parse_csv_rows() -> list[dict]:
    """Return rows joined for multi-line cells (CSV reader already handles quoting)."""
    rows = []
    with RAW_CSV.open(newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            # pad to at least 19 columns
            row = list(row) + [""] * (19 - len(row))
            rows.append(row)
    return rows


def build_heroes(images: dict[str, dict], hero_to_hash: dict[str, str]) -> list[dict]:
    heroes: list[dict] = []
    rows = parse_csv_rows()
    for row in rows[3:]:  # skip 3 header rows
        name = clean_cell(row[2])
        if not name or name.lower() == "name":
            continue
        tiers = {}
        for i, col in enumerate(COLUMNS):
            tiers[col["key"]] = clean_cell(row[3 + i])

        # overall rating
        overall_raw = clean_cell(row[17])
        try:
            overall_val: float | None = float(overall_raw) if overall_raw else None
        except ValueError:
            overall_val = None

        notes = clean_cell(row[18])

        heroes.append(
            {
                "name": name,
                "tiers": tiers,
                "overall": overall_val,
                "overall_band": overall_band(overall_val),
                "notes": notes,
                "image": resolve_image(name, images, hero_to_hash),
            }
        )
    return heroes


def main() -> int:
    images_data = json.loads(IMAGES.read_text()) if IMAGES.exists() else {"heroes": {}}
    inline_data = json.loads(INLINE_IMAGES.read_text()) if INLINE_IMAGES.exists() else {}
    hero_to_hash = inline_data.get("hero_to_hash", {})
    heroes = build_heroes(images_data.get("heroes", {}), hero_to_hash)

    # Sort by overall rating desc (None goes last)
    heroes.sort(key=lambda h: (h["overall"] is None, -(h["overall"] or 0)))

    payload = {
        "source": "https://docs.google.com/spreadsheets/d/1S6HcGV7DM9DDR7932bEF1yOCEA8yeMhBn7bnokxG6cU/edit?gid=1975044546",
        "fetched_at": images_data.get("fetched_at"),
        "columns": COLUMNS,
        "tier_order": TIER_ORDER,
        "heroes": heroes,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(heroes)} heroes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
