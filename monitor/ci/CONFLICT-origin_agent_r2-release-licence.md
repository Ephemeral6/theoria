# CONFLICT-origin_agent_r2-release-licence.md
branch: origin/agent/r2-release-licence
reason: verify gate red in release (verify.sh)

```
, su15-1944f8ab, tr87-cd924810, tu93-0768757b, vc33-5430563c, wa30-ee6fef47 (source or prose; ids named here are constants and guards, not content)
  note          release/runs/20260728T234923Z-S23/after/contamination.planted.txt names bp35-0a0ad940, dc22-fdcac232, ft09-0d8bbf25, ka59-38d34dbb, lf52-271a04aa, ls20-9607627b, m0r0-492f87ba, re86-8af5384d, sb26-7fbdac44 (source or prose; ids named here are constants and guards, not content)
  note          release/runs/20260728T234923Z-S23/before/check_redlines.full_tree.txt names bp35-0a0ad940, dc22-fdcac232, ls20-9607627b, vc33-5430563c (source or prose; ids named here are constants and guards, not content)
  note          release/runs/20260728T234923Z-S23/before/check_redlines.planted.txt names bp35-0a0ad940, cd82-fb555c5d, cn04-2fe56bfb, dc22-fdcac232, ft09-0d8bbf25, ka59-38d34dbb, lf52-271a04aa, lp85-305b61c3, ls20-9607627b, m0r0-492f87ba, r11l-495a7899, re86-8af5384d, s5i5-18d95033, sb26-7fbdac44, sc25-635fd71a, sp80-589a99af, su15-1944f8ab, tr87-cd924810, tu93-0768757b, vc33-5430563c, wa30-ee6fef47 (source or prose; ids named here are constants and guards, not content)
  note          release/runs/20260728T234923Z-S23/before/contamination.planted.txt names bp35-0a0ad940, dc22-fdcac232, ft09-0d8bbf25, ka59-38d34dbb, lf52-271a04aa, ls20-9607627b, m0r0-492f87ba, re86-8af5384d, sb26-7fbdac44 (source or prose; ids named here are constants and guards, not content)
  note          theoria-arm/tests/test_arm.py names bp35-0a0ad940 (source or prose; ids named here are constants and guards, not content)
  note          verify-lab/runs/20260728T152000Z-V11-negative-control-census/ADVERSARIAL.md names ls20-9607627b (source or prose; ids named here are constants and guards, not content)
  note          verify-lab/runs/20260728T152000Z-V11-negative-control-census/CENSUS_TABLE.md names bp35-0a0ad940, ls20-9607627b, vc33-5430563c (source or prose; ids named here are constants and guards, not content)
  note          verify-lab/runs/20260728T152000Z-V11-negative-control-census/partials/exam-battery.md names bp35-0a0ad940 (source or prose; ids named here are constants and guards, not content)
  note          verify-lab/runs/20260728T152000Z-V11-negative-control-census/partials/proxy-arcrecon.md names dc22-fdcac232, ls20-9607627b, vc33-5430563c (source or prose; ids named here are constants and guards, not content)

red lines: 0 credential violation(s), 0 sealed-pile violation(s), 0 file(s) this check could not read over 5336 tracked files.
Both red lines clear. A release manifest may be generated from this tree.
-- ok

== every tracked file is classified
  note credential loaded for comparison only: 7171...05dd (len 36)
  note 5336 of 5336 tracked file(s) scanned for the literal key
red lines clear over 5336 tracked files
  A   5069 file(s)     93.70 MB  self-built -> releasable
  B     53 file(s)     31.18 MB  api-derived-compilation -> needs-written-permission
  C    213 file(s)     10.13 MB  derived-statistics -> releasable-flagged
  D      1 file(s)      0.04 MB  upstream-payload -> not-releasable

dry run: nothing written
-- ok

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

```
