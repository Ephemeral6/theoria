"""Render the committed documents: `METRICS.md` and `audit/REDUNDANCY.md`.

The metric reference is generated rather than written, so a definition and its
documentation cannot drift apart: `tests/test_docs.py` fails if the committed
file stops matching the code. Regenerate with

    python -m battery.docs
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from battery.audit.gaming import GAMING_REGISTER, tier_of
from battery.audit.redundancy import as_markdown
from battery.metrics import FAMILIES, REGISTRY, cards_by_family

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "METRICS.md")
VALIDATION = os.path.join(HERE, "artifacts", "validation_material.json")
REDUNDANCY_TARGET = os.path.join(HERE, "audit", "REDUNDANCY.md")
REDUNDANCY = os.path.join(HERE, "artifacts", "redundancy.json")
DISCRIMINATION_ARMS = os.path.join(HERE, "artifacts",
                                   "discrimination_arms.json")


def _validation(path: str = VALIDATION) -> Dict[str, str]:
    """The 验证材料 column, read back from the last recompute.

    Generated rather than written, for the same reason the rest of this file
    is: a hand-maintained provenance column is a claim about the code, and
    this one is a record of what the code did.  A metric that has never been
    computed on a control arm says so here, in the table, next to its tier --
    which is the only place a reader is guaranteed to look.
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return {mid: row.get("summary", "")
            for mid, row in (doc.get("metrics") or {}).items()}

def _sign_test_games_needed(alpha: float = 0.05) -> int:
    """Non-tied paired games an exact two-sided sign test needs to reach alpha.

    Recomputed here from the same formula `audit/stats.py::sign_test` uses for
    `min_attainable_p` (2 / 2**n) rather than copied as a constant, so the
    headline in `METRICS.md` cannot outlive a change to the test.
    """
    n = 1
    while 2.0 / (2 ** n) > alpha:
        n += 1
    return n


def _non_tied(entry: Dict[str, object]) -> int:
    """The sign test's `n` for one metric: paired games minus exact ties.

    Shared with `verify.py`'s fourth rung so the two cannot disagree about
    which count the `2/2**n` arithmetic is a function of.
    """
    test = entry.get("sign_test") or {}
    n = test.get("n") if isinstance(test, dict) else None
    return n if isinstance(n, int) else 0


