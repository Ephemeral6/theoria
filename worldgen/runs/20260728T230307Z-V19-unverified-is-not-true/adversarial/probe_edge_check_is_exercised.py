"""Are the three new `edge_check`s exercised, or do they pass vacuously?

Answers attack line (c)'s worst case: an `edge_check` that runs over thousands
of transitions but on which the monotone quantity never actually *moves* would
be green for a flipped comparison too, and would be verifying nothing under a
new name.

Counts, per world, the transitions on which the quantity each check guards
genuinely changes.  A non-zero count is what makes the direction-flip mutants
(F02 / F07 / F12) discriminating.

Runnable from anywhere:

    python worldgen/runs/*-V19-*/adversarial/probe_edge_check_is_exercised.py

Result at review time (35 worlds):

    latch bit rises:            111    net bit rises:              111
    collected count rises:       94    lock openings:               42
    tile state rises:            43    collapsed-tile transitions: 995
"""

import os
import sys

# Four up from `adversarial/` is the checkout root, whatever the cwd is.
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")))

from worldgen.core.world import GridWorld
from worldgen.generate import CATALOGUE
from worldgen import mutate
from worldgen.mechanisms.switch_door import SwitchDoor
from worldgen.mechanisms.count_lock import CountLock
from worldgen.mechanisms.consumable import Consumable, COLLAPSED

specs = list(CATALOGUE) + mutate.mutant_specs()
tot = {"latch_rise": 0, "latch_net_rise": 0, "coll_rise": 0, "lock_opened": 0,
       "tile_rise": 0, "collapsed_exists": 0}
per = {}

for spec in specs:
    w = GridWorld(spec)
    states = list(w.reachable())
    row = {}
    for mech in w.mechanisms:
        mine = w.mine(mech)
        if isinstance(mech, SwitchDoor) and any(
                e.prop("mode", "toggle") == "latch"
                for _i, e in mech._switches(mine)):
            rise = netrise = 0
            for prev, _a, nxt, _r in w.transitions(states):
                b, af = w.view(mech, prev), w.view(mech, nxt)
                for i, e in mech._switches(mine):
                    if e.prop("mode", "toggle") == "latch" and af.get(i) > b.get(i):
                        rise += 1
                for net in {e.prop("net", "a") for _i, e in mech._switches(mine)}:
                    if (not mech._net_on(mine, b, net)) and mech._net_on(mine, af, net):
                        netrise += 1
            row["latch_rise"] = rise
            row["latch_net_rise"] = netrise
            tot["latch_rise"] += rise
            tot["latch_net_rise"] += netrise

        if isinstance(mech, CountLock) and mine:
            rise = opened = 0
            for prev, _a, nxt, _r in w.transitions(states):
                b, af = w.view(mech, prev), w.view(mech, nxt)
                if mech._collected(af) > mech._collected(b):
                    rise += 1
                if set(mech._closed_cells(mine, af)) < set(mech._closed_cells(mine, b)):
                    opened += 1
            row["coll_rise"] = rise
            row["lock_opened"] = opened
            tot["coll_rise"] += rise
            tot["lock_opened"] += opened

        if isinstance(mech, Consumable) and mine:
            rise = col = 0
            for prev, _a, nxt, _r in w.transitions(states):
                b, af = w.view(mech, prev), w.view(mech, nxt)
                if any(af.get(i) > b.get(i) for i in range(len(mine))):
                    rise += 1
                if any(af.get(i) == COLLAPSED for i in range(len(mine))):
                    col += 1
            row["tile_rise"] = rise
            row["collapsed_exists"] = col
            tot["tile_rise"] += rise
            tot["collapsed_exists"] += col
    if row:
        per[spec.world_id] = row

for k, v in sorted(per.items()):
    print("%-22s %s" % (k, v))
print("TOTALS", tot)
