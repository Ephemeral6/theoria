# RUN_STATE — R3, the desk refused on principle

**Cell:** R3 · **Territory:** `theoria-arm` · **Branch:** `z/r1b-goal-rider`
**Spend:** $0.00. No ARC action, no model call, no network, no ledger. Sealed
pile: zero contact. Nothing under `runs/` was written except this directory.

## What was asked

Understand R1b's result. The round turned on `goal_protocol=propose`; the arm
proposed and its mode moved off silence, and then `goal_declared_ever` stayed
`False`, `plan` reported `no_goal_declared` 16 of 16, and no level completed.
Establish from the records whether the desk (a) never saw the rider, (b) saw it
and ignored it, (c) answered and the answer never reached the manual, or (d)
answered and the parser rejected the clause — and fix it offline.

## What the records say

**The two legs are two different answers, and the round reported one.**

`R1b-g50t-a` is (b′): the rider was delivered three times and refused three
times, with the named theorem
`the_goal_is_absent_because_no_instance_can_name_the_socket`, whose body
enumerates the four goal forms this grammar admits and refutes each against the
frame in front of it. The refusal is about **expressive reach**, not
confidence: the socket cells have never changed, so they are board, so no
instance is seated on them, so no `count` ranges over them and no landmark
names them. The mechanism connected exactly as designed. What did not move is
the desk's mind, and it gave its reasons.

`R1b-sk48-b` is (a): the ask was booked on turn 1 and never posted. The rider
parks for the next theorize call a surprise pays for; turns 2–4 skipped
theorize under the new-transitions gate, the beat after that lost all five of
its replies in transit, and the leg hit its spend reservation. Nothing on that
leg is evidence about the rider's wording.

**Neither is (d). There is no parser bug here.** `answer_proposal` read every
delivered reply correctly, and `absence_signature` found the signature the
moment the manual carried one.

**And a defect nobody was looking for: (c), 11 times, $31.05.**
`harness/modelcall.py:561` reads `envelope["result"]`, the CLI's *last*
assistant message. When a reply spans messages the earlier ones are dropped and
what lands on disk is a tail — `R1b-sk48-b/desk/call-002` begins mid-header at
`=== THEORY (continued …) ===`, `call-006` begins mid-word at `ditional
repaint`. `inner/theorize.py` recorded all 11 as `no THEORY block in the
reply`, which reads as a bad answer and is a lost one. **28.6% of this arm's
lifetime desk bill; 56% of R1b itself; $14.03 of `sk48-b`'s $17.39** — which is
why that leg had no theorize call left to carry its goal ask.

## What was built

* `armtools/replyloss.py` — a closed four-class reading of every archived desk
  reply, decided **structurally** (all 53 accepted replies begin with `===
  THEORY ===`; none of the 35 rejected do) rather than by a token ratio, which
  does not separate them because `claude -p` bills thinking tokens that never
  reach `result`.
* `armtools/goal_forensics.py` — a closed eight-verdict reading of the goal ask
  per leg, plus readers that pull the refusal's *argument* out of the manual,
  not only its name.
* `inner/goal.py` — three record fixes and one prompt change. `refused_because`
  no longer quotes a failed check as an affirmative sentence; `record_proposal`
  / `mark_delivered` separate **booked** from **posted** so `answered: null`
  stops meaning two things; the rider grows a third channel asking the desk to
  name the target it cannot compile, under a findable name.
* `inner/loop.py` — one line: tell `GoalState` when the rider leaves the peg.

## Judging the prompt change without a live leg

It cannot be judged for effect offline and is not claimed to be. Its base rate
is measured rather than guessed — the desk produced exactly this artefact
unprompted on 2 of 2 legs that got that far — and its reading half is
fixture-tested and pays off regardless. A live judgement is one carried
`g50t-5849a774` leg from the r3 seed books at leg ceiling $25:
**$17–25, ~9 desk calls, ~25 ARC actions**, settling only whether a desk given
somewhere to put its target uses it. **Not run. Zero spend authority.**

## Blocked / residual

* The transport is **diagnosed, not repaired**. The fix is `--output-format
  stream-json` or an accumulation in `_invoke`, and it cannot be validated
  without a live call, so it is filed and not attempted.
* The goal grammar is the real blocker and is `theory-compiler`'s. It is the
  same missing thing as R2's 12 expressivity misses. Filed for
  `monitor/inbox/`, not acted on from here.
* Two gates were **already red on master `e8345aff`** before this branch
  existed, verified on a detached pristine worktree: `verify_provenance` check
  8 (manifest re-derivation drift on the four R1/R1b legs) and
  `test_the_ceiling_table_still_covers_the_archive`. Recorded in `GATES.txt`
  as inherited, not introduced.

## Next

The transport, first and alone. Until it is fixed, an A/B on any knob is
measuring a coin flip: `sk48-b` lost 5 of 6 replies and would have "failed" any
change whatsoever.
