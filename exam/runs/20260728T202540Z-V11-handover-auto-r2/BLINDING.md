# Blinding — what was blocked, and what was not

> **Two corrections were made to this file after the adversarial review; both
> are marked CORRECTION below and neither is a rewrite of history — the
> superseded wording is quoted where it stood. This is also the second cohort:
> the first was voided by a leak of exactly the kind this file exists to catch,
> and the account is at the bottom under "The first cohort, and why it was
> thrown away". A third leak, worse than either, was found by the review and is
> under "CORRECTION 3".**

Written **before** the first examinee was spawned, and committed in the same
commit as the sheet and the marking rules. The whole value of a handover test is
that the reader genuinely has no context; this file is the honest account of how
close to that we got.

## What the examinee receives

One string. Nothing else.

    exam/runs/20260728T202540Z-V11-handover-auto-r2/prompts/tier1_manual.prompt.md
    exam/runs/20260728T202540Z-V11-handover-auto-r2/prompts/tier2_manual_playbook.prompt.md

**CORRECTION 1 — this paragraph was false when written.** It said:

> It is **pasted into the subagent's prompt**, not pointed at. No path, no
> directory, no repository name, no branch, no run id, no mention of what is
> being measured.

The plan was to paste. What was actually done was the work order's other
sanctioned option: each reader was given the absolute path of a temporary
directory containing exactly one file, `TASK.md`, holding the prompt below and
nothing else, and told to read that file and nothing else. The reason was
context budget — six prompts of 43–51 KB pasted into six tool calls is 90 000
tokens of the orchestrator's window — and that reason is not good enough to
excuse leaving the note describing a mechanism that was not used. The
adversarial review caught it from the readers' own `TOOLS:` lines.

Three consequences, all real:

* a reader given a path has a working directory and therefore somewhere to look
  around from, which weakens the "the key file does not exist yet" argument
  below;
* the per-reader directories were named `A1 A2 A3 B1 B2 B3`, and `B3` is an arm
  label. The prompt passes the test forbidding `tier 1`/`tier 2`; the directory
  name reintroduced the signal outside the tested surface;
* **the artifact that was tested was not the artifact that was delivered.** The
  three blinding tests run against `prompts/*.prompt.md`; each reader received a
  short wrapper message naming `TASK.md` plus that file. The wrapper is now
  written down and hashed as `prompts/DELIVERY_WRAPPER.md`, which it should have
  been from the start.

No path, no repository name, no branch, no run id and no statement of what is
being measured appear *inside* the prompt; those parts stand and are tested. The two prompts are byte-identical from `# The question sheet`
onwards; they differ only by the playbook and by the one sentence naming which
documents are in the bundle.

`exam/tests/test_handover_auto.py` tests that as a property of the string:

* `test_the_prompt_names_no_place_the_reader_could_go` — 18 forbidden
  substrings (`a0-spike`, `exam/`, `artifacts`, `Theoria.md`, `PARTNER_SYNC`,
  `handover_auto`, `v11-handover-a0`, …). This is the **V15** failure: a
  tracked file that was in every checkout named the one false positive in the
  matrix. A prompt that names a place is an invitation to go there.
* `test_the_prompt_carries_no_answer` — every leak probe the paper declares,
  run against the *prompt* and not only against the sheet. This is the **V17**
  failure: the criteria document itself handed over the answers. Here the
  criteria are the answer *grammar* (which every examinee must have) and never
  a worked item.
* `test_the_prompt_does_not_say_which_tier_the_reader_is_in_relative_terms` —
  the brief may not contain `tier 1`, `tier 2`, `compare`, `the other`,
  `measur`, `hopeless`, `unsolvable`, `impossible`.

That last one caught a real leak in P-15's brief, which told the tier-2 reader
that its playbook covers "which situations are hopeless and why". Two of the
eight optimal-action items on this sheet are boards with no solution. A brief
that primes one arm to expect hopeless boards manufactures the difference the
run exists to measure, and the manufactured part is indistinguishable from the
real part afterwards. Both tier lines were rewritten to say only which documents
are in the bundle.

## The answer key was never on disk while the examinees ran — but a re-encoding of it was

**CORRECTION 2.** The heading above is true of the key *file* and false of the
key's *content*. `build()` wrote its whole leakage report into
`PREREGISTRATION.json`, and that report contains
`positional.example_ids_by_answer`, a literal map from answer label to item
ids — including `"none": ["v11-opt-01", "v11-opt-04"]`, which is precisely the
fact the first cohort was voided for. The adversarial review marked a submission
built from that file alone, against the real rubric and the real key, and scored
**0.569**; adding the `label_counts` block takes it to **0.603**. That is above
this paper's own memoriser calibration arm, from a reader that never saw the
manual.

