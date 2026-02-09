---
description: "Execute the next step in the SpecKit pipeline (specify->clarify->plan->plan-review->tasks->analyze->implement). Supports agent-teams for parallel plan review and implementation. Assumes idea.md exists."
allowed-tools: ["Bash(python *orchestrator.py*)", "Bash(python *partition_tasks.py*)", "Bash(*check_teams.sh*)", "Read(docs/features/*/orchestrator-state.json)", "Read(docs/features/*/idea.md)", "Read(specs/*/spec.md)", "Read(specs/*/plan.md)", "Read(specs/*/tasks.md)"]
---

# SpecKit Orchestrator — Execute

## Overview

This command executes the next step in the SpecKit pipeline for feature development:

```
specify → clarify → plan → [plan-review] → tasks → analyze → implement
                             ^                                  ^
                        Team phase (parallel           Team phase (parallel
                        specialist reviews)            implementation + tests)
```

**Prerequisites:**
- Feature branch exists (e.g., `042-dark-mode-toggle`)
- `docs/features/<feature>/idea.md` exists with the approved plan
- `docs/features/<feature>/orchestrator-state.json` exists

**The stop hook handles auto-continuation.** After each step, the hook reads `orchestrator-state.json` and feeds `/speckit-orchestrator:execute` to run the next step. It only allows stop when a step fails, the pipeline completes, or the pipeline is paused.

**Agent Teams** (optional): When enabled, `plan-review` and `implement` steps use multi-agent teams for parallel work. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Falls back to sequential when unavailable.

## When to Use

```
/speckit-orchestrator:execute
```

Use this when:
- Brainstorming is complete and idea.md exists
- You want to run the next step in the speckit pipeline
- You're on a feature branch with orchestrator state

## Pipeline Steps

Each execute call runs the next step. The stop hook auto-continues on success:

| Step | Command | Purpose | Team? |
|------|---------|---------|-------|
| 1 | `/speckit.specify` | Generate spec.md from idea.md | No |
| 2 | `/speckit.clarify` | Resolve ambiguities (may skip) | No |
| 3 | `/speckit.plan` | Generate implementation plan | No |
| 4 | Team phase | Parallel specialist plan reviews | Yes |
| 5 | `/speckit.tasks` | Generate tasks.md | No |
| 6 | `/speckit.analyze` | Check consistency | No |
| 7 | `/speckit.implement` | Execute tasks (parallel if teams) | Yes |

Steps marked "Team?" use agent teams when `teams_enabled` is true. When false, step 4 is skipped and step 7 runs sequentially.

## Execution Instructions

### Running the Pipeline

1. **Switch to feature branch:**
   ```bash
   git checkout 042-dark-mode-toggle
   ```

2. **Run next step:**
   ```
   /speckit-orchestrator:execute
   ```

3. **Orchestrator will:**
   - Read `orchestrator-state.json` to find next pending step
   - Read `idea.md` for context
   - Run the appropriate `/speckit.*` command (or team phase)
   - **Update `step_status` to `"completed"` and advance `current_step`** (this is the signal the stop hook reads)
   - **If step failed → STOP and wait for user**

4. The **stop hook** detects the completed step and auto-feeds `/speckit-orchestrator:execute` for the next step. Pipeline runs to completion unless a step fails.

### Context for Each Step

When running each `/speckit.*` command, pass this context:

```
Follow docs/features/<feature>/idea.md strictly.
Do not add features beyond what idea.md specifies.
All work must align with the approved plan.
```

### After Each Step (Critical for Stop Hook)

**You MUST update `orchestrator-state.json` before finishing:**
1. Set the current step's `step_status` to `"completed"`
2. Set `current_step` to the next step name
3. Update `last_updated` timestamp

The stop hook reads these fields to decide whether to auto-continue.

**On success**, display a brief status:
```
✅ specify — complete.
```

**On failure**, display the error and STOP:
```
══════════════════════════════════════════════════════════════
❌ STEP FAILED: clarify
══════════════════════════════════════════════════════════════

Error: <description of what went wrong>

Fix the issue, then run:
  /speckit-orchestrator:execute

══════════════════════════════════════════════════════════════
```

### After All Steps Complete

