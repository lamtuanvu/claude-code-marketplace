#!/usr/bin/env python3
"""
SpecKit Orchestrator - Execute the SpecKit pipeline one step at a time.

Pipeline: specify → clarify → plan → [plan-review] → tasks → analyze → implement

When agent-teams are enabled, plan-review and implement steps use parallel
multi-agent teams for specialist reviews and parallel implementation.

Prerequisites:
- Feature branch exists
- docs/features/<feature>/idea.md exists
- docs/features/<feature>/orchestrator-state.json exists

Usage:
    python orchestrator.py init <feature> <branch>   Initialize state
    python orchestrator.py execute                   Run next step
    python orchestrator.py status [feature]          Show progress
    python orchestrator.py rollback <step>           Reset to step
    python orchestrator.py team-status               Show team status
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
    PLAN_REVIEW = "plan-review"
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
    teams_enabled: bool = True
    team_state: Optional[dict] = None

    @classmethod
    def new(cls, feature_name: str, branch_name: str, base_dir: str,
            teams_enabled: bool = True) -> 'OrchestratorState':
        """Create new state."""
        now = datetime.utcnow().isoformat() + "Z"
        feature_dir = os.path.join(base_dir, "docs", "features", feature_name)

        step_status = {
            Step.SPECIFY.value: StepStatus.PENDING.value,
            Step.CLARIFY.value: StepStatus.PENDING.value,
            Step.PLAN.value: StepStatus.PENDING.value,
            Step.PLAN_REVIEW.value: StepStatus.SKIPPED.value if not teams_enabled else StepStatus.PENDING.value,
            Step.TASKS.value: StepStatus.PENDING.value,
            Step.ANALYZE.value: StepStatus.PENDING.value,
            Step.IMPLEMENT.value: StepStatus.PENDING.value,
        }

        return cls(
            feature_name=feature_name,
            branch_name=branch_name,
            idea_file=os.path.join(feature_dir, "idea.md"),
            spec_dir=os.path.join(base_dir, "specs", feature_name),
            current_step=Step.SPECIFY.value,
            step_status=step_status,
            started_at=now,
            last_updated=now,
            teams_enabled=teams_enabled,
            team_state=None,
        )

    @classmethod
    def load(cls, state_file: str) -> 'OrchestratorState':
        """Load state from file, with backward compatibility for old 6-step states."""
        with open(state_file, 'r') as f:
            data = json.load(f)

        # Backward compat: add teams_enabled if missing
        if 'teams_enabled' not in data:
            data['teams_enabled'] = False
        if 'team_state' not in data:
            data['team_state'] = None

        # Backward compat: add plan-review step if missing
        if Step.PLAN_REVIEW.value not in data.get('step_status', {}):
            data['step_status'][Step.PLAN_REVIEW.value] = (
                StepStatus.PENDING.value if data['teams_enabled']
                else StepStatus.SKIPPED.value
            )

        return cls(**data)

    def save(self, state_file: str) -> None:
        """Save state to file."""
        self.last_updated = datetime.utcnow().isoformat() + "Z"
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def get_next_step(self) -> Optional[Step]:
        """Get next pending step, skipping plan-review when teams disabled."""
        for step in Step:
            if step == Step.PLAN_REVIEW and not self.teams_enabled:
                continue
            status = StepStatus(self.step_status.get(step.value, 'pending'))
            if status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                return step
        return None

    def is_team_step(self, step: Step) -> bool:
        """Check if a step uses agent teams."""
        return self.teams_enabled and step in (Step.PLAN_REVIEW, Step.IMPLEMENT)

    def update_team_state(self, team_name: str, phase: str,
                          teammates: dict, timeout_minutes: int = 15) -> None:
        """Set team_state when a team phase starts."""
        self.team_state = {
            "active_team": team_name,
            "phase": phase,
            "teammates": teammates,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "timeout_minutes": timeout_minutes,
        }

    def clear_team_state(self) -> None:
        """Clear team_state after team phase completes."""
        self.team_state = None

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


def _step_label(step: Step, state: OrchestratorState) -> str:
    """Format step name with team indicator."""
    name = step.value.replace("-", " ").title()
    if state.is_team_step(step):
        name = f"{name} ⚡"
    return name


def print_progress(state: OrchestratorState) -> None:
    """Print progress display."""
    steps = list(Step)
    symbols = []

    for step in steps:
        status = StepStatus(state.step_status.get(step.value, 'pending'))
        label = _step_label(step, state)
        if status == StepStatus.COMPLETED:
            symbols.append(f"[✓] {label}")
        elif status == StepStatus.SKIPPED:
            symbols.append(f"[−] {label}")
        elif status == StepStatus.IN_PROGRESS:
            symbols.append(f"[▶] {label}")
        else:
            symbols.append(f"[ ] {label}")

    width = 72
    print("╔" + "═" * width + "╗")
    title = "SpecKit Orchestrator"
    if state.teams_enabled:
        title += " (Teams Enabled)"
    print(f"║  {title:<{width - 2}} ║")
    print("╠" + "═" * width + "╣")
    print(f"║  Feature: {state.feature_name:<{width - 12}} ║")
    print(f"║  Branch: {state.branch_name:<{width - 11}} ║")

    idea_display = state.idea_file
    max_idea = width - 11
    if len(idea_display) > max_idea:
        idea_display = "..." + idea_display[-(max_idea - 3):]
    print(f"║  Source: {idea_display:<{width - 11}} ║")
    print("╠" + "═" * width + "╣")

    # Row 1: specify, clarify, plan, plan-review (4 steps)
    row1 = "  →  ".join(symbols[:4])
    # Row 2: tasks, analyze, implement (3 steps)
    row2 = "  →  ".join(symbols[4:])
    print(f"║  {row1:<{width - 2}} ║")
    print(f"║  {row2:<{width - 2}} ║")

    # Show team status if active
    if state.team_state and state.team_state.get("active_team"):
        print("╠" + "═" * width + "╣")
        team_name = state.team_state["active_team"]
        phase = state.team_state.get("phase", "unknown")
        print(f"║  Team: {team_name:<{width - 9}} ║")
        teammates = state.team_state.get("teammates", {})
        for name, info in teammates.items():
            t_status = info.get("status", "unknown")
            icon = "✓" if t_status == "completed" else "▶" if t_status == "in_progress" else "✗" if t_status == "failed" else " "
            print(f"║    [{icon}] {name:<{width - 8}} ║")

    print("╚" + "═" * width + "╝")


# ============================================================================
# PIPELINE PAUSE HELPERS
# ============================================================================

def _clear_paused_flag(state_file: str) -> None:
    """Clear pipeline_paused flag from state file."""
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
        if data.get('pipeline_paused'):
            data['pipeline_paused'] = False
            data['last_updated'] = datetime.utcnow().isoformat() + "Z"
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
    except (json.JSONDecodeError, FileNotFoundError):
        pass


def _set_paused_flag(state_file: str) -> None:
    """Set pipeline_paused flag in state file."""
    try:
        with open(state_file, 'r') as f:
            data = json.load(f)
        data['pipeline_paused'] = True
        data['last_updated'] = datetime.utcnow().isoformat() + "Z"
        with open(state_file, 'w') as f:
            json.dump(data, f, indent=2)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: Could not update state file: {e}")
        sys.exit(1)


# ============================================================================
# COMMANDS
# ============================================================================

def cmd_init(args):
    """Initialize orchestrator state."""
    feature = args.feature
    branch = args.branch
    base_dir = os.getcwd()
    teams_enabled = getattr(args, 'teams', True)

    # Create state
    state = OrchestratorState.new(feature, branch, base_dir, teams_enabled=teams_enabled)

    # Check idea.md exists
    if not os.path.exists(state.idea_file):
        print(f"⚠ Warning: idea.md not found at {state.idea_file}")
        print("  Create idea.md before running /speckit-orchestrator:execute")

    # Save state
    state_file = state.get_state_file(base_dir)
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    state.save(state_file)

    teams_label = "enabled" if teams_enabled else "disabled"
    print(f"✓ Initialized: {state_file}")
    print(f"  Agent teams: {teams_label}")
    print(f"\nTo start pipeline: /speckit-orchestrator:execute")

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
    # Clear pipeline_paused flag on execute so the stop hook resumes auto-continuation
    _clear_paused_flag(state_file)

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

The stop hook will auto-continue to the next step.
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
    print(f"Teams: {'enabled' if state.teams_enabled else 'disabled'}")

    next_step = state.get_next_step()
    if next_step:
        step_type = " (team phase)" if state.is_team_step(next_step) else ""
        print(f"\nNext step: {next_step.value}{step_type}")
        print(f"Run: /speckit-orchestrator:execute")
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


def cmd_cancel(args):
    """Pause pipeline so the stop hook allows exit."""
    base_dir = os.getcwd()

    state_file, feature = find_state_file(base_dir)
    if not state_file:
        print("Error: No state file found. Nothing to cancel.")
        sys.exit(1)

    _set_paused_flag(state_file)

    state = OrchestratorState.load(state_file)
    next_step = state.get_next_step()

    print(f"⏸ Pipeline paused for feature: {feature}")
    if next_step:
        print(f"  Paused before step: {next_step.value}")
    print(f"\nTo resume: /speckit-orchestrator:execute")
    print_progress(state)


def cmd_team_status(args):
    """Show detailed team status."""
    base_dir = os.getcwd()

    state_file, feature = find_state_file(base_dir)
    if not state_file:
        print("Error: No state file found.")
        sys.exit(1)

    state = OrchestratorState.load(state_file)

    if not state.teams_enabled:
        print("Agent teams: disabled")
        print("Run with --teams to enable parallel team phases.")
        return

    print(f"Agent teams: enabled")

    if not state.team_state:
        print("No team currently active.")
        next_step = state.get_next_step()
        if next_step and state.is_team_step(next_step):
            print(f"Next team phase: {next_step.value}")
        return

    ts = state.team_state
    print(f"\nActive team: {ts.get('active_team', 'unknown')}")
    print(f"Phase: {ts.get('phase', 'unknown')}")
    print(f"Started: {ts.get('started_at', 'unknown')}")
    print(f"Timeout: {ts.get('timeout_minutes', 15)} minutes")

    teammates = ts.get("teammates", {})
    if teammates:
        print(f"\nTeammates ({len(teammates)}):")
        for name, info in teammates.items():
            t_status = info.get("status", "unknown")
            output = info.get("output", "")
            icon = {"completed": "✓", "in_progress": "▶", "failed": "✗"}.get(t_status, " ")
            line = f"  [{icon}] {name}: {t_status}"
            if output:
                line += f" → {output}"
            print(line)

        completed = sum(1 for i in teammates.values() if i.get("status") == "completed")
        failed = sum(1 for i in teammates.values() if i.get("status") == "failed")
        print(f"\n  Progress: {completed}/{len(teammates)} completed", end="")
        if failed:
            print(f", {failed} failed", end="")
        print()


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
    init_p.add_argument("--teams", dest="teams", action="store_true", default=True,
                        help="Enable agent teams for parallel phases (default)")
    init_p.add_argument("--no-teams", dest="teams", action="store_false",
                        help="Disable agent teams, run fully sequential")
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

    # Cancel (pause pipeline)
    cancel_p = subparsers.add_parser("cancel", help="Pause pipeline")
    cancel_p.set_defaults(func=cmd_cancel)

    # Team status
    team_p = subparsers.add_parser("team-status", help="Show team status")
    team_p.set_defaults(func=cmd_team_status)

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
