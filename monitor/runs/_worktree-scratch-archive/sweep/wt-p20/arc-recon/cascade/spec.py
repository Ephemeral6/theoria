"""P-20 cascade probe -- the sequences, the budget, and the offline expectations.

Frozen before any action is spent. `probe.py` reads this and nothing else; it
cannot choose an action at runtime, and it cannot lengthen a sequence.

THE QUESTION. `arc-recon/README.md` records that a command response's `frame`
field is a *list*, and that the determinism precheck saw batches of 7 (g50t
ACTION2) and 2 (sk48, every action). So `len(frame) > 1` is not in doubt. What
is in doubt -- and what A0's D-A0-004 ("model step as action -> single frame")
was decided under -- is whether that list is a *cascade*: several genuinely
different world states produced by one command, in which case a single-frame
model throws away intermediate states that a rule miner needs. A batch of 7
identical grids is padding, not a cascade, and would leave D-A0-004 defensible.

The precheck hashed each batch **as a whole**. It therefore cannot tell those two
worlds apart. This probe hashes **every frame individually**, which is the
smallest addition that answers the question it was run for.

BUDGET. 25 executed ACTIONs across the four development-pile games, hard cap 30,
per game <= 7. RESETs are logged and not counted, matching precheck.py and
canary.py. Failed commands execute nothing (the scorecard counts successful
actions only) but are still recorded.

WHY THESE SEQUENCES. Each is a prefix-compatible extension of a sequence the
precheck already ran, so the leading steps double as a cross-session residue and
drift check against hashes derived offline from `data/precheck.json` -- the free
sample P-20 was asked to collect -- and the tail explores actions the precheck
never reached.

SEALED PILE. Every game here is in the development pile and `probe.py` calls
`precheck.assert_playable` on each one regardless.
"""

# game_id -> list of (action_id, data). `data` is None except for click actions.
SEQUENCES = {
    # The known cascade. Steps 0-1 repeat the precheck exactly (ACTION1 is an
    # accepted no-op, ACTION2 returned 7 frames twice); the rest asks whether
    # the 7-frame response is a property of ACTION2, of the state, or of both.
    "g50t-5849a774": [(1, None), (2, None), (2, None), (3, None),
                      (4, None), (5, None), (2, None)],
    # Every precheck action here returned exactly 2 frames. The question is
    # whether the two frames differ from each other.
    "sk48-d8078629": [(1, None), (2, None), (3, None), (4, None),
                      (1, None), (2, None), (3, None)],
    # The control: 9/9 single-frame in the precheck. If a cascade appears here
    # it is state-dependent rather than game-dependent.
    "ar25-0c556536": [(1, None), (2, None), (3, None), (4, None),
                      (5, None), (1, None), (2, None)],
    # The click family's only development-pile representative, and the one whose
    # nominal action is broken: ACTION6 returned 500 on every precheck attempt,
    # with and without {x,y}. Two attempts at it (so the 500 is re-observed
    # rather than assumed) and two accepted no-ops. Deliberately short: spending
    # seven actions on known no-ops buys nothing.
    "tn36-ef4dde99": [(6, {"x": 32, "y": 32}), (6, None), (1, None), (2, None)],
}

# A DEVIATION FROM THE FROZEN PLAN, RECORDED RATHER THAN ABSORBED.
#
# The main run produced an unplanned result: `ACTION6 {x, y}` on tn36 returned
# **200** with a changed frame, and only the same command *without* coordinates
# returned 500. Every previous attempt in either track's logs put the
# coordinates under a `data` key (baseline-arms: 128 such calls, all 500) or
# omitted them (200 calls, all 500), so the shape had never been tried. That is
# the open item ACCESS_CHECK.md calls the blocker for tn36 and for the whole
# `click` family, and it rested here on ONE observation.
#
# Three more actions turn one observation into a checkable claim: does it
# reproduce from a fresh session, and are the coordinates actually read rather
# than ignored? Total spend goes to 25 of the 30 cap. This is an addition to a
# spec that was meant to be frozen before the run, so it is a separate dict, run
# into a separate run directory, with its own prediction written first -- and
# named a deviation here so nobody has to reconstruct it from the diff.
FOLLOWUP = {
    "tn36-ef4dde99": [
        (6, {"x": 32, "y": 32}),   # reproduce the main run's 200 from a fresh RESET
        (6, {"x": 5, "y": 5}),     # different coordinates: are x,y read or ignored?
        (6, {"x": 32, "y": 32}),   # the original coordinates again, from a new state
    ],
}

# Hard caps, checked before anything is spent.
BUDGET_TOTAL = 30
BUDGET_PER_GAME = 7

# 500 is not retryable (precheck._retryable agrees), so tn36's ACTION6 costs one
# HTTP call each. The retry envelope for everything else is INC-005's, unchanged:
# 40 attempts, cap 5s, full id only, `400 ... not found` / 429 / transport only.
RETRY_NOTE = ("INC-005 envelope unchanged: full id only, 40 attempts, backoff "
              "capped at 5s, retry on `400 ... not found` / 429 / transport")


SETS = {"main": SEQUENCES, "followup": FOLLOWUP}


def total_actions() -> int:
    """Every action this spec can spend, both sets. The cap is over the ticket."""
    return sum(len(s) for group in SETS.values() for s in group.values())


def check_budget() -> None:
    """Refuse to run at all if the frozen spec would overspend."""
    for name, group in SETS.items():
        for game, seq in group.items():
            if len(seq) > BUDGET_PER_GAME:
                raise SystemExit("spec: %s/%s has %d actions > per-game cap %d"
                                 % (name, game, len(seq), BUDGET_PER_GAME))
    if total_actions() > BUDGET_TOTAL:
        raise SystemExit("spec: %d actions > total cap %d"
                         % (total_actions(), BUDGET_TOTAL))


if __name__ == "__main__":
    check_budget()
    for name, group in SETS.items():
        for game, seq in sorted(group.items()):
            print("%-9s %-16s %d  %s"
                  % (name, game, len(seq),
                     " ".join("A%d%s" % (a, "+%s" % ",".join("%s=%s" % kv for kv
                                                             in sorted(d.items()))
                                         if d else "")
                              for a, d in seq)))
    print("total %d / %d" % (total_actions(), BUDGET_TOTAL))
