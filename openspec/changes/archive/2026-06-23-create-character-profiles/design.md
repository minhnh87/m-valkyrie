## Context

The Omniheroes companion site is a single, offline-first `index.html` assembled by a Python pipeline (`scripts/update.sh` → per-page builders → `scripts/build_html.py`). Hero data lives in five page JSONs plus an avatar cache (`data/images.json`). There is no per-hero aggregate and no skill data. Avatars are already scraped from the Fandom MediaWiki API (`scripts/fetch_images.py`) and mirrored locally (`scripts/download_images.py`) so the site works via `file://`.

This change adds a per-hero aggregate (`data/characters.json`) and a shared profile modal, reusing existing conventions: the `ALIASES`/`normalize()` matching pattern, the `missing`-log pattern, local asset mirroring, `time.sleep` throttling, IIFE-per-page bootstrap, and CSS scoping. No new tooling, framework, or runtime dependency is introduced.

Constraints verified during exploration:
- Tier List is the only sheet carrying all 113 canonical hero names; other sheets use shorthand/typo'd names.
- Eight source names need a curated alias to match the canonical (the `A.` prefix is ambiguous — `A. Bastet`→`Ascended Bastett`, `A. Dorabella`→`Arcane Dorabella` — and `P. Arkdina`→`Primordial Arkdina`, not "Primeval"). The remaining four are Beginners shorthands (`Arc. Dorabella`, `Jorm`, `S. Aiush`, `Tsuki`).
- Rune Priority lists 10 heroes in two rows with differing priority/group.
- The Fandom API 403s after a small burst of per-page `action=parse` calls.

## Goals / Non-Goals

**Goals:**
- Produce `data/characters.json`: one entry per hero aggregating avatar, tier ranks, rune note, rune-priority list, and skills.
- Make any hero, on any of the five tabs, open one shared rich profile modal.
- Preserve full source fidelity — no silent data loss (fail loud on unmatched names; keep all rune-priority rows).
- Keep the build deterministic and re-runnable; tolerate partial skill coverage.

**Non-Goals:**
- A new "Characters" tab or route (the modal enrichment is the agreed surface).
- Scraping hero stats, lore, or anything beyond the "Hero Skills" section.
- Re-resolving the 8 missing hero avatars (out of scope; they fall back to initials/source image).
- Any test framework or CI tooling (repo has none by design).

## Decisions

**D1 — Curated alias map, fail-loud on miss.** Cross-sheet matching uses an explicit `ALIASES` dict in `build_characters.py` (8 entries), not mechanical abbreviation expansion. Rationale: `A.` maps to different words per hero and there are typos (`Bastett`); mechanical expansion is provably wrong. Any source name that resolves to no canonical hero is collected into `unmatched_names` and the build exits non-zero. Alternative (fuzzy suffix match) rejected: ambiguous when base and variant coexist (`Dorabella` vs `Arcane Dorabella`).

**D2 — Variants are separate characters.** Arcane/Ascended/Primordial/Sovereign units get their own `characters[]` entry (they coexist as distinct rows in the Tier List and are distinct game units). The merge key is the canonical Tier-List name; the base hero and its variant never merge.

**D3 — `rune_priority` is an array.** Each character holds a list of `{priority, border, group_label, group_notes}` so the 10 heroes appearing in two priority rows keep both. Alternative (single object + precedence) rejected: loses the group nuance even when priorities differ within the same group.

**D4 — Skill scraping is best-effort, resumable, prototype-first.** `fetch_skills.py` reuses `fetch_images.py`'s `api_get`/UA/`ALIASES`. Per-hero `action=parse&prop=sections` locates the "Hero Skills" section, then `action=parse&section=<idx>&prop=wikitext` (the section's `{| class="fandom-table"`, chosen over rendered HTML as it parses more cleanly) yields rows parsed for name/type/description/`File:` icon. Mitigations for the known 403: a real User-Agent, exponential backoff + retry on 403/429, generous `time.sleep`, and a **resumable cache** — `data/skills.json` keyed by canonical name so re-runs only fetch missing heroes. Heroes with no wiki page or no Hero Skills section land in `missing_skills` with `skills: []`. Implementation starts by prototyping ~6 heroes (including a variant and a template-less page) to confirm the format before scaling to all ~115.

