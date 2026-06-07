#!/usr/bin/env bash
# run-trigger-evals-codex.sh — Automated Layer 2 trigger evals for Codex skills.
#
# Usage:
#   run-trigger-evals-codex.sh [skill-name] [--runs N] [--limit N]
#                              [--reasoning EFFORT] [--model MODEL]
#                              [--threshold FLOAT] [--out FILE]
#
#   skill-name: any Codex skill with a matching
#               tests/layer2-trigger/codex-evals/<skill>-trigger.json
#               or shared tests/layer2-trigger/evals/<skill>-trigger.json
#
# Flow:
#   1. Resolve the eval-file and skill-path, print them to stdout so that
#      runner-routing assertions in Layer 4 can verify path resolution
#      even when the codex CLI is unavailable.
#   2. If the codex CLI is on PATH, hand off to run_codex_evals.py for the
#      actual eval execution. That Python script stages the codex-skill
#      into an isolated workspace with a marker injected, runs each
#      fixture query via the codex CLI in headless mode, and scores
#      trigger correctness by searching stdout for the marker.
#   3. If codex is missing (typical on CI), exit 0 after printing the
#      paths. This keeps Layer 4 routing tests green without requiring
#      OpenAI tooling in CI.
#
# Per-run cost (when codex runs): ~5k–50k tokens per query depending on
# reasoning effort. Default reasoning is "minimal" but smoke testing
# showed grill-me needs at least "medium" to consistently match its
# description. Recommended invocation for real runs:
#   --runs 3 --reasoning medium
#
# Examples:
#   # Smoke test: 3 queries, 1 run each (cheap, ~10 invocations)
#   ./run-trigger-evals-codex.sh grill-me --limit 3 --runs 1
#
#   # Full eval with stricter reasoning
#   ./run-trigger-evals-codex.sh speckit-coach --runs 3 --reasoning medium
#
#   # Save detailed JSON results
#   ./run-trigger-evals-codex.sh grill-me --out /tmp/grill-me-codex-eval.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../../speckit-pro" && pwd)"
SKILL="${1:-speckit-coach}"

# Resolve eval file (prefer codex-evals/, fall back to shared evals/)
if [ -f "$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/codex-evals/${SKILL}-trigger.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/codex-evals/${SKILL}-trigger.json"
elif [ -f "$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/evals/${SKILL}-trigger.json" ]; then
  EVAL_FILE="$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/evals/${SKILL}-trigger.json"
else
  echo "ERROR: Eval file not found for: $SKILL" >&2
  echo "Available Codex trigger evals:" >&2
  find "$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/codex-evals" "$PLUGIN_ROOT/../tests/speckit-pro/layer2-trigger/evals" \
    -maxdepth 1 -name '*-trigger.json' 2>/dev/null | sort -u | while read -r f; do
    basename "$f" -trigger.json
  done >&2
  exit 1
fi

SKILL_PATH="$PLUGIN_ROOT/codex-skills/${SKILL}"

if [ ! -d "$SKILL_PATH" ]; then
  echo "ERROR: Codex skill not found: $SKILL_PATH" >&2
  exit 1
fi

# Print resolved paths to stdout so Layer 4 path-resolution assertions
# can verify routing. These exact lines are asserted on.
echo "Eval file: $EVAL_FILE"
echo "Skill path: $SKILL_PATH"

# Real eval execution is opt-in via --run, since each query burns ~5k–50k
# tokens and the full sweep across all skills is multi-million tokens.
# Without --run, the wrapper exits after printing paths — safe for CI,
# Layer 4 routing tests, and quick inspection.
RUN_EVAL=0
for arg in "$@"; do
  [ "$arg" = "--run" ] && RUN_EVAL=1
done

if [ "$RUN_EVAL" -eq 0 ]; then
  echo ""
  echo "Pass --run to invoke the codex CLI and execute the eval." >&2
  echo "Without --run, this script only resolves paths and exits." >&2
  exit 0
fi

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: --run was passed but codex CLI is not on PATH." >&2
  echo "Install codex first: https://developers.openai.com/codex/" >&2
  exit 1
fi

# Strip --run before delegating; run_codex_evals.py does not accept it.
PY_ARGS=()
for arg in "$@"; do
  [ "$arg" = "--run" ] && continue
  PY_ARGS+=("$arg")
done

exec python3 "$SCRIPT_DIR/run_codex_evals.py" "${PY_ARGS[@]}"