def _discrimination(path: str = DISCRIMINATION_ARMS) -> str:
    """The process-1 headline: how many metrics actually separated anything.

    Generated for the same reason the 验证材料 column is (see `_validation`),
    and added because the per-metric column was not enough on its own. A reader
    scanning 38 rows of `process 1: underpowered` / `no-data` has no way to see
    that the *total* is zero, and the battery was in fact being reported
    elsewhere as substantially validated while separating nothing at all.

    The block also states the ceiling, because the zero is not a measurement.
    The verdict ladder in `audit/discriminate.py` tests `min_attainable_p >
    0.05` before it looks at any effect size, so on a four-game development
    pile with game-level pairing every metric holding data lands in
    `underpowered` by arithmetic, and `discriminating` is unreachable for all
    of them. Reporting the zero without the ceiling would invite a reader to
    conclude the metrics failed a test they were never able to sit.
    """
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    metrics: Dict[str, Dict[str, object]] = doc.get("metrics") or {}
    if not metrics:
        return ""

    by_verdict: Dict[str, List[str]] = {}
    for metric_id, entry in sorted(metrics.items()):
        by_verdict.setdefault(str(entry.get("verdict")), []).append(metric_id)

    total = len(metrics)
    separating = by_verdict.get("discriminating", [])
    needed = _sign_test_games_needed()
    # **Non-tied** pairs, not paired games.  `2/2**n` is a function of the
    # sign test's `n`, which drops exact ties (`audit/stats.py:153-156`), and
    # three of the metrics scored here already lose a pair that way -- their
    # floor is 0.25, not 0.125.  Reading `n_paired_games` here would overstate
    # the power available and, once the pile grows, would call the ceiling
    # stale one tie before it actually is.
    paired = max((_non_tied(e) for e in metrics.values()), default=0)

    # The denominator, derived rather than argued.  "0 of 38" is true as
    # written and false as read: a metric that was never computed on both arms
    # did not fail to separate, it was never asked.  `tested` is the set that
    # was actually put to the question -- a declared direction *and* enough
    # paired games to pair at all.
    def _paired(entry):
        return int(entry.get("n_paired_games") or 0)

    neutral = [m for m, e in metrics.items() if e.get("direction") == "neutral"]
    tested = sorted(m for m, e in metrics.items()
                    if e.get("direction") != "neutral" and _paired(e) >= 2)
    # How much the diagnostic flag actually costs the denominator, as opposed
    # to how much it appears to cost: a neutral metric with no paired data
    # would have been excluded by the data anyway.
    neutral_with_data = sorted(m for m in neutral if _paired(metrics[m]) >= 2)

    order = ["discriminating", "underpowered", "wrong-direction", "no-effect",
             "no-data", "not-ranked"]
    seen = list(order) + sorted(v for v in by_verdict if v not in order)

    lines = [
        "## Process 1 — what this battery has actually separated\n",
        "**%d of %d metrics separate the specified capability gradient "
        "(%s).**\n" % (len(separating), total, doc.get("gradient", "unknown")),
        "| process-1 verdict | n | metrics |",
        "|---|---|---|",
    ]
    for verdict in seen:
        ids = by_verdict.get(verdict)
        if not ids:
            continue
        lines.append("| `%s` | %d | %s |"
                     % (verdict, len(ids), ", ".join("`%s`" % m for m in ids)))
    lines.append("")
    lines.append(
        "**The zero is a ceiling, not a result.** `audit/stats.py` puts the\n"
        "smallest attainable two-sided p at `2 / 2**n`, over the sign test's\n"
        "**non-tied** `n`, and `audit/discriminate.py` reaches `underpowered`\n"
        "whenever that floor exceeds 0.05 — before the effect size can license\n"
        "anything. Clearing 0.05 needs **%d** non-tied paired games; the\n"
        "development pile is four games and the best-covered metric here\n"
        "manages **%d** (metrics losing a pair to an exact tie do worse still,\n"
        "with a floor of 0.25). So on this pile, with game-level pairing,\n"
        "`discriminating` is unreachable for every metric no matter how\n"
        "cleanly it separates — rerunning the identical pass returns this same\n"
        "zero by arithmetic. It is evidence about the design, not about the\n"
        "metrics.\n" % (needed, paired))
    lines.append(
        "**The denominator is %d, not %d.** Only %d metric%s carried both a\n"
        "declared direction and enough paired games to be put to the question\n"
        "at all (%s). The other %d were never asked: %d are `neutral`\n"
        "diagnostics that rank nothing by construction, and the rest have no\n"
        "paired control-arm material — whole families of them, because no\n"
        "baseline control arm carries an explicit theory or a repair record.\n"
        "Note what that decomposition says about the diagnostic flag: it costs\n"
        "the tested denominator only %d metric%s (%s), because the remaining\n"
        "neutral%s had no paired data to be tested on regardless. The battery\n"
        "is not hiding failures behind `neutral`; it is short of material.\n"
        % (len(tested), total, len(tested), "" if len(tested) == 1 else "s",
           ", ".join("`%s`" % m for m in tested),
           total - len(tested), len(neutral),
           len(neutral_with_data), "" if len(neutral_with_data) == 1 else "s",
           ", ".join("`%s`" % m for m in neutral_with_data) or "none",
           " one" if len(neutral) - len(neutral_with_data) == 1 else "s"))
    # The sharpest true thing in this block, and the one a reader is least
    # likely to reconstruct: eligibility for the gradient and eligibility for
    # an ordering claim are different gates, and almost nothing passes both.
    main_tested = [m for m in tested if tier_of(m) == "main"]
    main_all = [m for m in REGISTRY if tier_of(m) == "main"]
    lines.append(
        "**And %d of those %d %s `main` tier — because the main table holds %d\n"
        "metric%s in total.** Process 1 is not the only gate a metric has to\n"
        "pass to carry an ordering claim: the anti-gaming audit demotes\n"
        "anything an arm could optimise by accident with no defence\n"
        "implemented, and this document's rule is that `reference` metrics are\n"
        "excluded from ordering claims entirely. After the V9 adversarial\n"
        "review that demotion emptied the table. So the set that is both\n"
        "eligible for the specified gradient and admissible for an ordering\n"
        "claim is **empty**, and it would still be empty if the pile were\n"
        "large enough to power the test. Any reading of the effect sizes below\n"
        "that reaches for the large clean ones (%s) is reaching for\n"
        "`reference` metrics, which this battery has already said may not\n"
        "carry an ordering. **This is the more binding of the two limits, and\n"
        "unlike the power ceiling it is not fixed by more games.**\n"
        % (len(main_tested), len(tested),
           "is" if len(main_tested) == 1 else "are",
           len(main_all), "" if len(main_all) == 1 else "s",
           ", ".join("`%s`" % m for m in tested)))
    lines.append(
        "**How to say this in a paper.** Not *\"the battery is validated\"*, and\n"
        "not *\"the metrics failed\"*. `0 of %d` is true as written and false as\n"
        "read. The defensible sentence is: *of %d registered metrics only %d\n"
        "were eligible for the specified gradient; none reached significance,\n"
        "but on four paired games the smallest attainable two-sided p is 0.125\n"
        "at best and 0.25 where a pair ties, so this is a power ceiling and not\n"
        "a null result.* Process 1 is **undetermined**, not negative. The\n"
        "effect sizes in\n"
        "`artifacts/discrimination_arms.json` are the only quantities here\n"
        "anyone should read — including the ones pointing the wrong way, which\n"
        "a bare verdict tally hides.\n" % (total, total, len(tested)))
    return "\n".join(lines)


