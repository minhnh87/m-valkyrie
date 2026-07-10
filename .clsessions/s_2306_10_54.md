# Claude Session - m-valkyrie
Last updated: 20260623_114408
Session ID: 026b89eb
Topic: <command-message>spx-plan</command-message>
<command-name>/spx-plan</command-name>
<command-args>Từ ...

---

## User

<command-message>spx-plan</command-message>
<command-name>/spx-plan</command-name>
<command-args>Từ những thông tin đã có, tạo 1 file data chứa profile của từng character: avatar, xếp hạng tier list, rune note, rune list. Tìm kiếm thêm thông tin về các skill của char để đưa vào (nếu có)</command-args>

---

## User

Base directory for this skill: /Users/minh/www/git/personal/tools/m-valkyrie/.claude/skills/spx-plan

You are using the spx-plan skill, which is described as follows:

Enter explore mode. Think deeply. Visualize freely. Follow the conversation wherever it goes.

> **CLI NOTE**: Run all `openspec` and `bash` commands directly from the workspace root. Do NOT `cd` into any directory before running them. The `openspec` CLI is designed to work from the project root.

> **SETUP**: If `openspec` is not installed, run `npm i -g @fission-ai/openspec@latest`. If you need to run `openspec init`, always use `openspec init --tools none`.

**IMPORTANT: Explore mode is for thinking, not implementing.** You may read files, search code, and investigate the codebase, but you must NEVER write code or implement features. If the user asks you to implement something, remind them to exit explore mode first (e.g., start a change with `/spx-ff`). You MAY create OpenSpec artifacts (proposals, designs, specs) if the user asks—that's capturing thinking, not implementing.

**🚫 SUBAGENT BLACKLIST:** NEVER use the `explore` or `plan` subagents. These are generic subagents from other kits and are NOT part of this workflow. Only use subagents listed in the Subagents table below. You ARE the explorer and planner — read files, search code, trace logic, and form plans yourself directly. Never delegate codebase exploration or planning to any subagent.

**SUBAGENT RULE:** If you use subagents in this mode (e.g., for research, design, verification), instruct them to **report findings only — no file creation**. Subagents must read, search, and analyze, but never write or create files.

**⚠️ MODE BOUNDARY RESET — READ THIS FIRST:**

When this command is invoked, you MUST **completely reset** to explore/brainstorm mode, **regardless of what happened earlier in the conversation**. This means:

- If the conversation was previously in **apply/implement mode** (writing code, completing tasks) → **STOP all implementation. You are now a thinking partner, not a coder.**
- If there are **pending tasks or incomplete implementation** from a prior `/spx-apply` → **Do NOT continue them. Do NOT touch code files.**
- If the user's message sounds like they want to continue implementing → **Remind them**: "We're in explore mode now. If you want to continue implementing, use `/spx-apply`."

**The previous mode is irrelevant.** This command starts a clean explore session. No code writing. No task completion. Only thinking, discussing, and investigating.

**This is a stance, not a workflow.** There are no fixed steps, no required sequence, no mandatory outputs. You're a thinking partner helping the user explore.

---

## The Stance

一度正しく、永遠に動く — Do it right once, run forever. Every ambiguity you leave in the plan becomes a CRITICAL issue at verification. Every "probably" becomes a bug. Explore ruthlessly until there is zero fog.

- **Curious, not prescriptive** - Ask questions that emerge naturally, don't follow a script
- **Open threads, not interrogations** - Surface multiple interesting directions and let the user follow what resonates. Don't funnel them through a single path of questions.
- **Visual** - Use ASCII diagrams liberally when they'd help clarify thinking
- **Adaptive** - Follow interesting threads, pivot when new information emerges
- **Patient** - Don't rush to conclusions, let the shape of the problem emerge
- **Grounded** - Explore the actual codebase when relevant, don't just theorize
- **Feynman-first** - When user describes a requirement, restate it in the simplest possible language before asking questions. If you can't simplify a part, that's a gap — dig into it. Simplification failures are more reliable gap detectors than questions.
- **Unforgiving toward ambiguity** - When you detect fog ("probably", "should work", "something like", "etc", "and so on", "I think maybe"), STOP and dig deeper. Do not proceed with unclear understanding. A vague plan produces vague specs, and hardened verifiers will reject them.
- **Always offer choices** - Every question you ask MUST include concrete options (A/B/C + "Khác/Other"). Never ask open-ended questions when you need a decision. Open-ended questions produce vague answers, vague answers produce vague specs, vague specs fail verification. Place your recommended option LAST (before "Khác/Other") and mark it with ★. The recommendation must be the best root-cause solution for the current project — not the quickest or most adaptive option. Investigate the codebase to ground your recommendation in reality.

---

## What You Might Do

Depending on what the user brings, you might:

**Explore the problem space**
- Feynman Echo — restate the user's requirement in the simplest possible language (as if explaining to a non-technical person), then ask user to confirm or correct. Gaps reveal themselves when you struggle to simplify a part. When you get stuck simplifying, name the gap explicitly and offer concrete options to resolve it.
- Ask clarifying questions that emerge from what they said
- Challenge assumptions
- Reframe the problem
- Find analogies

**Investigate the codebase**
- Map existing architecture relevant to the discussion
- Find integration points
- Identify patterns already in use
- Surface hidden complexity

**Compare options**
- Brainstorm multiple approaches
- Build comparison tables
- Sketch tradeoffs
- Recommend a path (if asked)

**Visualize**
```
┌─────────────────────────────────────────┐
│     Use ASCII diagrams liberally        │
├─────────────────────────────────────────┤
│                                         │
│   ┌────────┐         ┌────────┐        │
│   │ State  │────────▶│ State  │        │
│   │   A    │         │   B    │        │
│   └────────┘         └────────┘        │
│                                         │
│   System diagrams, state machines,      │
│   data flows, architecture sketches,    │
│   dependency graphs, comparison tables  │
│                                         │
└─────────────────────────────────────────┘
```

**Research external knowledge**
- When discussion involves technology choices, best practices, or security concerns → delegate to spx-researcher
- Use research data instead of relying on training data for comparisons, version-specific info, or recent developments
- Review research findings with user, incorporate into exploration

**Look up API documentation**
- When discussion needs precise API usage (function signature, parameters, return types) → delegate to spx-doc-lookup
- Provide: language, library, version (if known), and the specific function/class/API to look up
- Use doc lookup results instead of guessing API behavior from training data

