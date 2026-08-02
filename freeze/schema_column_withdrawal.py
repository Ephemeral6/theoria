"""The Schema (复现口径) column is withdrawn, and a withdrawn placeholder may not still be cited.

S48, 2026-08-02.  `baseline-arms` proposed withdrawing `Theoria.md:271`'s
**Schema（复现口径）** column outright rather than leaving it blank
(`monitor/inbox/20260801T0600Z-PROP-schema-column-withdrawal.md`, ruling in
`baseline-arms/SCHEMA_ARM_RULING.md`).  This gate holds down `freeze`'s half of
that: the three places in `CLAIMS_TEXT.md` where the column was load-bearing.

**Why a gate and not just an edit.**  The whole point of withdrawing rather than
blanking is that a blank keeps the promise that one day it will be filled.  A
withdrawal that can still be *cited* is that promise under a new name — so the
one thing this file exists to refuse is a live citation of `⟨复现值⟩`.  "Live"
matters: recording that the placeholder was withdrawn necessarily names it, and
that must stay legal, or the withdrawal could not be written down at all.  The
rule is therefore the one `exam/tools/check_withdrawn_claims.py` arrived at for
the same problem — a hit is **acquitted when a withdrawal marker stands within
`ACQUIT_WINDOW` lines of it**, and convicted otherwise.

**And a positive control, because the material was not withdrawn.**  Only the
same-shell reproduction claim was.  The upstream trajectories survive as the
`schema_upstream` reference row, and this gate fails if that row disappears or
loses its coverage — 开发堆 4 局, 8 runs, and the 1 of 2 collections that records
tokens.  Withdrawing a claim and deleting the evidence are different acts and a
gate that could not tell them apart would license the second.

    python freeze/schema_column_withdrawal.py --verify     # 0 = the withdrawal is intact
    python freeze/schema_column_withdrawal.py --selftest   # the negative controls
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Callable, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
CLAIMS = os.path.join(HERE, "CLAIMS_TEXT.md")

#: The bracketed placeholder itself, not the common noun `复现值`.  `无同壳复现值`
#: is ordinary prose and must never be convicted.
PLACEHOLDER = "⟨复现值⟩"

#: How far a withdrawal marker may stand from a placeholder mention and still
#: acquit it.  Two lines, as `exam`'s scanner uses: enough for `**已撤销**` to sit
#: on the line after the mention in a hard-wrapped paragraph, not enough for an
#: unrelated withdrawal elsewhere in the section to launder a live citation.
ACQUIT_WINDOW = 2

WITHDRAWAL_MARKERS = ("已撤销", "撤销该列", "撤除", "withdrawn", "已一并删除")

#: The retired arm name.  `repro` is the residue of the D-B-019 confusion, and
#: residue gets read again — `battery` owns the rename, this gate only refuses to
#: let the dead name back into freeze's claim text.
RETIRED_ARM = "schema_repro"
LIVE_ROW = "schema_upstream"


def _lines(text: str) -> List[str]:
    return text.replace("\r\n", "\n").split("\n")


def _acquitted(lines: List[str], i: int) -> bool:
    lo = max(0, i - ACQUIT_WINDOW)
    hi = min(len(lines), i + ACQUIT_WINDOW + 1)
    window = "\n".join(lines[lo:hi])
    return any(m in window for m in WITHDRAWAL_MARKERS)


def check(claims: str) -> List[str]:
    bad: List[str] = []
    lines = _lines(claims)

    # ---- W1  the placeholder may be recorded as withdrawn, never cited live.
    live = [i + 1 for i, ln in enumerate(lines)
            if PLACEHOLDER in ln and not _acquitted(lines, i)]
    if live:
        bad.append("W1/placeholder the withdrawn `%s` placeholder is still cited "
                   "as a live value at line(s) %s -- a withdrawal that can be "
                   "cited is the blank it replaced, wearing a new name"
                   % (PLACEHOLDER, live))
    if PLACEHOLDER not in claims:
        bad.append("W1b/norecord the withdrawal of `%s` is not recorded anywhere "
                   "in CLAIMS_TEXT.md -- deleting the mention loses the fact that "
                   "there was ever a promise to withdraw" % PLACEHOLDER)

    # ---- W2  the premise paragraph carries BOTH sentences, and no needs_human.
    if "同壳的 Schema 复现臂不存在，也不会存在" not in claims:
        bad.append("W2/premise the premise correction no longer says the "
                   "same-shell reproduction arm will never exist")
    if "存在的是另一样东西" not in claims:
        bad.append("W2b/halfpremise the premise correction states only the first "
                   "sentence again -- the second (the upstream trajectories were "
                   "ingested as `%s`) was already true for six hours when the "
                   "first was written alone" % LIVE_ROW)
    if "前提修正（needs_human）" in claims:
        bad.append("W2c/needshuman the premise correction still carries "
                   "`needs_human` -- SCHEMA_ARM_RULING.md §3 priced and closed all "
                   "three alternative routes, so there is no human decision left")

    # ---- W3  C1's 「唯一」 has its scope nailed down.
    if "在本实验的同壳三臂中唯一" not in claims:
        bad.append("W3/scope C1's 「唯一」 no longer writes its scope as "
                   "「在本实验的同壳三臂中唯一」 -- unscoped it reads as an "
                   "exclusivity claim over all known frameworks, which this "
                   "experiment did not test")
    if "本文对它在 U3/U4 上的表现**不作任何主张**" not in claims:
        bad.append("W3b/noclaim C1 no longer disclaims any position on upstream "
                   "Schema's U3/U4 performance")

    # ---- W4  C2's Schema comparator is withdrawn as UNMEASURABLE, not untested.
    if "「vs Schema 平坦」已撤除" not in claims:
        bad.append("W4/c2 C2 no longer records that 「vs Schema 平坦」 was "
                   "withdrawn")
    # The whole clause, not the bare word.  `不可测` also appears in the prose
    # paragraph that explains the distinction, so scanning for the word alone
    # would stay green while the sentence that carries the claim was deleted --
    # which is exactly what the negative control caught on the first run.
    if "**不可测**，而不是待测" not in claims:
        bad.append("W4b/unmeasurable C2 no longer says the comparator is "
                   "*unmeasurable rather than untested* on this material -- "
                   "「未测」 invites a future run, and there is no run that would "
                   "produce it")
    if "not-applicable" not in claims:
        bad.append("W4c/na C2 no longer records that E2 returns `not-applicable` "
                   "on the whole upstream arm")
    if "保持原样" not in claims:
        bad.append("W4d/prereg C2 no longer states that `PREDICTIONS.md:78`'s "
                   "pre-registration is left untouched -- editing a "
                   "pre-registration destroys it, so only the settlement moves")

    # ---- W5  C5's hard constraint says withdrawn, and the interval is gone.
    if "合规留空" in claims and "此前是「合规留空」" not in claims:
        bad.append("W5/blank C5's hard constraint still calls the placeholder a "
                   "compliant blank rather than a withdrawal")
    if "2.04–3.41 亿" in claims and "出处在仓库中不存在" not in claims:
        bad.append("W5b/interval the 「实测 2.04–3.41 亿」 interval is quoted "
                   "without the finding that it reproduces under neither counting "
                   "convention and has no provenance in this repository")

    # ---- W6  POSITIVE CONTROL: the material itself was not withdrawn.
    if LIVE_ROW not in claims:
        bad.append("W6/row the `%s` reference row is gone -- only the same-shell "
                   "reproduction was withdrawn, not the upstream material"
                   % LIVE_ROW)
    for token, what in (("开发堆 4 局", "the 4-game development-pile coverage"),
                        ("8 个 run", "the 8-run count"),
                        ("1 套", "the 1-of-2 collections that records tokens")):
        if token not in claims:
            bad.append("W6b/coverage a `%s` citation no longer carries %s; every "
                       "reference to it must name its coverage or it reads as a "
                       "25-game number" % (LIVE_ROW, what))

    # ---- W7  the retired arm name may not come back as a live name.
    dead = [i + 1 for i, ln in enumerate(lines) if RETIRED_ARM in ln]
    if dead:
        bad.append("W7/deadname `%s` is back in CLAIMS_TEXT.md at line(s) %s -- "
                   "the arm is `%s`, and this file said three different things "
                   "about it once already"
                   % (RETIRED_ARM, dead, LIVE_ROW))

    return bad


def _mutations() -> List[Tuple[str, Callable[[str], str], str]]:
    def cite_placeholder_live(c: str) -> str:
        return c.replace(
            "**本条是背景数字，不是主张**",
            "待 `Theoria.md:271` 的 ⟨复现值⟩ 填入后再行核算。"
            "**本条是背景数字，不是主张**")

    def erase_every_mention(c: str) -> str:
        return c.replace(PLACEHOLDER, "该占位符")

    def half_the_premise(c: str) -> str:
        return c.replace("**存在的是另一样东西**", "**此外无他**")

    def restore_needs_human(c: str) -> str:
        return c.replace("**一条贯穿全篇的前提修正**（2026-08-02 落地",
                         "**一条贯穿全篇的前提修正（needs_human）**（2026-08-02 落地")

    def unscope_the_only(c: str) -> str:
        return c.replace("**在本实验的同壳三臂中唯一**", "**唯一**")

    def c2_untested_not_unmeasurable(c: str) -> str:
        return (c.replace("在这批材料上它**不可测**，而不是待测", "这一项本轮未测")
                 .replace("而不是待测——所以它不能作为 C2 的比较项存在",
                          "所以它暂列限制节"))

    def edit_the_prereg(c: str) -> str:
        return c.replace("**保持原样一个字不改**", "已同步改为 `theoria > bare_cc`")

    def quote_the_interval_bare(c: str) -> str:
        return c.replace("出处在仓库中不存在", "出处见上游报告")

    def delete_the_row(c: str) -> str:
        return c.replace(LIVE_ROW, "该批材料")

    def bring_back_the_dead_name(c: str) -> str:
        return c.replace("上游 Schema **未被同壳评测**",
                         "`schema_repro` **未被同壳评测**")

    return [
        ("cite the withdrawn placeholder as a value still to be filled",
         cite_placeholder_live, "W1/placeholder"),
        ("erase every mention, losing the record of the withdrawal",
         erase_every_mention, "W1b/norecord"),
        ("state only the first half of the premise correction",
         half_the_premise, "W2b/halfpremise"),
        ("put the needs_human flag back", restore_needs_human, "W2c/needshuman"),
        ("let 「唯一」 go unscoped again", unscope_the_only, "W3/scope"),
        ("downgrade C2's `unmeasurable` to `not measured this round`",
         c2_untested_not_unmeasurable, "W4b/unmeasurable"),
        ("edit the pre-registration instead of its settlement",
         edit_the_prereg, "W4d/prereg"),
        ("quote the 2.04-3.41 interval without the no-provenance finding",
         quote_the_interval_bare, "W5b/interval"),
        ("delete the surviving upstream reference row", delete_the_row,
         "W6/row"),
        ("bring the retired arm name back", bring_back_the_dead_name,
         "W7/deadname"),
    ]


def selftest(claims: str) -> Tuple[int, int, List[str]]:
    lines: List[str] = []
    passed = failed = 0

    live = check(claims)
    if live:
        failed += 1
        lines.append("FAIL positive control: the real file does not pass, so a "
                     "red from any mutation proves nothing")
        for b in live:
            lines.append("       " + b)
    else:
        passed += 1
        lines.append("PASS positive control: CLAIMS_TEXT.md passes unmutated")

    for name, mutate, want in _mutations():
        mc = mutate(claims)
        if mc == claims:
            failed += 1
            lines.append("FAIL control could not be built (%s): the text is not "
                         "where this gate expects it, so the check may be "
                         "scanning nothing" % name)
            continue
        got = check(mc)
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
    ap.parse_args(argv)

    claims = open(CLAIMS, encoding="utf-8").read()

    if "--selftest" in (argv if argv is not None else sys.argv[1:]):
        passed, failed, lines = selftest(claims)
        for line in lines:
            print(line)
        print("%d/%d" % (passed, passed + failed))
        return 1 if failed else 0

    bad = check(claims)
    for b in bad:
        print("FAIL " + b)
    if bad:
        return 1
    print("PASS the Schema column is withdrawn rather than blank, the "
          "placeholder is recorded but nowhere cited live, C1's 「唯一」 is "
          "scoped to the three same-shell arms, C2's comparator is withdrawn as "
          "unmeasurable with its pre-registration untouched, and the "
          "`schema_upstream` reference row survives with its coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
