"""V23: can `lp_potential` walk the class (ii) path?

Five probes, all offline, no network, no API:

  A  what `solve()` actually reads off `graph`, established by deletion
  B  cost of materialising a peg1d graph as a function of n_pos (MEASURED)
  C  `solve()` on a geometry-only graph at large n_pos -- is the LP itself
     the bottleneck, or is the graph? (MEASURED)
  D  can an A2 comb transition be written as an `lp_potential` Move at all?
     (both sides enumerated: lp's over all role assignments, A2's over the
     reachable transitions of small levels chosen to cover every branch of
     `Level.step`)
  E  the smallest honest end-to-end: a comb level encoded as a state graph,
     handed to `solve()`.

**Not** "all under a second each" -- that line stood here while B, C and E were
measuring exactly the cost of not being.  A and D are sub-second; B, C and E are
the measurements, and their own cost is recorded next to their results
(`B_materialisation[].enumerate_s`, `C_lp_only[].solve_s`,
`E_comb[].build_s` / `.solve_s`).  E's last rung dominates the run: it builds a
multi-million-state graph, which takes tens of seconds on its own.  Read those
fields rather than this docstring -- they are measured, this sentence is not.

Those timing fields also make the artefact **not byte-reproducible**: rerunning
reproduces every structural number but not the wall-clock ones.  Nothing else in
the JSON varies between runs.

Run:  python exam/runs/20260730T021500Z-V23-large-space/probe_lp_interface.py
"""

