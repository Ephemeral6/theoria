#!/usr/bin/env bash
# monitor's completion gate. The rig that checks everyone else's gate had none
# until S13; `gates.py` reports this directory's state alongside every other, so
# the enforcer is in its own table.
#
#   bash monitor/verify.sh
#
# Exit 0 = green. The gate writes into a mkdtemp and leaves the workspace clean.
#
# S20: a gate nobody has made fail on purpose is decorative, so every gate names
# the test that manufactures its red. These build the failing world deliberately
# -- a heartbeat from the future, a probe that cannot report anything but the
# same verdict, a session that never started -- and require the red.
# negative-sample: monitor/tests/test_probes_injection.py
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$HERE/verify.py" "$@"
