#!/usr/bin/env python3
"""
Add an agent to an existing Claude Code plugin.

Usage:
    python add_agent.py <plugin-path> <agent-name> [options]

Examples:
    python add_agent.py ./my-plugin security-scanner
    python add_agent.py ./my-plugin security-scanner --description "Scans for vulnerabilities"
"""

import argparse
import sys
from pathlib import Path


def validate_plugin(plugin_path: Path) -> bool:
    """Check if the path is a valid plugin directory."""
    manifest = plugin_path / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        print(f"Error: '{plugin_path}' is not a valid plugin directory.", file=sys.stderr)
        print("Missing .claude-plugin/plugin.json manifest.", file=sys.stderr)
        return False
    return True


def add_agent(plugin_path: Path, agent_name: str, description: str) -> Path:
    """Add an agent to the plugin."""

    agents_dir = plugin_path / "agents"
    agents_dir.mkdir(exist_ok=True)

    agent_file = agents_dir / f"{agent_name}.md"
    if agent_file.exists():
        print(f"Error: Agent '{agent_name}' already exists at {agent_file}", file=sys.stderr)
        sys.exit(1)

    # Create agent markdown file
    agent_content = f"""---
name: {agent_name}
description: {description or f"An agent for {agent_name}"}
---

# {agent_name.replace("-", " ").title()} Agent

{description or f"Description of what the {agent_name} agent does."}

## Capabilities

This agent can:
- [Capability 1]
- [Capability 2]
- [Capability 3]

## Tools Available

The agent has access to the following tools:
- Read: Read files from the filesystem
- Grep: Search for patterns in files
- Glob: Find files matching patterns
- [Add other tools as needed]

## Usage

This agent is invoked through the Task tool with `subagent_type="{agent_name}"`.

## Behavior

[Describe the agent's behavior, decision-making process, and any special considerations]

## Examples

### Example 1: [Use case]

```
[Example interaction or command]
```

### Example 2: [Use case]

```
[Example interaction or command]
```
"""

    with open(agent_file, "w") as f:
        f.write(agent_content)

    return agent_file


def main():
    parser = argparse.ArgumentParser(
        description="Add an agent to an existing Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "agent_name",
        help="Name of the agent to add"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Agent description"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    agent_file = add_agent(
        plugin_path=plugin_path,
        agent_name=args.agent_name.lower(),
        description=args.description
    )

    print(f"Added agent at: {agent_file}")
    print()
    print("Next steps:")
    print(f"  1. Edit the agent file: {agent_file}")
    print("  2. Define capabilities and tools")
    print(f"  3. Test: claude --plugin-dir {plugin_path}")


if __name__ == "__main__":
    main()
