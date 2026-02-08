---
description: "Brainstorm and plan a new feature before SpecKit pipeline execution. Helps explore ideas, define requirements, and produce an approved idea.md file."
argument-hint: "<feature-description>"
---

# SpecKit Brainstorm

## Overview

This command facilitates feature brainstorming and planning. It guides the user through exploring their feature idea, defining requirements, and producing an approved `idea.md` file that serves as the source of truth for the subsequent SpecKit pipeline.

**Output**: `docs/features/<feature>/idea.md` + `orchestrator-state.json` + git branch

**Next Step**: If all 3 output steps succeed, automatically continue into `/speckit-orchestrator --execute` to start the pipeline. No manual handoff needed.

## When to Use

Use this command when:
- Starting a new feature from scratch
- User has a vague idea that needs refinement
- User wants to explore requirements before implementation
- Preparing for SpecKit pipeline execution

## Workflow

### Step 1: Enter Planning Mode

When invoked, IMMEDIATELY enter planning mode using the `EnterPlanMode` tool.

Planning mode enables:
- Deep codebase exploration
- Architecture analysis
- Requirement gathering
- Design decisions

### Step 2: Brainstorm with User

During planning mode:

1. **Understand the Feature**
   - Ask clarifying questions about the user's intent
   - Explore existing codebase patterns
   - Identify affected components

2. **Define Requirements**
   - Core functionality (must-have)
   - Nice-to-have features (if time permits)
   - Out of scope (explicitly excluded)

3. **Technical Considerations**
   - Architecture impact
   - Database changes
   - API changes
   - UI/UX considerations

4. **Write the Plan**
   - Document findings in the plan file
   - Structure using the idea.md template (see references/)
   - Include all decisions made during brainstorming

### Step 3: Get User Approval

When the plan is complete:

1. Present the plan summary to user
2. Use `ExitPlanMode` tool to request approval
3. Wait for user to approve or provide feedback

If user provides feedback, iterate on the plan until approved.

### Step 4: Create Feature Artifacts

After user approves the plan, **always execute these 3 steps in order**:

**Extract feature info first:**
- Feature name (kebab-case): e.g., `dark-mode-toggle`
- Ticket number (if provided): e.g., `042`
- Branch name: `<ticket>-<feature-name>` or just `<feature-name>`

**Step 4.1: Create git branch**
```bash
git checkout -b <branch-name>
```

**Step 4.2: Create `docs/features/<feature>/idea.md`**
- Create the directory: `mkdir -p docs/features/<feature-name>`
- Write the approved plan as `docs/features/<feature-name>/idea.md`
- Follow the SpecKit template from `references/idea-template.md`

**Step 4.3: Run `init_feature.py` to create `orchestrator-state.json`**
```bash
python scripts/init_feature.py <feature-name> <branch-name>
```

These 3 steps are the **mandatory output** of the brainstorming process. All 3 must complete successfully before proceeding.

### Step 5: Report and Continue

After all 3 steps complete successfully, display:

```
══════════════════════════════════════════════════════════════
BRAINSTORMING COMPLETE
══════════════════════════════════════════════════════════════

 1. Created git branch: <branch-name>
 2. Created idea.md: docs/features/<feature-name>/idea.md
 3. Created orchestrator-state.json via init_feature.py

Continuing to SpecKit pipeline...
══════════════════════════════════════════════════════════════
```

Then **automatically invoke `/speckit-orchestrator --execute`** to begin the pipeline. No manual handoff needed.

If any of the 3 steps **failed**, STOP, display the failure, and wait for the user to resolve it before continuing.

## Critical Rules

### AUTO-CONTINUE ON SUCCESS

**If all 3 output steps pass, automatically continue into the pipeline.**

- All 3 steps passed → invoke `/speckit-orchestrator --execute`
- Any step failed → STOP, display failure, wait for user
- DO NOT skip failed steps
- DO NOT start implementation directly (always go through orchestrator)

### Plan Must Be Approved

**Never write idea.md without user approval.**

- Use ExitPlanMode to get approval
- Iterate if user has feedback
- idea.md = approved plan only

## idea.md Structure

The idea.md file should follow this structure:

```markdown
# Feature: <Feature Name>

## Summary
<1-2 sentence description>

## Problem Statement
<What problem does this solve?>

## Requirements

### Must Have
- <core requirement 1>
- <core requirement 2>

### Nice to Have
- <optional feature 1>

### Out of Scope
- <explicitly excluded item>

## Technical Approach
<High-level technical decisions>

## Affected Components
- <component 1>
- <component 2>

## Open Questions
<Any unresolved questions for clarify phase>
```

## Resources

### scripts/
- `init_feature.py` - Initialize orchestrator-state.json for a feature

### references/
- `idea-template.md` - Full template for idea.md files
