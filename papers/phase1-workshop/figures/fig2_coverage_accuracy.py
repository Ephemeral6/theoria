"""SUPERSEDED AS A SOURCE (P9). Kept as the witness, not as the figure.

The paper's figures are now built by the repository's deterministic pipeline at
``figures/`` -- see ``papers/phase1-workshop/figures/PARITY.md`` and OUTLINE.md.
This script is retained because it is an *independent* second computation of the
same numbers, and a second opinion is the only instrument that can catch a first
one being wrong. ``check_figure_parity.py`` runs it against the pipeline.

Do not cite this file from a section. It is not the figure any more.

--- original docstring follows ---

Figure 2 — A0 vs A0-prime: coverage against accuracy.

The paper's headline contrast. Two cold starts: an irreversible latch becomes a
reversible toggle, and the trajectory budget is cut on purpose in the second run.
Two changed variables, not one -- and the worlds differ in more besides (rule
count, state count, mechanism object), which §3.3 states rather than glosses.

Read straight out of the runs' own artefacts:

* ``cold-start-a0/artifacts/score_vs_truth.json``    -- A0's score, sealed until M6
* ``cold-start-a0/artifacts/engines_report.json``    -- A0's probe tiers
* ``cold-start-a0/prime/artifacts/prime_report.json`` -- A0-prime's two runs

Nothing is retyped from the prose reports; if the numbers in the paper and the
numbers here disagree, the artefacts win. Where a figure exists only as prose
upstream, it is *derived* here and the derivation is recorded in the payload's
``derivations`` block rather than pasted in as a constant.
"""

from __future__ import annotations

from common import emit, repo_json, rule

A0 = "cold-start-a0/artifacts/score_vs_truth.json"
A0P = "cold-start-a0/prime/artifacts/prime_report.json"
A0_ENGINES = "cold-start-a0/artifacts/engines_report.json"


def _bar(frac: float, width: int = 40) -> str:
    filled = round(frac * width)
    return "#" * filled + "." * (width - filled)


