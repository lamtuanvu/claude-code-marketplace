# Claude Code Skills Marketplace

[![Skills](https://img.shields.io/badge/skills-6+-blue)](skills/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen)](docs/CONTRIBUTING.md)

A community-driven marketplace for Claude Code skills, featuring SpecKit workflows, MCP tools, and developer utilities.

## Quick Start

### 1. Add Marketplace
```
/plugin marketplace add https://github.com/lamtuanvu/claude-code-marketplace
```

### 2. Install Skills
```bash
# Install individual skill
/plugin install speckit-orchestrator@lamtuanvu-marketplace

# Or install all skills
/plugin install-all lamtuanvu-marketplace
```

### 3. Use Skills
Skills are automatically available based on context, or invoke directly:
```
/speckit-orchestrator --execute
/speckit-brainstorm Add dark mode toggle
```

## Featured Skills

### SpecKit Workflow

| Skill | Description |
|-------|-------------|
| [speckit-orchestrator](skills/development/speckit-orchestrator) | Execute SpecKit pipeline one step at a time |
| [speckit-brainstorm](skills/development/speckit-brainstorm) | Brainstorm and plan features |

### Development Tools

| Skill | Description |
|-------|-------------|
| [skill-creator](skills/development/skill-creator) | Create new Claude Code skills |
| [mcp-builder](skills/integrations/mcp-builder) | Build MCP servers |

### Utilities

| Skill | Description |
|-------|-------------|
| [brand-guidelines](skills/documentation/brand-guidelines) | Anthropic brand styling |
| [agent-manager-skill](skills/automation/agent-manager-skill) | Manage CLI agents with tmux |

## Skill Categories

```
skills/
├── development/      # Workflows, coding tools
├── integrations/     # APIs, MCP, external services
├── documentation/    # Docs, styling, templates
└── automation/       # Task automation, agents
```

## What is SpecKit?

SpecKit is a structured feature development workflow that guides features from idea to implementation:

```
brainstorm → specify → clarify → plan → tasks → analyze → implement
```

- **speckit-brainstorm**: Start here to explore and define your feature idea
- **speckit-orchestrator**: Execute the pipeline one step at a time

## What are MCP Servers?

MCP (Model Context Protocol) servers enable Claude to interact with external services. The `mcp-builder` skill guides you through creating production-ready MCP servers in Python or TypeScript.

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for how to add your skills.

### Quick Contribution

1. Fork this repository
2. Create your skill in `skills/<category>/<skill-name>/`
3. Add entry to `.claude-plugin/marketplace.json`
4. Submit a pull request

## Installation Verification

After installing, verify skills work:
```
/speckit-orchestrator --status
```

## Support

- [Issues](https://github.com/lamtuanvu/claude-code-marketplace/issues)
- [Discussions](https://github.com/lamtuanvu/claude-code-marketplace/discussions)

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

Built with Claude Code
