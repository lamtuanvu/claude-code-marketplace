#!/usr/bin/env python3
"""
SpecKit Orchestrator - Execute the SpecKit pipeline one step at a time.

Pipeline: specify → clarify → plan → tasks → analyze → implement

Prerequisites:
- Feature branch exists
- docs/features/<feature>/idea.md exists
- docs/features/<feature>/orchestrator-state.json exists

Usage:
    python orchestrator.py init <feature> <branch>   Initialize state
    python orchestrator.py execute                   Run next step
    python orchestrator.py status [feature]          Show progress
    python orchestrator.py rollback <step>           Reset to step
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Tuple


class Step(Enum):
    SPECIFY = "specify"
    CLARIFY = "clarify"
    PLAN = "plan"
    TASKS = "tasks"
    ANALYZE = "analyze"
    IMPLEMENT = "implement"


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class OrchestratorState:
    """Tracks pipeline execution state."""
    feature_name: str
    branch_name: str
    idea_file: str
    spec_dir: str
    current_step: str
    step_status: dict
    started_at: str
    last_updated: str

    @classmethod
    def new(cls, feature_name: str, branch_name: str, base_dir: str) -> 'OrchestratorState':
        """Create new state."""
        now = datetime.utcnow().isoformat() + "Z"
        feature_dir = os.path.join(base_dir, "docs", "features", feature_name)

        return cls(
            feature_name=feature_name,
            branch_name=branch_name,
            idea_file=os.path.join(feature_dir, "idea.md"),
            spec_dir=os.path.join(base_dir, "specs", feature_name),
            current_step=Step.SPECIFY.value,
            step_status={
                Step.SPECIFY.value: StepStatus.PENDING.value,
                Step.CLARIFY.value: StepStatus.PENDING.value,
                Step.PLAN.value: StepStatus.PENDING.value,
                Step.TASKS.value: StepStatus.PENDING.value,
                Step.ANALYZE.value: StepStatus.PENDING.value,
                Step.IMPLEMENT.value: StepStatus.PENDING.value,
            },
            started_at=now,
            last_updated=now,
        )

    @classmethod
    def load(cls, state_file: str) -> 'OrchestratorState':
        """Load state from file."""
        with open(state_file, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def save(self, state_file: str) -> None:
        """Save state to file."""
        self.last_updated = datetime.utcnow().isoformat() + "Z"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def get_next_step(self) -> Optional[Step]:
        """Get next pending step."""
        for step in Step:
            status = StepStatus(self.step_status.get(step.value, 'pending'))
            if status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                return step
        return None

    def get_state_file(self, base_dir: str) -> str:
        """Get state file path."""
        return os.path.join(base_dir, "docs", "features", self.feature_name, "orchestrator-state.json")


def get_current_branch() -> Optional[str]:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def extract_feature_from_branch(branch: str) -> Optional[str]:
    """Extract feature name from branch."""
    if not branch or branch in ['main', 'master', 'develop', 'HEAD']:
        return None

    # Pattern: 042-feature-name
    match = re.match(r'^\d+-(.+)$', branch)
    if match:
        return match.group(1)

    return branch


def find_state_file(base_dir: str) -> Tuple[Optional[str], Optional[str]]:
    """Find state file from current branch."""
    branch = get_current_branch()
    if not branch:
        return None, None

    feature = extract_feature_from_branch(branch)
    if not feature:
        return None, None

    state_file = os.path.join(base_dir, "docs", "features", feature, "orchestrator-state.json")
    if os.path.exists(state_file):
        return state_file, feature

    return None, feature


def print_progress(state: OrchestratorState) -> None:
    """Print progress display."""
    steps = list(Step)
    symbols = []

    for step in steps:
        status = StepStatus(state.step_status.get(step.value, 'pending'))
        if status == StepStatus.COMPLETED:
            symbols.append(f"[✓] {step.value.title()}")
        elif status == StepStatus.SKIPPED:
            symbols.append(f"[−] {step.value.title()}")
        elif status == StepStatus.IN_PROGRESS:
            symbols.append(f"[▶] {step.value.title()}")
        else:
            symbols.append(f"[ ] {step.value.title()}")

    print("╔" + "═" * 68 + "╗")
    print("║  SpecKit Orchestrator" + " " * 47 + "║")
    print("╠" + "═" * 68 + "╣")
    print(f"║  Feature: {state.feature_name:<56} ║")
    print(f"║  Branch: {state.branch_name:<57} ║")

    # Truncate idea_file if too long
    idea_display = state.idea_file
    if len(idea_display) > 48:
        idea_display = "..." + idea_display[-45:]
    print(f"║  Source: {idea_display:<57} ║")
    print("╠" + "═" * 68 + "╣")

    row1 = "  →  ".join(symbols[:3])
    row2 = "  →  ".join(symbols[3:])
    print(f"║  {row1:<64} ║")
    print(f"║  {row2:<64} ║")
    print("╚" + "═" * 68 + "╝")


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_init(args):
    """Initialize orchestrator state."""
    feature = args.feature
    branch = args.branch
    base_dir = os.getcwd()

    # Create state
    state = OrchestratorState.new(feature, branch, base_dir)

    # Check idea.md exists
    if not os.path.exists(state.idea_file):
        print(f"⚠ Warning: idea.md not found at {state.idea_file}")
        print("  Create idea.md before running --execute")

    # Save state
    state_file = state.get_state_file(base_dir)
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    state.save(state_file)

    print(f"✓ Initialized: {state_file}")
    print(f"\nTo start pipeline: /speckit-orchestrator --execute")

    print_progress(state)


def cmd_execute(args):
    """Execute next pipeline step."""
    base_dir = os.getcwd()

    # Find state
    state_file, feature = find_state_file(base_dir)

    if not state_file:
        branch = get_current_branch()
        if branch in ['main', 'master', 'develop']:
            print(f"Error: On '{branch}' branch. Switch to feature branch.")
        elif feature:
            print(f"Error: No state file found.")
            print(f"Run: python orchestrator.py init {feature} {branch}")
        else:
            print("Error: Not on a feature branch.")
        sys.exit(1)

    state = OrchestratorState.load(state_file)

    # Check idea.md
    if not os.path.exists(state.idea_file):
        print(f"Error: idea.md not found at {state.idea_file}")
        print("Create idea.md first.")
        sys.exit(1)

    # Get next step
    next_step = state.get_next_step()

    if not next_step:
        print("✅ All steps complete!")
        print_progress(state)
        return

    print("╔" + "═" * 68 + "╗")
    print("║  SpecKit Orchestrator - Execute Next Step                        ║")
    print("╠" + "═" * 68 + "╣")
    print(f"║  Feature: {state.feature_name:<56} ║")
    print(f"║  Next Step: {next_step.value:<54} ║")
    print("╚" + "═" * 68 + "╝")

    print(f"\n" + "=" * 70)
    print(f"RUN: /speckit.{next_step.value}")
    print("=" * 70)
    print(f"""
