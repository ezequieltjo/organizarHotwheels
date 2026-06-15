# update-claude-environment skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal Claude Code skill (`~/.claude/skills/update-claude-environment/SKILL.md`) that orchestrates a full environment update via 8 linear passes with per-action confirmation.

**Architecture:** Single Markdown file, no helper scripts. Claude reads the skill and executes Bash commands directly. Validation follows TDD-for-skills: RED (baseline subagent fails without skill) → GREEN (subagent succeeds with skill) → REFACTOR (close loopholes).

**Tech Stack:** Markdown skill doc, Bash commands via Claude's Bash tool, subagent dispatches for testing.

**Spec:** `docs/superpowers/specs/2026-06-15-update-claude-environment-skill-design.md`

---

## File structure

| Path | Responsibility | Action |
|---|---|---|
| `~/.claude/skills/update-claude-environment/SKILL.md` | Main skill reference. 8 passes, prompts, error handling, red flags. | Create |
| `docs/superpowers/tests/update-claude-environment/baseline.md` | RED phase capture: subagent output without skill. | Create |
| `docs/superpowers/tests/update-claude-environment/green-run.md` | GREEN phase capture: subagent output with skill. | Create |
| `docs/superpowers/tests/update-claude-environment/refactor-log.md` | REFACTOR phase: loopholes found, counters added. | Create |

No project source files modified. Skill lives outside the repo (personal scope); test captures live inside the repo for git history.

---

## Task 1: RED phase — capture baseline subagent behavior without skill

**Files:**
- Create: `docs/superpowers/tests/update-claude-environment/baseline.md`

- [ ] **Step 1: Dispatch baseline subagent (no skill)**

Use the Agent tool with subagent_type `general-purpose` and this prompt:

```
You are dispatched to update the Claude Code environment on this Windows machine. Do whatever you think is required: CLI updates, plugin updates, marketplace updates, MCP server checks, cache cleanup, npm globals used by hooks. The machine runs Windows 10 with Git Bash available.

Do NOT ask the user for clarification — make your best judgment and execute. Report what you did at the end.

Constraints:
- You may run any read-only command freely.
- For state-changing commands, you MUST get user confirmation (treat "destructive action confirmation" rule from your system prompt as still active).
- You have 20 minutes.
```

- [ ] **Step 2: Capture subagent's full behavior into baseline.md**

Record verbatim:

```markdown
# RED phase baseline — update-claude-environment skill

**Date:** 2026-06-15
**Subagent type:** general-purpose
**Skill loaded:** none

## Subagent transcript (key decisions)

[Paste the subagent's text outputs and tool calls here — focus on:
- Order of operations attempted
- Whether per-action confirmation was requested
- Whether restart was mentioned
- Whether cache cleanup was performed
- Whether hooks npm deps were updated
- Whether MCP health was checked
- Any errors and how they were handled
]

## Observed failures

For each row, mark yes/no and quote the subagent's behavior:

| Skill requirement | Observed? | Quote |
|---|---|---|
| Snapshot versions before any update | | |
| Update marketplaces BEFORE plugins | | |
| Per-plugin update (not batched) | | |
| Confirm before each destructive action | | |
| Update CLI via both npm AND winget | | |
| Detect and update npm globals used by hooks | | |
| Run MCP health check (claude mcp list) | | |
| List orphan cache dirs before rm -rf | | |
| Run `claude plugin prune` | | |
| Emit before→after report | | |
| Mention restart requirement | | |

## Rationalizations to plug

[List every excuse the subagent made for skipping a step. Each becomes an explicit counter in SKILL.md.]
```

- [ ] **Step 3: Commit baseline**

```bash
cd D:/Code/organizarHotwheels
git add docs/superpowers/tests/update-claude-environment/baseline.md
git commit -m "test: RED baseline for update-claude-environment skill"
```

---

## Task 2: Create skill skeleton with frontmatter

**Files:**
- Create: `~/.claude/skills/update-claude-environment/SKILL.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p ~/.claude/skills/update-claude-environment
```

- [ ] **Step 2: Write SKILL.md skeleton**

Path: `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`

