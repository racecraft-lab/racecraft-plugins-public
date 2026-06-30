#!/usr/bin/env bash
# test-speckit-pro-runner.sh — Unit and contract fixtures for the XPLAT runner.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/test-speckit-pro-runner.py"
