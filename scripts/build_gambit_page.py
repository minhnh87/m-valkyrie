#!/usr/bin/env python3
"""Assemble the standalone Sacred Gambit Q&A page (gambit.html).

Deliberately separate from build_mobile.py: gambit.html is a one-off, fully
self-contained page (no shell, no nav, no shared CSS, icons inlined as data
URIs — it references nothing under assets/) that changes only when the Q&A
sheet does. It is NOT part of data/pages.json and is not rebuilt by
scripts/update.sh.

Pipeline:
    scripts/build_gambit.py       # pull the published sheet -> data/gambit.json
    scripts/build_gambit_page.py  # this: template + JSON  -> gambit.html

Run:
    python3 scripts/build_gambit_page.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates-mobile" / "gambit.template.html"
DATA = ROOT / "data" / "gambit.json"
OUT = ROOT / "gambit.html"

PLACEHOLDER = "__GAMBIT_DATA__"


def main() -> int:
    if not TEMPLATE.exists():
        raise SystemExit(f"template {TEMPLATE.relative_to(ROOT)} not found")
    if not DATA.exists():
        raise SystemExit(
            f"data file {DATA.relative_to(ROOT)} not found "
            f"(run scripts/build_gambit.py first)"
        )

    html = TEMPLATE.read_text()
    if PLACEHOLDER not in html:
        raise SystemExit(f"template is missing placeholder {PLACEHOLDER!r}")

    # The JSON goes inside <script type="application/json">, so the one thing
    # that could break the document is a literal `</script>` in the data.
    data = DATA.read_text().replace("</script>", "<\\/script>")
    OUT.write_text(html.replace(PLACEHOLDER, data))

    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
