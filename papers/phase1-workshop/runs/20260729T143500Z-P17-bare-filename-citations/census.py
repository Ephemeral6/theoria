"""The executable form of OPEN_ITEMS B1.

B1 states its finding in prose -- "22 distinct, 30 occurrences, 9 of them
ambiguous across 6-24 real candidates". A number in a checklist cannot be
re-run, cannot go stale loudly, and cannot be checked by a reader. This writes
`census.json`: every bare-filename citation in the body, where it is, and every
file in the tree that could be meant.

Run:  python papers/phase1-workshop/runs/20260729T143500Z-P17-bare-filename-citations/census.py

Measured 2026-07-29 at base bb06b8d9, over the 12 **body** sections (the
abstract is exempt here as it is in checks E and F): **108 occurrences, 32
distinct, 13 ambiguous tokens across 19 occurrences**.

That disagrees with B1's 22/30/9, and the disagreement is not all drift: B1
gives no method, so there is no way to reproduce it and no way to tell which of
the two is counting what. Counting the abstract as well gives 110/34 -- the
ambiguous 13/19 is the same either way, and it is the number the gate acts on.
Which is the argument for this file existing.

`n_candidates` for a common name drifts upward as runs accumulate
(`MANIFEST.json` was 124 an hour before this line was written, and 125 after
this directory gained one). Nothing depends on the exact figure; check F only
asks whether it exceeds one.
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve()
PAPER = HERE.parents[2]
sys.path.insert(0, str(PAPER))
import verify_paper as vp  # noqa: E402


def main() -> int:
    occurrences = []
    for section in sorted(vp.SECTIONS.glob("*.md")):
        if section.name in vp.EXEMPT_SECTIONS:
            continue
        for lineno, line in enumerate(
                section.read_text(encoding="utf-8").splitlines(), 1):
            for m in vp.CITE_TOKEN.finditer(line):
                token = m.group(1)
                if "/" in token or not token.lower().endswith(vp.ARTEFACT_SUFFIX):
                    continue
                occurrences.append({
                    "section": section.name, "line": lineno, "token": token,
                    "n_candidates": len(vp._candidates(token)),
                })

    per_token = collections.Counter(o["token"] for o in occurrences)
    candidates = {t: vp._candidates(t) for t in per_token}
    ambiguous = {t: c for t, c in candidates.items() if len(c) > 1}

    (HERE.parent / "census.json").write_text(
        json.dumps({"occurrences": occurrences, "candidates": candidates},
                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"occurrences:            {len(occurrences)}")
    print(f"distinct tokens:        {len(per_token)}")
    print(f"ambiguous tokens:       {len(ambiguous)}")
    print(f"ambiguous occurrences:  {sum(per_token[t] for t in ambiguous)}")
    print()
    for token, cands in sorted(ambiguous.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(cands):3d} candidates  x{per_token[token]:<2d}  {token}")
    missing = [t for t, c in candidates.items() if not c]
    print()
    print(f"cited but absent from the tree: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
