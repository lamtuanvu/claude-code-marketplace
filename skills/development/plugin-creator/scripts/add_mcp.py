#!/usr/bin/env python3
"""
Add or update MCP server configuration for a Claude Code plugin.

Usage:
    python add_mcp.py <plugin-path> <server-name> --command <cmd> [-- args...]

Examples:
    python add_mcp.py ./my-plugin my-server --command "node server.js"
    python add_mcp.py ./my-plugin my-server --command "${CLAUDE_PLUGIN_ROOT}/bin/server"
    python add_mcp.py ./my-plugin my-server --command npx -- my-mcp-server --port 3000
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional


def validate_plugin(plugin_path: Path) -> bool:
    """Check if the path is a valid plugin directory."""
    manifest = plugin_path / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        print(f"Error: '{plugin_path}' is not a valid plugin directory.", file=sys.stderr)
        print("Missing .claude-plugin/plugin.json manifest.", file=sys.stderr)
        return False
    return True


def load_mcp_config(mcp_file: Path) -> dict:
    """Load existing MCP configuration or return empty structure."""
    if mcp_file.exists():
        with open(mcp_file) as f:
            return json.load(f)
    return {"mcpServers": {}}


def add_mcp(plugin_path: Path, server_name: str, command: str,
            args: Optional[List[str]], env: Optional[dict]) -> Path:
    """Add or update MCP server configuration."""

    mcp_file = plugin_path / ".mcp.json"
    config = load_mcp_config(mcp_file)

    # Ensure mcpServers dict exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Check for existing server
    if server_name in config["mcpServers"]:
        print(f"Warning: Overwriting existing MCP server '{server_name}'", file=sys.stderr)

    # Build server entry
    server_entry = {"command": command}

    if args:
        server_entry["args"] = args

    if env:
        server_entry["env"] = env

    # Add to config
    config["mcpServers"][server_name] = server_entry

    # Write updated config
    with open(mcp_file, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    return mcp_file


def main():
    parser = argparse.ArgumentParser(
        description="Add or update MCP server configuration for a Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "server_name",
        help="Name of the MCP server"
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Command to start the MCP server"
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Additional arguments for the command (after --)"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    mcp_file = add_mcp(
        plugin_path=plugin_path,
        server_name=args.server_name,
        command=args.command,
        args=args.extra_args if args.extra_args else None,
        env=None
    )

    print(f"Updated MCP configuration at: {mcp_file}")
    print()
    print("Server added:")
    print(f"  Name: {args.server_name}")
    print(f"  Command: {args.command}")
    if args.extra_args:
        print(f"  Args: {args.extra_args}")
    print()
    print("Tip: Use ${CLAUDE_PLUGIN_ROOT} for plugin-relative paths:")
    print('  --command "${CLAUDE_PLUGIN_ROOT}/bin/my-server"')
    print()
    print("To add environment variables, edit .mcp.json directly.")
    print()
    print("Next steps:")
    print(f"  1. Ensure the server executable exists")
    print(f"  2. Test: claude --plugin-dir {plugin_path}")


if __name__ == "__main__":
    main()
