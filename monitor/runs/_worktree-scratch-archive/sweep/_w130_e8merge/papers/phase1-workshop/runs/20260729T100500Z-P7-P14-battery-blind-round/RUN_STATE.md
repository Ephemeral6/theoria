# RUN_STATE — P7-P14-battery-section-blind-round

**Branch** `agent/p7-p14-battery-section-blind-round`, worktree
`.worktrees/p7-p14-battery-blind/`, base `c1a60420`. **Passive:** zero API, zero
model calls, zero network, $0.00, sealed pile untouched. No battery artefact was
regenerated; every figure was read as committed, and where two committed artefacts
disagree the section says so rather than choosing.

**Two board notes.** The item declares `territory: battery`, but its deliverable is
`papers/phase1-workshop/sections/07_battery.md`; nobody held `papers`, so there was
no collision, but the territory guard would not have caught one. And the item's
"blocked on an unmerged branch" note was stale — `ADVERSARIAL_ROUND.md` is on
master. It shares this branch with `P4-P16-e06-contradiction` because both are
paper-body items regenerating `PAPER.md`, which two branches cannot both do.

## What §7 said, and why it had to move

§7 reported one anti-gaming round. A second, blind, pre-registered round had
landed and was reported in §1.2 and §11 but not in §7 — so the paper's intro led
with numbers its own results section contradicted. Three readers were sent at the
artefacts before anything was written: a fact sheet of the blind round, a
line-by-line map of what in §7 the round makes false, and an independent attempt to
break the five limits §1.2 states.

## The rewrite

**New §7.7a** carries the round: six mutually invisible attackers, register and
exploits and reports stripped from their tree, thresholds committed before any
attack and the ordering provable by git ancestry. **105 attacks, 91 landed, 37 of
38 metrics at threshold.** The main table went from nine to two, and then to zero —
and the last two did not fall to the blind protocol: a **sighted** review took E1,
and M3 was moved to an `undetermined` tier created for it afterwards. What the
battery publishes today is `Main table (0)` against `Reference (38)`.

Knock-ons, all verified against artefacts: §7.1's "artefacts regenerate" is false
of `gaming_audit.json`; §7.2a's present-tense "the main table holds nine metrics"
is now history; §7.7's heading said the table "moved twice" and it has moved four
times; §7.7's "nineteen of the twenty metrics" is **eighteen**, settled by the
battery's own test; §7.9's punchline about the main table containing a retired
metric is void, and is kept only for the class of defect it illustrates; §7.10's
gap list gains the largest gap it lacked.

## What the checks changed in my own draft

The three readers did not merely confirm. **Three things I had already written were
wrong and are corrected in the delivered text:**

* I wrote that fifty-one of the ninety-one landing attacks fabricate producer-side
  records. **No artefact carries that count** — the attack record has no
  producer-side field — so the paper states the limit and refuses the number. The
  paper's own rule is that a number with no path does not go in.
* I wrote "the blind round took the main table from nine to two" flatly. The two is
  true of the code as it stood at the blind commit, before the `undetermined` tier
  existed; re-run through today's adjudication the same 105 attacks leave eight
  demotions, not nine. The count now carries its date.
* I wrote the strong/medium/weak demotion grading as though it were an artefact
  field. **It is prose only**, and the nine metrics graded are not the nine
  demoted — the table includes E1, which fell to the sighted review, and omits M3.

Added on the fact sheet's evidence: `battery/artifacts/gaming_audit.json` — the
file this section cites throughout, and the one `run_battery` regenerates — still
records a main table of nine. It was deliberately not rewritten. **The shipped
artefact set contradicts the shipped conclusion, and the file that contradicts it
is the convenient one.**

## Seven limits, carried and corrected

§7.7a states seven. Five come from §1.2 and two were added by the independent
check: that after the collapse `accidental` is the only author-asserted field left
in the adjudication, and that "37 of 38" is not thirty-seven findings — the round's
own section heading says so, and one label-swapping convention satisfies five
exploration metrics at once.

**One limit from §1.2 was dropped, not carried.** §1.2 lists eleven first-round
exploits that hard-code their own success. The count is right, but the flag has
been ANDed with a live re-evaluation since the day before this round, one of the
eleven now reads `False` as a result, and it is a finding about the *first* round
that was already mitigated. Carrying it as a live limit of the blind round would
have been wrong twice. What survives is narrower and is not in the paper: the
re-evaluation checks that the metric still answers, not that its value still
reaches the threshold.
