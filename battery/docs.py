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
