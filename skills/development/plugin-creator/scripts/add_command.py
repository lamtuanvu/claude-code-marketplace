#!/usr/bin/env python3
"""
Add a command to an existing Claude Code plugin.

Usage:
    python add_command.py <plugin-path> <command-name> [options]

Examples:
    python add_command.py ./my-plugin hello
    python add_command.py ./my-plugin hello --description "Say hello"
    python add_command.py ./my-plugin deploy --disable-model-invocation
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


def add_command(plugin_path: Path, command_name: str, description: str,
                disable_model_invocation: bool) -> Path:
    """Add a command to the plugin."""

    commands_dir = plugin_path / "commands"
    commands_dir.mkdir(exist_ok=True)

    command_file = commands_dir / f"{command_name}.md"
    if command_file.exists():
        print(f"Error: Command '{command_name}' already exists at {command_file}", file=sys.stderr)
        sys.exit(1)

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"name: {command_name}",
        f"description: {description or f'The {command_name} command'}",
    ]

    if disable_model_invocation:
        frontmatter_lines.append("disable-model-invocation: true")

    frontmatter_lines.append("---")

    # Get plugin name from path for namespace example
    plugin_name = plugin_path.name

    # Create command markdown file
    command_content = f"""{chr(10).join(frontmatter_lines)}

# {command_name.replace("-", " ").title()} Command

{description or f"Description of what the {command_name} command does."}

## Usage

```
/{plugin_name}:{command_name} [arguments]
```

## Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `arg1` | [Description] | Yes/No |

## Examples

### Basic usage

```
/{plugin_name}:{command_name}
```

### With arguments

```
/{plugin_name}:{command_name} --option value
```

## Notes

[Additional notes about the command behavior]
"""

    with open(command_file, "w") as f:
        f.write(command_content)

    return command_file


def main():
    parser = argparse.ArgumentParser(
        description="Add a command to an existing Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "command_name",
        help="Name of the command to add"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Command description"
    )
    parser.add_argument(
        "--disable-model-invocation",
        action="store_true",
        help="Prevent the model from automatically invoking this command"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    command_file = add_command(
        plugin_path=plugin_path,
        command_name=args.command_name.lower(),
        description=args.description,
        disable_model_invocation=args.disable_model_invocation
    )

    print(f"Added command at: {command_file}")
    print()
    print("Next steps:")
    print(f"  1. Edit the command file: {command_file}")
    print(f"  2. Test: claude --plugin-dir {plugin_path}")
    print(f"  3. Invoke: /{plugin_path.name}:{args.command_name.lower()}")


if __name__ == "__main__":
    main()
