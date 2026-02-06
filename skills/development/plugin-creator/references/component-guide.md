# Plugin Component Guide

This guide covers all component types that can be included in a Claude Code plugin.

## Directory Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json        # Required manifest
├── skills/                # Skill directories
│   └── my-skill/
│       ├── SKILL.md       # Skill definition
│       ├── scripts/       # Helper scripts
│       ├── references/    # Reference docs
│       └── assets/        # Static assets
├── agents/                # Agent definitions
│   └── my-agent.md
├── commands/              # Command definitions
│   └── my-command.md
├── hooks/                 # Hook configurations
│   └── hooks.json
├── .mcp.json              # MCP server config
└── .lsp.json              # LSP server config
```

---

## Skills

Skills are the primary way to extend Claude's capabilities with specialized knowledge and workflows.

### Location

```
skills/<skill-name>/SKILL.md
```

### Structure

```markdown
---
name: skill-name
description: What this skill does
---

# Skill Name

Content and instructions...
```

### Required Frontmatter

| Field | Description |
|-------|-------------|
| `name` | Skill identifier (lowercase, hyphens) |
| `description` | Brief description for skill discovery |

### Optional Subdirectories

- `scripts/` - Helper scripts (Python, shell, etc.)
- `references/` - Reference documentation
- `assets/` - Static assets (images, templates)

### Namespacing

Skills in plugins are namespaced:
```
/my-plugin:skill-name
```

---

## Agents

Agents define specialized AI assistants that can be invoked via the Task tool.

### Location

```
agents/<agent-name>.md
```

### Structure

```markdown
---
name: agent-name
description: What this agent does
---

# Agent Name

## Capabilities

This agent can:
- Capability 1
- Capability 2

## Tools Available

- Read
- Grep
- Glob
- etc.

## Behavior

Description of how the agent operates...
```

### Required Frontmatter

| Field | Description |
|-------|-------------|
| `name` | Agent identifier |
| `description` | Brief description for agent discovery |

### Invocation

Agents are invoked via the Task tool:
```
Task(subagent_type="my-plugin:agent-name", prompt="...")
```

---

## Commands

Commands are legacy slash commands that can be invoked by users.

### Location

```
commands/<command-name>.md
```

### Structure

```markdown
---
name: command-name
description: What this command does
disable-model-invocation: false
---

# Command Name

Instructions for executing this command...
```

### Frontmatter Options

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Command identifier |
| `description` | string | Brief description |
| `disable-model-invocation` | boolean | Prevent automatic invocation |

### Invocation

```
/my-plugin:command-name [args]
```

---

## Hooks

Hooks allow plugins to respond to events during Claude's execution.

### Location

```
hooks/hooks.json
```

### Structure

```json
{
  "hooks": {
    "EventType": [
      {
        "type": "command|prompt|agent",
        "command": "...",
        "matcher": "regex pattern"
      }
    ]
  }
}
```

### Event Types

| Event | Description | Matcher Support |
|-------|-------------|-----------------|
| `PreToolUse` | Before a tool is used | Yes (tool name) |
| `PostToolUse` | After a tool is used | Yes (tool name) |
| `Notification` | When notifications occur | No |
| `Stop` | When Claude stops | No |
| `SubagentStop` | When a subagent stops | No |

### Hook Types

#### Command Hook

Runs a shell command:

```json
{
  "type": "command",
  "command": "echo 'Tool used: $TOOL_NAME'",
  "matcher": "Write|Edit",
  "timeout": 5000
}
```

#### Prompt Hook

Sends a prompt to Claude:

```json
{
  "type": "prompt",
  "prompt": "Review the changes for security issues",
  "matcher": "Write"
}
```

#### Agent Hook

Invokes an agent:

```json
{
  "type": "agent",
  "agent": "security-scanner",
  "matcher": "Write|Edit"
}
```

### Matcher Patterns

Matchers use regex to filter which tools trigger the hook:

- `Write` - Only Write tool
- `Write|Edit` - Write or Edit tools
- `.*` - All tools
- `mcp__.*` - All MCP tools

---

## MCP Servers

MCP (Model Context Protocol) servers provide additional tools to Claude.

### Location

```
.mcp.json
```

### Structure

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command to start server",
      "args": ["arg1", "arg2"],
      "env": {
        "KEY": "value"
      }
    }
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `command` | string | Yes | Command to start the server |
| `args` | string[] | No | Command arguments |
| `env` | object | No | Environment variables |

### Plugin Root Variable

Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

### Example: Node.js MCP Server

```json
{
  "mcpServers": {
    "database-tools": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/database-server.js"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data/db.sqlite"
      }
    }
  }
}
```

---

## LSP Servers

LSP (Language Server Protocol) servers provide language intelligence features.

### Location

```
.lsp.json
```

### Structure

```json
{
  "lspServers": {
    "server-name": {
      "command": "command to start server",
      "args": ["arg1", "arg2"],
      "extensionToLanguage": {
        ".ext": "language-id"
      },
      "initializationOptions": {}
    }
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `command` | string | Command to start the LSP server |
| `extensionToLanguage` | object | Maps file extensions to language IDs |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `args` | string[] | Command arguments |
| `initializationOptions` | object | LSP initialization options |

### Example: Custom Language LSP

```json
{
  "lspServers": {
    "my-lang-lsp": {
      "command": "${CLAUDE_PLUGIN_ROOT}/bin/my-lang-lsp",
      "extensionToLanguage": {
        ".mylang": "mylang",
        ".ml": "mylang"
      },
      "initializationOptions": {
        "diagnostics": true,
        "formatting": true
      }
    }
  }
}
```

---

## Best Practices

### Naming

- Use lowercase with hyphens for names
- Be descriptive but concise
- Avoid generic names that might conflict

### Organization

- Group related functionality in skills
- Use agents for complex, multi-step workflows
- Use hooks sparingly for cross-cutting concerns

### Performance

- MCP servers should start quickly
- Hooks should complete within timeout
- Avoid heavy initialization in LSP servers

### Documentation

- Include clear descriptions in frontmatter
- Document usage examples
- Provide reference documentation for complex features
