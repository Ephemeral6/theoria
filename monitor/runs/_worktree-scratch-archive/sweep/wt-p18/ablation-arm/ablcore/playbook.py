"""C-5: the playbook's theorem tier is demoted to the empirical tier.

`Theoria.md:110-112` gives the playbook two tiers:

    **定理级**:势函数/pagoda 权重、地标序、死锁刻画——相对说明书用 Lean 证。
              依赖追踪免费送一致性:说明书改一条规则,依赖它的玩法条目自动作废重审。
    **经验级**:打法偏好,携胜率/节点账,无证明,标明身份。

and constraint 5 (`Theoria.md:243`) says a strategy must carry **证明或节点账**.
Cut the proofs and only the node accounts are left, so every entry lands in the
empirical tier and must say so.

This is bookkeeping in the `order` and `heuristic` cases.  It is **not**
bookkeeping in the `prune` case, and that is the finding this module exists to
make visible:

    prune w_room(Cart) > 0 and no_button => dead [proof: lean]

`Theoria.md:116` calls a pruning rule 一条条件化的迷你不可解定理 — a deadlock
characterisation *is* a small unsolvability theorem, and its proof is what
licenses the planner to discard those nodes. Demoted to empirical, the same line
is an unproved instruction to throw away part of the search space: it can now
prune a branch that contains a real solution, and nothing in this arm would
notice, because the planner would simply report UNSAT and C-4 would settle it.
**The cut therefore reaches search soundness, not only the certificate.**

Two more consequences follow and are recorded rather than fixed:

* an inadmissible heuristic can no longer certify optimality — `Theoria.md:118`'s
  "最优性是不可解性的有限亲戚" (a lower-bound lemma plus a witness) needs the
  admissibility proof, so this arm's plans are plans, never *optimal* plans;
* dependency-driven re-审 (`Theoria.md:111`) has nothing left to invalidate —
  DESIGN.md §6 shadow 2.
"""

import re
from typing import Dict, List, Tuple

#: `[proof: lean]` and `[admissible: lean]` are the two theorem-tier markers in
#: `dsl_grammar_v0.1`'s playbook forms (`Theoria.md:173-176`).
_PROVEN = re.compile(r"\[(proof|admissible):\s*lean\s*\]")

_FORM = re.compile(r"^\s*(order|prune|heuristic|prefer)\b")

BANNER = (
    "# --- ABLATION (P-18) --------------------------------------------------\n"
    "# The theorem tier is gone.  Every entry below is empirical: it carries a\n"
    "# node account or nothing, and no entry is proved relative to the manual.\n"
    "# `prune` is the one that costs more than a label -- an unproved deadlock\n"
    "# characterisation may discard a branch that holds a real solution, and\n"
    "# this arm has no layer that would notice.  See ablcore/playbook.py.\n"
    "# ----------------------------------------------------------------------\n"
)

#: Which demotions cost soundness rather than only standing.
SOUNDNESS_BEARING = ("prune",)


def demote_text(text: str) -> Tuple[str, Dict[str, object]]:
    lines = text.splitlines(keepends=True)
    demoted: List[Dict[str, str]] = []
    out: List[str] = []
    inserted = False
    for line in lines:
        if not inserted and _FORM.match(line):
            out.append(BANNER)
            inserted = True
        match = _FORM.match(line)
        if match and _PROVEN.search(line):
            form = match.group(1)
            demoted.append({
                "form": form,
                "entry": line.strip(),
                "was": _PROVEN.search(line).group(0),
                "costs": ("search soundness: an unproved deadlock rule may prune "
                          "a branch containing a real solution"
                          if form in SOUNDNESS_BEARING else "standing only"),
            })
            line = _PROVEN.sub("[proof: none  tier: empirical]", line)
        out.append(line)
    if not inserted:
        out.append(BANNER)
    return "".join(out), {
        "entries_demoted": demoted,
        "count": len(demoted),
        "soundness_bearing": [d["entry"] for d in demoted
                              if d["form"] in SOUNDNESS_BEARING],
        "theorem_tier_entries_remaining": 0,
    }


def demote_file(src: str, dst: str) -> Dict[str, object]:
    with open(src, encoding="utf-8") as handle:
        text = handle.read()
    result, report = demote_text(text)
    with open(dst, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(result)
    report["source"] = src
    report["written"] = dst
    return report