Display:
```
══════════════════════════════════════════════════════════════
✅ PIPELINE COMPLETE
══════════════════════════════════════════════════════════════

 [✓] Specify   →  [✓] Clarify      →  [✓] Plan     →  [✓] Plan Review ⚡
 [✓] Tasks     →  [✓] Analyze      →  [✓] Implement ⚡

Feature <feature-name> is fully implemented.
══════════════════════════════════════════════════════════════
```

---

## Team Steps

### Detecting Team Availability

Before running a team step, check:
1. Is `teams_enabled` true in state?
2. Run `scripts/check_teams.sh` to verify agent-teams is available
3. If either fails → set `teams_enabled: false`, skip `plan-review`, run `implement` sequentially

### Plan Review Team Phase (Step 4)

**Trigger:** `plan` step completed, `teams_enabled` is true.

**Procedure:**

1. **Check for UI keywords** in `idea.md`:
   Search for: `UI`, `frontend`, `component`, `design`, `page`, `form`, `modal`, `dialog`, `button`, `layout`, `responsive`, `CSS`, `style`, `theme`
   If found → spawn `ui-reviewer` alongside other reviewers

2. **Create team:**
   ```
   TeamCreate: speckit-<feature>-plan-review
   ```

3. **Update state:**
   ```json
   {
     "current_step": "plan-review",
     "step_status": { "plan-review": "in_progress" },
     "team_state": {
       "active_team": "speckit-<feature>-plan-review",
       "phase": "plan-review",
       "teammates": {
         "security-reviewer": { "status": "in_progress", "output": "reviews/security.md" },
         "performance-reviewer": { "status": "in_progress", "output": "reviews/performance.md" },
         "conventions-reviewer": { "status": "in_progress", "output": "reviews/conventions.md" }
       },
       "started_at": "<ISO8601>",
       "timeout_minutes": 15
     }
   }
   ```

4. **Spawn teammates** (all in parallel):
   - `security-reviewer` — read `agents/security-reviewer.md`, mode: plan
   - `performance-reviewer` — read `agents/performance-reviewer.md`, mode: plan
   - `conventions-reviewer` — read `agents/conventions-reviewer.md`, mode: plan
   - `ui-reviewer` (conditional) — read `agents/ui-reviewer.md`, mode: plan

5. **Monitor:** Poll `TaskList` until all teammates are `completed` or `failed`

6. **Consolidate findings:**
   - Read all `specs/<feature>/reviews/*.md` files
   - Create `specs/<feature>/reviews/summary.md` with combined verdict
   - If any reviewer says "REVISE REQUIRED" → pause pipeline for user review
   - If all PASS → continue automatically

7. **Teardown:**
   - `SendMessage` type: `shutdown_request` to each teammate
   - `TeamDelete`
   - Clear `team_state` in state
   - Set `plan-review: "completed"`, advance `current_step` to `tasks`

### Implementation Team Phase (Step 7)

**Trigger:** `analyze` step completed, `teams_enabled` is true.

**Procedure:**

1. **Partition tasks:**
   ```bash
   python scripts/partition_tasks.py specs/<feature>/tasks.md --max-groups 3
   ```
   If `parallelizable: false` → run sequential implementation (no team)

2. **Create team:**
   ```
   TeamCreate: speckit-<feature>-implement
   ```

3. **Update state** with team_state (similar to plan-review)

4. **Spawn teammates:**
   - `implementer-1` through `implementer-N` (max 3) — each with assigned task group and file ownership
   - `test-writer` — read `agents/test-writer.md`, starts immediately alongside implementers
   - After implementers + test writer finish:
   - `qa-reviewer` — read `agents/qa-reviewer.md`, mode: plan

5. **Monitor and coordinate:**
   - The lead uses **delegate mode** (coordination only, no direct code changes)
   - Monitor `TaskList` for completion
   - Handle file ownership conflicts if they arise
   - Re-assign failed tasks if possible

6. **After QA:**
   - Read `specs/<feature>/reviews/qa.md`
   - If FAIL → pause pipeline for user review
   - If PASS → continue to completion

7. **Teardown:** Same as plan-review team

---

## State Management

### State File
```
docs/features/<feature>/orchestrator-state.json
```

