---
name: "hero-skill-extract"
description: "Extract an Omniheroes character's skills from in-game screenshots into data/character_skills.json (bilingual EN/VI), then rebuild so the profile modal shows them. Use when the user shares screenshots of a hero's skill / rune-skill cards and wants them added to the site."
---

You are using the hero-skill-extract skill.

Turn in-game skill-card screenshots into a bilingual `skill_profile` for a hero,
rendered in the shared character-profile modal with an EN/VI toggle (EN default).

**Input**: one or more screenshots of a single hero's skill cards (Ultimate /
Active / Passive / Oath Force) and, when present, the "<Hero> Rune Skill" card.

**Output**: a new/updated entry under `data/character_skills.json` → `characters.<Hero>`,
merged into `data/characters.json` and inlined into `index.html` by the build.

---

## Pipeline (do these in order)

1. **Read every screenshot** for the hero. Each in-game skill card has: a name, a
   type line (`Active` / `Passive`), a base description, and sometimes `Lv.N:
   unlocks at M-Star` upgrade blocks. The left rail shows slot order top→bottom;
   the **top** icon labelled `ULTIMATE` is the ultimate. `Oath Force N` cards
   carry their own `Lv.1: unlocks at M-Star` line — that is the skill's unlock,
   not a per-level upgrade.

2. **Transcribe EN verbatim.** Copy the exact in-game wording (percentages, `MDMG`
   / `PDMG`, `Round`, `CD`, star thresholds). Screenshots are base-level +
   per-level and are the source of truth. `data/character_skills.json` is now the
   **sole** skill source: it already holds every hero the Fandom wiki had (55
   heroes, marked `"source": "fandom-wiki"` — flat, max-level, no `levels`/
   `rune_skill`). If the hero you're adding already has a `fandom-wiki` entry,
   **replace** it with the richer screenshot version (base-level + per-level +
   rune card) and drop the `source` marker.

3. **Translate to VI** per the policy below.

4. **Write the entry** into `data/character_skills.json` following the schema.
   Use the hero's **canonical Tier-List name** as the key (the build resolves it
   through the same alias map as every other sheet; an unresolved name fails the
   build loudly).

5. **Rebuild + verify** (commands at the bottom). Confirm `with skill_profile`
   incremented and spot-check the modal (open the hero, flip EN⇄VI).

6. **Deploy + push** (do NOT wait to be asked): run the `push` skill to deploy
   the rebuilt `index.html` + `assets/` to the Bitbucket pages repo, then commit
   & push the m-valkyrie source changes to GitHub — see "Deploy & push" at the
   bottom.

---

## Schema (`data/character_skills.json`)

Every user-visible string is a `{ "en": "...", "vi": "..." }` bundle. `\n`
separates lines inside a field. Omit a field rather than leaving it blank.

```jsonc
"characters": {
  "<Canonical Hero Name>": {
    "rarity": "Legendary",                      // optional, informational
    "title": { "en": "Fallen Star", "vi": "Sao Sa" },   // optional epithet
    "skills": [
      {
        "slot": "ultimate",                     // ultimate | active | passive | oath
        "type": "active",                       // active | passive (badge color/kind)
        "name": { "en": "...", "vi": "..." },
        "unlock": { "en": "Unlocks at 8-Star", "vi": "Mở khóa tại 8-Star" }, // ONLY if the base skill itself is star-gated (e.g. Oath Force)
        "description": { "en": "...", "vi": "..." },
        "levels": [                             // per-level upgrade blocks; [] if none
          {
            "unlock": { "en": "Lv.2: unlocks at 8-Star", "vi": "Cấp 2: mở khóa tại 8-Star" },
            "text":   { "en": "Damage dealt is increased to 379%.", "vi": "..." }
          }
        ]
      }
    ],
    "rune_skill": {                             // omit the whole block if the hero has no rune card
      "name": { "en": "<Hero> Rune Skill", "vi": "Kỹ Năng Rune <Hero>" },
      "tiers": [
        {
          "name":         { "en": "Fallen Star I", "vi": "Sao Sa I" },
          "effect":       { "en": "...", "vi": "..." },
          "requirements": { "en": "Equip 4 ... Exclusive Runes", "vi": "Trang bị 4 Rune Độc Quyền ..." }
        }
      ]
    }
  }
}
```