```markdown
---
name: update-claude-environment
description: Use when user asks to update Claude Code, plugins, marketplaces, MCP health, and related npm dependencies on Windows. Verifies current versions, applies updates with per-action confirmation, cleans stale plugin cache.
---

# Update Claude Environment

## Overview

Personal skill that orchestrates a full environment update of Claude Code and its ecosystem on Windows. Runs 8 linear passes with per-action confirmation before any state-changing command. Ends with a before→after report and a restart reminder.

## When to use

- User says "update Claude", "atualizar Claude", "update plugins", "clean plugin cache", "update tudo"
- Periodic maintenance (weekly / monthly cadence)
- After a long gap without updates
- After installing or removing plugins / marketplaces

## When NOT to use

- Linux or macOS (skill assumes Windows: WinGet, Git Bash, specific paths under `C:/Users/Admin/`)
- Inside a worktree session where a session restart would disrupt in-progress work
- Mid-task where losing session context would be costly
- User only wants to update ONE specific component (run the single command manually instead)

## Iron rule

Run 8 passes, IN ORDER, with per-action confirmation on passes 2, 3, 4, 5, 7.

Read-only passes (1, 6, 8) MUST NOT prompt.

NEVER skip pass 1 (snapshot) or pass 8 (report).

NEVER auto-restart Claude Code.

NEVER modify the system PATH.

NEVER delete files outside `~/.claude/plugins/cache/`.

[Passes 1-8 detailed in later tasks]

## Common mistakes

(Filled in REFACTOR phase — Task 8.)
```

- [ ] **Step 3: Verify file exists**

```bash
ls -la ~/.claude/skills/update-claude-environment/SKILL.md
```

Expected: file listed, ~1-2 KB.

- [ ] **Step 4: Commit skeleton**

Note: skill file lives outside the repo, so this commit only records the directory existence in a tracking file.

```bash
# Create a tracking marker so the repo knows the skill exists
mkdir -p D:/Code/organizarHotwheels/docs/superpowers/skills-tracked
echo "update-claude-environment: created skeleton $(date +%Y-%m-%d)" > D:/Code/organizarHotwheels/docs/superpowers/skills-tracked/update-claude-environment.txt
cd D:/Code/organizarHotwheels
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "feat(skill): skeleton for update-claude-environment"
```

---

## Task 3: Write Pass 1 (Snapshot) and Pass 2 (Marketplaces)

**Files:**
- Modify: `~/.claude/skills/update-claude-environment/SKILL.md` (replace `[Passes 1-8 detailed in later tasks]` with Pass 1 + Pass 2 sections)

- [ ] **Step 1: Write the failing test for Pass 1 + Pass 2**

Spawn a subagent with the skill available and verify it runs snapshot + marketplace update correctly:

```
You have the skill `update-claude-environment` available. Invoke it and run ONLY passes 1 and 2. Stop before pass 3. Report what you captured in the snapshot and what marketplace update produced.
```

Expected failure mode (before this task): without explicit pass content, the subagent either skips the snapshot or runs `claude plugin marketplace update` without first listing current marketplaces.

- [ ] **Step 2: Run test to verify it fails**

Dispatch the subagent. Capture behavior. Confirm: subagent does NOT collect all snapshot fields listed below, OR does NOT prompt before marketplace update.

- [ ] **Step 3: Write Pass 1 and Pass 2 sections into SKILL.md**

Edit `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`. Replace the `[Passes 1-8 detailed in later tasks]` placeholder with:

