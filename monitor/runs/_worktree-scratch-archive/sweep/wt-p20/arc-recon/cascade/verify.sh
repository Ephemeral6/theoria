#!/usr/bin/env bash
# P-20 stop-hook. Exit 0 only if the run's books balance.
#
#   ./cascade/verify.sh                       # newest run under cascade/runs/
#   ./cascade/verify.sh runs/<UTC>-p20        # a named one
#
# Run from arc-recon/. The assertions live in cascade/verify.py; this wrapper
# picks the run directory and refuses to report success on an empty one -- a
# check that passes when there is nothing to check is the INC-003 shape.
set -euo pipefail

cd "$(dirname "$0")/.."

RUN_DIR="${1:-}"
if [ -z "$RUN_DIR" ]; then
  RUN_DIR="$(ls -1d cascade/runs/*-p20 2>/dev/null | sort | tail -1 || true)"
fi

if [ -z "$RUN_DIR" ] || [ ! -d "$RUN_DIR" ]; then
  echo "verify: no run directory found (looked for cascade/runs/*-p20)" >&2
  exit 1
fi

if ! ls "$RUN_DIR"/steps.*.jsonl >/dev/null 2>&1; then
  echo "verify: $RUN_DIR holds no steps.*.jsonl -- nothing to verify" >&2
  exit 1
fi

echo "verify: $RUN_DIR"
python -m cascade.verify --run-dir "$RUN_DIR"
