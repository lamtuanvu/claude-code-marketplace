---
name: hello-world
description: Example skill demonstrating proper skill structure. Use this as a template for creating your own skills.
argument-hint: [name]
---

# Hello World Skill

## Overview

This is an example skill that demonstrates the proper structure and format for Claude Code skills. Use it as a starting point for creating your own skills.

## When to Use

Use this skill when:
- Learning how to create Claude Code skills
- Need a template for a new skill
- Want to test skill installation

## Instructions

### Basic Usage

When invoked with `/hello-world`, greet the user:

```
Hello, World! This is an example Claude Code skill.
```

If a name argument is provided (`/hello-world Alice`), personalize:

```
Hello, Alice! Welcome to Claude Code skills.
```

### Skill Anatomy

This skill demonstrates:

1. **YAML Frontmatter**: Required metadata
2. **Markdown Body**: Instructions for Claude
3. **When to Use**: Clear triggering conditions
4. **Instructions**: Step-by-step guidance

### Creating Your Own

To create a skill based on this template:

1. Copy this directory to `skills/<category>/<your-skill-name>/`
2. Update SKILL.md with your content
3. Add scripts/ if needed for code
4. Add references/ for documentation
5. Register in marketplace.json

## Resources

- [Contributing Guide](../../docs/CONTRIBUTING.md)
