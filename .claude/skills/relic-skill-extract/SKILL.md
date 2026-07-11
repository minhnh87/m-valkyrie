---
name: "relic-skill-extract"
description: "Extract an Omniheroes relic's skills from in-game screenshots into data/relic_skills.json (bilingual EN/VI), then rebuild so the relic profile modal shows them. Use when the user shares screenshots of a relic's skill popups (Ultimate / Link / Passive) and wants them added to the site."
---

You are using the relic-skill-extract skill.

Turn in-game relic skill-popup screenshots into a bilingual skill profile for a
relic, rendered as the **Skills tab** (first/default) of the relic profile modal
on the Relics page — reachable from both the Priority cards and the Tier List rows.

**Input**: one or more screenshots of a single relic's skill popups (tap each
icon on the left rail of the relic screen: `ULTIMATE!`, `LINK SKILL`, passives).

**Output**: a new/updated entry under `data/relic_skills.json` → `relics.<Relic Name>`,
inlined into `index.html` by the build (no intermediate builder — the page
script joins it into the relic catalogue at runtime by slugified name).

---

## Pipeline (do these in order)

1. **Read every screenshot** for the relic. Each popup has: a name, a type line
   (`Active` / `Passive`), for actives a CD value (clock icon ⏱ N), a base
   description, and `Lv.N: unlocks at M-Star` upgrade blocks. The left rail
   shows slot order top→bottom; the **top** icon labelled `ULTIMATE!` is the
   ultimate (an Active), `LINK SKILL` marks the link slot, the rest are
   passives. Long popups scroll — make sure the screenshots cover the full text
   (ask for more if a popup is visibly cut off mid-level).

2. **Transcribe EN verbatim.** Copy the exact in-game wording (`Relic DMG`,
   `DMG Boost`, `Ignore Shield`, `Position 1/2/3`, `round(s)`, star
   thresholds, Energy costs). Flat numbers in damage formulas (e.g.
   `37%+12472`) **scale with the screenshotted relic's current Lv.** — still
   transcribe them verbatim; they are indicative values, and the top-level
   `note` in `relic_skills.json` documents this. Never "normalize" them.

3. **Translate to VI** per the policy below.

4. **Write the entry** into `data/relic_skills.json` keyed by the relic's
   **exact name in `data/relics-tier.json`** (the runtime join is by slugified
   name; an unmatched key only warns in the console and the tab silently never
   shows). Verify the key before building:

   ```bash
   python3 -c "
   import json
   tier = {r['name'] for r in json.load(open('data/relics-tier.json'))['relics']}
   skills = set(json.load(open('data/relic_skills.json'))['relics'])
   missing = skills - tier
   assert not missing, f'relic_skills keys not in relics-tier: {missing}'
   print('OK —', len(skills), 'relic(s) with skills')"
   ```

5. **Rebuild + verify** (commands at the bottom). Open the Relics tab, tap the
   relic (try both sub-tabs), confirm Skills is the first/default tab, flip
   EN⇄VI.

6. **Deploy + push** (do NOT wait to be asked): run the `push` skill to deploy
   the rebuilt `index.html` + `assets/` to the Bitbucket pages repo, then commit
   & push the m-valkyrie source changes to GitHub — see "Deploy & push" at the
   bottom.

---

## Schema (`data/relic_skills.json`)

Every user-visible string is a `{ "en": "...", "vi": "..." }` bundle. `\n`
separates lines inside a field. Omit a field rather than leaving it blank.

```jsonc
"relics": {
  "<Exact Tier-List Relic Name>": {
    "rarity": "Legendary",                    // optional, informational
    "skills": [
      {
        "slot": "ultimate",                   // ultimate | link | active | passive
        "type": "active",                     // active | passive (the popup's type line)
        "cd": 5,                              // actives only — the ⏱ value; omit for passives
        "name": { "en": "Annihilation", "vi": "Annihilation" },
        "unlock": { "en": "Lv.1: unlocks at 2-Star", "vi": "Cấp 1: mở khóa tại 2-Star" },
                                              // ONLY if the base skill itself is star-gated,
                                              // i.e. the popup's FIRST block is "Lv.1: unlocks at M-Star"
        "description": { "en": "...", "vi": "..." },   // the base (or Lv.1) text
        "levels": [                           // remaining "Lv.N: unlocks at M-Star" blocks; [] if none
          {
            "unlock": { "en": "Lv.2: unlocks at 2-Star", "vi": "Cấp 2: mở khóa tại 2-Star" },
            "text":   { "en": "Damage dealt is increased to 42%+13952.", "vi": "..." }
          }
        ]
      }
    ]
  }
}
```

