# character-profile-data Specification

## Purpose
TBD - created by archiving change create-character-profiles. Update Purpose after archive.
## Requirements
### Requirement: Unified character profile data file

The build pipeline SHALL produce `data/characters.json` containing one entry per hero that aggregates avatar, tier-list ranks, rune note, rune priority, and skills, plus top-level metadata (`columns`, `impact_tiers`, `priorities`, `fetched_at`, `source`) and diagnostic logs (`missing_skills`, `unmatched_names`).

#### Scenario: Each character aggregates all available sources

- **WHEN** `build_characters.py` runs with all source JSONs present
- **THEN** each `characters[]` entry has `name`, `aliases[]`, `avatar` (`{local,url}` or `null`), `tier` (or `null`), `rune_note` (or `null`), `rune_priority` (array, possibly empty), and `skills` (array, possibly empty)

#### Scenario: Top-level metadata is carried through

- **WHEN** the output file is written
- **THEN** it includes the 14-column `columns` list, `impact_tiers`, `priorities`, a `fetched_at` timestamp, the `source` URL, and the `missing_skills` and `unmatched_names` arrays

### Requirement: Cross-sheet name matching via curated alias map with fail-loud validation

The merge SHALL reconcile differing hero names across sheets using a hand-curated alias map and SHALL exit non-zero, recording every offender in `unmatched_names`, when any source name cannot be resolved to a canonical hero. Mechanical abbreviation expansion MUST NOT be used.

#### Scenario: Known shorthand resolves to canonical hero

- **WHEN** a source sheet uses a shorthand such as `A. Bastet`, `A. Dorabella`, `P. Arkdina`, `S. Aiushtha`, `Arc. Dorabella`, `Jorm`, `S. Aiush`, or `Tsuki`
- **THEN** it is matched to its canonical Tier-List name (e.g. `Ascended Bastett`, `Arcane Dorabella`, `Primordial Arkdina`, `Sovereign Aiushtha`, `Jormungand`, `Tsukuyomi`) and merged into that character

#### Scenario: Unmatched name fails the build

- **WHEN** a source name resolves to no canonical hero and no alias entry covers it
- **THEN** the build adds it to `unmatched_names` and exits with a non-zero status instead of silently dropping the hero

### Requirement: Variant heroes are distinct characters

Arcane/Ascended/Primordial/Sovereign variants SHALL each be their own character entry and MUST NOT be merged into their base hero.

#### Scenario: Base and variant coexist as separate entries

- **WHEN** both a base hero (e.g. `Dorabella`) and its variant (e.g. `Arcane Dorabella`) appear in the sources
- **THEN** `characters.json` contains two separate entries, each with its own tier/rune/skill data

### Requirement: Rune priority preserves all rows

A character's `rune_priority` SHALL be an array that retains every priority row in which the hero appears, with no precedence-based dropping.

#### Scenario: Hero in two priority groups keeps both

- **WHEN** a hero (e.g. `Emily`) appears in two Rune-Priority rows with differing priority/group
- **THEN** that character's `rune_priority` array contains both `{priority, border, group_label, group_notes}` entries

### Requirement: Avatar resolution with fallback

Each character's `avatar` SHALL prefer the resolved hero avatar, fall back to the per-source image, and be `null` when neither exists.

#### Scenario: Hero with no resolved avatar

- **WHEN** a hero is in `images.json`'s missing list (e.g. `Asmodeus`) and has no hero avatar
- **THEN** `avatar` is either the per-source image (if any) or `null`, never a broken hero-avatar reference

### Requirement: Skill scraping is best-effort, resumable, and locally mirrored

`fetch_skills.py` SHALL scrape each hero's "Hero Skills" section from the Fandom MediaWiki API, cache results to `data/skills.json` keyed by canonical name, mirror skill icons to `assets/skills/`, and degrade gracefully when data is unavailable.

#### Scenario: Hero with a Hero Skills section

- **WHEN** a hero's wiki page has a "Hero Skills" section
- **THEN** each skill is recorded with `name`, `type` (active/passive), `description`, and `icon: {local, url}` whose `local` file is downloaded under `assets/skills/`

#### Scenario: Hero without skill data

- **WHEN** a hero has no wiki page or no "Hero Skills" section
- **THEN** the hero's `skills` is `[]` and the hero name is added to `missing_skills`

#### Scenario: Resumable across rate-limited runs

- **WHEN** the API returns 403/429 mid-run and the script retries with backoff but cannot complete every hero
- **THEN** already-fetched skills persist in `data/skills.json` and a subsequent run fetches only the still-missing heroes