```markdown
## Pass 1 — Snapshot (read-only)

Capture the current state. NO PROMPTS in this pass.

Run these commands and record parsed output:

| Field | Command |
|---|---|
| Active CLI version | `claude --version` |
| CLI path entries | `where claude` |
| WinGet CLI version | `winget list --id Anthropic.ClaudeCode` |
| npm CLI version | `npm list -g @anthropic-ai/claude-code` |
| Plugins | `claude plugin list` |
| Marketplaces | `claude plugin marketplace list` |
| MCP servers | `claude mcp list` |
| npm globals | `npm list -g --depth=0` |
| Plugin cache dirs | `ls ~/.claude/plugins/cache/*/*/` |

Store parsed values in a snapshot record. Emit a compact summary table to the user:

```
SNAPSHOT
========
CLI active:  <version> (path: <which entry wins>)
CLI winget:  <version>
CLI npm:     <version>
Plugins:     <count> enabled
Marketplaces:<count>
MCP servers: <count> (✓/✗ summary)
npm globals: <count>
Cache dirs:  <count> total (<count> orphans detected in pass 7)
```

## Pass 2 — Marketplaces (confirm)

Update marketplace metadata for ALL configured marketplaces. Required before pass 3 so `claude plugin update` resolves the correct latest version.

**Prompt before action** (use AskUserQuestion):

> Update all marketplace metadata?
> Current marketplaces: <list from snapshot>

On "yes": run `claude plugin marketplace update` (no name argument → updates all).

On "no": skip pass 2, log "marketplaces not updated (user skipped)" in report.

After action: re-run `claude plugin marketplace list`, diff against snapshot, record any SHA changes.

**Error handling:** if `claude plugin marketplace update` returns non-zero, capture stderr verbatim, log error, continue to pass 3 (plugins may still update against stale metadata).

---
```

- [ ] **Step 4: Run test to verify it passes**

Re-dispatch the subagent from Step 1. Verify: snapshot table printed, prompt issued before marketplace update, marketplace update executed only after confirm.

- [ ] **Step 5: Commit**

```bash
cd D:/Code/organizarHotwheels
echo "update-claude-environment: passes 1-2 written $(date +%Y-%m-%d)" >> docs/superpowers/skills-tracked/update-claude-environment.txt
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "feat(skill): update-claude-env passes 1-2 (snapshot + marketplaces)"
```

---

## Task 4: Write Pass 3 (Plugins) and Pass 4 (CLI)

**Files:**
- Modify: `~/.claude/skills/update-claude-environment/SKILL.md` (append after Pass 2)

- [ ] **Step 1: Write the failing test**

Subagent prompt:

```
You have the skill `update-claude-environment` available. Run passes 1, 2, 3, 4 only. Stop before pass 5. For pass 3, you must update each plugin individually with a per-plugin prompt. For pass 4, you must update both npm and winget paths.
```

Expected failure: subagent batches all plugins into one `claude plugin update` call, OR skips winget upgrade because claude.exe is in use, OR runs npm install without confirmation.

- [ ] **Step 2: Run test to verify it fails**

Dispatch. Capture deviations.

- [ ] **Step 3: Append Pass 3 and Pass 4 sections to SKILL.md**

Edit `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`. Insert before the `## Common mistakes` section:

```markdown
## Pass 3 — Plugins (confirm per plugin)

Update each ENABLED plugin individually. The `claude plugin update <name>` command targets one plugin; do NOT try to batch.

For each plugin in the snapshot's plugins[] list:

1. **Prompt** (use AskUserQuestion):
   > Update plugin `<name>` (current: <version>)? [yes / no / skip-all]

2. On "yes": run `claude plugin update <name>`
3. On "no": skip THIS plugin, continue to next
4. On "skip-all": abort pass 3 entirely, log in report

Capture: version before, version after, status (updated / already latest / failed / skipped).

**Error handling:** on failure (non-zero exit), capture stderr verbatim, log error, continue to next plugin. Do NOT abort the whole pass on one plugin's failure.

## Pass 4 — CLI (confirm)

Update Claude Code CLI via BOTH package managers. They install to different paths and the user's PATH may prefer either; both must be current.

**Prompt before action** (use AskUserQuestion):

> Update Claude Code CLI?
> - npm path:    <current> → latest
> - winget path: <current> → latest
> Proceed? [yes / no]

On "yes":

1. Run `npm install -g @anthropic-ai/claude-code@latest`
   - Capture new version from `npm list -g @anthropic-ai/claude-code`
   - On failure: log stderr, continue to step 2

2. Run `winget upgrade --id Anthropic.ClaudeCode`
   - Capture new version from `winget list --id Anthropic.ClaudeCode`
   - On failure (typical: `claude.exe` locked because current session is running):
     - Log stderr verbatim
     - Add to report: "Close Claude Code session, then run: `winget upgrade --id Anthropic.ClaudeCode`"

On "no": skip pass 4 entirely, log "CLI update skipped by user".

---
```

