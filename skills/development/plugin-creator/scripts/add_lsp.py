#!/usr/bin/env python3
"""
Add or update LSP server configuration for a Claude Code plugin.

Usage:
    python add_lsp.py <plugin-path> <server-name> --command <cmd> --extensions <exts> [options]

Examples:
    python add_lsp.py ./my-plugin my-lsp --command "node lsp.js" --extensions ".foo,.bar"
    python add_lsp.py ./my-plugin rust-lsp --command "rust-analyzer" --extensions ".rs"
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


def load_lsp_config(lsp_file: Path) -> dict:
    """Load existing LSP configuration or return empty structure."""
    if lsp_file.exists():
        with open(lsp_file) as f:
            return json.load(f)
    return {"lspServers": {}}


def add_lsp(plugin_path: Path, server_name: str, command: str,
            extensions: List[str], args: Optional[List[str]],
            initialization_options: Optional[dict]) -> Path:
    """Add or update LSP server configuration."""

    lsp_file = plugin_path / ".lsp.json"
    config = load_lsp_config(lsp_file)

    # Ensure lspServers dict exists
    if "lspServers" not in config:
        config["lspServers"] = {}

    # Check for existing server
    if server_name in config["lspServers"]:
        print(f"Warning: Overwriting existing LSP server '{server_name}'", file=sys.stderr)

    # Build extension to language mapping
    # Infer language from server name or use generic mapping
    language = server_name.replace("-lsp", "").replace("-", "_")
    ext_to_lang = {}
    for ext in extensions:
        # Ensure extension starts with a dot
        if not ext.startswith("."):
            ext = f".{ext}"
        ext_to_lang[ext] = language

    # Build server entry
    server_entry = {
        "command": command,
        "extensionToLanguage": ext_to_lang
    }

    if args:
        server_entry["args"] = args

    if initialization_options:
        server_entry["initializationOptions"] = initialization_options

    # Add to config
    config["lspServers"][server_name] = server_entry

    # Write updated config
    with open(lsp_file, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

    return lsp_file


def main():
    parser = argparse.ArgumentParser(
        description="Add or update LSP server configuration for a Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "server_name",
        help="Name of the LSP server"
    )
    parser.add_argument(
        "--command",
        required=True,
        help="Command to start the LSP server"
    )
    parser.add_argument(
        "--extensions",
        required=True,
        help="Comma-separated file extensions (e.g., '.rs,.rust')"
    )
    parser.add_argument(
        "--args",
        nargs="*",
        help="Additional arguments for the command"
    )
    parser.add_argument(
        "--init-option",
        nargs="*",
        dest="init_options",
        help="Initialization options (KEY=VALUE format)"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    # Parse extensions
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    # Parse initialization options
    init_options = None
    if args.init_options:
        init_options = {}
        for item in args.init_options:
            if "=" not in item:
                print(f"Error: Invalid init-option format '{item}'. Use KEY=VALUE", file=sys.stderr)
                sys.exit(1)
            key, value = item.split("=", 1)
            # Try to parse as JSON for nested values
            try:
                init_options[key] = json.loads(value)
            except json.JSONDecodeError:
                init_options[key] = value

    lsp_file = add_lsp(
        plugin_path=plugin_path,
        server_name=args.server_name,
        command=args.command,
        extensions=extensions,
        args=args.args,
        initialization_options=init_options
    )

    print(f"Updated LSP configuration at: {lsp_file}")
    print()
    print("Server added:")
    print(f"  Name: {args.server_name}")
    print(f"  Command: {args.command}")
    print(f"  Extensions: {', '.join(extensions)}")
    if args.args:
        print(f"  Args: {' '.join(args.args)}")
    print()
    print("Tip: Use ${CLAUDE_PLUGIN_ROOT} for plugin-relative paths:")
    print('  --command "${CLAUDE_PLUGIN_ROOT}/bin/my-lsp"')
    print()
    print("Next steps:")
    print(f"  1. Ensure the LSP server executable exists")
    print(f"  2. Test: claude --plugin-dir {plugin_path}")


if __name__ == "__main__":
    main()
