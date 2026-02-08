#!/bin/bash

# SpecKit Orchestrator Stop Hook
# Intercepts stop signals to auto-continue the pipeline between steps.
# Only blocks stop when a step was positively completed and a next step exists.
# Any ambiguity → allow stop (safety-first to prevent infinite loops).
#
# Team-aware: when an agent team is active, blocks stop until all teammates
# finish or the timeout expires.

set -euo pipefail

# Read hook input from stdin
HOOK_INPUT=$(cat)

# -------------------------------------------------------------------
# 1. Determine current branch; skip non-feature branches
# -------------------------------------------------------------------
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

if [[ -z "$BRANCH" ]] || [[ "$BRANCH" == "main" ]] || [[ "$BRANCH" == "master" ]] || [[ "$BRANCH" == "develop" ]] || [[ "$BRANCH" == "HEAD" ]]; then
  exit 0
fi

# -------------------------------------------------------------------
# 2. Extract feature name from branch (pattern: NNN-feature-name)
# -------------------------------------------------------------------
if [[ "$BRANCH" =~ ^[0-9]+-(.+)$ ]]; then
  FEATURE="${BASH_REMATCH[1]}"
else
  FEATURE="$BRANCH"
fi

# -------------------------------------------------------------------
# 3. Locate orchestrator-state.json; if missing → allow stop
# -------------------------------------------------------------------
STATE_FILE="docs/features/${FEATURE}/orchestrator-state.json"

if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

# -------------------------------------------------------------------
# 4. Parse state JSON with jq; if corrupted → allow stop with warning
# -------------------------------------------------------------------
if ! STATE=$(jq '.' "$STATE_FILE" 2>/dev/null); then
  echo "Warning: SpecKit orchestrator-state.json is corrupted. Allowing stop." >&2
  exit 0
fi

# -------------------------------------------------------------------
# 5. Check pipeline_paused flag → if true, allow stop
# -------------------------------------------------------------------
PAUSED=$(echo "$STATE" | jq -r '.pipeline_paused // false')
if [[ "$PAUSED" == "true" ]]; then
  exit 0
fi

# -------------------------------------------------------------------
# 6. Check if a team is active → block stop while teammates working
# -------------------------------------------------------------------
TEAM_ACTIVE=$(echo "$STATE" | jq -r '.team_state.active_team // ""')
if [[ -n "$TEAM_ACTIVE" ]]; then
  # Check timeout: if elapsed > timeout_minutes, allow stop with warning
  TEAM_STARTED=$(echo "$STATE" | jq -r '.team_state.started_at // ""')
  TIMEOUT_MINS=$(echo "$STATE" | jq -r '.team_state.timeout_minutes // 15')

  if [[ -n "$TEAM_STARTED" ]]; then
    # Calculate elapsed minutes
    STARTED_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${TEAM_STARTED%%.*}" "+%s" 2>/dev/null || \
                    date -d "${TEAM_STARTED}" "+%s" 2>/dev/null || echo "0")
    NOW_EPOCH=$(date "+%s")
    if [[ "$STARTED_EPOCH" -gt 0 ]]; then
      ELAPSED_MINS=$(( (NOW_EPOCH - STARTED_EPOCH) / 60 ))
      if [[ "$ELAPSED_MINS" -ge "$TIMEOUT_MINS" ]]; then
        # Timeout exceeded → allow stop with warning
        echo "Warning: SpecKit team timeout exceeded (${ELAPSED_MINS}m >= ${TIMEOUT_MINS}m). Allowing stop." >&2
        exit 0
      fi
    fi
  fi

  # Check incomplete teammates
  INCOMPLETE=$(echo "$STATE" | jq '[.team_state.teammates // {} | to_entries[]
    | select(.value.status != "completed" and .value.status != "failed")] | length')

  if [[ "$INCOMPLETE" -gt 0 ]]; then
    # Block stop - teammates still working
    PHASE=$(echo "$STATE" | jq -r '.team_state.phase // "unknown"')
    jq -n \
      --arg reason "/speckit-orchestrator --execute" \
      --arg msg "SpecKit Team [${PHASE}]: ${INCOMPLETE} teammates still working on ${FEATURE}" \
      '{
        "decision": "block",
        "reason": $reason,
        "systemMessage": $msg
      }'
    exit 0
  fi

  # All teammates done → fall through to normal step logic