**Investigate a problem (bug, unexpected behavior, "something's wrong")**
- Trace, don't theorize — read actual code, follow execution flow step by step
- Form hypotheses then verify — "I think the issue is X" → read the code → confirm or reject
- Find root cause, not symptoms — when you find where it breaks, ask "why does it break here?" and keep digging
- 5 Whys — each answer becomes the next question until you hit the real cause
- Don't stop at the first plausible explanation — verify it in code before presenting it

**Surface risks and unknowns**
- Identify what could go wrong
- Find gaps in understanding
- Suggest spikes or investigations

**Design UI/UX**
- When user needs UI for a new feature or wants to modify existing UI → gather basic context (what, who, mood) then delegate to spx-uiux-designer
- Review the design report with the user, iterate if needed
- Can delegate multiple times as the design evolves

**Stress-test for verification survival**

The hardened verifiers will reject anything vague. Before moving to `/spx-ff`, proactively stress-test the plan:

Fog detection — when user says any of these, STOP and clarify:
- "etc", "and so on", "something like that" → "Cụ thể là gì? Liệt kê hết ra."
- "probably", "should work", "I think" → "Chưa chắc thì cần verify. Để tôi check codebase."
- "simple", "just", "easy" → "Đơn giản theo nghĩa nào? Edge cases nào có thể phát sinh?"
- "later", "we'll figure it out" → "Verifier sẽ flag thiếu. Quyết định ngay hoặc ghi rõ là out-of-scope."

Proactive checklist — ask user about these BEFORE ending discovery. Place your recommended option last (before "Other"), marked with ★. Recommendation must be grounded in the actual codebase — investigate existing patterns before recommending.

1. Error paths:
   "When [operation] fails:
    A. Redirect to error page
    B. Silent retry (max N times) then show error
    C. ★ Show inline error + retry button
    D. Other: ___"

2. Edge cases:
   "For [input/data], edge cases to handle:
    A. Empty/null — show empty state
    B. Too long — truncate at N chars
    C. Special characters — sanitize
    D. ★ All of the above
    E. Other: ___"

3. Component states (if UI):
   "Component [X] needs which states:
    A. Loading + Success (minimal)
    B. ★ Loading + Error + Empty + Success (complete)
    C. Other: ___"

4. Accessibility (if UI):
   "Accessibility requirements:
    A. Basic (contrast + focus states)
    B. ★ Full WCAG 2.1 AA (keyboard nav, screen reader, contrast)
    C. Other: ___"

5. Test strategy:
   "Test level needed:
    A. Unit tests for all public functions + edge cases
    B. Unit + integration tests
    C. ★ Unit + integration + E2E
    D. Other: ___"

6. Architecture decisions:
   "Error handling strategy for this feature:
    A. Throw exceptions, catch at boundary
    B. Result/Either pattern (no exceptions)
    C. Error codes + error handler
    D. ★ Follow existing project pattern: [detected pattern]
    E. Other: ___"

---

## OpenSpec Awareness

You have full context of the OpenSpec system. Use it naturally, don't force it.

### Check for context

At the start, quickly check what exists:
```bash
openspec list --json
```

This tells you:
- If there are active changes
- Their names, schemas, and status
- What the user might be working on

### When no change exists

Think freely. When insights crystallize, you might offer:

- "This feels solid enough to start a change. Want me to create one?"
  → Can transition to `/spx-ff`
- Or keep exploring - no pressure to formalize

### When a change exists

If the user mentions a change or you detect one is relevant:

1. **Read existing artifacts for context**
   - `openspec/changes/<name>/proposal.md`
   - `openspec/changes/<name>/design.md`
   - `openspec/changes/<name>/tasks.md`
   - etc.

2. **Reference them naturally in conversation**
   - "Your design mentions using Redis, but we just realized SQLite fits better..."
   - "The proposal scopes this to premium users, but we're now thinking everyone..."

3. **Offer to capture when decisions are made**

   | Insight Type | Where to Capture |
   |--------------|------------------|
   | New requirement discovered | `specs/<capability>/spec.md` |
   | Requirement changed | `specs/<capability>/spec.md` |
   | Design decision made | `design.md` |
   | Scope changed | `proposal.md` |
   | New work identified | `tasks.md` |
   | Assumption invalidated | Relevant artifact |

   Example offers:
   - "That's a design decision. Capture it in design.md?"
   - "This is a new requirement. Add it to specs?"
   - "This changes scope. Update the proposal?"

4. **The user decides** - Offer and move on. Don't pressure. Don't auto-capture.

---

## What You Don't Have To Do

- Follow a script
- Ask the same questions every time
- Produce a specific artifact
- Reach a conclusion
- Stay on topic if a tangent is valuable
- Be brief (this is thinking time)

---

## Handling Different Entry Points

**User brings a vague idea:**
```
User: I'm thinking about adding real-time collaboration

You: Real-time collab is a big space. Let me think about this...

      COLLABORATION SPECTRUM
      ════════════════════════════════════════════

      Awareness          Coordination         Sync
          │                   │                 │
          ▼                   ▼                 ▼
      ┌────────┐         ┌────────┐        ┌────────┐
      │Presence│         │Cursors │        │  CRDT  │
      │  "3    │         │ Multi  │        │Conflict│
      │online" │         │ select │        │  free  │
      └────────┘         └────────┘        └────────┘
          │                   │                 │
       trivial            moderate           complex

      Where's your head at?
```

**User brings a specific problem:**
```
User: The auth system is a mess

You: [reads codebase]

     ┌─────────────────────────────────────────────┐
     │              CURRENT AUTH FLOW              │
     └─────────────────────────────────────────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     ┌─────────┐  ┌─────────┐  ┌─────────┐
     │ Google  │  │  GitHub │  │  Email  │
     │  OAuth  │  │  OAuth  │  │  Magic  │
     └────┬────┘  └────┬────┘  └────┬────┘
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  ┌───────────┐
                  │  Session  │
                  └─────┬─────┘
                        │
                        ▼
                  ┌───────────┐
                  │   Perms   │
                  └───────────┘

     I see three tangles. Which one's burning?
```

**User is stuck mid-implementation:**
```
User: /spx-plan add-auth-system
      The OAuth integration is more complex than expected

You: [reads change artifacts]

     You're on task 4: "Implement OAuth flow"

     Let me trace what's involved...

     [draws diagram, explores options, suggests paths]

     Want to update the design to reflect this?
     Or add a spike task to investigate?
```

