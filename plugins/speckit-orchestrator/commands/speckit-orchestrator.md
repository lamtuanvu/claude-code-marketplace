---
description: "Execute the SpecKit pipeline (specify->clarify->plan->tasks->analyze->implement) for a feature. Assumes idea.md exists. Use after brainstorming is complete."
argument-hint: "--execute | --status | --rollback <phase>"
---

# SpecKit Orchestrator

## Overview

This command executes the SpecKit pipeline for feature development:

```
specify → clarify → plan → tasks → analyze → implement
```

**Prerequisites:**
- Feature branch exists (e.g., `042-dark-mode-toggle`)
- `docs/features/<feature>/idea.md` exists with the approved plan
- `docs/features/<feature>/orchestrator-state.json` exists

**The stop hook handles auto-continuation.** After each step, the hook reads `orchestrator-state.json` and feeds `/speckit-orchestrator --execute` to run the next step. It only allows stop when a step fails, the pipeline completes, or the pipeline is paused.

## When to Use

```
/speckit-orchestrator --execute
```

Use this when:
- Brainstorming is complete and idea.md exists
- You want to run the next step in the speckit pipeline
- You're on a feature branch with orchestrator state

## Pipeline Steps

Each `--execute` call runs the next step. The stop hook auto-continues on success:

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `/speckit.specify` | Generate spec.md from idea.md |
| 2 | `/speckit.clarify` | Resolve ambiguities (may skip) |
| 3 | `/speckit.plan` | Generate implementation plan |
| 4 | `/speckit.tasks` | Generate tasks.md |
| 5 | `/speckit.analyze` | Check consistency |
| 6 | `/speckit.implement` | Execute tasks |

## Execution Instructions

### Running the Pipeline

1. **Switch to feature branch:**
   ```bash
   git checkout 042-dark-mode-toggle
   ```

2. **Run next step:**
   ```
   /speckit-orchestrator --execute
   ```

3. **Orchestrator will:**
   - Read `orchestrator-state.json` to find next pending step
   - Read `idea.md` for context
   - Run the appropriate `/speckit.*` command
   - **Update `step_status` to `"completed"` and advance `current_step`** (this is the signal the stop hook reads)
   - **If step failed → STOP and wait for user**

4. The **stop hook** detects the completed step and auto-feeds `/speckit-orchestrator --execute` for the next step. Pipeline runs to completion unless a step fails.

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
  /speckit-orchestrator --execute

══════════════════════════════════════════════════════════════
```

### After All Steps Complete

Display:
```
══════════════════════════════════════════════════════════════
✅ PIPELINE COMPLETE
══════════════════════════════════════════════════════════════

 [✓] Specify  →  [✓] Clarify  →  [✓] Plan
 [✓] Tasks    →  [✓] Analyze  →  [✓] Implement

Feature <feature-name> is fully implemented.
══════════════════════════════════════════════════════════════
```

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
    "tasks": "pending",
    "analyze": "pending",
    "implement": "pending"
  },
  "started_at": "ISO8601",
  "last_updated": "ISO8601"
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

## Command Reference

| Command | Description |
|---------|-------------|
| `/speckit-orchestrator --execute` | Run next pipeline step |
| `/speckit-orchestrator --status` | Show current progress |
| `/speckit-orchestrator --rollback <step>` | Reset to a step |
| `/speckit-orchestrator:cancel-pipeline` | Pause pipeline (stop hook allows exit) |

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

## Critical Rules

### UPDATE STATE ON SUCCESS (Stop Hook Signal)

**The stop hook reads `orchestrator-state.json` to decide auto-continuation. You MUST update state after each step.**

- Step succeeded → set `step_status` to `"completed"`, advance `current_step`, then finish your turn
- Step failed → output "STEP FAILED", leave state as-is, stop for user to fix
- DO NOT skip steps
- DO NOT continue past a failed step

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

2. Then run:
   ```
   /speckit-orchestrator --execute
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

### Scope drift detected
If analyze finds artifacts drifting from idea.md:
- Flag as error
- HALT
- User must fix or update idea.md