FAMILY_TITLES = {
    "exploration": "探索 · Exploration — systematic, or circling?",
    "planning": "计划 · Planning — is a decision buying more actions?",
    "economy": "经济 · Economy — the shape of the bill",
    "mechanism": "机制 · Mechanism — seen it, then used it, how long between?",
    "epistemic": "认识 · Epistemic — the quality of the books themselves",
}

PREAMBLE = """# METRICS — battery v1

**Generated from the code by `python -m battery.docs`. Do not edit by hand;
edit the metric and regenerate.** `tests/test_docs.py` fails if this file and
the registry disagree.

Five families, per `Theoria.md` Phase 2. Each metric carries a declared
direction — whether higher or lower is the more capable reading — so that no
ordering can be flipped after the numbers are in.

**Tier** is decided mechanically by the anti-gaming audit
(`battery/audit/gaming.py`), not by opinion:

> a metric an arm could optimise **by accident**, with **no defence implemented
> in the battery**, is demoted to `reference`.

Demotion is not deletion. Reference metrics are computed, reported and
correlated; they are excluded from ordering claims and from the main table.
`neutral`-direction metrics are diagnostics: they describe a run without
ranking it, and are never used in an ordering at all.

**验证材料 / validation material** is new in v1, and it is the column to read
before believing any other. `Theoria.md` Phase 2 process 1 says validation uses
the **control arms only** — 验证只用对照两臂，与 Theoria 无关 — so a metric
computed on a Theoria arm is *computable*, not *validated*. This column reports
control-arm runs and the process-1 verdict, and is generated from the recompute
rather than asserted, so it cannot drift from what actually happened.

A metric reading `none — never computed on a control arm` has not been shown to
separate anything. `Theoria.md` is blunt about what that means:
分不开已知差异的指标，没资格测未知差异.
"""


