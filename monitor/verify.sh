#!/usr/bin/env bash
# monitor's completion gate. The rig that checks everyone else's gate had none
# until S13; `gates.py` reports this directory's state alongside every other, so
# the enforcer is in its own table.
#
#   bash monitor/verify.sh
#
# Exit 0 = green. The gate writes into a mkdtemp and leaves the workspace clean.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$HERE/verify.py" "$@"
