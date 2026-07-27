"""Render `METRICS.md` from the registry.

The metric reference is generated rather than written, so a definition and its
documentation cannot drift apart: `tests/test_docs.py` fails if the committed
file stops matching the code. Regenerate with

    python -m battery.docs
"""

from __future__ import annotations

import os
from typing import List

from battery.audit.gaming import GAMING_REGISTER, tier_of
from battery.metrics import FAMILIES, REGISTRY, cards_by_family

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "METRICS.md")

FAMILY_TITLES = {
    "exploration": "探索 · Exploration — systematic, or circling?",
    "planning": "计划 · Planning — is a decision buying more actions?",
    "economy": "经济 · Economy — the shape of the bill",
    "mechanism": "机制 · Mechanism — seen it, then used it, how long between?",
    "epistemic": "认识 · Epistemic — the quality of the books themselves",
}

PREAMBLE = """# METRICS — battery v0

**Generated from the code by `python -m battery.docs`. Do not edit by hand;
edit the metric and regenerate.** `tests/test_docs.py` fails if this file and
the registry disagree.

Five families and twenty-eight metrics, per `Theoria.md` Phase 2. Each carries
a declared direction — whether higher or lower is the more capable reading —
so that no ordering can be flipped after the numbers are in.

**Tier** is decided mechanically by the anti-gaming audit
(`battery/audit/gaming.py`), not by opinion:

> a metric an arm could optimise **by accident**, with **no defence implemented
> in the battery**, is demoted to `reference`.

Demotion is not deletion. Reference metrics are computed, reported and
correlated; they are excluded from ordering claims and from the main table.
`neutral`-direction metrics are diagnostics: they describe a run without
ranking it, and are never used in an ordering at all.
"""


def render() -> str:
    lines: List[str] = [PREAMBLE]

    main = sorted(m for m in REGISTRY if tier_of(m) == "main")
    reference = sorted(m for m in REGISTRY if tier_of(m) == "reference")
    lines.append("**Main table (%d):** %s\n" % (len(main), ", ".join(main)))
    lines.append("**Reference (%d):** %s\n" % (len(reference),
                                               ", ".join(reference)))
    lines.append("---\n")

    by_family = cards_by_family()
    for family in FAMILIES:
        lines.append("## %s\n" % FAMILY_TITLES[family])
        lines.append("| id | direction | tier | needs | definition |")
        lines.append("|---|---|---|---|---|")
        for card in by_family[family]:
            lines.append("| `%s` | %s | %s | %s | %s |" % (
                card.metric_id, card.direction, tier_of(card.metric_id),
                ", ".join(card.needs) or "—",
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
        "* **The turn axis is model-call order**, because the ledger carries no\n"
        "  turn index. `INPUT_FORMAT.md` gap 5.\n")
    return "\n".join(lines).rstrip() + "\n"


def write(path: str = TARGET) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render())
    return path


if __name__ == "__main__":
    print(write())