import json
import os
import sys
import time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for path in (REPO, os.path.join(REPO, "engine-rig")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engines.lp_potential import potential as lp          # noqa: E402
from interop import peg1d                                  # noqa: E402
from exam.papers import verdict as V                       # noqa: E402
from exam.grading import rubrics_verdict as RV             # noqa: E402

OUT = {}

#: Every branch `rubrics_verdict.Level.step` can take.  The A2 measurement below
#: refuses to report unless the levels it enumerated between them exercised all
#: six: a coefficient sum measured over three branches of six is a measurement
#: of something narrower than "an A2 transition", and would be recorded as
#: though it were the whole thing.
STEP_BRANCHES = ("wall_or_edge", "button", "door_closed", "door_open",
                 "portal", "floor")

#: Hard cap on the A2 enumeration below.  `rubrics_verdict` already fixes a
#: number for "past here, do not enumerate a state space", so reuse it rather
#: than inventing a second one.  Hitting it RAISES; it never truncates.  The
#: previous version of this probe had no bound at all and could not terminate.
A2_STATE_BOUND = RV.MAX_ENUMERATION


def _branch_of(level, cart, pressed, action):
    """Which branch of `Level.step` this command takes -- label cross-checked.

    Reading the branch off the level's own fields is a second implementation of
    `step`'s case order, and second implementations drift: `rubrics_verdict`
    documents `_neighbours` drifting from `step` in exactly this way, and the
    drift produced accepted-but-false certificates.  So the label is only used
    after the outcome it predicts has been checked against what `step` actually
    returned, and a disagreement raises rather than being recorded.
    """
    dr, dc = RV.DELTA[action]
    target = (cart[0] + dr, cart[1] + dc)
    nxt, npressed = level.step(cart, pressed, action)
    if not level.in_bounds(target) or level.is_wall(target):
        branch, expect = "wall_or_edge", (cart, pressed)
    elif level.button is not None and target == level.button:
        branch, expect = "button", (cart, True)
    elif level.door is not None and target == level.door:
        branch, expect = (("door_open", (target, pressed)) if pressed
                          else ("door_closed", (cart, pressed)))
    elif level.portal is not None and target == level.portal:
        branch, expect = "portal", (level.portal_dest or target, pressed)
    else:
        branch, expect = "floor", (target, pressed)
    if (nxt, npressed) != expect:
        raise AssertionError(
            "branch label %r for %s from %s (pressed=%s) predicts %s but "
            "Level.step returned %s -- the label is a second implementation "
            "and it has drifted" % (branch, action, cart, pressed, expect,
                                    (nxt, npressed)))
    return branch, nxt, npressed


def _enumerate_a2_level(doc):
    """Every reachable transition of one A2 level, with its coefficient sum.

    The occupancy vector has one coordinate per cell for the cart (one-hot), one
    per switch for its latch bit, and one for `pressed`.  A transition's
    coefficient sum is therefore (bits that turned on) - (bits that turned off),
    and both halves are read off the states rather than argued.
    """
    level = RV.Level(doc)

    def latch(cart, mask):
        if cart in level.switch_index:
            return mask | (1 << level.switch_index[cart])
        return mask

    start = (level.start, False, latch(level.start, 0))
    seen = {start}
    queue = [start]
    sums = set()
    sum_by_kind = {}
    count_by_kind = {}
    branches = {}
    transitions = 0
    while queue:
        cart, pressed, mask = queue.pop()
        for command in level.commands():
            branch, nxt, npressed = _branch_of(
                level, cart, pressed, level.world_action(command))
            nmask = latch(nxt, mask)
            transitions += 1
            branches[branch] = branches.get(branch, 0) + 1

            moved = nxt != cart
            latched_now = nmask != mask
            pressed_now = bool(npressed) and not pressed
            # No coordinate ever falls except the cart's own -1, and that is
            # repaid by the +1 at the cell it enters.  Both halves are checked
            # here rather than assumed: `mask & ~nmask` is any latch bit that
            # went off, and `pressed and not npressed` is the button going off.
            if mask & ~nmask or (pressed and not npressed):
                raise AssertionError(
                    "a monotone bit turned OFF in %s: %s -> %s"
                    % (doc["level_id"], (cart, pressed, mask),
                       (nxt, npressed, nmask)))
            if latched_now and pressed_now:
                raise AssertionError(
                    "a latch bit and the button turned on in the same "
                    "transition of %s; the two are supposed to be mutually "
                    "exclusive because the button branch leaves the cart "
                    "where it was" % doc["level_id"])
            bits = bin(nmask ^ mask).count("1") + (1 if pressed_now else 0)
            sums.add(bits)

            if latched_now:
                kind = "latching move"
            elif pressed_now:
                kind = "button press"
            elif moved:
                kind = "plain move"
            else:
                kind = "blocked"
            # Every transition of a kind must agree, or "the" sum for that kind
            # is not a well-defined number and this probe is measuring an average.
            if kind in sum_by_kind and sum_by_kind[kind] != bits:
                raise AssertionError(
                    "A2 %s transitions disagree on their coefficient sum: "
                    "%d and %d" % (kind, sum_by_kind[kind], bits))
            sum_by_kind[kind] = bits
            count_by_kind[kind] = count_by_kind.get(kind, 0) + 1

            state = (nxt, npressed, nmask)
            if state not in seen and nxt not in level.lost_cells:
                seen.add(state)
                if len(seen) > A2_STATE_BOUND:
                    raise AssertionError(
                        "%s exceeded the %d-state enumeration bound; this "
                        "probe refuses to report a partial sweep as a "
                        "measurement" % (doc["level_id"], A2_STATE_BOUND))
                queue.append(state)
    # `coefficient_sum_by_kind` and `transitions_by_kind` are two different
    # things and were one field until now: the old name was `by_kind` and it
    # held the sums, so `a2_plain_move: 0` and `a2_blocked: 0` reached the
    # record reading like counts -- i.e. like "no plain move and no blocked
    # transition was ever seen", which would empty the measurement out, when
    # what they say is that those transitions' coefficient sum *is* 0, which is
    # the result. The counts are now published beside the sums instead of being
    # unobtainable, and `transitions_by_branch` keeps the per-branch tallies
    # this function was already computing and then discarding with a `sorted()`
    # over the keys -- "all six branches covered" says nothing about a branch
    # covered by four transitions in one level, and that is exactly what a
    # reader needs in order to distrust it.
    return {"level_id": doc["level_id"], "latch_bits": len(level.switch_index),
            "states": len(seen), "transitions": transitions,
            "sums": sorted(sums),
            "coefficient_sum_by_kind": dict(sum_by_kind),
            "transitions_by_kind": dict(count_by_kind),
            "transitions_by_branch": dict(branches),
            "branches": sorted(branches)}


def _measure_a2_coefficient_sums():
    """Enumerate A2's own transitions and sum each occupancy-vector delta.

    Why *small* levels, and why they suffice -- stated so it can be attacked:

    * The cart's coordinate is one-hot, so a move contributes -1 at the cell it
      leaves and +1 at the cell it enters: 0.  A blocked command contributes
      nothing.  Neither figure depends on how many switches the board has.
    * Latch bits and `pressed` are monotone -- `|=` and `True`, never cleared --
      so no coordinate ever goes down except that cart -1, which is repaid in
      the same transition.  Checked in the loop above, not assumed.
    * At most one of them can turn on per transition: a latch bit turns on only
      for the cell the cart *lands* on, and the button branch leaves the cart
      where it was, so the two are mutually exclusive.  Also checked, not
      assumed.

    So a transition's coefficient sum is 0 or +1 whatever the board's width;
    widening the comb adds coordinates and states but no new *kind* of
    transition, and the kind is what fixes the sum.  The sweep over corridor
    lengths 2..5 below is the empirical half of that claim: the latch bits go
    4 -> 6 -> 8 -> 10, identical sums and identical kinds.  (This read "4x
    the latch bits" until round six measured it: 4 to 10 is 2.5x, and the
    only 4x in sight is the *shipped* board's 40, which is the thing that
    was never enumerated.  A ratio nobody recomputed, next to the number it
    was a ratio of.)  `atrium` is A2's own 9x9 board and is
    here for coverage -- it is the only level in the family carrying a button, a
    door and a teleport, so without it three of `Level.step`'s six branches
    would go unmeasured.  The union of branches is asserted against
    `STEP_BRANCHES`, so this stays true if the level set is edited.

    What this does **not** do is enumerate the shipped `comb_open(..., 20, ...)`.
    That board carries 40 latch bits and ~4.4e13 states; enumerating it is
    precisely the thing this whole ticket exists to say cannot be done, and the
    previous version of this function tried to, with an unbounded `while queue`,
    and could not terminate (aborted at 45 s with seen=7547299, frontier=191).
    `a2_shipped_level_enumerated` is False in the record for that reason, and
    the general claim rests on the three bullets above, which are argument
    checked by assertion -- not on a sweep of the shipped size.
    """
    docs = [V.comb_open("lp-iface-comb%d" % n, n, 1, n) for n in (2, 3, 4, 5)]
    docs.append(V.a2_echo())
    # `updraft`, `cistern`, `quarry` and `meander` are here because the first
    # run that published per-branch counts showed what the branch *set* had been
    # hiding: `portal` was taken by exactly 1 transition out of 51164 and the
    # `button press` kind by exactly 1, with `button` / `door_open` /
    # `door_closed` at 2 each -- all of them inside `a2_echo` alone.  The
    # agreement check below ("every transition of a kind must agree, or the sum
    # is not well defined") cannot fire on a sample of one: there is nothing for
    # the single transition to disagree with, so for `button press` the check
    # was decorative.  Coverage asserted as a set of branch names looked
    # complete while resting on single observations.
    docs.extend([V.updraft(), V.cistern(), V.quarry(), V.meander()])

    per_level = [_enumerate_a2_level(doc) for doc in docs]

    sums = set()
    sum_by_kind = {}
    count_by_kind = {}
    count_by_branch = {}
    branches = set()
    transitions = 0
    states = 0
    for row in per_level:
        sums.update(row["sums"])
        branches.update(row["branches"])
        transitions += row["transitions"]
        states += row["states"]
        for kind, value in row["coefficient_sum_by_kind"].items():
            if kind in sum_by_kind and sum_by_kind[kind] != value:
                raise AssertionError(
                    "levels disagree on the coefficient sum of an A2 %s: "
                    "%d and %d" % (kind, sum_by_kind[kind], value))
            sum_by_kind[kind] = value
        for kind, n in row["transitions_by_kind"].items():
            count_by_kind[kind] = count_by_kind.get(kind, 0) + n
        for branch, n in row["transitions_by_branch"].items():
            count_by_branch[branch] = count_by_branch.get(branch, 0) + n

    # Coverage asserted as a set of names, with the sample sizes discarded, is
    # how `portal x1` and `button press x1` passed for complete.  Adding
    # `updraft`, `cistern`, `quarry` and `meander` did not move them: those four
    # levels raised `plain move` 27923 -> 28337 and `blocked` 11864 -> 12166
    # across four fresh geometries, and left `button press` at 1, `portal` at 1
    # and each door branch at 2, because **`atrium` is the only level in
    # `verdict.py` that has a button, a door or a portal at all**.  So this is
    # not a gap that more of the shipped levels can close, and the record says
    # so instead of implying otherwise.  THIN is 3 because the agreement check
    # above needs two observations to be capable of firing and a third to be
    # worth calling a sample.
    THIN = 3
    thin = {"threshold": THIN,
            "kinds": {k: n for k, n in sorted(count_by_kind.items()) if n < THIN},
            "branches": {b: n for b, n in sorted(count_by_branch.items())
                         if n < THIN},
            "note": ("Every kind and branch listed here was observed fewer than "
                     "%d times, all of them inside `atrium`, the only shipped "
                     "level with a button, a door or a portal. For a kind seen "
                     "once the cross-transition agreement assertion cannot fire "
                     "-- there is nothing for the single observation to "
                     "disagree with -- so its coefficient sum is a single "
                     "measurement, not a confirmed constant. The general claim "
                     "rests on the monotonicity argument, which these "
                     "transitions are consistent with and do not "
                     "independently establish." % THIN)}

    missing = [b for b in STEP_BRANCHES if b not in branches]
    if missing:
        raise AssertionError(
            "the enumerated levels never took these branches of Level.step: "
            "%s -- the measurement would be narrower than the claim it is "
            "about to support" % (missing,))
    extra = sorted(branches.difference(STEP_BRANCHES))
    if extra:
        raise AssertionError(
            "Level.step took a branch this probe does not know about: %s"
            % (extra,))

    return {"sums": sorted(sums), "coefficient_sum_by_kind": sum_by_kind,
            "transitions_by_kind": count_by_kind,
            "transitions_by_branch": count_by_branch,
            "thin_coverage": thin,
            "branches": sorted(branches), "transitions": transitions,
            "states": states, "per_level": per_level,
            "level_ids": [row["level_id"] for row in per_level]}

def banner(text):
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72)


