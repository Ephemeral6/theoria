"""Emit the pre-registration artefacts for endpoint 2.

    python -m exam.tools.build_prereg          # writes artifacts/prereg/ + controls

Four files, and each answers one question a reader should not have to read code
to answer:

    prereg/verdict_prereg.json          what was promised, and does the paper
                                        still match it
    prereg/verdict_class_inventory.md   which of Theoria.md 1.11's three classes
                                        have items, on what constructive basis
    prereg/verdict_negative_controls.md what the gate refuses, and which floor
                                        does the refusing
    endpoint_controls/*.answers.json    the transcripts those refusals were
                                        computed from, on disk, so a launch
                                        gate can point at a file

Deterministic by construction: no clock, no absolute paths, no iteration over a
set.  `exam/verify.py` runs it into a shadow tree and `check_artifacts_match`
compares the result byte for byte against what is committed.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Sequence

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import endpoint as ep                                     # noqa: E402
from exam import prereg                                            # noqa: E402
from exam.grading.registry import digest                           # noqa: E402
from exam.model import ARTIFACTS, artifact_rel, read_json, write_json  # noqa: E402
from exam.papers import module_for                                 # noqa: E402
from exam.tools import endpoint_verdict as ev                      # noqa: E402

PREREG_DIR = os.path.join(ARTIFACTS, "prereg")


def _spec_of(truth: Dict[str, Any]) -> Dict[str, Any]:
    """The variant spec behind an item, read from the emitted spec file.

    Theoria.md:289 requires 构造性依据 -- *why* the variant is unsolvable by
    construction, not because a run failed.  The justification is a field of the
    spec, so the inventory quotes the spec rather than restating it, and a spec
    that stops existing is a missing file rather than a stale paragraph.
    """
    spec = truth.get("spec")
    if isinstance(spec, str):                     # truth files stringify it
        import ast
        spec = ast.literal_eval(spec)
    path = os.path.join(REPO, spec["spec_file"]) if spec else None
    if path and os.path.isfile(path):
        return read_json(path)
    # A spec_file path is relative to the repo when the artefacts sit in their
    # tracked place and relative to the shadow root when they do not, so the
    # second attempt is not paranoia, it is the redirect.
    if spec:
        alt = os.path.join(ARTIFACTS, os.path.basename(
            os.path.dirname(spec["spec_file"])), os.path.basename(spec["spec_file"]))
        if os.path.isfile(alt):
            return read_json(alt)
    return {}


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        import ast
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
    return {}


def inventory() -> Dict[str, Any]:
    """One row per item: class, basis, and what the basis is allowed to claim."""
    module = module_for("verdict")
    paper = module.build()
    key_doc = paper.key(digest())
    rows: List[Dict[str, Any]] = []
    for entry in key_doc["items"]:
        truth = entry["truth"]
        spec = _spec_of(truth)
        state = _as_dict(truth.get("state_space"))
        cert = _as_dict(truth.get("certificate_blob"))
        rows.append({
            "item_id": entry["item_id"],
            "class": truth["class"],
            "board_size_class": truth["board_size_class"],
            "claim": truth["claim"],
            "variant_id": spec.get("variant_id"),
            "base_level": spec.get("base_level"),
            "operators": [op.get("op") for op in spec.get("operators", [])],
            "constructive_justification": spec.get("justification"),
            "naive_enumeration_feasible": state.get("naive_enumeration_feasible"),
            "enumeration_attempted": state.get("enumeration_attempted"),
            "enumerated": state.get("enumerated"),
            "lower_bound": state.get("lower_bound"),
            "positional_states": state.get("positional_states"),
            "certificate_kind": cert.get("kind"),
            "witness_source": truth.get("witness_source"),
            "search_credible": truth.get("search_credible"),
        })
    rows.sort(key=lambda r: (r["class"], r["item_id"]))
    return {"paper_id": paper.paper_id, "rubric_digest": digest(), "items": rows}


CLASS_HEADERS = {
    "small_unsolvable": (
        "(i) small-space unsolvable",
        "Exhaustive search is feasible and is *measured* to be: every item's "
        "state space is enumerated at build time and the count and cap are in "
        "the truth file. What the class scores is the reason -- a certificate "
        "against 'I searched and did not find' -- because a complete searcher "
        "stops correctly here too, and a searcher with a missing edge stops "
        "correctly for a reason that is false."),
    "large_unsolvable": (
        "(ii) large-space unsolvable",
        "**The claim this class carries is narrower than Theoria.md 1.11's.** "
        "What is established is `naive_enumeration_feasible: False` -- forward "
        "enumeration over the full (cart, button, latch mask) state, the method "
        "class (i) is graded on, cannot terminate against a constructive bound "
        "of 2^60 to 2^120. What is **withdrawn** is 唯不变量推理能答: every "
        "shipped item of this class is settled by an exhaustive computation "
        "over at most 600 nodes, and each of the four is settled by a different "
        "one. So the class measures **method selection under an apparent search "
        "barrier**. D-EX-028."),
    "solvable_hard": (
        "(iii) solvable but hard",
        "The false-positive trap. Every item carries a witness plan that was "
        "computed and replayed rather than asserted, and the key records "
        "whether the witness came from a search or a construction -- a plan "
        "that wins proves solvability however it was found, but on a paper "
        "whose premise is 由构造即知答案 the key has to say which."),
}


def render_inventory(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# 判决题 · class inventory and constructive basis")
    lines.append("")
    lines.append("paper `%s`, rubric digest `%s`"
                 % (data["paper_id"], data["rubric_digest"][:12]))
    lines.append("")
    lines.append("Theoria.md:289 requires a **构造性依据** for every variant: "
                 "why it is unsolvable *by construction*, never because a run "
                 "failed. The `justification` column is the variant spec's own "
                 "field, quoted, not a restatement.")
    lines.append("")
    by_class: Dict[str, List[Dict[str, Any]]] = {}
    for row in data["items"]:
        by_class.setdefault(row["class"], []).append(row)
    for klass in ("small_unsolvable", "large_unsolvable", "solvable_hard"):
        rows = by_class.get(klass, [])
        title, blurb = CLASS_HEADERS[klass]
        lines.append("## %s — %d item%s"
                     % (title, len(rows), "" if len(rows) == 1 else "s"))
        lines.append("")
        lines.append(blurb)
        lines.append("")
        lines.append("| item | variant | operators | claim | naive enum | bound / enumerated "
                     "| relaxed nodes | certificate | witness |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for row in rows:
            enumerated = row["enumerated"]
            bound = row["lower_bound"]
            size = ("%s states, enumerated" % enumerated if enumerated is not None
                    else "2^m = %.3g, by construction" % float(bound)
                    if bound is not None else "--")
            lines.append("| `%s` | `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
                row["item_id"], row["variant_id"] or "--",
                ", ".join("`%s`" % o for o in row["operators"]) or "--",
                row["claim"],
                {True: "feasible", False: "**out of reach**", None: "--"}[
                    row["naive_enumeration_feasible"]
                    if isinstance(row["naive_enumeration_feasible"], bool) else None],
                size, row["positional_states"],
                "`%s`" % row["certificate_kind"] if row["certificate_kind"] else "--",
                row["witness_source"] or "--"))
        lines.append("")
        for row in rows:
            if row["constructive_justification"]:
                lines.append("* **`%s`** (`%s`): %s"
                             % (row["item_id"], row["variant_id"],
                                row["constructive_justification"]))
        lines.append("")
    lines.append("## What class (ii) cannot be given, and why it is not an oversight")
    lines.append("")
    lines.append(
        "Every unsolvable item on this paper carries a certificate in the "
        "closed grammar (`invariant` / `cut_set` / `counting`), and checking one "
        "is polynomial in the board. That is not a weakness of these four items; "
        "it is what 构造性依据 *means*. A variant whose unsolvability we know by "
        "construction has, by definition, a short proof — and a short proof in a "
        "checkable grammar is a cheap decision procedure for that instance. So "
        "\"the state space defeats exhaustive search\" and \"the truth is known "
        "by construction\" pull against each other, and the second is the one "
        "Theoria.md:289 makes non-negotiable.")
    lines.append("")
    lines.append(
        "The operator library is the second constraint and it is the harder one. "
        "The wrapper-legal set is `forbid_action`, `remap_action`, `step_limit`, "
        "`observation_loss` and `win_tighten` — all five are monotone: they "
        "remove behaviour, they never make a latched switch un-latch. A world "
        "whose latches only ever latch has a monotone reachability structure, "
        "which is exactly the structure that relaxations settle for free. To "
        "build a level where a relaxation returns *unknown* one needs a "
        "**non-monotone** dynamic — a toggle, a consumable resource, a door that "
        "can re-close — and no wrapper can introduce one: the hosted environment "
        "owns the dynamics and the wrapper sits outside it (Theoria.md Phase 1, "
        "包裹合法集).")
    lines.append("")
    lines.append(
        "**So the honest statement is the one shipped**: class (ii) items have a "
        "constructive lower bound of 2^60 to 2^120 that defeats the naive "
        "enumerator, and an apparent search barrier that a method-selecting "
        "examinee can walk around. What it would take to close the gap is a "
        "non-monotone operator in the legal set, which is a change to the "
        "environment proxy and not to this paper — filed rather than asserted, "
        "and until it exists the claim stays withdrawn.")
    lines.append("")
    return "\n".join(lines)


def render_controls(table: Dict[str, Any], loo: Dict[str, List[str]]) -> str:
    lines: List[str] = []
    lines.append("# 判决题 · the negative controls, and which floor catches which")
    lines.append("")
    lines.append("paper `%s`, rubric digest `%s`"
                 % (table["paper_id"], table["rubric_digest"][:12]))
    lines.append("")
    lines.append("Thresholds: `S_min` %.2f, `c_min` %.2f, BA > %.2f. Rates are "
                 "computed **after 弃权计错** (`exam/endpoint.py`); the observed "
                 "rates the marker reports are beside them, and the two differ "
                 "exactly where an examinee declined to answer."
                 % (table["thresholds"]["S_min"], table["thresholds"]["c_min"],
                    table["thresholds"]["ba_floor"]))
    lines.append("")
    lines.append("| examinee | sens | spec | BA | observed sens | observed spec "
                 "| class (ii) coverage | certified share | verdict |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    def num(value: Any) -> str:
        return "--" if value is None else "%.3f" % value

    for name, row in table["controls"].items():
        lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | **%s** |" % (
            name, num(row["sensitivity"]), num(row["specificity"]),
            num(row["balanced_accuracy"]), num(row["observed_sensitivity"]),
            num(row["observed_specificity"]),
            num(row["class_ii_coverage_positive"]),
            num(row["certified_share"]), row["verdict"]))
    lines.append("")
    lines.append("## Leave one floor out")
    lines.append("")
    lines.append("Each floor is disabled in turn and every control re-judged. "
                 "A floor that changes no verdict when it is removed has never "
                 "been observed to do anything.")
    lines.append("")
    lines.append("| floors in force | controls credited |")
    lines.append("|---|---|")
    for key in ("all_floors", "without_S_min", "without_c_min", "without_ba_floor"):
        credited = loo[key]
        lines.append("| `%s` | %s |" % (key, ", ".join("`%s`" % c for c in credited)
                                        or "none"))
    lines.append("")
    lines.append(
        "**This table was wrong when it was first written.** `S_min` was "
        "described as catching `abstainer` and `null`; disabling it changed no "
        "verdict, because both of those fail the BA floor as well. `overclaimer` "
        "— `unsolvable` everywhere except three solvable items, sensitivity "
        "1.000, specificity 0.375, BA 0.688 — was constructed afterwards to be "
        "the case only the specificity floor refuses. Each floor now catches "
        "exactly one control on its own.")
    lines.append("")
    lines.append("## The one it credits that it should not")
    lines.append("")
    lines.append(
        "`cheater-v4` is a real transcript: a reader handed the sheet and "
        "nothing else. It is identical to `oracle` in every gated number and is "
        "**credited**. The only column that separates them is `certified share` "
        "— 0.000 against 1.000 — and `freeze/STATS_RULES.md` §2.2 demotes "
        "exactly that column to exploratory while citing 这里考的是理由 as its "
        "reason. exam reports the number on every transcript and has proposed "
        "the amendment through `monitor/inbox/`; legislating it here would be "
        "one territory overruling a frozen document from inside its own.")
    lines.append("")
    return "\n".join(lines)


def build() -> List[str]:
    written: List[str] = []
    os.makedirs(PREREG_DIR, exist_ok=True)

    written.extend(ev.emit_controls())

    table = ev.table()
    loo = prereg.floor_leave_one_out()
    inv = inventory()

    doc = {
        "prereg": prereg.PREREG,
        "paper_check_failures": prereg.check(),
        "control_check_failures": prereg.check_controls(),
        "control_table": table,
        "floor_leave_one_out": loo,
        "class_inventory": inv,
        "control_transcripts": [artifact_rel(p) for p in written],
    }
    path = os.path.join(PREREG_DIR, "verdict_prereg.json")
    write_json(path, doc)
    written.append(path)

    for name, text in (("verdict_class_inventory.md", render_inventory(inv)),
                       ("verdict_negative_controls.md",
                        render_controls(table, loo))):
        path = os.path.join(PREREG_DIR, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(path)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    failures = prereg.check() + prereg.check_controls()
    for path in build():
        print("wrote %s" % artifact_rel(path))
    if failures:
        print("\nRED: the pre-registration does not match the paper it registers")
        for line in failures:
            print("  - %s" % line)
        return 1
    print("pre-registration matches the built paper and every control was "
          "judged as pre-registered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
