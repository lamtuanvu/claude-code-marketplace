# Claude Code Skills Marketplace

[![Skills](https://img.shields.io/badge/skills-2-blue)](skills/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](docs/CONTRIBUTING.md)

SpecKit workflow skills for Claude Code - structured feature development from idea to implementation.

## Quick Start

### 1. Add Marketplace
```
/plugin marketplace add https://github.com/lamtuanvu/claude-code-marketplace
```

### 2. Install Skills
```bash
# Install individual skill
/plugin install speckit-orchestrator@lamtuanvu-marketplace
/plugin install speckit-brainstorm@lamtuanvu-marketplace

# Or install all skills
/plugin install-all lamtuanvu-marketplace
```

### 3. Use Skills
```
/speckit-brainstorm Add dark mode toggle
/speckit-orchestrator --execute
```

## SpecKit Workflow

SpecKit is a structured feature development workflow:

```
brainstorm → specify → clarify → plan → tasks → analyze → implement
```

| Skill | Description |
|-------|-------------|
| [speckit-brainstorm](skills/development/speckit-brainstorm) | Start here - explore ideas, define requirements, produce idea.md |
| [speckit-orchestrator](skills/development/speckit-orchestrator) | Execute the pipeline one step at a time |

### Workflow

1. **Start with brainstorming**: `/speckit-brainstorm <feature description>`
   - Explores your feature idea
   - Defines requirements
   - Creates `idea.md` and `orchestrator-state.json`

2. **Execute the pipeline**: `/speckit-orchestrator --execute`
   - Runs one step at a time
   - Follows `idea.md` as source of truth
   - Progress: specify → clarify → plan → tasks → analyze → implement

## Skill Structure

```
skills/
└── development/
    ├── speckit-brainstorm/
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── references/
    └── speckit-orchestrator/
        ├── SKILL.md
        ├── scripts/
        ├── references/
        └── assets/
```

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for how to add your skills.

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

Built with Claude Code
