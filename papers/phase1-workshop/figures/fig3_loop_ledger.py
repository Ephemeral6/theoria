"""SUPERSEDED AS A SOURCE (P9). Kept as the witness, not as the figure.

The paper's figures are now built by the repository's deterministic pipeline at
``figures/`` -- see ``papers/phase1-workshop/figures/PARITY.md`` and OUTLINE.md.
This script is retained because it is an *independent* second computation of the
same numbers, and a second opinion is the only instrument that can catch a first
one being wrong. ``check_figure_parity.py`` runs it against the pipeline.

Do not cite this file from a section. It is not the figure any more.

--- original docstring follows ---

Figure 3 — A2's ledger flow, from a false theorem back to a solved level.

Source of truth: ``cold-start-a2/artifacts/loop_ledger.json``. The ledger is the
account of the whole exhibit: two beats to build the thing (a complete manual,
then the holed manual whose machine-checked impossibility theorem is false of
the world) and six beats to take it apart again — 打脸 / 定位 / 戳探 / 修订 /
重证 / 解出.

Each beat carries its own evidence paths. The figure is a flow, so the
rendering keeps them attached to their beat: a reader who doubts a box can open
exactly the files that box was settled by.
"""

from __future__ import annotations

import textwrap

from common import emit, repo_json, rule

LEDGER = "cold-start-a2/artifacts/loop_ledger.json"

GLOSS = {
    "打脸": "refutation",
    "定位": "localisation",
    "戳探": "probe",
    "修订": "revision",
    "重证": "re-certification",
    "解出": "solve",
}

# The six loop beats, in the order Theoria 1.4 states them. M0/M5 build the
# exhibit and are not part of the loop.
LOOP_BEATS = ("L1", "L2", "L3", "L4", "L5", "L6")


def _gloss(name: str) -> str:
    for zh, en in GLOSS.items():
        if zh in name:
            return f"{zh} ({en})"
    return name


def main() -> None:
    ledger = repo_json(LEDGER)
    beats = ledger["beats"]

    rows = []
    for b in beats:
        rows.append({
            "beat": b["beat"],
            "name": _gloss(b["name"]),
            "phase": "loop" if b["beat"] in LOOP_BEATS else "exhibit",
            "claim": b["claim"],
            "detail": b["detail"],
            "evidence": b["evidence"],
            "status": b["status"],
        })

    payload = {
        "source": LEDGER,
        "authority": ledger.get("authority"),
        "totals": {
            "beats": len(rows),
            "pass": sum(1 for r in rows if r["status"] == "pass"),
            "fail": sum(1 for r in rows if r["status"] not in ("pass", "absent")),
            "absent": sum(1 for r in rows if r["status"] == "absent"),
            "loop_beats": sum(1 for r in rows if r["phase"] == "loop"),
        },
        "beats": rows,
        "claim": (
            "Every gate on the holed manual is green — replay, planner, Lean, empty "
            "axiom list — and the manual is still false of the world. The instrument "
            "cannot tell the two Lean files apart; the refutation loop is what settles "
            "it, and the ledger is the account of that loop turning."
        ),
    }

    width = 72
    lines = [
        "FIGURE 3 - A2 ledger flow: 打脸 -> 重证, and what settled each beat",
        f"source: {LEDGER}",
        rule(width),
        "",
    ]
    for i, r in enumerate(rows):
        head = f"[{r['beat']}] {r['name']}"
        tag = "exhibit" if r["phase"] == "exhibit" else "loop"
        # Beat names carry CJK, which is double-width in a terminal and
        # single-width to str.ljust; the box is therefore sized off the
        # display width, not len().
        disp = sum(2 if ord(c) > 0x2E7F else 1 for c in head)
        pad = max(1, (width - 5) - disp - 9 - 1 - 4)
        lines.append(f"  +{'-' * (width - 4)}+")
        lines.append(f"  | {head}{' ' * pad}{tag:>9} {r['status'].upper():<4}|")
        lines.append(f"  +{'-' * (width - 4)}+")
        for wrapped in textwrap.wrap(r["claim"], width - 10):
            lines.append(f"    {wrapped}")
        for path in r["evidence"]:
            lines.append(f"      -> cold-start-a2/{path}")
        if i < len(rows) - 1:
            lines += ["", f"{' ' * 12}|", f"{' ' * 12}v", ""]

    t = payload["totals"]
    lines += [
        "",
        rule(width),
        f"  {t['beats']} beats, {t['pass']} pass, {t['fail']} fail, "
        f"{t['absent']} absent; {t['loop_beats']} of them are the loop itself.",
        "",
        payload["claim"],
    ]

    emit("fig3_loop_ledger", payload, "\n".join(lines))


if __name__ == "__main__":
    main()
