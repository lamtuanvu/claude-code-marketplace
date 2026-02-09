# SpecKit Orchestrator Workflow Reference

## Overview

The orchestrator executes the SpecKit pipeline **step by step, with a stop hook providing auto-continuation**:

```
specify → clarify → plan → [plan-review] → tasks → analyze → implement
                             ^                                  ^
                        Team phase                         Team phase
```

Steps in brackets `[]` use agent teams when enabled. When teams are disabled, `plan-review` is skipped and `implement` runs sequentially.

**Prerequisites:**
- Feature branch exists
- `docs/features/<feature>/idea.md` exists
- `docs/features/<feature>/orchestrator-state.json` exists

## Pipeline Steps

### Step 1: Specify

**Command:** `/speckit.specify`

**Context to pass:**
```
Follow docs/features/<feature>/idea.md strictly.
Generate spec from the approved plan.
Do not add features beyond what idea.md specifies.
```

**Output:** `specs/<feature>/spec.md`

---

### Step 2: Clarify

**Command:** `/speckit.clarify`

**Context to pass:**
```
Reference idea.md for original intent.
Clarifications must stay within idea.md scope.
```

**Output:** Updated `spec.md` (may skip if spec is clear)

---

### Step 3: Plan

**Command:** `/speckit.plan`

**Context to pass:**
```
Implementation plan MUST align with idea.md.
Technical decisions in idea.md take precedence.
```

**Output:** `specs/<feature>/plan.md`, `research.md`, `data-model.md`, etc.

---

### Step 4: Plan Review (Team Phase)

**Requires:** `teams_enabled: true`

**When skipped:** If `teams_enabled` is false, this step is automatically skipped.

**Procedure:**
1. Create team: `speckit-<feature>-plan-review`
2. Spawn specialist reviewers in parallel:
   - `security-reviewer` → `reviews/security.md`
   - `performance-reviewer` → `reviews/performance.md`
   - `conventions-reviewer` → `reviews/conventions.md`
   - `ui-reviewer` (conditional) → `reviews/ui.md`
3. Monitor via TaskList until all complete
4. Consolidate into `reviews/summary.md`
5. If any reviewer says "REVISE REQUIRED" → pause for user
6. Teardown team, advance to tasks

**See:** `references/team-workflow-reference.md` for detailed team procedures.

---

### Step 5: Tasks

**Command:** `/speckit.tasks`

**Context to pass:**
```
Tasks must trace back to idea.md scope.
No tasks for features outside idea.md.
```

**Output:** `specs/<feature>/tasks.md`

---

### Step 6: Analyze

**Command:** `/speckit.analyze`

**Context to pass:**
```
Check consistency against idea.md.
Flag scope drift as error.
```

**Output:** Analysis report, may update artifacts

---

### Step 7: Implement (Team Phase when enabled)

**Command:** `/speckit.implement` (sequential) or team phase (parallel)

**When teams enabled:**
1. Run `partition_tasks.py` to group tasks by file ownership
2. Create team: `speckit-<feature>-implement`
3. Spawn implementers (max 3) + test writer in parallel
4. After completion, spawn QA reviewer
5. Consolidate and teardown

**When teams disabled:**
```
Implementation must match idea.md exactly.
HALT if scope change is required.
```

**Output:** Implemented code + tests

---

## State Management

### State File Location
```
docs/features/<feature>/orchestrator-state.json
```

### State Schema
```json
{
  "feature_name": "string",
  "branch_name": "string",
  "idea_file": "string",
  "spec_dir": "string",
  "current_step": "specify|clarify|plan|plan-review|tasks|analyze|implement",
  "step_status": {
    "specify": "pending|in_progress|completed|skipped",
    "clarify": "pending|in_progress|completed|skipped",
    "plan": "pending|in_progress|completed|skipped",
    "plan-review": "pending|in_progress|completed|skipped",
    "tasks": "pending|in_progress|completed|skipped",
    "analyze": "pending|in_progress|completed|skipped",
    "implement": "pending|in_progress|completed|skipped"
  },
  "started_at": "ISO8601",
  "last_updated": "ISO8601",
  "teams_enabled": true,
  "team_state": null
}
```

### Team State (when active)
```json
{
  "team_state": {
    "active_team": "speckit-<feature>-plan-review",
    "phase": "plan-review",
    "teammates": {
      "security-reviewer": { "status": "in_progress", "output": "reviews/security.md" },
      "performance-reviewer": { "status": "completed", "output": "reviews/performance.md" }
    },
    "started_at": "ISO8601",
    "timeout_minutes": 15
  }
}
```

### Updating State After Each Step

```json
{
  "step_status": {
    "specify": "completed"
  },
  "current_step": "clarify",
  "last_updated": "2025-02-04T12:00:00Z"
}
```

---

## Command Reference

| Command | Description |
|---------|-------------|
| `/speckit-orchestrator:execute` | Run next pipeline step |
| `/speckit-orchestrator:status` | Show progress |
| `/speckit-orchestrator:rollback <step>` | Reset to step |
| `/speckit-orchestrator:cancel-pipeline` | Pause pipeline |

### Script Commands

```bash
# Initialize state
python orchestrator.py init <feature> <branch>
python orchestrator.py init <feature> <branch> --no-teams

# Show status
python orchestrator.py status

# Show team status
python orchestrator.py team-status

# Rollback
python orchestrator.py rollback <step>

# Partition tasks for parallel implementation
python partition_tasks.py specs/<feature>/tasks.md

# Check team availability
./check_teams.sh
```

---

## Critical Rules

### ONE STEP PER EXECUTE (Stop Hook Auto-Continues)

Each `/speckit-orchestrator:execute` call:
1. Reads state to find next pending step
2. Reads idea.md for context
3. Runs ONE /speckit.* command (or manages one team phase)
4. **Updates `step_status` to `"completed"` and advances `current_step`**
5. Finishes the turn — the stop hook reads state and auto-feeds the next `/speckit-orchestrator:execute`

**DO NOT:**
- Run multiple /speckit.* commands in a single turn
- Skip steps
- Forget to update state (the hook depends on it)

### TEAM STATE (for team phases)

- Set `team_state` when starting a team phase
- Update teammate status as they complete
- Clear `team_state` before marking the step complete
- The stop hook blocks premature stops while teammates are working

### FOLLOW idea.md

- Read idea.md before each step
- Pass context about following idea.md
- All output must align with idea.md scope

---

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
╚════════════════════════════════════════════════════════════════════════════╝
```

**Symbols:**
- `[✓]` Completed
- `[−]` Skipped
- `[▶]` In Progress
- `[ ]` Pending
- `⚡` Team step (parallel agents)

---

## After Step Completion

Display:
```
══════════════════════════════════════════════════════════════
✅ STEP COMPLETE: <step-name>
══════════════════════════════════════════════════════════════

Next step: <next-step>
══════════════════════════════════════════════════════════════
```

The stop hook will detect the updated state and auto-continue to the next step.
