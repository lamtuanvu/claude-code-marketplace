---
description: "Pause the SpecKit pipeline so the stop hook allows exit"
allowed-tools: ["Bash(python *orchestrator.py*)", "Read(docs/features/*/orchestrator-state.json)"]
hide-from-slash-command-tool: "true"
---

# Cancel Pipeline

To pause the SpecKit orchestrator pipeline (so the stop hook stops auto-continuing):

1. Run the orchestrator cancel command:
   ```bash
   python skills/development/speckit-orchestrator/scripts/orchestrator.py cancel
   ```

2. Report the result to the user.

3. To resume later, the user can run `/speckit-orchestrator:execute` which clears the pause flag.