`slot` drives the badge: `ultimate`/`active` → amber, `passive` → cyan, `oath` →
violet. The renderer is in `templates-mobile/index.template.html`
(`renderSkillProfile`), reached via `renderSkillsSection`. `skill_profile` is the
only skill source the modal reads; heroes without one show an empty state. A skill
may carry an optional `icon: {local, url}` (Fandom-wiki entries keep theirs); the
renderer shows it, else a ◆ placeholder.

---

## VI translation policy — translate prose, keep game terms in EN

Keep these **as-is in English** inside the VI text (this is how VN players read them):

- **All proper names — never translate them.** The VI value equals the EN value for:
  every skill card `name` (`Soaring Dragon`, `Oath Force 1`, …), the hero `title`/epithet
  (`Warrior Maiden`, `Fallen Star`), and every `rune_skill` tier `name`
  (`Dragon Soul I`, `Fallen Star II`, …). Do NOT coin a VI move name.
- Damage/stat tags: `MDMG`, `PDMG`, `ATK`, `DEF`, `HP`, `Max HP`
- Rates: `ACC Rate`, `CRIT Rate`, `Dodge`, `Cure Rate`, `Reflect Rate`
- Star thresholds: `8-Star`, `11-Star`, … (do NOT render "8 sao")
- Status / keyword names & bracketed refs: `Contained`, `[United Strike]`,
  `Corrode`, `Burn`, `Immobilize`, `Swap`, `Shield`, `Stun`, `PvP`, `GvG`, and any
  mechanic/skill name referenced in prose (`Dragon Soul`, `Martial Dragon`, …)
- The word `Active` when it means the Active-skill class (e.g. "kỹ năng Active")

Translate only prose: descriptions, `levels[].text`, rune `effect`/`requirements`.

Translate everything else naturally. Conventions used so far:
`Casts in Round N. CD: 3 rounds.` → `Ra chiêu ở Hiệp N. CD: 3 hiệp.` ·
`unlocks at` → `mở khóa tại` · `Lv.2` → `Cấp 2` · `Increases … by X%` →
`Tăng X% …` · `stacking up to N times` → `cộng dồn tối đa N lần` ·
`Exclusive Runes` → `Rune Độc Quyền` · `Legendary Exclusive Runes` →
`Rune Độc Quyền Huyền Thoại` · `all allies` → `toàn bộ đồng minh` ·
`Stat Increase:` → `Tăng chỉ số:`.

Reuse existing Lucifer entries as the style reference before inventing new phrasing.

---

## Gotchas

- **Only capture what's revealed.** Locked slots (padlock icon) and higher Oath
  Force tiers not shown in the screenshots are omitted, not guessed.
- **Screenshot values are base level.** e.g. Final Dance shows 316% base with a
  `Lv.2 → 379%` block; a `fandom-wiki` entry would show only 379%. Keep the base
  in `description` and the upgrade in `levels[]` — this is exactly why a screenshot
  entry supersedes a `fandom-wiki` one.
- **Canonical name.** Variants (Arcane/Ascended/…) are their own heroes. If the
  key doesn't resolve, add an alias in `scripts/build_characters.py` — don't
  rename the hero.
- **The 55 `fandom-wiki` entries are the migrated wiki scrape** (flat, max-level,
  no `rune_skill`). Screenshots upgrade them and fill the ~52 heroes still missing.

---

## Build & verify

```bash
python3 scripts/build_characters.py   # merges character_skills.json → characters.json (watch "with skill_profile")
python3 scripts/build_mobile.py       # inlines characters.json into index.html
```

Then open the app and check the hero (open profile → Skills section → toggle EN/VI):

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
   git add data/character_skills.json data/characters.json index.html
   git commit -m "feat(skills): add <Hero> skill profile"
   git push origin main
   ```

   Stage only the files this skill touched (plus anything the build regenerated —
   check `git status` first). If either push fails, report the error verbatim and
   stop — never force-push.

Finish by listing edge cases + suggested tests (per repo workflow), then print the
open command.
