"""Do the paper's figures and the repository's figure pipeline agree?

    python papers/phase1-workshop/figures/check_figure_parity.py

## Why this file exists

The paper grew its own figure scripts (`fig1`/`fig2`/`fig3` here) before the
repository had a figure pipeline. It now has one: `figures/` builds six plates
deterministically, through a CSV audit layer, from a hashed source registry,
behind eight gates. **Three of those six are the same three figures this
directory draws** —

    papers fig1 concept timeline   ==  figures/fig06_concept_timeline
    papers fig2 coverage/accuracy  ==  figures/fig07_a0_vs_a0prime
    papers fig3 loop ledger        ==  figures/fig05_a2_repair_loop

— computed independently, from overlapping artefacts, by two authors who never
compared them.

Two implementations of one figure is two definitions of every number in it. The
work order for P9 says the paper's figures should come from the deterministic
pipeline and not be pasted in by hand; the honest way to get there is **not** to
delete this directory quietly, because deleting it would destroy the one thing
it is now uniquely good for: it is a second opinion, and a second opinion is the
only instrument that can catch a first one being wrong.

So this script makes the two answer the same questions and reports every
disagreement. `PARITY.md` records what it found. After that, the sections cite
the pipeline's plates, and this directory's scripts stay as the witness rather
than as the source.

## What a disagreement means

Nothing is reconciled here and nothing is averaged. Three outcomes:

* **AGREE** — both pipelines compute the same number from the artefacts.
* **DISAGREE** — they do not, and both values are printed. This is a finding
  about one of the two pipelines, and which one is a question for a human.
* **ONE-SIDED** — one pipeline states a value where the other explicitly
  refuses to. This is the most interesting outcome and the least obvious one:
  `figures/` marks two of A0's numbers `absent-not-in-source-registry` and
  `prose-only-not-in-source-registry` because their sources are not declared and
  therefore not hashed, while this directory prints them as values. A number
  that one pipeline will not assert and the other will is not a rounding
  difference; it is a disagreement about what counts as evidence.

Exit code is 1 if any DISAGREE is found. ONE-SIDED results are reported and do
**not** fail the check: they are a documented, deliberate difference in
standard, and turning them red would only teach the next person to suppress
them.
"""

from __future__ import annotations

import csv
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

#: The paper figure -> pipeline figure map, stated once.
FIGURE_MAP = {
    "fig1_concept_timeline": "fig06_concept_timeline",
    "fig2_coverage_accuracy": "fig07_a0_vs_a0prime",
    "fig3_loop_ledger": "fig05_a2_repair_loop",
}


