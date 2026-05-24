#!/usr/bin/env python3
"""Mirror every Fandom hero avatar in data/images.json into assets/heroes/.

Why: Fandom's CDN (static.wikia.nocookie.net) returns 404 when the request
Referer is an unrelated origin (e.g. *.bitbucket.io). So pages that <img src>
the CDN URL break on the deployed site. We pre-download the bytes into
assets/heroes/<original-filename> and rewrite each entry with a `local` field
that page builders consume.

The downloader is idempotent: it skips files that already exist on disk with
non-zero size. Pass --refresh to force re-download.

Run:
    python3 scripts/download_images.py
    python3 scripts/download_images.py --refresh
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGES_JSON = ROOT / "data" / "images.json"
ASSETS_DIR = ROOT / "assets" / "heroes"
ASSET_PREFIX = "assets/heroes/"  # what builders embed in page JSON

UA = "Mozilla/5.0 (m-valkyrie image mirror)"


def download(url: str, dest: Path) -> int:
    """Fetch `url` into `dest`. Returns bytes written."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true",
                    help="re-download even if local file already exists")
    args = ap.parse_args()

    if not IMAGES_JSON.exists():
        print(f"error: {IMAGES_JSON.relative_to(ROOT)} not found "
              f"(run scripts/fetch_images.py first)", file=sys.stderr)
        return 1

    payload = json.loads(IMAGES_JSON.read_text())
    heroes = payload.get("heroes", {})
    if not heroes:
        print("nothing to download (images.json has no heroes)")
        return 0

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = skipped = failed = 0
    failures: list[tuple[str, str]] = []  # (hero, reason)

    for name, info in heroes.items():
        fname = info.get("file")
        url = info.get("url")
        if not fname or not url:
            # missing entry — leave alone, builder will fall back to None
            continue

        dest = ASSETS_DIR / fname
        local_rel = ASSET_PREFIX + fname

        if not args.refresh and dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            info["local"] = local_rel
            continue

        try:
            size = download(url, dest)
            downloaded += 1
            info["local"] = local_rel
            print(f"  ↓ {name:<28} {fname:<32} ({size:,} bytes)")
            # gentle pace so we don't slam the CDN on a fresh clone
            time.sleep(0.15)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            failed += 1
            failures.append((name, str(e)))
            # remove any zero-byte file the failed write may have left
            if dest.exists() and dest.stat().st_size == 0:
                dest.unlink()
            # don't set `local` — builder will emit None for this hero
            info.pop("local", None)

    IMAGES_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(f"\n{downloaded} downloaded, {skipped} already cached, {failed} failed")
    if failures:
        print("failures:")
        for n, why in failures:
            print(f"  ✗ {n}: {why}")
    print(f"wrote: {IMAGES_JSON.relative_to(ROOT)}")
    print(f"cache: {ASSETS_DIR.relative_to(ROOT)}/")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
