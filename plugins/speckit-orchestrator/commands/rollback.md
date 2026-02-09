---
description: "Reset SpecKit pipeline to a specific step"
argument-hint: "<step>"
allowed-tools: ["Bash(python *orchestrator.py*)", "Read(docs/features/*/orchestrator-state.json)"]
---

# SpecKit Orchestrator — Rollback

Reset the SpecKit pipeline to a specific step, marking that step and all subsequent steps as pending.

## Usage

```
/speckit-orchestrator:rollback <step>
```

## Valid Steps

`specify`, `clarify`, `plan`, `plan-review`, `tasks`, `analyze`, `implement`

## Instructions

1. Run the orchestrator rollback command:
   ```bash
   python plugins/speckit-orchestrator/scripts/orchestrator.py rollback <step>
   ```

2. Show confirmation and updated progress to the user.

3. Inform the user they can resume with:
   ```
   /speckit-orchestrator:execute
   ```