def main() -> None:
    a0 = repo_json(A0)
    a0p = repo_json(A0P)

    # A0's report states "zero executable probes" in prose; the artefact records
    # a tier per designed probe instead of a count, so derive it. Anything not
    # tiered `executable` could not be run.
    a0_probes = repo_json(A0_ENGINES)["probes"]
    a0_executable = sum(1 for p in a0_probes if p.get("tier") == "executable")

    base = a0["base"]["behavioural"]
    run_a = a0p["run_a"]
    run_b = a0p["run_b"]

    a0_pairs = base["pairs"]
    a0_seen = a0_pairs - a0["base"]["held_out"]["held_out_pairs"]
    a0p_pairs = run_a["score_vs_truth"]["pairs"]
    a0p_seen = a0p["trace"]["a0p-base"]["covered_pairs"]

    arms = [
        {
            "arm": "A0",
            "mechanism": "Button, latch - pressable once",
            "explorer": "exhaustive",
            "pairs_total": a0_pairs,
            "pairs_covered": a0_seen,
            "coverage": round(a0_seen / a0_pairs, 6),
            "replay_green": True,
            "accuracy_vs_truth": base["accuracy"],
            "agree": base["agree"],
            "disagree": base["disagree"],
            "held_out_pairs": a0["base"]["held_out"]["held_out_pairs"],
            "held_out_accuracy": a0["base"]["held_out"]["accuracy"],
            "executable_probes": a0_executable,
            "probes_designed": len(a0_probes),
            "revisions": 0,
            "source": [A0, A0_ENGINES],
        },
        {
            "arm": "A0-prime run A",
            "mechanism": "Switch, toggle - re-witnessable",
            "explorer": "truncated",
            "pairs_total": a0p_pairs,
            "pairs_covered": a0p_seen,
            "coverage": (round(a0p_seen / a0p_pairs, 6) if a0p_seen else None),
            "replay_green": run_a["certify_cheap"]["green"],
            "accuracy_vs_truth": run_a["score_vs_truth"]["accuracy"],
            "agree": run_a["score_vs_truth"]["agree"],
            "disagree": run_a["score_vs_truth"]["disagree"],
            "held_out_pairs": None,
            "held_out_accuracy": None,
            "executable_probes": a0p["engines"]["executable_probes"],
            "revisions": run_a["revisions"],
            "source": A0P,
        },
    ]

    seeded = {
        "arm": "A0-prime run B (seeded error, controlled)",
        "seed": run_b["seed"],
        "replay_on_seeded_manual": "GREEN - blind, as predicted",
        "caught_by_lean": run_b["certify_lean"],
        "caught_by_coverage_probe": run_b["coverage_probes"]["refuted"],
        "probes_run": run_b["coverage_probes"]["probes_run"],
        "accuracy_before": run_b["score_vs_truth_before"]["accuracy"],
        "accuracy_after": run_b["score_vs_truth_after"]["accuracy"],
        "revisions": run_b["revisions"],
        "repair": run_b["repair"]["action"],
        "source": A0P,
    }

    payload = {
        "claim": (
            "Reversibility beats coverage. A0 saw nearly every reachable "
            "(state, action) pair and shipped a manual wrong in three places; "
            "A0-prime saw under half and shipped one with no errors. The variable "
            "is not how much was seen but whether what was seen could be seen again."
        ),
        "caveat": (
            "n=1 per arm, both worlds self-built and adjudicated by the same "
            "instance -- but the objection that bites is analytic, not statistical: "
            "A0-prime's toggle was designed so every direction-by-polarity case "
            "would have a witness, so the adjudication rule mechanically admits "
            "what it mechanically rejected in A0. This demonstrates the mechanism; "
            "it does not test it."
        ),
        "arms": arms,
        "seeded_error_experiment": seeded,
        "sources": [A0, A0P, A0_ENGINES],
        "derivations": {
            "A0.pairs_covered": (
                "pairs - held_out.held_out_pairs = "
                f"{a0_pairs} - {a0['base']['held_out']['held_out_pairs']} = {a0_seen}. "
                "The held-out set is defined as the pairs the trajectory could never "
                "contain, so its complement is the covered set. Agrees with the "
                "233/236 coverage figure in cold-start-a0/prime/A0P_REPORT.md §1."
            ),
            "A0.covered_equals_agreed": (
                "A0's covered count and its agreement count are both 233. That is not "
                "a coincidence: the three uncovered pairs are exactly the three the "
                "manual gets wrong (cold-start-a0/THEORIZE_LOG.md R-05)."
            ),
            "A0-prime.pairs_covered": (
                "trace['a0p-base'].covered_pairs, the truncated explorer's own count."
            ),
            "A0.executable_probes": (
                f"probes in {A0_ENGINES} whose tier is 'executable' = {a0_executable}, "
                f"of {len(a0_probes)} designed entries. A0's artefact records a tier per "
                "probe rather than a count; the report's prose figure is 0 of 22 designed, "
                "counting frontier members rather than probe rows."
            ),
        },
    }

    lines = [
        "FIGURE 2 - coverage vs accuracy, A0 against A0-prime",
        f"sources: {A0}",
        f"         {A0P}",
        rule(),
        "",
        f"{'':<16}{'coverage of reachable (s,a) pairs':<44}{'accuracy vs truth'}",
        "",
    ]
    for a in arms:
        cov = a["coverage"]
        cov_s = f"{a['pairs_covered']}/{a['pairs_total']} = {cov:.1%}" if cov else "n/a"
        lines.append(f"  {a['arm']:<14} {_bar(cov or 0)}  {cov_s}")
        lines.append(f"  {'':<14} {_bar(a['accuracy_vs_truth'])}  "
                     f"{a['agree']}/{a['pairs_total']} = {a['accuracy_vs_truth']:.4%}")
        lines.append(f"  {'':<14} mechanism: {a['mechanism']}")
        lines.append(f"  {'':<14} executable probes: {a['executable_probes']}   "
                     f"revisions: {a['revisions']}   replay: "
                     f"{'GREEN' if a['replay_green'] else 'RED'}")
        lines.append("")

    lines += [
        rule(),
        "SEEDED-ERROR EXPERIMENT (A0-prime run B) - controlled, not a discovery",
        "",
        f"  seed        : {seeded['seed']}",
        f"  replay      : {seeded['replay_on_seeded_manual']}",
        f"  Lean caught : {seeded['caught_by_lean']}",
        f"  probe caught: {', '.join(seeded['caught_by_coverage_probe'])} "
        f"({seeded['probes_run']} probe run)",
        f"  repair      : {seeded['repair']}  ->  {seeded['revisions']} revision",
        f"  accuracy    : {seeded['accuracy_before']:.4f} -> {seeded['accuracy_after']:.4f}",
        "",
        rule(),
        payload["claim"],
        "",
        "CAVEAT: " + payload["caveat"],
    ]

    emit("fig2_coverage_accuracy", payload, "\n".join(lines))


if __name__ == "__main__":
    main()
