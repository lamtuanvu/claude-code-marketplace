#!/usr/bin/env python3
"""
Initialize a feature for SpecKit orchestration.

Creates:
- docs/features/<feature>/orchestrator-state.json

Usage:
    python init_feature.py <feature-name> <branch-name>
"""

import argparse
import json
import os
import sys
from datetime import datetime


def create_state(feature_name: str, branch_name: str, base_dir: str) -> dict:
    """Create initial orchestrator state."""
    now = datetime.utcnow().isoformat() + "Z"
    feature_dir = os.path.join(base_dir, "docs", "features", feature_name)

    return {
        "feature_name": feature_name,
        "branch_name": branch_name,
        "idea_file": os.path.join(feature_dir, "idea.md"),
        "spec_dir": os.path.join(base_dir, "specs", feature_name),
        "current_step": "specify",
        "step_status": {
            "specify": "pending",
            "clarify": "pending",
            "plan": "pending",
            "tasks": "pending",
            "analyze": "pending",
            "implement": "pending",
        },
        "started_at": now,
        "last_updated": now,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a feature for SpecKit orchestration"
    )
    parser.add_argument("feature", help="Feature name (kebab-case)")
    parser.add_argument("branch", help="Git branch name")
    parser.add_argument(
        "--base-dir",
        default=os.getcwd(),
        help="Base directory (default: current working directory)",
    )

    args = parser.parse_args()

    feature_dir = os.path.join(args.base_dir, "docs", "features", args.feature)
    state_file = os.path.join(feature_dir, "orchestrator-state.json")

    # Create directory
    os.makedirs(feature_dir, exist_ok=True)

    # Check if idea.md exists
    idea_file = os.path.join(feature_dir, "idea.md")
    if not os.path.exists(idea_file):
        print(f"⚠ Warning: idea.md not found at {idea_file}")
        print("  Create idea.md before running /speckit-orchestrator --execute")

    # Create state
    state = create_state(args.feature, args.branch, args.base_dir)

    # Save state
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    print(f"✓ Created: {state_file}")
    print(f"\nNext step: /speckit-orchestrator --execute")


if __name__ == "__main__":
    main()
