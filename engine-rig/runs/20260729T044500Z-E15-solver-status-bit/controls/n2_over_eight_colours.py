"""N2 -- a truncated subset scan does not get to call a law `global`.

E15 item P4, second negative control.  Run it from `engine-rig/`:

    python runs/20260729T044500Z-E15-solver-status-bit/controls/n2_over_eight_colours.py

Exit **0** iff the property holds, exit **1** on any violation.  The verdict is
also written to `artifacts/n2-over-eight-colours.json` (`--out-dir` to
relocate): the pre-registration judges this control on its exit code *and* on
fields of the artifact it writes.

## What makes this a control rather than a demonstration

`zero_space.local_laws` enumerates the colour subsets of each cell to decide
whether a recovered law is about the *encoding* (`cell_local`) or about the
*world* (`global`).  Above `SUBSET_ENUMERATION_LIMIT = 8` colours that
enumeration is truncated to singletons plus the full set, so a cell-local law
over three of eleven colours is never looked for.  It does not vanish -- it stays
in the quotient, and before E15 it went out labelled `scope: "global"`.  A
budget was deciding a classification, and the classification is the difference
between a law about the world and a bookkeeping identity of the encoding.

Ten colours is an ARC palette, so the path is live rather than hypothetical.
This control drives the **real public entry point** `zero_space.run` over a
ten-colour trajectory, emits real candidate rows through the real
`common.candidates` writer, reads them back off disk, and asserts:

  * **no** emitted payload carries `scope == "global"` -- nor any scope word
    with `global` inside it, since a consumer written as `"global" in scope`
    must not resurrect the claim either;
  * every degraded payload carries the **budget**, positively: the limit that
    bit, the cells it truncated, `scope_proved: False`, and an `error` naming
    the cap -- the shape `bench/ladder.py` uses for an over-budget rung;
  * a two-colour run, where nothing is truncated, still does emit
    `scope == "global"`.

The last one is the guard against the cheap pass.  Without it the control is
satisfied by an engine that has deleted the `global` label altogether, which
would be the same defect from the other side: the word must survive where it is
earned and disappear where it is not.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from common.jsonio import read_jsonl                      # noqa: E402
from engines import zero_space                            # noqa: E402
from engines.zero_space import zerospace                  # noqa: E402

CONTROL = "N2"
TITLE = "a truncated colour enumeration may not publish a law as global"

#: Frozen so the emitted rows are byte-stable; ids are content-addressed under
#: THEORIA_DETERMINISTIC_IDS but the timestamp is not, and this control writes a
#: checked-in artifact.
TIMESTAMP = "2026-07-27T00:00:00Z"

#: Two above the limit -- an ARC palette is ten.  Built from the engine's own
#: constant so that raising the cap moves the fixture with it instead of
#: silently turning the control green.
PALETTE = [chr(ord("a") + i)
           for i in range(zerospace.SUBSET_ENUMERATION_LIMIT + 2)]

SMALL_PALETTE = ["r", "b"]
SMALL_STATES = [["r", "b"], ["b", "r"], ["r", "b"]]

#: Keys a degraded payload has to carry, per P3 item 2: the budget, positively.
BUDGET_KEYS = ("scope_proved", "subset_enumeration_limit", "truncated_cells",
               "error", "scope_note")


def trajectory(palette):
    """A two-cell walk that cycles the whole palette, so every colour is seen."""
    return [[palette[i % len(palette)], palette[(i + 1) % len(palette)]]
            for i in range(len(palette))]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--out-dir", default=os.path.join(HERE, "artifacts"),
                        help="where the verdict artifact is written")
    args = parser.parse_args(argv)

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, "n2-over-eight-colours.json")
    # `common.candidates.emit` is append-only by contract, so the stream this
    # control reads back has to start empty or a second run reads the first.
    big_path = os.path.join(out_dir, "n2-candidates-10colour.jsonl")
    small_path = os.path.join(out_dir, "n2-candidates-2colour.jsonl")
    for path in (big_path, small_path):
        if os.path.exists(path):
            os.remove(path)

    checks = []

    def check(name, condition, detail=""):
        passed = condition is True
        checks.append({"name": name, "passed": passed, "detail": str(detail)})
        print(("  PASS  " if passed else "  FAIL  ") + name
              + (" -- " + str(detail) if detail else ""))
        return passed

    print("%s: %s" % (CONTROL, TITLE))
    print("  limit        SUBSET_ENUMERATION_LIMIT = %d"
          % zerospace.SUBSET_ENUMERATION_LIMIT)
    print("  palette      %d colours: %s" % (len(PALETTE), "".join(PALETTE)))

    observed = {"palette_size": len(PALETTE),
                "subset_enumeration_limit": zerospace.SUBSET_ENUMERATION_LIMIT}

    # ------------------------------------------- 1. the real run, over the limit
    result = None
    rows = []
    try:
        result = zero_space.run(trajectory(PALETTE), PALETTE,
                                out_path=big_path, timestamp=TIMESTAMP)
        rows = read_jsonl(big_path)
    except Exception as exc:                      # noqa: BLE001 -- reported, not swallowed
        observed["run_raised"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc()

    truncated = list(getattr(result, "truncated_cells", []) or [])
    observed["truncated_cells"] = truncated
    observed["n_rows"] = len(rows)

    check("the fixture really crosses the enumeration limit",
          bool(truncated) and len(PALETTE) > zerospace.SUBSET_ENUMERATION_LIMIT,
          "truncated_cells=%r" % (truncated,))
    check("the run emitted candidate rows to read back",
          len(rows) > 0, "%d row(s) at %s" % (len(rows), os.path.basename(big_path)))

    payloads = [row.get("payload", {}) for row in rows]
    scopes = Counter(p.get("scope") for p in payloads)
    observed["scope_counts"] = dict(sorted(
        (str(k), v) for k, v in scopes.items()))

    # --- the property itself
    global_rows = [p for p in payloads if p.get("scope") == zerospace.GLOBAL]
    check("no emitted payload claims scope == 'global'",
          not global_rows,
          "%d row(s) still claim it" % len(global_rows))
    substring_rows = [p for p in payloads
                      if zerospace.GLOBAL in str(p.get("scope"))]
    check("nor any scope word a `'global' in scope` reader would accept",
          not substring_rows,
          "%r" % sorted({str(p.get("scope")) for p in substring_rows}))

    degraded = [p for p in payloads if p.get("scope") == zerospace.UNDETERMINED]
    observed["n_degraded"] = len(degraded)
    check("the quotient representatives are published, under the degraded word",
          len(degraded) > 0,
          "%d payload(s) with scope=%r" % (len(degraded), zerospace.UNDETERMINED))

    # --- and the degradation is written positively into every degraded payload
    missing_keys = sorted({k for p in degraded for k in BUDGET_KEYS if k not in p})
    check("every degraded payload carries the budget keys",
          not missing_keys and bool(degraded),
          "missing %r" % (missing_keys,))

    bad_budget = [
        p for p in degraded
        if p.get("subset_enumeration_limit") != zerospace.SUBSET_ENUMERATION_LIMIT
        or not p.get("truncated_cells")
        or p.get("scope_proved") is not False
        or not isinstance(p.get("error"), str)
        # the error has to *name* the cap, not merely exist: a message that does
        # not say which budget bit leaves the reader where they started
        or str(zerospace.SUBSET_ENUMERATION_LIMIT) not in str(p.get("error"))
    ]
    check("and the budget it carries is the one that actually bit",
          not bad_budget and bool(degraded),
          "%d payload(s) with a wrong or absent budget" % len(bad_budget))
    check("every degraded payload names the cells that went unenumerated",
          bool(degraded) and all(
              sorted(p.get("truncated_cells") or []) == sorted(truncated)
              for p in degraded),
          "run truncated %r" % (truncated,))
    if degraded:
        observed["degraded_example"] = {k: degraded[0].get(k)
                                        for k in ("scope",) + BUDGET_KEYS}

    # ------------------------------- 2. the contrast: `global` is still earned
    #
    # Without this, deleting the label outright passes the control.
    small_rows = []
    small_result = None
    try:
        small_result = zero_space.run(SMALL_STATES, SMALL_PALETTE,
                                      out_path=small_path, timestamp=TIMESTAMP)
        small_rows = read_jsonl(small_path)
    except Exception as exc:                      # noqa: BLE001
        observed["small_run_raised"] = "%s: %s" % (type(exc).__name__, exc)
        traceback.print_exc()

    small_payloads = [row.get("payload", {}) for row in small_rows]
    small_scopes = Counter(p.get("scope") for p in small_payloads)
    observed["small_scope_counts"] = dict(sorted(
        (str(k), v) for k, v in small_scopes.items()))
    observed["small_truncated_cells"] = list(
        getattr(small_result, "truncated_cells", []) or [])

    check("under the limit nothing is truncated",
          not observed["small_truncated_cells"],
          "truncated_cells=%r" % (observed["small_truncated_cells"],))
    check("and `global` is still emitted where it was proved",
          small_scopes.get(zerospace.GLOBAL, 0) > 0,
          "scopes=%r" % (observed["small_scope_counts"],))
    check("an exhaustive row carries no degradation keys",
          bool(small_payloads) and not any(
              k in p for p in small_payloads for k in BUDGET_KEYS),
          "keys on an exhaustive row would re-hash a pinned artifact")

    failures = [c["name"] for c in checks if not c["passed"]]
    exit_code = 1 if failures else 0
    report = {
        "control": CONTROL,
        "item": "E15-solver-status-bit",
        "property": TITLE,
        "entry_point": "engines.zero_space.run",
        "palette": list(PALETTE),
        "checks": checks,
        "failures": failures,
        "observed": observed,
        "verdict": "violated" if failures else "hold",
        "exit_code": exit_code,
    }
    with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")

    print("")
    print("  artifact     %s" % report_path)
    if failures:
        print("VIOLATED: " + ", ".join(failures))
    else:
        print("HOLD: over the budget no law is published as `global`, and every "
              "degraded law carries the cap that demoted it.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