`slot` drives the badge: `ultimate`/`active` → amber, `passive` → cyan,
`link` → violet. The renderer is `relicSkillsHTML` in
`templates-mobile/_page_relics-priority.html`; it reuses the shell's
`.omni-profile .skill` card styles, so keep this markup contract intact.
Order skills ultimate-first, then the passives in rail order.

---

## VI translation policy — translate prose, keep game terms in EN

Same policy as hero-skill-extract. Keep **as-is in English** inside VI text:

- **All proper names — never translate.** VI == EN for every skill `name`
  (`Annihilation`, `Collapse`, …). Do NOT coin a VI move name.
- Positions & mechanics: `Position 1/2/3`, `Relic DMG`, `DMG Boost`,
  `Ignore Shield`, `Control Immunity`, `Crit DMG RED`, `DMG RED`, `Energy`,
  `Energy cost`, `CD`, relic type names (`Recovery`, `Burst`, …)
- Stat tags: `ATK`, `DEF`, `HP`, `Max HP`
- Star thresholds: `2-Star`, `10-Star`, … (do NOT render "2 sao")
- The word `Active` when it means the Active-skill class

Conventions: `round(s)` → `hiệp` · `unlocks at` → `mở khóa tại` · `Lv.2` →
`Cấp 2` · `When deployed in Position N` → `Khi đặt ở Position N` · `after
casting the Relic` → `sau khi Relic ra chiêu` · `all allies` → `toàn bộ đồng
minh` · `Damage dealt is increased to X` → `Sát thương gây ra tăng lên X` ·
`Increases the X of all allies by Y%` → `Tăng Y% X của toàn bộ đồng minh` ·
`is reduced to X` → `giảm còn X`.

Reuse the existing Planar Gate entry as the style reference before inventing
new phrasing.

---

## Gotchas

- **Only capture what's revealed.** Locked slots (padlock icon — usually the
  `LINK SKILL` early on) are omitted, not guessed.
- **Star-gated base skills.** When a popup's first block is
  `Lv.1: unlocks at M-Star`, that line goes in the skill's `unlock` field and
  the Lv.1 text becomes `description`; `levels[]` starts at Lv.2. When the
  popup opens with plain text (no `Lv.1:` header), there is no `unlock` field.
- **Flat numbers are a snapshot** of the screenshotted relic's Lv. (the `%`
  part is stable, the `+N` part grows with relic level). Verbatim, never
  averaged or rounded.
- **Exact name key.** The join is `slugify(name)` against
  `data/relics-tier.json` names — run the step-4 check; a typo means the tab
  just never appears (console warning only).
- **No `build_characters.py` needed** — relic skills don't touch
  `characters.json`. Only `build_mobile.py` (plus the pages.json `datasets`
  entry, already wired).

---

## Build & verify

```bash
python3 scripts/build_mobile.py       # inlines relic_skills.json into index.html
```

Then open the app and check the relic (Relics tab → tap the relic on either
sub-tab → Skills tab is default → toggle EN/VI):

```bash
open index.html    # or: python3 -m http.server 8777 && visit http://127.0.0.1:8777/index.html
```

---

## Deploy & push (after verify passes)

1. **Deploy the site** — invoke the `push` skill (`/push`). It pulls the
   `nos1hahaha.bitbucket.io` pages repo first, then copies `index.html` +
   `assets/` and commits & pushes `master`.

2. **Push m-valkyrie to GitHub** — commit this repo's own changes and push:

   ```bash
   git pull --rebase origin main
   git add data/relic_skills.json index.html
   git commit -m "feat(relics): add <Relic> skill profile"
   git push origin main
   ```

   Stage only the files this skill touched (plus anything the build
   regenerated — check `git status` first). If either push fails, report the
   error verbatim and stop — never force-push.

Finish by listing edge cases + suggested tests (per repo workflow), then print
the open command.