# ------------------------------------------------------------------ probe A
def probe_a():
    banner("A. which keys of `graph` does solve() read?")
    full = peg1d.build_graph(6, "111111", goal_states=["100000"])
    keys = sorted(full)
    print("build_graph emits: %s" % keys)

    survived = []
    for key in keys:
        trimmed = {k: v for k, v in full.items() if k != key}
        try:
            lp.solve(trimmed, "111111", goal_states=["100000"])
        except KeyError as exc:
            survived.append(key)
            print("  removing %-18s -> KeyError(%s)  REQUIRED" % (key, exc))
        else:
            print("  removing %-18s -> ok" % key)
    OUT["A_required_keys"] = survived

    # and the granularity: how many LP rows come from how many edges?
    moves = lp.moves_from_graph(full)
    print("\n  n_pos=6: %d edges in the graph -> %d distinct move geometries"
          % (len(full["edges"]), len(moves)))
    print("  LP shape: 2*n = %d variables, %d move rows + %d goal rows + %d box rows"
          % (2 * 6, len(moves), 1, 2 * 6))
    OUT["A_granularity"] = {
        "n_pos": 6, "edges": len(full["edges"]), "distinct_geometries": len(moves),
        "lp_variables": 12, "lp_rows": len(moves) + 1 + 12,
    }


