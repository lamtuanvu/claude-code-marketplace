---
name: speckit-orchestrator
description: Execute the SpecKit pipeline (specify→clarify→plan→tasks→analyze→implement) for a feature. This skill assumes idea.md already exists and runs one pipeline step at a time, following idea.md as the source of truth. Use this after brainstorming is complete and idea.md has been created.
argument-hint: --execute | --status | --rollback <phase>
---

# SpecKit Orchestrator

## Overview

This skill executes the SpecKit pipeline for feature development:

```
specify → clarify → plan → tasks → analyze → implement
```

**Prerequisites:**
- Feature branch exists (e.g., `042-dark-mode-toggle`)
- `docs/features/<feature>/idea.md` exists with the approved plan
- `docs/features/<feature>/orchestrator-state.json` exists

**The orchestrator runs ONE step at a time**, requiring user to trigger each step.

## When to Use

```
/speckit-orchestrator --execute
```

Use this when:
- Brainstorming is complete and idea.md exists
- You want to run the next step in the speckit pipeline
- You're on a feature branch with orchestrator state

## Pipeline Steps

Each `--execute` call runs ONE step, then STOPS:

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
   - Update state
   - **STOP and wait**

4. **Repeat step 2** until all steps complete

### Context for Each Step

When running each `/speckit.*` command, pass this context:

```
Follow docs/features/<feature>/idea.md strictly.
Do not add features beyond what idea.md specifies.
All work must align with the approved plan.
```

### After Each Step

Display:
```
══════════════════════════════════════════════════════════════
✅ STEP COMPLETE: specify
══════════════════════════════════════════════════════════════

Next step: clarify

To continue, run:
  /speckit-orchestrator --execute

══════════════════════════════════════════════════════════════
```

Then **STOP AND WAIT** for user.

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

### ⛔ ONE STEP AT A TIME

**Each --execute runs ONLY ONE /speckit.* command, then STOPS.**

- ❌ DO NOT run multiple /speckit.* commands
- ❌ DO NOT skip steps
- ❌ DO NOT auto-continue
- ✅ Run ONE step, update state, STOP, wait for user

### 📋 FOLLOW idea.md

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

## Example Session

```
User: /speckit-orchestrator --execute

Claude: Reading state... Next step: specify
        Reading idea.md for context...
        Running /speckit.specify...
        [spec.md created]
        Updating state...

        ══════════════════════════════════════════════════════════════
        ✅ STEP COMPLETE: specify
        Next step: clarify
        To continue: /speckit-orchestrator --execute
        ══════════════════════════════════════════════════════════════

User: /speckit-orchestrator --execute

Claude: Reading state... Next step: clarify
        Running /speckit.clarify...
        [clarifications applied or skipped]
        Updating state...

        ══════════════════════════════════════════════════════════════
        ✅ STEP COMPLETE: clarify
        Next step: plan
        To continue: /speckit-orchestrator --execute
        ══════════════════════════════════════════════════════════════

... continues until implement is complete
```

## Error Handling

### Missing idea.md
```
Error: idea.md not found at docs/features/<feature>/idea.md
Create idea.md first (use brainstorming skill or create manually)
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
