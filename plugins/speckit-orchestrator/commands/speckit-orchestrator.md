---
description: "SpecKit Orchestrator — manage the feature development pipeline"
---

# SpecKit Orchestrator

The SpecKit Orchestrator manages the feature development pipeline:

```
specify → clarify → plan → [plan-review] → tasks → analyze → implement
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/speckit-orchestrator:execute` | Run the next pipeline step |
| `/speckit-orchestrator:status` | Show current pipeline progress |
| `/speckit-orchestrator:rollback <step>` | Reset pipeline to a specific step |
| `/speckit-orchestrator:brainstorm <description>` | Brainstorm and plan a new feature |
| `/speckit-orchestrator:cancel-pipeline` | Pause the pipeline |

## Quick Start

1. **Start a new feature:**
   ```
   /speckit-orchestrator:brainstorm add dark mode toggle
   ```

2. **Run the pipeline:**
   ```
   /speckit-orchestrator:execute
   ```

3. **Check progress:**
   ```
   /speckit-orchestrator:status
   ```
