#!/usr/bin/env bash
# The arm's completion gate. DESIGN.md §12 names this file, so this is the name
# it has; the assertions live in `verify.py` because they are arithmetic over
# JSON artefacts and shell is a poor place to do arithmetic over JSON.
#
#   bash ablation-arm/verify.sh
#
# Exit 0 = green. Exit 1 = a stage failed or an assertion this item is entitled
# to make came back false. Predictions that need a second arm are printed under
# their own heading and can never turn this red -- see verify.py's docstring for
# why that split is the honest one.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$HERE/verify.py" "$@"
