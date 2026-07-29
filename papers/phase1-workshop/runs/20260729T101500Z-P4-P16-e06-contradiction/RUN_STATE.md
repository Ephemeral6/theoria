# RUN_STATE — P4-P16-e06-contradiction

**Branch** `agent/p7-p14-battery-section-blind-round` (shared — see below),
worktree `.worktrees/p7-p14-battery-blind/`, base `c1a60420`.
**Territory:** `papers/` only. **Passive:** zero API, zero model calls, zero
network, $0.00, sealed pile untouched.

**Why this item shares a branch with P7-P14.** Both are paper-body items held by
RES-2 at the same time, and both regenerate `papers/phase1-workshop/PAPER.md`.
Two branches each carrying a different rebuild of the same generated file conflict
on merge by construction. They are committed separately on one branch so the
history still reads item by item. Flagged rather than done quietly.

## The question the item posed

`sections/04_a1.md` headed a subsection "What A1 did not settle: E-06, an open
problem", while the ledger it cites now marks E-06 **discharged**. The item's
instruction was to decide from the ledger: either E-06 is discharged and §4.4 is
rewritten, or it is not and `theory-compiler/STATUS.md:165` is wrong.

## Decided: discharged. Two sources agree, and the third contradicts itself.

* `cold-start-a0/THEORIZE_LOG.md:362` — E-06 → **discharged**, reason recorded as
  "the certificate covers what it covers, exhaustion closes the rest, each goal
  attributed to its method".
* `theory-compiler/STATUS.md:159` — delivery 3, the *transcription* half of E-06,
  清偿. `:165` — delivery 8, the *proof* half, 清偿, "两条论证分开署名".
* `theory-compiler/STATUS.md:325` — still heads "未清偿：新增台账 E-06".

**The file books it both ways, and the ordering is the thing to get right.** The
`:325` block describes E-06 as newly added and calls it "本 sprint 唯一的开放问题"
— the only open problem of *that* sprint. The `:165` delivery table is a later
sprint's. So the file is newest-first at sprint level, and the discharge is the
later record. That reading is corroborated by the ledger, which is the artefact
§4.4 actually cites.

`STATUS.md:165` is therefore not wrong. The paper was.

## What changed

* **`sections/04_a1.md` §4.4** — retitled "What A1 did not settle, and how E-06
  was closed afterwards". The whole technical account is unchanged and still true:
  `lp_potential` cannot certify `10000`, `00100`, `00001`; `test_interop.py` pins
  it; the compiler answers with `CertificateGapError` and refuses to generate. What
  is added is how the entry closed — **not** by extending the invariant language,
  but by closing the remaining goals with a second method and attributing every
  goal to whichever method proved it. That is the same discipline as the refusal,
  one level up: first "do not state what you cannot certify", then "do not let one
  method's success be read as another's". The `STATUS.md` self-collision is named
  in the paper rather than resolved silently in its favour.
* **`sections/11_limitations.md`** — records the discharge and states explicitly
  that the limitation below it is unaffected: the linear pagoda method still cannot
  reach those three end states.
* **`sections/02_framework.md`** — `ic3_pdr` is still "not exercised by any result
  below", but the sentence now says why it is the closer of the two: the compile
  chain's consumer side is complete and the emitter is an unwritten `engine-rig`
  file (`STATUS.md` delivery 9). A consumer with nothing to consume still produces
  no result.

## Reported, not fixed — outside this item's territory

`figures/fig06_concept_timeline.py:64` still says "the seven expressivity-ledger
rows" in its module docstring while the declared id set at `:108` now carries nine
(E-01…E-09). The set was corrected in an earlier item; the prose above it was not.
`figures/` is not this item's territory. Filed to `monitor/inbox/`.