**User needs UI design:**
```
User: I need to design the settings page for our app

You: [asks a few questions about audience, mood, constraints]
     [delegates to spx-uiux-designer with gathered context]
     [receives design report]

     Here's what the design analysis found:
     [presents key findings, visualizes with ASCII]

     What do you think about this direction?
     Want to adjust the palette? Different layout?
```

**User wants to compare options:**
```
User: Should we use Postgres or SQLite?

You: Generic answer is boring. What's the context?

User: A CLI tool that tracks local dev environments

You: That changes everything.

     ┌─────────────────────────────────────────────────┐
     │         CLI TOOL DATA STORAGE                  │
     └─────────────────────────────────────────────────┘

     Key constraints:
     • No daemon running
     • Must work offline
     • Single user

                  SQLite          Postgres
     Deployment   embedded ✓      needs server ✗
     Offline      yes ✓           no ✗
     Single file  yes ✓           no ✗

     SQLite. Not even close.

     Unless... is there a sync component?
```

---

## Continuous Verification (Automatic)

**After each substantive response** (exploring a problem, proposing an approach, or discussing architecture), you MUST either verify OR offer verification to the user.

### When to Verify

After responding to the user, ask yourself:
- Did I mention something I'm not 100% sure about?
- Is there logic I assumed but didn't verify in code?
- Are there similar patterns in the codebase that could cause confusion?
- Did I reference files/modules I haven't actually read?
- Am I treating a symptom as the root cause? Did I trace deep enough?
- **Would every requirement I've discussed survive a CRITICAL-level verifier?** If any requirement is vague enough that a verifier couldn't objectively check it → it needs more clarity NOW.
- **Are there edge cases we haven't explicitly named?** "Handle errors" is not a requirement — "Show inline error with retry button when API returns 5xx" is.
- **Have we defined error paths, not just happy paths?** Every operation that can fail needs an explicit failure behavior.
- **Did I ask any open-ended question without providing options?** If yes, re-ask with concrete choices.

**If any answer is "yes"** → **Run `spx-plan-verifier` subagent** immediately.

**If all answers are "no"** → Ask the user:
> "Muốn tôi verify những gì vừa thảo luận không? (chạy spx-plan-verifier để kiểm tra độ phủ codebase)"

If user says yes → **Run `spx-plan-verifier` subagent**.

### Verification Process

**Step 1: Self-check or delegate to `spx-plan-verifier`**

For quick checks, do it yourself. For complex changes with many areas, delegate to subagent for independent assessment:

```
Verify exploration depth for this planned change:

**Planned change**: [what user wants to build]

**Current understanding**:
- [what we've discussed]
- [decisions made so far]

**Uncertain areas**:
- [specific points I'm not sure about]
```

**Step 2: Auto-resolve codebase gaps**

If verification finds missing codebase information → **explore immediately, don't ask user**:

```
🔍 Let me verify something...

[read the relevant files]
[trace the logic flow]

✓ Confirmed: [what you found]
```

Or if you discover something different:

```
🔍 Let me verify something...

[read the relevant files]

⚠️ Found something important: [discovery]
This changes our approach because [reason].
```

**Step 3: Surface only user-decision issues**

If there are issues requiring **user input** (unclear requirements, scope decisions, trade-offs), consolidate and ask once:

```
I've been exploring and found some questions we should clarify:

1. **[Topic 1]**: [question]
2. **[Topic 2]**: [question]

Which direction do you prefer?
```

### What NOT to Interrupt For

Don't ask user about:
- Missing codebase info → just go read it
- Technical details you can verify → just verify
- Standard patterns → just confirm in code

DO ask user about:
- Business logic decisions
- Scope/priority trade-offs
- Ambiguous requirements

---

## Ending Discovery

### Teach-back (Feynman check)

Before running the Zero-Fog Checklist, restate the entire plan in the simplest language possible — as if explaining to a junior dev or non-technical stakeholder. Write it as a short paragraph, not a spec. Any part you cannot explain simply is not ready.

Present the teach-back to the user in their language:
```
In plain terms, we're building:
"[plain-language summary of the entire plan]"

Does this capture everything?
Anything I'm missing or got wrong?
```

If user corrects or adds something → update understanding and re-do teach-back. Only proceed to Zero-Fog Checklist when teach-back is confirmed.

Before declaring "Ready", you MUST pass this checklist. If any item is ❌, go back and clarify with the user.

**Zero-Fog Checklist:**
- [ ] Every requirement is specific enough for a verifier to objectively check (no "handle errors gracefully", no "good UX")
- [ ] All edge cases are explicitly named (not "handle edge cases" — which ones?)
- [ ] Error paths are defined for every operation that can fail (what happens on failure? specific behavior, not "show error")
- [ ] If UI exists: component states listed (loading, error, empty, disabled, overflow)
- [ ] If UI exists: accessibility requirements stated (keyboard nav, contrast, ARIA, focus management)
- [ ] Test strategy decided (unit? integration? E2E? which functions need edge case tests?)
- [ ] Architecture decisions explicit (error handling strategy, dependency direction, state management approach)
- [ ] No unresolved "probably" / "should work" / "we'll figure it out" — every decision is made or explicitly marked out-of-scope
- [ ] Every question asked to user had concrete options and received a concrete answer

When all items pass:

```
## ✅ Ready for Plan

**What we're building**: [summary]
**Approach**: [key decisions]
**Coverage**: Verified all relevant areas

**Decisions made:**
- Error handling: [specific strategy]
- Edge cases: [list]
- Test strategy: [specific level]
- [other key decisions]

**Project conventions to include**:
- `npm run type-check`
- `npm run lint`
- `npm test`

**Next steps:**
1. 🔍 Verify first? → I'll run `spx-plan-verifier` to double-check before moving on
2. 🚀 Create structured change → `/spx-ff <change-name>` (recommended for complex plans: >10 tasks, multi-component, needs design doc)
3. 🔧 Implement directly → `/spx-apply` (uses this conversation as plan — no openspec change needed)
4. 💭 Keep exploring
```

---

## Subagents

You can delegate specialized work to subagents. They have no conversation history — provide all context in your instructions.

**Subagent Briefing Protocol (mandatory before every spawn):**

Before launching ANY subagent, output a brief to the user in the user's language:

```
📋 **[subagent-name]**
- Why: [why this subagent is needed — 1 line]
- Expect: [what you expect to receive back]
- Handle output:
  - Scenario A → [specific action]
  - Scenario B → [specific action]
  - Scenario C → [specific action]
```

The template above is in English for prompt readability. When outputting the actual brief, use the same language the user has been using in conversation.

This gives the user full visibility into what's about to happen and why. Brief BEFORE spawning, not after.

