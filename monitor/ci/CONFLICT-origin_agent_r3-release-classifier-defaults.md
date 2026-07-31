# CONFLICT-origin_agent_r3-release-classifier-defaults.md
branch: origin/agent/r3-release-classifier-defaults
reason: verify gate red in release (verify.sh)
tip: e8d95c53683390ecf28260a19d35fe02412fbedb
base: edb6e6886ca0a8ffac1a8b4323dfc570a31a0590
first_seen: 2026-07-29T18:32:53Z
last_seen: 2026-07-30T22:44:24Z
attempts: 24

```
--- cause lines (lifted out of the transcript) ---
-- FAILED (exit 1)
  figures/paper/dark/figure6_bill_shape.pdf: names ARC game(s) ar25-0c556536, g50t-5849a774, sk48-d8078629, tn36-ef4dde99 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xac in position 10: invalid start byte, so whether it carries environment payload is undetermined
  figures/paper/light/figure6_bill_shape.pdf: names ARC game(s) ar25-0c556536, g50t-5849a774, sk48-d8078629, tn36-ef4dde99 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xac in position 10: invalid start byte, so whether it carries environment payload is undetermined
  theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt: names ARC game(s) g50t-5849a774 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa1 in position 1805: invalid start byte, so whether it carries environment payload is undetermined
--- tail of the transcript ---
not read over 6708 tracked files.
Both red lines clear. A release manifest may be generated from this tree.
-- ok

== every tracked file is classified
  note credential loaded for comparison only: 7171...05dd (len 36)
  note 6708 of 6708 tracked file(s) scanned for the literal key
red lines clear over 6708 tracked files
  ?      3 file(s)      1.30 MB  undetermined -> needs_human
  A   6317 file(s)    171.60 MB  self-built -> releasable
  B     72 file(s)     96.52 MB  api-derived-compilation -> needs-written-permission
  C    315 file(s)     27.26 MB  derived-statistics -> releasable-flagged
  D      1 file(s)      0.04 MB  upstream-payload -> not-releasable

dry run: nothing written
-- FAILED (exit 1)

== no checklist item rests on an unclassified file
7 present, 3 withheld, 0 absent, 0 undetermined
  WITHHELD     全部账本  (18 file(s))
  PRESENT      两本书（各形态）  (138 file(s))
  PRESENT      Lean 证明  (25 file(s))
  PRESENT      候选箱  (33 file(s))
  WITHHELD     探针日志  (10 file(s))
  PRESENT      电池代码与回算结果  (49 file(s))
  PRESENT      冻结清单  (2 file(s))
  PRESENT      incident ledger  (3 file(s))
  PRESENT      复跑说明  (1 file(s))
  WITHHELD     runs 档案（P5 条目追加）  (488 file(s))
-- ok

== the S23 before/after archive still reproduces
base ref: bac8282
  check_redlines before: exit 0
  check_redlines after: exit 2
  contamination before: exit 0
  contamination after: exit 1

wrote before/ and after/ under release\runs\20260728T234923Z-S23

Before: both checks reported CLEAN on inputs they could not read.
After:  both report the failure and exit non-zero.
-- ok

VERIFY: RED

3 tracked file(s) could not be classified and are in the manifest as class ? / needs_human. A licence class has NOT been established for them, so this enumeration is not a finished manifest:
  figures/paper/dark/figure6_bill_shape.pdf: names ARC game(s) ar25-0c556536, g50t-5849a774, sk48-d8078629, tn36-ef4dde99 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xac in position 10: invalid start byte, so whether it carries environment payload is undetermined
  figures/paper/light/figure6_bill_shape.pdf: names ARC game(s) ar25-0c556536, g50t-5849a774, sk48-d8078629, tn36-ef4dde99 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xac in position 10: invalid start byte, so whether it carries environment payload is undetermined
  theoria-arm/runs/20260728T233900Z-A3-campaign-devpile/pytest-baseline.txt: names ARC game(s) g50t-5849a774 but UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa1 in position 1805: invalid start byte, so whether it carries environment payload is undetermined

```
