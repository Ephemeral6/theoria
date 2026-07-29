"""E14 item 2: re-run the existing instance set and reconcile.

The question this answers is a count, and only a count:

    of the exhaustiveness / coverage / no-violation claims standing in the
    committed reports, how many were made on top of an UNCOUNTED crash?

Two instance sets, both entirely offline -- no API, no network, no model call:

* `theoria-arm/runs/20260728T015354Z-g50t-first-contact` -- the one archived arm
  run that carries both books and a ledger. `certify` and `plan` are
  deterministic and spend nothing, which is the same reason `armtools.salvage`
  is allowed to re-run them after the fact.
* `a0-spike` -- the whole A0 pipeline, whose evidence is generated from
  `world/sokoban2.py` rather than fetched.

The books are copied out of the committed run directory before compiling, so
this script cannot write a byte into a published artifact.

    python runs/20260729T080000Z-E14-crash-is-not-a-finding/reconcile.py
"""

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ARM)
RAW = os.path.join(HERE, "raw")

sys.path.insert(0, ARM)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))
sys.path.insert(0, REPO)

import _bootstrap                                     # noqa: E402,F401

RUN_SLUG = "20260728T015354Z-g50t-first-contact"
RUN_DIR = os.path.join(ARM, "runs", RUN_SLUG)


