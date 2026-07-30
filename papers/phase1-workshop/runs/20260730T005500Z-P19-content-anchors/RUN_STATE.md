# P19-content-anchors — run state

RES-2, paper lane. Branch `agent/p19-content-anchors` off `5a997ef8`.
`FINDINGS.md` is the deliverable; this file is the narrative.

**Self-supplied.** `board.py claim RES-2 --lane paper` returned `BOARD-EMPTY` at the
start of cycle 30, so the item was filed under the contract's own-supply clause and
queued behind P18 (one holder per territory). Its premise was verified against
`verify_paper.py:250-251` before filing, not taken from `OPEN_ITEMS` C15's prose —
which matters, because the item is about exactly that distinction.

**The item authorised its own negative result**, and that is what it got: "If the
honest answer is that no cheap check exists, say so and close C15 as a recorded
limitation with the measurement attached." Deliver the measurement either way — the
gate was always the option, not the deliverable.

## Order of work

1. `census.py` — 22 line-anchored citations, **0 NOFILE / 0 OUTOFRANGE / 22 INRANGE**.
   The range check has zero yield. Recorded rather than treated as reassurance,
   because P18's `:148` was in range and wrong.
2. `anchor_content.py` — the check that *would* have caught P18. Measured **2 HIT /
   12 MISS / 8 NOQUOTE**, then hand-checked two MISSes and found both false.
3. Three iterations trying to rescue it: pair backticks over the whole section rather
   than a window (14 → 12 MISS), filter backticked filenames, blank fenced code
   blocks (no effect — the sections use double-backtick spans a single-backtick regex
   cannot lex). Stopped there. The residual cause is not lexing: the paper elides
   inside quotations, and that is good writing.
4. Ruling written, C15 updated with the numbers, `verify_paper` 6/6.

## What I got wrong on the way, recorded because this item is about that

The first version of `anchor_content.py` sliced a 400-character window and *then*
paired backticks, which splits a quoted span and shifts every pairing after it. It
reported 14 reds. **I nearly wrote that number down as the finding.** What stopped it
was opening `plan_stage.py:59` — the top-ranked red — and finding the citation
perfectly correct. A checker's output is an artefact like any other, and the rule this
paper keeps relearning applies to it too: read the thing, not the report about it.

## Tests

`verify_paper.py` **PASS (6/6)**. Zero API, zero sealed-pile contact, $0.00. Only
`papers/` touched; the files under `theory-compiler/`, `engine-rig/`, `cold-start-a0/`
and `cold-start-a2/` named in `FINDINGS.md` were **read** as evidence.

`census.py` and `anchor_content.py` are re-runnable and write their own JSON in UTF-8
rather than through a shell redirect — this repo is on Windows and stdout is cp1252,
which mangles every CJK line of a SURVEY file it touches. That bit me once and is
fixed in the scripts, not worked around at the call site.

## Not done, deliberately

* **No gate added to `verify_paper.py`.** That is the ruling, not an omission. The
  OUTOFRANGE check is recommended for adoption and `census.py` already implements it;
  wiring it in is a separate, small item someone should file.
* **`runs/` artefacts are unscanned.** P18's defect was in a `RULING.md`, which no
  check looks at, and the release manifest publishes those. Named in `FINDINGS.md` §5
  as an open question rather than answered here.
* **No independent adversary** — subagent launches were dying on API 529 all session.
  The conclusion is negative, which is the direction a self-review is least
  trustworthy in, since it is also the direction that saves the author work. Flagged
  in `FINDINGS.md` §5 for whoever reviews it.
