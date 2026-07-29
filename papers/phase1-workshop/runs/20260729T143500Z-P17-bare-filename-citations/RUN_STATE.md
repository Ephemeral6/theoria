# P17 — check F: the citation neither check was reading

`prompt_id` P17-P17-bare-filename-citations · branch
`agent/p17-bare-filename-citations` · base `bb06b8d9` (P16 merged with
`origin/master`) · RES-2 · zero API calls, zero sealed-pile contact.

## The hole

P16 closed "a quantitative claim with no path at all". Triaging it surfaced the
next class, and this one falls between **two** checks rather than outside one:

* **check B** skips a token with no `/` **by design** — it resolves *paths*, and
  a bare filename is not a path;
* **check E** accepts a bare filename as a citation if the basename exists
  anywhere in the tree.

So `` `MANIFEST.json` `` — **125 real files in this repository** — satisfied both
while pointing a reader at none of them. The paper's binding rule is that every
citation is repo-relative, and for this form nothing enforced it.

The bar check F sets is **ambiguity, not bareness**. A filename with exactly one
candidate is locatable, which is what the rule protects; making the paper spell
out every `Theoria.md` would be noise, and a noisy gate gets switched off. P16
learned that the expensive way with the abstract.

## The census, because B1 was prose

`OPEN_ITEMS.md` B1 already knew about this and stated it as "22 distinct paths,
30 occurrences, 9 ambiguous across 6–24 candidates". A number in a checklist
cannot be re-run and cannot go stale loudly, so the first deliverable is
`census.py`, which writes `census.json`:

```
108 occurrences · 32 distinct · 13 ambiguous tokens across 19 occurrences
```

over the 12 body sections. That **disagrees with B1**, and not only through
drift: B1 states no method, so there is no way to reproduce its 22/30/9 or to
tell which of the two is counting what. Counting the abstract as well gives
110/34; the ambiguous 13/19 is the same either way, and that is the number the
gate acts on.

Worst offenders: `MANIFEST.json` 125 candidates, `ground_truth.json` 41,
`raw_trace.jsonl` 39, `playbook.dsl` 15, `theory.dsl` 13, `STATUS.md` 9,
`FINDINGS.md` 9, `THEORIZE_LOG.md` 6 (cited 6 times).

## The 19

**14 resolved, 5 generic, 0 unresolved.** Most were settled by something only
one candidate has — an entry id, a quoted value, a field name, a line count.
Not all: two were settled by convention, and saying "every one was decided on
content" (as an earlier commit message here did) is not true of those two. They
are named below.

The ones worth naming, because they show the method:

* `raw_trace.jsonl` → `cold-start-a0/artifacts/raw_trace.jsonl`. The paper says
  **276-frame**; that file has exactly 276 lines, its two rivals 111 and 248.
* `leakage.json` → `exam/artifacts/leakage.json`. The claim is
  `label_sets_checked: []` for two of four papers; the rival file **has no such
  key at all** — it is a different schema.
* `dividend.json` → `engine-rig/runs/p13-fd-real/dividend.json`. The claim is
  about `same_answer`, a field the two other `dividend.json` do not carry, and
  about `json.dump` running before the Markdown renderer — which is the write
  order in the tool the sentence names.
* `THEORIZE_LOG.md` ×4 → `cold-start-a0/THEORIZE_LOG.md`, each by its own quoted
  content: "the three pairs R-05 named" appears in that file and nowhere else;
  Round 0 "opens on 28"; P-03 has no bold verdict there while A2's P-03 *does*
  have one; the 6511/4423 operator table is in that log and no other. (The
  *file* was right. The **entry id beside it was not** -- see the adversarial
  pass below.)

**Two rest on something weaker than content, and are recorded rather than
smoothed over:**

* `cold-start-a0/run_all.py` — the evidence is a **call chain**
  (`run_all.py` → `pipeline.plan_stage` → `solve(..., prefer="stub")`), not text
  in the cited file. None of the four `run_all.py` contains the string `prefer`.
* `cold-start-a3/artifacts/score_vs_truth.json` — a run snapshot under
  `cold-start-a3/runs/p-17/` is **byte-identical** (same sha256). The choice is
  settled by the section's own anaphora ("the third row of *that artefact*",
  after a full-path cite two lines up), not by content, because content cannot
  distinguish them.

The **5 generic** name a kind of file rather than an artefact — "written down by
the LLM in a `THEORIZE_LOG.md`", "35 directories with a `ground_truth.json`",
`playbook.dsl` as the *form* the frozen grammar defines. They are ruled in
`ADJUDICATED_BARE`, reasons printed on every run.

**One of the five did not survive the adversarial pass and is now a citation,
leaving 4.** It was flagged in the table at the time as the weak one, on the
grounds that no content hook existed — and that was itself wrong. See below.

## The controls, which went red first

`test_bare_gate.py` — 20 negative controls. `mutation_check.py` breaks check F
twelve ways and asserts the suite goes red for each. The first nine **caught
only 5 of 9**, and all four failures were worth having:

* **"stale rulings stop gating" SLIPPED** — `check_uncited` has a
  byte-identical `stale = [...]` line and comes *first* in the file, so
  `replace(old, new, 1)` mutated **check E** while the report named check F. The
  suite was right to stay green. A mutation aimed at the wrong function proves
  nothing about the one it names.
* **"the abstract exemption widens" was PATTERN NOT FOUND** — the fragment was
  written at the wrong indentation. Exactly the silent-drift mode P16 hit, made
  again one file later, and caught only because a missing pattern counts as a
  miss here rather than a skip.
