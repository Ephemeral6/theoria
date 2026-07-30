# S34 — papers owes a verify gate

RES-2, lane `paper`, branch `agent/s34-papers-verify-gate`, base `c54954d6`.

## The item was stale on arrival, and that is the finding

S34 asked for three things: give `papers` a three-stage `verify.py`, remove it
from `test_gates.py`'s `tests_only` allowance, and expect that test to go red
once. All three were already done before the item was claimed:

* `papers/verify.py` landed with S32 (`ca23738a`) and merged at
  2026-07-29T15:55:51Z (`monitor/ci/merge.log:1872`);
* `gates.survey()` puts `papers` in `gated`, kind `verify`, name `verify.py`;
* `monitor/tests/test_gates.py:159` pins `tests_only == {"verify-lab"}` —
  `papers` is not in it. S33 retired the pin the same evening, and the file's
  own comment (`:146-158`) narrates why.

Writing a second gate on top of a working one would have been the wrong
delivery. What was worth doing was asking what the closed debt cost, since the
item's premise was written from a survey snapshot that was already false.

## Two defects, both created by closing the hole

Each was put to an adversarial subagent instructed to refute it. Both came
back **partially confirmed** — mechanism right, story wrong — and the
corrections are in the record below rather than dropped.

### D2 — the gate displaced a suite that had just arrived

`monitor/gates.py:192 gate_for()` returns inside its `find_gate` branch and
never reaches `has_tests()` at `:213`. A territory that ships a gate is gated
by that gate alone.

| merge.log | UTC | gate run for `papers` |
|---|---|---|
| `:1838` | 11:12:21Z | `none` — `NO GATE, MERGED UNCHECKED` |
| `:1856` | 15:02:51Z | `pytest:papers` — P16's first `test_*.py` |
| `:1872` | 15:55:51Z | `verify:papers(verify.py)` — S32 lands |
| `:1894` | 18:02:35Z | `verify:papers(verify.py)` |
| `:1938` | 20:57:33Z | `verify:papers(verify.py)` |
| `:1948` | 21:15:02Z | `verify:papers(verify.py)` |

So `pytest:papers` ran **once, ever**, over the 62 tests of
`test_uncited_gate.py`. `test_bare_gate.py` (20 tests, check F's negative
control) reached master at 18:02:35Z, after the switch, and has **never been
run by CI**. 82 tests exist to show `verify_paper.py`'s checks can go red;
62 ran once and 20 have never run.

**Refuter's corrections, kept.** The claim as filed said the gate displaced an
existing suite. It did not: S32 authored `papers/verify.py` at 11:03Z, when the
territory held no test at all, and P16's suite arrived at 15:02Z in between.
Both commits were right separately; the loss lives only in the order they
merged, which no author could see. The refuter also found the sharper point:
`monitor/tests/test_gates.py:163-166` records the *identical* event for
`proxy` — a canonical `verify.py` superseding `verify_spend.sh` — and says the
only reason it was acceptable is that `proxy/verify.py:260` re-invokes the
superseded gate as one of its own stages. `papers/verify.py` did not. The
lesson was learned, written down, and not applied one commit later.

**How many other territories owe the same debt — counted, and it is not the
number I first had.** 19 of the 24 gated territories ship a verify script and
a `test_*.py`. That was nearly the finding. It is not: grepping each gate
script for `pytest`, **17 of 19 run their tests themselves**
(`monitor/verify.sh:23` execs `verify.py`, whose stage 1 is
`pytest monitor/tests`, so it counts). The live instances are **two**:
`papers`, fixed here, and **`ablation-arm`**, whose `verify.sh` contains
neither `pytest` nor `test` while `ablation-arm/tests/` holds at least five
test files. That is grep-level only — I did not read or run that gate, and it
is not this territory's — so it went to
`monitor/inbox/20260729T233000Z-RES-2-a-new-gate-silently-retires-the-old-one.md`
with the proposal, flagged as unverified. The proposal's first item is to make
`survey()` report the overlap, and the fact that the answer is 2 rather than 19
is the argument for it: nobody could know which without writing the query, and
nobody had.

### D1 — the gate reds on the repository's own provenance convention

`paper_dirs()` returned every subdirectory and demanded a gate file from each.
Reproduced at `71e9dc00`: `mkdir papers/runs/probe` → `FAIL runs ships no
gate`, exit 1. `runs/` is gitignored nowhere; at this branch's base commit,
`git ls-tree -r --name-only c54954d6 | grep -cE '(^|/)runs/'` is **3870** across
22 top-level directories, and `CLAUDE.md` requires it. (The first draft said
3706 and bound it to nothing. Two hours later no definition of the query
reproduced that figure at any commit on this branch's ancestry — the tree gains
provenance files continuously. Corrected in the cycle-35 pass below, with the
command and the commit attached so a reader can re-derive it.)

