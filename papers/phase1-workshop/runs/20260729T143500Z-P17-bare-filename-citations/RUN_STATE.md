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

## The 19, decided on content

Every one was settled by something only one candidate has — an entry id, a
quoted value, a field name, a line count — never by which directory looked
right. **14 resolved, 5 generic, 0 unresolved.**

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
  have one; O-01 carries the 6511/4423 operator table.

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

One of the five is marked in the table as the weak one. `11_limitations.md`'s
`THEORIZE_LOG.md` quotes no entry id, value or line, so there is no content hook
that would settle it either way; the ruling says exactly that rather than
implying a confidence it does not have, and names what would retire it.

## The controls, which went red first

`test_bare_gate.py` — 15 negative controls. `mutation_check.py` breaks check F
nine ways and asserts the suite goes red for each. **It caught 5 of 9 on its
first run**, and all four failures were worth having:

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

## Verification

```
verify_paper.py             PASS (6/6)
                            F: 94 bare citations, 0 ambiguous, 5 ruled, 0 stale
                            B: 217 path citations, 0 broken   (was 213)
test_bare_gate.py           15 passed
test_uncited_gate.py        62 passed
mutation_check.py (F)       PASS — 9/9 caught
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
