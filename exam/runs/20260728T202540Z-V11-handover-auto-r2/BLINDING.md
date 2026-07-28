# Blinding — what was blocked, and what was not

> **This is the second cohort. The first one was voided by a leak of exactly the
> kind this file exists to catch, and the account of it is at the bottom under
> "The first cohort, and why it was thrown away". Read that first if you are
> auditing the result.**

Written **before** the first examinee was spawned, and committed in the same
commit as the sheet and the marking rules. The whole value of a handover test is
that the reader genuinely has no context; this file is the honest account of how
close to that we got.

## What the examinee receives

One string. Nothing else.

    exam/runs/20260728T202540Z-V11-handover-auto-r2/prompts/tier1_manual.prompt.md
    exam/runs/20260728T202540Z-V11-handover-auto-r2/prompts/tier2_manual_playbook.prompt.md

It is **pasted into the subagent's prompt**, not pointed at. No path, no
directory, no repository name, no branch, no run id, no mention of what is being
measured. The two prompts are byte-identical from `# The question sheet`
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

## The answer key was never on disk while the examinees ran

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