**Refuter's corrections, kept — this one is smaller than it looked.** It has
never fired: `grep "red in papers" monitor/ci/merge.log` is empty. The reason
is that this territory's provenance has always gone one level deeper, into
`papers/phase1-workshop/runs/`, where `paper_dirs()` never looked; the
convention and the trap have been missing each other by one directory for as
long as both existed. On the ordinary branch path it would fail the offending
*branch*, not master — the dangerous path is a direct-to-master commit, which
does happen here. And it is not `runs/`-specific: any committed top-level
directory under `papers/` did the same thing. Latent fragility, not an
incident, and the record says so.

It stops being latent with this commit. S34's own provenance is at
`papers/runs/20260729T224939Z-S34/` — the territory-root location `CLAUDE.md`
specifies, a deliberate move off phase1-workshop's local habit and onto the
repository's rule. The fix and its first user land together.

### D3 — found while fixing, not looked for

Adding the `negative-sample` declaration did not work. `gates.py:160`
`NEGATIVE_SAMPLE.search()` takes the first match **anywhere in the file**, and
this gate's docstring explains the mechanism — so the prose shadowed the
declaration and `survey()` read the sample as a single backtick:

```
ns {'declared': '`', 'exists': False}
```

It failed safe (a backtick is not a file, so the territory stayed
`decorative`). It would not have failed safe if the prose had named a path
that exists. `gates.py` is `monitor`'s, not this territory's, so this went out
as a proposal:
`monitor/inbox/20260729T231500Z-RES-2-negative-sample-shadowed-by-prose.md`.
`test_verify_delegator.py::test_this_gate_declares_a_negative_sample_that_exists`
pins the resolved value, so a future edit to this docstring that shadows the
declaration again turns the territory red.

## What was changed

`papers/verify.py` — two stages to three:

1. **classify** — a directory is a paper iff it holds `PAPER.md`; `runs/` is
   named provenance and skipped; anything else is a **stray** and is RED and
   named. Fail-closed survives, the trap does not. The positive marker was
   chosen over "has a gate", which would be circular: a paper that lost its
   gate would become invisible, which is the silence the file exists to refuse.
2. **run each paper's gate** — now with `--timeout` actually applied. It was
   parsed and then passed to nothing; a gate that hung took the merge rig with
   it.
3. **run the suite the gate displaced** — with pytest's exit 5 ("collected
   nothing") treated as RED, because a deleted suite and a green suite
   otherwise report the same green, which is exactly how the territory lost its
   tests. Guarded by `THEORIA_PAPERS_VERIFY_INNER` so a test that drives the
   gate end to end cannot re-enter stage 3.

Also: the repository root now goes on `PYTHONPATH` for sub-gates, the contract
`monitor/gates.py: gate_env()` states and this delegator was not honouring.

`papers/test_verify_delegator.py` — new, 26 tests, the declared negative
sample. Every one is a mutation of a synthetic `papers/` tree. The two that
matter: `test_provenance_directory_is_not_a_defect` (D1) and
`test_a_vanished_suite_is_red` (D2). One is a positive control on the live
tree, `test_the_live_papers_tree_classifies_cleanly`, which will red if anyone
adds an unclassified directory under `papers/`.

## What a third audit added, and what it changed here

A separate subagent audited the territory for silent-pass holes. Six of its
findings are inside `phase1-workshop/verify_paper.py` and are filed as
`S-P20-nosecret-noop` (priority 1 — its headline is that check D, the one
standing between the ARC key and the Phase 4 release manifest, builds its
secret list from a gitignored `.env` and therefore iterates zero times in
every worktree `ci_merge` checks out). Four landed in this delivery:

* **The `--timeout` default was decorative even after being applied.**
  `ci_merge.py:543` kills a gate at 1800s and the default here was also 1800,
  so the outer kill always won and the gate never got to name what hung. Now
  1500. A subordinate timeout has to be strictly shorter than its supervisor's.
* **The delegator gave sub-gates no `PYTHONPATH`.** The entitlement
  `gates.gate_env()` states reached them only by inheritance from `ci_merge`,
  so it held under CI and not under the invocation this file's own docstring
  documents. Now set explicitly.
* **A gate that exits 0 saying nothing was green.** A zero-byte
  `verify_paper.py` printed `(no output)` on the `ok` line and took the
  territory green — the third silence, after "no paper" and "no gate". Now RED.
  What remains trusted is the exit code: a gate that prints its own FAIL and
  exits 0 still passes, and `test_a_gate_that_prints_and_exits_zero_is_green`
  says so out loud rather than leaving it to be discovered. Requiring a verdict
  token would be a contract on every future paper's gate and is not this file's
  to impose alone.
* **The recursion guard could have restored the defect it protects.** If
  `THEORIA_PAPERS_VERIFY_INNER` were set in a real environment, stage 3 would
  skip and the gate would still exit 0 — silently, invisibly to `ci_merge`,
  which reads only the exit code. A legitimate nested run is always inside
  pytest, so the guard now refuses to fire outside one.

## The fix is not decorative — one mutation, measured

The audit's sharpest result was that three of check E's four documented
escape-hatch guards could be deleted with `papers` still green, because
nothing ran the tests that pin them. That is exactly what stage 3 is for, so
it was measured rather than assumed. `MIN_ANCHOR = 24 → 0` in
`verify_paper.py`, then `cd papers && python verify.py`:

```
[2/3] ok    phase1-workshop -> verify_paper.py: verify_paper: PASS (6/6)
[3/3] FAIL  pytest exited 1: 1 failed, 73 passed
papers: RED (1 problem(s))            EXIT=1
```

Stage 2 green, stage 3 red, gate red. Before this change that mutation merged.
`verify_paper.py` was restored byte-for-byte afterwards (`git diff` clean).

## Verification

```
cd papers && python verify.py
[1/3] classify the directories under papers/
   --    runs (provenance, not a paper)
   ok    1 paper(s): phase1-workshop