def render() -> str:
    lines: List[str] = [PREAMBLE]
    validation = _validation()

    main = sorted(m for m in REGISTRY if tier_of(m) == "main")
    reference = sorted(m for m in REGISTRY if tier_of(m) == "reference")
    lines.append("**Main table (%d):** %s\n" % (len(main), ", ".join(main)))
    lines.append("**Reference (%d):** %s\n" % (len(reference),
                                               ", ".join(reference)))
    if validation:
        never = sorted(m for m in REGISTRY
                       if validation.get(m, "").startswith("none"))
        lines.append("**Never validated on a control arm (%d):** %s\n"
                     % (len(never), ", ".join(never) or "—"))
    lines.append("---\n")

    discrimination = _discrimination()
    if discrimination:
        lines.append(discrimination)
        lines.append("---\n")

    by_family = cards_by_family()
    for family in FAMILIES:
        lines.append("## %s\n" % FAMILY_TITLES[family])
        lines.append("| id | direction | tier | needs | 验证材料 | definition |")
        lines.append("|---|---|---|---|---|---|")
        for card in by_family[family]:
            lines.append("| `%s` | %s | %s | %s | %s | %s |" % (
                card.metric_id, card.direction, tier_of(card.metric_id),
                ", ".join(card.needs) or "—",
                validation.get(card.metric_id, "not computed"),
                card.definition.replace("|", "\\|")))
        lines.append("")

        lines.append("**How each would be gamed.**\n")
        for card in by_family[family]:
            entry = GAMING_REGISTER[card.metric_id]
            lines.append("* **`%s`** — %s" % (card.metric_id,
                                              entry["how_to_game"]))
            lines.append("  *Accidental:* %s. *Defence:* %s %s" % (
                "yes" if entry["accidental"] else "no",
                entry["defence"],
                "(implemented)" if entry["defended"]
                else "**(not implemented — demoted)**"
                if entry["accidental"] else "(implemented)"))
        lines.append("")

    lines.append("---\n")
    lines.append("## Deviations from `Theoria.md` Phase 2\n")
    lines.append(
        "* **X4** is normalised by run length. The runs in hand differ in\n"
        "  length by a factor of twenty, and a raw streak would rank a long run\n"
        "  above a short one for no reason but its length.\n"
        "* **P4** additionally requires the run to have been *trying to win*.\n"
        "  A0's 275-step coverage walk scores 22.9x optimal against its\n"
        "  12-step plan, which measures the trace's purpose, not the arm.\n"
        "* **E2 / E3** require at least eight turns. A run that ends on turn\n"
        "  four spent all its money in its first quarter and looks maximally\n"
        "  front-loaded while having understood nothing. This matters more\n"
        "  here than elsewhere: the front-load index is a Phase 4 primary\n"
        "  endpoint.\n"
        "* **The turn axis is the decision, not the model call.** v0 used\n"
        "  model-call order because the ledger carries no turn index. That\n"
        "  counted a retried decision as several turns: one pilot run bills\n"
        "  three model calls at one step, with three different prices. v1\n"
        "  groups calls onto the step they were deciding for E2/E3, and leaves\n"
        "  E1 on the billing axis, because the money was really spent.\n"
        "  `INPUT_FORMAT.md` gap 5 is still open upstream.\n"
        "* **E7 duplicates E4 on a different axis** rather than replacing it.\n"
        "  E4 fits curvature to context *tokens*, which are constant by\n"
        "  construction on a one-shot-CLI arm and therefore measure the\n"
        "  harness. E7 fits the same curvature to prompt size, which is the\n"
        "  axis that grows. Both are kept so the discrepancy stays visible.\n"
        "* **K13's currency is environment actions**, because no producer in\n"
        "  the repository records tokens, wall time or model calls for a\n"
        "  repair. `Theoria.md` does not fix a unit for U4; this is the unit\n"
        "  the artefacts can support, not the most informative one.\n")
    return "\n".join(lines).rstrip() + "\n"


def write(path: str = TARGET) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render())
    return path


def write_redundancy(path: str = REDUNDANCY_TARGET,
                     source: str = REDUNDANCY) -> Optional[str]:
    """Process 3's basis, rendered from the last recompute's artefact.

    Generated here rather than by `run_battery` because this is a *committed
    document*, and a recompute may legitimately be pointed elsewhere with
    `--out`. While `run_battery` wrote it to a fixed path,
    `tests/test_determinism.py` — which runs the real pipeline over a small
    fixture — silently replaced the real audit document with a three-cluster
    version computed from six runs, every time the suite ran.
    """
    if not os.path.exists(source):
        return None
    with open(source, "r", encoding="utf-8") as fh:
        result = json.load(fh)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(as_markdown(result))
    return path


if __name__ == "__main__":
    print(write())
    written = write_redundancy()
    if written:
        print(written)
