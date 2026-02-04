# Contributing to Claude Code Skills Marketplace

Thank you for your interest in contributing! This guide explains how to add your own skills to the marketplace.

## Skill Structure

Every skill must follow this structure:

```
skills/<category>/<skill-name>/
├── SKILL.md              # Required: Main skill file
├── scripts/              # Optional: Executable code
├── references/           # Optional: Documentation
└── assets/               # Optional: Templates, images
```

### Required: SKILL.md

Your skill must have a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: my-skill
description: Clear description of what this skill does and when to use it.
argument-hint: Optional hint for skill arguments
---

# My Skill

## Overview

Explain what this skill does...

## When to Use

Describe scenarios when this skill should trigger...

## Instructions

Step-by-step guidance for Claude...
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique skill identifier (kebab-case) |
| `description` | Yes | Clear, specific description of purpose |
| `argument-hint` | No | Hint for command arguments |
| `license` | No | License reference |

## Categories

Place your skill in the appropriate category:

| Category | Description | Examples |
|----------|-------------|----------|
| `development` | Coding workflows, tools | speckit, code-review |
| `integrations` | APIs, services, MCP | mcp-builder, slack |
| `documentation` | Docs, styling | brand-guidelines, readme-gen |
| `automation` | Task automation | agent-manager, cron-jobs |

## Adding Your Skill

### 1. Fork the Repository

```bash
git clone https://github.com/lamtuanvu/claude-code-marketplace.git
cd claude-code-marketplace
```

### 2. Create Skill Directory

```bash
mkdir -p skills/<category>/<skill-name>
```

### 3. Create SKILL.md

Write your skill following the structure above.

### 4. Add to marketplace.json

Edit `.claude-plugin/marketplace.json` and add your skill:

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "What my skill does",
  "source": "./skills/category/my-skill",
  "keywords": ["relevant", "keywords"]
}
```

### 5. Submit Pull Request

```bash
git checkout -b add-my-skill
git add .
git commit -m "Add my-skill to marketplace"
git push origin add-my-skill
```

Then open a pull request on GitHub.

## Quality Guidelines

### Good Skills

- Solve a specific, real problem
- Have clear, actionable instructions
- Include usage examples
- Work reliably across environments

### Skill.md Best Practices

1. **Be Specific**: Claude needs clear instructions
2. **Use Imperative Form**: "Run this command" not "You should run"
3. **Include Examples**: Show concrete usage
4. **Reference Resources**: Point to scripts, docs as needed
5. **Handle Errors**: Explain what to do when things fail

### Testing Your Skill

Before submitting:

1. Install locally: `cp -r my-skill ~/.claude/skills/`
2. Test invocation: `/my-skill`
3. Verify Claude understands the instructions
4. Test edge cases

## Validation

The CI pipeline validates:

- SKILL.md exists with valid frontmatter
- Required fields (`name`, `description`) present
- Skill directory structure
- marketplace.json format

## License

By contributing, you agree your skill will be licensed under Apache 2.0.

## Questions?

Open an issue or discussion on GitHub.