[2/3] run the gate each paper ships
   ok    phase1-workshop -> verify_paper.py: verify_paper: PASS (6/6)
[3/3] run the suite that shows those gates can go red
   ok    108 passed
papers: green -- 1 paper(s), each gated by its own check, and the checks' own suite run
EXIT=0
```

`papers/test_verify_delegator.py`: 26 passed.

**The gate does not dirty the worktree** — checked deliberately, because adding
a pytest stage to a gate is the exact shape that just cost the `freeze` track a
finding: `monitor/verify.py`'s stage 1 is `pytest monitor/tests`, and a test
inside it wrote `state.json`/`index.html` into `monitor/`, so every run of that
gate left the tree dirty and the noise read as "my branch changed something".
`merge.log` records `a gate dirtied the worktree` for several merges. Here,
`git status --porcelain` before and after a full gate run is byte-identical:
pytest's `__pycache__/` and `.pytest_cache/` are covered by the root
`.gitignore`, and nothing in either suite writes into the tree.

Also added `papers/.gitattributes` (`* text eol=lf`). S34 puts the first
tracked files at the territory root, outside the reach of
`phase1-workshop/.gitattributes` one directory down — and a gate and the tests
that prove it can go red are the last files whose bytes should depend on whose
`core.autocrlf` checked them out.

`monitor/tests/test_gates.py` and `test_gate_negative_sample.py`: 18 passed —
checked deliberately, because `papers` leaving `decorative` (22 → 21) changes
`survey()` output, and a master-side red in `monitor` holds every branch
(`merge.log:1875` is that outage). Nothing pins the live `decorative` set; all
of those tests build synthetic trees. So this merge does not red `monitor`.

Unlike the item's prediction, `test_gates.py` does **not** go red once: the
sets it pins (`ungated == {}`, `tests_only == {"verify-lab"}`) are unchanged by
this work, because S33 had already moved them to the truth.

## The cycle-35 pass: two probes against this delivery, not against the findings

Cycle 33 wrote the work and staged it. Cycle 34 resumed it, re-ran the gate
green, dispatched two adversaries against *its own delivery* — and died before
either returned, so nothing was recorded. Cycle 35 ran both probes itself. Both
found something, which is the argument for the step: cycles 33 and 34 had each
already declared this delivery finished.

**Probe A — try to make `verify.py` exit 0 on a territory it did not check.**
Two findings, one of them mine to fix.

`THEORIA_PAPERS_VERIFY_INNER=1` alone is correctly refused (`RED`, exit 1 —
that is the cycle-33 guard working). But `INNER=1` *plus* `PYTEST_CURRENT_TEST`
set to any string skips stage 3 and exits 0. That much is unavoidable: it is
also the shape of the legitimate nested run, the guard cannot tell an inherited
`PYTEST_CURRENT_TEST` from a fabricated one, and the alternative to exiting 0
there is a fork bomb. Two variables neither of which a merge sets is a narrow
door and it stays open.

What was **not** acceptable is what the gate printed while walking through it:

```
papers: green -- 1 paper(s), each gated by its own check, and the checks' own suite run
```

Stage 3 was skipped and the summary said the suite ran. A green line asserting
a check that did not execute is precisely the silence this file's three stages
were built to refuse, shipped in the file's own output — the defect class D2,
D4 and stage 3 all exist to catch, committed by the gate about itself. It went
undetected through both prior cycles because every test asserted on `run_suite`'s
return value or on the exit code, and nothing read the sentence.

Fixed structurally rather than by rewording: `run_suite()` now returns
`(ok, detail, ran)`. `ran` has to be a third value because `ok` cannot carry it
— the skip is genuinely green — and it is returned rather than recovered by
sniffing `detail`'s prose so the caller cannot get it wrong. `main()` prints
`the checks' own suite NOT run (stage 3 skipped)` on that path. Five call sites
in the suite were updated to the 3-tuple, and each now also asserts `ran`, which
is the assertion that was missing.

