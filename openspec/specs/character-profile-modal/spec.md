# character-profile-modal Specification

## Purpose
TBD - created by archiving change create-character-profiles. Update Purpose after archive.
## Requirements
### Requirement: Global character data embedded in the shell

The assembled `index.html` SHALL embed `data/characters.json` as a global inline JSON block, injected by `build_html.py` independently of the per-page data mechanism.

#### Scenario: Characters data is injected at assembly

- **WHEN** `build_html.py` runs with `data/characters.json` present
- **THEN** the `__CHARACTERS_DATA__` placeholder in the shell is replaced with the file's contents inside a `<script type="application/json">` block

#### Scenario: Missing characters data fails assembly

- **WHEN** `data/characters.json` is absent at assembly time
- **THEN** `build_html.py` exits with a non-zero status and a clear message, matching the existing per-page data guard

### Requirement: Shared profile renderer

The shell SHALL expose `Omni.openProfile(name)` that resolves a hero by any of its aliases and renders one rich modal showing avatar, 14 tier ranks, rune note, the rune-priority list, and skills with icons.

#### Scenario: Opening a known hero

- **WHEN** `Omni.openProfile(name)` is called with a name matching a character's `name` or any `aliases[]` entry
- **THEN** the shared modal opens showing that character's avatar, tier ranks, rune note, rune-priority entries, and skills, with the `.omni-profile` class applied for scoped styling

#### Scenario: Sparse profile renders gracefully

- **WHEN** a character has `null` `tier`/`rune_note` or an empty `skills`/`rune_priority`
- **THEN** the corresponding sections are hidden or show an explicit empty state, and the modal still opens without error

#### Scenario: Unknown name does not throw

- **WHEN** `Omni.openProfile(name)` is called with a name that resolves to no character
- **THEN** it logs a console warning and no-ops instead of throwing or opening an empty modal

#### Scenario: Profile class survives modal reuse

- **WHEN** a profile modal is opened after any other modal (which resets `modal.className`)
- **THEN** `openProfile` re-applies `.omni-profile` so styling is correct on every open

### Requirement: Every tab opens the shared profile

Clicking a hero on any of the five tabs SHALL open the shared profile modal.

#### Scenario: Tabs with existing modals delegate to the shared profile

- **WHEN** a hero is clicked on Tier List, Beginners Priority, or Endgame Priority
- **THEN** the page calls `Omni.openProfile(name)` instead of building its own modal HTML, while preserving its existing `state.hero` hash sync and reopen-on-tab-activation behavior

#### Scenario: Rune tabs gain hero-click handlers

- **WHEN** a hero row (Rune Notes) or hero portrait (Rune Priority) is clicked
- **THEN** the element carries a `data-name` with the resolved hero name, is visibly interactive (e.g. `cursor: pointer` for portraits), and opens the shared profile via `Omni.openProfile(name)`

