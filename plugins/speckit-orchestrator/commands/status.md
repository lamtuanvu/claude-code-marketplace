---
description: "Show current SpecKit pipeline progress"
argument-hint: "[feature-name]"
allowed-tools: ["Bash(python *orchestrator.py*)", "Read(docs/features/*/orchestrator-state.json)"]
---

# SpecKit Orchestrator — Status

Show the current progress of the SpecKit pipeline for a feature.

## Usage

```
/speckit-orchestrator:status
/speckit-orchestrator:status dark-mode-toggle
```

## Instructions

1. Run the orchestrator status command:
   ```bash
   python plugins/speckit-orchestrator/scripts/orchestrator.py status [feature-name]
   ```
   If no feature name is provided, it auto-detects from the current branch.

2. Display the progress box and next step info to the user.

3. If there is an active team phase, also run:
   ```bash
   python plugins/speckit-orchestrator/scripts/orchestrator.py team-status
   ```