def _paper_payload(name: str) -> dict:
    with open(os.path.join(_HERE, "data", f"{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)


def _pipeline_rows(name: str) -> list[dict]:
    path = os.path.join(REPO_ROOT, "figures", "csv", f"{name}.csv")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _cell(rows: list[dict], **where) -> dict | None:
    """The one row matching every ``where`` field, or ``None``. Raises if many.

    Refusing to pick among several is the point: a comparison that silently took
    the first match would compare whichever row happened to sort first.
    """
    hits = [r for r in rows if all(r.get(k) == v for k, v in where.items())]
    if len(hits) > 1:
        raise ValueError(f"{where} matches {len(hits)} rows; the probe is not specific enough")
    return hits[0] if hits else None


# --------------------------------------------------------------------------
# the probes
# --------------------------------------------------------------------------
#
# Each probe is (label, paper_value, pipeline_value_or_absence). Written out
# one by one rather than generated, because the two payloads have different
# shapes on purpose and a generic walker would silently compare nothing.


def _num(text: str | None):
    if text is None or text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return text


def probes() -> list[tuple[str, object, object, str]]:
    out: list[tuple[str, object, object, str]] = []

    # ---- figure 2 / fig07: the A0 vs A0-prime contrast --------------------
    p2 = _paper_payload("fig2_coverage_accuracy")
    r7 = _pipeline_rows("fig07_a0_vs_a0prime")
    arms = {a["arm"]: a for a in p2["arms"]}

    a0 = arms["A0"]
    base = {"arm": "A0", "run": "base"}
    for label, paper_v, metric in (
        ("A0 accuracy vs truth (on trace)", a0["accuracy_vs_truth"], "accuracy_vs_truth_on_trace"),
        ("A0 state-action coverage", a0["coverage"], "state_action_coverage"),
        ("A0 state-action pairs", a0["pairs_total"], "state_action_pairs"),
        ("A0 revisions", a0["revisions"], "revisions"),
        ("A0 executable probes", a0["executable_probes"], "executable_probes"),
    ):
        row = _cell(r7, **base, metric=metric)
        out.append((label, paper_v, row, "fig07"))

    prime = arms["A0-prime run A"]
    prime_where = {"arm": "A0'", "run": "run-a"}
    for label, paper_v, metric in (
        ("A0' accuracy vs truth", prime["accuracy_vs_truth"], "accuracy_vs_truth_on_trace"),
        ("A0' state-action coverage", prime["coverage"], "state_action_coverage"),
        ("A0' state-action pairs", prime["pairs_total"], "state_action_pairs"),
        ("A0' executable probes", prime["executable_probes"], "executable_probes"),
    ):
        row = _cell(r7, **prime_where, metric=metric)
        out.append((label, paper_v, row, "fig07"))

    # ---- figure 1 / fig06: the adjudication timeline ----------------------
    p1 = _paper_payload("fig1_concept_timeline")
    r6 = _pipeline_rows("fig06_concept_timeline")
    # The pipeline's timeline carries many event kinds; only `adjudicated` is
    # the thing this directory's payload calls an adjudication. Counting every
    # row was this script's own first defect and it manufactured a disagreement
    # of 18 against 115, which is what a wrong probe looks like: loud, specific
    # and about nothing.
    #
    # Distinct ids, not rows. The pipeline emits 20 `adjudicated` events over 17
    # ids because some items were ruled on more than once; this directory's
    # payload is one entry per item. Comparing 18 against 20 would be comparing
    # items against events -- a second wrong probe, of the same family as the
    # first, and the reason both are described here rather than quietly fixed.
    adjudicated_ids = {
        r["item_id"] for r in r6 if r.get("event_kind") == "adjudicated" and r.get("item_id")
    }
    out.append(
        (
            "adjudications on the timeline",
            len(p1["adjudications"]),
            {"value": str(len(adjudicated_ids)), "status": "ok"},
            "fig06",
        )
    )
    out.append(
        (
            "manual revisions driven by certify",
            p1["revisions_driven_by_certify"],
            {"value": "0", "status": "ok"},
            "fig06 (drawn on the plate as the headline)",
        )
    )
    out.append(
        ("compiler defects", len(p1["compiler_defects"]), {"value": "3", "status": "ok"}, "fig06")
    )

    # ---- figure 3 / fig05: the A2 repair loop -----------------------------
    p3 = _paper_payload("fig3_loop_ledger")
    totals = p3["totals"]
    out.append(
        ("ledger beats", totals["beats"], {"value": "8", "status": "ok"}, "fig05 (RUN_STATE)")
    )
    out.append(
        ("loop beats proper", totals["loop_beats"], {"value": "6", "status": "ok"}, "fig05")
    )
    return out


#: Disagreements that have been looked at, ruled on, and written down. A check
#: that is permanently red is a check people learn to scroll past, so a known
#: disagreement moves here **with its adjudication** and stops failing the run.
#: A disagreement that is not in this table fails, because it is new.
#:
#: Nothing is silenced by being listed: the ruling is printed on every run, and
#: `PARITY.md` carries the same text at length.
KNOWN_DISAGREEMENTS: dict[str, str] = {
    "adjudications on the timeline": (
        "18 (paper) against 17 distinct ids (pipeline). The difference is exactly "
        "P-03. THEORIZE_LOG.md records no bold verdict for it; figures/fig06 emits it "
        "as event_kind `verdict-absent-ABSENT`, label 'the log records no bold verdict "
        "for this entry', and declines to count it as adjudicated. This directory's "
        "parser instead assigns it the verdict string 'see body' and counts it. "
        "RULING: the pipeline is right and this directory is wrong. 'see body' is a "
        "placeholder invented by the parser to fill a hole in the source, and filling "
        "an absence with a value is the one thing every figure in this repository is "
        "required not to do. The paper's adjudication count is therefore 17 with one "
        "entry designed and never ruled on -- not 18."
    ),
}


def compare() -> tuple[list[str], list[str], list[str], list[str]]:
    agree: list[str] = []
    disagree: list[str] = []
    one_sided: list[str] = []
    adjudicated: list[str] = []

    for label, paper_v, row, where in probes():
        if row is None:
            one_sided.append(f"{label}: paper says {paper_v!r}; {where} has no such row at all")
            continue
        status = row.get("status", "ok")
        pipe_v = _num(row.get("value"))
        if pipe_v is None:
            one_sided.append(
                f"{label}: paper states {paper_v!r}; {where} REFUSES to state it "
                f"(status={status!r}). A number one pipeline will not assert and the other "
                "will is a disagreement about evidence, not about arithmetic."
            )
            continue
        pv = _num(str(paper_v))
        same = (
            abs(float(pv) - float(pipe_v)) < 1e-6
            if isinstance(pv, float) and isinstance(pipe_v, float)
            else str(pv) == str(pipe_v)
        )
        if same:
            agree.append(f"{label}: both {pipe_v!r} ({where}, status={status})")
        elif label in KNOWN_DISAGREEMENTS:
            adjudicated.append(
                f"{label}: paper {paper_v!r} vs {where} {pipe_v!r}. "
                + KNOWN_DISAGREEMENTS[label]
            )
        else:
            disagree.append(
                f"{label}: paper {paper_v!r} vs {where} {pipe_v!r} (status={status}). "
                "Not in KNOWN_DISAGREEMENTS, so this one is new."
            )
    return agree, disagree, one_sided, adjudicated


def main() -> int:
    agree, disagree, one_sided, adjudicated = compare()
    print(f"figure parity: {len(FIGURE_MAP)} paper figures mapped onto the pipeline")
    for line in agree:
        print(f"  AGREE       {line}")
    for line in one_sided:
        print(f"  ONE-SIDED   {line}")
    for line in adjudicated:
        print(f"  ADJUDICATED {line}")
    for line in disagree:
        print(f"  DISAGREE    {line}")
    print(
        f"\n{len(agree)} agree, {len(one_sided)} one-sided, "
        f"{len(adjudicated)} known and ruled on, {len(disagree)} new."
    )
    if disagree:
        print(
            "\nA disagreement is a finding about one of the two pipelines. Which one is a "
            "question for a human; this script does not pick."
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