def _dump(name, payload):
    path = os.path.join(RAW, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    return path


def theoria_arm_instance():
    """Re-certify and re-plan the archived arm run, with the crash account on."""
    from armtools.salvage import rebuild_trace         # noqa: PLC0415
    from inner import certify, commit, plan as plan_beat  # noqa: PLC0415
    from inner.books import Books                      # noqa: PLC0415
    from proxy.ledger import read_ledger               # noqa: PLC0415
    from world.frames import load_store                # noqa: PLC0415

    workdir = os.path.join(RAW, "theoria-arm-replay")
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    # Copy, so that compiling the books cannot rewrite a committed artifact.
    shutil.copytree(os.path.join(RUN_DIR, "books"),
                    os.path.join(workdir, "books"))

    records = read_ledger(os.path.join(RUN_DIR, "ledger.jsonl"))
    trace_path = os.path.join(workdir, "trace.jsonl")
    trace = rebuild_trace(records, trace_path)

    books = Books(os.path.join(workdir, "books"))
    store = load_store(trace_path)
    compiled = books.compile_all()
    out = {"slug": RUN_SLUG, "trace": trace,
           "compile_ok": bool(compiled.get("ok"))}
    out["certify"] = certify.cheap(books, store, commit.action_to_manual)
    namespace, error = books.load_predictor()
    if namespace is None:
        out["plan"] = {"status": "no_predictor", "detail": error}
    else:
        out["plan"] = plan_beat.plan(books, namespace, compiled)

    # And, because the archived manual declares no goal, BFS never runs on it.
    # A `plan.py` exhaustiveness claim that is never reached is not evidence
    # about `plan.py`; say so rather than counting it as a clean one.
    out["bfs_reached"] = out["plan"].get("status") not in (
        "no_goal_declared", "no_predictor", "not_attempted")
    return out


def theoria_arm_bfs_instance():
    """A second arm instance, because the archived one never reaches BFS.

    The archived g50t manual declares no winning condition, so `plan()` stops at
    `no_goal_declared` and the site this ticket is really about -- the `unsat` /
    "the whole reachable set was enumerated" exit -- is never executed on it.
    Reporting that as a clean claim would be the ticket's own disease. So the
    arm's worked example is compiled with an unreachable goal, which drains the
    queue for real: the Cart moves only up, from (2,1) to (0,1), so (2,2) is not
    on that line and the reachable set is three states.

    This goes through `plan()`, the real entry point. The first version of this
    script called `_tier_bfs` directly and justified it by saying the PDDL tier
    answered `sat` with an empty plan and the ladder never descended to BFS.
    That was **false** for this instance and an adversarial review caught it:
    with `goal Cart.pos = (2, 2)` the PDDL tier refuses correctly ("the grounded
    task has no plan"), the ladder descends, and BFS returns the `unsat` /
    `exhaustive: true` the audit wants. The sentence was true of an earlier
    draft that used `goal Cart.pos = (0, 0)` -- `gen_pddl` hardcodes objects to
    cell 0,0, so that goal is trivially satisfied in the PDDL form -- and it was
    not re-checked when the goal changed. It cost something real: `plan()`'s
    aggregation layer is exactly where the review then found a false zero on the
    `sat` path, and skipping that layer here is why the first pass missed it.
    """
    from inner import plan as plan_beat                # noqa: PLC0415
    from inner.books import Books                      # noqa: PLC0415
    from inner.grammar_card import WORKED_EXAMPLE      # noqa: PLC0415

    workdir = os.path.join(RAW, "theoria-arm-bfs")
    if os.path.isdir(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1",
                                    "goal Cart.pos = (2, 2)")
    books = Books(workdir)
    books.write(theory=theory, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    compiled = books.compile_all()
    namespace, error = books.load_predictor()
    if namespace is None:
        raise RuntimeError("the worked example did not compile: %s" % error)
    return plan_beat.plan(books, namespace, compiled)


#: `theoria-arm/world` and `a0-spike/world` are two different packages with the
#: same name, so the A0 half runs in its own interpreter rather than fighting
#: the first one onto `sys.path`. `encoding=` is pinned because this is a
#: Windows cp936 machine and a mojibake traceback is exactly the diagnostic a
#: crash-counting ticket must not lose.
A0_DRIVER = r"""
import json, os, sys
here = os.path.abspath(sys.argv[1])
sys.path.insert(0, here)
sys.path.insert(0, os.path.join(os.path.dirname(here), "engine-rig"))
from pipeline import adapt, run_a0
out = {"a0_report": run_a0.run(), "adaptation": adapt.run_all()}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"),
          indent=1, sort_keys=True, default=str, ensure_ascii=False)
"""


def a0_instance():
    import subprocess                                  # noqa: PLC0415
    out_path = os.path.join(RAW, "a0_report_rerun.json")
    driver = os.path.join(RAW, "_a0_driver.py")
    with open(driver, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(A0_DRIVER)
    done = subprocess.run(
        [sys.executable, driver, os.path.join(REPO, "a0-spike"), out_path],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=os.path.join(REPO, "a0-spike"))
    if done.returncode != 0:
        raise RuntimeError("the A0 re-run did not complete (exit %d):\n%s"
                           % (done.returncode, done.stderr[-2000:]))
    with open(out_path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    os.makedirs(RAW, exist_ok=True)
    findings = []

    arm = theoria_arm_instance()
    _dump("theoria-arm-recertify.json", arm)

    amb = (arm["certify"].get("checks") or {}).get("unambiguous") or {}
    old = json.load(open(os.path.join(RUN_DIR, "certify_reconstructed.json"),
                         encoding="utf-8"))
    old_amb = ((old.get("certify") or {}).get("cheap") or {}).get(
        "checks", {}).get("unambiguous", {})
    findings.append({
        "claim": "theoria-arm certify constraint 9 (`unambiguous`)",
        "artifact": "runs/%s/certify_reconstructed.json" % RUN_SLUG,
        "committed_claim_ok": old_amb.get("ok"),
        "committed_claim_detail": old_amb.get("detail"),
        "committed_crash_count_field": None,      # there was no such field
        "rerun_ok": amb.get("ok"),
        "rerun_crash_count": (amb.get("step_crashes") or {}).get("count"),
        "rerun_pairs_nominal": amb.get("pairs_nominal"),
        "rerun_pairs_checked": amb.get("pairs_checked"),
        "carried_an_uncounted_crash": bool(
            (amb.get("step_crashes") or {}).get("count")),
    })

    findings.append({
        "claim": "theoria-arm plan `unsat` / \"the whole reachable set was enumerated\"",
        "artifact": "runs/%s/certify_reconstructed.json" % RUN_SLUG,
        "committed_claim_ok": (old.get("plan") or {}).get("status"),
        "committed_claim_detail": (old.get("plan") or {}).get("detail"),
        "committed_crash_count_field": None,
        "rerun_ok": arm["plan"].get("status"),
        "rerun_crash_count": (arm["plan"].get("step_crashes") or {}).get("count"),
        "not_exercised": not arm["bfs_reached"],
        "carried_an_uncounted_crash": bool(
            (arm["plan"].get("step_crashes") or {}).get("count")),
        "note": ("the archived manual declares no goal, so BFS never ran on "
                 "this instance and no exhaustiveness claim was ever reached. "
                 "NOT COUNTED as clean -- counted as not exercised."),
    })

    bfs = theoria_arm_bfs_instance()
    _dump("theoria-arm-bfs-plan.json", bfs)
    bfs_tier = next((t for t in bfs.get("tiers", [])
                     if t.get("tier") == "object-state-bfs"), {})
    findings.append({
        "claim": ("theoria-arm plan `unsat` / \"the whole reachable set (%s "
                  "states) was enumerated\", worked example, unreachable goal, "
                  "through plan() rather than the tier"
                  % bfs_tier.get("reachable_states")),
        "artifact": "(not previously published -- this instance is new here, "
                    "added because the archived run never reaches BFS)",
        "committed_claim_ok": "n/a -- no committed artifact makes this claim",
        "committed_claim_detail": None,
        "committed_crash_count_field": None,
        "rerun_ok": bfs.get("status"),
        "rerun_exhaustive": bfs.get("exhaustive"),
        "rerun_crash_count": (bfs.get("step_crashes") or {}).get("count"),
        "rerun_search_ceiling": bfs.get("search_ceiling"),
        "carried_an_uncounted_crash": bool(
            (bfs.get("step_crashes") or {}).get("count")),
        "audits_a_committed_claim": False,
    })

    a0_out = a0_instance()             # already written to raw/a0_report_rerun.json
    a0 = a0_out["a0_report"]
    adaptation = a0_out["adaptation"]
    account = a0["mine"]["account"]
    old_a0 = json.load(open(os.path.join(REPO, "a0-spike", "artifacts",
                                         "a0_report.json"), encoding="utf-8"))
    classes = {}
    for rule in old_a0["mine"]["rules"]:
        classes.setdefault((rule["action"], json.dumps(rule["effect"],
                                                       sort_keys=True)), 0)
        classes[(rule["action"], json.dumps(rule["effect"],
                                            sort_keys=True))] += 1
    committed_disjunctive = sum(1 for v in classes.values() if v > 1)
    findings.append({
        "claim": ("a0-spike mined rule set: each disjunctive effect class "
                  "asserts \"this class admits no single conjunctive guard\""),
        "artifact": "a0-spike/artifacts/a0_report.json",
        "committed_claim_ok": "%d of %d effect classes published as disjunctive"
                              % (committed_disjunctive, len(classes)),
        "committed_claim_detail": ("no field in the committed report "
                                   "distinguishes NoSeparatingGuard from a "
                                   "crash; both produced the same rules"),
        "committed_crash_count_field": None,
        "rerun_ok": account["disjunction_is_a_finding"],
        "rerun_crash_count": account["synthesis_crashes"],
        "rerun_no_separating_guard": account["classes_no_separating_guard"],
        "carried_an_uncounted_crash": bool(account["synthesis_crashes"]),
    })

    # --- the denominator, widened (adversarial review, correction 3+6) -------
    # The first pass audited 3 claims. The review pointed out that the audited
    # call site -- `stages.mine` -- also produces the coverage and no-violation
    # fields in `a0_report.json:certify` and in all four `repair` blocks of
    # `adaptation.json`, and that a denominator drawn without them is chosen
    # rather than found. Both are now in.
    old_a0_cert = old_a0["certify"]
    for field in ("replay_exact", "exactly_one_successor"):
        findings.append({
            "claim": "a0-spike certify.%s (replayed through the MINED rules)" % field,
            "artifact": "a0-spike/artifacts/a0_report.json",
            "committed_claim_ok": old_a0_cert.get(field),
            "committed_claim_detail": "%d transitions" % old_a0_cert["transitions"],
            "committed_crash_count_field": None,
            "rerun_ok": a0["certify"][field],
            "rerun_crash_count": a0["certify"]["synthesis_crashes"],
            "carried_an_uncounted_crash": bool(a0["certify"]["synthesis_crashes"]),
        })

    old_adapt_path = os.path.join(REPO, "a0-spike", "artifacts", "adaptation.json")
    old_adapt = json.load(open(old_adapt_path, encoding="utf-8"))
    old_by_variant = {v["variant"]: v["repair"] for v in old_adapt["variants"]}
    for entry in adaptation["variants"]:
        old_repair = old_by_variant.get(entry["variant"], {})
        for field in ("replay_exact", "exactly_one_successor"):
            findings.append({
                "claim": "a0-spike adaptation repair[%s].%s" % (entry["variant"], field),
                "artifact": "a0-spike/artifacts/adaptation.json",
                "committed_claim_ok": old_repair.get(field),
                "committed_claim_detail": "%s transitions re-mined after the "
                                          "variant was injected"
                                          % old_repair.get("transitions"),
                "committed_crash_count_field": old_repair.get("synthesis_crashes"),
                "rerun_ok": entry["repair"][field],
                "rerun_crash_count": entry["repair"]["synthesis_crashes"],
                "carried_an_uncounted_crash": bool(
                    entry["repair"]["synthesis_crashes"]),
            })

    # --- claims deliberately left OUT of the population, with the reason -----
    # The review also listed `certify_generated.replay_exact`, `held_out.exact`
    # and `levels[*].theorem.unsolvable`. Checked rather than assumed: none of
    # them touches the mined rules, so counting them would attribute a defect to
    # a site that has none -- a report saying something the computation did not,
    # which is the same error in the other direction.
    out_of_scope = [
        {"claim": "a0-spike certify_generated.replay_exact",
         "depends_on": "gen_exec.compile_module(theory/theory.dsl) -- "
                       "`certify_generated(module, episodes)` never sees `rules`",
         "value_under_an_injected_mining_crash": True},
        {"claim": "a0-spike held_out.exact",
         "depends_on": "the same compiled module, enumerated against "
                       "world/sokoban2.py; no mined rule is consulted",
         "value_under_an_injected_mining_crash": True},
        {"claim": "a0-spike levels[*].theorem.unsolvable",
         "depends_on": "stages.unsolvability_certificate(level) -- takes only a "
                       "Level and compares two parities; no rules, no search",
         "value_under_an_injected_mining_crash": True},
    ]

    exercised = [f for f in findings if not f.get("not_exercised")]
    committed = [f for f in findings
                 if f.get("audits_a_committed_claim", True)]
    committed_exercised = [f for f in committed if not f.get("not_exercised")]
    summary = {
        "prompt_id": "E14-crash-is-not-a-finding",
        "instance_sets": ["theoria-arm/runs/%s" % RUN_SLUG,
                          "theoria-arm worked example (BFS, unreachable goal)",
                          "a0-spike"],
        "claims_audited": len(findings),
        "committed_claims_audited": len(committed),
        "committed_claims_exercised_by_this_rerun": len(committed_exercised),
        "committed_claims_not_exercised": len(committed) - len(committed_exercised),
        # THE DELIVERABLE NUMBER: of the exhaustiveness claims standing in the
        # committed artifacts, how many were made on top of an uncounted crash.
        "claims_that_carried_an_uncounted_crash": sum(
            1 for f in committed_exercised if f["carried_an_uncounted_crash"]),
        "crashes_observed_anywhere_in_this_rerun": sum(
            f["rerun_crash_count"] or 0 for f in findings),
        "findings": findings,
        "claims_deliberately_out_of_population": out_of_scope,
        "reading": ("A claim is counted as carrying an uncounted crash only if "
                    "the instrumented re-run OBSERVED a crash under it. A claim "
                    "the re-run never reached is reported separately and is NOT "
                    "folded into the clean column -- 'no crash was recorded' and "
                    "'no crash happened' are the two things this whole ticket "
                    "exists to keep apart, and collapsing them here would be "
                    "the same error one level up."),
    }
    _dump("reconciliation.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "findings"},
                     indent=1, ensure_ascii=False))
    for f in findings:
        print("\n- %s" % f["claim"])
        print("    committed: %s" % f["committed_claim_ok"])
        print("    re-run   : ok=%s crashes=%s%s"
              % (f["rerun_ok"], f["rerun_crash_count"],
                 "  [NOT EXERCISED]" if f.get("not_exercised") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