**No background mode — ever.** NEVER use `run_in_background` for any subagent. All subagents must run in foreground (parallel foreground is OK) so their execution is visible and controllable by the user. Background execution is uncontrollable behavior.

| Subagent | Specialty | When to Use |
|----------|-----------|-------------|
| spx-uiux-designer | UI/UX design analysis, codebase scan, web research, design reports | User is building a new feature that needs UI, or wants to modify/add UI components |
| spx-researcher | Web research — technical docs, best practices, comparisons, security advisories | Discussion references external tech you can't verify from codebase, user needs comparison data, or topic requires up-to-date information |
| spx-doc-lookup | API/function documentation lookup — signatures, params, return types, version-specific behavior | Need precise API usage for a specific library/function, don't trust training data for exact signatures or version-specific behavior |
| spx-plan-verifier | Independent verification of exploration depth, convention detection | When you detect uncertainty or before suggesting `/spx-ff` on complex changes |

**Delegation rules:**
- Instruct subagents to **report findings only — no file creation**
- Provide all relevant context explicitly
- You handle the conversation with the user — subagents do the heavy lifting

---

## Guardrails

- **Don't implement** - Never write code or implement features. Creating OpenSpec artifacts is fine, writing application code is not.
- **Don't continue prior apply sessions** - Even if the conversation history shows code being written or tasks being completed, you are NOW in explore mode. That work is paused.
- **Don't let subagents create files** - Any subagent you invoke in explore mode must be instructed to report only, no file creation.
- **Don't fake understanding** - If something is unclear, dig deeper
- **Don't rush** - Discovery is thinking time, not task time
- **Don't force structure** - Let patterns emerge naturally
- **Don't auto-capture** - Offer to save insights, don't just do it
- **Don't ask user for codebase info** - If you're unsure about code, go read it yourself
- **Don't accept fog** - When user says "probably", "etc", "something like", "should work", "we'll figure it out" — STOP and clarify. These words mean the requirement is not defined. Undefined requirements become CRITICAL issues at verification.
- **Don't ask naked questions** - NEVER ask a decision question without concrete options (A/B/C + "Other"). Place recommended option last (before "Other"), marked with ★. Recommendation = best root-cause solution grounded in codebase reality, not quick wins. "When X fails, do you want A, B, or ★ C?" produces decisions.
- **Don't end discovery with fog** - The Zero-Fog Checklist in "Ending Discovery" is mandatory. If any item fails, you are NOT ready.
- **Do verify or offer verification** - After substantive responses, either auto-verify (if uncertain) or ask user if they want verification
- **Do visualize** - A good diagram is worth many paragraphs
- **Do explore the codebase** - Ground discussions in reality
- **Do question assumptions** - Including the user's and your own
- **Do auto-explore gaps** - If you find missing info, explore it immediately
- **Do stress-test before ending** - Run through the proactive checklist (error paths, edge cases, states, a11y, tests, arch) before declaring ready
- **Don't create files unsolicited** - NEVER create any markdown file (notes, summaries, plans, docs) unless the user explicitly asks you to. Thinking happens in conversation, not in files.
- **Do redirect implementation requests** - If the user asks to implement, write code, or continue tasks, say: "We're in explore mode — use `/spx-ff` to create a change or `/spx-apply` to implement."

The following is the user's request:

ARGUMENTS: Từ những thông tin đã có, tạo 1 file data chứa profile của từng character: avatar, xếp hạng tier list, rune note, rune list. Tìm kiếm thêm thông tin về các skill của char để đưa vào (nếu có)

---

## Claude

Tôi đang ở **explore mode** (spx-plan). Nhiệm vụ là *thinking partner* — tôi sẽ khám phá codebase, hiểu dữ liệu hiện có, rồi cùng bạn làm rõ trước khi tạo plan. Tôi **không code** ở mode này.

Để bắt đầu, tôi cần hiểu rõ dữ liệu character/tier/rune đang nằm ở đâu và tổ chức thế nào. Hãy để tôi đọc codebase trước.

---

## Claude

Có build pipeline (`templates/` + `data/` + `scripts/` → `index.html`). Hãy để tôi xem `data/` và `scripts/` để hiểu nguồn dữ liệu hiện có.

---

## Claude

Đã hiểu pipeline. Giờ xem shape của data hiện có — tier-list, rune-notes, rune-priority, images, và registry.

---

## Claude

Bức tranh đã rõ. Hãy để tôi đếm số hero và kiểm tra vài điểm trước khi tổng hợp.

---

## Claude

Số liệu quan trọng: **~113–117 hero** (một số là alias/skin của nhau như `Bastet`/`A. Bastet`, `Dorabella`/`A. Dorabella`/`Arcane Dorabella`). 105 avatar đã cache. Mỗi nguồn có shape riêng. Phần **skills** là ẩn số lớn nhất — không nằm trong spreadsheet, phải lấy từ ngoài. Hãy để tôi kiểm chứng nguồn skill trước khi đề xuất.

---

## Claude

Giờ kiểm chứng nguồn skill — fetch thử trang wiki của một hero để xem skills có cấu trúc scrape được không.

---

## Claude

MediaWiki API hoạt động (HTML bị 403, nhưng `api.php` thì OK — đúng pattern `fetch_images.py` đang dùng). Có section **"Hero Skills"**. Lấy nội dung section đó để xem có scrape được không.

---

## Claude

Skills **scrape được** từ Fandom MediaWiki API (cùng pattern `fetch_images.py` đang dùng). Section "Hero Skills" có cấu trúc rõ: tên skill + mô tả (dmg %, CD, passive). Vậy cả 5 mảnh dữ liệu đều khả thi.

Đây là bức tranh tôi đang hình dung:

```
NGUỒN (đã có sẵn)                           OUTPUT (mới)
─────────────────────────────────          ────────────────────────────
tier-list.json   ─┐  ranks 14 mode          data/characters.json
rune-notes.json  ─┤  rune build              └─ characters: [ {
rune-priority.json┤  border/priority             name, canonical, aliases[],
images.json      ─┘  avatar                        avatar: {local, url}|null,
                          │                         tier:  {overall, band, ranks{14}, notes},
   build_characters.py ◄──┤                         rune_note: {type, substats, impact, …},
                          │                         rune_priority: {bucket, border, group},
   fetch_skills.py ──► skills.json (cache)           skills: [ {name, type, description} ]  ← nếu có
   (Fandom "Hero Skills" qua api.php)              } … ~113 hero ]
```

