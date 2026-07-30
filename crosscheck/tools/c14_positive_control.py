"""Positive control: show the instrument scoring known-good PDDL as GOOD.

C14 reported that 0 of 303 actions compile to well-formed, non-empty PDDL. A
measuring instrument that has only ever been pointed at a corpus where everything
scores bad has not been shown to be capable of saying "good" at all -- and this one
turned out to have a real false negative (``declared_predicates`` used a regex that
required the ``(:predicates ...)`` block to close on its own line, so any domain
closing it inline had every action reported ``undeclared-predicate``).

That defect was found by an adversarial pass rather than by the measurement, which
is the argument for this file existing. Two controls, both over PDDL the census
never generated:

* **the second backend** -- ``cold-start-a0/compile/gen_pddl_a0.py`` emits 25
  committed domains over the same worlds. They must score 263 of 263 GOOD. This is
  the control that matters: it is real, committed, Fast-Downward-accepted PDDL
  produced from the same ``theory.dsl`` files the census scores 0 on.
* **a textbook domain** -- ``engine-rig/engines/fd_adapter/domain.pddl`` (gripper),
  which closes its predicates block inline. It must score 3 of 3. This is the
  regression pin for the false negative above.

    python -m crosscheck.tools.c14_positive_control

Exit 0 green, 1 red. Reads only; generates nothing.
"""

from __future__ import annotations

import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "crosscheck", "tools"))

import c14_pddl_census as census                                   # noqa: E402

BACKEND_B_MARK = "gen_pddl_a0.py"
GRIPPER = os.path.join("engine-rig", "engines", "fd_adapter", "domain.pddl")


def score(text: str):
    """``(good, total)`` for one domain, using the census's own classifier."""
    declared = census.declared_predicates(text)
    acts = [census.classify(n, b, declared)
            for n, b in census.action_blocks(text)]
    return sum(1 for a in acts if a["semantically_non_empty"]), len(acts)


def tracked_domains(root: str) -> list:
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                         text=True, timeout=120)
    return [p for p in out.stdout.split("\n") if p.endswith("domain.pddl")]


def main(argv=None) -> int:
    # `.toolchain/` and the second backend's output live in the main checkout;
    # from a worktree, ask git where that is rather than silently finding nothing.
    root = REPO
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute",
                             "--git-common-dir"], cwd=REPO, capture_output=True,
                            text=True, timeout=30)
    if common.returncode == 0:
        main_checkout = os.path.dirname(common.stdout.strip())
        if main_checkout and os.path.isdir(main_checkout):
            root = main_checkout

    failures = []

    # --- control 1: the second backend ---------------------------------------
    good = total = domains = 0
    for rel in tracked_domains(root):
        path = os.path.join(root, rel)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        first = text.split("\n", 1)[0]
        if BACKEND_B_MARK not in first:
            continue
        domains += 1
        g, t = score(text)
        good += g
        total += t
        if g != t:
            failures.append("backend-B domain scored %d/%d GOOD: %s" % (g, t, rel))
    if not domains:
        failures.append("found no domains from the second backend (%s) -- the "
                        "positive control did not run, which is not a pass"
                        % BACKEND_B_MARK)
    else:
        print("green  second backend: %d domains, %d/%d actions GOOD"
              % (domains, good, total))

    # --- control 2: a textbook domain, inline-closed predicates block --------
    gpath = os.path.join(root, GRIPPER)
    if not os.path.isfile(gpath):
        print("SKIP   %s absent; inline-predicates regression unchecked" % GRIPPER)
    else:
        g, t = score(open(gpath, encoding="utf-8").read())
        if t == 0:
            failures.append("%s parsed to zero actions" % GRIPPER)
        elif g != t:
            failures.append(
                "gripper scored %d/%d GOOD -- the inline-closed (:predicates) "
                "false negative is back" % (g, t))
        else:
            print("green  gripper (inline-closed predicates): %d/%d actions GOOD"
                  % (g, t))

    for line in failures:
        print("RED  %s" % line)
    if failures:
        print("\nC14 POSITIVE CONTROL: RED (%d)" % len(failures))
        return 1
    print("\nC14 POSITIVE CONTROL: GREEN -- the instrument can say GOOD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