CONTEXT TO PASS:

"Follow {state.idea_file} strictly.
Do not add features beyond what idea.md specifies.
All work must align with the approved plan."

AFTER COMPLETION:

1. Update state file: {state_file}
   Set "{next_step.value}": "completed"
   Set "current_step": "<next-step>"

2. Display completion message

3. STOP AND WAIT for user to re-run --execute
""")
    print("=" * 70)

    print_progress(state)


def cmd_status(args):
    """Show pipeline status."""
    base_dir = os.getcwd()

    if hasattr(args, 'feature') and args.feature:
        state_file = os.path.join(base_dir, "docs", "features", args.feature, "orchestrator-state.json")
    else:
        state_file, _ = find_state_file(base_dir)

    if not state_file or not os.path.exists(state_file):
        print("Error: No state file found.")
        sys.exit(1)

    state = OrchestratorState.load(state_file)
    print_progress(state)

    print(f"\nStarted: {state.started_at}")
    print(f"Updated: {state.last_updated}")

    next_step = state.get_next_step()
    if next_step:
        print(f"\nNext step: {next_step.value}")
        print(f"Run: /speckit-orchestrator --execute")
    else:
        print("\n✅ All steps complete!")


def cmd_rollback(args):
    """Rollback to a step."""
    base_dir = os.getcwd()
    target = args.step

    state_file, _ = find_state_file(base_dir)
    if not state_file:
        print("Error: No state file found.")
        sys.exit(1)

    state = OrchestratorState.load(state_file)

    # Validate step
    try:
        target_step = Step(target)
    except ValueError:
        print(f"Invalid step: {target}")
        print(f"Valid steps: {', '.join(s.value for s in Step)}")
        sys.exit(1)

    # Reset from target onwards
    steps = list(Step)
    target_idx = steps.index(target_step)

    for i in range(target_idx, len(steps)):
        state.step_status[steps[i].value] = StepStatus.PENDING.value

    state.current_step = target_step.value
    state.save(state_file)

    print(f"Rolled back to: {target}")
    print_progress(state)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SpecKit Orchestrator - Execute pipeline one step at a time"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Init
    init_p = subparsers.add_parser("init", help="Initialize state")
    init_p.add_argument("feature", help="Feature name")
    init_p.add_argument("branch", help="Branch name")
    init_p.set_defaults(func=cmd_init)

    # Execute
    exec_p = subparsers.add_parser("execute", help="Run next step")
    exec_p.set_defaults(func=cmd_execute)

    # Status
    status_p = subparsers.add_parser("status", help="Show status")
    status_p.add_argument("feature", nargs='?', help="Feature name")
    status_p.set_defaults(func=cmd_status)

    # Rollback
    rollback_p = subparsers.add_parser("rollback", help="Rollback to step")
    rollback_p.add_argument("step", help="Step to rollback to")
    rollback_p.set_defaults(func=cmd_rollback)

    args = parser.parse_args()

    if not args.command:
        # Default: show status or help
        state_file, _ = find_state_file(os.getcwd())
        if state_file:
            cmd_status(args)
        else:
            parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
