# P19 · The anchor exposure, measured — and why the cheap gate does not exist

RES-2, 2026-07-30. Item `P19-P19`, self-supplied after `board.py claim --lane paper`
returned `BOARD-EMPTY`. Base `5a997ef8`.

The item asked for three things: measure the exposure, decide what an anchor is, and
**say so plainly if no cheap check exists** rather than shipping a gate that passes by
adjudicating everything. The answer is the third one, and the measurement is why.

## 1 · The gap is real, and it is narrower than C15 implies

Verified against the gate rather than its description. `verify_paper.py:250-251` is the
whole of check B's evidence:

    at_root  = (ROOT / token).exists()
    at_local = (HERE / token).exists()

`classify()` (`:232-265`) returns ok / RULED / AMBIGUOUS / ELIDED / BROKEN from path
resolution alone. **Nothing in the gate opens the cited file.** So the paper's citation
checks certify that a reader can follow a link and say nothing about what is at the
other end. `OPEN_ITEMS` B4 named the sharper half — "check F resolves the file, nothing
resolves the anchor inside it" — and P18 then produced the instance:
`TheoriaLean.lean:148` cited for a line that is at `:149`, in the one citation carrying
that ruling's refusal of C12.

## 2 · Measurement: `census.py`

**22 line-anchored citations** across 4 sections (18 in §10, 2 in §5, 1 in §4, 1 in
§11). Reproduce with `python census.py`; `census.json` is the row-level output.

| verdict | count | meaning |
|---|---|---|
| NOFILE | **0** | the cited file does not resolve at all |
| OUTOFRANGE | **0** | file resolves, but has fewer lines than the anchor names |
| INRANGE | **22** | the anchor lands inside the file |

**A range check would catch nothing on this paper — zero yield.** That is not
reassurance: P18's `:148` was in range and wrong. The cheapest mechanically-certain
gate is exactly the one with no value here, and stating its yield as 0 is the point of
measuring rather than assuming.

One thing the census settled in passing: the four `SURVEY-*.md` citations resolve, to
the byte-verbatim copies under `runs/20260729T140000Z-P14-honesty-section/inputs-verbatim/`.
§10.7 says the *originals* are untracked on an unpushed branch and that the paper
therefore cites committed copies whose line numbers are the ones used. **§10.7 is
accurate, not stale** — checked because P17's round flagged those citations as the
weakest in the paper.

## 3 · The check with real yield, and why it fails: `anchor_content.py`

A range check cannot catch an off-by-one, so the only check worth building is a
**content anchor**: when a section quotes a string beside a line anchor, require the
quote to appear inside the cited range. The quote is already in the paper, so it costs
no maintenance — which is the property the item demanded.

Measured over the 22: **2 HIT, 12 MISS, 8 NOQUOTE.**

**The 12 MISSes are dominated by false reds, and I hand-checked two of them:**

* `cold-start-a0/pipeline/plan_stage.py:59` (§11) — the line really is
  `plan = fd_adapter.solve(domain, instance, prefer="stub")`. The paper quotes it as
  `solve(..., prefer="stub")`. **The citation is correct; the elision defeats a
  substring test.**
* `gen_lean.py:722-724` (§4) — line 722 reads `closes it with an empty axiom set. The
  two proofs are kept **separate and`, and the paper's quotation "kept **separate and
  attributed**, because they are not the same argument" does span 722-724. The check
  never even tested that quote: it extracted three junk fragments instead.

Three distinct causes, and only the first two are fixable:

1. **Backtick pairing over markdown is unreliable.** The junk spans (`" and unsafe at "`,
   `" plus 11 backticked paths in the prose at "`) are the *text between* two real
   quotations — the pairing is shifted. Slicing a window before pairing caused part of
   it; blanking fenced blocks did not fix the rest, because the sections also use
   double-backtick spans (`` `` `x` `` ``) that a single-backtick regex cannot lex.
   A correct version needs a real CommonMark inline lexer, not a regex.
2. **Backticked filenames are citations, not content.** Filtered, and it moved MISS
   from 14 to 12.
3. **The paper legitimately elides inside quotations.** `solve(..., prefer="stub")` is
   *good* writing — the argument list is noise at that point. No substring or
   normalisation trick handles this, and demanding verbatim quotation would make the
   paper worse to read. This cause is not a bug in the checker.

## 4 · Ruling: do not build this gate. Close C15 as a recorded limitation.

The item authorised this outcome in advance, and the measurement earns it.

A content-anchor gate on this paper would need a CommonMark inline lexer plus fuzzy
matching tolerant of deliberate elision. That tolerance is precisely the tuning surface
that produces false reds, and **this paper has already paid that tuition twice**: P16
learned that a noisy gate gets its summaries adjudicated into silence, and P17's F BARE
shipped only because it fires on *ambiguity* rather than on bare-ness. A gate whose 12
reds are all false gets disabled in one sitting, and a disabled gate is worse than a
documented limitation — it reads as coverage.

What to do instead, in order of value per unit of work:

1. **Adopt the range check anyway, at zero current cost.** Yield is 0 today, which
   means it is free to turn on and it can never regress silently: a future citation
   naming line 900 of a 300-line file becomes red immediately. `census.py`'s
   OUTOFRANGE verdict is that check, already written. It catches a *different* defect
   from P18's, and catching a cheap subset is honest as long as nobody calls it
   coverage.
2. **Prefer anchors that name themselves.** B4's true fix was not a line number: the
   segmentation block names itself `D-A0-007` at `THEORIZE_LOG.md:86`. A self-naming
   anchor survives edits to the file; a line number does not. This is guidance for
   authors, not a gate.
3. **Record that line anchors decay.** All 22 are correct today and none is protected
   by anything. That sentence belongs in `OPEN_ITEMS`, because it is true and no check
   changes it.

## 5 · What this run does not establish

* **The census covers `sections/` only.** P18's defect was in a `runs/…/RULING.md`, and
  no gate scans run artefacts. Whether it should is a real question this item did not
  answer — the release manifest publishes them.
* **"All 22 INRANGE" is not "all 22 correct".** I hand-verified two, plus P18's, and
  read the anchored line of every one in the census output. That is a spot check, not
  a proof, and the number of anchors whose *content* is wrong is unmeasured. Saying so
  is the only honest option, given that this item exists because a stated count with
  an invisible criterion is the defect.
* **No independent adversary.** As in P18: subagent launches were dying on API 529
  through this session. The conclusion here is a negative one — "do not build it" —
  which is the direction where a self-review is least trustworthy, since it is also
  the direction that saves the author work. Flagged deliberately for whoever reviews
  this.
