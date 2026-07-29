"""P3 verification driver -- E15, item P3 (zero_space scope degradation).

Runs the REAL public entry `engines.zero_space.run` over a >8-colour palette and
over the 2-colour baseline, and reports on the three pass conditions.  Writes
nothing outside its own run directory.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from engines import zero_space
from engines.zero_space import zerospace
from common.jsonio import read_jsonl

COLORS_10 = ["c%d" % i for i in range(10)]          # 10 > SUBSET_ENUMERATION_LIMIT
COLORS_2 = ["B", "R"]


def trajectory_10(n_cells=4, n_steps=12):
    """A deterministic >8-colour walk that preserves (#c0) mod 2.

    Two cells flip together on every step, so the parity of any single colour is
    conserved and the null space is non-trivial.
    """
    state = [COLORS_10[i % len(COLORS_10)] for i in range(n_cells)]
    states = [list(state)]
    for t in range(n_steps):
        a = t % n_cells
        b = (t + 1) % n_cells
        state[a], state[b] = state[b], state[a]
        states.append(list(state))
    return states


def trajectory_2(n_cells=4, n_steps=12):
    state = ["R" if i % 2 == 0 else "B" for i in range(n_cells)]
    states = [list(state)]
    for t in range(n_steps):
        a = t % n_cells
        b = (t + 1) % n_cells
        state[a], state[b] = state[b], state[a]
        states.append(list(state))
    return states


def main():
    report = {}

    # ---------------------------------------------------------------- P3.1
    tmpdir = tempfile.mkdtemp(prefix="e15p3-")
    out10 = os.path.join(tmpdir, "cand10.jsonl")
    states = trajectory_10()
    result = zero_space.run(states, COLORS_10, out_path=out10)

    rows = list(read_jsonl(out10))
    scopes = sorted({r["payload"]["scope"] for r in rows})
    report["p3_1"] = {
        "limit": zerospace.SUBSET_ENUMERATION_LIMIT,
        "n_colors": len(COLORS_10),
        "n_cells": len(states[0]),
        "n_features": result.n_features,
        "truncated_cells": list(result.truncated_cells),
        "n_laws": len(result.laws),
        "scopes_present": scopes,
        "n_scope_global": sum(1 for r in rows if r["payload"]["scope"] == "global"),
        "n_scope_global_substring": sum(
            1 for r in rows if "global" in r["payload"]["scope"]),
        "n_undetermined": len(result.undetermined_laws()),
        "n_cell_local": len(result.cell_local_laws()),
        "global_laws_accessor_len": len(result.global_laws()),
        "run_as_json": result.as_json(),
    }

    # ---------------------------------------------------------------- P3.2
    degraded = [r for r in rows if r["payload"]["scope"] == "undetermined"]
    undegraded = [r for r in rows if r["payload"]["scope"] != "undetermined"]
    extra_keys = {"scope_proved", "subset_enumeration_limit",
                  "truncated_cells", "error", "scope_note"}
    report["p3_2"] = {
        "n_degraded_rows": len(degraded),
        "sample_degraded_payload": degraded[0]["payload"] if degraded else None,
        "every_degraded_row_has_all_extra_keys": all(
            extra_keys <= set(r["payload"]) for r in degraded),
        "ladder_shape": {
            "negative_bit_present": all(
                r["payload"].get("scope_proved") is False for r in degraded),
            "error_names_the_budget": all(
                "over budget" in str(r["payload"].get("error", "")) and
                str(zerospace.SUBSET_ENUMERATION_LIMIT)
                in str(r["payload"].get("error", ""))
                for r in degraded),
            "limit_carried": all(
                r["payload"].get("subset_enumeration_limit")
                == zerospace.SUBSET_ENUMERATION_LIMIT for r in degraded),
            "truncated_cells_carried": all(
                r["payload"].get("truncated_cells") == list(result.truncated_cells)
                for r in degraded),
            "sentence_present": all(
                len(str(r["payload"].get("scope_note", ""))) > 40 for r in degraded),
        },
    }

    # ---------------------------------------------------------------- P3.3
    out2 = os.path.join(tmpdir, "cand2.jsonl")
    result2 = zero_space.run(trajectory_2(), COLORS_2, out_path=out2)
    rows2 = list(read_jsonl(out2))
    leaked = sorted({k for r in rows2 for k in extra_keys & set(r["payload"])})
    leaked_same_run = sorted(
        {k for r in undegraded for k in extra_keys & set(r["payload"])})
    report["p3_3"] = {
        "baseline_truncated_cells": list(result2.truncated_cells),
        "baseline_n_rows": len(rows2),
        "baseline_scopes": sorted({r["payload"]["scope"] for r in rows2}),
        "extra_keys_on_baseline_rows": leaked,
        "extra_keys_on_undegraded_rows_of_truncated_run": leaked_same_run,
        "n_undegraded_rows_in_truncated_run": len(undegraded),
    }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