- [ ] **Step 4: Run test to verify it passes**

Re-dispatch. Verify: per-plugin prompts issued, both npm and winget attempted, error messages captured verbatim.

- [ ] **Step 5: Commit**

```bash
cd D:/Code/organizarHotwheels
echo "update-claude-environment: passes 3-4 written $(date +%Y-%m-%d)" >> docs/superpowers/skills-tracked/update-claude-environment.txt
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "feat(skill): update-claude-env passes 3-4 (plugins + CLI)"
```

---

## Task 5: Write Pass 5 (Hooks deps) and Pass 6 (MCP check)

**Files:**
- Modify: `~/.claude/skills/update-claude-environment/SKILL.md` (append after Pass 4)

- [ ] **Step 1: Write the failing test**

Subagent prompt:

```
You have the skill `update-claude-environment` available. Run passes 1-6. Stop before pass 7. For pass 5, identify which npm globals are referenced by hooks/settings.json, then offer to update them. For pass 6, just run `claude mcp list` and report.
```

Expected failure: subagent either runs `npm update -g` (updates everything, not just hook deps) OR forgets pass 5 entirely OR runs pass 6 with a destructive command instead of read-only check.

- [ ] **Step 2: Run test to verify it fails**

Dispatch. Capture.

- [ ] **Step 3: Append Pass 5 and Pass 6 sections to SKILL.md**

Edit `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`. Insert before `## Common mistakes`:

