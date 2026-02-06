#!/usr/bin/env python3
"""
Validate a Claude Code plugin structure and components.

Usage:
    python validate_plugin.py <plugin-path>

Examples:
    python validate_plugin.py ./my-plugin
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ValidationError:
    def __init__(self, component: str, message: str, severity: str = "error"):
        self.component = component
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.upper()}] {self.component}: {self.message}"


def validate_manifest(plugin_path: Path) -> List[ValidationError]:
    """Validate the plugin manifest."""
    errors = []
    manifest_path = plugin_path / ".claude-plugin" / "plugin.json"

    if not manifest_path.exists():
        errors.append(ValidationError(
            "manifest",
            "Missing .claude-plugin/plugin.json"
        ))
        return errors

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            "manifest",
            f"Invalid JSON: {e}"
        ))
        return errors

    # Required fields
    required_fields = ["name", "version", "description"]
    for field in required_fields:
        if field not in manifest:
            errors.append(ValidationError(
                "manifest",
                f"Missing required field: {field}"
            ))

    # Validate name format
    if "name" in manifest:
        name = manifest["name"]
        if not re.match(r"^[a-z][a-z0-9-]*$", name):
            errors.append(ValidationError(
                "manifest",
                f"Invalid name '{name}'. Use lowercase letters, numbers, and hyphens only."
            ))

    # Validate version format (semver)
    if "version" in manifest:
        version = manifest["version"]
        if not re.match(r"^\d+\.\d+\.\d+", version):
            errors.append(ValidationError(
                "manifest",
                f"Invalid version '{version}'. Use semantic versioning (e.g., 1.0.0).",
                "warning"
            ))

    return errors


def validate_skills(plugin_path: Path) -> List[ValidationError]:
    """Validate skills in the plugin."""
    errors = []
    skills_dir = plugin_path / "skills"

    if not skills_dir.exists():
        return errors

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(ValidationError(
                f"skill/{skill_dir.name}",
                "Missing SKILL.md"
            ))
            continue

        # Check for frontmatter
        content = skill_md.read_text()
        if not content.startswith("---"):
            errors.append(ValidationError(
                f"skill/{skill_dir.name}",
                "SKILL.md missing YAML frontmatter"
            ))
        else:
            # Parse frontmatter
            frontmatter_end = content.find("---", 3)
            if frontmatter_end == -1:
                errors.append(ValidationError(
                    f"skill/{skill_dir.name}",
                    "SKILL.md has unclosed frontmatter"
                ))
            else:
                frontmatter = content[3:frontmatter_end].strip()
                if "name:" not in frontmatter:
                    errors.append(ValidationError(
                        f"skill/{skill_dir.name}",
                        "SKILL.md frontmatter missing 'name' field"
                    ))
                if "description:" not in frontmatter:
                    errors.append(ValidationError(
                        f"skill/{skill_dir.name}",
                        "SKILL.md frontmatter missing 'description' field"
                    ))

    return errors


def validate_agents(plugin_path: Path) -> List[ValidationError]:
    """Validate agents in the plugin."""
    errors = []
    agents_dir = plugin_path / "agents"

    if not agents_dir.exists():
        return errors

    for agent_file in agents_dir.glob("*.md"):
        content = agent_file.read_text()

        # Check for frontmatter
        if not content.startswith("---"):
            errors.append(ValidationError(
                f"agent/{agent_file.stem}",
                "Agent file missing YAML frontmatter"
            ))
        else:
            frontmatter_end = content.find("---", 3)
            if frontmatter_end == -1:
                errors.append(ValidationError(
                    f"agent/{agent_file.stem}",
                    "Agent file has unclosed frontmatter"
                ))
            else:
                frontmatter = content[3:frontmatter_end].strip()
                if "name:" not in frontmatter:
                    errors.append(ValidationError(
                        f"agent/{agent_file.stem}",
                        "Agent frontmatter missing 'name' field"
                    ))
                if "description:" not in frontmatter:
                    errors.append(ValidationError(
                        f"agent/{agent_file.stem}",
                        "Agent frontmatter missing 'description' field"
                    ))

    return errors


def validate_commands(plugin_path: Path) -> List[ValidationError]:
    """Validate commands in the plugin."""
    errors = []
    commands_dir = plugin_path / "commands"

    if not commands_dir.exists():
        return errors

    for command_file in commands_dir.glob("*.md"):
        content = command_file.read_text()

        # Check for frontmatter
        if not content.startswith("---"):
            errors.append(ValidationError(
                f"command/{command_file.stem}",
                "Command file missing YAML frontmatter"
            ))

    return errors


def validate_hooks(plugin_path: Path) -> List[ValidationError]:
    """Validate hooks configuration."""
    errors = []
    hooks_file = plugin_path / "hooks" / "hooks.json"

    if not hooks_file.exists():
        return errors

    try:
        with open(hooks_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            "hooks",
            f"Invalid JSON in hooks.json: {e}"
        ))
        return errors

    valid_events = ["PreToolUse", "PostToolUse", "Notification", "Stop", "SubagentStop"]
    valid_types = ["command", "prompt", "agent"]

    hooks = config.get("hooks", {})
    for event, handlers in hooks.items():
        if event not in valid_events:
            errors.append(ValidationError(
                "hooks",
                f"Unknown event type: {event}",
                "warning"
            ))

        if not isinstance(handlers, list):
            errors.append(ValidationError(
                "hooks",
                f"Event '{event}' handlers must be an array"
            ))
            continue

        for i, handler in enumerate(handlers):
            if "type" not in handler:
                errors.append(ValidationError(
                    "hooks",
                    f"Handler {i} for '{event}' missing 'type' field"
                ))
            elif handler["type"] not in valid_types:
                errors.append(ValidationError(
                    "hooks",
                    f"Handler {i} for '{event}' has invalid type: {handler['type']}"
                ))

    return errors


def validate_mcp(plugin_path: Path) -> List[ValidationError]:
    """Validate MCP configuration."""
    errors = []
    mcp_file = plugin_path / ".mcp.json"

    if not mcp_file.exists():
        return errors

    try:
        with open(mcp_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            "mcp",
            f"Invalid JSON in .mcp.json: {e}"
        ))
        return errors

    servers = config.get("mcpServers", {})
    for name, server in servers.items():
        if "command" not in server:
            errors.append(ValidationError(
                f"mcp/{name}",
                "Missing required 'command' field"
            ))

    return errors


def validate_lsp(plugin_path: Path) -> List[ValidationError]:
    """Validate LSP configuration."""
    errors = []
    lsp_file = plugin_path / ".lsp.json"

    if not lsp_file.exists():
        return errors

    try:
        with open(lsp_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(ValidationError(
            "lsp",
            f"Invalid JSON in .lsp.json: {e}"
        ))
        return errors

    servers = config.get("lspServers", {})
    for name, server in servers.items():
        if "command" not in server:
            errors.append(ValidationError(
                f"lsp/{name}",
                "Missing required 'command' field"
            ))
        if "extensionToLanguage" not in server:
            errors.append(ValidationError(
                f"lsp/{name}",
                "Missing required 'extensionToLanguage' field"
            ))

    return errors


def validate_plugin(plugin_path: Path) -> Tuple[List[ValidationError], List[ValidationError]]:
    """Validate the entire plugin."""
    all_errors = []

    all_errors.extend(validate_manifest(plugin_path))
    all_errors.extend(validate_skills(plugin_path))
    all_errors.extend(validate_agents(plugin_path))
    all_errors.extend(validate_commands(plugin_path))
    all_errors.extend(validate_hooks(plugin_path))
    all_errors.extend(validate_mcp(plugin_path))
    all_errors.extend(validate_lsp(plugin_path))

    errors = [e for e in all_errors if e.severity == "error"]
    warnings = [e for e in all_errors if e.severity == "warning"]

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(
        description="Validate a Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )

    args = parser.parse_args()
    plugin_path = Path(args.plugin_path)

    if not plugin_path.exists():
        print(f"Error: Path '{plugin_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not plugin_path.is_dir():
        print(f"Error: '{plugin_path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    errors, warnings = validate_plugin(plugin_path)

    # Print warnings
    for warning in warnings:
        print(f"\033[33m{warning}\033[0m")

    # Print errors
    for error in errors:
        print(f"\033[31m{error}\033[0m")

    # Summary
    print()
    if errors:
        print(f"\033[31mValidation failed: {len(errors)} error(s), {len(warnings)} warning(s)\033[0m")
        sys.exit(1)
    elif warnings:
        print(f"\033[33mValidation passed with {len(warnings)} warning(s)\033[0m")
    else:
        print(f"\033[32mValidation passed: Plugin is valid\033[0m")


if __name__ == "__main__":
    main()