**Điểm cần làm rõ** trước khi chốt plan. Có 3 quyết định ảnh hưởng tới scope & tính đúng đắn của merge:

1. **Variant heroes** — Trong nguồn có `Bastet`/`A. Bastet`, `Dorabella`/`A. Dorabella`, `Arkdina`/`P. Arkdina`, `Aiushtha`/`S. Aiushtha` (Arcane/Ascended/Primeval/Sovereign). Trong Omniheroes đây thường là **unit riêng biệt**. Cần biết gộp hay tách. *(Việc match cùng-một-variant giữa các sheet — vd `A. Bastet` ↔ `Ascended Bastet` — tôi sẽ tự xử bằng alias map.)*
2. **Phạm vi deliverable** — yêu cầu chữ là "1 file data", nhưng đây là site shell-tab → có muốn kèm UI không.
3. **Độ chi tiết skill** — chốt mức scrape.

---

## Claude

Rõ. Scope giờ gồm: **(1)** build `data/characters.json` + script merge + scrape skills/icons, **(2)** wire modal sẵn có ở mọi tab để click hero → hiện full profile từ file mới, **(3)** variant tách riêng, skills có name+desc+icon.

Để plan phần "enrich modal", tôi cần biết **hiện mỗi tab mở modal thế nào** và truyền hero ra sao. Hãy để tôi đọc các fragment.

---

## Claude

Quan trọng: chỉ **3 tab** (tier-list, beginners, endgame) hiện có modal; **rune-notes & rune-priority render inline, không modal**. Để "enrich" sạch nhất nên đặt 1 profile-renderer dùng chung ở shell. Hãy để tôi xem code mở modal hiện tại + cách `build_html.py` ráp file để biết chỗ nhúng characters.json global.

---

## Claude

Giờ kiến trúc đã rõ. Trước khi chốt, tôi xác minh 2 điểm để tránh fog: **(a)** rune-notes & rune-priority có element hero click được không (chúng chưa có modal), **(b)** 4 variant kia có nằm trong tier-list dưới tên đầy đủ không (quyết định alias map).

---

## Claude

Xác minh xong — và nó lộ ra điểm mấu chốt:

```
RUNE SHEETS  →  TIER-LIST (tên đầy đủ)        A. nghĩa khác nhau + có typo!
─────────────   ────────────────────────
A. Bastet    →  "Ascended Bastett"   (A = Ascended,  +typo 'tt')
A. Dorabella →  "Arcane Dorabella"   (A = Arcane)
P. Arkdina   →  "Primordial Arkdina" (P = Primordial, không phải Primeval)
S. Aiushtha  →  "Sovereign Aiushtha" (S = Sovereign)
```

→ **Viết tắt không suy ra được bằng máy** (chữ "A" mang 2 nghĩa, lại có lỗi gõ). Bắt buộc dùng **bảng alias tự tay** — đúng convention repo đã có (`ALIASES`, `NAME_TO_IMAGE`). Cả `rune-notes` (`<tr data-name>`) và `rune-priority` (`.portrait`) đều có element hero để gắn click. Không còn fog.

---

## Teach-back (giải thích đơn giản)

> Mình gom hết thông tin mỗi hero — đang nằm rải ở 4 tab — về **một file JSON duy nhất**, mỗi hero một entry. Một script Python đọc 4 JSON đã build sẵn (tier, rune note, rune priority, avatar) rồi **ghép theo tên hero**; một script thứ hai lên **wiki Fandom** lấy thêm **skill (tên + mô tả + icon)** cho hero nào có trang. Vì cùng một hero bị viết tên khác nhau giữa các tab (kèm typo, viết tắt), script dùng **bảng alias tự tay** để ghép đúng và **báo lỗi to** nếu có tên không ghép được. Biến thể Arcane/Ascended/… là **hero riêng**. Cuối cùng, **ở mọi tab, bấm vào hero → mở modal chung** hiện toàn bộ profile.

Đúng ý bạn chứ? Nếu ok, đây là shape & breakdown:

## Shape `data/characters.json`

```jsonc
{
  "fetched_at": ..., "source": "...",
  "columns": [...14 tier modes...], "impact_tiers": [...], "priorities": [...],
  "characters": [{
    "name": "Lucifer",
    "aliases": ["Lucifer"],                          // mọi tên nguồn → cho lookup runtime
    "avatar": { "local": "assets/heroes/...jpg", "url": "..." } | null,
    "tier":   { "overall": 10.93, "overall_band": "...", "notes": "...", "ranks": {14 mode} } | null,
    "rune_note":     { "rune_type", "secondary_type", "substats", "impact", "reasoning", "if_needed" } | null,
    "rune_priority": { "priority": "red", "border": "FF0000", "group_label", "group_notes" } | null,
    "skills": [ { "name", "type": "active|passive", "description", "icon": {local,url} } ]   // [] nếu không có
  }],
  "missing_skills": [...], "unmatched_names": [...]   // log như images.json.missing
}
```

## Breakdown (≈ multi-component, nên dùng `/spx-ff`)

| # | Việc | File |
|---|------|------|
| 1 | `fetch_skills.py` — scrape "Hero Skills" qua MediaWiki API (`action=parse`), parse tên/desc/icon File, resolve + **download icon** về `assets/skills/` (offline-first như avatar), cache `data/skills.json`, throttle + reuse `ALIASES` | new |
| 2 | `build_characters.py` — merge 4 JSON + skills theo **alias map tự tay** (seed: Bastett/Arcane/Primordial/Sovereign…), avatar ưu tiên hero-avatar rồi tới ảnh nguồn, **fail loud** nếu tên không ghép | new |
| 3 | Shell: nhúng `__CHARACTERS_DATA__` global + `Omni.openProfile(name)` (lookup qua alias) + CSS `.omni-profile` (avatar/tier-grid/rune/skills) | `index.template.html`, `build_html.py` |
| 4 | Wire **5 tab**: tier/beginners/endgame thay modal cũ → `Omni.openProfile`; rune-notes/rune-priority **thêm** click→openProfile (gắn `data-name`) | 5 fragments |
| 5 | `update.sh`: thêm step skills + build_characters; chèn `__CHARACTERS_DATA__` vào assembly | `update.sh` |

