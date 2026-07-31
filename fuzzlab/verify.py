"""One command that decides whether fuzzlab is green.

```bash
cd .worktrees/e4-property-fuzz && python -m fuzzlab.verify
```

Three stages, then one gate on the published main result:

| stage | question |
|---|---|
| `pytest fuzzlab/tests` | do the oracles compute what they claim, and does a short campaign still find nothing? |
| `campaign --worlds 60` | does the battery run end to end on every engine, with a reproducible seed table? |
| `engine-rig pytest` | is the tree under test the one the report says it is? |
| main-result scale | is the artifact the documents point at the size they say it is? |

The fourth is not a stage but a check on a file, and it is here because of
V-26: `README.md` pointed a reader at `out/campaign.json` for the 3000-world
result, and `out/campaign.json` is a 60-world smoke that reports zero
violations just as convincingly. The reader checks, the check passes, and what
was checked is not what was claimed. A README drifts again; this does not.

**A violation does not fail this script**, and that is the point: 失败是战利品.
A found defect is the battery's product. What fails is fuzzlab being broken —
an oracle that disagrees with its own closed form, a generator that cannot build
its own world, a campaign that cannot run. Violations are counted, printed, and
routed to `BUGS.md`; the exit code is about the instrument, not the reading.
"""

import json
import os
import subprocess
import sys
from typing import List, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE_RIG = os.path.join(ROOT, "engine-rig")

# --- the main result, and the scale it is published at ------------------------
#
# These are the numbers `README.md`, `BUGS.md` and `MUTATION.md` quote. They are
# here, in the gate, so that a document quoting a smaller run has to disagree
# with executable code rather than with prose. Recomputed 2026-07-31 (V-26) from
# a fresh `--worlds 500` run: identical to the artifact below in every field
# except `elapsed_s` and `engine_rig_head`.
MAIN_RESULT = os.path.join(
    "runs", "20260729T104608Z-V21-lp-unavailable-is-not-a-pass",
    "campaign", "campaign.json")
CLAIMED_WORLDS_PER_ENGINE = 500
CLAIMED_ENGINES = 6
CLAIMED_INVARIANTS = 26
CLAIMED_SEED = "0x00005eedc1e4f002"

# The 60-world snapshot. Named here only so the printout can say what it is; it
# is not the main result and nothing gates on its contents.
SMOKE_SNAPSHOT = os.path.join("out", "campaign.json")


def main_result_path() -> str:
    """Where the gate looks for the published 3000-world campaign.

    `FUZZLAB_MAIN_RESULT` overrides it. That override exists for the negative
    control — `tests/test_main_result_scale.py` points it at the 60-world smoke
    and asserts this gate goes red — and a probe that cannot be shown failing is
    a green light with nothing behind it.
    """
    override = os.environ.get("FUZZLAB_MAIN_RESULT")
    if override:
        return override
    return os.path.join(HERE, MAIN_RESULT)


