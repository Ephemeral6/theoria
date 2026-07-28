"""Figure 1 — the concept-birth timeline of the A0 manual.

Source of truth: ``cold-start-a0/THEORIZE_LOG.md``. Every adjudication in that
file is a heading of the shape

    ### R-05 Direction generality of `press_left` ... -> **reject, probe-pending**

so the timeline is *parsed out of the adjudication record itself* rather than
re-typed. Two further tables in the same file supply the revision history (what
changed the manual, and what triggered it) and the compiler-defect log (the
iterations that did happen, in the compiler rather than in the manual).

What the figure is meant to show: the manual was revised **zero** times by
certify, and every iteration that did occur was in the backend. That is the
finding, and it is unflattering, so the extractor reads it off the record rather
than being told it.
"""

from __future__ import annotations

import re

from common import emit, repo_text, rule

LOG = "cold-start-a0/THEORIZE_LOG.md"

# "### R-05 Direction generality ... -> **reject, probe-pending**"
ENTRY = re.compile(r"^### ([ORLPE]-\d+)\s+(.*)$", re.MULTILINE)
VERDICT = re.compile(r"\*\*(accept|reject|entailed|admitted anyway|not read|"
                     r"not represented, logged|probe-pending|reject, probe-pending)\*\*",
                     re.IGNORECASE)

FAMILY = {"O": "object", "R": "rule", "L": "law", "P": "probe", "E": "expressivity"}


def _row_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table_after(text: str, marker: str, n_cols: int) -> list[list[str]]:
    """Return the body rows of the first pipe table following ``marker``."""
    start = text.index(marker)
    rows: list[list[str]] = []
    seen_header = False
    for line in text[start:].splitlines()[1:]:
        s = line.strip()
        if not s.startswith("|"):
            if rows:
                break
            continue
        cells = _row_cells(s)
        if len(cells) != n_cols:
            continue
        if set("".join(cells)) <= set("-: "):
            seen_header = True
            continue
        if not seen_header:
            continue
        rows.append(cells)
    return rows


def main() -> None:
    text = repo_text(LOG)

    entries = []
    matches = list(ENTRY.finditer(text))
    for i, m in enumerate(matches):
        ident, title = m.group(1), m.group(2).strip()
        body = text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        verdict = VERDICT.search(title) or VERDICT.search(body)
        entries.append({
            "id": ident,
            "family": FAMILY[ident[0]],
            "title": re.sub(r"\s+", " ", title),
            "verdict": (verdict.group(1).lower() if verdict else "see body"),
        })

    # Located by their own header rows rather than by surrounding prose: prose
    # gets rewrapped, header rows do not.
    revisions = [
        {"rev": int(r[0]), "milestone": r[1], "trigger": r[2], "change": r[3]}
        for r in _table_after(text, "| rev | when | trigger | change |", 4)
    ]
    defects = [
        {"n": int(d[0]), "layer": d[1], "defect": d[2], "surfaced_by": d[3]}
        for d in _table_after(text, "| # | layer | defect | how it surfaced |", 4)
    ]
    ledger = [
        {"id": e[0], "wanted": e[1], "worked_around_by": e[2], "cost": e[3]}
        for e in _table_after(text, "| # | wanted | worked around by | cost |", 4)
    ]

    payload = {
        "source": LOG,
        "claim": (
            "The A0 manual was revised zero times by certify: both certify layers "
            "went green against revision 1. The iterations that did happen were in "
            "the compiler, not in the manual."
        ),
        "adjudications": entries,
        "adjudication_counts": {
            fam: sum(1 for e in entries if e["family"] == fam)
            for fam in sorted({e["family"] for e in entries})
        },
        "verdict_counts": {
            v: sum(1 for e in entries if e["verdict"] == v)
            for v in sorted({e["verdict"] for e in entries})
        },
        "revisions": revisions,
        # Counted, not asserted: a revision is certify-driven only if its
        # trigger says so. The log's two revisions are M3 (the first pass over
        # the candidate stream) and M5 (a planner UNSAT), so this comes out 0 --
        # which is the figure's point, and it has to be derived or it is just a
        # claim with a number attached.
        "revisions_driven_by_certify": sum(
            1 for r in revisions if "certify" in r["trigger"].lower()
        ),
        "compiler_defects": defects,
        "expressivity_ledger": ledger,
    }

    lines = [
        "FIGURE 1 - concept-birth timeline, A0",
        f"source: {LOG}",
        rule(),
        "",
        "ADJUDICATIONS (engines propose, the LLM decides; one line per decision)",
        "",
    ]
    for e in entries:
        lines.append(f"  {e['id']:<5} {e['family']:<13} {e['verdict']:<22} {e['title'][:70]}")
    lines += ["", "REVISIONS OF THE MANUAL", ""]
    for r in revisions:
        lines.append(f"  rev {r['rev']}  [{r['milestone']}]  trigger: {r['trigger']}")
        lines.append(f"          change: {r['change']}")
    lines += [
        "",
        f"  revisions driven by certify: {payload['revisions_driven_by_certify']}",
        "",
        "THE ITERATIONS THAT DID HAPPEN - in the compiler, not the manual",
        "",
    ]
    for d in defects:
        lines.append(f"  {d['n']}. {d['layer']}")
        lines.append(f"     {d['defect']}")
        lines.append(f"     surfaced by: {d['surfaced_by']}")
    lines += ["", "WHAT THE WORLD SAID THAT THE GRAMMAR COULD NOT (expressivity ledger)", ""]
    for e in ledger:
        lines.append(f"  {e['id']:<6} wanted: {e['wanted']}")
        lines.append(f"  {'':<6} cost  : {e['cost']}")
    lines += ["", rule(), payload["claim"]]

    emit("fig1_concept_timeline", payload, "\n".join(lines))


if __name__ == "__main__":
    main()