# ------------------------------------------------------------------ probe B
def probe_b():
    banner("B. cost of materialising the input, vs n_pos (MEASURED)")
    rows = []
    for n in range(6, 21):
        initial = "1" * n
        goals = ["1" + "0" * (n - 1)]
        t0 = time.perf_counter()
        states = peg1d.all_states(n)
        insts = peg1d.move_instances(n)
        edges = 0
        for state in states:
            for move in insts:
                if peg1d.legal(state, move):
                    edges += 1
        t1 = time.perf_counter()
        rows.append({"n_pos": n, "states": len(states), "edges": edges,
                     "geometries": len(insts), "enumerate_s": round(t1 - t0, 4)})
        print("  n=%2d  states=%9d  edges=%10d  geometries=%3d  enumerate=%7.3fs"
              % (n, len(states), edges, len(insts), t1 - t0))
        if t1 - t0 > 20:
            print("  (stopping: next n doubles this)")
            break
    OUT["B_materialisation"] = rows


# ------------------------------------------------------------------ probe C
def probe_c():
    banner("C. solve() on a geometry-only graph -- the LP alone (MEASURED)")
    # `moves_from_graph` de-duplicates, so a graph carrying one edge per
    # geometry produces exactly the LP a fully materialised graph produces.
    rows = []
    for n in (6, 12, 25, 50, 100, 250, 500, 1000):
        insts = peg1d.move_instances(n)
        graph = {
            "n_pos": n,
            "goal_states": ["1" + "0" * (n - 1)],
            "edges": [{"positions": [m["src"], m["over"], m["dst"]],
                       "src_state": "", "dst_state": "", "move": ""}
                      for m in insts],
        }
        initial = "1" * n
        t0 = time.perf_counter()
        outcome = lp.solve(graph, initial, goal_states=["1" + "0" * (n - 1)])
        t1 = time.perf_counter()
        rows.append({"n_pos": n, "geometries": len(insts),
                     "status": outcome.status, "solve_s": round(t1 - t0, 4)})
        print("  n_pos=%4d  geometries=%4d  status=%-16s  %6.3fs"
              % (n, len(insts), outcome.status, t1 - t0))
    OUT["C_lp_only"] = rows

    # sanity: does the geometry-only graph agree with the materialised one?
    full = peg1d.build_graph(8, "1" * 8, goal_states=["1" + "0" * 7])
    thin = {"n_pos": 8, "goal_states": ["1" + "0" * 7],
            "edges": [{"positions": [m["src"], m["over"], m["dst"]]}
                      for m in peg1d.move_instances(8)]}
    a = lp.solve(full, "1" * 8, goal_states=["1" + "0" * 7])
    b = lp.solve(thin, "1" * 8, goal_states=["1" + "0" * 7])
    print("\n  materialised graph -> %s ; geometry-only graph -> %s ; agree=%s"
          % (a.status, b.status, a.status == b.status))
    OUT["C_agreement"] = {"materialised": a.status, "geometry_only": b.status,
                          "agree": a.status == b.status}


