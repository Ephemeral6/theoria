"""fleetkit — the repository-agnostic core of a self-assembling agent fleet.

Extracted from Theoria's `monitor/`, where it ran a 12-agent fleet for a day.
What it provides is coordination, not intelligence: a work board with atomic
claiming and territory exclusivity, a message bus with acknowledgement and
interruption, and the state layout both sit on.

    python -m fleetkit init --prefix MyFleet-   # write fleet.json
    python -m fleetkit board list
    python -m fleetkit bus say W-1 "..."

`FLEET_HOME` selects the state tree; without it, the package directory is used.
Read `KNOWN_TRAPS.md` before deploying on Windows -- every entry in it cost a
real outage.
"""

__all__ = ["config", "board", "bus"]
#: Bumped by S42: `python -m fleetkit` now exists (it never did), `cmd_sweep`
#: reads task_prefix from fleet.json instead of an unassigned `_PREFIX = ""`,
#: and lane *ownership* -- which no data source could supply -- is gone.
__version__ = "0.2.0"
