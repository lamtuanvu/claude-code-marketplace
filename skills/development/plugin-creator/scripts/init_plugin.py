#!/usr/bin/env python3
"""
Initialize a new Claude Code plugin with basic structure.

Usage:
    python init_plugin.py <plugin-name> [options]

Examples:
    python init_plugin.py my-plugin
    python init_plugin.py my-plugin --path ./plugins
    python init_plugin.py my-plugin --description "My awesome plugin" --author "John Doe"
"""

import argparse
import json
import os
import sys
from pathlib import Path


def create_plugin(name: str, path: str, description: str, author: str) -> Path:
    """Create a new plugin with basic structure."""

    # Validate plugin name
    if not name.replace("-", "").replace("_", "").isalnum():
        print(f"Error: Plugin name '{name}' contains invalid characters.", file=sys.stderr)
        print("Use only alphanumeric characters, hyphens, and underscores.", file=sys.stderr)
        sys.exit(1)

    # Create plugin directory
    plugin_dir = Path(path) / name
    if plugin_dir.exists():
        print(f"Error: Directory '{plugin_dir}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Create directory structure
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / "skills").mkdir()
    (plugin_dir / "agents").mkdir()
    (plugin_dir / "commands").mkdir()
    (plugin_dir / "hooks").mkdir()

    # Create plugin.json manifest
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": description or f"A Claude Code plugin: {name}",
    }

    if author:
        manifest["author"] = author

    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    # Create README.md
    readme_content = f"""# {name}

{description or f"A Claude Code plugin: {name}"}

## Installation

```bash
claude --plugin-dir ./{name}
```

## Components

This plugin includes:

- **Skills**: Custom SKILL.md files in `skills/`
- **Agents**: Agent definitions in `agents/`
- **Commands**: Command files in `commands/`
- **Hooks**: Hook configurations in `hooks/`

## Usage

After loading the plugin, use namespaced commands:

```
/{name}:<command-name>
```

## Development

Add components using the plugin-creator skill:

```bash
# Add a skill
python add_skill.py ./{name} my-skill

# Add an agent
python add_agent.py ./{name} my-agent

# Validate plugin
python validate_plugin.py ./{name}
```
"""

    readme_path = plugin_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    return plugin_dir


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Claude Code plugin"
    )
    parser.add_argument(
        "name",
        help="Plugin name (lowercase, hyphens allowed)"
    )
    parser.add_argument(
        "--path",
        default=".",
        help="Parent directory for the plugin (default: current directory)"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Plugin description"
    )
    parser.add_argument(
        "--author",
        default="",
        help="Plugin author"
    )

    args = parser.parse_args()

    plugin_dir = create_plugin(
        name=args.name.lower(),
        path=args.path,
        description=args.description,
        author=args.author
    )

    print(f"Created plugin at: {plugin_dir}")
    print()
    print("Next steps:")
    print(f"  1. Add skills:   python add_skill.py {plugin_dir} <skill-name>")
    print(f"  2. Add agents:   python add_agent.py {plugin_dir} <agent-name>")
    print(f"  3. Validate:     python validate_plugin.py {plugin_dir}")
    print(f"  4. Test:         claude --plugin-dir {plugin_dir}")


if __name__ == "__main__":
    main()