# ------------------------------------------------------------------ probe D
def probe_d():
    banner("D. can an A2 cart move be written as an lp_potential Move?")
    # lp_potential builds one LP row per Move as:
    #     row[dst] += 1 ; row[src] -= 1 ; row[over] -= 1
    # so the coefficient vector of every expressible transition sums to -1,
    # whatever the three indices are (including collisions).
    sums = set()
    n = 5
    assignments = 0
    for src in range(n):
        for over in range(n):
            for dst in range(n):
                row = [0.0] * n
                row[dst] += 1.0
                row[src] -= 1.0
                row[over] -= 1.0
                sums.add(sum(row))
                assignments += 1
    print("  coefficient-sum over all %d role assignments (n=%d): %s"
          % (assignments, n, sorted(sums)))
    OUT["D_coefficient_sums"] = sorted(sums)
    # The loop's width and its trip count, recorded rather than left for a reader
    # to recover from the source.  Round four withdrew the exhaustiveness claim
    # because "the figure 5 appears nowhere"; it was in the generator all along,
    # and round five withdrew the withdrawal.  Neither round would have had to
    # guess if the artefact had carried the two numbers, so now it does.
    OUT["D_role_assignments"] = {"n": n, "assignments": assignments}

    # The A2 side.  These numbers were once literals -- `% 0` and `% 1` written
    # into a print in the format of a measurement, and copied into `D_verdict` as
    # though derived.  The replacement enumerated a 20-wide comb and could not
    # terminate, so the artefact kept the literals' values from a run that never
    # happened.  Now: small levels, an explicit bound that raises, and every
    # number below comes back from the enumeration.
    a2 = _measure_a2_coefficient_sums()
    for row in a2["per_level"]:
        print("  %-16s latch bits=%2d  states=%6d  transitions=%7d  sums=%s"
              % (row["level_id"], row["latch_bits"], row["states"],
                 row["transitions"], row["sums"]))
    for label, value in sorted(a2["coefficient_sum_by_kind"].items()):
        print("  A2 %-18s: coefficient sum = %+d  (over %d transitions)"
              % (label, value, a2["transitions_by_kind"][label]))
    # Printed with counts, because "covered" is the claim and the count is the
    # only thing that says how thinly.  `portal` and `door_open` come from one
    # level between them, and a reader is entitled to see that here rather than
    # having to reconstruct it from `per_level`.
    print("  Level.step branches covered: %s"
          % ", ".join("%s x%d" % (b, a2["transitions_by_branch"][b])
                      for b in a2["branches"]))
    thin = a2["thin_coverage"]
    if thin["kinds"] or thin["branches"]:
        print("  THIN (<%d observations, so the agreement check is weak or "
              "vacuous): kinds=%s branches=%s"
              % (thin["threshold"], thin["kinds"] or "{}",
                 thin["branches"] or "{}"))
    print("  lp_potential Move    : coefficient sum = -1, always")
    print("  => no assignment of (src, over, dst) expresses an A2 transition.")
    OUT["D_verdict"] = {
        "lp_move_coefficient_sum": -1,
        # Named for their unit.  `a2_plain_move: 0` stood here and read as a
        # count of plain moves -- 0 of them -- when it was that kind's
        # coefficient sum, which is the finding.  Sums and counts are now two
        # fields with the word in the key.
        "a2_coefficient_sum_by_kind": a2["coefficient_sum_by_kind"],
        "a2_transitions_by_kind": a2["transitions_by_kind"],
        "a2_transitions_by_branch": a2["transitions_by_branch"],
        "a2_thin_coverage": a2["thin_coverage"],
        "a2_coefficient_sums_measured": a2["sums"],
        "a2_transitions_enumerated": a2["transitions"],
        "a2_states_enumerated": a2["states"],
        "a2_enumeration_bound": A2_STATE_BOUND,
        "a2_step_branches_covered": a2["branches"],
        "a2_levels": a2["per_level"],
        "a2_level_ids": a2["level_ids"],
        "a2_shipped_level_enumerated": False,
        "expressible": False,
        "how": ("every reachable (cart, pressed, latched) transition of %s was "
                "enumerated under a %d-state bound that raises rather than "
                "truncating, and each transition's occupancy-vector delta was "
                "summed. The cart's one-hot contributes 0 whether it moves or "
                "is blocked; latch bits and `pressed` are monotone and at most "
                "one turns on per transition (both checked in the loop, not "
                "assumed), so the sum is the number of bits that turned on. "
                "Measured sums %s, none of them -1, against lp_potential's "
                "invariant -1. The shipped comb_open(.., 20, ..) was NOT "
                "enumerated -- 40 latch bits, ~4.4e13 states, which is the "
                "impossibility this ticket is about; the step from these "
                "levels to every size is the monotonicity argument above, "
                "supported by the corridor-length sweep (latch bits 4 to 10, "
                "identical sums and kinds), not by a sweep of the shipped size."
                % (", ".join("`%s`" % i for i in a2["level_ids"]),
                   A2_STATE_BOUND, a2["sums"])),
    }


