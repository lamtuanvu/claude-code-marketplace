---
description: "Brainstorm and plan a new feature using multi-angle analysis (agent team or parallel subagents). Produces an approved idea.md file."
argument-hint: "<feature-description>"
---

# SpecKit Brainstorm

## Overview

This command facilitates feature brainstorming by analyzing the proposed feature from multiple angles simultaneously. Four specialist analysts — UX, architecture, feasibility, and devil's advocate — explore the codebase and challenge the idea in parallel, then the lead synthesizes their findings into a comprehensive `idea.md`.

**Two execution modes:**
- **Agent Teams** (preferred): when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is set, spawns a full team with shared task list and inter-agent messaging
- **Subagent Fallback**: when agent teams are unavailable, spawns 4 parallel subagents via the `Task` tool and collects their reports

Both modes produce identical output. The analysis quality is the same; only the coordination mechanism differs.

**Output**: `docs/features/<feature>/idea.md` + `orchestrator-state.json` + git branch

**Next Step**: After all artifacts are created, automatically continue into `/speckit-orchestrator:execute` to start the pipeline.

## CRITICAL: This Command Produces idea.md ONLY

**DO NOT write any implementation code during brainstorming.**

This command's sole purpose is to produce an approved `idea.md` file. The SpecKit pipeline (`specify → clarify → plan → tasks → analyze → implement`) handles everything else.

## Workflow

### Step 1: Understand the Feature Request

Parse the user's feature description from the command arguments. If the description is too vague to brief analysts on, use `AskUserQuestion` to gather essential context:
- What problem does this solve?
- Who is the target user?
- Any constraints or preferences?

Keep this brief — the analysts will do the deep exploration. You just need enough to write a clear brief.

Extract feature info:
- Feature name (kebab-case): e.g., `dark-mode-toggle`
- Ticket number (if provided): e.g., `042`

### Step 2: Detect Agent Teams Availability

Run the detection script:
```bash
plugins/speckit-orchestrator/scripts/check_teams.sh
```

- **Exit code 0** → agent teams available → follow **Path A: Agent Teams**
- **Exit code 1** → agent teams unavailable → follow **Path B: Subagent Fallback**

Display which mode is being used:
```
🔍 Agent teams: [available|not available]
📋 Using: [agent team|parallel subagents] for multi-angle analysis
```

---

## Path A: Agent Teams

Use this path when `check_teams.sh` exits with code 0.

### A.1: Create the Brainstorm Team

1. **Create the team:**
   ```
   TeamCreate: speckit-<feature-name>-brainstorm
   ```

2. **Create 4 tasks** (one per analyst) using `TaskCreate`:

   | Task | Assignee | Description |
   |------|----------|-------------|
   | UX analysis | `ux-analyst` | Analyze feature from UI/UX perspective |
   | Architecture analysis | `architect` | Analyze feature from architecture perspective |
   | Feasibility analysis | `feasibility-analyst` | Analyze feature for technical feasibility and risks |
   | Devil's advocate | `devils-advocate` | Challenge assumptions and find weaknesses |

### A.2: Spawn Teammates

Spawn all 4 teammates in parallel using the `Task` tool with `team_name` set to your team. Each teammate gets:

- **Their agent instructions** from the corresponding file in `agents/`
- **The feature description** from the user
- **The codebase context** — they will explore it themselves

**Spawn prompt template** (customize per role):
```
You are the [role] for a brainstorm analysis team.

Feature under analysis: "<feature-description>"

Read your agent instructions at plugins/speckit-orchestrator/agents/[agent-file].md,
then explore the codebase to understand the current state.

Analyze this feature from your specialist perspective and write your report.
When done, send your full report to the team lead and mark your task as completed.
```

**Teammates to spawn:**

| Name | Agent file | Subagent type |
|------|-----------|---------------|
| `ux-analyst` | `agents/ux-analyst.md` | `general-purpose` |
| `architect` | `agents/architect.md` | `general-purpose` |
| `feasibility-analyst` | `agents/feasibility-analyst.md` | `general-purpose` |
| `devils-advocate` | `agents/devils-advocate.md` | `general-purpose` |

Assign each teammate their corresponding task via `TaskUpdate`.

### A.3: Monitor and Coordinate

While teammates work:

1. **Use delegate mode** (Shift+Tab) — do NOT explore the codebase yourself; let the team do the analysis
2. **Monitor `TaskList`** periodically to check progress
3. **Respond to teammate messages** if they have questions
4. **Wait for all 4 teammates to complete** before proceeding

If a teammate gets stuck or fails:
- Send them a message with guidance
- If unrecoverable, note the gap and proceed with the remaining analyses

### A.4: Collect Reports

Teammates send their reports via messages to the lead. Collect all 4 reports and proceed to **Step 3: Synthesize into idea.md Draft**.

### A.5: Shut Down the Team

After collecting all reports:

1. Send `shutdown_request` to each teammate
2. Wait for shutdown confirmations
3. Run `TeamDelete` to clean up team resources

Then proceed to **Step 3: Synthesize into idea.md Draft**.

---

## Path B: Subagent Fallback

Use this path when `check_teams.sh` exits with code 1 (agent teams unavailable).

### B.1: Launch 4 Parallel Subagents

Spawn all 4 analysts simultaneously using the `Task` tool (NOT as a team — just parallel subagent calls). Launch all 4 in a **single message** so they run concurrently:

**Subagent prompt template** (customize per role):
```
You are the [role] analyst for a feature brainstorm.

Feature under analysis: "<feature-description>"

Read your agent instructions at plugins/speckit-orchestrator/agents/[agent-file].md,
then explore the codebase to understand the current state.

Analyze this feature from your specialist perspective.

Return your FULL analysis report as your final output. Use the report format
described in your agent instructions.
```

