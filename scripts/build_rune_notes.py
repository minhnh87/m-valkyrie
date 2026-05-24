#!/usr/bin/env python3
"""Convert the raw Rune Notes CSV + images.json into clean JSON.

Run:
    python3 scripts/build_rune_notes.py

Output:
    data/rune-notes.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "rune-notes.csv"
IMAGES = ROOT / "data" / "images.json"
INLINE_IMAGES = ROOT / "data" / "inline_images.json"
OUT = ROOT / "data" / "rune-notes.json"
SHEETS = ROOT / "data" / "sheets.json"

# Browser-side asset path for hashes extracted from the workbook XLSX. Kept
# relative so the page works from file:// as well as a real web root.
LOCAL_AVATAR_PREFIX = "assets/runes/"

# Sheet layout (0-indexed array, 1-indexed col letter in comment):
#   A (0): empty
#   B (1): Avatar (inline image — not in CSV)
#   C (2): Name
#   D (3): Rune Type (primary set, e.g. "Dodge (Protection)")
#   E (4): Secondary Type
#   F (5): Reasoning
#   G (6): Substat 1 — Pre 11-stars
#   H (7): Substat 2 — 11-star +
#   I (8): Roll For Unique / Supreme  (TRUE / FALSE)
#   J (9): Impact  (e.g. "(Z) Insane")
#   K (10): If Needed Notes

# Rune Notes name → name to look up in data/images.json (which uses Fandom spelling).
NAME_TO_IMAGE: dict[str, str] = {
    "P. Arkdina": "Phantom Arkdina",
    "A. Bastet": "Abyssal Bastet",
    "A. Dorabella": "Arcane Dorabella",
    "S. Aiushtha": "Sovereign Aiushtha",
}

# Impact rating string → (letter code, display label, sort order).
IMPACT_TIERS = {
    "(Z) Insane": ("Z", "Insane", 0),
    "(Y) High": ("Y", "High", 1),
    "(X) Medium": ("X", "Medium", 2),
    "(W) Low": ("W", "Low", 3),
}


def clean(s: str) -> str:
    return (s or "").strip()


def collapse_ws(s: str) -> str:
    """Strip + collapse internal whitespace into single spaces (drops newlines)."""
    return re.sub(r"\s+", " ", (s or "").strip())


def normalize_multiline(s: str) -> str:
    """Trim, collapse runs of blank lines, strip per-line trailing spaces."""
    s = (s or "").strip()
    if not s:
        return ""
    lines = [ln.rstrip() for ln in s.splitlines()]
    out: list[str] = []
    blank = False
    for ln in lines:
        if not ln:
            if blank:
                continue
            blank = True
        else:
            blank = False
        out.append(ln)
    return "\n".join(out).strip()


def parse_bool(s: str) -> bool | None:
    v = clean(s).upper()
    if v == "TRUE":
        return True
    if v == "FALSE":
        return False
    return None


def parse_impact(raw: str) -> dict | None:
    v = clean(raw)
    if not v:
        return None
    if v in IMPACT_TIERS:
        code, label, order = IMPACT_TIERS[v]
        return {"code": code, "label": label, "order": order, "raw": v}
    # Fallback: treat as unknown tier at the end so we don't lose data.
    print(f"  warning: unknown impact rating: {v!r}")
    return {"code": "?", "label": v, "order": 99, "raw": v}


def resolve_image(name: str, fandom: dict[str, dict], hero_to_hash: dict[str, str]) -> str | None:
    """Prefer the mirrored Fandom avatar; fall back to the local hash-named PNG
    extract_sheet_images.py wrote into assets/runes/. We use the mirrored copy
    (img['local']) instead of img['url'] because the Fandom CDN refuses
    hotlinks from the deployed origin."""
    img = fandom.get(NAME_TO_IMAGE.get(name, name))
    if img and img.get("local"):
        return img["local"]
    h = hero_to_hash.get(name)
    if h:
        return f"{LOCAL_AVATAR_PREFIX}{h}.png"
    return None


def build_heroes(fandom: dict[str, dict], hero_to_hash: dict[str, str]) -> list[dict]:
    heroes: list[dict] = []
    with RAW_CSV.open(newline="") as f:
        rows = list(csv.reader(f))

    # Row 0 empty, row 1 header, body starts at row 2.
    for row in rows[2:]:
        row = list(row) + [""] * (11 - len(row))
        name = collapse_ws(row[2])
        if not name:
            continue

        heroes.append({
            "name": name,
            "rune_type": collapse_ws(row[3]),
            "secondary_type": collapse_ws(row[4]),
            "reasoning": normalize_multiline(row[5]),
            "substat_pre_11": collapse_ws(row[6]),
            "substat_post_11": collapse_ws(row[7]),
            "roll_unique": parse_bool(row[8]),
            "impact": parse_impact(row[9]),
            "if_needed": normalize_multiline(row[10]),
            "image": resolve_image(name, fandom, hero_to_hash),
        })
    return heroes


def main() -> int:
    images_data = json.loads(IMAGES.read_text()) if IMAGES.exists() else {"heroes": {}}
    inline_data = json.loads(INLINE_IMAGES.read_text()) if INLINE_IMAGES.exists() else {}
    hero_to_hash = inline_data.get("hero_to_hash", {})
    sheets = json.loads(SHEETS.read_text())
    tab = next(t for t in sheets["tabs"] if t["slug"] == "rune-notes")

    heroes = build_heroes(images_data.get("heroes", {}), hero_to_hash)
    missing_img = sum(1 for h in heroes if not h["image"])

    source = (
        f"https://docs.google.com/spreadsheets/d/{sheets['spreadsheetId']}"
        f"/edit?gid={tab['gid']}"
    )
    payload = {
        "source": source,
        "fetched_at": images_data.get("fetched_at"),
        "impact_tiers": [
            {"code": c, "label": l, "raw": raw}
            for raw, (c, l, _) in sorted(IMPACT_TIERS.items(), key=lambda kv: kv[1][2])
        ],
        "heroes": heroes,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(heroes)} heroes "
          f"({missing_img} without Fandom image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
