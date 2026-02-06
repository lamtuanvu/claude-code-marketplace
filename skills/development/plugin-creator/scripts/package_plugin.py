#!/usr/bin/env python3
"""
Package a Claude Code plugin for distribution.

Usage:
    python package_plugin.py <plugin-path> <output-dir>

Examples:
    python package_plugin.py ./my-plugin ./dist
    python package_plugin.py ./my-plugin ./dist --validate
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


def get_plugin_info(plugin_path: Path) -> dict:
    """Get plugin name and version from manifest."""
    manifest_path = plugin_path / ".claude-plugin" / "plugin.json"

    if not manifest_path.exists():
        print(f"Error: '{plugin_path}' is not a valid plugin directory.", file=sys.stderr)
        print("Missing .claude-plugin/plugin.json manifest.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        return json.load(f)


def run_validation(plugin_path: Path) -> bool:
    """Run validation and return success status."""
    script_dir = Path(__file__).parent
    validate_script = script_dir / "validate_plugin.py"

    if not validate_script.exists():
        print("Warning: validate_plugin.py not found, skipping validation", file=sys.stderr)
        return True

    result = subprocess.run(
        [sys.executable, str(validate_script), str(plugin_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Validation failed:")
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return False

    print("Validation passed")
    return True


def should_include(path: Path, plugin_path: Path) -> bool:
    """Determine if a path should be included in the package."""
    # Get relative path
    rel_path = path.relative_to(plugin_path)
    parts = rel_path.parts

    # Exclude patterns
    exclude_patterns = [
        ".git",
        ".gitignore",
        ".DS_Store",
        "__pycache__",
        "*.pyc",
        ".env",
        ".venv",
        "node_modules",
        "dist",
        "build",
        "*.log",
    ]

    for part in parts:
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if part.endswith(pattern[1:]):
                    return False
            elif part == pattern:
                return False

    return True


def package_plugin(plugin_path: Path, output_dir: Path, validate: bool) -> Path:
    """Package the plugin into a zip file."""

    # Run validation if requested
    if validate:
        if not run_validation(plugin_path):
            sys.exit(1)

    # Get plugin info
    info = get_plugin_info(plugin_path)
    plugin_name = info.get("name", plugin_path.name)
    plugin_version = info.get("version", "1.0.0")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create zip filename
    zip_name = f"{plugin_name}-{plugin_version}.zip"
    zip_path = output_dir / zip_name

    # Remove existing zip if present
    if zip_path.exists():
        zip_path.unlink()

    # Create zip file
    with ZipFile(zip_path, "w") as zf:
        for path in plugin_path.rglob("*"):
            if path.is_file() and should_include(path, plugin_path):
                rel_path = path.relative_to(plugin_path)
                # Include plugin name as root directory in zip
                archive_path = Path(plugin_name) / rel_path
                zf.write(path, archive_path)
                print(f"  Added: {rel_path}")

    return zip_path


def main():
    parser = argparse.ArgumentParser(
        description="Package a Claude Code plugin for distribution"
    )
    parser.add_argument(
        "plugin_path",
        help="Path to the plugin directory"
    )
    parser.add_argument(
        "output_dir",
        help="Output directory for the package"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run validation before packaging (default: true)"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation"
    )

    args = parser.parse_args()

    plugin_path = Path(args.plugin_path)
    output_dir = Path(args.output_dir)

    if not plugin_path.exists():
        print(f"Error: Plugin path '{plugin_path}' does not exist", file=sys.stderr)
        sys.exit(1)

    validate = args.validate and not args.no_validate

    print(f"Packaging plugin: {plugin_path}")
    print()

    zip_path = package_plugin(plugin_path, output_dir, validate)

    print()
    print(f"\033[32mPackage created: {zip_path}\033[0m")
    print()
    print("Distribution:")
    print(f"  1. Upload to a plugin marketplace")
    print(f"  2. Or share the zip file directly")
    print()
    print("Installation:")
    print(f"  1. Unzip to a directory")
    print(f"  2. Run: claude --plugin-dir <unzipped-path>")


if __name__ == "__main__":
    main()
