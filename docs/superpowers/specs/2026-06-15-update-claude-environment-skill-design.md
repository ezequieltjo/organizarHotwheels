# Design: update-claude-environment skill

**Date:** 2026-06-15
**Scope:** Personal skill, `~/.claude/skills/update-claude-environment/`
**Target OS:** Windows 10/11 (WinGet + npm via Git Bash)

---

## 1. Overview

Personal skill that orchestrates a full environment update of Claude Code and its ecosystem: CLI binaries, plugins, marketplaces, MCP server health, npm globals used by hooks, and stale plugin cache cleanup.

Format: **skill document** (Markdown). Claude reads it and executes Bash commands, confirming each destructive action via AskUserQuestion before proceeding. Skill is Windows-specific because it uses WinGet for CLI updates and Git Bash for shell commands.

Core principle: **one linear pass, per-action confirmation, full before→after report at the end.**

---

## 2. Requirements

### Functional

- F1: Detect current versions of CLI (WinGet + npm), plugins, marketplaces, MCP servers, npm globals used by hooks/settings.
- F2: Update all configured marketplaces.
- F3: Update each enabled plugin individually.
- F4: Update Claude Code CLI via both `npm` and `winget` paths.
- F5: Update npm globals referenced by `~/.claude/settings.json` and `~/.claude/hooks/`.
- F6: Run MCP server health check, report failures.
- F7: Detect and remove orphaned plugin cache versions under `~/.claude/plugins/cache/`, run `claude plugin prune`.
- F8: Emit a final before→after report with restart instructions.

### Non-functional

- NF1: Per-action confirmation before any state-changing command (passes 2–5, 7). Read-only passes (1, 6, 8) require no prompt.
- NF2: Idempotent — re-running when everything is up-to-date produces no-op report.
- NF3: Never auto-restart Claude Code. Report `Restart Claude Code to apply` at end.
- NF4: Never modify system PATH. WinGet vs npm priority is reported, not fixed.
- NF5: Never delete files outside `~/.claude/plugins/cache/`.

### Out of scope

- Updating skills in `~/.claude/skills/` (not git-tracked, no canonical update source).
- Updating hooks in `~/.claude/hooks/` source code (treated as user-owned; only their npm dependencies are updated).
- Reordering PATH to resolve WinGet vs npm priority.
- Auto-restart of Claude Code session.
- Cross-platform support (Linux/macOS). Skill is Windows-only.
- Rollback automation on update failure (report only; user decides).

---

## 3. Components covered

| Component | Source of truth | Update command | Read-only check |
|---|---|---|---|
| CLI WinGet | `winget list --id Anthropic.ClaudeCode` | `winget upgrade --id Anthropic.ClaudeCode` | `claude --version` |
| CLI npm | `npm list -g @anthropic-ai/claude-code` | `npm install -g @anthropic-ai/claude-code@latest` | `npm outdated -g` |
| Marketplaces | `claude plugin marketplace list` | `claude plugin marketplace update` (all) | compare before/after |
| Plugins | `claude plugin list` | `claude plugin update <plugin>` (each) | compare versions |
| MCP servers | `claude mcp list` | none (no update command — reinstall if broken) | ✓/✗ status |
| npm globals (hooks) | parse `settings.json` + `hooks/*.js` for `require()` of npm packages, cross-ref `npm list -g --depth=0` | `npm install -g <pkg>@latest` per package | `npm outdated -g` |
| Plugin cache | `ls ~/.claude/plugins/cache/<marketplace>/<plugin>/` (multiple version dirs = orphans) | `rm -rf` orphan dirs + `claude plugin prune` | diff count of version dirs |

---

## 4. Architecture — 8 linear passes

