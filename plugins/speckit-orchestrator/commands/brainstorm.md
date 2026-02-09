---
description: "Brainstorm and plan a new feature before SpecKit pipeline execution. Helps explore ideas, define requirements, and produce an approved idea.md file."
argument-hint: "<feature-description>"
---

# SpecKit Brainstorm

## Overview

This command facilitates feature brainstorming and planning. It guides the user through exploring their feature idea, defining requirements, and producing an approved `idea.md` file that serves as the source of truth for the subsequent SpecKit pipeline.

**Output**: `docs/features/<feature>/idea.md` + `orchestrator-state.json` + git branch

**Next Step**: After all artifacts are created, automatically continue into `/speckit-orchestrator:execute` to start the pipeline. The pipeline handles specification, planning, and implementation — this command only produces `idea.md`.

## CRITICAL: This Command Produces idea.md ONLY

**DO NOT write any implementation code during brainstorming.**

This command's sole purpose is to produce an approved `idea.md` file. The SpecKit pipeline (`specify → clarify → plan → tasks → analyze → implement`) handles everything else. After brainstorming completes, the orchestrator takes over.

## Workflow

### Step 1: Enter Planning Mode (MANDATORY FIRST ACTION)

**IMMEDIATELY call `EnterPlanMode` as your very first action.** Do not read files, do not respond to the user, do not do anything else first. Call `EnterPlanMode` right away.

Planning mode is essential because:
- It prevents any code changes during brainstorming
- It gives you read-only access to explore the codebase
- The plan file becomes the draft of `idea.md`
- The user must explicitly approve before anything is written

### Step 2: Brainstorm with User (Inside Plan Mode)

While in plan mode, collaborate with the user to refine their idea:

1. **Understand the Feature**
   - Parse the user's feature description from the command arguments
   - Ask clarifying questions about intent, scope, and priorities
   - Explore the existing codebase to understand context
   - Identify affected components and dependencies

2. **Define Requirements**
   - Core functionality (must-have P0)
   - Nice-to-have features (P1, if time permits)
   - Out of scope (explicitly excluded)

3. **Technical Considerations**
   - Architecture impact
   - Database changes
   - API changes
   - UI/UX considerations

4. **Use `AskUserQuestion` to resolve ambiguities** — don't guess at requirements

### Step 3: Write the Plan File AS idea.md Content

**The plan file you write IS the draft of idea.md.** Structure the plan file content using the idea.md template below. This is what the user will review and approve.

Write the plan file with this exact structure:

```markdown
# Feature: <Feature Name>

## Summary
<1-2 sentence description of what this feature does>

## Problem Statement
<What problem does this feature solve? Why is it needed?>

## User Stories
- As a [user type], I want to [action] so that [benefit]

## Requirements

### Must Have (P0)
- [ ] <core requirement 1>
- [ ] <core requirement 2>

### Nice to Have (P1)
- [ ] <optional feature 1>

### Out of Scope
- <excluded item> — <reason>

## Technical Approach

### Architecture
<High-level architecture decisions>

### Database Changes
<Any new tables, columns, or migrations — or "None">

### API Changes
<New or modified endpoints — or "None">

### UI/UX
<User interface considerations — or "None">

## Affected Components
- <file or module 1>
- <file or module 2>

## Dependencies
- <external dependency or prerequisite>

## Testing Strategy
- Unit tests for: <components>
- Integration tests for: <flows>

## Open Questions
1. <Any unresolved questions for the clarify phase>

## Success Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
```

### Step 4: Exit Plan Mode for User Approval

When the plan is complete, call `ExitPlanMode` to present it to the user.

- **User approves** → proceed to Step 5
- **User provides feedback** → revise the plan and call `ExitPlanMode` again
- **User rejects** → stop, do not create any artifacts

**DO NOT use `AskUserQuestion` to ask "Is this plan okay?" — that is what `ExitPlanMode` does.**

### Step 5: Create Feature Artifacts (ONLY After Approval)

After the user approves the plan, execute these 4 steps in order:

