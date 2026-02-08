#!/bin/bash

# Check if Claude Code agent-teams feature is available.
# Used by the orchestrator and stop hook for fallback detection.
#
# Exit codes:
#   0 = agent-teams available
#   1 = agent-teams not available
#
# Usage:
#   if ./check_teams.sh; then
#     echo "Teams available"
#   else
#     echo "Teams not available, falling back to sequential"
#   fi

set -euo pipefail

# Check 1: Environment variable must be set
if [[ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" != "1" ]]; then
  echo "agent-teams: not enabled (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS != 1)" >&2
  exit 1
fi

# Check 2: Verify claude CLI is available
if ! command -v claude &>/dev/null; then
  echo "agent-teams: claude CLI not found" >&2
  exit 1
fi

echo "agent-teams: available" >&2
exit 0