```
┌─────────────────────────────────────────────────────────────────┐
│  1. SNAPSHOT   (read-only)                                      │
│     Capture versions for CLI/npm/plugins/marketplaces/MCP/globals│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. MARKETPLACES   (confirm)                                    │
│     claude plugin marketplace update                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. PLUGINS   (confirm per plugin)                              │
│     for each enabled plugin: claude plugin update <p>          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. CLI   (confirm)                                             │
│     npm install -g @anthropic-ai/claude-code@latest            │
│     winget upgrade --id Anthropic.ClaudeCode                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. HOOKS_DEPS   (confirm)                                      │
│     Parse settings.json + hooks/*.js for npm deps              │
│     npm install -g <pkg>@latest for each                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. MCP_CHECK   (read-only)                                     │
│     claude mcp list, parse ✓/✗, report failures                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. CACHE   (confirm)                                           │
│     Detect orphan version dirs in ~/.claude/plugins/cache/     │
│     rm -rf each orphan                                          │
│     claude plugin prune                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. REPORT   (read-only)                                        │
│     Before→after table, failures, restart instructions         │
└─────────────────────────────────────────────────────────────────┘
```

### Ordering rationale

- **Marketplaces before plugins:** `claude plugin update` reads marketplace metadata to resolve "latest". Stale metadata → wrong version resolved.
- **Plugins before CLI:** Plugin updates are cheap and safe; CLI update may require restart mid-flow.
- **CLI before hooks deps:** If CLI version bump changes runtime expectations, hook behavior is re-validated against new CLI.
- **MCP check after all updates:** Health check reflects post-update state.
- **Cache cleanup last:** Only removes orphan dirs after all updates have settled, so we never delete a dir another step needs.

---

## 5. Per-step specification

### Pass 1 — SNAPSHOT (read-only)

Capture into in-memory record:

```text
cli.winget.version    = parse(winget list --id Anthropic.ClaudeCode)
cli.npm.version       = parse(npm list -g @anthropic-ai/claude-code)
cli.active            = parse(claude --version)            # which PATH entry wins
cli.path.entries      = where claude                        # ordered list
plugins[]             = parse(claude plugin list)           # name, version, scope, status
marketplaces[]        = parse(claude plugin marketplace list)
mcp.servers[]         = parse(claude mcp list)              # name, status
hooks.npm.globals[]   = extract from settings.json + ~/.claude/hooks/*.js
cache.version.dirs{}  = map: marketplace/plugin -> [version dirs]
```

No prompts. Output: compact summary table of "current state".

### Pass 2 — MARKETPLACES (confirm)

Action: `claude plugin marketplace update` (no name → updates all).

Prompt:
> Update all marketplaces? [Y/n]
> Current: claude-plugins-official, caveman.

On success: re-run `claude plugin marketplace list`, diff against snapshot, note changes.

On failure: log error, continue to pass 3.

### Pass 3 — PLUGINS (confirm per plugin)

For each enabled plugin from snapshot:

Action: `claude plugin update <plugin>`.

Prompt (batched if all share scope):
> Update plugin `<name>` (current: <v>)?

On "already latest": skip, note in report.
On success: record new version.
On failure: log error, continue next plugin.

### Pass 4 — CLI (confirm)

Two sub-actions, both confirmed in one prompt:

> Update Claude Code CLI?
> - npm: 2.1.177 → latest
> - winget: 2.1.143 → latest
> Proceed? [Y/n]

Sub-action A: `npm install -g @anthropic-ai/claude-code@latest`
Sub-action B: `winget upgrade --id Anthropic.ClaudeCode`

On winget failure (typically: claude.exe locked because session is running):
- Log error verbatim.
- Note in report: "Close Claude Code session, run `winget upgrade --id Anthropic.ClaudeCode` manually."

On npm failure:
- Log error.
- Note in report with command to retry.

### Pass 5 — HOOKS_DEPS (confirm)

Algorithm:

1. Read `~/.claude/settings.json` — collect every `mcpServers.*` entry pointing at `npm/node_modules` paths.
2. Read `~/.claude/hooks/*.js` and `*.ps1` — collect `require('<pkg>')` and `node ... node_modules/<pkg>/...` references.
3. Cross-ref collected package names against `npm list -g --depth=0`.
4. Build candidate list of npm globals to update (only those present globally).

Prompt:
> Update npm globals used by hooks/settings?
> - cavemem (current: x.y.z)
> - @gitlawb/openclaude (current: 0.6.0)
> Proceed? [Y/n]

