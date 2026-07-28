"""The incision, applied to a manual's source: laws lose their standing.

`Theoria.md:167` writes the obligation into the DSL itself:

    # 定律:全称断言,用说明书自己的词汇写;**声明即证明义务**
    invariant parity   (#Red + #Blue) mod 2 = c          [status: proven]
    theorem  unsolvable_L3  "每次推动保持红蓝奇偶;开局偶,赢需奇"

This module performs C-5 and the DSL half of C-1 (DESIGN.md §4) mechanically:

* every `invariant … [status: proven]` becomes `[status: empirical]` — the
  regularity is still *observed*, it is simply no longer *guaranteed*;
* every `theorem …` declaration is deleted outright, together with its
  `[depends: … probe: …]` continuation.  A theorem is nothing but a standing
  proof obligation; with no昂贵层 to discharge it, an undischarged one on the
  page would be a lie rather than a demotion.

**Nothing outside the `laws:` section may change.** That is not a stylistic
preference, it is the attributability requirement of `Theoria.md:280` made
checkable: if a single byte of the vocabulary, the semantics, the events, the
rules or the goal differed, a difference in the arms' behaviour could no longer
be pinned on the cut.  `downgrade_text` asserts it, and `tests/test_incision.py`
asserts it again on every generated file.

The transform is deliberately mechanical.  It is *not* a theorize step — no
semantic decision is being made here, and none may be: an ablation that also
re-adjudicated the manual would be two changes, not one.
"""

import re
from typing import Dict, List, Tuple

#: A top-level section header: no indentation, a bare word, a colon.
_SECTION = re.compile(r"^([a-z_]+):\s*(#.*)?$")

_STATUS_PROVEN = re.compile(r"\[status:\s*proven\s*\]")

BANNER = (
    "  # --- ABLATION (P-18) ------------------------------------------------\n"
    "  # This arm has no expensive certify layer, so nothing here is proven.\n"
    "  # `proven` -> `empirical`: the regularity was observed on the evidence\n"
    "  # below and carries no guarantee.  Theorem declarations are deleted\n"
    "  # rather than demoted: a theorem IS a proof obligation, and an\n"
    "  # undischarged one on the page would be a lie, not a demotion.\n"
    "  # Everything outside this section is byte-identical to the upstream\n"
    "  # manual -- see ablcore/downgrade.py and DESIGN.md §4.\n"
    "  # ---------------------------------------------------------------------\n"
)


def _laws_span(lines: List[str]) -> Tuple[int, int]:
    """`[start, end)` line indices of the `laws:` section, or `(-1, -1)`."""
    start = -1
    for i, line in enumerate(lines):
        match = _SECTION.match(line)
        if match and match.group(1) == "laws":
            start = i
            break
    if start < 0:
        return -1, -1
    for j in range(start + 1, len(lines)):
        match = _SECTION.match(lines[j])
        if match:
            return start, j
    return start, len(lines)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def downgrade_text(text: str) -> Tuple[str, Dict[str, object]]:
    """Return the ablated manual and a report of exactly what the cut removed."""
    lines = text.splitlines(keepends=True)
    start, end = _laws_span(lines)
    report: Dict[str, object] = {
        "has_laws_section": start >= 0,
        "invariants_demoted": [],
        "theorems_deleted": [],
    }
    if start < 0:
        return text, report

    out: List[str] = list(lines[:start + 1])
    out.append(BANNER)

    i = start + 1
    while i < end:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("theorem "):
            name = stripped.split()[1]
            base = _indent(line)
            consumed = [line]
            i += 1
            while i < end and lines[i].strip() and _indent(lines[i]) > base:
                consumed.append(lines[i])
                i += 1
            report["theorems_deleted"].append({
                "name": name, "lines": len(consumed),
                "source": "".join(consumed).rstrip("\n"),
            })
            continue
        if stripped.startswith("invariant ") and _STATUS_PROVEN.search(line):
            report["invariants_demoted"].append(stripped.split()[1])
            line = _STATUS_PROVEN.sub("[status: empirical]", line)
        out.append(line)
        i += 1

    out.extend(lines[end:])
    result = "".join(out)

    # The attributability check, run every time rather than trusted.
    before = "".join(lines[:start + 1] + lines[end:])
    after_lines = result.splitlines(keepends=True)
    a_start, a_end = _laws_span(after_lines)
    after = "".join(after_lines[:a_start + 1] + after_lines[a_end:])
    if before != after:
        raise AssertionError(
            "the downgrade changed something outside `laws:`; the arms would "
            "no longer be comparable (Theoria.md:280)")
    return result, report


def downgrade_file(src: str, dst: str) -> Dict[str, object]:
    with open(src, encoding="utf-8") as handle:
        text = handle.read()
    result, report = downgrade_text(text)
    with open(dst, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(result)
    report["source"] = src
    report["written"] = dst
    report["bytes"] = len(result.encode("utf-8"))
    return report
