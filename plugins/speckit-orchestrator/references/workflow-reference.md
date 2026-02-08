# SpecKit Orchestrator Workflow Reference

## Overview

The orchestrator executes the SpecKit pipeline **step by step, with a stop hook providing auto-continuation**:

```
specify → clarify → plan → tasks → analyze → implement
```

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

### Step 4: Tasks

**Command:** `/speckit.tasks`

**Context to pass:**
```
Tasks must trace back to idea.md scope.
No tasks for features outside idea.md.
```

**Output:** `specs/<feature>/tasks.md`

---

### Step 5: Analyze

**Command:** `/speckit.analyze`

**Context to pass:**
```
Check consistency against idea.md.
Flag scope drift as error.
```

**Output:** Analysis report, may update artifacts

---

### Step 6: Implement

**Command:** `/speckit.implement`

**Context to pass:**
```
Implementation must match idea.md exactly.
HALT if scope change is required.
```

**Output:** Implemented code

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
  "current_step": "specify|clarify|plan|tasks|analyze|implement",
  "step_status": {
    "specify": "pending|in_progress|completed|skipped",
    "clarify": "pending|in_progress|completed|skipped",
    "plan": "pending|in_progress|completed|skipped",
    "tasks": "pending|in_progress|completed|skipped",
    "analyze": "pending|in_progress|completed|skipped",
    "implement": "pending|in_progress|completed|skipped"
  },
  "started_at": "ISO8601",
  "last_updated": "ISO8601"
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
| `/speckit-orchestrator --execute` | Run next pipeline step |
| `/speckit-orchestrator --status` | Show progress |
| `/speckit-orchestrator --rollback <step>` | Reset to step |

### Script Commands

```bash
# Initialize state (if doesn't exist)
python orchestrator.py init <feature> <branch>

# Show status
python orchestrator.py status

# Rollback
python orchestrator.py rollback <step>
```

---

## Critical Rules

### ✅ ONE STEP PER EXECUTE (Stop Hook Auto-Continues)

Each `--execute` call:
1. Reads state to find next pending step
2. Reads idea.md for context
3. Runs ONE /speckit.* command
4. **Updates `step_status` to `"completed"` and advances `current_step`**
5. Finishes the turn — the stop hook reads state and auto-feeds the next `--execute`

**DO NOT:**
- ❌ Run multiple /speckit.* commands in a single turn
- ❌ Skip steps
- ❌ Forget to update state (the hook depends on it)

### 📋 FOLLOW idea.md

- Read idea.md before each step
- Pass context about following idea.md
- All output must align with idea.md scope

---

## Progress Display

```
╔════════════════════════════════════════════════════════════════════╗
║  SpecKit Orchestrator                                               ║
╠════════════════════════════════════════════════════════════════════╣
║  Feature: dark-mode-toggle                                          ║
║  Branch: 042-dark-mode-toggle                                       ║
║  Source: docs/features/dark-mode-toggle/idea.md                     ║
╠════════════════════════════════════════════════════════════════════╣
║  [✓] Specify  →  [✓] Clarify  →  [▶] Plan                          ║
║  [ ] Tasks    →  [ ] Analyze  →  [ ] Implement                      ║
╚════════════════════════════════════════════════════════════════════╝
```

**Symbols:**
- `[✓]` Completed
- `[−]` Skipped
- `[▶]` In Progress
- `[ ]` Pending

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