## Edge cases (đã có cách xử lý)
- Tên không ghép được → `unmatched_names` + build fail (không drop ngầm).
- Hero thiếu avatar (8 hero: Asmodeus, Susanoo, Izanami, Loki, Death Knight, Hera, Victoria, Vittoria) → dùng ảnh nguồn/initials.
- Hero không có trang wiki / không có section "Hero Skills" → `skills: []`, log `missing_skills`.
- Icon/avatar load fail → onerror → initials/ẩn icon (pattern sẵn có).
- Base vs variant trùng prefix (Dorabella ↔ Arcane Dorabella) → KHÔNG gộp, alias map khớp đúng tên nguồn.
- Wiki rate-limit (~110 page + section + icon) → `time.sleep` + cache `skills.json`, rebuild không re-hit.

**Lưu ý chi phí**: chọn "+ icon" + offline-first ⇒ tải ~400 icon nhỏ về `assets/skills/`. Nếu bạn muốn icon chỉ trỏ CDN (nhẹ repo, nhưng vỡ khi offline) thì nói mình đổi.

## Zero-Fog ✅
Scope ✓ · Variants (tách) ✓ · Skill detail (name+desc+icon) ✓ · Error paths ✓ · Edge cases liệt kê đủ ✓ · Test: repo không có test framework → **validation trong build script** (assert mọi hero nguồn khớp; in count missing) + **checklist click thủ công 5 tab** ✓ · Convention `npm`-less, Python pipeline + `update.sh` ✓

**Next step** — mình đang ở explore mode, không code. Chọn:
1. 🔍 `spx-plan-verifier` soát lại độ phủ trước
2. 🚀 `/spx-ff create-character-profiles` — tạo change có artifacts (khuyến nghị: multi-component, >10 task)
3. 🔧 `/spx-apply` — implement thẳng từ plan này
4. 💭 Bàn thêm

Bạn muốn đi hướng nào?

---

## User

spx-plan-verifier

---

## Claude

📋 **spx-plan-verifier**
- **Vì sao**: Plan này multi-component (2 script mới + sửa shell + 5 fragment + update.sh). Cần một góc nhìn độc lập soát lại độ phủ codebase, convention, và những chỗ tôi có thể đã bỏ sót trước khi tạo change.
- **Kỳ vọng nhận lại**: Đánh giá độ phủ + danh sách gap/ambiguity (nếu có), phân loại CRITICAL/WARNING, convention mà tôi nên tuân theo.
- **Xử lý output**:
  - Gap về codebase (tôi tự đọc được) → tôi tự verify, không hỏi bạn.
  - Gap cần bạn quyết (business/scope) → tôi tổng hợp hỏi bạn 1 lần.
  - Pass sạch → chốt, mời bạn sang `/spx-ff`.

Subagent chỉ **report — không tạo file**.

---

## Claude

Verifier trả về **4 CRITICAL**. Để mình tự kiểm chứng 2 cái thuộc về dữ liệu (alias thiếu + duplicate rune-priority) trước khi chốt — không tin mù.

---

## Claude

Cả 2 đều **đúng như verifier nói** — mình tự xác nhận:

- **C1**: thiếu đúng 4 alias trong `beginners` (`Arc. Dorabella`, `Jorm`, `S. Aiush`, `Tsuki`); `endgame` sạch. → **8 alias** là đủ.
- **C2**: đúng 10 hero xuất hiện 2 dòng trong rune-priority với priority khác nhau (vài cái còn khác cả _trong cùng_ group, vd `Janna`: Niche Picks·yellow **và** Niche Picks·red). Shape 1-object của mình sẽ **mất dữ liệu im lặng**.

