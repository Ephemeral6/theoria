"""Does `figures/` still build where the release tree differs from this repo?

Two of V23's first-pass changes would have broken the release and neither was
caught by any gate, because no gate runs in a release tree. An adversarial review
found them by reading `release/`. This probe is what should have existed instead
of that review, so the next change to `sources.py` has something to fail against.

Both cases are checked by running the real functions with `sources.REPO_ROOT`
pointed at a synthetic tree outside the repository -- never by reasoning about
what they would do.

**Case A -- no repository.** A release tarball is a directory of files with a git
binary on PATH and no `.git`. V23's first `git_log` asked `shutil.which("git")` to
decide whether to degrade, which answers "git is here" in exactly that tree, so it
raised -- in the case its own docstring promises to survive. Required behaviour:
`git_log` returns `[]`, records the reason in `GIT_DEGRADED`, and does not raise.

**Case B -- the shards are absent on purpose.** `release/LICENCE_POSTURE.md`
classes `baseline-arms/out/shards/ledger.*.jsonl` as class B, "NEEDS WRITTEN
PERMISSION. Default: excluded", to be shipped as a digest plus a reproduction
script. V23's first pass set `floor=15, optional=False` on that family, which turns
`check_required()` non-empty and `verify.sh` gate 0 red before any other gate runs.
Required behaviour: `floor_violations()` and `tracked_but_missing()` are both empty
when the family is absent and git cannot be asked about it.

    python figures/runs/<id>/release_tree_probe.py
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import tempfile

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES = os.path.dirname(os.path.dirname(RUN_DIR))
sys.path.insert(0, FIGURES)

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if detail:
        print(f"        {detail}")
    if not ok:
        failures.append(label)


def main() -> int:
    print(f"git on PATH: {shutil.which('git') is not None}  "
          "(the release-tarball condition: a binary, and no repository)\n")

    with tempfile.TemporaryDirectory(prefix="v23-release-tree.") as tmp:
        # A synthetic release tree: the declared source paths that a release
        # ships, and nothing else. No .git, no shards.
        for rel in (
            "baseline-arms/BUDGET_REPORT.md",
            "baseline-arms/ledger.jsonl",
            "cold-start-a0/THEORIZE_LOG.md",
        ):
            dst = os.path.join(tmp, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write("synthetic\n")
        os.makedirs(os.path.join(tmp, "baseline-arms", "out", "shards"), exist_ok=True)

        import sources
        importlib.reload(sources)
        sources.REPO_ROOT = tmp
        sources._ALL_TRACKED = None
        sources.TRACKING_UNAVAILABLE.clear()
        sources.GIT_DEGRADED.clear()

        print("case A -- no repository:")
        check("in_git_work_tree() is False in a non-repo",
              sources.in_git_work_tree() is False)
        try:
            rows = sources.git_log("cold-start-a0/THEORIZE_LOG.md")
            check("git_log degrades instead of raising", rows == [],
                  f"returned {len(rows)} row(s)")
            check("and says why, in GIT_DEGRADED", len(sources.GIT_DEGRADED) == 1,
                  sources.GIT_DEGRADED[0] if sources.GIT_DEGRADED else "(empty)")
        except Exception as exc:  # noqa: BLE001
            check("git_log degrades instead of raising", False, f"raised {exc!r}")

        print("\ncase B -- the class-B shards are absent on purpose:")
        check("_tracked_paths cannot answer, and records that",
              sources._tracked_paths("baseline-arms/out/shards") is None
              and len(sources.TRACKING_UNAVAILABLE) >= 1,
              (sources.TRACKING_UNAVAILABLE or ["(empty)"])[0])
        # The rule under test, re-discovered against the synthetic tree.
        rule = sources.rule("envelope_ledger")
        check("envelope_ledger is floor=0 and optional",
              rule.floor == 0 and rule.optional,
              f"floor={rule.floor} optional={rule.optional} tracked={rule.tracked}")
        found = sources._discover(rule)
        check("it discovers nothing there, without complaint", found == (),
              f"discovered {len(found)}")
        sources.DISCOVERED[rule.name] = found
        # Scoped to the rule under test. The first version of this assertion
        # required `floor_violations()` to be empty *overall*, and it failed --
        # on `pilot_rollup`'s floor of 6, because the synthetic tree has no
        # pilot roll-ups either. That is a fact about my synthetic tree and, more
        # importantly, about a pre-existing condition this change did not create;
        # see the note this probe prints at the end. Asserting the broad version
        # would have made this probe fail for a reason it is not about, which is
        # how a probe gets switched off.
        envelope_violations = [
            v for v in sources.floor_violations() if "envelope_ledger" in v
        ]
        check("no floor violation from envelope_ledger", envelope_violations == [],
              str(envelope_violations))
        check("tracked_but_missing() is empty", sources.tracked_but_missing() == [],
              str(sources.tracked_but_missing()))

    print("""
NOT FIXED HERE, AND FOUND BY WRITING THIS PROBE -- `figures/` cannot build in a
default release tree at all, and never could. `release/LICENCE_POSTURE.md:48`
puts `baseline-arms/ledger.jsonl` in class B ("NEEDS WRITTEN PERMISSION.
Default: excluded"), and `sources.py` declares it as the `pilot_ledger` Source
with `optional=False`. So `check_required()` reports it missing and gate 0 goes
red before any other gate runs -- for the required ledger, not for the shards.
`pilot_rollup`'s floor of 6 is a second, similar question depending on how
`baseline-arms/out/pilot_*.json` is classified, which is not mine to rule on.

This probe therefore checks the narrow thing it can honestly check: that V23's
change to `envelope_ledger` adds no new release-time failure. It does not claim
the release build works. Whether `figures/` should be reproducible from a class-A
tree is a `release/` decision -- either the plates that read class-B inputs are
declared unbuildable downstream, or those inputs get written permission. Reported
to monitor rather than decided here.""")
    if failures:
        print(f"RELEASE-TREE PROBE: red. {len(failures)} failure(s): "
              f"{', '.join(failures)}", file=sys.stderr)
        return 1
    print("RELEASE-TREE PROBE: green. The class-B shard exclusion no longer turns "
          "gate 0 red, and a tree with no repository degrades instead of raising.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