def check_main_result(path: str) -> List[str]:
    """Reasons the artifact at `path` is not the run the documents claim.

    Empty list means it is. A **violation is not a reason** — the campaign's
    product is findings, and this function is about scale and provenance, not
    about what the engines did.
    """
    problems: List[str] = []
    if not os.path.exists(path):
        return ["main result missing: %s" % path]
    try:
        with open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
    except (ValueError, OSError) as exc:
        return ["main result unreadable: %s (%s)" % (path, exc)]

    totals = doc.get("totals", {})
    per_engine = doc.get("worlds_per_engine")
    if not isinstance(per_engine, int) or per_engine < CLAIMED_WORLDS_PER_ENGINE:
        problems.append(
            "worlds_per_engine is %r, below the claimed %d"
            % (per_engine, CLAIMED_WORLDS_PER_ENGINE))
    engines = doc.get("engines") or []
    if len(engines) < CLAIMED_ENGINES:
        problems.append(
            "%d engine(s) in the artifact, below the claimed %d"
            % (len(engines), CLAIMED_ENGINES))
    claimed_total = CLAIMED_WORLDS_PER_ENGINE * CLAIMED_ENGINES
    checked = totals.get("worlds_checked")
    if not isinstance(checked, int) or checked < claimed_total:
        problems.append(
            "totals.worlds_checked is %r, below the claimed %d"
            % (checked, claimed_total))
    invariants = totals.get("invariants")
    if not isinstance(invariants, int) or invariants < CLAIMED_INVARIANTS:
        problems.append(
            "totals.invariants is %r, below the claimed %d"
            % (invariants, CLAIMED_INVARIANTS))
    seed = doc.get("campaign_seed")
    if seed != CLAIMED_SEED:
        problems.append(
            "campaign_seed is %r, not the published %s" % (seed, CLAIMED_SEED))
    # `unavailable` is absent in pre-V-21 artifacts, and absent is not zero:
    # that schema could not count the quantity, so it cannot testify that it was
    # zero. The V-13 partial `campaign.500w.json` is the same 3000 worlds and
    # fails here for exactly that reason.
    unavailable = totals.get("unavailable")
    if unavailable is None:
        problems.append(
            "totals.unavailable absent — pre-V-21 schema cannot say whether a "
            "tool failed to compute")
    elif unavailable:
        problems.append(
            "totals.unavailable is %r; this run measured less than its "
            "coverage column claims" % unavailable)
    return problems


STAGES: Tuple[Tuple[str, Sequence[str], str], ...] = (
    ("oracle and battery tests",
     (sys.executable, "-m", "pytest", "fuzzlab/tests", "-q"), ROOT),
    ("campaign smoke, all six engines",
     (sys.executable, "-m", "fuzzlab.campaign", "--worlds", "60"), ROOT),
    ("engine-rig's own suite (the tree under test)",
     (sys.executable, "-m", "pytest", "-q"), ENGINE_RIG),
)


def main() -> int:
    failures: List[str] = []
    for label, command, cwd in STAGES:
        proc = subprocess.run(command, cwd=cwd, capture_output=True)
        text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        ok = proc.returncode == 0
        print("[%s] %s" % ("ok  " if ok else "FAIL", label))
        tail = text.strip().splitlines()
        for line in tail[-(4 if ok else 14):]:
            print("        " + line)
        if not ok:
            failures.append(label)

    main_path = main_result_path()
    problems = check_main_result(main_path)
    print()
    print("[%s] published main result (%s)"
          % ("ok  " if not problems else "FAIL",
             os.path.relpath(main_path, HERE).replace(os.sep, "/")))
    if problems:
        for problem in problems:
            print("        " + problem)
        failures.append("published main result is not at the claimed scale")
    else:
        with open(main_path, encoding="utf-8") as handle:
            doc = json.load(handle)
        print("        %d worlds per engine x %d engines, %d invariants, "
              "seed %s" % (doc["worlds_per_engine"], len(doc["engines"]),
                           doc["totals"]["invariants"], doc["campaign_seed"]))
        print("        totals: %s" % json.dumps(doc["totals"], sort_keys=True))

    findings = os.path.join(HERE, SMOKE_SNAPSHOT)
    if os.path.exists(findings):
        with open(findings, encoding="utf-8") as handle:
            totals = json.load(handle)["totals"]
        print()
        print("out/campaign.json is the 60-world SMOKE snapshot, not the "
              "result above")
        print("smoke totals: %s" % json.dumps(totals, sort_keys=True))
        if totals.get("violated"):
            print("  violations are the product, not a failure — see fuzzlab/BUGS.md")
        # `unavailable` is the one total that is not a reading about the engines.
        # It counts worlds no invariant judged because a tool could not compute,
        # and it is printed apart from `skipped` because most skips are the
        # engine correctly declining and this is nobody knowing. Non-zero means
        # the campaign measured less than its coverage column claims.
        if totals.get("unavailable"):
            print("  %d world(s) unjudged because a tool could not compute — "
                  "this run's coverage was not earned; see skips_by_cause"
                  % totals["unavailable"])

    print()
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        return 1
    print("green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