> 🪞 *Reflect (rule #5)*: mình chỉ so tên rune-sheets ↔ tier-list, **quên check `beginners`/`endgame`** và **quên check duplicate nội bộ trong 1 sheet**. Bài học đưa vào plan: khi merge nhiều sheet → đối chiếu **mọi** sheet với canonical + quét **duplicate key nội bộ** từng sheet.

## Cách xử lý 3/4 CRITICAL (mình tự fix, không cần bạn quyết)
- **C1** → alias map đủ 8 entry + giữ guard `unmatched_names` fail-loud.
- **C3** (Fandom 403 anti-bot) → `fetch_skills.py`: **prototype ~6 hero trước**, dùng UA sẵn có, backoff/retry khi 403, cache **resumable** `skills.json`, coi "mọi hero có skill parse được" là *giả thuyết* — hero nào fail → `missing_skills[]` (đúng tinh thần "nếu có"). Coverage có thể **một phần**, bù dần qua nhiều lần chạy.
- **C4** → thêm placeholder thứ 4 `__CHARACTERS_DATA__` vào tuple trong `build_html.py` (đọc `data/characters.json`, fail nếu thiếu như guard per-page) + thêm step `build_characters.py` vào `update.sh` (sau mọi page build, trước `build_html.py`).
- **W1** → giữ `state.hero` ở **per-page** (low-risk), page chỉ ủy quyền *render* cho `Omni.openProfile`; 2 tab rune thêm plumbing tương tự. W2/W3/W4 (re-add class `.omni-profile` sau openModal; portrait rune-priority clickable + `data-name` canonical; renderer chịu được null/[]): fold vào.

## Còn 1 quyết định của bạn — C2

`rune_priority` nên là object hay mảng?

---

## Claude

Chốt: `rune_priority` = **mảng**. Tất cả CRITICAL đã xử lý, mọi quyết định đã có. Hết fog.

---

## ✅ Ready for Plan

**Xây gì**: 1 file dữ liệu `data/characters.json` gom full profile mỗi hero (avatar · tier · rune note · rune priority · skills), + wire modal chung để click hero ở **5 tab** → mở profile.

**Shape cuối** (đã sửa theo verifier):
```jsonc
characters: [{
  name, aliases[],
  avatar: {local,url} | null,
  tier: {overall,overall_band,notes,ranks{14}} | null,
  rune_note: {rune_type,secondary_type,substat_pre_11,substat_post_11,roll_unique,impact,reasoning,if_needed} | null,
  rune_priority: [ {priority,border,group_label,group_notes} ],   // ← MẢNG, giữ hết
  skills: [ {name,type,description,icon:{local,url}} ]            // [] nếu không có
}]
// + columns[14], impact_tiers, priorities, fetched_at, source
// + missing_skills[], unmatched_names[]   (log như images.json.missing)
```

**Quyết định đã chốt**
| Vấn đề | Quyết định |
|--------|-----------|
| Scope | Data file + enrich modal 5 tab (không tab mới) |
| Variants | Tách riêng (Bastet ≠ Ascended Bastett…) |
| Skills | name + desc + icon, **tải icon về** `assets/skills/` (offline) |
| Alias map | **8 entry** (4 variant + `Arc. Dorabella`/`Jorm`/`S. Aiush`/`Tsuki`), fail-loud `unmatched_names` |
| rune_priority | **Mảng** (giữ 10 hero trùng dòng) |
| Hash state | Per-page `state.hero`, page ủy quyền render cho `Omni.openProfile` |
| Skills 403 | Prototype 6 hero trước → backoff/retry + cache resumable; coverage có thể một phần |
| `__CHARACTERS_DATA__` | Placeholder thứ 4 trong `build_html.py` + step trong `update.sh` |

**Edge cases** (đã có cách xử lý): tên không match → fail-loud; 8 hero no-avatar → initials/ảnh nguồn; no wiki / no Hero Skills → `skills:[]`; null sub-object → renderer chịu được; icon load fail → ẩn; rune-priority trùng dòng → mảng; rate-limit → throttle + cache.

**Test/verify** (repo không có test framework): validation trong `build_characters.py` (assert mọi tên nguồn match, in count missing) + chạy `python3 scripts/build_html.py` (tự `SystemExit` nếu thiếu placeholder/data) + **checklist click thủ công 5 tab** + in lệnh mở app (theo CLAUDE.md).

**Convention tuân thủ**: pipeline Python + `update.sh`; CSS scope `.omni-profile`; IIFE bootstrap; ALIASES/`missing` log; offline-first local assets; throttle `time.sleep`.

---

**Next step** (mình vẫn ở explore mode — chưa code):

1. 🚀 **`/spx-ff create-character-profiles`** — tạo change có artifacts *(khuyến nghị: multi-component, 2 script mới + sửa shell + 5 fragment + update.sh, đáng có design doc — nhất là phần prototype fetch_skills)*
2. 🔧 `/spx-apply` — implement thẳng từ plan này
3. 💭 Bàn thêm

Bạn chọn hướng nào?

---

## User

<command-message>spx-ff</command-message>
<command-name>/spx-ff</command-name>
<command-args>create-character-profiles</command-args>

---

## User

Base directory for this skill: /Users/minh/www/git/personal/tools/m-valkyrie/.claude/skills/spx-ff

You are using the spx-ff skill, which is described as follows:

Create a new change — explore if needed, then generate all artifacts for implementation.

> **CLI NOTE**: Run all `openspec` and `bash` commands directly from the workspace root. Do NOT `cd` into any directory before running them. The `openspec` CLI is designed to work from the project root.

> **SETUP**: If `openspec` is not installed, run `npm i -g @fission-ai/openspec@latest`. If you need to run `openspec init`, always use `openspec init --tools none`.

**⚠️ MODE BOUNDARY RESET:** When this command is invoked, **stop any prior activity** — whether you were implementing code (`/spx-apply`), exploring (`/spx-plan`), or anything else. You are now in **change creation mode**. No code writing. No continuing prior tasks. Fresh start.

**🚫 SUBAGENT BLACKLIST:** NEVER use the `explore` or `plan` subagents. These are generic subagents from other kits and are NOT part of this workflow. Only use subagents explicitly listed in this kit (e.g., `spx-uiux-designer`). Do your own exploration and planning directly.

**Input**: A description of what to build, optionally with a kebab-case name. Can range from vague ("login page") to specific ("add JWT auth with refresh tokens using Redis session store").

---

## Phase 0: Context Check

Before evaluating the user's request, check what already exists:

```bash
openspec list --json
```

**If active changes exist**, the user might want to:
- **Create a brand new change** — proceed normally to Phase 1
- **Update an existing change's artifacts** — e.g., "I forgot to add email validation to the auth change"

**How to tell the difference:**
- User's input clearly relates to an active change → ask: "You have an active change `<name>`. Want to update its artifacts, or create a separate change?"
- User's input is unrelated to any active change → proceed to Phase 1 (new change)
- User explicitly says "new" or provides a new name → proceed to Phase 1

**If updating an existing change**: Skip `openspec new change`, go directly to Phase 2 step 3 (get status) using the existing change name. Update only the artifacts that need changes.

---

## Phase 1: Understand

Evaluate the user's input to decide the next phase.

**If no input provided**, ask what they want to build (open-ended, no preset options). Do NOT proceed without a request.

**If input provided**, assess clarity:

| Signal | Means | Next Phase |
|--------|-------|------------|
| Clear scope, known tech, specific enough to write a proposal | **Ready** | → Phase 2 (Create) |
| Vague idea, missing key decisions, multiple possible approaches, unknown constraints | **Needs exploration** | → Explore (below) |

**Bias toward action.** If you can make reasonable assumptions, go to Phase 2. Only explore when the ambiguity would lead to fundamentally wrong artifacts.

---

## Explore (when needed)

**Goal**: Get enough clarity to create good artifacts. This is NOT open-ended brainstorming — it's focused exploration with a destination.

**Subagent rule**: If you use subagents during exploration (e.g., for codebase analysis, planning), instruct them to **report findings only — no file creation**.

**Subagent Briefing Protocol (mandatory before every spawn):**

Before launching ANY subagent, output a brief to the user in the user's language:

```
📋 **[subagent-name]**
- Why: [why this subagent is needed — 1 line]
- Expect: [what you expect to receive back]
- Handle output:
  - Scenario A → [specific action]
  - Scenario B → [specific action]
```

The template above is in English for prompt readability. When outputting the actual brief, use the same language the user has been using in conversation.

This gives the user full visibility into what's about to happen and why. Brief BEFORE spawning, not after.

**No background mode — ever.** NEVER use `run_in_background` for any subagent. All subagents must run in foreground (parallel foreground is OK) so their execution is visible and controllable by the user. Background execution is uncontrollable behavior.

**Stance**: Curious, visual, grounded. Ask questions that emerge naturally. Use ASCII diagrams when they help. Investigate the codebase for context.

**What you might do:**
- Ask 2-3 clarifying questions (not an interrogation)
- Sketch the problem space with ASCII diagrams
- Investigate the codebase to surface relevant patterns, integration points, or constraints
- Compare approaches briefly if there's a real fork in the road
- Look up API docs via `spx-doc-lookup` if the approach depends on a specific library's behavior or version

**Keep it focused.** You're exploring to CREATE, not exploring to explore. When you have enough to write a solid proposal, move on.

**When sufficient clarity emerges**, present a brief summary and ask for confirmation:

```
## Ready to create

**What**: [1-2 sentence summary of the change]
**Approach**: [key technical decisions]
**Scope**: [what's in, what's out]

Create this change? (yes / discuss more)
```

- User confirms → Phase 2
- User wants to discuss more → continue exploring
- If exploration reveals this is too vague or the user just wants to think → suggest `/spx-plan` for open-ended exploration

---

## Phase 2: Create

Once the request is clear (either from input or after exploration):

1. **Derive a kebab-case name** from the description (e.g., "add user authentication" → `add-user-auth`).

2. **Create the change directory**
   ```bash
   openspec new change "<name>"
   ```

3. **Get the artifact build order**
   ```bash
   openspec status --change "<name>" --json
   ```
   Parse: `applyRequires` (artifact IDs needed before implementation) and `artifacts` (list with status and dependencies).

4. **Create artifacts in dependency order**

   Use the **TodoWrite tool** to track progress.

   For each artifact that is `ready` (dependencies satisfied):
   - Get instructions: `openspec instructions <artifact-id> --change "<name>" --json`
   - The instructions JSON includes:
     - `context`: Project background (constraints for you — do NOT include in output)
     - `rules`: Artifact-specific rules (constraints for you — do NOT include in output)
     - `template`: The structure to use for your output file
     - `instruction`: Schema-specific guidance for this artifact type
     - `outputPath`: Where to write the artifact
     - `dependencies`: Completed artifacts to read for context
   - Read any completed dependency files for context
   - Create the artifact file using `template` as structure
   - Apply `context` and `rules` as constraints — do NOT copy them into the file
   - Show brief progress: "✓ Created <artifact-id>"

   Continue until all `applyRequires` artifacts have `status: "done"`. Re-check with `openspec status` after each artifact.

   If an artifact requires user input (unclear context), ask and continue.

5. **Show final status**
   ```bash
   openspec status --change "<name>"
   ```

**Output**: Change name/location, artifacts created, and: "Run `/spx-apply` to start implementation."

---

**Artifact Creation Guidelines**

- Follow the `instruction` field from `openspec instructions` for each artifact type
- Read dependency artifacts for context before creating new ones
- Use `template` as structure — fill in its sections
- **`context` and `rules` are constraints for YOU, not content for the file** — never copy them into output
- **Always write artifact files in English** — regardless of conversation language
- **Annotate verify points in tasks.md** — For the last task of each major group or any high-risk task, append a verify annotation: `← (verify: what to check)`. This tells the verifier WHERE to deep-check and WHAT to look for. Place annotations on tasks that are end-of-flow (everything before must work for this to work) or high-risk (complex logic, integration points, security). Example:
  ```
  1. Setup database
    1.1 Create users table
    1.2 Create sessions table
    1.3 Add migration script ← (verify: schema matches design.md, migrations run without errors)
  2. Auth endpoints
    2.1 POST /login
    2.2 POST /register
    2.3 POST /refresh-token ← (verify: all endpoints match spec scenarios, token refresh flow works end-to-end)
  ```

**Guardrails**
- Create ALL artifacts needed for implementation (as defined by schema's `apply.requires`)
- Always read dependency artifacts before creating a new one
- Prefer making reasonable decisions to keep momentum — only ask when critically unclear
- If a change with that name already exists, suggest continuing that change instead
- Verify each artifact file exists after writing before proceeding to next
- **Don't over-explore** — 2-3 rounds of questions max before creating. If still unclear, create with best understanding and note assumptions in the proposal

The following is the user's request:

ARGUMENTS: create-character-profiles

---

## Claude

Đã có plan đầy đủ từ phần explore. Vào thẳng Phase 2 (Create). Trước hết kiểm tra openspec.

---

## Claude

openspec đã cài (v1.2.0) nhưng chưa init. Khởi tạo với `--tools none`.

---

## Claude

openspec đã init. Tạo change `create-character-profiles`.

---

## Claude

Build order: `proposal` → `design` + `specs` → `tasks`. Lấy instructions cho `proposal` trước.

---

## Claude

Tạo `proposal.md`. Change này có 2 capability: data layer + modal UI.

---

## Claude

✓ Created `proposal`. Giờ `design` + `specs` đã unlock. Lấy instructions cả hai.

---

## Claude

✓ Lấy xong. Viết `design.md`, `specs/character-profile-data/spec.md`, `specs/character-profile-modal/spec.md` (đều chỉ phụ thuộc proposal).

---

## Claude

✓ Created `design`. Giờ viết 2 spec file.

---

## Claude

✓ Created `specs` (2 capabilities). Validate + check status để unlock `tasks`.

---

## Claude

✓ Specs valid, `tasks` ready. Viết `tasks.md` (artifact cuối cho apply).

---

## Claude

Change `create-character-profiles` đã tạo xong — **4/4 artifacts**, validate sạch.

```
openspec/changes/create-character-profiles/
├── proposal.md                              # why + 2 capabilities + impact
├── design.md                                # D1–D9 decisions, risks, migration
├── specs/
│   ├── character-profile-data/spec.md       # merge, alias fail-loud, variants, rune_priority array, skills
│   └── character-profile-modal/spec.md      # __CHARACTERS_DATA__, openProfile, 5-tab wiring
└── tasks.md                                 # 6 nhóm, có verify annotations
```

**Đã đóng băng vào artifacts toàn bộ quyết định + phát hiện của verifier:**

| Đã chốt | Ở đâu |
|---------|-------|
| 8 alias (gồm 4 cái verifier tìm thêm trong beginners) + fail-loud `unmatched_names` | data spec R2, task 2.2/2.4 |
| `rune_priority` = **mảng** (giữ 10 hero trùng dòng) | data spec R4, task 2.3 |
| Variant tách riêng | data spec R3 |
| Skills best-effort + 403 backoff + cache resumable + **prototype 6 hero trước** | data spec R6, task 1.5/1.7, design D4 |
| Icon tải về `assets/skills/` (offline) | task 1.6, design D5 |
| `__CHARACTERS_DATA__` = placeholder thứ 4 trong build_html.py | modal spec R1, task 5.1, design D7 |
| Hash state per-page, page ủy quyền render | design D8, task 4.x |
| Renderer chịu null/[] + re-apply `.omni-profile` sau openModal | modal spec R2, task 3.2/3.4 |

**Tasks theo thứ tự phụ thuộc**: scraper (prototype) → merge build → shell renderer → wire 5 tab → pipeline integration → build & verify (kèm in lệnh mở app theo CLAUDE.md).

Sẵn sàng implement. Chạy **`/spx-apply`** để bắt đầu — nó sẽ làm theo `tasks.md`. Lưu ý task 1.5 là checkpoint quan trọng (xác nhận format Fandom + 403 trước khi scrape full ~115 hero).

---

