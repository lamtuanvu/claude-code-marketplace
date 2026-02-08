# Team Workflow Reference

## Overview

The SpecKit orchestrator supports two team phases where parallel multi-agent work happens:

1. **Plan Review** (after `plan` step) — specialist reviewers analyze the plan from different angles
2. **Implementation** (at `implement` step) — parallel implementers, test writer, and QA reviewer

Teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in environment settings. When unavailable, the pipeline falls back to sequential execution automatically.

---

## Plan Review Team

### When It Runs

After the `plan` step completes and `plan.md` exists in `specs/<feature>/`.

### Team Creation

```
TeamCreate:
  team_name: "speckit-<feature>-plan-review"
  description: "Plan review for <feature>"
```

### Teammates to Spawn

#### 1. Security Reviewer (always)
```
Task:
  name: "security-reviewer"
  team_name: "speckit-<feature>-plan-review"
  subagent_type: "general-purpose"
  mode: "plan"
  prompt: |
    You are the security reviewer. Read agents/security-reviewer.md for your full instructions.
    Feature: <feature>
    Spec dir: specs/<feature>/
    Write your review to: specs/<feature>/reviews/security.md
```

#### 2. Performance Reviewer (always)
```
Task:
  name: "performance-reviewer"
  team_name: "speckit-<feature>-plan-review"
  subagent_type: "general-purpose"
  mode: "plan"
  prompt: |
    You are the performance reviewer. Read agents/performance-reviewer.md for your full instructions.
    Feature: <feature>
    Spec dir: specs/<feature>/
    Write your review to: specs/<feature>/reviews/performance.md
```

#### 3. Conventions Reviewer (always)
```
Task:
  name: "conventions-reviewer"
  team_name: "speckit-<feature>-plan-review"
  subagent_type: "general-purpose"
  mode: "plan"
  prompt: |
    You are the conventions reviewer. Read agents/conventions-reviewer.md for your full instructions.
    Feature: <feature>
    Spec dir: specs/<feature>/
    Write your review to: specs/<feature>/reviews/conventions.md
```

#### 4. UI Reviewer (conditional)
Only spawn if `idea.md` contains UI-related keywords: `UI`, `frontend`, `component`, `design`, `page`, `form`, `modal`, `dialog`, `button`, `layout`, `responsive`, `CSS`, `style`, `theme`.

```
Task:
  name: "ui-reviewer"
  team_name: "speckit-<feature>-plan-review"
  subagent_type: "general-purpose"
  mode: "plan"
  prompt: |
    You are the UI reviewer. Read agents/ui-reviewer.md for your full instructions.
    Feature: <feature>
    Spec dir: specs/<feature>/
    Write your review to: specs/<feature>/reviews/ui.md
```

### Monitoring Teammates

Poll `TaskList` periodically to check teammate completion:
- All teammates `completed` or `failed` → proceed to consolidation
- Timeout (default 15 minutes) → proceed with whatever is available

### Consolidation

After all reviewers finish, the lead consolidates findings:

1. Read all review files from `specs/<feature>/reviews/`
2. Create `specs/<feature>/reviews/summary.md` with:
   - Combined verdict (PASS if all pass, REVISE if any reviewer says REVISE)
   - Key findings across all reviews
   - Recommended actions before proceeding

3. Present summary to user:
   - If all PASS → auto-continue to `tasks` step
   - If any REVISE REQUIRED → pause pipeline, ask user to revise plan

### Team Teardown

```
1. Send shutdown_request to each teammate
2. Wait for shutdown_response
3. TeamDelete to clean up
4. Clear team_state in orchestrator-state.json
5. Mark plan-review step as completed
6. Advance current_step to "tasks"
```

---

## Implementation Team

### When It Runs

At the `implement` step, after `analyze` completes.

### Pre-Team Setup

1. Run `partition_tasks.py` on `specs/<feature>/tasks.md`:
   ```bash
   python scripts/partition_tasks.py specs/<feature>/tasks.md --max-groups 3
   ```

2. If `parallelizable: false` → fall back to sequential implementation (single agent)
3. If `parallelizable: true` → proceed with team

### Team Creation

```
TeamCreate:
  team_name: "speckit-<feature>-implement"
  description: "Implementation for <feature>"
```

### Teammates to Spawn

