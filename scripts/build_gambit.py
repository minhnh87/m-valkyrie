#!/usr/bin/env python3
"""Build the Sacred Gambit Q&A page data (Others tab) from its published sheet.

Unlike every other page, this one does NOT come from the main Omniheroes
workbook (data/sheets.json). It lives in a second, *publish-to-web only*
spreadsheet ("Random omni sheets", tab "gambit"), so there is no editable
spreadsheetId to hang off sheets.json — the published key + gid below are the
whole address. Export it as CSV via the /pub endpoint:

    https://docs.google.com/spreadsheets/d/e/<PUB_KEY>/pub?gid=<GID>&single=true&output=csv

Sheet layout — two plain-text columns, one quiz entry per row:

    A  (0)  Question
    B  (1)  Answer

Run:
    python3 scripts/build_gambit.py            # fetch fresh, then build
    python3 scripts/build_gambit.py --offline  # rebuild from data/raw/gambit.csv
Output:
    data/raw/gambit.csv  (cached export)
    data/gambit.json
"""
from __future__ import annotations

import csv
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "gambit.csv"
OUT = ROOT / "data" / "gambit.json"

PUB_KEY = (
    "2PACX-1vTuv97SEX07fKFPD_gRSWmAHckLNHPMPQpiFDM7UMZuGUacquVvvwwITjscC_"
    "kqey6olOgrZc9AI3w5"
)
GID = "1646213982"
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/e/{PUB_KEY}"
    f"/pub?gid={GID}&single=true&output=csv"
)
VIEW_URL = (
    f"https://docs.google.com/spreadsheets/d/e/{PUB_KEY}"
    f"/pubhtml?gid={GID}&single=true"
)

COL_QUESTION = 0
COL_ANSWER = 1


def collapse_ws(s: str) -> str:
    """Trim and collapse every run of whitespace (incl. newlines) to one space —
    questions/answers are single-line prose, and the search index wants them
    normalised."""
    return re.sub(r"\s+", " ", (s or "").strip())


def fetch_csv() -> None:
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(CSV_URL, timeout=30) as resp:
        body = resp.read()
    if b"," not in body.split(b"\n", 1)[0]:
        raise SystemExit(
            f"Export from {CSV_URL} doesn't look like CSV — the sheet may have "
            f"been unpublished or the gid changed."
        )
    RAW_CSV.write_bytes(body)
    print(f"Fetched gid={GID} → {RAW_CSV.relative_to(ROOT)}")


def build_items() -> list[dict]:
    with RAW_CSV.open(newline="") as f:
        rows = [list(r) for r in csv.reader(f)]
    width = COL_ANSWER + 1
    rows = [r + [""] * (width - len(r)) for r in rows]

    # Drop the header row ("Question,Answer") if present, then any row missing
    # either half — a Q with no A is useless for lookup.
    if rows and collapse_ws(rows[0][COL_QUESTION]).lower() == "question":
        rows = rows[1:]

    items: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        q = collapse_ws(row[COL_QUESTION])
        a = collapse_ws(row[COL_ANSWER])
        if not q or not a:
            continue
        # The sheet is community-maintained and occasionally repeats a question;
        # keep the first occurrence so the list stays 1 card per question.
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        items.append({"q": q, "a": a})
    return items


def main(argv: list[str]) -> int:
    offline = "--offline" in argv[1:]
    if offline:
        if not RAW_CSV.exists():
            raise SystemExit(
                f"--offline needs a cached {RAW_CSV.relative_to(ROOT)}; run "
                f"without the flag once."
            )
    else:
        fetch_csv()

    items = build_items()
    if not items:
        raise SystemExit("No Q&A rows found — check the CSV export.")

    payload = {
        "source": VIEW_URL,
        "title": "Sacred Gambit Q&A",
        "subtitle": "Tra nhanh đáp án câu hỏi Sacred Gambit — gõ vài chữ trong câu hỏi là ra.",
        "items": items,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(items)} Q&A pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
