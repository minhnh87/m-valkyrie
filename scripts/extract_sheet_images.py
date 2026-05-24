#!/usr/bin/env python3
"""Extract inline images from data/raw/omni.xlsx, identify which hero each image
shows, and save metadata for downstream page builders.

Inline images don't survive Google Sheets' CSV export, but XLSX preserves them
as drawing anchors that pin each image to a (row, col) cell. We:

  1. Walk the XLSX zip to discover sheet → drawing → image media mappings.
  2. For "source" sheets that have a Name column adjacent to each avatar
     (rune-notes, beginners-priority, endgame-priority), pair each image hash
     with the neighbouring text → build a global `hash → hero name` map.
  3. For each TARGET sheet (currently rune-priority), record every anchor's
     (row, col, hash, hero?) and copy the unique image bytes to
     `assets/runes/<hash>.png` so the page can `<img src>` them at runtime.

Output:
    assets/runes/<hash>.png    (one file per unique image referenced by targets)
    data/inline_images.json    {sheets: {slug: [{row, col, hash, hero?}]}, hash_to_hero: {...}}

Run:
    python3 scripts/extract_sheet_images.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "data" / "raw" / "omni.xlsx"
ASSETS_DIR = ROOT / "assets" / "runes"
OUT_JSON = ROOT / "data" / "inline_images.json"
SHEETS_JSON = ROOT / "data" / "sheets.json"

NS = {
    "ss": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    "dr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "dm": "http://schemas.openxmlformats.org/drawingml/2006/main",
}

# Sheet slugs whose Name column is text in the XLSX and whose Avatar column is
# inline images. Used to build the hash → hero map. Order matters — entries
# earlier in the list win when a hash appears in multiple sheets.
SOURCE_SHEETS = [
    # (slug, name_column_letter)
    ("rune-notes", "C"),
    ("endgame-priority", "C"),
    ("beginners-priority", "C"),
]

# Sheets we actually want anchor coordinates for (consumed by page builders).
TARGET_SHEETS = ["rune-priority"]


def _ns(tag: str, ns_key: str) -> str:
    return f"{{{NS[ns_key]}}}{tag}"


def load_xml(z: zipfile.ZipFile, name: str) -> ET.Element:
    with z.open(name) as f:
        return ET.parse(f).getroot()


def build_sheet_map(z: zipfile.ZipFile) -> dict[str, str]:
    """Return sheet display-name → worksheet xml path (e.g. 'xl/worksheets/sheet6.xml')."""
    wb = load_xml(z, "xl/workbook.xml")
    rels = load_xml(z, "xl/_rels/workbook.xml.rels")
    rid_to_target = {
        r.get("Id"): "xl/" + r.get("Target").lstrip("/")
        for r in rels
        if r.get("Type", "").endswith("/worksheet")
    }
    out: dict[str, str] = {}
    for s in wb.findall(f".//{_ns('sheet', 'ss')}"):
        name = s.get("name")
        rid = s.get(_ns("id", "r"))
        if rid in rid_to_target:
            out[name] = rid_to_target[rid]
    return out


def sheet_rels_path(sheet_path: str) -> str:
    """xl/worksheets/sheet6.xml → xl/worksheets/_rels/sheet6.xml.rels"""
    p = Path(sheet_path)
    return str(p.parent / "_rels" / (p.name + ".rels"))


def find_drawing_path(z: zipfile.ZipFile, sheet_path: str) -> str | None:
    rels_path = sheet_rels_path(sheet_path)
    if rels_path not in z.namelist():
        return None
    rels = load_xml(z, rels_path)
    for r in rels:
        if r.get("Type", "").endswith("/drawing"):
            target = r.get("Target")
            if target.startswith("/"):
                return target.lstrip("/")
            base = str(Path(sheet_path).parent).replace("\\", "/")
            return normalize_zip_path(f"{base}/{target}")
    return None


def normalize_zip_path(p: str) -> str:
    """Resolve `..` segments while keeping zip-style forward slashes."""
    parts: list[str] = []
    for chunk in p.split("/"):
        if chunk == ".." and parts:
            parts.pop()
        elif chunk and chunk != ".":
            parts.append(chunk)
    return "/".join(parts)


def drawing_image_map(z: zipfile.ZipFile, drawing_path: str) -> dict[str, str]:
    """rId in the drawing rels → media path (e.g. 'xl/media/image35.png')."""
    p = Path(drawing_path)
    rels_path = str(p.parent / "_rels" / (p.name + ".rels"))
    if rels_path not in z.namelist():
        return {}
    rels = load_xml(z, rels_path)
    out: dict[str, str] = {}
    for r in rels:
        if not r.get("Type", "").endswith("/image"):
            continue
        target = r.get("Target")
        base = Path(drawing_path).parent
        full = normalize_zip_path(str(base / target).replace("\\", "/"))
        out[r.get("Id")] = full
    return out


def load_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = load_xml(z, "xl/sharedStrings.xml")
    out: list[str] = []
    for si in root.findall(_ns("si", "ss")):
        out.append("".join(t.text or "" for t in si.iter(_ns("t", "ss"))))
    return out


def load_sheet_cells(z: zipfile.ZipFile, sheet_path: str, strings: list[str]) -> dict[str, str]:
    """Return {cell-ref like 'C3' → text value} for non-empty cells."""
    root = load_xml(z, sheet_path)
    cells: dict[str, str] = {}
    for row in root.findall(f".//{_ns('row', 'ss')}"):
        for c in row.findall(_ns("c", "ss")):
            ref = c.get("r")
            t = c.get("t")
            v = c.find(_ns("v", "ss"))
            # Inline strings use <is><t>...</t></is> instead of a shared-string index.
            inline = c.find(_ns("is", "ss"))
            if v is not None:
                if t == "s":
                    idx = int(v.text)
                    if 0 <= idx < len(strings):
                        cells[ref] = strings[idx]
                else:
                    cells[ref] = v.text
            elif inline is not None:
                cells[ref] = "".join(t.text or "" for t in inline.iter(_ns("t", "ss")))
    return cells


def parse_drawing_anchors(z: zipfile.ZipFile, drawing_path: str) -> list[tuple[int, int, str]]:
    """Return list of (row, col, embed_rId) for every image anchor (0-indexed cells)."""
    root = load_xml(z, drawing_path)
    out: list[tuple[int, int, str]] = []
    for anchor in root:
        fr = anchor.find(_ns("from", "dr"))
        if fr is None:
            continue
        col_el = fr.find(_ns("col", "dr"))
        row_el = fr.find(_ns("row", "dr"))
        if col_el is None or row_el is None:
            continue
        blip = anchor.find(f".//{_ns('blip', 'dm')}")
        if blip is None:
            continue
        embed = blip.get(_ns("embed", "r"))
        if not embed:
            continue
        out.append((int(row_el.text), int(col_el.text), embed))
    return out


def _dominant_border_color(border_el: ET.Element) -> str | None:
    """Pick the most common RGB color across a border's 4 sides.

    Returns 6-digit uppercase hex like 'FF0000', or None if the border has no
    colored sides. We pick by frequency because corner cases (e.g. only one
    side colored) shouldn't confuse the priority bucket.
    """
    counts: dict[str, int] = {}
    for side in border_el:
        c = side.find(_ns("color", "ss"))
        if c is not None and c.get("rgb"):
            rgb = c.get("rgb")
            # openpyxl-style ARGB → strip leading FF alpha
            if len(rgb) == 8:
                rgb = rgb[2:]
            counts[rgb.upper()] = counts.get(rgb.upper(), 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def load_style_borders(z: zipfile.ZipFile) -> dict[int, str]:
    """Build {cellXf-index → dominant border RGB hex} for the workbook.

    Empty cells / borders with no color are omitted from the map.
    """
    if "xl/styles.xml" not in z.namelist():
        return {}
    root = load_xml(z, "xl/styles.xml")
    borders_el = root.find(_ns("borders", "ss"))
    if borders_el is None:
        return {}
    border_colors = [_dominant_border_color(b) for b in borders_el]
    cell_xfs = root.find(_ns("cellXfs", "ss"))
    if cell_xfs is None:
        return {}
    out: dict[int, str] = {}
    for idx, xf in enumerate(cell_xfs):
        bid = xf.get("borderId")
        if bid is None:
            continue
        bi = int(bid)
        if 0 <= bi < len(border_colors) and border_colors[bi]:
            out[idx] = border_colors[bi]
    return out


def load_sheet_cell_styles(z: zipfile.ZipFile, sheet_path: str) -> dict[tuple[int, int], int]:
    """Return {(row_1idx, col_0idx) → cellXf-index} for cells that declare a style."""
    root = load_xml(z, sheet_path)
    out: dict[tuple[int, int], int] = {}
    for c in root.iter(_ns("c", "ss")):
        ref = c.get("r")
        style = c.get("s")
        if not ref or style is None:
            continue
        letters = ""
        for ch in ref:
            if ch.isalpha():
                letters += ch
            else:
                break
        if not letters or len(letters) == len(ref):
            continue
        col = 0
        for ch in letters:
            col = col * 26 + (ord(ch) - ord("A") + 1)
        col -= 1
        try:
            row = int(ref[len(letters):])
        except ValueError:
            continue
        out[(row, col)] = int(style)
    return out


def hash_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:12]


def main() -> int:
    if not XLSX.exists():
        raise SystemExit(f"{XLSX.relative_to(ROOT)} not found — run ./scripts/fetch_xlsx.sh")

    sheets_meta = json.loads(SHEETS_JSON.read_text())
    name_to_slug = {t["name"]: t["slug"] for t in sheets_meta["tabs"]}
    slug_to_name = {v: k for k, v in name_to_slug.items()}

    with zipfile.ZipFile(XLSX) as z:
        sheet_map = build_sheet_map(z)  # name → sheet xml path
        strings = load_shared_strings(z)
        style_borders = load_style_borders(z)  # cellXf-index → border RGB hex

        # Per-slug cache so we don't reparse sheets we touch from both source + target lists.
        sheet_cells: dict[str, dict[str, str]] = {}
        sheet_styles: dict[str, dict[tuple[int, int], int]] = {}
        sheet_drawings: dict[str, list[tuple[int, int, str, bytes, str]]] = {}
        # entry: (row, col, embed_rId, image_bytes, image_zip_path)

        def get_cells(slug: str) -> dict[str, str]:
            if slug not in sheet_cells:
                name = slug_to_name.get(slug)
                if name is None or name not in sheet_map:
                    sheet_cells[slug] = {}
                else:
                    sheet_cells[slug] = load_sheet_cells(z, sheet_map[name], strings)
            return sheet_cells[slug]

        def get_cell_styles(slug: str) -> dict[tuple[int, int], int]:
            if slug not in sheet_styles:
                name = slug_to_name.get(slug)
                if name is None or name not in sheet_map:
                    sheet_styles[slug] = {}
                else:
                    sheet_styles[slug] = load_sheet_cell_styles(z, sheet_map[name])
            return sheet_styles[slug]

        def get_drawing(slug: str) -> list[tuple[int, int, str, bytes, str]]:
            if slug in sheet_drawings:
                return sheet_drawings[slug]
            name = slug_to_name.get(slug)
            if name is None or name not in sheet_map:
                sheet_drawings[slug] = []
                return []
            sheet_path = sheet_map[name]
            drawing_path = find_drawing_path(z, sheet_path)
            if not drawing_path or drawing_path not in z.namelist():
                sheet_drawings[slug] = []
                return []
            embed_to_media = drawing_image_map(z, drawing_path)
            anchors = parse_drawing_anchors(z, drawing_path)
            resolved: list[tuple[int, int, str, bytes, str]] = []
            for row, col, embed in anchors:
                media_path = embed_to_media.get(embed)
                if not media_path or media_path not in z.namelist():
                    continue
                with z.open(media_path) as f:
                    data = f.read()
                resolved.append((row, col, embed, data, media_path))
            sheet_drawings[slug] = resolved
            return resolved

        # --- pass 1: build hash → hero map from source sheets ---
        # Also save these images: rune-notes builder uses them as a local
        # fallback for heroes that Fandom doesn't have.
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        seen_hashes_written: set[str] = set()

        def save_image(h: str, data: bytes) -> None:
            if h in seen_hashes_written:
                return
            (ASSETS_DIR / f"{h}.png").write_bytes(data)
            seen_hashes_written.add(h)

        hash_to_hero: dict[str, str] = {}
        hero_to_hash: dict[str, str] = {}
        for slug, name_col in SOURCE_SHEETS:
            cells = get_cells(slug)
            anchors = get_drawing(slug)
            added = 0
            for row, _, _, data, _ in anchors:
                ref = f"{name_col}{row + 1}"  # drawing row is 0-indexed; cell ref is 1-indexed
                raw = (cells.get(ref) or "").strip()
                if not raw:
                    continue
                # Heroes occasionally have multiline names ("Ying\nZheng",
                # "Tsukuyomi "). Collapse whitespace for stable matching.
                name = " ".join(raw.split())
                h = hash_bytes(data)
                save_image(h, data)
                if h not in hash_to_hero:
                    hash_to_hero[h] = name
                    added += 1
                # earliest source-sheet listing wins for the reverse lookup
                hero_to_hash.setdefault(name, h)
            print(f"  source {slug}: {len(anchors)} anchors, +{added} new heroes")
        print(f"hash → hero map size: {len(hash_to_hero)}")

        # --- pass 2: for each target sheet, dump anchors + unique images ---
        target_data: dict[str, list[dict]] = {}
        unknown_count = 0
        for slug in TARGET_SHEETS:
            anchors = get_drawing(slug)
            cell_styles = get_cell_styles(slug)
            entries: list[dict] = []
            for row, col, _, data, media_path in anchors:
                h = hash_bytes(data)
                hero = hash_to_hero.get(h)
                if not hero:
                    unknown_count += 1
                save_image(h, data)
                # Drawing anchors use 0-indexed rows; sheet cell refs use 1-indexed.
                style_idx = cell_styles.get((row + 1, col))
                border = style_borders.get(style_idx) if style_idx is not None else None
                entries.append({
                    "row": row,
                    "col": col,
                    "hash": h,
                    "hero": hero,
                    "border": border,
                })
            target_data[slug] = entries
            print(f"  target {slug}: {len(entries)} anchors "
                  f"({sum(1 for e in entries if e['hero'])} identified)")

    payload = {
        "hash_to_hero": dict(sorted(hash_to_hero.items())),
        "hero_to_hash": dict(sorted(hero_to_hash.items())),
        "sheets": target_data,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} "
          f"({len(seen_hashes_written)} unique images → assets/runes/)")
    if unknown_count:
        print(f"  ⚠ {unknown_count} anchor(s) had no name match — image saved but unlabeled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
