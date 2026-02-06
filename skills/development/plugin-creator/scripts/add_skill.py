#!/usr/bin/env python3
"""
Add a skill to an existing Claude Code plugin.

Usage:
    python add_skill.py <plugin-path> <skill-name> [options]

Examples:
    python add_skill.py ./my-plugin code-reviewer
    python add_skill.py ./my-plugin code-reviewer --description "Reviews code quality"
    python add_skill.py ./my-plugin code-reviewer --with-scripts --with-references
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


def add_skill(plugin_path: Path, skill_name: str, description: str,
              with_scripts: bool, with_references: bool, with_assets: bool) -> Path:
    """Add a skill to the plugin."""

    skills_dir = plugin_path / "skills"
    skills_dir.mkdir(exist_ok=True)

    skill_dir = skills_dir / skill_name
    if skill_dir.exists():
        print(f"Error: Skill '{skill_name}' already exists at {skill_dir}", file=sys.stderr)
        sys.exit(1)

    skill_dir.mkdir()

    # Create optional subdirectories
    if with_scripts:
        (skill_dir / "scripts").mkdir()
    if with_references:
        (skill_dir / "references").mkdir()
    if with_assets:
        (skill_dir / "assets").mkdir()

    # Create SKILL.md
    skill_content = f"""---
name: {skill_name}
description: {description or f"A skill for {skill_name}"}
---

# {skill_name.replace("-", " ").title()}

{description or f"Description of what {skill_name} does."}

## When to Use

Use this skill when:
- [Describe use case 1]
- [Describe use case 2]

## Usage

[Describe how to use this skill]

## Examples

```
# Example usage
/{plugin_path.name}:{skill_name}
```
"""

    if with_scripts:
        skill_content += """
## Scripts

This skill includes helper scripts in the `scripts/` directory.
"""

    if with_references:
        skill_content += """
## References

Additional documentation available in the `references/` directory.
"""

    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, "w") as f:
        f.write(skill_content)

    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Add a skill to an existing Claude Code plugin"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "skill_name",
        help="Name of the skill to add"
    )
    parser.add_argument(
        "--description",
        default="",
        help="Skill description"
    )
    parser.add_argument(
        "--with-scripts",
        action="store_true",
        help="Create a scripts/ subdirectory"
    )
    parser.add_argument(
        "--with-references",
        action="store_true",
        help="Create a references/ subdirectory"
    )
    parser.add_argument(
        "--with-assets",
        action="store_true",
        help="Create an assets/ subdirectory"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    if not validate_plugin(plugin_path):
        sys.exit(1)

    skill_dir = add_skill(
        plugin_path=plugin_path,
        skill_name=args.skill_name.lower(),
        description=args.description,
        with_scripts=args.with_scripts,
        with_references=args.with_references,
        with_assets=args.with_assets
    )

    print(f"Added skill at: {skill_dir}")
    print()
    print("Next steps:")
    print(f"  1. Edit the SKILL.md: {skill_dir / 'SKILL.md'}")
    if args.with_scripts:
        print(f"  2. Add scripts to: {skill_dir / 'scripts'}")
    print(f"  3. Test: claude --plugin-dir {plugin_path}")


if __name__ == "__main__":
    main()
