#!/usr/bin/env python3
"""Extract per-relic icons from the two Relics tabs of data/raw/omni.xlsx.

Both tabs pin one icon per relic in column B with the relic name in column C, so
we harvest both. The *Tier* List is the primary source (it lists every relic,
55); the rebuilt *Priority* List (43) only fills in names the Tier List lacks —
e.g. Crimson Chalice, which appears on the Priority tab alone. A name already
harvested is skipped outright, so the two tabs' differing crops of the same relic
never both land in assets/relics/.

Reuses the XLSX-walking helpers from extract_sheet_images.py (same scripts/ dir).

Output:
    assets/relics/<hash>.png    one file per unique relic icon
    data/relic_images.json      {"by_norm": {normalized name: "assets/relics/<hash>.png"},
                                 "names":   {raw tier name: "assets/relics/<hash>.png"}}

Run:
    python3 scripts/extract_relic_images.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_sheet_images as ex  # noqa: E402  (helpers: build_sheet_map, etc.)

ROOT = ex.ROOT
XLSX = ex.XLSX
ASSETS_DIR = ROOT / "assets" / "relics"
OUT_JSON = ROOT / "data" / "relic_images.json"
LOCAL_PREFIX = "assets/relics/"

# Harvest order matters: the first tab to claim a name wins.
SOURCE_SHEETS = ["Relics Tier List", "Relics Priority List"]
NAME_COL = "C"  # relic name column on both tabs (icons sit in column B)


def norm(s: str) -> str:
    """Normalize a relic name for cross-tab matching: fold apostrophe variants,
    drop parentheticals like '(Telescope)', lowercase, collapse to a-z0-9 words.
    Shared by build_relics_priority.py so the two sides agree on keys."""
    s = unicodedata.normalize("NFKC", s or "").replace("’", "'").replace("‘", "'")
    s = re.sub(r"\(.*?\)", "", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main() -> int:
    if not XLSX.exists():
        raise SystemExit(f"{XLSX.relative_to(ROOT)} not found — run ./scripts/fetch_xlsx.sh")

    by_norm: dict[str, str] = {}
    names: dict[str, str] = {}
    written: set[str] = set()

    per_sheet: dict[str, int] = {}
    with zipfile.ZipFile(XLSX) as z:
        sheet_map = ex.build_sheet_map(z)
        strings = ex.load_shared_strings(z)
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)

        for sheet_name in SOURCE_SHEETS:
            if sheet_name not in sheet_map:
                raise SystemExit(f"sheet {sheet_name!r} not found in workbook")
            sheet_path = sheet_map[sheet_name]
            cells = ex.load_sheet_cells(z, sheet_path, strings)
            drawing_path = ex.find_drawing_path(z, sheet_path)
            if not drawing_path or drawing_path not in z.namelist():
                raise SystemExit(f"no drawing/images found on {sheet_name!r}")
            embed_to_media = ex.drawing_image_map(z, drawing_path)
            anchors = ex.parse_drawing_anchors(z, drawing_path)

            taken = 0
            for row, _col, embed in anchors:
                name = " ".join((cells.get(f"{NAME_COL}{row + 1}") or "").split())
                media = embed_to_media.get(embed)
                if not name or not media or media not in z.namelist():
                    continue
                # First tab (then first anchor) to claim a name wins; a later tab's
                # crop of the same relic is dropped before it costs a PNG on disk.
                if norm(name) in by_norm:
                    continue
                data = z.read(media)
                h = ex.hash_bytes(data)
                if h not in written:
                    (ASSETS_DIR / f"{h}.png").write_bytes(data)
                    written.add(h)
                local = f"{LOCAL_PREFIX}{h}.png"
                names.setdefault(name, local)
                by_norm[norm(name)] = local
                taken += 1
            per_sheet[sheet_name] = taken

    payload = {
        "by_norm": dict(sorted(by_norm.items())),
        "names": dict(sorted(names.items())),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    breakdown = ", ".join(f"{n} from {s}" for s, n in per_sheet.items())
    print(
        f"Wrote {OUT_JSON.relative_to(ROOT)} ({len(names)} named relics, "
        f"{len(written)} unique icons → {LOCAL_PREFIX})\n  {breakdown}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