#### Implementers (1-3, based on partition results)
```
Task:
  name: "implementer-<N>"
  team_name: "speckit-<feature>-implement"
  subagent_type: "general-purpose"
  mode: "default"
  prompt: |
    You are implementer <N>. Execute these tasks from specs/<feature>/tasks.md:
    <list of task titles from group N>

    File ownership (ONLY modify these files):
    <list of files from group N>

    Context:
    - Follow docs/features/<feature>/idea.md strictly
    - Reference specs/<feature>/plan.md for architecture
    - Reference specs/<feature>/spec.md for requirements
    - Do NOT modify files outside your ownership list
```

#### Test Writer (parallel with implementers)
```
Task:
  name: "test-writer"
  team_name: "speckit-<feature>-implement"
  subagent_type: "general-purpose"
  mode: "default"
  prompt: |
    You are the test writer. Read agents/test-writer.md for your full instructions.
    Feature: <feature>
    Write tests based on specs, not implementation code.
    Only write to test files (*.test.*, *.spec.*, tests/ directories).
```

#### QA Reviewer (after implementers + test writer)
Spawned only after all implementers and the test writer have completed.

```
Task:
  name: "qa-reviewer"
  team_name: "speckit-<feature>-implement"
  subagent_type: "general-purpose"
  mode: "plan"
  prompt: |
    You are the QA reviewer. Read agents/qa-reviewer.md for your full instructions.
    Feature: <feature>
    All implementation and tests are complete. Review the results.
    Write your review to: specs/<feature>/reviews/qa.md
```

### Lead Coordination

The lead operates in **delegate mode** — coordination only, no direct code changes.

Responsibilities:
1. Create tasks for each implementer group + test writer
2. Assign tasks to teammates
3. Monitor progress via `TaskList`
4. Handle conflicts (if two teammates accidentally touch same file)
5. Spawn QA reviewer after implementers + test writer finish
6. Consolidate QA findings

### Handling Failures

| Scenario | Action |
|----------|--------|
| Implementer fails on a task | Re-assign to another implementer or handle as lead |
| Test writer fails | Log warning, implementation still proceeds |
| QA finds critical issues | Pause for user review before marking complete |
| File ownership conflict | Lead resolves by re-assigning one party's tasks |

### Team Teardown

```
1. Send shutdown_request to each teammate
2. Wait for shutdown_response
3. TeamDelete to clean up
4. Clear team_state in orchestrator-state.json
5. Mark implement step as completed
6. Advance current_step (pipeline complete)
```

---

## State Management During Team Phases

### Starting a Team Phase

```python
state.update_team_state(
    team_name="speckit-<feature>-plan-review",
    phase="plan-review",
    teammates={
        "security-reviewer": {"status": "in_progress", "output": "reviews/security.md"},
        "performance-reviewer": {"status": "in_progress", "output": "reviews/performance.md"},
        "conventions-reviewer": {"status": "in_progress", "output": "reviews/conventions.md"},
    },
    timeout_minutes=15,
)
state.save(state_file)
```

### Updating Teammate Status

When a teammate completes or fails, update the team_state:

```python
state.team_state["teammates"]["security-reviewer"]["status"] = "completed"
state.save(state_file)
```

### Ending a Team Phase

```python
state.clear_team_state()
state.step_status["plan-review"] = "completed"
state.current_step = "tasks"
state.save(state_file)
```

---

## Error Handling & Timeouts

### Team Creation Failure

If `TeamCreate` fails (e.g., agent-teams not available):
1. Set `teams_enabled: false` in state
2. Set `plan-review: "skipped"` in step_status
3. Continue with sequential pipeline
4. Log: "Agent teams unavailable, falling back to sequential execution"

### Teammate Timeout

The stop hook checks `team_state.started_at` against `timeout_minutes`:
- Default timeout: 15 minutes
- If exceeded: stop hook allows stop with a warning
- Lead should check partial results and decide whether to continue

### Communication

- Use `SendMessage` for direct teammate communication
- Use `TaskList` / `TaskGet` / `TaskUpdate` for work coordination
- Avoid `broadcast` — use targeted messages

---

## Fallback Behavior

When teams are disabled (`--no-teams` or `teams_enabled: false`):

| Team Step | Fallback |
|-----------|----------|
| `plan-review` | Skipped entirely (status: "skipped") |
| `implement` (team) | Runs as single sequential implementation (no team) |

The pipeline produces identical results — teams add parallel reviews and parallel implementation but don't change the final artifacts.