**D5 — Icons mirrored locally.** Skill icon `File:` refs are resolved via batched `imageinfo` (50 titles/call, as avatars are) and downloaded to `assets/skills/`; each skill stores `icon: {local, url}`. Rationale: offline-first parity with avatars (page JSON embeds the `local` path; CDN 404s on cross-origin Referer). Trade-off: ~400 small downloads, throttled and cached.

**D6 — Avatar preference order.** `avatar = images.json hero avatar (local+url) if resolved, else the per-source image field (may be a rune image), else null`. Null renders the existing initials placeholder.

**D7 — `__CHARACTERS_DATA__` is a 4th shell placeholder.** `characters.json` is global, not a page, so it is NOT added to `pages.json`. `build_html.py` gains a 4th entry in its substitution tuple that reads `data/characters.json` into a `<script id="omni-characters" type="application/json">` block in the shell, failing if the file is absent (mirrors the per-page data guard). `update.sh` runs `build_characters.py` after all page builders and before `build_html.py`.

**D8 — Shared renderer, per-page hash ownership.** `Omni.openProfile(name)` is shell-owned: it builds an alias→character lookup once, renders the unified modal, calls `openModal`, then re-applies the `.omni-profile` class (because `openModal` resets `modal.className`). Hash state stays **per-page**: the three existing pages keep their `state.hero`/`syncHash`/reopen-on-`omni:tab-active`/clear-on-`omni:modal-closed` logic and only delegate rendering to `openProfile`. The two rune tabs get the same minimal `state.hero` plumbing plus `data-name` on their hero elements (Rune Priority portraits become clickable with `cursor: pointer` and the resolved canonical name). Rationale: lowest-risk; preserves existing deep-link/reopen behavior.

**D9 — Renderer tolerates sparsity.** The modal renders whatever is present: missing `tier`/`rune_note`/`rune_priority` sections are hidden; empty `skills` shows a "no skill data" state; a name that resolves to no character logs a console warning and no-ops rather than throwing.

## Risks / Trade-offs

- **Fandom 403 / rate-limit on ~115 per-page parses** → backoff + retry + resumable `skills.json` cache; partial runs accumulate coverage across invocations; `--no-skills`-style gating like `maybe_refresh_images` so normal rebuilds don't re-hit the wiki.
- **Hero Skills wikitext format may vary across heroes** → parse defensively; any unparseable page → `missing_skills` + `skills: []`. Treated as a hypothesis validated by the 6-hero prototype, not a guarantee.
- **Future heroes add new name shorthands** → fail-loud `unmatched_names` surfaces them immediately at build time rather than silently dropping; fix = add an alias entry (documented in WORKFLOW.md).
- **`openModal` clears `modal.className`** → `openProfile` adds `.omni-profile` after the open call; covered by D8.
- **Icon volume (~400 files)** → throttled downloads + cache; icons are small; skip already-downloaded files.
- **Cross-sheet duplicate beyond the known 10** → `build_characters.py` also asserts no UNEXPECTED duplicate canonical keys outside rune-priority and logs any it finds.

## Migration Plan

Additive and fully regenerable. Build order: `fetch_skills.py` → (page builders, unchanged) → `build_characters.py` → `build_html.py`. Rollback = revert the touched files and re-run `build_html.py`; `index.html` is a generated artifact. No data migration, no user-facing breaking change (existing tabs keep working; only the modal content is richer).

## Open Questions

None — scope, variant handling, `rune_priority` cardinality, skill detail level, icon storage, and hash ownership were all resolved during exploration.