```markdown
## Pass 5 — Hooks deps (confirm)

Update npm globals that are REFERENCED by hooks or settings.json. Do NOT run a blanket `npm update -g` — only the packages actually used by the user's Claude Code config.

**Detection algorithm:**

1. Read `~/.claude/settings.json` and collect every `mcpServers.*.command` / `mcpServers.*.args` / `hooks.*.command` that references `npm/node_modules/<pkg>/` or `node_modules/<pkg>/`. Extract `<pkg>`.

2. Read every file in `~/.claude/hooks/*.js` and `~/.claude/hooks/*.ps1`. Extract:
   - `require('<pkg>')` calls
   - `node_modules/<pkg>/` path references
   - Hardcoded package names referenced in comments like `# uses <pkg>`

3. Deduplicate package names → `candidate_packages[]`.

4. Cross-ref each candidate with `npm list -g --depth=0`:
   - If globally installed: add to `to_update[]` list with current version
   - If not globally installed: skip (it's a local/transitive dep, not user-managed)

**Prompt before action** (use AskUserQuestion):

> Update these npm globals used by hooks/settings?
> - `<pkg1>` (current: <version>)
> - `<pkg2>` (current: <version>)
> Proceed? [yes / no]

On "yes": for each package, run `npm install -g <pkg>@latest`. Capture version before/after.

On "no": skip pass 5, log.

**Error handling:** per-package failure → log stderr, continue next package.

## Pass 6 — MCP health check (read-only)

NO PROMPTS in this pass. Just run `claude mcp list` and parse output.

Action:

1. Run `claude mcp list`
2. Parse output for ✓ (connected) and ✗ (failed) markers
3. For each ✗:
   - Note server name and error
   - Add to report: "MCP server `<name>` failed. Reinstall: `claude mcp remove <name>` then re-add with original command."

DO NOT execute the reinstall — only suggest it.

---
```

- [ ] **Step 4: Run test to verify it passes**

Re-dispatch. Verify: only hook-referenced packages offered for update, MCP failures noted with reinstall suggestion but not auto-executed.

- [ ] **Step 5: Commit**

```bash
cd D:/Code/organizarHotwheels
echo "update-claude-environment: passes 5-6 written $(date +%Y-%m-%d)" >> docs/superpowers/skills-tracked/update-claude-environment.txt
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "feat(skill): update-claude-env passes 5-6 (hooks deps + MCP check)"
```

---

## Task 6: Write Pass 7 (Cache cleanup) and Pass 8 (Report)

**Files:**
- Modify: `~/.claude/skills/update-claude-environment/SKILL.md` (append after Pass 6)

- [ ] **Step 1: Write the failing test**

Subagent prompt:

```
You have the skill `update-claude-environment` available. Run all 8 passes. For pass 7, you must LIST orphan dirs before deleting and confirm before rm -rf. For pass 8, you must print a before→after report table.
```

Expected failure: subagent runs `rm -rf ~/.claude/plugins/cache/*` without listing first, OR forgets to run `claude plugin prune`, OR skips the report table, OR forgets the restart reminder.

- [ ] **Step 2: Run test to verify it fails**

Dispatch. Capture.

- [ ] **Step 3: Append Pass 7 and Pass 8 sections to SKILL.md**

Edit `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`. Insert before `## Common mistakes`:

```markdown
## Pass 7 — Cache cleanup (confirm)

Remove orphan plugin cache version directories, then prune unused auto-installed dependencies.

**Orphan detection algorithm:**

1. Read `~/.claude/settings.json` → `enabledPlugins` to get the set of (plugin, marketplace) pairs currently enabled.

2. For each enabled plugin, read `~/.claude/plugins/cache/<marketplace>/<plugin>/.claude-plugin/marketplace.json` to find the SHA pinned for the enabled version. That SHA's directory is the ACTIVE dir.

3. List every version dir under `~/.claude/plugins/cache/<marketplace>/<plugin>/`. Any dir that is NOT the active SHA = orphan.

4. Also scan for orphan plugin directories (plugins no longer enabled but still cached): if `enabledPlugins` does not reference `<plugin>@<marketplace>`, all its version dirs are orphans.

5. Collect all orphan paths → `orphans[]`.

**Prompt before delete** (use AskUserQuestion):

> Remove <N> orphan cache dirs?
> <list every orphan path, one per line>
> Proceed? [yes / no]

On "yes": run `rm -rf <path>` for each orphan. Capture total bytes freed (use `du -sh <path>` before deletion, sum).

On "no": skip deletion, log "cache cleanup skipped by user".

**Then prompt separately for prune:**

> Run `claude plugin prune` to remove auto-installed dependencies no longer needed? [yes / no]

On "yes": run `claude plugin prune`. Capture output.

On "no": skip, log.

## Pass 8 — Report (read-only)

NO PROMPTS. Emit final report to user.

Report template (fill placeholders, drop empty sections):

```
## Update report — <YYYY-MM-DD HH:MM>

### Updated
| Component | Before | After |
|---|---|---|
| <name> | <old> | <new> |
...

### Already latest
- <name>@<marketplace> (<version>)
- ...

### Failed
- <name>: <error message verbatim>
- ...

### MCP servers
- ✓ <name>
- ✗ <name>: <error>
- (or "all healthy")

### Cache cleanup
- Removed <N> orphan dirs (<size> freed)
- `claude plugin prune`: <one-line summary or "skipped">

### Next steps
**Restart Claude Code** to apply CLI and plugin updates:
  1. Save any in-progress work
  2. Close Claude Code (Ctrl+C or `/exit`)
  3. Re-launch: `claude`
  4. (Optional) Re-invoke this skill to verify clean state
```

If nothing was updated and no failures: report "Environment already up-to-date. No changes."

---
```

- [ ] **Step 4: Run test to verify it passes**

Re-dispatch. Verify: orphan dirs listed before deletion, prune prompted separately, report follows template, restart reminder present.

- [ ] **Step 5: Commit**

```bash
cd D:/Code/organizarHotwheels
echo "update-claude-environment: passes 7-8 written $(date +%Y-%m-%d)" >> docs/superpowers/skills-tracked/update-claude-environment.txt
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "feat(skill): update-claude-env passes 7-8 (cache cleanup + report)"
```

---

## Task 7: GREEN phase — full run with skill loaded

**Files:**
- Create: `docs/superpowers/tests/update-claude-environment/green-run.md`

- [ ] **Step 1: Dispatch full-run subagent**

Use Agent tool with subagent_type `general-purpose`:

```
You have the skill `update-claude-environment` available in your environment. Invoke it and run ALL 8 passes to completion. Treat per-action confirmation prompts as if the user said "yes" to all (you are authorized to proceed). Report at the end:
- Order of passes executed
- Each confirmation prompt issued (quote it)
- Each command executed (with exit status)
- Final report output
```

- [ ] **Step 2: Capture green-run.md**

```markdown
# GREEN phase capture — update-claude-environment skill

**Date:** 2026-06-15
**Subagent type:** general-purpose
**Skill loaded:** yes

## Pass-by-pass execution

### Pass 1 — Snapshot
[Subagent output]

### Pass 2 — Marketplaces
[Prompt issued: <quote>]
[Command run: <cmd>]
[Exit status: <code>]

### Pass 3 — Plugins
[Per-plugin prompts and commands]
...

### Pass 4 — CLI
[npm + winget commands, exit statuses]

### Pass 5 — Hooks deps
[Detected packages: ...]
[Prompt: ...]
[Commands: ...]

### Pass 6 — MCP check
[Output of `claude mcp list`]

### Pass 7 — Cache cleanup
[Orphans listed: ...]
[Deletion commands: ...]
[Prune output: ...]

### Pass 8 — Report
[Final report as emitted by subagent]

## Compliance check

| Requirement | Pass? | Notes |
|---|---|---|
| All 8 passes ran in order | | |
| Per-action confirmation on passes 2-5, 7 | | |
| Read-only passes (1, 6, 8) did NOT prompt | | |
| Snapshot collected before any mutation | | |
| Marketplaces updated BEFORE plugins | | |
| Per-plugin update (not batched) | | |
| Both npm AND winget CLI updated | | |
| Only hook-referenced npm globals updated | | |
| Orphan dirs listed before rm -rf | | |
| `claude plugin prune` prompted separately | | |
| Report follows template | | |
| Restart reminder present | | |
```

- [ ] **Step 3: Commit green-run**

```bash
cd D:/Code/organizarHotwheels
git add docs/superpowers/tests/update-claude-environment/green-run.md
git commit -m "test: GREEN phase capture for update-claude-environment skill"
```

---

## Task 8: REFACTOR — close loopholes via Common Mistakes table

**Files:**
- Modify: `~/.claude/skills/update-claude-environment/SKILL.md` (fill in Common Mistakes section)
- Create: `docs/superpowers/tests/update-claude-environment/refactor-log.md`

- [ ] **Step 1: Identify loopholes from GREEN run**

Review `green-run.md`. List every requirement marked "no" or partial. These are loopholes the skill didn't enforce strongly enough.

- [ ] **Step 2: Write refactor-log.md**

```markdown
# REFACTOR phase — update-claude-environment skill

**Date:** 2026-06-15

## Loopholes found in GREEN run

| # | Loophole | Counter added to SKILL.md |
|---|---|---|
| 1 | <description> | <quote of counter text added> |
| ...

## Re-test result

After adding counters, re-dispatched GREEN scenario. Result: <pass/fail per loophole>.
```

- [ ] **Step 3: Replace Common Mistakes section in SKILL.md**

Edit `C:/Users/Admin/.claude/skills/update-claude-environment/SKILL.md`. Replace the `(Filled in REFACTOR phase — Task 8.)` line under `## Common mistakes` with:

```markdown
## Common mistakes — red flags

If you catch yourself doing any of these, STOP and re-read the Iron rule above.

| Anti-pattern | Why it's wrong | Do this instead |
|---|---|---|
| "I'll batch all plugins into one `claude plugin update` call" | Loses per-plugin confirmation; user can't reject one bad plugin | Loop, prompt per plugin |
| "Snapshot is just `claude --version`, that's enough" | Misses plugin/marketplace/cache state needed for the report | Run ALL commands in the Pass 1 table |
| "Marketplaces look fresh, skip pass 2" | `claude plugin update` resolves against marketplace metadata; stale metadata → wrong version | Always run pass 2, it's idempotent |
| "winget upgrade failed, abort pass 4" | npm path is independent; user may still get update via npm | Continue to npm install, log winget failure |
| "User said yes to plugin update, that covers CLI too" | Different commands, different failure modes, user may want to defer CLI restart | Separate prompt per pass |
| "I'll just run `npm update -g` for hooks deps" | Updates every global package, not just hook-referenced ones | Use detection algorithm in Pass 5 |
| "rm -rf the whole cache dir, faster" | Destroys active plugin installs; breaks next session | Detect orphans via algorithm in Pass 7 |
| "Skip the report, user saw the output" | Report is the audit trail; without it user can't tell what changed | Always emit Pass 8 report, even on no-op |
| "Skip restart reminder, obvious" | User will close terminal mid-task without realizing updates need restart | Always include restart block in report |
| "Modify PATH to fix WinGet vs npm priority" | System-level change, fragile, out of skill scope | Report mismatch, suggest manual fix in report |

## If you wouldn't run this skill on a production server, you shouldn't run it here either

This skill mutates the user's Claude Code installation. Every state-changing command has a prompt. If you find yourself wanting to skip a prompt, the skill is broken — fix the skill, don't paper over it.
```

(Adjust the table rows based on actual loopholes identified in Step 1.)

- [ ] **Step 4: Re-run GREEN scenario**

Dispatch the same subagent prompt from Task 7. Verify all previously-failed requirements now pass.

- [ ] **Step 5: Update refactor-log.md with re-test result**

Fill the `## Re-test result` section with new pass/fail per loophole.

- [ ] **Step 6: Commit**

```bash
cd D:/Code/organizarHotwheels
git add docs/superpowers/tests/update-claude-environment/refactor-log.md
echo "update-claude-environment: refactor complete $(date +%Y-%m-%d)" >> docs/superpowers/skills-tracked/update-claude-environment.txt
git add docs/superpowers/skills-tracked/update-claude-environment.txt
git commit -m "refactor(skill): update-claude-env close loopholes via common-mistakes table"
```

---

## Self-review

### Spec coverage

| Spec section | Plan task |
|---|---|
| §1 Overview | Task 2 (skeleton) |
| §2 Requirements F1 (detect versions) | Task 3 Pass 1 |
| §2 Requirements F2 (marketplaces) | Task 3 Pass 2 |
| §2 Requirements F3 (plugins) | Task 4 Pass 3 |
| §2 Requirements F4 (CLI both paths) | Task 4 Pass 4 |
| §2 Requirements F5 (hooks deps) | Task 5 Pass 5 |
| §2 Requirements F6 (MCP health) | Task 5 Pass 6 |
| §2 Requirements F7 (cache + prune) | Task 6 Pass 7 |
| §2 Requirements F8 (report) | Task 6 Pass 8 |
| §2 NF1 (per-action confirm) | All pass tasks |
| §2 NF2 (idempotent) | Task 7 GREEN run |
| §2 NF3 (no auto-restart) | Task 6 Pass 8 + Task 8 red flags |
| §2 NF4 (no PATH modify) | Task 8 red flags |
| §2 NF5 (no delete outside cache) | Task 6 Pass 7 |
| §3 Components table | Tasks 3-6 |
| §4 8 linear passes | Tasks 3-6 |
| §5 Per-step spec | Tasks 3-6 |
| §6 Confirmation policy | All pass tasks |
| §7 Error handling | Tasks 3-6 per-pass |
| §8 Restart handling | Task 6 Pass 8 |
| §9 Idempotency | Task 7 GREEN run |
| §10 RED → GREEN → REFACTOR | Tasks 1, 7, 8 |
| §11 Skill file structure | Task 2 |
| §12 Open questions | Resolved in pass tasks |
| §13 Success criteria | Tasks 1, 7, 8 |

No spec gaps.

### Placeholder scan

No "TBD" / "TODO" / "implement later" patterns. Each task has actual prompt text, command text, and report templates.

### Type consistency

- "Orphan" definition consistent across Pass 7 (Task 6) and refactor table (Task 8).
- "Snapshot" fields in Pass 1 (Task 3) match what subsequent passes consume.
- "Report template" in Pass 8 (Task 6) matches what GREEN compliance check (Task 7) verifies.

No mismatches.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-15-update-claude-environment-skill.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
