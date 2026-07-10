#!/usr/bin/env python3
"""Build the Accessories Guide page data (Others tab) from the raw CSV.

The source tab (gid 1355345618, "Accessories Guide") ranks accessory *reroll*
stats. Each row's stat is shown as an **icon image floating over column A**, so
it does NOT survive CSV / gviz export — column A comes back empty. Everything
else is plain text:

    A  (0)  Stat icon           -> empty on export; supplied by STAT_NAMES below
    B  (1)  Priority advice
    G  (6)  Hero example / note  (header: "Hero Example - so that you get the idea")
    M  (12) Overall Order (IMO)  ("1st".."5th" | "As you wish" | "Generally not needed")

STAT_NAMES is therefore a *curated* list, in the sheet's top-to-bottom row
order, merged 1:1 with the exported rows. Names flagged `# verify` are best
guesses from the advice text (the icons are unreadable from export) — correct
them here and re-run; the structure never changes.

Run:
    python3 scripts/build_accessories.py
Output:
    data/accessories.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "accessories.csv"
SHEETS = ROOT / "data" / "sheets.json"
OUT = ROOT / "data" / "accessories.json"

# Column indices in the exported CSV (see module docstring).
COL_ADVICE = 1
COL_EXAMPLE = 6
COL_ORDER = 12

# Curated stat names, in the exact top-to-bottom row order of the sheet. The
# icons in column A don't export, so these are hand-supplied. Entries marked
# `# verify` are inferred from the advice text and may need a human check.
STAT_NAMES = [
    "Healing",                  # "sustain the most and the Doomsdayers"  -> 5th
    "Crit DMG",                 # "Epic ... 50% Crit DMG"                  -> not needed
    "Ultimate DMG Reduction",   # "lots of ULT spammers ... reducing those" -> 4th
    "DEF",                      # "Defence is completely useless"          -> as you wish
    "HP / Round",               # "HP/Round doesn't matter"                -> not needed
    "Skill DMG Reduction",      # "Reducing Skill Damage ... last resort"  -> as you wish
    "ATK",                      # "higher ATK = higher Heals/Shields"      -> 2nd
    "Accuracy",                 # verify: "heroes missing a lot"           -> not needed
    "Crit Rate",                # verify: "only good vs. Protector teams"  -> as you wish
    "Speed",                    # "supports ... buffer before your DPS"    -> 1st
    "HP",                       # verify: "useless ... get a Green ATK"     -> not needed
    "Dodge",                    # verify: "Dodge is highly relevant ..."   -> 3rd
]

ORDINAL_RE = re.compile(r"^(\d+)(st|nd|rd|th)$", re.IGNORECASE)


def collapse_ws(s: str) -> str:
    """Trim and collapse runs of spaces/tabs, but keep newlines (advice text
    is multi-line and we render it with white-space: pre-wrap)."""
    return re.sub(r"[ \t]+", " ", (s or "").strip())


def classify(order: str) -> tuple[str, int | None]:
    """Map the "Overall Order (IMO)" cell to (verdict, rank).

    "1st".."5th" -> ("priority", n) ; "As you wish" -> ("situational", None) ;
    "Generally not needed" (or anything skip-like) -> ("skip", None)."""
    o = (order or "").strip()
    m = ORDINAL_RE.match(o)
    if m:
        return "priority", int(m.group(1))
    low = o.lower()
    if "not needed" in low or "skip" in low:
        return "skip", None
    return "situational", None


def read_rows() -> list[list[str]]:
    with RAW_CSV.open(newline="") as f:
        rows = [list(r) for r in csv.reader(f)]
    # Pad every row to cover the columns we read.
    width = COL_ORDER + 1
    return [r + [""] * (width - len(r)) for r in rows]


def build_stats() -> list[dict]:
    rows = read_rows()
    # Keep only rows that actually carry advice; this drops the header row and
    # the blank merged-cell spacer rows between stat groups.
    data_rows = [r for r in rows if collapse_ws(r[COL_ADVICE])]

    if len(data_rows) != len(STAT_NAMES):
        raise SystemExit(
            f"Row/name mismatch: sheet has {len(data_rows)} stat rows but "
            f"STAT_NAMES has {len(STAT_NAMES)}. The sheet layout changed — "
            f"re-sync data/raw/accessories.csv and update STAT_NAMES."
        )

    stats: list[dict] = []
    for name, row in zip(STAT_NAMES, data_rows):
        order = collapse_ws(row[COL_ORDER])
        verdict, rank = classify(order)
        stats.append(
            {
                "name": name,
                "order": order,
                "rank": rank,
                "verdict": verdict,
                "advice": collapse_ws(row[COL_ADVICE]),
                "example": collapse_ws(row[COL_EXAMPLE]),
            }
        )
    return stats


def main() -> int:
    sheets = json.loads(SHEETS.read_text())
    tab = next(t for t in sheets["tabs"] if t["slug"] == "accessories")
    source = (
        f"https://docs.google.com/spreadsheets/d/{sheets['spreadsheetId']}"
        f"/edit?gid={tab['gid']}"
    )

    stats = build_stats()
    # Stable display order: priorities first (by rank), then situational, then
    # skip — while preserving the sheet's row order inside each bucket.
    bucket = {"priority": 0, "situational": 1, "skip": 2}
    stats_sorted = sorted(
        stats,
        key=lambda s: (bucket[s["verdict"]], s["rank"] if s["rank"] is not None else 99),
    )

    payload = {
        "source": source,
        "title": "Accessories Guide",
        "subtitle": "Ưu tiên reroll chỉ số phụ (accessory) — theo Overall Order của tác giả",
        "columns": {"advice": "Priority", "example": "Hero example / note", "order": "Overall Order (IMO)"},
        "stats": stats_sorted,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    n_pri = sum(1 for s in stats if s["verdict"] == "priority")
    print(
        f"Wrote {OUT.relative_to(ROOT)} with {len(stats)} stats "
        f"({n_pri} ranked priorities)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
