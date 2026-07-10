#!/usr/bin/env python3
"""Build the Relics *Tier* List page data from the workbook XLSX.

Sibling of build_relics_priority.py. Where the *Priority* tab is relic-centric
with red-highlighted star breakpoints (needing XLSX rich-text parsing), the
*Tier* List tab is a flat ranking: one row per relic with a letter grade for
each game mode plus an overall numeric score. Grades are plain text (the colour
in the sheet is decorative — the letter carries the meaning), so we read the
sheet cells directly; no rich-text run parsing is required.

Sheet layout (1-indexed columns), header on row 2 (C == "Name"):
    B  Avatar   (inline image — resolved from the icon extract, not cell text)
    C  Name
    D  Missions            \\
    E  Lost City            |
    F  Rift Odyssey         |  per-mode letter grade (S+ … D)
    G  Forgotten Lands      |
    H  Celestial Trials     |
    I  PvP                 /
    J  Overall Ranking     (numeric, sheet is pre-sorted by this descending)
    K  Note
    L  Minimal Star Level
    M  Ideal Star Level

Icons come from data/relic_images.json (harvested from this very tab by
extract_relic_images.py), matched via the shared norm().

Run:
    python3 scripts/build_relics_tier.py

Output:
    data/relics-tier.json
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_sheet_images as ex  # noqa: E402  (XLSX-walking helpers)
from extract_relic_images import norm  # noqa: E402  (shared name normalization)

ROOT = ex.ROOT
XLSX = ex.XLSX
OUT = ROOT / "data" / "relics-tier.json"
SHEETS = ROOT / "data" / "sheets.json"
RELIC_IMAGES = ROOT / "data" / "relic_images.json"

SHEET_NAME = "Relics Tier List"

# Column letter → (output key, full label, short header). Order defines the
# grade columns rendered in the lite table + detail card.
GRADE_COLS = [
    ("D", "missions", "Missions", "Msn"),
    ("E", "lost_city", "Lost City", "LC"),
    ("F", "rift", "Rift Odyssey", "RO"),
    ("G", "forgotten", "Forgotten Lands", "FL"),
    ("H", "celestial", "Celestial Trials", "CT"),
    ("I", "pvp", "PvP", "PvP"),
]

# Priority-name → tier-list icon-name overrides. Empty: this tab *is* the icon
# source, so every name already matches after norm().
ALIASES: dict[str, str] = {}


def load_relic_images() -> dict[str, str]:
    if not RELIC_IMAGES.exists():
        return {}
    return json.loads(RELIC_IMAGES.read_text()).get("by_norm", {})


def resolve_image(name: str, by_norm: dict[str, str]) -> str | None:
    return by_norm.get(norm(ALIASES.get(name, name)))


def collapse_ws(s: str | None) -> str:
    """Collapse spaces/tabs, trim; used for names + short grade cells."""
    return re.sub(r"[ \t]+", " ", (s or "").strip())


def clean_note(s: str | None) -> str:
    """Trim outer whitespace but keep internal newlines (rendered pre-wrap).
    A lone '.' placeholder (used in the sheet as an empty marker) → ''."""
    t = (s or "").strip()
    return "" if t == "." else t


def tab_url(sheets: dict, slug: str) -> str | None:
    m = [t for t in sheets["tabs"] if t["slug"] == slug]
    if not m:
        return None
    return (
        f"https://docs.google.com/spreadsheets/d/{sheets['spreadsheetId']}"
        f"/edit?gid={m[0]['gid']}"
    )


def build(sheets: dict) -> tuple[dict, list[str]]:
    by_norm = load_relic_images()
    with zipfile.ZipFile(XLSX) as z:
        sm = ex.build_sheet_map(z)
        if SHEET_NAME not in sm:
            raise SystemExit(f"sheet {SHEET_NAME!r} not found in workbook")
        strings = ex.load_shared_strings(z)
        cells = ex.load_sheet_cells(z, sm[SHEET_NAME], strings)

    def g(col: str, r: int) -> str:
        return (cells.get(f"{col}{r}") or "").strip()

    maxr = max(int(re.match(r"[A-Z]+(\d+)", ref).group(1)) for ref in cells)

    relics: list[dict] = []
    no_icon: list[str] = []
    for r in range(1, maxr + 1):
        name = collapse_ws(cells.get(f"C{r}"))
        if not name or name == "Name":  # blank row or the table header
            continue
        grades = {key: collapse_ws(cells.get(f"{col}{r}")) for col, key, *_ in GRADE_COLS}
        img = resolve_image(name, by_norm)
        if not img:
            no_icon.append(name)
        relics.append({
            "name": name,
            "image": img,
            "overall": g("J", r),
            "grades": grades,
            "min_star": g("L", r),
            "ideal_star": g("M", r),
            "note": clean_note(cells.get(f"K{r}")),
        })

    payload = {
        "source": tab_url(sheets, "relics-tier"),
        "columns": [
            {"key": key, "label": label, "short": short}
            for _col, key, label, short in GRADE_COLS
        ],
        "relics": relics,
    }
    return payload, no_icon


def main() -> int:
    if not XLSX.exists():
        raise SystemExit(f"{XLSX.relative_to(ROOT)} not found — run ./scripts/fetch_xlsx.sh")
    sheets = json.loads(SHEETS.read_text())
    payload, no_icon = build(sheets)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(payload['relics'])} relics")
    if no_icon:
        print(f"  {len(no_icon)} without icon (initials fallback): {', '.join(no_icon)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
