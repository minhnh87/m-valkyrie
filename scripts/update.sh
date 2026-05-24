#!/usr/bin/env bash
# One-shot update: re-pull the spreadsheet tabs, refresh hero images, rebuild
# every page's data JSON, and re-assemble the single tabbed index.html.
#
# Usage:
#   ./scripts/update.sh                  # update everything
#   ./scripts/update.sh tier-list        # only rebuild this page's data
#   ./scripts/update.sh --no-images      # skip the wiki image refresh
#
# Adding a new page: see WORKFLOW.md.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REFRESH_IMAGES=1
TARGETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-images) REFRESH_IMAGES=0; shift ;;
    --) shift; TARGETS+=("$@"); break ;;
    *) TARGETS+=("$1"); shift ;;
  esac
done

ALL_PAGES=(tier-list beginners-priority)
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${ALL_PAGES[@]}")
fi

IMAGES_REFRESHED=0
maybe_refresh_images() {
  if [[ $REFRESH_IMAGES -eq 1 && $IMAGES_REFRESHED -eq 0 ]]; then
    echo "▶ refreshing hero images from Fandom"
    python3 scripts/fetch_images.py
    IMAGES_REFRESHED=1
  fi
}

build_tier_list() {
  echo "▶ tier-list: pulling CSV"
  ./scripts/fetch_sheet.sh tier-list
  maybe_refresh_images
  echo "▶ tier-list: building data JSON"
  python3 scripts/build_tier_list.py
}

build_beginners_priority() {
  echo "▶ beginners-priority: pulling CSV"
  ./scripts/fetch_sheet.sh beginners-priority
  maybe_refresh_images
  echo "▶ beginners-priority: building data JSON"
  python3 scripts/build_beginners_priority.py
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    tier-list) build_tier_list ;;
    beginners-priority) build_beginners_priority ;;
    *) echo "Unknown target: $t (known: ${ALL_PAGES[*]})" >&2; exit 1 ;;
  esac
done

echo "▶ assembling index.html"
python3 scripts/build_html.py

echo "✓ Done. Open index.html in a browser."