* **two were genuine holes in the suite.** A path whose *basename* is ambiguous
  (`cold-start-a0/STATUS.md`, nine `STATUS.md` in the tree) had no test, so
  deleting the `"/" in token` guard — which would flag the very form the check
  asks authors to use — passed. And the worktree test asserted a path prefix
  that is **vacuous when the suite runs from inside a worktree**, since there is
  no `.worktrees/` under ROOT there; it now asserts membership of `_WALK_SKIP`,
  which holds wherever it runs.

`.worktrees/`, `.claude/`, `.git/` and the caches are excluded from the
candidate set: ~90 checkouts of this same repository live under `.worktrees/`,
and counting them would make every filename in the paper ambiguous — the check
would be measuring the agent's scratch space rather than the published tree.

## The second adversarial pass, which overturned three of my own judgements

Eleven of the fourteen resolutions held under content re-verification. Three did
not, and **two of the three were published sentences**, not gate internals.

**The anchor was wrong, and I had already blessed it.** `03_a0.md` and
`PROVENANCE.md` both cite the segmentation table as `THEORIZE_LOG.md` **O-01**.
It is not O-01: the block names itself at `cold-start-a0/THEORIZE_LOG.md:86` —
"Recorded as **D-A0-007**" — and is followed by `### O-04`. Following O-01 lands
a reader on a one-line entry about naming `obj0` the Button. `OPEN_ITEMS` B4 said
"O-03, should be O-01"; earlier the same day I checked it, agreed, and marked it
closed. **The third answer is the right one.** Fixed in all three places.

This is the shape of F's deepest gap, and it is now in the docstring: **check F
resolves which file a citation means, and nothing resolves the anchor inside
it.** The rewrite made the file findable and left a reader pointed at the wrong
entry within it.

**A cited file that does not contain the claim.** `11_limitations` said the
reproducible pipeline "(`run_all.py`, `prime.run_prime`) calls
`solve(..., prefer="stub")`". Neither file contains `solve` or `prefer`; the call
is at `cold-start-a0/pipeline/plan_stage.py:59`. The previous commit **conceded
this in its message** while the published sentence still asserted it — a
concession in a git log is not a correction to the paper. Now cited properly.

**A ruling whose stated evidence was false.** The `theory.dsl` ruling claimed
three files carry the same `frame persist` comment. `a0-spike/theory/theory.dsl`
carries the keyword bare with no comment at all. Ten other `.dsl` files do carry
it, so the generic conclusion survives — but on a basis I had not checked, and
**nothing in the table would ever have caught the false reason.**

**One ruling retired rather than defended.** `11_limitations`' `THEORIZE_LOG.md`
was ruled generic because "a path rewrite would have to become a four-item list"
and "no content hook exists". The paragraph names **two** arms, not four, and
"written before the scores existed" *is* the ground-truth-seal claim this paper
already sources twice elsewhere. It is now a two-path citation. **5 rulings → 4.**

Two smaller corrections: `probe.py` constructs the `Environment` at **108-109**,
not 108; and `02_framework`'s seal clause ("Those logs … written before the
scores existed") carried no provenance at all and now names its four logs.

### What it broke in check F

* **The two guards I ported the table without.** Check E has `MIN_ANCHOR` and
  `BROAD` because a ruling that silences more than the claim it was written for
  is as dangerous as one that silences nothing. F's table is keyed
  `(section, token)` with **no text anchor**, so one entry silenced a scratch
  section holding one generic mention and three specific ones — the last brand
  new. F now fails on `hits > 1`.
* **`n == 0` was green.** A bare name matching *nothing* is an invented
  citation, and it was the one case **nobody** read: B skips it for having no
  `/`, E only sees it beside a quantity. `ledger_summary.jsonl` — the example
  `_basename_exists`'s own docstring gives as the motivating hole — passed. Now
  a separate `ABSENT` verdict. Case is part of this: NTFS is case-insensitive
  and `_candidates` is not, so `Status.md` opened any of nine files for the
  author and matched none for the check.
* **Sibling notation evaded**, in the paper's own idiom: `` `{STATUS.md}` `` and
  `` `STATUS.md,DECISIONS.md` ``. §7 already cites siblings as
  `{a0-base,a2-base}`, so this is one keystroke away.

Three of the twelve F mutations came back **PATTERN NOT FOUND** on the next run —
my own re-indent had drifted them. Third instance of that failure mode today.

### The gap worth stating plainly

**Uniqueness is not findability, and it is the proxy this check is built on.**
§10 cites four `SURVEY-*.md` bare; each is unique, so F passes all four — while
**§10.7 itself says those files exist only as untracked files in a machine-local
worktree, on a branch that was never pushed.** F calls the paper's least
resolvable citations locatable, and would call a contextually-resolved one
ambiguous. Five further gaps are in the docstring, each reproduced against the
live scanner.

## Verification

```
verify_paper.py             PASS (6/6)
                            F: 93 bare citations, 0 ambiguous, 4 ruled, 0 stale
                            B: 220 path citations, 0 broken   (was 213)
test_bare_gate.py           20 passed
test_uncited_gate.py        62 passed
mutation_check.py (F)       PASS — 12/12 caught
mutation_check.py (E)       PASS — 21/21 caught, unchanged by the shared walk
```

Check B is the independent confirmation of the 14 rewrites: it resolves every
one of them, and it did not before.

## Checklist items closed

* **B1** — closed, and its 22/30/9 superseded by the measurement above.
* **B3** — `PROVENANCE.md` already carries the full
  `theory-compiler/src/theory_compiler/certificate.py`, and that is the only
  `certificate.py` in the tree. Fixed some time after the audit; the checklist
  was never updated.
* **B4** — both citations already read O-01, not O-03.

B3 and B4 were **already true when I got here**. The item warned that B3/B4 are
audit prose and might themselves be wrong; they were not wrong, they were stale.
That is its own small instance of the run's theme — a checklist is a claim about
the world, and it goes out of date silently.