Action per package: `npm install -g <pkg>@latest`.

### Pass 6 — MCP_CHECK (read-only)

Action: `claude mcp list`.

Parse output for ✓/✗ markers. For each ✗:
- Note server name.
- Suggest reinstall: `claude mcp remove <name>` then `claude mcp add ...` (do not execute — only suggest).

No prompts.

### Pass 7 — CACHE (confirm)

Algorithm:

1. For each `~/.claude/plugins/cache/<marketplace>/<plugin>/`:
   - List version dirs.
   - Cross-ref against `enabledPlugins` in settings.json to determine which version dir is active.
   - All other version dirs = orphans.

2. Prompt:
   > Remove <N> orphan cache dirs?
   > - ~/.claude/plugins/cache/.../<old-version-1>
   > - ~/.claude/plugins/cache/.../<old-version-2>
   > Proceed? [Y/n]

3. On confirm: `rm -rf` each orphan.

4. Then prompt:
   > Run `claude plugin prune` to remove auto-installed dependencies no longer needed? [Y/n]

5. On confirm: `claude plugin prune`.

### Pass 8 — REPORT (read-only)

Output structured report:

```markdown
## Update report — 2026-06-15

### Updated
| Component | Before | After |
|---|---|---|
| CLI npm | 2.1.177 | 2.1.180 |
| superpowers | 5.0.7 | 5.0.8 |
| ...

### Already latest
- claude-md-management@claude-plugins-official (1.0.0)
- context7@claude-plugins-official
- ...

### Failed
- winget upgrade: claude.exe locked. Manual: `winget upgrade --id Anthropic.ClaudeCode`
- <plugin-name>: <error>

### MCP servers
- ✓ context7
- ✗ none

### Cache
- Removed 3 orphan dirs (~12 MB)
- `claude plugin prune`: <output>

### Next steps
**Restart Claude Code** to apply CLI/plugin updates.
Then re-run this skill to confirm clean state.
```

---

## 6. Confirmation policy

Every state-changing pass (2, 3, 4, 5, 7) MUST call `AskUserQuestion` (or equivalent) before its primary command. Read-only passes (1, 6, 8) MUST NOT prompt.

If user denies a pass: skip, log "skipped by user" in report, continue to next pass. Do not abort the whole flow.

---

## 7. Error handling

| Scenario | Behavior |
|---|---|
| Plugin update fails (network, sha mismatch) | Log error verbatim, continue next plugin |
| `winget upgrade` fails (claude.exe locked) | Log error, suggest manual command, continue to pass 5 |
| `npm install -g` fails (EACCES, ENOTFOUND) | Log error, continue next package |
| `claude plugin marketplace update` fails | Log error, abort pass 2 only, continue pass 3 |
| Any Bash command non-zero exit | Capture stderr, classify as soft (continue) or hard (abort pass) |
| Hard error (disk full, permission) | Abort current pass, log, continue next pass, surface in report |

No automatic rollback. Rollback is a user decision after seeing the report.

---

## 8. Restart handling

Plugin updates and CLI updates require a Claude Code restart to take effect. The skill:

- Does NOT attempt auto-restart (impossible from within session).
- Surfaces restart requirement in pass 8 report with the literal command:
  ```
  # Close Claude Code (Ctrl+C or /exit)
  # Then in terminal:
  claude
  ```
- Recommends re-running the skill after restart to verify clean state.

---

## 9. Idempotency

Re-running the skill when everything is up-to-date must:

- Complete all 8 passes without errors.
- Prompt "Y/n" on state-changing passes; on "Y", commands execute and return "already latest" / "no orphans found".
- Final report shows "Already latest" section populated, "Updated" section empty.

Tested as part of GREEN phase (see §10).

---

## 10. Testing strategy (RED → GREEN → REFACTOR)

This is a discipline-enforcing skill (forces per-action confirmation, ordered flow). Per the writing-skills Iron Law, test before writing.

### RED — baseline scenario

Dispatch a subagent WITHOUT the skill with this prompt:

> "Atualize tudo do Claude Code nesse ambiente Windows: CLI (WinGet e npm), todos os plugins, todos os marketplaces, MCP servers, e limpa cache velho. Faça agora sem perguntar."

