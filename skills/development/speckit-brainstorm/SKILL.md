---
name: speckit-brainstorm
description: Brainstorm and plan a new feature before SpecKit pipeline execution. This skill should be used when starting a new feature from scratch, helping users explore ideas, define requirements, and produce an approved idea.md file. After completion, use speckit-orchestrator to execute the pipeline.
argument-hint: <feature-description>
---

# SpecKit Brainstorm

## Overview

This skill facilitates feature brainstorming and planning. It guides the user through exploring their feature idea, defining requirements, and producing an approved `idea.md` file that serves as the source of truth for the subsequent SpecKit pipeline.

**Output**: `docs/features/<feature>/idea.md` + `orchestrator-state.json` + git branch

**Next Step**: After this skill completes, run `/speckit-orchestrator --execute` to start the pipeline.

## When to Use

Use this skill when:
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

After user approves the plan:

1. **Extract Feature Information**
   - Feature name (kebab-case): e.g., `dark-mode-toggle`
   - Ticket number (if provided): e.g., `042`
   - Branch name: `<ticket>-<feature-name>` or just `<feature-name>`

2. **Create Git Branch**
   ```bash
   git checkout -b <branch-name>
   ```

3. **Create Feature Directory**
   ```bash
   mkdir -p docs/features/<feature-name>
   ```

4. **Write idea.md**
   - Location: `docs/features/<feature-name>/idea.md`
   - Content: The approved plan from planning mode
   - Use the template structure from `references/idea-template.md`

5. **Create orchestrator-state.json**
   Run the initialization script:
   ```bash
   python scripts/init_feature.py <feature-name> <branch-name>
   ```

### Step 5: STOP and Provide Next Steps

After creating all artifacts, display:

```
══════════════════════════════════════════════════════════════
✅ BRAINSTORMING COMPLETE
══════════════════════════════════════════════════════════════

Feature: <feature-name>
Branch: <branch-name>
Idea file: docs/features/<feature-name>/idea.md

To start the SpecKit pipeline, run:
  /speckit-orchestrator --execute

══════════════════════════════════════════════════════════════
```

Then **STOP AND WAIT**. Do NOT automatically start the pipeline.

## Critical Rules

### ⛔ STOP AFTER idea.md

**After creating idea.md and orchestrator-state.json, STOP immediately.**

- ❌ DO NOT run /speckit.* commands
- ❌ DO NOT start implementation
- ❌ DO NOT auto-continue to pipeline
- ✅ Display completion message
- ✅ Wait for user to run /speckit-orchestrator

### 📋 Plan Must Be Approved

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
