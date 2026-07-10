## 1. Skill scraper (prototype-first)

- [x] 1.1 Create `scripts/fetch_skills.py` reusing `fetch_images.py` conventions: shared `api_get`, real `User-Agent`, `ALIASES` map (canonical hero name → wiki page title), and a resumable cache at `data/skills.json` keyed by canonical name
- [x] 1.2 Implement section discovery: `action=parse&page=<title>&prop=sections`, locate the "Hero Skills" section index (case-insensitive)
- [x] 1.3 Implement skill parsing: fetch that section (`prop=wikitext` — cleaner than rendered HTML for this `fandom-table`), extract per skill `name`, `type` (active/passive), `description`, and the `File:` icon reference
- [x] 1.4 Add 403/429 handling: exponential backoff + retry + generous `time.sleep`; on persistent failure, record the hero in `missing_skills` and continue
- [x] 1.5 Prototype against ~6 heroes (include a variant like `Arcane Dorabella` and a template-less page) to confirm the wikitext/HTML format before scaling ← (verify: parser returns name+desc+icon for the prototype set; format assumptions documented; 403 backoff actually triggers)
- [x] 1.6 Resolve icon `File:` refs to CDN URLs via batched `imageinfo` (≤50 titles/call) and download to `assets/skills/`, skipping already-present files; store `icon: {local, url}` per skill
- [x] 1.7 Run the full scrape; write `data/skills.json` with `heroes{}`, `missing_skills[]`, `fetched_at`, `source` ← (verify: re-running fetches only missing heroes; no re-download of existing icons; missing heroes logged, not crashed) — 113 heroes cached, 56 with skills, 65 icons downloaded, 0 failed

## 2. Character merge build

- [x] 2.1 Create `scripts/build_characters.py` that loads `tier-list.json`, `rune-notes.json`, `rune-priority.json`, `beginners-priority.json`, `endgame-priority.json`, `images.json`, and `skills.json`
- [x] 2.2 Define the curated `ALIASES` map with all 8 entries (`A. Bastet`→`Ascended Bastett`, `A. Dorabella`→`Arcane Dorabella`, `P. Arkdina`→`Primordial Arkdina`, `S. Aiushtha`→`Sovereign Aiushtha`, `Arc. Dorabella`→`Arcane Dorabella`, `Jorm`→`Jormungand`, `S. Aiush`→`Sovereign Aiushtha`, `Tsuki`→`Tsukuyomi`); build canonical entries keyed by Tier-List name, keeping variants separate
- [x] 2.3 Merge per character: `avatar` (hero avatar → source image → null), `tier`, `rune_note`, `rune_priority` (array of all rows), `skills`; record every source name into `aliases[]`
- [x] 2.4 Validation: collect any source name that resolves to no canonical hero into `unmatched_names`; assert no unexpected duplicate canonical keys outside the known 10 rune-priority dups; print counts of missing avatars/skills ← (verify: with the 8 aliases, `unmatched_names` is empty across all 5 source sheets; build exits non-zero if a name is unmatched; the 10 dup heroes keep both rune_priority rows)
- [x] 2.5 Write `data/characters.json` with `characters[]` + top-level `columns`/`impact_tiers`/`priorities`/`fetched_at`/`source` + `missing_skills`/`unmatched_names`

## 3. Shell: global data, renderer, styling

- [x] 3.1 Add `<script id="omni-characters" type="application/json">__CHARACTERS_DATA__</script>` to `templates/index.template.html`
- [x] 3.2 Add `Omni.openProfile(name)` to the shell IIFE: build an alias→character lookup once; render the unified modal (avatar with initials fallback, 14 tier ranks grouped, rune note, rune-priority list, skills with icons); call `openModal` then re-apply the `.omni-profile` class; warn + no-op on unknown name
- [x] 3.3 Add `.omni-profile` scoped CSS for the profile sections (reuse theme vars, tier palette `--t-*`, hairlines; no new ad-hoc colors)
- [x] 3.4 Ensure the renderer hides absent `tier`/`rune_note`/`rune_priority` sections and shows an explicit empty state for `skills: []` ← (verify: opening a hero with null sub-objects / empty skills renders cleanly without errors)

## 4. Wire the five page fragments

- [x] 4.1 `_page_tier-list.html`: replace bespoke modal HTML in `openHero` with `Omni.openProfile(name)`, keep `state.hero`/`syncHash`/onTab/onModalClosed
- [x] 4.2 `_page_beginners-priority.html`: replace its `Omni.openModal(...)` call with `Omni.openProfile(name)`, preserving hash state
- [x] 4.3 `_page_endgame-priority.html`: same delegation as beginners
- [x] 4.4 `_page_rune-notes.html`: add a click handler on `<tr data-name>` rows → `Omni.openProfile(name)` + minimal `state.hero` plumbing
- [x] 4.5 `_page_rune-priority.html`: add `data-name` (resolved canonical) + `cursor: pointer` to `.portrait`, add click → `Omni.openProfile(name)` + minimal `state.hero` plumbing ← (verify: clicking a hero on all 5 tabs opens the same shared profile; rune-priority duplicate portraits both open the same hero)

## 5. Pipeline integration

- [x] 5.1 `scripts/build_html.py`: add a 4th substitution for `__CHARACTERS_DATA__` reading `data/characters.json`, failing with a clear non-zero exit if absent (mirror the per-page data guard)
- [x] 5.2 `scripts/update.sh`: add a skills step (gated like `maybe_refresh_images`) and a `build_characters.py` step ordered after all page builders and before `build_html.py` ← (verify: a full `./scripts/update.sh` run executes fetch_skills → build_characters → build_html in order and regenerates index.html)
- [x] 5.3 Update `WORKFLOW.md` with the new files, the alias-on-new-hero note, and the skills-cache/`--no-skills` behavior

## 6. Build & verify

- [x] 6.1 Run the pipeline end to end; confirm `python3 scripts/build_html.py` succeeds and `index.html` regenerates without errors
- [x] 6.2 Manual click checklist: open `index.html` via `file://`, click heroes across all 5 tabs, confirm the shared profile shows avatar/tier/rune/skills correctly, including a sparse hero and a variant ← (verify: profile modal correct on every tab; icons load from `assets/skills/`; no console errors; deep-link/reopen-on-reload still works) — verified via headless jsdom smoke suites (31 functional + 20 a11y, 0 console errors); skill icon `<img src="assets/skills/…">` confirmed rendering
- [x] 6.3 Print the command to open the app (per CLAUDE.md)