# ---------------------------------------------------------- comb encoding
def comb_level(corridor_len, start_col, goal_col):
    """The shipped comb_open geometry, small enough to enumerate."""
    width = corridor_len + 2
    border = "#" * width
    upper = "#" + "s" * corridor_len + "#"
    corridor = list("#" + "." * corridor_len + "#")
    corridor[start_col] = "S"
    corridor[goal_col] = "G"
    rows = [border, upper, "".join(corridor), upper, border]
    switches = ([(1, c) for c in range(1, corridor_len + 1)]
                + [(3, c) for c in range(1, corridor_len + 1)])
    return {"rows": rows, "start": (2, start_col), "goal": (2, goal_col),
            "switches": switches, "width": width, "height": 5}


DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def comb_state_graph(level, forbidden=()):
    """Full (cart, latch-mask) graph of a comb level, in lp_potential's shape.

    Bit layout: cells 0..C-1 are `cart is here`, cells C..C+S-1 are
    `switch j is latched`.  This is the most faithful bitstring encoding
    available -- potential = sum of w over occupied cells, which is what
    `Certificate.potential` computes.
    """
    rows, height, width = level["rows"], level["height"], level["width"]
    cells = [(r, c) for r in range(height) for c in range(width)
             if rows[r][c] != "#"]
    index = {cell: i for i, cell in enumerate(cells)}
    switches = list(level["switches"])
    sw_index = {c: i for i, c in enumerate(switches)}
    C, S = len(cells), len(switches)
    n_pos = C + S
    actions = [a for a in ("UP", "DOWN", "LEFT", "RIGHT") if a not in forbidden]

    def encode(cart, mask):
        bits = ["0"] * n_pos
        bits[index[cart]] = "1"
        for j in range(S):
            if mask >> j & 1:
                bits[C + j] = "1"
        return "".join(bits)

    def step(cart, action):
        dr, dc = DELTA[action]
        nxt = (cart[0] + dr, cart[1] + dc)
        if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
            return cart
        if rows[nxt[0]][nxt[1]] == "#":
            return cart
        return nxt

    start_mask = 1 << sw_index[level["start"]] if level["start"] in sw_index else 0
    start = (level["start"], start_mask)
    seen = {start}
    stack = [start]
    edges = []
    while stack:
        cart, mask = stack.pop()
        src_text = encode(cart, mask)
        for action in actions:
            nxt = step(cart, action)
            nmask = mask
            if nxt in sw_index:
                nmask |= 1 << sw_index[nxt]
            node = (nxt, nmask)
            if node == (cart, mask):
                continue
            edges.append({"src_state": src_text, "move": action,
                          "positions": [index[cart], index[cart], index[nxt]],
                          "dst_state": encode(*node)})
            if node not in seen:
                seen.add(node)
                stack.append(node)
    full_mask = (1 << S) - 1
    goals = [encode(level["goal"], full_mask)]
    return {
        "n_pos": n_pos, "cells": C, "switches": S,
        "states": sorted(encode(c, m) for c, m in seen),
        "goal_states": goals, "goal": goals[0],
        "edges": edges,
        "initial": encode(*start),
    }


