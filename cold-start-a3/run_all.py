"""Everything, in order, from nothing.  `python run_all.py`

Six stages.  The order is the experiment's order and is not arbitrary: the
control arm runs *before* the transfer arm reads anything, and the negative
controls run last, so no stage can be accused of having been tuned against a
result it had already seen.

    1. world        the two levels' traces, the referee's copy, the four
                    first frames
    2. cold start   level 1 from nothing            -> bill_l1_cold_start.json
    3. control      level 2 from nothing            -> bill_l2_from_scratch.json
    4. transfer     level 2 carrying the two books  -> bill_l2_transfer.json
    5. negative     level 2 with one mechanism edited, books carried
    6. bill         the comparison table, generated from the meters

Determinism: `THEORIA_DETERMINISTIC_IDS=1` and a fixed timestamp are set here
and nowhere else that matters.  Two clean runs produce byte-identical
`artifacts/` and byte-identical generated forms; `tests/test_world.py` and the
subagent's determinism check both assert it.

Zero API calls, zero network, zero contact with the sealed pile.  A3's world is
self-built and its truth is a Python function in `a3world/`, which the pipeline
never imports — `tests/test_sealing.py` checks that rather than trusting it.
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

import _bootstrap  # noqa: F401,E402

from a3world import ground_truth  # noqa: E402

from a3pipeline import bill, coldstart, negctl, transfer  # noqa: E402
from a3pipeline import concepts  # noqa: E402

THEORY = os.path.join(HERE, "theory")


def rule(title: str) -> None:
    print("\n== %s %s" % (title, "=" * max(0, 62 - len(title))))


def main() -> int:
    start = time.time()

    rule("1. the world")
    report = ground_truth.build()
    for name, entry in sorted(report["levels"].items()):
        truth = entry["truth"]
        cov = entry.get("coverage")
        print("   %-16s states=%-4s shortest=%-5s %s" % (
            name, truth["reachable_states"], truth["shortest_solution_length"],
            ("sweep %d frames, pair coverage %.3f"
             % (cov["frames"], cov["coverage"])) if cov else "(frame 0 only)"))

    rule("2. cold start — level 1, carrying nothing")
    coldstart._print(coldstart.run(coldstart.L1, "THEORIZE_LOG.md"))

    rule("3. control — level 2, carrying nothing")
    scratch_dsl = os.path.join(THEORY, coldstart.L2_SCRATCH["dsl"])
    if os.path.exists(scratch_dsl):
        coldstart._print(coldstart.run(coldstart.L2_SCRATCH,
                                       "THEORIZE_LOG_L2_SCRATCH.md"))
    else:
        print("   SKIPPED — %s is absent.  The report's like-for-like column "
              "cannot be produced without it." % coldstart.L2_SCRATCH["dsl"])

    rule("4. transfer — level 2, carrying domain.dsl + playbook.dsl")
    result = transfer.run()
    counts = result["bill"]["counts"]
    print("   outcome=%s  static=%s replay=%s plan=%s/%s  win=%s"
          % (result["outcome"], result["certify_static"]["green"],
             result.get("certify_replay", {}).get("green"),
             result["plan"].get("status"), result["plan"].get("length"),
             result.get("execution", {}).get("win")))
    print("   bill  frames=%d actions=%d engines=%d candidates=%d rounds=%d "
          "clauses=%d" % (counts["world_frames"], counts["world_actions"],
                          counts["engine_stages"],
                          counts["candidates_adjudicated"],
                          counts["theorize_rounds"],
                          counts["dsl_clauses_written"]))

    rule("5. negative controls — the same arm, a world that was edited")
    verdict = negctl.run_all()
    for row in verdict["controls"]:
        print("   %-22s static=%-5s plan=%-5s replay=%-5s caught=%s"
              % (row["arm"], row["static_certify_green"], row["planned"],
                 row["replay_certify_green"], row["caught"]))
    print("   all caught: %s | none claimed a win: %s"
          % (verdict["all_caught"], verdict["none_claimed_a_win"]))

    rule("6. score against the referee — every reachable pair, not just the plan")
    from a3world import score as score_mod
    for row in score_mod.run_all()["results"]:
        print("   %-22s %-8s %4d/%-4d = %.4f  %s"
              % (row["theory"].split("/")[1], row["level"],
                 row["pairs_correct"], row["pairs_checked"],
                 row["accuracy"], row["note"]))

    rule("7. bookkeeping")
    accounts = concepts.write_accounts()
    print("   concept accounts: %s" % ", ".join(
        "%s %+d" % (a["name"], a["script_delta"]) for a in accounts))
    pin = concepts.write_upstream_pin()
    print("   upstream pin: %d files hashed" % len(pin["files"]))

    table = bill.build()
    text = bill.markdown(table)
    with open(os.path.join(HERE, "artifacts", "bill_table.md"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print()
    print(text)

    print("done in %.1fs" % (time.time() - start))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