fi

# -------------------------------------------------------------------
# 7. Define step order and read statuses
#    Conditionally include plan-review based on teams_enabled
# -------------------------------------------------------------------
TEAMS_ENABLED=$(echo "$STATE" | jq -r '.teams_enabled // false')

if [[ "$TEAMS_ENABLED" == "true" ]]; then
  STEPS=("specify" "clarify" "plan" "plan-review" "tasks" "analyze" "implement")
else
  STEPS=("specify" "clarify" "plan" "tasks" "analyze" "implement")
fi
TOTAL_STEPS=${#STEPS[@]}

# Check for any failed step → allow stop
for STEP in "${STEPS[@]}"; do
  STATUS=$(echo "$STATE" | jq -r --arg s "$STEP" '.step_status[$s] // "pending"')
  if [[ "$STATUS" == "failed" ]]; then
    exit 0
  fi
done

# Find the first non-completed/non-skipped step (the next step to run)
NEXT_STEP=""
NEXT_STEP_INDEX=0
COMPLETED_COUNT=0

for i in "${!STEPS[@]}"; do
  STEP="${STEPS[$i]}"
  STATUS=$(echo "$STATE" | jq -r --arg s "$STEP" '.step_status[$s] // "pending"')
  if [[ "$STATUS" == "completed" ]] || [[ "$STATUS" == "skipped" ]]; then
    COMPLETED_COUNT=$((COMPLETED_COUNT + 1))
  elif [[ -z "$NEXT_STEP" ]]; then
    NEXT_STEP="$STEP"
    NEXT_STEP_INDEX=$i
  fi
done

# -------------------------------------------------------------------
# 8. All steps complete → allow stop (pipeline done)
# -------------------------------------------------------------------
if [[ -z "$NEXT_STEP" ]]; then
  exit 0
fi

# -------------------------------------------------------------------
# 9. Check transcript for failure/completion signals → allow stop
# -------------------------------------------------------------------
TRANSCRIPT_PATH=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // ""')

if [[ -n "$TRANSCRIPT_PATH" ]] && [[ -f "$TRANSCRIPT_PATH" ]]; then
  # Look for STEP FAILED or PIPELINE COMPLETE in the last assistant message
  LAST_ASSISTANT=$(grep '"role":"assistant"' "$TRANSCRIPT_PATH" | tail -1 || echo "")
  if [[ -n "$LAST_ASSISTANT" ]]; then
    LAST_TEXT=$(echo "$LAST_ASSISTANT" | jq -r '
      .message.content |
      map(select(.type == "text")) |
      map(.text) |
      join("\n")
    ' 2>/dev/null || echo "")

    if echo "$LAST_TEXT" | grep -q "STEP FAILED"; then
      exit 0
    fi
    if echo "$LAST_TEXT" | grep -q "PIPELINE COMPLETE"; then
      exit 0
    fi
  fi
fi

# -------------------------------------------------------------------
# 10. If current step is still in_progress (not yet completed) → allow stop
#     This prevents infinite loops when a step is ambiguous/stuck.
# -------------------------------------------------------------------
CURRENT_STEP=$(echo "$STATE" | jq -r '.current_step // ""')
CURRENT_STATUS=$(echo "$STATE" | jq -r --arg s "$CURRENT_STEP" '.step_status[$s] // "pending"')

if [[ "$CURRENT_STATUS" == "in_progress" ]]; then
  exit 0
fi

# -------------------------------------------------------------------
# 11. We have a completed current step and a next step → block stop
# -------------------------------------------------------------------
STEP_NUMBER=$((COMPLETED_COUNT + 1))

# Add team indicator for team steps
STEP_LABEL="$NEXT_STEP"
if [[ "$TEAMS_ENABLED" == "true" ]] && { [[ "$NEXT_STEP" == "plan-review" ]] || [[ "$NEXT_STEP" == "implement" ]]; }; then
  STEP_LABEL="${NEXT_STEP} ⚡"
fi

jq -n \
  --arg reason "/speckit-orchestrator --execute" \
  --arg msg "SpecKit Pipeline [${STEP_NUMBER}/${TOTAL_STEPS}] | Feature: ${FEATURE} | Next: ${STEP_LABEL}" \
  '{
    "decision": "block",
    "reason": $reason,
    "systemMessage": $msg
  }'

exit 0
