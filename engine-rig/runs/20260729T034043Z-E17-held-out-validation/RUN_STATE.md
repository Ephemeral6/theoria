# E17 · run state — where this stopped, and why

Read order: `PREREGISTRATION.md` → `CORRECTIONS.md` → `ENGINE_TABLE.md` rows 3
and 4 → `ADVERSARIAL-heldout.md` for the full attack → `RESULTS.md` last, as the
pre-correction text the corrections are checkable against.

## The three items

**Item 1 — the fact in `ENGINE_TABLE.md`'s boundary column: DONE.** Rows 3 and 4
carry the held-out figures with their cuts named, and the file gains a standing
rule on 「已验证」 with a test behind it. `ENGINE_TABLE.md` was not on this branch
(it is E9's, unmerged), so `agent/e9-engine-paper-table` was merged in first —
the file forbids hand-editing, so the change is in `tools/engine_table.py` and
every number enters through a probe.

**Item 2 — a real held-out validation for `zero_space` and `lp_potential`:
DONE, and the honest answer is smaller than the first draft claimed.** See
`CORRECTIONS.md`. `zero_space`: 13.1 % of global laws survive leaving one
operation out; the companion random-transition cut returns 100.0 % and is
vacuous, which the review proved and the harness now measures.
`lp_potential`: 26.4 % of certificates still satisfy `inv_closed` on a withheld
move geometry, 58 of 1408 are outright false, and the emit gate does not stop
them once it is handed the evidence a partial-evidence caller actually has.

**Item 3 — making the split a rig-wide routine at fixture-generation time: NOT
DONE. Stopped here deliberately, on two grounds.**

1. **Discipline.** The fixtures under `fixtures/data/` are byte-pinned committed
   artifacts, and this ticket's standing instruction is not to modify any
   already-committed artifact. Cutting a hold-out at generation time rewrites
   every one of them and re-hashes anything downstream that pins them.
2. **And the better reason: as literally specified it would produce a vacuous
   split.** F1 is the finding that settles it. A hold-out is only informative
   when the withheld rows carry evidence the fit did not see, and for Fixture B
   a transition-level cut withholds nothing — the difference vector is a
   function of the operation alone. A fixture-time transition split, applied
   uniformly, would hand every future engine a 100 % hit rate that means
   nothing, which is precisely the defect this ticket was opened to remove,
   institutionalised.

   What the rig should adopt instead, and what this run leaves behind as the
   working shape: the split unit must be the **generative unit** of the family
   (the operation for `parityworld`, the move geometry for `jumpgraph`), and
   every hit rate must be published beside a **novelty count** —
   `heldout_row_novelty` in `results.json` — saying how much of the held-out
   side the fit had not already consumed. `heldout/split.py` and
   `heldout/zero_space_heldout.py` are the reference implementation. Writing
   that into `fixtures/generate_all.py` is a separate ticket and needs a
   per-family answer to "what is the generative unit", which is a design call
   this run does not have the standing to make for four families it never fed
   to an engine.

## Provenance and discipline

* Commit order is `git`-provable: `ef382c9` (pre-registration, no results) →
  `c781a73` (harness, no results) → `e0fd43a` (results + table) → `8d899bf`
  (corrections after the adversarial review). `git merge-base --is-ancestor
  ef382c9 HEAD` holds; `PREREGISTRATION.md` is byte-unchanged since `ef382c9`,
  verified by the reviewer independently.
* Zero API calls, zero network, zero sealed-pile contact. Both corpora are
  generated in memory; the only committed fixture touched is Fixture C, read as
  a correctness gate.
* Measured, not narrated: `measured/heldout-run.txt`, `measured/pytest.txt`
  (**521 passed, 27 skipped, exit 0**), `measured/mutation-recheck.txt`.
* One incidental change outside E17's scope, flagged rather than absorbed: three
  `fuzzlab` expectations in `tools/engine_table.py` (500/55/15) were already
  stale on this branch and are now 60/64/14, re-read from `fuzzlab/out/*.json`
  directly. Without that the table could not be regenerated at all.
* Not merged into E16, per the ticket. E16's acceptance line is two verdict
  wirings; this one is a number.