**First, extract feature info:**
- Feature name (kebab-case): e.g., `dark-mode-toggle`
- Ticket number (if provided): e.g., `042`
- Branch name: `<ticket>-<feature-name>` or just `<feature-name>`

**Step 5.1: Create git branch**
```bash
git checkout -b <branch-name>
```

**Step 5.2: Write `docs/features/<feature>/idea.md`**
- Create the directory: `mkdir -p docs/features/<feature-name>`
- Write the **approved plan content** as `docs/features/<feature-name>/idea.md`
- The content is the plan you wrote in Step 3 — copy it exactly as approved

**Step 5.3: Create `orchestrator-state.json`**

Write the state file directly to `docs/features/<feature-name>/orchestrator-state.json` with this exact structure:

```json
{
  "feature_name": "<feature-name>",
  "branch_name": "<branch-name>",
  "idea_file": "docs/features/<feature-name>/idea.md",
  "spec_dir": "specs/<feature-name>",
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
  "started_at": "<ISO8601>",
  "last_updated": "<ISO8601>",
  "teams_enabled": true,
  "team_state": null
}
```

Key points:
- `current_step` MUST be `"specify"` — the pipeline starts from the beginning
- All 7 steps must be present in `step_status`, all set to `"pending"`
- `teams_enabled` defaults to `true` (agent teams for plan-review and implement)
- `team_state` starts as `null` (no team active yet)

**Step 5.4: Verify the state file**

Read back the state file and confirm:
- `current_step` is `"specify"` (NOT `"implement"`)
- All 7 steps are present and `"pending"`
- `idea_file` path matches the idea.md you wrote in Step 5.2

All 4 steps must complete successfully before proceeding.

### Step 6: Report and Continue to Pipeline

After all steps succeed, display:

```
══════════════════════════════════════════════════════════════
BRAINSTORMING COMPLETE
══════════════════════════════════════════════════════════════

 1. Created git branch: <branch-name>
 2. Created idea.md: docs/features/<feature-name>/idea.md
 3. Created orchestrator-state.json (7 steps, starting at specify)
 4. Verified state file

Pipeline: specify → clarify → plan → plan-review → tasks → analyze → implement
          ^
     Starting here

Continuing to SpecKit pipeline...
══════════════════════════════════════════════════════════════
```

Then **automatically invoke `/speckit-orchestrator:execute`** to begin the pipeline. The pipeline will run `specify` as its first step — NOT `implement`.

If any step **failed**, STOP, display the failure, and wait for the user to resolve it.

## Critical Rules

### ENTER PLAN MODE FIRST

**Your very first action MUST be calling `EnterPlanMode`.** No exceptions. No reading files first. No responding to the user first. Call `EnterPlanMode` immediately.

### PLAN FILE = idea.md DRAFT

**The plan file content IS the idea.md content.** Use the template structure above. When the user approves the plan, you write that same content to `idea.md`. The user is approving the idea.md before it's written.

### NO CODE, NO IMPLEMENTATION

**This command produces `idea.md` ONLY.** Do not:
- Write any implementation code
- Create any source files
- Modify any existing code
- Run any build/test commands
- Skip ahead to implementation

The SpecKit pipeline handles everything after `idea.md` is created.

### AUTO-CONTINUE TO PIPELINE (NOT TO IMPLEMENTATION)

After artifacts are created:
- All 3 steps passed → invoke `/speckit-orchestrator:execute` (starts with `specify`)
- Any step failed → STOP, display failure, wait for user
- DO NOT skip the pipeline and jump to implementation
- DO NOT run `/speckit.implement` directly

### PLAN MUST BE APPROVED

**Never write idea.md without user approval via `ExitPlanMode`.**

- Use `ExitPlanMode` to present the plan
- Iterate if user has feedback
- `idea.md` = approved plan only

## Resources

### scripts/
- `init_feature.py` - Initialize orchestrator-state.json for a feature

### references/
- `idea-template.md` - Full template for idea.md files

### assets/
- `idea-template.md` - Simplified brainstorming template
