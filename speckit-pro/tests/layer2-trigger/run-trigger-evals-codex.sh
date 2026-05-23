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
# This wraps run_codex_evals.py, which stages the codex-skill into an
# isolated workspace with a marker injected, runs each fixture query via
# the codex CLI in headless mode, and scores trigger correctness by
# searching stdout for the marker.
#
# Per-run cost: ~5k–50k tokens depending on reasoning effort. Default
# reasoning is "minimal" to keep cost down; raise to "medium" or "high"
# for closer fidelity to interactive sessions.
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
exec python3 "$SCRIPT_DIR/run_codex_evals.py" "$@"
