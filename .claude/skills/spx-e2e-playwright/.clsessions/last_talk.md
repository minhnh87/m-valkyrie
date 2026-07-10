# Last Talk - spx-e2e-playwright
Updated: 20260704_220010
Mode: bypassPermissions

---

## User

/btw, install playwright luôn

---

## Claude

Done. Playwright is installed and wired up.

## What I did
- **Registered the Playwright MCP server** at **user scope** (works in every project, not just this one):
  `claude mcp add playwright -s user -- npx -y @playwright/mcp@latest` → written to `~/.claude.json`, and `claude mcp list` reports it **✔ Connected**.
- **Downloaded Chromium** (+ headless shell) into `~/Library/Caches/ms-playwright/` — the browser the MCP drives.
- Saved a memory note so future sessions know it's available for visual verification.

## ⚠️ One step needed on your side
The `browser_*` tools aren't in *this* session yet — Claude Code only loads MCP tools **at session start**. **Restart Claude Code** (or start a new session) and they'll appear.

## After restart
I'll be able to actually drive the browser to verify UI — e.g. open the built app, resize to a phone width (390×844), switch to **Relics → Tier List**, and screenshot to confirm the grade columns (MSN…PVP) now fit. The `/spx-e2e-playwright` skill also becomes usable then. Want me to run that mobile-viewport check on the Relics fix once you've restarted?

To undo anytime: `claude mcp remove playwright -s user`.

---

