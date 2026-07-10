# Verify fix log — create-character-profiles

## [2026-06-23] Round 1 (from spx-apply auto-verify)

### spx-verifier
- Fixed: design.md D4 said the section is fetched with `prop=text` (rendered HTML); the
  scraper actually uses `prop=wikitext`. Updated D4 to match the as-built choice (S1).

### spx-arch-verifier
- Fixed: removed dead `.omni-modal-from-tier-list` (8 rule blocks) and
  `.omni-modal-from-endgame-priority .tier-chip` CSS left over after the modal
  consolidation, plus the stale `.omni-modal-from-*` header comments in
  `_page_tier-list.html`, `_page_endgame-priority.html`, `_page_beginners-priority.html`.
- Fixed: `fetch_skills.py` `find_skills_section` docstring claimed it "Raises if the page
  does not exist" — it returns `None` for a missing page (error in response). Corrected.

### spx-uiux-verifier
- Fixed (CRITICAL): hero triggers were mouse-only. Added `role="button"` (where semantically
  valid), `tabindex="0"`, `aria-label`, and Enter/Space keydown handlers to the hero triggers
  on all 5 pages (tier-list cards + table rows, beginners/endgame pcards, rune-notes rows
  with table semantics preserved, rune-priority named portraits). Cursor scoped to
  `.portrait[data-name]` on rune-priority.
- Fixed (CRITICAL): shared modal `aria-labelledby="omni-modal-title"` referenced a missing
  id. `renderProfile()` now emits `<h2 id="omni-modal-title">`.
- Fixed (CRITICAL): no modal focus management. `openModal` now records the trigger and moves
  focus to the close button; `closeModal` restores focus; a Tab focus-trap keeps focus inside
  the open dialog (Esc/scrim close were already correct).
- Fixed (WARNING): modal close button enlarged to a 44×44 minimum touch target.

## [2026-06-23] Round 2 (from spx-apply auto-verify)

### spx-arch-verifier
- Fixed: removed the now-dead `heroByName()` function from `_page_beginners-priority.html`
  and `_page_endgame-priority.html` (unused after `openHero` was simplified to delegate to
  `Omni.openProfile`).

### spx-uiux-verifier
- Fixed: added explicit `:focus-visible` outline rings (`2px solid var(--primary)`) to the
  newly keyboard-focusable hero triggers on all 5 pages (tier-list card + row-portrait,
  beginners/endgame pcard, rune-notes row, rune-priority portrait) instead of relying on the
  weak default outline.

Round-2 re-verify: 0 CRITICAL remaining (both round-1 verifier sets re-run); both jsdom
smoke suites pass (31 functional + 20 a11y/keyboard, 0 console errors).
