# -*- coding: utf-8 -*-
"""Guard the 2026-08-01 ruling that withdrew the front-load endpoint.

WHAT WAS RULED (`STATS_RULES.md` §3.0, `CLAIMS_TEXT.md` C2).  The front-loading
index paired difference -- `Theoria.md:373`'s third primary endpoint, the
battery's metric id `E2` -- is no longer a confirmatory endpoint.  It buckets
cost by `Call.turn`, a label the *recorder* writes, and battery's own repaired
attack `batched-turn-label-coherent` reaches 0.973387097 while breaking none of
the corpus-validated recorder invariants and passing the poverty certificate.
So the value is reachable by an arm that changed a batching convention and
nothing else.

WHY THIS FILE EXISTS.  A withdrawal is a cheap thing to undo quietly, and it is
cheap in a direction that pays: drop the endpoint AND drop Holm's divisor from
3 to 2, and the two survivors get their threshold loosened from alpha/3 to
alpha/2 -- by §4.1's arithmetic the sign test's entry price falls from k >= 7 to
k >= 6.  The kit already refused that trade for the *inconclusive* case (stage
[16]'s `*/family` probe, §4.4.3).  This file refuses it for the *withdrawal*
case, and guards five other ways the ruling can be hollowed out without being
reversed.

WHAT IT CANNOT DO.  It reads whether the ruling is STATED, never whether it is
right, and it cannot see a defect the ruling itself carries: §3.0.6's last row
records that the axis-validity flaw survives the demotion and lives on in every
exploratory front-load number that still gets printed.  A green here means the
withdrawal is on the record with its price attached, not that the metric is
fixed.

    python freeze/e2_withdrawal.py --verify     # 0 = the ruling is intact
    python freeze/e2_withdrawal.py --selftest   # the negative controls
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
CLAIMS = os.path.join(HERE, "CLAIMS_TEXT.md")
STATS = os.path.join(HERE, "STATS_RULES.md")


def norm(text: str) -> str:
    """One wording up to whitespace.  Nothing else is normalised -- stage [16]'s
    rule, kept identical so the two gates cannot disagree about what a match is."""
    return re.sub(r"[ \t　]+", "", text)


def section(text: str, start: str, end: str) -> Optional[str]:
    """The span from `start` to `end`, or None if EITHER anchor is missing.

    Never falls back to end-of-file: stage [16] records what that costs -- the
    scope silently swallows later sections and probes start passing on somebody
    else's text.  A scope that cannot be located is a failure, not a pass.
    """
    if not re.search(start, text, re.M) or not re.search(end, text, re.M):
        return None
    m = re.search(start + r".*?(?=" + end + r")", text, re.M | re.S)
    return m.group(0) if m else None


#: The three verbatim outcome blocks C2 must publish.  A closed set: a fourth
#: one would be an outcome nobody audited, which is stage [10]'s finding on C1
#: transplanted to the endpoint that just lost its confirmatory status.
C2_BLOCKS = ("成立版", "不成立版", "不可结论版")

#: The identity sentence every C2 outcome block must open with.  Without it a
#: reader who lands on one block reads a confirmatory claim.
IDENTITY = "本段是探索性并列报告，不是确证主张"

#: Statements that must be present, and where.  (id, what, side, scope, needle)
#: side: "S" = STATS_RULES.md, "C" = CLAIMS_TEXT.md, "B" = both files.
REQUIRED: List[Tuple[str, str, str, str, str]] = [
    ("W1/ruled", "the withdrawal is ruled in STATS_RULES §3",
     "S", "S3", "撤出确证家族"),
    ("W1/head", "§3.0 is where the ruling lives",
     "S", "S3", "###3.0裁定"),
    ("W2/ruled", "the withdrawal is stated in CLAIMS_TEXT C2",
     "C", "C2", "撤出主终点确证家族"),
    ("W3/divisor", "the Holm divisor survives the withdrawal at 3",
     "B", "*", "除数仍为3"),
    ("W3/family", "the family invariant is still stated as three slots",
     "B", "*", "family恒为三个主终点"),
    ("W5/noexempt", "§8's exploratory clause carries no exception",
     "S", "*", "一律标探索性，一条例外都没有"),
    ("W6/caveat", "the axis-validity defect survives the demotion and is disclosed",
     "B", "*", "轴的效度"),
    ("W7/value", "the measured attack value is named, not paraphrased",
     "B", "*", "0.973387097"),
    ("W8/reach", "the attack is named as arm-reachable, not recorder-only",
     "B", "*", "arm-reachable"),
]

#: Negations: a rule kept as a token while its content is reversed.  Deliberately
#: narrow.  The kit already learned that a negation regex which cannot tell 不X
#: from X is worse than no regex -- it trains people to reword correct prose --
#: so nothing here matches a phrase the correct text also uses under a 不 / 若.
NEGATIONS: List[Tuple[str, str]] = [
    (r"除数(仍|恒|钉死|改)为2",
     "the Holm divisor has been dropped to 2 -- the withdrawal would then buy "
     "the two survivors a looser threshold (alpha/2 instead of alpha/3, sign "
     "test k>=6 instead of k>=7), which is the trade §3.0 ruling 2 refuses"),
    (r"family恒为两个主终点",
     "the family has been re-declared as two -- same trade, stated as an "
     "invariant"),
    (r"前载(指数)?(配对差)?(重回|回到|仍是|仍为|依然是)主终点",
     "the withdrawn endpoint has been put back without process 1"),
    (r"探索性读数(可|得|能)(作为|用作)确证",
     "an exploratory reading is being promoted to evidence -- §8's closed door"),
]


def _scopes(claims: str, stats: str) -> Dict[str, Optional[str]]:
    return {
        "S3": section(stats, r"^## 3\. 主终点三", r"^## 4\."),
        "C2": section(claims, r"^## C2 [·・]", r"^## C3 [·・]"),
        "*": None,          # whole file; resolved in `_body`
    }


def _body(scope: str, side: str, claims: str, stats: str,
          scopes: Dict[str, Optional[str]]) -> Optional[str]:
    if scope == "*":
        return stats if side == "S" else claims
    return scopes.get(scope)


def check(claims: str, stats: str) -> List[str]:
    """-> list of complaints.  Empty list == the ruling is intact."""
    bad: List[str] = []
    scopes = _scopes(claims, stats)
    for key in ("S3", "C2"):
        if scopes[key] is None:
            bad.append("scope %s could not be located -- this gate would be "
                       "scanning nothing" % key)
    NC, NS = norm(claims), norm(stats)

    for pid, what, side, scope, needle in REQUIRED:
        sides = ("S", "C") if side == "B" else (side,)
        for s in sides:
            body = _body(scope, s, claims, stats, scopes)
            if body is None:
                continue                       # already reported as a bad scope
            if norm(needle) not in norm(body):
                where = "STATS_RULES.md" if s == "S" else "CLAIMS_TEXT.md"
                bad.append("%s: %s -- %r not found in %s (%s)"
                           % (pid, what, needle, where, scope))

    # Each outcome block of C2 must carry the identity sentence in its own body.
    c2 = scopes["C2"]
    if c2 is not None:
        blocks = {}
        for m in re.finditer(r"^### ([^\n]*?（逐字）)([^\n]*)$(.*?)(?=^###|\Z)",
                             c2, re.M | re.S):
            name = m.group(1).strip().replace("（逐字）", "")
            blocks[name] = m.group(3)
        for name in C2_BLOCKS:
            if name not in blocks:
                bad.append("W4/%s: C2 has no %s（逐字）block -- the both-outcomes "
                           "discipline survives the withdrawal" % (name, name))
            elif norm(IDENTITY) not in norm(blocks[name]):
                bad.append("W4/%s: C2's %s（逐字）block does not open with %r -- a "
                           "reader landing on this block reads a confirmatory "
                           "claim" % (name, name, IDENTITY))
        extra = [n for n in blocks if n not in C2_BLOCKS]
        if extra:
            bad.append("W4/extra: C2 carries an unaudited verbatim outcome %s -- "
                       "a fourth block may not carry a different status"
                       % sorted(extra))

    for pat, why in NEGATIONS:
        for label, body in (("STATS_RULES.md", NS), ("CLAIMS_TEXT.md", NC)):
            if re.search(pat, body):
                bad.append("W8/neg: %s matches %r -- %s" % (label, pat, why))
    return bad


# ---------------------------------------------------------------- selftest
#: (name, mutate, id-prefix that MUST appear among the complaints)
#: A control that cannot be built is a failure, not a skip: an unbuildable
#: mutation means this gate is scanning text that is no longer where it thinks.
def _mutations() -> List[Tuple[str, Callable[[str, str], Tuple[str, str]], str]]:
    def drop_identity_from_one_block(c: str, s: str):
        # Only the 不成立版 block, so the control proves the check is per-block
        # rather than per-file.
        marker = ("### 不成立版（逐字）\n> **" + IDENTITY + "**：前载指数配对差已按\n"
                  "> `STATS_RULES.md` §3.0 撤出主终点确证家族，**Holm 的除数仍为 3**。\n>\n")
        return c.replace(marker, "### 不成立版（逐字）\n"), s

    def divisor_to_two(c: str, s: str):
        return c.replace("除数仍为 3", "除数仍为 2"), s.replace("除数仍为 3", "除数仍为 2")

    def restore_exception(c: str, s: str):
        return c, s.replace("**一律标探索性，一条例外都没有**",
                            "中，除 `E2` 外**一律标探索性**")

    def drop_caveat(c: str, s: str):
        return c.replace("轴的效度", "形状的效度"), s

    def drop_ruling_heading(c: str, s: str):
        return c, s.replace("### 3.0 裁定", "### 3.0 说明")

    def blur_the_value(c: str, s: str):
        return c.replace("0.973387097", "0.97"), s.replace("0.973387097", "0.97")

    def family_to_two(c: str, s: str):
        return c, s.replace("family 恒为三个主终点，本终点保留席位",
                            "family 恒为两个主终点，本终点退席")

    return [
        ("drop the identity sentence from ONE C2 block",
         drop_identity_from_one_block, "W4/不成立版"),
        ("drop the Holm divisor from 3 to 2", divisor_to_two, "W3/divisor"),
        ("restore §8's `除 E2 外` exception", restore_exception, "W5/noexempt"),
        ("delete the axis-validity caveat from CLAIMS_TEXT", drop_caveat,
         "W6/caveat"),
        ("demote §3.0 from a ruling to a note", drop_ruling_heading, "W1/head"),
        ("blur the measured attack value", blur_the_value, "W7/value"),
        ("re-declare the family as two", family_to_two, "W8/neg"),
    ]


def selftest(claims: str, stats: str) -> Tuple[int, int, List[str]]:
    lines: List[str] = []
    passed = failed = 0

    live = check(claims, stats)
    if live:
        failed += 1
        lines.append("FAIL positive control: the real files do not pass, so a "
                     "red from any mutation proves nothing")
        for b in live:
            lines.append("       " + b)
    else:
        passed += 1
        lines.append("PASS positive control: the real files pass unmutated")

    for name, mutate, want in _mutations():
        mc, ms = mutate(claims, stats)
        if (mc, ms) == (claims, stats):
            failed += 1
            lines.append("FAIL control could not be built (%s): the text is not "
                         "where this gate expects it, so the check may be "
                         "scanning nothing" % name)
            continue
        got = check(mc, ms)
        if any(b.startswith(want) for b in got):
            passed += 1
            lines.append("PASS control fires: %s -> %s" % (name, want))
        else:
            failed += 1
            lines.append("FAIL control did NOT fire: %s (expected %s, got %s)"
                         % (name, want, got or "no complaint at all"))
    return passed, failed, lines


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    claims = open(CLAIMS, encoding="utf-8").read()
    stats = open(STATS, encoding="utf-8").read()

    if args.selftest:
        passed, failed, lines = selftest(claims, stats)
        for line in lines:
            print(line)
        print("%d/%d" % (passed, passed + failed))
        return 1 if failed else 0

    bad = check(claims, stats)
    for b in bad:
        print("FAIL " + b)
    if bad:
        return 1
    print("PASS the §3.0 withdrawal is stated in both files, the Holm divisor "
          "is still 3, all three C2 blocks carry the identity sentence, §8 "
          "carries no exception, and the surviving axis defect is disclosed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