# ------------------------------------------------------------------ probe E
def probe_e():
    banner("E. a real comb level, materialised, handed to solve()")
    rows = []
    for corridor_len in (2, 3, 4, 5, 6, 7, 8, 9, 10):
        level = comb_level(corridor_len, 1, corridor_len)
        t0 = time.perf_counter()
        graph = comb_state_graph(level, forbidden=("LEFT",))
        t1 = time.perf_counter()
        entry = {"corridor_len": corridor_len, "n_pos": graph["n_pos"],
                 "reachable_states": len(graph["states"]),
                 "edges": len(graph["edges"]),
                 "build_s": round(t1 - t0, 4)}
        t2 = time.perf_counter()
        try:
            outcome = lp.solve(graph, graph["initial"])
            entry["status"] = outcome.status
            entry["certificate"] = (outcome.certificate.as_json()
                                    if outcome.certificate else None)
        except Exception as exc:                                  # noqa: BLE001
            entry["status"] = "%s: %s" % (type(exc).__name__, exc)
        entry["solve_s"] = round(time.perf_counter() - t2, 4)
        rows.append(entry)
        print("  len=%2d  n_pos=%3d  states=%8d  edges=%9d  build=%6.3fs  "
              "solve=%6.3fs  -> %s"
              % (corridor_len, graph["n_pos"], len(graph["states"]),
                 len(graph["edges"]), entry["build_s"], entry["solve_s"],
                 entry["status"]))
        if t1 - t0 > 15:
            print("  (stopping: next corridor cell doubles the mask space)")
            break
    OUT["E_comb"] = rows

    # What does the LP claim, and is the claim about the right system?
    last = rows[-1]
    if last.get("certificate"):
        print("\n  a certificate WAS returned; check it against the real system:")
    else:
        print("\n  no certificate at any size tried.")

    # The soundness question: lp_potential's re-check only looks at its own
    # Move list, whose delta is w[dst]-w[src]-w[over].  Compare that against the
    # true potential delta of each edge.
    level = comb_level(4, 1, 4)
    graph = comb_state_graph(level, forbidden=("LEFT",))
    moves = lp.moves_from_graph(graph)
    print("  n_pos=%d, %d edges -> %d distinct (src,over,dst) triples"
          % (graph["n_pos"], len(graph["edges"]), len(moves)))
    weights = [Fraction(i + 1) for i in range(graph["n_pos"])]
    mismatched = 0
    for edge in graph["edges"]:
        src, over, dst = edge["positions"]
        modelled = weights[dst] - weights[src] - weights[over]
        occ_s = sum((weights[i] for i, ch in enumerate(edge["src_state"]) if ch == "1"),
                    Fraction(0))
        occ_d = sum((weights[i] for i, ch in enumerate(edge["dst_state"]) if ch == "1"),
                    Fraction(0))
        if modelled != occ_d - occ_s:
            mismatched += 1
    print("  edges whose lp_potential-modelled delta != the true potential "
          "delta: %d of %d" % (mismatched, len(graph["edges"])))
    OUT["E_delta_mismatch"] = {"n_pos": graph["n_pos"],
                               "edges": len(graph["edges"]),
                               "mismatched": mismatched}


if __name__ == "__main__":
    probe_a()
    probe_b()
    probe_c()
    probe_d()
    probe_e()
    path = os.path.join(HERE, "probe_lp_interface.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(OUT, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % path)