### State Schema
```json
{
  "feature_name": "dark-mode-toggle",
  "branch_name": "042-dark-mode-toggle",
  "idea_file": "docs/features/dark-mode-toggle/idea.md",
  "spec_dir": "specs/dark-mode-toggle",
  "current_step": "specify",
  "step_status": {
    "specify": "pending",
    "clarify": "pending",
    "plan": "pending",
    "plan-review": "pending",
    "tasks": "pending",
    "analyze": "pending",
    "implement": "pending"
  },
  "started_at": "ISO8601",
  "last_updated": "ISO8601",
  "teams_enabled": true,
  "team_state": null
}
```

### Updating State

After each step completes:
```json
{
  "step_status": {
    "specify": "completed"
  },
  "current_step": "clarify"
}
```

During team phases, also update `team_state` with teammate progress.

## Progress Display

```
╔════════════════════════════════════════════════════════════════════════════╗
║  SpecKit Orchestrator (Teams Enabled)                                      ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Feature: dark-mode-toggle                                                 ║
║  Branch: 042-dark-mode-toggle                                              ║
║  Source: docs/features/dark-mode-toggle/idea.md                            ║
╠════════════════════════════════════════════════════════════════════════════╣
║  [✓] Specify  →  [✓] Clarify  →  [✓] Plan  →  [▶] Plan Review ⚡          ║
║  [ ] Tasks    →  [ ] Analyze  →  [ ] Implement ⚡                          ║
╠════════════════════════════════════════════════════════════════════════════╣
║  Team: speckit-dark-mode-toggle-plan-review                                ║
║    [✓] security-reviewer                                                   ║
║    [▶] performance-reviewer                                                ║
║    [▶] conventions-reviewer                                                ║
╚════════════════════════════════════════════════════════════════════════════╝
```

**Symbols:**
- `[✓]` Completed
- `[−]` Skipped
- `[▶]` In Progress
- `[ ]` Pending
- `⚡` Team step (parallel agents)

## Critical Rules

### UPDATE STATE ON SUCCESS (Stop Hook Signal)

**The stop hook reads `orchestrator-state.json` to decide auto-continuation. You MUST update state after each step.**

- Step succeeded → set `step_status` to `"completed"`, advance `current_step`, then finish your turn
- Step failed → output "STEP FAILED", leave state as-is, stop for user to fix
- DO NOT skip steps
- DO NOT continue past a failed step

### TEAM STATE MANAGEMENT

**During team phases, keep `team_state` updated:**

- Team started → set `team_state` with all teammates and their status
- Teammate finished → update their status in `team_state`
- All done → clear `team_state` before marking step complete
- The stop hook checks `team_state` to block premature stops

### FOLLOW idea.md

**All steps must follow idea.md strictly.**

- Read idea.md before running any /speckit.* command
- Pass context about following idea.md
- Flag scope drift as error

## Setup (if state doesn't exist)

If `orchestrator-state.json` doesn't exist but `idea.md` does:

1. Create the state file:
   ```bash
   python orchestrator.py init <feature-name> <branch-name>
   ```
   Or without teams:
   ```bash
   python orchestrator.py init <feature-name> <branch-name> --no-teams
   ```

2. Then run:
   ```
   /speckit-orchestrator:execute
   ```

## Error Handling

### Missing idea.md
```
Error: idea.md not found at docs/features/<feature>/idea.md
Create idea.md first (use /speckit-orchestrator:brainstorm or create manually)
```

### Missing state file
```
Error: orchestrator-state.json not found
Run: python orchestrator.py init <feature> <branch>
```

### Team creation failure
```
Warning: Agent teams unavailable, falling back to sequential execution
```
Sets `teams_enabled: false` and continues without teams.

### Teammate failure
- Single reviewer fails → continue with remaining reviewers, note gap in summary
- Implementer fails → lead re-assigns tasks or handles directly
- Test writer fails → non-critical, log warning and continue
- All teammates fail → treat as step failure, allow stop for user intervention

### Teammate timeout
If `team_state.started_at` exceeds `timeout_minutes`:
- Stop hook allows stop with warning
- Lead should check partial results and proceed or abort

### Scope drift detected
If analyze finds artifacts drifting from idea.md:
- Flag as error
- HALT
- User must fix or update idea.md
