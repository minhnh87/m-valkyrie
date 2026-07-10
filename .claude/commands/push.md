---
description: Deploy omnihero — pull latest in the nos1hahaha.bitbucket.io pages repo, copy index.html + assets/ in, then commit & push master (scoped to omnihero/)
allowed-tools: Bash(cp:*), Bash(rsync:*), Bash(git:*), Bash(mkdir:*), Bash(echo:*), Bash(date:*), Bash(test:*), Bash(rm:*)
---

Deploy the Omniheroes single-page site to the `nos1hahaha.bitbucket.io` Bitbucket Pages repo.

Run the script below in **one** Bash call, then report the outcome to the user:
- on success: the short commit hash that was pushed,
- on no-op: "nothing to deploy",
- on failure (auth/network/etc.): the error verbatim — do **not** retry destructively.

```bash
set -euo pipefail

SRC="/Users/minh/www/git/personal/tools/m-valkyrie"
DEST="/Users/minh/www/git/personal/minh/nos1hahaha.bitbucket.io"
OUT="$DEST/omnihero"

# guard: never deploy from a missing/empty source (rsync --delete would wipe target)
test -f "$SRC/index.html"  || { echo "✗ missing $SRC/index.html";  exit 1; }
test -d "$SRC/assets"      || { echo "✗ missing $SRC/assets";      exit 1; }
test -d "$DEST/.git"       || { echo "✗ $DEST is not a git repo";  exit 1; }

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
  git -C "$DEST" commit -m "omnihero: deploy $(date '+%Y-%m-%d %H:%M')"
  git -C "$DEST" push origin master
  echo "Deployed: $(git -C "$DEST" rev-parse --short HEAD)"
fi
```
