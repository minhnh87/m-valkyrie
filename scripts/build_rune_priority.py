#!/usr/bin/env python3
"""Convert the raw Rune Priority List CSV + inline_images.json into clean JSON.

Heroes on this sheet are inline images (no text in CSV), so the data shape is
driven by extract_sheet_images.py: for every (row, col) anchor we know which
hero it shows AND the cell's border color (which is what conveys priority in
the source spreadsheet — red = 4 Legendary, orange = 2 Epic 2 Leg, yellow = 4
Epic, gray = skip). We pair those anchors with tier labels + notes from the CSV
and bucket them by border color.

Run:
    python3 scripts/build_rune_priority.py

Output:
    data/rune-priority.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "rune-priority.csv"
IMAGES = ROOT / "data" / "images.json"
INLINE_IMAGES = ROOT / "data" / "inline_images.json"
OUT = ROOT / "data" / "rune-priority.json"
SHEETS = ROOT / "data" / "sheets.json"

LOCAL_AVATAR_PREFIX = "assets/runes/"

# Priority buckets — keyed by cell border color in the source spreadsheet.
# The CSV column layout is decorative; priority is the border around each
# image. Listed from highest priority (red) to lowest (skip).
SECTIONS = [
    {"key": "red",    "label": "Red Border · 4 Legendary",      "rarity": "legendary"},
    {"key": "orange", "label": "Orange Border · 2 Epic 2 Leg.", "rarity": "mixed"},
    {"key": "yellow", "label": "Yellow Border · 4 Epic",        "rarity": "epic"},
    {"key": "skip",   "label": "No Priority · Skip",            "rarity": "skip"},
]

# Map dominant cell-border RGB hex (uppercase, alpha stripped) → bucket key.
# Source spreadsheet uses these exact colors; anything else falls through to
# `unbucketed` so it shows up in the page rather than silently disappearing.
BORDER_TO_KEY: dict[str, str] = {
    "FF0000": "red",
    "FF9900": "orange",
    "FFFF00": "yellow",
    "EFEFEF": "skip",
}

NOTES_COL = 34

# Rune Priority hero name (from rune-notes hash map) → Fandom images.json key.
# Mirrors build_rune_notes.NAME_TO_IMAGE; keep them aligned.
NAME_TO_IMAGE: dict[str, str] = {
    "P. Arkdina": "Phantom Arkdina",
    "A. Bastet": "Abyssal Bastet",
    "A. Dorabella": "Arcane Dorabella",
    "S. Aiushtha": "Sovereign Aiushtha",
}


def clean(s: str) -> str:
    return (s or "").strip()


def collapse_inline(s: str) -> str:
    """Collapse internal whitespace, used for tier names that have stray newlines."""
    return re.sub(r"\s+", " ", (s or "").strip())


def normalize_multiline(s: str) -> str:
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


def section_for_border(border: str | None) -> str | None:
    if not border:
        return None
    return BORDER_TO_KEY.get(border.upper())


def resolve_image(name: str | None, fandom: dict[str, dict], h: str) -> str:
    """Same precedence as build_rune_notes: mirrored Fandom avatar → local hash
    PNG. We use img['local'] (downloaded by scripts/download_images.py) rather
    than img['url'] because the Fandom CDN blocks hotlinks from the deployed
    origin."""
    if name:
        key = NAME_TO_IMAGE.get(name, name)
        img = fandom.get(key)
        if img and img.get("local"):
            return img["local"]
    return f"{LOCAL_AVATAR_PREFIX}{h}.png"


def load_tiers_from_csv() -> dict[int, dict]:
    """Return {0-indexed row → {label, notes}} for rows that name a tier."""
    out: dict[int, dict] = {}
    with RAW_CSV.open(newline="") as f:
        for idx, row in enumerate(csv.reader(f)):
            row = list(row) + [""] * (NOTES_COL + 1 - len(row))
            label = collapse_inline(row[0])
            if not label or label == "Tier":  # header row
                continue
            # Find the notes cell — usually near col NOTES_COL, sometimes shifted
            # a few columns left when the spreadsheet author merged differently.
            notes = ""
            for col in range(NOTES_COL, 19, -1):  # search 20..NOTES_COL backwards
                if col < len(row) and row[col].strip():
                    notes = row[col]
                    break
            out[idx] = {
                "label": label,
                "notes": normalize_multiline(notes),
            }
    return out


def build_payload() -> dict:
    fandom = json.loads(IMAGES.read_text()).get("heroes", {}) if IMAGES.exists() else {}
    inline = json.loads(INLINE_IMAGES.read_text())
    sheets = json.loads(SHEETS.read_text())
    tab = next(t for t in sheets["tabs"] if t["slug"] == "rune-priority")

    anchors = inline.get("sheets", {}).get("rune-priority", [])
    tiers_by_row = load_tiers_from_csv()

    # Group anchors by row; sort by col so heroes appear left-to-right.
    by_row: dict[int, list[dict]] = {}
    for a in anchors:
        by_row.setdefault(a["row"], []).append(a)
    for entries in by_row.values():
        entries.sort(key=lambda e: e["col"])

    tiers_out: list[dict] = []
    unknown = 0
    for row in sorted(set(tiers_by_row) | set(by_row)):
        tier_meta = tiers_by_row.get(row, {"label": f"(unnamed row {row})", "notes": ""})
        hero_anchors = by_row.get(row, [])
        if not hero_anchors and not tier_meta["notes"] and tier_meta["label"].startswith("(unnamed"):
            continue

        heroes: list[dict] = []
        for a in hero_anchors:
            border_hex = (a.get("border") or "").upper() or None
            entry = {
                "name": a.get("hero") or None,
                "col": a["col"],
                "border": border_hex,
                "priority": section_for_border(a.get("border")),
                "image": resolve_image(a.get("hero"), fandom, a["hash"]),
            }
            if not entry["name"]:
                unknown += 1
            heroes.append(entry)

        # hero_anchors already sorted by col upstream, but be explicit.
        heroes.sort(key=lambda h: h["col"])
        tiers_out.append({
            "row": row,
            "label": tier_meta["label"],
            "notes": tier_meta["notes"],
            "heroes": heroes,
        })

    source = (
        f"https://docs.google.com/spreadsheets/d/{sheets['spreadsheetId']}"
        f"/edit?gid={tab['gid']}"
    )
    return {
        "source": source,
        "fetched_at": json.loads(IMAGES.read_text()).get("fetched_at") if IMAGES.exists() else None,
        "priorities": SECTIONS,
        "tiers": tiers_out,
        "stats": {
            "tier_count": len(tiers_out),
            "hero_anchor_count": sum(len(t["heroes"]) for t in tiers_out),
            "unknown_anchor_count": unknown,
        },
    }


def main() -> int:
    payload = build_payload()
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    s = payload["stats"]
    print(f"Wrote {OUT.relative_to(ROOT)}: "
          f"{s['tier_count']} tiers, {s['hero_anchor_count']} hero anchors "
          f"({s['unknown_anchor_count']} unidentified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
