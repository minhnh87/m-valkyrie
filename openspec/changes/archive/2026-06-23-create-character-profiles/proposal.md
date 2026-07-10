## Why

Every hero's information is currently scattered across four separate tabs (Tier List, Rune Notes, Rune Priority, Beginners/Endgame Priority) plus a hidden avatar cache, with no single place to see a hero's full picture. Players have to hop between tabs to answer "what is this hero good at, and how do I build them?". There is also no skill/ability data anywhere on the site. This change consolidates everything per hero into one data file and surfaces it as a single click-to-open profile from any tab.

## What Changes

- Add a new build step that scrapes each hero's **Hero Skills** (name + description + icon) from the Omniheroes Fandom wiki via the MediaWiki API, mirrors icons locally to `assets/skills/`, and caches results to `data/skills.json` (resumable across partial runs).
- Add a new merge build step that produces `data/characters.json` — one entry per hero aggregating avatar, tier-list ranks, rune note, rune priority, and skills. Cross-sheet name variants are reconciled with a hand-curated alias map; the build **fails loudly** on any unmatched source name.
- Treat Arcane/Ascended/Primordial/Sovereign variants as **separate** characters (not merged with their base hero).
- Embed `data/characters.json` globally in the assembled `index.html` and add a shared `Omni.openProfile(name)` runtime that renders one rich profile modal (avatar, 14 tier ranks, rune note, rune priority list, skills with icons).
- Wire all five page fragments so clicking a hero opens the shared profile: the three tabs with bespoke modals (Tier List, Beginners, Endgame) delegate to `Omni.openProfile`; the two rune tabs (Rune Notes, Rune Priority) gain hero-click handlers.
- Extend `scripts/build_html.py` and `scripts/update.sh` to wire the new data file and build steps into the pipeline.

## Capabilities

### New Capabilities
- `character-profile-data`: the `data/characters.json` artifact and the pipeline that produces it — skill scraping, cross-sheet merge, alias-based name matching, duplicate-row handling, and fail-loud validation.
- `character-profile-modal`: the shared `Omni.openProfile(name)` profile modal and the integration that makes every hero across all five tabs open it.

### Modified Capabilities
<!-- None: there are no existing OpenSpec specs in this repo; the build pipeline and shell are documented in WORKFLOW.md but not as OpenSpec capabilities. -->

## Impact

- **New files**: `scripts/fetch_skills.py`, `scripts/build_characters.py`, `data/skills.json` (cache), `data/characters.json` (output), `assets/skills/` (icon mirror).
- **Modified files**: `templates/index.template.html` (global data block, `Omni.openProfile`, `.omni-profile` CSS), `scripts/build_html.py` (4th placeholder `__CHARACTERS_DATA__`), `scripts/update.sh` (skills + characters build steps), and all five `templates/_page_*.html` fragments (hero-click → profile).
- **External dependency**: Omniheroes Fandom MediaWiki API (`api.php`) — same source already used for avatars; known to rate-limit/403 on per-page parse bursts, so the scraper must back off, retry, and resume from cache.
- **No new tooling**: pure Python pipeline + vanilla JS, consistent with the existing single-file offline-first architecture. No package.json, no test framework introduced.
