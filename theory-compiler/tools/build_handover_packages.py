"""Build the two handover packages this track ships.

    python -m tools.build_handover_packages           # write
    python -m tools.build_handover_packages --check   # rebuild in memory, diff

The two are chosen to be the two manuals that exist, not two convenient ones,
and they differ in the way that matters for 1.11: one ships a playbook and one
does not, so the repository carries an example of each delivery tier.

`a0-cart` is `cold-start-a0/theory/theory.dsl` — this track's own A0 manual —
with its playbook, at tier `manual+playbook`.

`a0-sokoban2` is the `a0-spike` manual at tier `manual`, and which file that is
takes a paragraph. **The upstream `a0-spike/theory/theory.dsl` yields no package
at all**, and the refusal is earlier than the known blocker. The known blocker is
that it leaves `dir` a free name — its own generator passes it in as a function
parameter, so nothing in the file says what `dir` ranges over, and `gen_python`
stops at *"expected a direction from ['down', 'left', 'right', 'up'], got
NameRef(name='dir')"*. The builder never gets that far: the manual declares
`slid(o, dir)`, a two-argument slide, and the language implements
`slid(o, pusher, dir)`. A push moves the box **and** carries the pusher, so a
two-argument signature leaves half the effect unnamed, and there is no statement
of what the event does that could be handed to a reader. That is ledger X-1 seen
from the handover side. Measured, with both refusal messages, in
`runs/20260728T134022Z-C8-handover-package/upstream_vs_shipped.json`.

What ships is `tests/fixtures/sokoban2_theory.dsl`: the same manual with the v0.3
repairs, held against `a0-spike/world/sokoban2.py` as ground truth by
`tools/probe_mentions.py`. The substitution is recorded in that package's
`MANIFEST.json` under `provenance`, where a reader checking "is this really the
deliverable?" will find it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
REPO = os.path.dirname(TRACK)
sys.path.insert(0, os.path.join(TRACK, "src"))

from theory_compiler.handover import (LevelInput, PackageSpec,  # noqa: E402
                                      build_files, read_package, write_package)

OUT_ROOT = os.path.join(TRACK, "handover_packages")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _level(level_id: str, path: str) -> LevelInput:
    with open(path, encoding="utf-8") as handle:
        return LevelInput(level_id=level_id, doc=json.load(handle),
                          source=os.path.relpath(path, REPO).replace(os.sep, "/"))


def cart_package() -> PackageSpec:
    root = os.path.join(REPO, "cold-start-a0")
    return PackageSpec(
        world_id="a0-cart",
        title="The cart world — handover package (manual and playbook)",
        manual_dsl=_read(os.path.join(root, "theory", "theory.dsl")),
        playbook_dsl=_read(os.path.join(root, "theory", "playbook.dsl")),
        levels=(
            _level("base", os.path.join(root, "artifacts", "problem_a0-base.json")),
            _level("no-button",
                   os.path.join(root, "artifacts", "problem_a0-no-button.json")),
        ),
        provenance={
            "manual": {
                "copied_from": "cold-start-a0/theory/theory.dsl",
                "edits": "line endings normalised to LF; nothing else",
            },
            "playbook": {
                "copied_from": "cold-start-a0/theory/playbook.dsl",
                "edits": "line endings normalised to LF; nothing else",
            },
            "note": (
                "Both boards are the ones this manual was adjudicated against. "
                "They are not fresh instances: a handover *test* needs boards "
                "the author never saw, and choosing those is the exam's job, "
                "not the package builder's. What this package demonstrates is "
                "the domain/problem split, for which two boards of any "
                "provenance suffice."),
        },
    )


def sokoban_package() -> PackageSpec:
    fixtures = os.path.join(TRACK, "tests", "fixtures")
    return PackageSpec(
        world_id="a0-sokoban2",
        title="The sokoban-2 world — handover package (manual only)",
        manual_dsl=_read(os.path.join(fixtures, "sokoban2_theory.dsl")),
        playbook_dsl=None,
        levels=(
            _level("match", os.path.join(fixtures, "sokoban2_match_problem.json")),
            _level("crossing-up",
                   os.path.join(fixtures, "sokoban2_crossing_UP_problem.json")),
        ),
        provenance={
            "manual": {
                "copied_from": "theory-compiler/tests/fixtures/sokoban2_theory.dsl",
                "upstream": "a0-spike/theory/theory.dsl",
                "why_not_upstream": (
                    "no package can be built from the upstream manual. It "
                    "declares `slid(o, dir)`; a push moves the box and carries "
                    "the pusher, so a two-argument slide leaves half its own "
                    "effect unnamed and there is nothing to tell a reader the "
                    "event does. It also leaves `dir` a free name, which the "
                    "executable and proof backends refuse. The shipped file is "
                    "that manual with the v0.3 repairs (X-1, X-5), every rule "
                    "bound over a declared `domain direction`."),
                "ground_truth_check": (
                    "theory-compiler/tools/probe_mentions.py, against "
                    "a0-spike/world/sokoban2.py"),
            },
            "playbook": {
                "why_absent": (
                    "a0-spike ships no playbook file. This package is tier "
                    "`manual` because that is what the arm produced, not "
                    "because a tier was withheld."),
            },
        },
    )


PACKAGES = {"a0-cart": cart_package, "a0-sokoban2": sokoban_package}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.build_handover_packages")
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and compare against what is on "
                             "disk; write nothing")
    args = parser.parse_args(argv)

    failures = 0
    for name in sorted(PACKAGES):
        spec = PACKAGES[name]()
        out = os.path.join(OUT_ROOT, name)
        if args.check:
            want, _manifest = build_files(spec)
            have = read_package(out) if os.path.isdir(out) else {}
            missing = sorted(set(want) - set(have))
            extra = sorted(set(have) - set(want))
            differ = sorted(p for p in set(want) & set(have) if want[p] != have[p])
            if missing or extra or differ:
                failures += 1
                print("FAIL %s: %d missing, %d extra, %d differing"
                      % (name, len(missing), len(extra), len(differ)))
                for path in (missing + extra + differ)[:20]:
                    print("     %s" % path)
            else:
                print("ok   %s (%d files)" % (name, len(want)))
        else:
            manifest = write_package(spec, out)
            refused = {k: v.get("why", "")
                       for k, v in manifest["forms"].items()
                       if v["status"] != "generated"}
            print("wrote %s: %d files, tier %s, digest %s"
                  % (name, len(manifest["files"]), manifest["tier"],
                     manifest["bundle_digest"][:16]))
            for key, why in sorted(refused.items()):
                print("      form %s refused: %s" % (key, why[:120]))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
