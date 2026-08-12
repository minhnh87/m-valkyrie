---
description: Ship omnihero — commit & push the m-valkyrie source to GitHub (pull --rebase first), then deploy index.html + assets/ into the nos1hahaha.bitbucket.io pages repo and push master (scoped to omnihero/)
allowed-tools: Bash(cp:*), Bash(rsync:*), Bash(git:*), Bash(mkdir:*), Bash(echo:*), Bash(date:*), Bash(test:*), Bash(rm:*), Bash(ls:*)
---

Ship the Omniheroes site. Two repos, in this order:

1. **Source** — `m-valkyrie` → GitHub `origin/main`.
2. **Deploy** — the built `index.html` + `assets/` → `nos1hahaha.bitbucket.io` `origin/master`, under `omnihero/`.

Source goes first so the deployed commit always exists upstream and the deploy
message can point back at it. If step 1 fails, **stop** — do not deploy an
unpushed tree.

## Step 1 — read the changes

Run this first (read-only) to see what is being shipped:

```bash
cd /Users/minh/www/git/personal/tools/m-valkyrie
git status --short
echo "--- staged+unstaged stat ---"
git diff HEAD --stat
```

If it reports nothing, skip to Step 3 — the source is already pushed, but the
pages repo may still be behind.

## Step 2 — write the commit message, then push the source

Compose the message yourself from the diff above; do **not** use a generic
"update" subject. Match the repo's existing style:

- Conventional commit: `feat(scope): …`, `fix(scope): …`, `chore(scope): …`
  (scopes in use: `relics`, `skills`, `endgame`, `tier-list`, `runes`, `build`).
- Subject on one line, imperative, specific about *what changed in the data or
  the UI* — e.g. `feat(endgame): sync tier moves + add About block to hero profile`.
- Add a body when the change needs a why (data source moved, a trap avoided, a
  decision that isn't obvious from the diff). Skip the body for small ones.
- End with the trailer `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

`.clsessions/` and `.playwright-mcp/` were untracked on 2026-08-12
(`git rm -r --cached`), so `.gitignore` now actually holds and `git add -A`
stages code + data only. If either dir ever shows up in the diff again,
something re-added it — untrack it rather than committing session churn.

Then run the whole block in **one** Bash call, with your message in the heredoc:

```bash
set -euo pipefail

SRC="/Users/minh/www/git/personal/tools/m-valkyrie"

test -d "$SRC/.git" || { echo "✗ $SRC is not a git repo"; exit 1; }
BRANCH="$(git -C "$SRC" rev-parse --abbrev-ref HEAD)"
test "$BRANCH" = "main" || { echo "✗ on branch '$BRANCH', expected main — resolve manually"; exit 1; }

if [ -z "$(git -C "$SRC" status --porcelain)" ]; then
  echo "Source: nothing to commit."
else
  git -C "$SRC" add -A
  git -C "$SRC" commit -F - <<'MSG'
feat(scope): REPLACE THIS with the subject you composed

REPLACE or delete this body.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
fi

# pull BEFORE pushing — rebase our commit on top of anything upstream.
# Fails loudly on a conflict: report it verbatim, never force-push.
git -C "$SRC" pull --rebase origin main
git -C "$SRC" push origin main
echo "Source pushed: $(git -C "$SRC" rev-parse --short HEAD)"
```

## Step 3 — deploy to the pages repo

Run this in **one** Bash call:

```bash
set -euo pipefail

SRC="/Users/minh/www/git/personal/tools/m-valkyrie"
DEST="/Users/minh/www/git/personal/minh/nos1hahaha.bitbucket.io"
OUT="$DEST/omnihero"

# guard: never deploy from a missing/empty source (rsync --delete would wipe target)
test -f "$SRC/index.html"  || { echo "✗ missing $SRC/index.html";  exit 1; }
test -d "$SRC/assets"      || { echo "✗ missing $SRC/assets";      exit 1; }
test -d "$DEST/.git"       || { echo "✗ $DEST is not a git repo";  exit 1; }

# guard: index.html is generated from templates-mobile/ — refuse to ship a build
# that predates a template edit (silently deploying stale HTML is the footgun here)
for f in "$SRC"/templates-mobile/*; do
  if [ "$f" -nt "$SRC/index.html" ]; then
    echo "✗ $(basename "$f") is newer than index.html — run: python3 scripts/build_mobile.py"
    exit 1
  fi
done

# 0. pull latest BEFORE touching the tree — never commit/push on a stale master
#    (fails loudly on conflicts or a dirty tree; report verbatim, don't force)
git -C "$DEST" pull --rebase origin master

mkdir -p "$OUT"

# 1. copy the single-page app (index.html is the only user-facing file now)
cp "$SRC/index.html" "$OUT/index.html"

# 1b. drop the retired mobile.html if it's still in the deployed tree
rm -f "$OUT/mobile.html"

# 2. mirror assets/ — add new (incl. skills/), drop stale, skip .DS_Store
rsync -a --delete --exclude '.DS_Store' "$SRC/assets/" "$OUT/assets/"

# 3. stage ONLY the omnihero folder (-A so the mobile.html removal is staged too)
git -C "$DEST" add -A omnihero

# 4. commit + push master only when something actually changed
if git -C "$DEST" diff --cached --quiet; then
  echo "Nothing to deploy — omnihero already up to date."
else
  git -C "$DEST" commit -m "omnihero: deploy $(git -C "$SRC" rev-parse --short HEAD) ($(date '+%Y-%m-%d %H:%M'))"
  git -C "$DEST" push origin master
  echo "Deployed: $(git -C "$DEST" rev-parse --short HEAD)"
fi
```

## Reporting

Report both halves to the user:
- source: the short hash pushed, or "nothing to commit",
- deploy: the short hash pushed, or "nothing to deploy",
- on failure (auth/network/rebase conflict): the error **verbatim**, say which
  step it broke on, and stop — do not retry destructively, do not force-push.
