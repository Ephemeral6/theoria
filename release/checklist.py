"""Cross-walk the manifest against Theoria.md's release list.

    python release/checklist.py            # writes release/CHECKLIST.md
    python release/checklist.py --dry-run

Step 3 of `release/PLAN.md`. `Theoria.md`:379 names what a Phase 4 release must
contain. This reads `MANIFEST.jsonl` and, for each named item, reports what
satisfies it, how much of it there is, and **what its licence verdict does to
it** — because on this project several checklist items are satisfied by material
that exists, is complete, and may not be published.

## A tick is not the interesting outcome

Three statuses, and two of them are more useful than a tick:

* `PRESENT` — the item exists and every file satisfying it is releasable.
* `WITHHELD` — the item exists **and cannot ship as itself**. Class B is
  releasable only as a hash plus a regeneration script; class D not at all. An
  item in this state is not a gap in the work, it is a gap in what a reader can
  be handed, and the two are different claims.
* `ABSENT` — nothing satisfies it. This is the state a checklist exists to find,
  and it must carry a reason rather than a blank.

The failure mode being designed against: a checklist that reports nine ticks
because it was written by reading the same list it is checking. Each matcher
below is a rule over paths in the manifest, and an item that matches nothing
says so loudly instead of being quietly dropped.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys

# Item labels are Chinese, quoted from the design document because it is the
# authority. A Windows console falls back to the locale codec -- GBK here -- and
# rendered seven of ten item names as mojibake for a reader following
# REPRODUCING.md, making the run output unreadable. Pinned, as build_all.py
# already does for the same reason.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", newline="
")
    except (AttributeError, OSError):  # pragma: no cover
        pass

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
MANIFEST = os.path.join(_HERE, "MANIFEST.jsonl")
OUT = os.path.join(_HERE, "CHECKLIST.md")

#: `Theoria.md`:379, item by item, in its own order. The Chinese is quoted
#: because it is the authority; the gloss is this file's.
CHECKLIST: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "全部账本",
        "all ledgers -- every arm's record of what it did and what it cost",
        ("*/ledger.jsonl", "*/ledger.*.jsonl", "baseline-arms/ledger.jsonl", "*/cost_curve.json"),
    ),
    (
        "两本书（各形态）",
        "the two books -- manual and playbook -- in each compiled form",
        ("*/theory*.dsl", "*/playbook*.dsl", "*.pddl", "*/generated/*.py", "*/generated/*.md"),
    ),
    ("Lean 证明", "the machine-checked proofs", ("*.lean",)),
    (
        "候选箱",
        "the candidate box: what the engines proposed, before adjudication",
        ("*/candidates*.jsonl", "CONTRACTS/candidates_schema*.md"),
    ),
    ("探针日志", "probe logs", ("*/probe_log*.jsonl", "*/probes*.jsonl", "*/probe_report.json")),
    (
        "电池代码与回算结果",
        "the battery: its code and the results of recomputing over every arm",
        ("battery/*.py", "battery/**/*.py", "battery/artifacts/*.json"),
    ),
    (
        "冻结清单",
        "the freeze list -- what was pre-registered and frozen before the campaign",
        ("*frozen*.json", "*freeze*.json", "*/PREDICTIONS.md", "*/PREREGISTRATION*.md"),
    ),
    (
        "incident ledger",
        "the incident ledger",
        ("*/incidents.jsonl", "*INCIDENTS.md", "INCIDENTS.md"),
    ),
    (
        "复跑说明",
        "reproduction instructions -- how a stranger re-runs this",
        # The DOCUMENT, not the tool. `release/reproduce.py` was in this matcher
        # until step 5, which meant that committing the script flipped this item
        # from ABSENT to PRESENT while the instructions still did not exist --
        # a tick earned by the wrong artefact. 复跑说明 is something a stranger
        # reads; a script they cannot find is not it.
        ("release/REPRODUCING.md", "*/REPRODUCING.md"),
    ),
    (
        "runs 档案（P5 条目追加）",
        "the runs archive; named by the work order rather than by Theoria.md",
        ("*/runs/*",),
    ),
)

#: Why an item is absent, where absence is known and explicable. An absent item
#: with no reason is the thing this file exists to prevent; an absent item with
#: a reason is a finding.
ABSENCE_REASONS: dict[str, str] = {
    "复跑说明": (
        "not written yet -- it is step 5 of release/PLAN.md, and reproduce.py is step 4. "
        "The checklist is correct to fail here: the release cannot ship without it."
    ),
}


def load() -> list[dict]:
    with open(MANIFEST, encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


def match(rows: list[dict], patterns: tuple[str, ...]) -> list[dict]:
    hits: dict[str, dict] = {}
    for r in rows:
        p = r["path"]
        for pat in patterns:
            if fnmatch.fnmatchcase(p, pat) or (
                pat.startswith("*/") and fnmatch.fnmatchcase(p, pat[2:])
            ):
                hits[p] = r
                break
    return [hits[k] for k in sorted(hits)]


def status_of(hits: list[dict]) -> tuple[str, str]:
    if not hits:
        return "ABSENT", "nothing in the manifest satisfies this item"
    classes = sorted({h["class"] for h in hits})
    blocked = [h for h in hits if h["class"] in ("B", "D")]
    if not blocked:
        return "PRESENT", f"{len(hits)} file(s), class {'/'.join(classes)}"
    return (
        "WITHHELD",
        f"{len(hits)} file(s), class {'/'.join(classes)}; {len(blocked)} of them cannot "
        "ship as themselves",
    )


def completeness(zh: str, hits: list[dict]) -> list[str]:
    """Per-item detail that a status word cannot carry.

    A tick answers "does anything match", which is the weakest question a
    checklist can ask. Two items here matched and were still not what the list
    asks for, and neither would have been visible from `PRESENT`.
    """
    notes: list[str] = []
    if zh.startswith("两本书"):
        # CLAUDE.md: the two books compile to FOUR co-derived forms -- Lean,
        # Python, PDDL, Markdown. "各形态" is that set, per territory.
        forms = {".lean": "Lean", ".py": "Python", ".pddl": "PDDL", ".md": "Markdown"}
        by_terr: dict[str, set[str]] = {}
        for h in hits:
            terr = h["path"].split("/")[0]
            ext = os.path.splitext(h["path"])[1]
            by_terr.setdefault(terr, set()).add(ext)
        full = [t for t, e in by_terr.items() if set(forms) - {".lean"} <= e]
        notes.append(
            f"**Form coverage is partial, and the status word hides it.** Of "
            f"{len(by_terr)} territories holding a book, **{len(full)}** carry the "
            "Python + PDDL + Markdown set alongside the DSL source "
            f"({', '.join(sorted(full))}). The rest carry a subset:"
        )
        for t, e in sorted(by_terr.items()):
            if t in full:
                continue
            have = ", ".join(forms.get(x, x) for x in sorted(e) if x in forms) or "DSL only"
            notes.append(f"* `{t}/` — {have}")
        notes.append(
            "Whether a territory *should* hold all four is not decided here: some hold a "
            "manual and no playbook by design. What this records is that "
            "「各形态」 is not uniformly satisfied, which a tick would have denied."
        )
    if zh.startswith("冻结清单"):
        notes.append(
            "**Matched, but check what it matched.** `battery/PREDICTIONS.md` is the "
            "battery's pre-registration and `proxy/scoring/frozen.json` is the frozen "
            "scoring table. Neither is the *campaign* freeze: "
            "`arc-recon/data/campaign_freeze.json` is referenced by drift reports and "
            "**is not on disk** (OPS-R, 2026-07-28). So the item is satisfied in two of "
            "its senses and not in the third, and a reader handed this release would find "
            "no frozen campaign roster."
        )
    return notes


def report(rows: list[dict]) -> tuple[list[str], dict[str, int]]:
    lines: list[str] = []
    tally = {"PRESENT": 0, "WITHHELD": 0, "ABSENT": 0}
    for zh, gloss, patterns in CHECKLIST:
        hits = match(rows, patterns)
        status, detail = status_of(hits)
        tally[status] += 1
        size = sum(h["size"] for h in hits)
        by_class: dict[str, int] = {}
        for h in hits:
            by_class[h["class"]] = by_class.get(h["class"], 0) + 1
        lines.append(f"### {zh} — {gloss}")
        lines.append("")
        lines.append(f"**{status}.** {detail}")
        if hits:
            lines.append("")
            lines.append(
                f"{len(hits)} file(s), {size / 1e6:.2f} MB, classes "
                + ", ".join(f"{c}x{n}" for c, n in sorted(by_class.items()))
            )
            blocked = [h for h in hits if h["class"] in ("B", "D")]
            if blocked:
                lines.append("")
                lines.append(
                    "Cannot ship as itself — ships as sha256 + a regeneration script "
                    "(class B) or not at all (class D):"
                )
                for h in blocked[:8]:
                    lines.append(f"* `{h['path']}` — class {h['class']}, {h['size'] / 1e6:.2f} MB")
                if len(blocked) > 8:
                    lines.append(f"* … and {len(blocked) - 8} more")
        else:
            reason = ABSENCE_REASONS.get(zh, "no reason recorded — this needs one before release")
            lines.append("")
            lines.append(f"Reason: {reason}")
        for note in completeness(zh, hits):
            lines.append("")
            lines.append(note)
        lines.append("")
    return lines, tally


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    rows = load()
    lines, tally = report(rows)
    header = [
        "# release/CHECKLIST.md — Theoria.md's release list against the manifest",
        "",
        "Generated by `release/checklist.py` from `release/MANIFEST.jsonl`. The list is",
        "`Theoria.md`:379's, quoted item by item; the last entry is added by the P5 work",
        "order rather than by `Theoria.md`.",
        "",
        f"**{tally['PRESENT']} present · {tally['WITHHELD']} withheld · {tally['ABSENT']} absent.**",
        "",
        "*Withheld* does not mean missing. It means the material exists and complete and",
        "cannot be handed over as itself: class B ships as a sha256 plus the script that",
        "regenerates it, class D not at all. See `release/LICENCE_POSTURE.md`.",
        "",
        "---",
        "",
    ]
    body = "\n".join(header + lines)
    print(f"{tally['PRESENT']} present, {tally['WITHHELD']} withheld, {tally['ABSENT']} absent")
    for zh, _, patterns in CHECKLIST:
        hits = match(rows, patterns)
        st, _d = status_of(hits)
        print(f"  {st:9s} {zh}  ({len(hits)} file(s))")
    if args.dry_run:
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(f"\nwrote {os.path.relpath(OUT, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
