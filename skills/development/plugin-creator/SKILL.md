---
name: plugin-creator
description: Guide for creating and incrementally building Claude Code plugins. Use when users want to create a new plugin, add components to an existing plugin, or package plugins for distribution.
---

# Plugin Creator

This skill helps you create and develop Claude Code plugins - modular packages that extend Claude's capabilities with skills, agents, commands, hooks, MCP servers, and LSP servers.

## Plugin vs Skill

- **Skill**: Single `SKILL.md` file with optional resources (scripts, references, assets)
- **Plugin**: Directory with `.claude-plugin/plugin.json` manifest containing multiple components

## Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # Required manifest
├── skills/                # SKILL.md directories
│   └── my-skill/
│       ├── SKILL.md
│       └── scripts/
├── agents/                # Agent markdown files
│   └── my-agent.md
├── commands/              # Command markdown files (legacy)
│   └── my-command.md
├── hooks/                 # Hooks configuration
│   └── hooks.json
├── .mcp.json              # MCP server configurations
├── .lsp.json              # LSP server configurations
└── README.md
```

## Development Workflow

### 1. Initialize Plugin

Create a new plugin with the manifest and basic structure:

```bash
python scripts/init_plugin.py <plugin-name> --path <directory>
```

Options:
- `--path`: Parent directory for plugin (default: current directory)
- `--description`: Plugin description
- `--author`: Author name

### 2. Add Components Incrementally

Add components as your plugin grows:

**Add a skill:**
```bash
python scripts/add_skill.py <plugin-path> <skill-name>
```

**Add an agent:**
```bash
python scripts/add_agent.py <plugin-path> <agent-name>
```

**Add a command:**
```bash
python scripts/add_command.py <plugin-path> <command-name>
```

**Add hooks:**
```bash
python scripts/add_hooks.py <plugin-path> --event <event-type>
```

**Add MCP server:**
```bash
python scripts/add_mcp.py <plugin-path> <server-name> --command <cmd>
```

**Add LSP server:**
```bash
python scripts/add_lsp.py <plugin-path> <server-name> --command <cmd> --extensions <exts>
```

### 3. Validate Plugin

Check plugin structure and component validity:

```bash
python scripts/validate_plugin.py <plugin-path>
```

### 4. Package for Distribution

Create a distributable zip file:

```bash
python scripts/package_plugin.py <plugin-path> <output-dir>
```

## Testing Your Plugin

Load your plugin during development:

```bash
claude --plugin-dir ./my-plugin
```

## Key Concepts

### Plugin Manifest (plugin.json)

Required fields:
- `name`: Unique plugin identifier (lowercase, hyphens allowed)
- `version`: Semantic version (e.g., "1.0.0")
- `description`: Brief plugin description

Optional fields:
- `author`: Plugin author
- `homepage`: Project URL
- `repository`: Source code URL
- `license`: License identifier

### Namespaced Commands

Plugin commands are namespaced with the plugin name:
- Plugin skill `hello` in plugin `my-plugin` → `/my-plugin:hello`

### Environment Variable

Use `${CLAUDE_PLUGIN_ROOT}` in configurations to reference the plugin root:

```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/bin/my-server"
}
```

## Reference Documentation

- `references/plugin-manifest-schema.md` - Complete manifest specification
- `references/component-guide.md` - Detailed component documentation

## Example: Creating a Code Review Plugin

```bash
# 1. Initialize
python scripts/init_plugin.py code-review-plugin --path ./plugins \
  --description "Automated code review tools"

# 2. Add a review skill
python scripts/add_skill.py ./plugins/code-review-plugin code-reviewer

# 3. Add a security agent
python scripts/add_agent.py ./plugins/code-review-plugin security-scanner

# 4. Add pre-commit hooks
python scripts/add_hooks.py ./plugins/code-review-plugin \
  --event PreToolUse --matcher "Write|Edit"

# 5. Validate
python scripts/validate_plugin.py ./plugins/code-review-plugin

# 6. Package
python scripts/package_plugin.py ./plugins/code-review-plugin ./dist
```
