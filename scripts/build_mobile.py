#!/usr/bin/env python3
"""Assemble the single-file site (index.html) from the mobile-first shell
template + page fragments.

The mobile-first build is now the ONLY build: it writes the sole user-facing
file, index.html. (The legacy desktop build_html.py + templates/ are retired —
kept on disk for reference but no longer run.) It reuses the SAME data pipeline
(data/pages.json, data/<page>.json, data/characters.json) and reads templates
from templates-mobile/.

For each page listed in data/pages.json we:
  1. Read templates-mobile/<fragment>  (style + markup + data block + IIFE)
  2. Split on the marker `<!-- ::: PAGE SCRIPT ::: -->`
  3. Replace the page's placeholder with its data JSON (data/<data_file>)
  4. Append the markup half to __PAGE_FRAGMENTS__ and the script half to
     __PAGE_SCRIPTS__ in the mobile shell.

Run:
    python3 scripts/build_mobile.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates-mobile"
DATA = ROOT / "data"
PAGES_JSON = DATA / "pages.json"
CHARACTERS_JSON = DATA / "characters.json"
SHELL = TEMPLATES / "index.template.html"
OUT = ROOT / "index.html"

SCRIPT_MARKER = "<!-- ::: PAGE SCRIPT ::: -->"
FRAGMENT_MARKER = "<!-- ::: PAGE FRAGMENT ::: -->"


def load_fragment(page: dict) -> tuple[str, str]:
    """Return (markup_part, script_part) with the page's data inlined."""
    frag_path = TEMPLATES / page["fragment"]
    if not frag_path.exists():
        raise SystemExit(
            f"mobile fragment {frag_path.relative_to(ROOT)} not found "
            f"(every page in pages.json needs a templates-mobile/ fragment)"
        )
    raw = frag_path.read_text()

    if SCRIPT_MARKER not in raw:
        raise SystemExit(
            f"{frag_path.name} is missing the `{SCRIPT_MARKER}` separator"
        )
    markup, _, script = raw.partition(SCRIPT_MARKER)
    markup = markup.replace(FRAGMENT_MARKER, "").strip()
    script = script.strip()

    # A page injects one data block by default (placeholder + data), but may
    # declare several via `datasets` — e.g. the Relics page hosts both the
    # Priority and Tier List sub-tabs, each with its own JSON.
    datasets = page.get("datasets") or [
        {"placeholder": page["placeholder"], "data": page["data"]}
    ]
    for ds in datasets:
        placeholder = ds["placeholder"]
        if placeholder not in markup:
            raise SystemExit(
                f"{frag_path.name} markup section is missing placeholder {placeholder!r}"
            )
        data_path = DATA / ds["data"]
        if not data_path.exists():
            raise SystemExit(
                f"data file {data_path.relative_to(ROOT)} not found "
                f"(run the page builder first)"
            )
        markup = markup.replace(placeholder, data_path.read_text())

    return markup, script


def main() -> int:
    meta = json.loads(PAGES_JSON.read_text())
    shell = SHELL.read_text()

    markup_parts: list[str] = []
    script_parts: list[str] = []
    for page in meta["pages"]:
        m, s = load_fragment(page)
        markup_parts.append(f"<!-- page: {page['slug']} -->\n{m}")
        script_parts.append(f"<!-- script: {page['slug']} -->\n{s}")

    if not CHARACTERS_JSON.exists():
        raise SystemExit(
            f"data file {CHARACTERS_JSON.relative_to(ROOT)} not found "
            f"(run scripts/build_characters.py first)"
        )
    characters_data = CHARACTERS_JSON.read_text()

    for placeholder, value in (
        ("__PAGES_META__", json.dumps(meta, ensure_ascii=False)),
        ("__PAGE_FRAGMENTS__", "\n\n".join(markup_parts)),
        ("__PAGE_SCRIPTS__", "\n\n".join(script_parts)),
        ("__CHARACTERS_DATA__", characters_data),
    ):
        if placeholder not in shell:
            raise SystemExit(f"mobile shell template is missing placeholder {placeholder!r}")
        shell = shell.replace(placeholder, value)

    OUT.write_text(shell)
    print(
        f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes) "
        f"with {len(meta['pages'])} pages"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