Capture baseline behavior:

- Does subagent skip per-action confirmation and just run commands?
- Does subagent run `winget upgrade` blindly without checking if update is available?
- Does subagent forget cache cleanup entirely?
- Does subagent forget to mention restart?
- Does subagent reorder passes (e.g., update plugins before refreshing marketplaces)?
- Does subagent run `rm -rf` on cache without listing what will be deleted?
- Does subagent skip MCP health check?
- Does subagent skip hooks deps entirely?

These failures become the rationalization table the skill must plug.

### GREEN — write skill, re-test

Write SKILL.md addressing each observed failure. Re-dispatch the SAME scenario to a fresh subagent WITH the skill loaded. Verify:

- Subagent runs SNAPSHOT first.
- Subagent prompts before each destructive action.
- Subagent runs passes in order 1→8.
- Subagent lists orphan cache dirs before `rm -rf`.
- Subagent mentions restart in report.

### REFACTOR — close loopholes

If subagent finds a workaround (e.g., runs `claude plugin update` for all plugins in one command without per-plugin prompt), add explicit prohibition to SKILL.md and a red-flag checklist. Re-test.

---

## 11. Skill file structure

```
~/.claude/skills/update-claude-environment/
  SKILL.md     # main reference (this design's executable form)
```

No helper scripts. No supporting files. The skill is pure documentation; Claude executes commands directly.

SKILL.md structure:

```markdown
---
name: update-claude-environment
description: Use when user asks to update Claude Code, plugins, marketplaces, MCP health, and related npm dependencies on Windows. Verifies current versions, applies updates with per-action confirmation, cleans stale plugin cache.
---

# Update Claude Environment

## Overview
[1-2 sentences]

## When to use
- User says "update Claude", "atualizar Claude", "update plugins", "clean plugin cache"
- Periodic maintenance
- After long gap without updates

## When NOT to use
- Linux/macOS (skill is Windows-only — WinGet and Git Bash assumed)
- Inside a worktree session where restart would disrupt work
- Mid-task where session restart would lose context

## Iron rule
8 passes, in order. Confirm each destructive action. Never skip snapshot, never skip report.

## Pass 1 — Snapshot (read-only)
[commands, expected output]

## Pass 2 — Marketplaces (confirm)
[command, prompt template]

## Pass 3 — Plugins (confirm per plugin)
[command, prompt template]

## Pass 4 — CLI (confirm)
[npm + winget commands, failure handling]

## Pass 5 — Hooks deps (confirm)
[settings.json + hooks parsing, npm install]

## Pass 6 — MCP check (read-only)
[claude mcp list, parse ✓/✗]

## Pass 7 — Cache cleanup (confirm)
[orphan detection, rm -rf, prune]

## Pass 8 — Report (read-only)
[report template]

## Common mistakes
[red flags list derived from RED phase]

## Restart
[always required after pass 4 and any plugin update]
```

---

## 12. Open questions (resolved during implementation)

- Q: How does the skill detect which npm globals are referenced by hooks? A: Parse `~/.claude/settings.json` for `mcpServers.*` and `~/.claude/hooks/*.js` for `require()` / `node_modules/<pkg>` patterns. Cross-ref with `npm list -g --depth=0`. Documented in §5 pass 5.
- Q: Does the skill also update skills in `~/.claude/skills/`? A: No. Out of scope (§2). Skills are user-owned files, no canonical update source.
- Q: Should the skill prompt before re-running `claude plugin marketplace update` when marketplaces were updated <1h ago? A: No — `claude plugin marketplace update` is cheap and idempotent. Always run.

---

## 13. Success criteria

The skill is done when:

1. SKILL.md exists at `~/.claude/skills/update-claude-environment/SKILL.md` with the frontmatter specified in §11.
2. RED phase baseline captured (subagent without skill fails in predicted ways).
3. GREEN phase passes (subagent with skill executes 8 passes correctly).
4. Idempotency verified (second run on already-up-to-date state produces clean no-op report).
5. Spec reviewed and committed.