It was on disk, in the examinees' own run directory, for the whole run.
`test_the_driver_freezes_the_key_without_writing_it` walked that directory and
reported 61 declared probes and 0 hits, because the probes look for
`"v11-opt-01 => none"` and the leak was spelled `"none": ["v11-opt-01"]`. Same
failure as D-EX-018, one commit later: a checker matching a spelling.

`build()` now persists counts and hit totals only, and says in the file that the
positional block is withheld and why. That change was made after this run and
does not retroactively clean it.

### The original claim, which stands only as far as the key file goes

`build` writes the sheet and the prompts, and writes the key's sha256 —
`f21ee3d66ebc` — into
`PREREGISTRATION.json` **without writing the key**. `build()` is deterministic,
so `score` re-derives the key and refuses to mark if the digest has moved.

This is not belt-and-braces. The examinees are subagents on this machine with a
shell. "Do not look" is an instruction; "the file does not exist yet" is a fact.
`test_the_driver_freezes_the_key_without_writing_it` walks the run directory
after `build` and asserts no declared probe hits anything in it.

## Pre-registration, by commit order

1. Commit **A** — the marking rules (`exam/grading/rubrics_handover_auto.py`),
   the paper (`exam/papers/handover_auto.py`), the driver, the tests, this file,
   `PREREGISTRATION.json` with the frozen sheet and key digests and the written
   prediction. *No examinee has run.*
2. The six examinees run.
3. Commit **B** — the raw answers, exactly as returned.
4. Commit **C** — `RESULTS.json` and the write-up.
5. Commit **D** — the adversarial review, verbatim, and any correction it forces.

`git log --stat` is the evidence. V10 was called out tonight for having no such
ordering; there is no excuse for not producing it.

The **prediction** is in `PREREGISTRATION.json` and in
`exam.papers.handover_auto.PREDICTION`, frozen in commit A: the delta should
land on `optimal_action` and specifically on `cairn`, should be absent on
`step_semantics` and `name_class`, and **any tier scoring above 0.95 means the
sheet saturated and the delta carries no information whatever its sign**.

## What is NOT blocked — the residue

Listing these is the point of the file. A blinding note that claims a clean seal
is a blinding note nobody should believe.

1. **The examinee's own weights.** The reader is an instance of a model that may
   have been trained on this repository, on Sokoban, or on push-two-cells
   variants of it. Nothing here can block that. A reader that already knows
   Sokoban starts ahead on `optimal_action` in a way the manual did not buy.
   Both tiers draw from the same pool, so it inflates both and should not bias
   the *difference* — but it does put a floor under both tiers and brings
   saturation closer, which is why the saturation rule is pre-registered.

2. **The examinee has tools.** There is no tool-less subagent type available.
   The prompt forbids their use and asks for a `TOOLS:` self-report, which is
   evidence and not proof. A reader that ignored the instruction could:
   * run `python -c "from exam.papers.handover_auto import build"` and read the
     key out of the builder — the strongest available cheat, and the reason
     commit A must be checked against the tool reports;
   * read `a0-spike/world/sokoban2.py`, the ground-truth simulator, which is
     strictly more than the manual;
   * read `exam/artifacts/truth/p15-handover-a0.truth.json`, which is a
     *different* sheet on the same world but teaches the five rules verbatim.

3. **The deliverable points out of itself.** `MANUAL.dsl` is shipped verbatim,
   as it must be, and its comments cite `../THEORIZE_LOG.md`,
   `CONTRACTS/dsl_grammar_v0.2.md`, `probes/semantics_probe.py` and
   `runs/20260728T040057Z-c2/RUN_STATE.md`. Every one of those is a real path in
   this repository. Redacting them would mean examining a document nobody ships.
   They are the most likely accidental route out of the bundle, and the first
   thing to check in the tool reports.

4. **The bundle is not P-15's bundle.** `a0-spike/theory/theory.dsl` migrated to
   grammar v0.2 and gained a `semantics:` section since P-15 ran. This run reads
   the manual live, so tier 1 here is the deliverable as it stands today. No
   score in this run may be differenced against a P-15 score. A second
   consequence: `render_manual` predates the new section and omits it from
   `MANUAL.md`, so the `.dsl` is strictly more informative than the `.md` — a
   reader who only reads the English gets less than one who reads the source.

