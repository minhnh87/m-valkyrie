#!/usr/bin/env python3
"""Fetch hero avatar URLs from the Omniheroes Fandom wiki.

Strategy:
  1. Parse the Heroes page to build a name → avatar-filename map (best source).
  2. For names in the tier list that aren't in that map, try common filename
     patterns (e.g. "<name>avt.jpg", "<name>avt.png") via the imageinfo API.
  3. For each filename collected, resolve to a real CDN URL via imageinfo.
  4. Persist to data/images.json so we don't re-hit the wiki on every build.

Run:
    python3 scripts/fetch_images.py
    python3 scripts/fetch_images.py --refresh   # ignore cache
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
IMAGES_JSON = DATA / "images.json"

API = "https://omniheroesgame.fandom.com/api.php"
UA = "Mozilla/5.0 (m-valkyrie tier-list builder)"


def api_get(params: dict) -> dict:
    """Single GET against the MediaWiki API."""
    params = {**params, "format": "json"}
    url = API + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def fetch_heroes_page_map() -> dict[str, str]:
    """Return {hero_name: avatar_filename} from the Heroes page wikitext."""
    data = api_get({"action": "parse", "page": "Heroes", "prop": "wikitext"})
    wt = data["parse"]["wikitext"]["*"]
    # Matches: |Name then |[[File:Avatar.ext|...]] OR |[[Name]] then |[[File:Avatar.ext|...]]
    pat = re.compile(
        r"\|(?:\[\[)?([A-Za-zÀ-ÿ' &]{2,40}?)(?:\]\])?\n\|\[\[File:([^|\]]+(?:avt|Avt|AVT)\.(?:jpg|png|jpeg|gif))",
        re.IGNORECASE,
    )
    return {n.strip(): f for n, f in pat.findall(wt)}


def normalize(name: str) -> str:
    return re.sub(r"\s+", "", name).lower().strip()


def candidate_filenames(name: str) -> list[str]:
    """Generate likely Fandom file names for a hero."""
    clean = name.strip()
    bare = re.sub(r"\s+", "", clean)
    cands = []
    for stem in (bare, clean.replace(" ", ""), clean.replace(" ", "_"), clean):
        for suffix in ("avt", "Avt", "AVT"):
            for ext in ("png", "jpg", "jpeg"):
                cands.append(f"{stem}{suffix}.{ext}")
    # dedupe preserving order
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_image_urls(filenames: list[str]) -> dict[str, str]:
    """Batch the imageinfo API to map filename → CDN URL."""
    out: dict[str, str] = {}
    # MediaWiki allows up to 50 titles per call
    for i in range(0, len(filenames), 40):
        chunk = filenames[i : i + 40]
        titles = "|".join(f"File:{fn}" for fn in chunk)
        data = api_get(
            {
                "action": "query",
                "titles": titles,
                "prop": "imageinfo",
                "iiprop": "url",
            }
        )
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            if "imageinfo" in p:
                title = p["title"].removeprefix("File:")
                out[title] = p["imageinfo"][0]["url"]
        time.sleep(0.3)
    return out


def read_tier_list_names() -> list[str]:
    """Pull hero names from the tier-list CSV (column C, index 2)."""
    csv_path = RAW / "tier-list.csv"
    names: list[str] = []
    with csv_path.open(newline="") as f:
        for row in csv.reader(f):
            if len(row) < 3:
                continue
            name = (row[2] or "").strip()
            if not name or name == "Name":
                continue
            # join multi-line cells like "Sovereign Aiushtha\n"
            name = re.sub(r"\s+", " ", name).strip()
            names.append(name)
    return names


# Manual overrides: tier-list name → wiki page/file basename.
# Use this for spelling differences and heroes not on the Heroes page table.
ALIASES = {
    "King Arthur": "Arthur",
    "RA": "Ra",
    "Arianna": "Ariana",
    "Ascended Bastett": "Ascended Bastet",
    "Tsukuyomi ": "Tsukuyomi",
    # NOTE: do NOT alias Vittoria → Victoria, they are different heroes.
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="ignore existing cache")
    args = ap.parse_args()

    cache: dict = {}
    if IMAGES_JSON.exists() and not args.refresh:
        cache = json.loads(IMAGES_JSON.read_text())
    by_name: dict[str, dict] = cache.get("heroes", {})

    print("Fetching Heroes page map…")
    heroes_map = fetch_heroes_page_map()
    print(f"  {len(heroes_map)} avatar filenames listed on the Heroes page")

    # Normalize lookup for fuzzy matches
    heroes_map_norm = {normalize(k): (k, v) for k, v in heroes_map.items()}

    tier_names = read_tier_list_names()
    print(f"Tier list has {len(tier_names)} heroes")

    needed_files: set[str] = set()
    resolution: dict[str, str] = {}  # tier-name → filename

    for name in tier_names:
        alias = ALIASES.get(name, name)
        norm = normalize(alias)
        if norm in heroes_map_norm:
            _, fn = heroes_map_norm[norm]
            resolution[name] = fn
            needed_files.add(fn)
        # else: try candidates further down

    unresolved = [n for n in tier_names if n not in resolution]
    print(f"Resolved from Heroes page: {len(resolution)}; unresolved: {len(unresolved)}")
    if unresolved:
        print("  Trying candidate filenames for:", ", ".join(unresolved))

    candidate_pool: list[str] = []
    cand_by_name: dict[str, list[str]] = {}
    for name in unresolved:
        alias = ALIASES.get(name, name)
        cands = candidate_filenames(alias)
        cand_by_name[name] = cands
        candidate_pool.extend(cands)

    # de-dupe pool
    candidate_pool = list(dict.fromkeys(candidate_pool))
    cand_urls: dict[str, str] = {}
    if candidate_pool:
        print(f"  Probing {len(candidate_pool)} candidate filenames…")
        cand_urls = resolve_image_urls(candidate_pool)

    for name, cands in cand_by_name.items():
        for c in cands:
            if c in cand_urls:
                resolution[name] = c
                needed_files.add(c)
                break

    # Resolve URLs for everything we accepted
    print(f"Resolving {len(needed_files)} avatar URLs…")
    urls = resolve_image_urls(sorted(needed_files))

    final: dict[str, dict] = {}
    missing: list[str] = []
    for name in tier_names:
        fn = resolution.get(name)
        if fn and fn in urls:
            final[name] = {"file": fn, "url": urls[fn]}
        else:
            missing.append(name)
            # preserve any prior cache entry
            if name in by_name:
                final[name] = by_name[name]

    out = {
        "fetched_at": int(time.time()),
        "source": "https://omniheroesgame.fandom.com",
        "heroes": final,
        "missing": missing,
    }
    IMAGES_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {IMAGES_JSON.relative_to(ROOT)}")
    print(f"  Resolved: {len(final)}; still missing: {len(missing)}")
    if missing:
        print("  Missing:", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
