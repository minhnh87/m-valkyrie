#!/usr/bin/env python3
"""Build the Relics Priority List page data from the workbook XLSX.

The "Relics Priority List" tab was rebuilt (2026-06) into a relic-centric,
multi-column layout. Crucially, the star breakpoints in column F highlight the
"key" levels in **red**, and CSV export throws colour away — so this builder
reads the XLSX directly (the same workbook extract_relic_images.py harvests
icons from) instead of the CSV, and parses the rich-text runs to recover which
breakpoint numbers are red.

Sheet layout (1-indexed columns):
    A  spacer
    B  Avatar       (inline image — not cell text; icon resolved from Tier List)
    C  Name
    D  Priority Notes
    E  Source        (may be multi-line, e.g. "Relic Rebate\nShops")
    F  Star Level Breakpoints   (some digits coloured red)
    G  Focus (PvP or PvE)
    H  Spending Money           (Justified / Only if whale / blank)

Row kinds: header (C == "Name"), section (C empty, D = title, E = subtitle),
relic (C = name). A relic row may be otherwise blank (a WIP placeholder).

Run:
    python3 scripts/build_relics_priority.py

Output:
    data/relics-priority.json
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
OUT = ROOT / "data" / "relics-priority.json"
SHEETS = ROOT / "data" / "sheets.json"
RELIC_IMAGES = ROOT / "data" / "relic_images.json"

SHEET_NAME = "Relics Priority List"  # the rebuilt tab; the old one is "… (Outdated)"

# Priority-name → Relics-Tier-List icon-name overrides, for the few that still
# differ after norm() folds apostrophes/parentheticals. The rebuilt tab already
# uses canonical names, so this is intentionally empty — relics with no
# tier-list icon (e.g. the "Crimson Chalice" placeholder) fall back to initials.
ALIASES: dict[str, str] = {}


# ── XLSX rich-text helpers ─────────────────────────────────────────────────
def is_red(rgb: str | None) -> bool:
    """True for a reddish (A)RGB hex. The sheet marks key breakpoints in pure
    red, exported as 'FFFF0000'; we accept any strongly-red colour."""
    if not rgb:
        return False
    h = rgb[-6:]  # drop a leading FF alpha byte if present
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return False
    return r >= 0xC0 and g <= 0x60 and b <= 0x60


def _runs_from_element(el) -> list[tuple[str, str | None]]:
    """Parse <r> runs (with their font colour) under a sharedString <si> or an
    inline-string <is>. Falls back to the concatenated <t> text for plain runs."""
    runs: list[tuple[str, str | None]] = []
    rs = el.findall(ex._ns("r", "ss"))
    if rs:
        for r in rs:
            txt = "".join(t.text or "" for t in r.findall(ex._ns("t", "ss")))
            rgb = None
            rpr = r.find(ex._ns("rPr", "ss"))
            if rpr is not None:
                col = rpr.find(ex._ns("color", "ss"))
                if col is not None:
                    rgb = col.get("rgb")
            runs.append((txt, rgb))
    else:
        runs.append(("".join(t.text or "" for t in el.findall(ex._ns("t", "ss"))), None))
    return runs


def load_strings_rich(z: zipfile.ZipFile) -> list[list[tuple[str, str | None]]]:
    """Shared strings as runs: index → [(text, rgb_or_None), ...]."""
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ex.load_xml(z, "xl/sharedStrings.xml")
    return [_runs_from_element(si) for si in root.findall(ex._ns("si", "ss"))]


def _col_letters(ref: str) -> str:
    out = ""
    for ch in ref:
        if not ch.isalpha():
            break
        out += ch
    return out


def load_column_runs(z, sheet_path, strings_rich, want_col="F") -> dict[int, list]:
    """Return {row_1idx → runs} for every cell in `want_col`, resolving shared
    and inline rich strings so colour survives."""
    root = ex.load_xml(z, sheet_path)
    out: dict[int, list] = {}
    for c in root.iter(ex._ns("c", "ss")):
        ref = c.get("r")
        if not ref:
            continue
        letters = _col_letters(ref)
        if letters != want_col:
            continue
        row = int(ref[len(letters):])
        ty = c.get("t")
        v = c.find(ex._ns("v", "ss"))
        inline = c.find(ex._ns("is", "ss"))
        if ty == "s" and v is not None:
            idx = int(v.text)
            out[row] = strings_rich[idx] if 0 <= idx < len(strings_rich) else [("", None)]
        elif inline is not None:
            out[row] = _runs_from_element(inline)
        elif v is not None:
            out[row] = [(v.text or "", None)]
        else:
            out[row] = [("", None)]
    return out


def breakpoints_from_runs(runs) -> tuple[str, list[str]]:
    """(plain breakpoints text, [red numbers]) from coloured runs."""
    plain = "".join(tx for tx, _ in runs).strip()
    red: list[str] = []
    for tx, rgb in runs:
        if is_red(rgb):
            red.extend(re.findall(r"\d+", tx))
    seen: set[str] = set()
    red = [n for n in red if not (n in seen or seen.add(n))]  # de-dup, keep order
    return plain, red


# ── name → icon ────────────────────────────────────────────────────────────
def load_relic_images() -> dict[str, str]:
    if not RELIC_IMAGES.exists():
        return {}
    return json.loads(RELIC_IMAGES.read_text()).get("by_norm", {})


def resolve_image(name: str, by_norm: dict[str, str]) -> str | None:
    return by_norm.get(norm(ALIASES.get(name, name)))


# ── misc ───────────────────────────────────────────────────────────────────
def clean(s: str | None) -> str:
    return (s or "").strip()


def collapse_ws(s: str | None) -> str:
    """Collapse runs of spaces/tabs but keep newlines."""
    return re.sub(r"[ \t]+", " ", (s or "").strip())


def join_lines(s: str | None) -> str:
    """Multi-line cell (e.g. Source "Relic Rebate\nShops") → "Relic Rebate / Shops"."""
    return " / ".join(p.strip() for p in (s or "").split("\n") if p.strip())


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
        sheet_path = sm[SHEET_NAME]
        strings = ex.load_shared_strings(z)
        cells = ex.load_sheet_cells(z, sheet_path, strings)
        strings_rich = load_strings_rich(z)
        f_runs = load_column_runs(z, sheet_path, strings_rich, "F")

    def g(col: str, r: int) -> str:
        return clean(cells.get(f"{col}{r}"))

    maxr = max(int(re.match(r"[A-Z]+(\d+)", ref).group(1)) for ref in cells)

    sections: list[dict] = []
    no_icon: list[str] = []
    for r in range(1, maxr + 1):
        C, D, E, G, H = (g(col, r) for col in "CDEGH")
        runs = f_runs.get(r, [("", None)])
        f_text = "".join(tx for tx, _ in runs).strip()
        if not any((C, D, E, G, H, f_text)):
            continue
        if C == "Name":  # table header
            continue
        if not C and D:  # section divider: title in D, subtitle in E
            sections.append({"title": D, "subtitle": E, "relics": []})
            continue
        if not C:  # stray non-relic row
            continue

        bp, bp_red = breakpoints_from_runs(runs)
        img = resolve_image(C, by_norm)
        if not img:
            no_icon.append(C)
        relic = {
            "name": C,
            "notes": collapse_ws(D),
            "source": join_lines(E),
            "breakpoints": bp,
            "breakpoints_red": bp_red,
            "focus": G,
            "spending": H,
            "image": img,
        }
        if not sections:  # defensive: a relic before any section header
            sections.append({"title": "Relics", "subtitle": "", "relics": []})
        sections[-1]["relics"].append(relic)

    sections = [s for s in sections if s["relics"]]
    payload = {
        "source": tab_url(sheets, "relics-priority"),
        "sections": sections,
    }
    return payload, no_icon


def main() -> int:
    if not XLSX.exists():
        raise SystemExit(f"{XLSX.relative_to(ROOT)} not found — run ./scripts/fetch_xlsx.sh")
    sheets = json.loads(SHEETS.read_text())
    payload, no_icon = build(sheets)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    total = sum(len(s["relics"]) for s in payload["sections"])
    print(
        f"Wrote {OUT.relative_to(ROOT)}: {total} relics across "
        f"{len(payload['sections'])} sections"
    )
    if no_icon:
        print(f"  {len(no_icon)} without icon (initials fallback): {', '.join(no_icon)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