5. **n = 3 per tier.** Three readers per arm is enough to put an interval on the
   difference and not enough to make it narrow. The interval is reported and the
   run refuses to call a difference a finding unless it clears both that
   interval and an interval over items.

6. **The author of this exam knows the world.** The items and the key were
   written by an agent with the oracle in hand — that is unavoidable, since
   somebody has to know the answers. What is avoidable is the marking rule
   moving afterwards, and that is what commit A and the rubric digest
   (`63ce1eabcc32…`) are for.

7. **`abstain` is unpriced.** It scores zero, like a wrong answer, and is only
   recorded separately. A reader that abstains everywhere and a reader that
   guesses everywhere both score near zero, so this sheet cannot tell an honest
   reader from a reckless one by score alone. The counts are in the report;
   nothing in the delta uses them.

## The first cohort, and why it was thrown away

Run `20260728T202101Z-V11-handover-auto` was built, committed, and six readers
were spawned on it. While they were reading, an inspection of the sheet found
this on the two boards with no solution:

    "tags": ["optimal_action", "level:stile", "dead"]

`Item.tags` is printed on the sheet. The word `dead` is the answer to the two
sharpest items on the paper, written beside the question. The readers could not
be recalled — a spawned subagent cannot be stopped by the agent that spawned it
— so the cohort was allowed to finish and its answers are kept, clearly marked,
as evidence about the leak rather than as a result. **No number from cohort 1
appears in `RESULTS.json`.**

**Why the leak checker did not catch it.** `leakage.metadata_hits` buckets on
the whole value of `tags`. Every item also carries a unique `level:` token, so
every bucket held exactly one item, and the checker skipped them all under its
own rule that a field taking a different value on every item is an identifier
and predicts nothing. That rule is true of *values* and false of *tokens*. The
leak sat in a token inside a value that was unique for an unrelated reason.

**What now stands there.** `test_no_single_tag_token_predicts_an_answer` buckets
on each tag token separately, within one answer alphabet, and fails any token
that appears on more than one item, on fewer than all of them, and agrees with
the answer every time. Run against the tags that shipped it reports exactly one
offender, `('dead', ['none'], 2)`. The generalisation — that `leakage.py` should
bucket tokens and not values — applies to all four P-15 papers and is recorded in
`exam/STATUS.md` rather than fixed here, because changing a shared checker in the
middle of a run is how the next run gets voided.

**The honest reading of this episode.** The three defences that were designed and
tested — forbidden substrings, declared probes, brief wording — all held, and the
leak came in through the one channel none of them watched. That is the pattern
the work order named: 泄漏面会跟着证据走，堵一处它换一处. It is recorded here
rather than quietly fixed because a blinding note that only lists the leaks it
prevented is worth nothing.


## CORRECTION 3 — the leak that took the result, found by the adversarial review

The sheet handed the control arm the treatment.

Two `rule_justification` items state, in English and as claims whose truth the
question presupposes, exactly the playbook's two `prune` entries:

* `v11-why-02` restates `prune parity(Box.pos) != parity(target) => dead`
* `v11-why-05` restates `prune no_direction_admits_a_push(Box.pos) => dead`,
  with the off-board case — the part that decides `cairn` — spelled out.

The playbook is tier 2 only. The tier-1 paper therefore contained both prunes.
The review showed the two printed criteria are jointly a complete and sound
classifier for all eight optimal-action items: dead on exactly the two dead
boards, no false positives, with no manual, no playbook and no search.

`PREREGISTRATION.json` pre-registered `optimal_action`, and `cairn` inside it, as
the only place a difference should appear. That is exactly where the
contamination landed. **The manipulation did not happen**, and no reading of this
run can recover the tier comparison.

`exam.papers.handover_auto.cross_item_leak_report` is the check that would have
caught it, added afterwards; `test_no_new_sheet_claim_restates_a_playbook_entry`
pins these two so a third fails the suite. The items themselves are left on the
sheet: six readers answered this paper, and editing it now would leave a run
whose artefacts describe a paper that never existed.

## What the residue list got wrong

Residue 1 below says the two dead levels are the only ones appearing once in the
optimal family. True, and secondary. The review found a worse one that was not
listed: the counterexample item `v11-why-ce-01` prints five boards *with their
start positions drawn*, and three of those five draw the Box on an even row —
which is what the item asks the reader to find. Four of the six readers answered
with the `cairn` start state copied verbatim out of the picture. Only two
constructed a position of their own.