**Subagents to launch (all in parallel):**

| Description | Agent file | Subagent type |
|-------------|-----------|---------------|
| `UX analysis` | `agents/ux-analyst.md` | `Explore` |
| `Architecture analysis` | `agents/architect.md` | `Explore` |
| `Feasibility analysis` | `agents/feasibility-analyst.md` | `Explore` |
| `Devil's advocate` | `agents/devils-advocate.md` | `Explore` |

Use subagent_type `Explore` since these are read-only analysis tasks — no file editing needed.

### B.2: Collect Reports

Each subagent returns its report directly as the tool result. Collect all 4 reports. If any subagent fails, note the gap and proceed with the available reports.

Then proceed to **Step 3: Synthesize into idea.md Draft**.

---

## Common Steps (Both Paths)

### Step 3: Synthesize into idea.md Draft

Once all analyst reports are collected (from either Path A or Path B), synthesize their findings into a unified `idea.md` draft.

Read all reports and combine them:
- **UX analyst** → informs User Stories, UI/UX section, and relevant requirements
- **Architect** → informs Technical Approach, Architecture, Affected Components, Dependencies
- **Feasibility analyst** → informs Technical Approach, Testing Strategy, risk-related requirements
- **Devil's advocate** → informs Out of Scope, Open Questions, and any adjusted requirements

**idea.md template:**

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

## Risks & Mitigations
- <Risk 1> — <Mitigation>
- <Risk 2> — <Mitigation>

## Open Questions
1. <Any unresolved questions for the clarify phase>

## Success Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
```

### Step 4: Present to User for Approval

Present the synthesized `idea.md` draft to the user using `AskUserQuestion`:

```
Here's the synthesized idea.md based on analysis from 4 specialist analysts
(UX, Architecture, Feasibility, Devil's Advocate):

<display the full idea.md draft>

Does this look good, or would you like changes?
```

**Options:**
- **Approve** → proceed to Step 5
- **Request changes** → revise the draft based on feedback, present again
- **Reject** → do not create any artifacts

Iterate until the user approves.

### Step 5: Create Feature Artifacts (ONLY After Approval)

After the user approves the idea.md draft:

**Step 5.1: Create git branch**
```bash
git checkout -b <branch-name>
```
Branch name: `<ticket>-<feature-name>` or just `<feature-name>`

**Step 5.2: Write `docs/features/<feature>/idea.md`**
- Create the directory: `mkdir -p docs/features/<feature-name>`
- Write the **approved draft** as `docs/features/<feature-name>/idea.md`

**Step 5.3: Create `orchestrator-state.json`**

Write the state file to `docs/features/<feature-name>/orchestrator-state.json`:

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

**Step 5.4: Verify the state file**

Read back the state file and confirm:
- `current_step` is `"specify"`
- All 7 steps are present and `"pending"`
- `idea_file` path matches the idea.md you wrote

### Step 6: Report and Continue to Pipeline

After all artifacts are created, display:

```
══════════════════════════════════════════════════════════════
BRAINSTORMING COMPLETE
══════════════════════════════════════════════════════════════

 Analysis mode: [Agent Team | Parallel Subagents]
   [✓] UX Analyst
   [✓] Architect
   [✓] Feasibility Analyst
   [✓] Devil's Advocate

 Artifacts:
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

Then **automatically invoke `/speckit-orchestrator:execute`** to begin the pipeline.

If any artifact creation step **failed**, STOP and wait for the user to resolve it.

## Critical Rules

### DETECT AND ADAPT

**Always check `check_teams.sh` before choosing a path.** Use agent teams when available for richer collaboration; fall back to subagents seamlessly when not. Both paths must produce the same quality output.

### NO PLAN MODE

This command uses parallel analysis (team or subagents). Do NOT use `EnterPlanMode`. The analysts do the exploration work; the lead synthesizes and coordinates.

### NO CODE, NO IMPLEMENTATION

**This command produces `idea.md` ONLY.** Do not:
- Write any implementation code
- Create any source files
- Modify any existing code
- Run any build/test commands
- Skip ahead to implementation

The SpecKit pipeline handles everything after `idea.md` is created.

### WAIT FOR ALL ANALYSTS

**Do not synthesize until all analysts have reported back** (or failed). The value of this approach is getting multiple independent perspectives. Synthesizing early defeats the purpose.

### USER MUST APPROVE idea.md

**Never write idea.md without user approval.**

- Present the synthesized draft via `AskUserQuestion`
- Iterate if user has feedback
- Only write `idea.md` after explicit approval

### AUTO-CONTINUE TO PIPELINE

After artifacts are created:
- All steps passed → invoke `/speckit-orchestrator:execute` (starts with `specify`)
- Any step failed → STOP, display failure, wait for user
- DO NOT skip the pipeline and jump to implementation

### CLEAN UP (Agent Teams Path Only)

**Always shut down teammates and delete the team** before creating artifacts. The brainstorm team is temporary — it exists only for the analysis phase. This does not apply to the subagent fallback path (subagents clean up automatically).

## Resources

### agents/
- `ux-analyst.md` — UI/UX analysis agent
- `architect.md` — Architecture analysis agent
- `feasibility-analyst.md` — Technical feasibility agent
- `devils-advocate.md` — Assumption challenger agent

### scripts/
- `check_teams.sh` — Detect agent-teams availability
- `init_feature.py` — Initialize orchestrator-state.json for a feature

### references/
- `idea-template.md` — Full template for idea.md files

### assets/
- `idea-template.md` — Simplified brainstorming template