`test_the_skipped_summary_does_not_claim_the_suite_ran` pins it, and is itself
mutation-checked: restoring the unconditional `"run"` takes it red and nothing
else (`1 failed, 25 passed`).

**Probe A, second half — is the 25-test suite decorative?** Four independent
mutations of `verify.py`, each restored afterwards:

| mutation | result |
|---|---|
| `if not tail:` → `if False:` (a gate may say nothing) | `test_a_gate_that_says_nothing_is_red` fails |
| `MIN_PAPERS = 1 → 0` (an empty walk passes) | 2 fail, incl. `test_no_paper_at_all_is_red_not_a_vacuous_pass` |
| `NO_TESTS_COLLECTED = 5 → 999` (a deleted suite passes) | `test_a_vanished_suite_is_red` fails |
| `strays.append` → `skipped.append` (a stray is not red) | 2 fail, incl. `test_an_unrecognised_directory_is_still_red` |

Four for four, each caught by the test named for that property and not by a
blanket failure. The suite is load-bearing. `git diff verify.py` clean after.

**Probe B — fact-check every citation against the logs.** Line numbers into
`monitor/gates.py` (`:160`, `:177`, `:192`, `:213`), `monitor/tests/test_gates.py`
(`:159`, `:163-166`), `monitor/ci_merge.py:543` (the 1800s kill), and
`proxy/verify.py:260` all resolve to the claimed text. All six `merge.log`
citations (`:1838`, `:1856`, `:1872`, `:1875`, `:1894`, `:1938`, `:1948`)
resolve to the claimed entries, and `grep -c "red in papers"` is still `0`. All
five test names quoted in this document and in the docstring exist. Test counts
verified by collection: `test_uncited_gate.py` 62, `test_bare_gate.py` 20,
`test_verify_delegator.py` 26.

Two numbers were wrong, both mine, both corrected above:

* **3706** tracked files under `*/runs/`. Does not reproduce: at base commit
  `c54954d6` the count is **3870** by `(^|/)runs/` and 3745 by
  `^[^/]+/runs/`, and no ancestor commit on this branch yields 3706. The claim
  it supports — that `runs/` is a repository-wide convention with thousands of
  files, so the old `paper_dirs()` demanded a gate from all of them — holds at
  every one of those figures, which is why the error survived two readings.
  Both the docstring and this document now carry the query and the commit.
* **23 tests** in one sentence and **25 passed** in another, in this same
  document. Now 26 in both, after this pass added one.

Worth stating plainly: a stale seal, a rotted count and an internally
inconsistent count are the three defect classes this delivery spends most of its
length filing against other people's work. They were in it because cycles 33 and
34 both wrote the narrative after measuring and never re-measured.

## What this did not do

* Did not touch `papers/phase1-workshop/verify_paper.py` — except to mutate
  and restore it for the measurement above. Its six checks are a separate
  piece of work, filed as `S-P20-nosecret-noop`.
* Did not patch `gates.py`, for D2's root cause or D3's. Both are `monitor`'s
  territory; both went to `monitor/inbox/` (D3) and to the bus (D2).
* Did not remove anything from `test_gates.py`'s allowance sets. There was
  nothing left to remove.
* Did not change `release/reproduce.py:86-90`, which reproduces the paper by
  running `verify_paper.py` directly with `cwd=papers/phase1-workshop` — so
  the release reproduction still does not execute the 107 tests, only the six
  checks. Same shape as D2 one level out: the territory gate is now the
  complete one and the release path points past it. `release/` is not this
  territory's, so it is recorded here rather than patched.
