#!/usr/bin/env python3
"""
Add or update hooks configuration for a Claude Code plugin.

Usage:
    python add_hooks.py <plugin-path> --event <event-type> [options]

Examples:
    python add_hooks.py ./my-plugin --event PreToolUse --matcher "Write|Edit"
    python add_hooks.py ./my-plugin --event PostToolUse --command "echo 'Tool used'"
    python add_hooks.py ./my-plugin --event Notification --type prompt
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


VALID_EVENTS = [
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "SubagentStop"
]

VALID_HOOK_TYPES = ["command", "prompt", "agent"]


def validate_plugin(plugin_path: Path) -> bool:
    """Check if the path is a valid plugin directory."""
    manifest = plugin_path / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        print(f"Error: '{plugin_path}' is not a valid plugin directory.", file=sys.stderr)
        print("Missing .claude-plugin/plugin.json manifest.", file=sys.stderr)
        return False
    return True


def load_hooks_config(hooks_file: Path) -> dict:
    """Load existing hooks configuration or return empty structure."""
    if hooks_file.exists():
        with open(hooks_file) as f:
            return json.load(f)
    return {"hooks": {}}


def add_hooks(plugin_path: Path, event: str, hook_type: str,
              command: Optional[str], matcher: Optional[str],
              timeout: Optional[int]) -> Path:
    """Add or update hooks configuration."""

    hooks_dir = plugin_path / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    hooks_file = hooks_dir / "hooks.json"
    config = load_hooks_config(hooks_file)

    # Ensure hooks dict exists
    if "hooks" not in config:
        config["hooks"] = {}

    # Initialize event array if needed
    if event not in config["hooks"]:
        config["hooks"][event] = []

    # Build hook entry
    hook_entry = {"type": hook_type}

    if hook_type == "command":
        if not command:
            print("Error: --command is required for command hooks", file=sys.stderr)
            sys.exit(1)
        hook_entry["command"] = command
    elif hook_type == "prompt":
        hook_entry["prompt"] = command or "Review the changes and provide feedback"
    elif hook_type == "agent":
        hook_entry["agent"] = command or "review-agent"

    if matcher:
        hook_entry["matcher"] = matcher

    if timeout:
        hook_entry["timeout"] = timeout

    # Add to config
    config["hooks"][event].append(hook_entry)

    # Write updated config
    with open(hooks_file, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    return hooks_file


def main():
    parser = argparse.ArgumentParser(
        description="Add or update hooks configuration for a Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "--event",
        required=True,
        choices=VALID_EVENTS,
        help="Hook event type"
    )
    parser.add_argument(
        "--type",
        dest="hook_type",
        default="command",
        choices=VALID_HOOK_TYPES,
        help="Type of hook handler (default: command)"
    )
    parser.add_argument(
        "--command",
        help="Command to run (for command hooks) or prompt/agent name"
    )
    parser.add_argument(
        "--matcher",
        help="Regex pattern to match tool names (for PreToolUse/PostToolUse)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout in milliseconds"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    hooks_file = add_hooks(
        plugin_path=plugin_path,
        event=args.event,
        hook_type=args.hook_type,
        command=args.command,
        matcher=args.matcher,
        timeout=args.timeout
    )

    print(f"Updated hooks at: {hooks_file}")
    print()
    print("Hook added:")
    print(f"  Event: {args.event}")
    print(f"  Type: {args.hook_type}")
    if args.matcher:
        print(f"  Matcher: {args.matcher}")
    print()
    print("Next steps:")
    print(f"  1. Review the configuration: {hooks_file}")
    print(f"  2. Test: claude --plugin-dir {plugin_path}")


if __name__ == "__main__":
    main()
