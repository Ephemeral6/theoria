"""Regenerate `interop/certificates/*.json` from the engine that proves them.

The three documents in `certificates/` were committed by hand and no script in
the tree produced them: the only record of a regeneration is a prose line in
`runs/20260729T020000Z-E16-verdict-must-gate/MANIFEST.json`, with no command
quoted. An artefact whose producer is a sentence in another artefact's manifest
is an artefact nobody can rebuild, and "self-contained, independently checkable"
is a weaker claim when the first half of the chain is missing.

This is the missing half. `--check` compares the committed bytes against what
this run makes, the same discipline `recheck/build_cases.py --check` uses for
its cases.

Run from `engine-rig/`:

    python -m interop.export_certificates --check     # bytes still agree?
    python -m interop.export_certificates             # rewrite them

One caveat, recorded rather than papered over: the LP is solved by
`scipy.optimize.linprog(method="highs")` in floating point and snapped to
rationals with `Fraction.limit_denominator(1000)` (`engines/lp_potential/
potential.py:388`), then re-checked exactly. The snap is what makes the
committed weights clean integers and is wide enough to absorb float noise, but
the guarantee it buys is "same scipy/HiGHS build ⟹ same bytes", not "same bytes
anywhere". `--check` is therefore a real regression test on this machine and a
provenance record everywhere else.
"""

import argparse
import json
import os
import sys

from engines.lp_potential.potential import solve_certificate
from interop import certificate_export as ce
from interop import peg1d

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "certificates")

#: The LP bound the interop cases were solved at. Not the engine default (10);
#: `interop/README.md` records that infeasibility was confirmed at 10, 100 and
#: 10000, and the certificates that do exist were taken from the widest run.
BOUND = 10000

#: (n_pos, initial, goal_states, claim_name) -- one row per committed document.
#: The filename is derived by `certificate_export.write`, not stated here, so a
#: rename in the writer shows up as a missing file rather than as two files.
CASES = (
    (4, "1110", ("0100",), "unsolvable_1110_to_0100"),
    (5, "11011", ("00010",), "unsolvable_11011_to_00010"),
    (5, "11011", ("01000",), "unsolvable_11011_to_01000"),
)


def build_one(n_pos, initial, goal_states, claim_name):
    """Engine in, document out. Raises if the LP finds no certificate.

    A silent `None` here would mean "this claim has no linear pagoda", which is
    a real answer for other configurations (`interop/README.md` tabulates which
    ones) but would be a regression for these three, so it is an error rather
    than an empty result.
    """
    goals = list(goal_states)
    graph = peg1d.build_graph(n_pos, initial, goal_states=goals)
    certificate = solve_certificate(graph, initial, goal_states=goals,
                                    bound=BOUND)
    if certificate is None:
        raise RuntimeError(
            "no linear pagoda for %s -> %s on %d cells; this case is committed "
            "as certified, so an empty result is a regression, not an answer"
            % (initial, "+".join(goals), n_pos))
    return ce.build(certificate, graph, claim_name=claim_name), graph


def rendered(document):
    """Exactly the bytes `certificate_export.write` would put on disk."""
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def path_for(document):
    return os.path.join(OUT_DIR, "pagoda_%s_%s_to_%s.json" % (
        document["n_pos"], document["initial_state"],
        "+".join(document["goal_states"])))


def regenerate(check_only):
    problems = []
    for case in CASES:
        document, _ = build_one(*case)
        path = path_for(document)
        text = rendered(document)
        name = os.path.relpath(path, HERE)
        if check_only:
            if not os.path.exists(path):
                problems.append("%s: committed file is missing" % name)
                continue
            with open(path, encoding="utf-8") as handle:
                on_disk = handle.read()
            if on_disk != text:
                problems.append(
                    "%s: %d bytes on disk, %d rebuilt; they differ"
                    % (name, len(on_disk), len(text)))
        else:
            os.makedirs(OUT_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
            sys.stdout.write("wrote %s\n" % name)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="compare against the committed bytes; write nothing")
    args = parser.parse_args(argv)
    problems = regenerate(args.check)
    if problems:
        for line in problems:
            sys.stderr.write("%s\n" % line)
        return 1
    if args.check:
        sys.stdout.write("%d certificate(s) rebuild byte-for-byte\n"
                         % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
