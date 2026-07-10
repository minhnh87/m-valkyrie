#!/usr/bin/env python3
"""Merge every per-sheet hero JSON into one per-character aggregate.

Produces data/characters.json: one entry per canonical hero (keyed by the
Tier-List name, the only sheet carrying all canonical names) aggregating
avatar, tier ranks, rune note, rune priority (all rows), and skills.

Cross-sheet name variants are reconciled with a hand-curated `ALIASES` map
(NOT mechanical abbreviation expansion — `A.` means different words per hero
and there are typos). Any source name that resolves to no canonical hero is
collected into `unmatched_names` and the build exits non-zero — we fail loud
rather than silently drop a hero.

Variants (Arcane/Ascended/Primordial/Sovereign …) are their own canonical
Tier-List rows, so they stay separate characters; they never merge into the
base hero.

Run:
    python3 scripts/build_characters.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "characters.json"

TIER_LIST = DATA / "tier-list.json"
RUNE_NOTES = DATA / "rune-notes.json"
RUNE_PRIORITY = DATA / "rune-priority.json"
BEGINNERS = DATA / "beginners-priority.json"
ENDGAME = DATA / "endgame-priority.json"
IMAGES = DATA / "images.json"
CHAR_SKILLS = DATA / "character_skills.json"  # sole skill source (bilingual EN/VI)

# Curated cross-sheet aliases: source name → canonical Tier-List name.
# The `A.` prefix is ambiguous (Ascended vs Arcane) and `Bastett` is a
# Tier-List typo, so these cannot be derived mechanically.
ALIASES = {
    "A. Bastet": "Ascended Bastett",
    "A. Dorabella": "Arcane Dorabella",
    "P. Arkdina": "Primordial Arkdina",
    "S. Aiushtha": "Sovereign Aiushtha",
    "Arc. Dorabella": "Arcane Dorabella",
    "Jorm": "Jormungand",
    "S. Aiush": "Sovereign Aiushtha",
    "Tsuki": "Tsukuyomi",
}

# Heroes known to appear in two Rune-Priority rows (different priority/group).
# Used only as a sanity check — both rows are always kept regardless.
KNOWN_RP_DUPS = {
    "Amaterasu", "Aphrodite", "Emily", "Gaia", "Janna",
    "Jormungand", "Karnak", "Persephone", "Seraphina", "Wu Zetian",
}


def normalize(s: str) -> str:
    return re.sub(r"\s+", "", s or "").lower().strip()


def load(path: Path, *, required: bool = True) -> dict:
    if not path.exists():
        if required:
            raise SystemExit(
                f"error: {path.relative_to(ROOT)} not found (run its builder first)"
            )
        return {}
    return json.loads(path.read_text())


def main() -> int:
    tier = load(TIER_LIST)
    runenotes = load(RUNE_NOTES)
    runepri = load(RUNE_PRIORITY)
    beginners = load(BEGINNERS)
    endgame = load(ENDGAME)
    images = load(IMAGES)
    char_skills_doc = load(CHAR_SKILLS, required=False)

    canon_names = [h["name"] for h in tier["heroes"]]
    canon_by_norm = {normalize(n): n for n in canon_names}
    alias_norm = {normalize(k): v for k, v in ALIASES.items()}

    # Validate every alias targets a real canonical hero (fail fast on a typo).
    for src, tgt in ALIASES.items():
        if normalize(tgt) not in canon_by_norm:
            raise SystemExit(
                f"error: alias {src!r} → {tgt!r} targets no canonical hero"
            )

    def resolve(name: str) -> str | None:
        if not name or not name.strip():
            return None
        n = normalize(name)
        if n in canon_by_norm:
            return canon_by_norm[n]
        if n in alias_norm:
            t = normalize(alias_norm[n])
            if t in canon_by_norm:
                return canon_by_norm[t]
        return None

    chars: dict[str, dict] = {}
    alias_sets: dict[str, set] = {}
    src_image: dict[str, str] = {}  # canonical → first non-null source image
    for name in canon_names:
        chars[name] = {
            "name": name,
            "aliases": [],
            "avatar": None,
            "tier": None,
            "rune_note": None,
            "rune_priority": [],
            "skill_profile": None,
        }
        alias_sets[name] = set()

    unmatched: list[dict] = []

    def add_alias(canonical: str, raw: str) -> None:
        if raw and raw not in alias_sets[canonical]:
            alias_sets[canonical].add(raw)
            chars[canonical]["aliases"].append(raw)

    def note_image(canonical: str, img: str | None) -> None:
        if img and canonical not in src_image:
            src_image[canonical] = img

    # --- Tier List (canonical source) ---
    for h in tier["heroes"]:
        c = h["name"]
        add_alias(c, h["name"])
        chars[c]["tier"] = {
            "tiers": h.get("tiers", {}),
            "overall": h.get("overall"),
            "overall_band": h.get("overall_band"),
            "notes": h.get("notes", ""),
        }
        note_image(c, h.get("image"))

    # --- Rune Notes ---
    for h in runenotes["heroes"]:
        c = resolve(h["name"])
        if not c:
            unmatched.append({"sheet": "rune-notes", "name": h["name"]})
            continue
        add_alias(c, h["name"])
        chars[c]["rune_note"] = {
            "rune_type": h.get("rune_type"),
            "secondary_type": h.get("secondary_type"),
            "reasoning": h.get("reasoning"),
            "substat_pre_11": h.get("substat_pre_11"),
            "substat_post_11": h.get("substat_post_11"),
            "roll_unique": h.get("roll_unique"),
            "impact": h.get("impact"),
            "if_needed": h.get("if_needed"),
        }
        note_image(c, h.get("image"))

    # --- Rune Priority (keep every row) ---
    for t in runepri["tiers"]:
        for h in t["heroes"]:
            nm = (h.get("name") or "").strip()
            if not nm:
                continue  # unidentified anchor — image only, no hero name
            c = resolve(nm)
            if not c:
                unmatched.append({"sheet": "rune-priority", "name": nm})
                continue
            add_alias(c, nm)
            chars[c]["rune_priority"].append({
                "priority": h.get("priority"),
                "border": h.get("border"),
                "group_label": t.get("label"),
                "group_notes": t.get("notes"),
            })
            note_image(c, h.get("image"))

    # --- Beginners + Endgame (names + image fallback only) ---
    for sheet_name, doc in (("beginners-priority", beginners),
                            ("endgame-priority", endgame)):
        for s in doc["sections"]:
            for h in s["heroes"]:
                c = resolve(h["name"])
                if not c:
                    unmatched.append({"sheet": sheet_name, "name": h["name"]})
                    continue
                add_alias(c, h["name"])
                note_image(c, h.get("image"))

    # --- Skill profiles (bilingual EN/VI; the sole skill source) ---
    # Keys are canonical names but pass through resolve() so aliases/variants
    # still land on the right hero (fail loud otherwise). The profile modal
    # renders this; heroes without one show an empty state.
    for raw_name, profile in (char_skills_doc.get("characters") or {}).items():
        c = resolve(raw_name)
        if not c:
            unmatched.append({"sheet": "character-skills", "name": raw_name})
            continue
        chars[c]["skill_profile"] = profile

    # --- Avatar resolution: images.json hero avatar → source image → null ---
    img_heroes = images.get("heroes", {})
    for c in canon_names:
        entry = img_heroes.get(c)
        if entry and entry.get("local"):
            chars[c]["avatar"] = {"local": entry["local"], "url": entry.get("url")}
        elif src_image.get(c):
            chars[c]["avatar"] = {"local": src_image[c], "url": None}
        else:
            chars[c]["avatar"] = None

    # --- Validation + diagnostics ---
    dup_heroes = {c for c in canon_names if len(chars[c]["rune_priority"]) > 1}
    unexpected_dups = sorted(dup_heroes - KNOWN_RP_DUPS)
    missing_expected_dups = sorted(KNOWN_RP_DUPS - dup_heroes)
    if unexpected_dups:
        print(f"⚠ unexpected rune-priority duplicates (not in known 10): "
              f"{', '.join(unexpected_dups)}")
    if missing_expected_dups:
        print(f"⚠ expected rune-priority dup missing a 2nd row: "
              f"{', '.join(missing_expected_dups)}")

    missing_avatars = sorted(c for c in canon_names if chars[c]["avatar"] is None)
    missing_skills = sorted(c for c in canon_names if not chars[c]["skill_profile"])

    print(f"characters: {len(canon_names)}")
    print(f"  with rune_note:     {sum(1 for c in canon_names if chars[c]['rune_note'])}")
    print(f"  with rune_priority: {sum(1 for c in canon_names if chars[c]['rune_priority'])}")
    print(f"  with skill_profile: {sum(1 for c in canon_names if chars[c]['skill_profile'])}")
    print(f"  rune-priority dups: {len(dup_heroes)} (known {len(KNOWN_RP_DUPS)})")
    print(f"  missing avatars:    {len(missing_avatars)}")
    print(f"  missing skills:     {len(missing_skills)}")

    out = {
        "fetched_at": int(time.time()),
        "source": tier.get("source"),
        "columns": tier.get("columns", []),
        "impact_tiers": runenotes.get("impact_tiers", []),
        "priorities": runepri.get("priorities", []),
        "characters": [chars[n] for n in canon_names],
        "missing_skills": missing_skills,
        "unmatched_names": [u["name"] for u in unmatched],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size:,} bytes)")

    if unmatched:
        print(f"\n✗ {len(unmatched)} unmatched source name(s) — add an ALIASES "
              f"entry for each, then re-run:", file=sys.stderr)
        for u in unmatched:
            print(f"    [{u['sheet']}] {u['name']!r}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
