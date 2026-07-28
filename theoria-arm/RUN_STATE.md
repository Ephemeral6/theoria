# RUN_STATE — theoria-arm

Where the runs stand. One section per run; the numbers here are copied from
`runs/<slug>/MANIFEST.json`, which is generated, so this file is a summary and
never a source. A number that appears only here is a mistake.

---

## `preflight-20260728T012057Z` — the live chain, for zero quota

**Purpose.** Prove that the key, the guard, the proxy and the retry envelope
all work before an action is spent. RESET is not billed, so opening a
scorecard, sending one RESET and closing costs nothing.

**Result: PASS**, and two findings.

| | |
|---|---|
| RESET | 200, **after 18 attempts** |
| env_steps in the ledger | 18 (17 × 400, 1 × 200) |
| billed actions | 0 — `scorecard.total_actions: 0` |
| key injected inside the proxy | yes; the arm holds nothing |
| guard | `3feca53e…41bbc19a`, cut `v1`, 4 dev / 21 sealed |
| incidents | 0 bypass attempts, 0 credential-in-body, 0 sealed-pile requests |
| frame | one 64×64 grid, colours `{0, 1, 5, 8, 9}` |
| `available_actions` | `[1, 2, 3, 4, 5]` (no ACTION6 on this game) |
| `win_levels` | 7 |
| `levels_completed` | 0 |

**Finding 1 — the wave is live.** 18 attempts for one RESET. `arc-recon`'s
40-attempt envelope is load-bearing right now, not a historical artefact.
`proxy/forward.py`'s 5 attempts, which exclude 400 entirely, would have
returned a hard failure here. This is why the retry lives arm-side
(`DECISIONS.md` D-P8-003), and why the ledger carries 18 `env_step` records for
one successful command.

**Finding 2 — no `score` field.** Confirmed on live data: the response key set
is `action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels`. `LEDGER_FORMAT.md` §3's score obligation
cannot be computed against this API. Recorded as `INC-TA-002`.

---

## `20260728T015354Z-g50t-first-contact` — the first online contact

**Purpose.** P-8: connect the inner loop, proved four times offline
(`a0-spike`, `cold-start-a0`, A1, `cold-start-a2`), to a real environment
through the double proxy. The goal is not to win — it is that the loop turns
online and the books balance.

**Settings.** `g50t-5849a774`, 109 successful actions (120 minus the 11 spent
on the two aborted attempts, so the red line holds across all three), 3000 HTTP
commands, `claude-opus-5` at the desk, $16 ceiling, 7200s wall clock, no
variant.

**Three attempts. The first two aborted on defects in this arm** (landmarks the
level generator never placed; a desk that had tools and spent its turn writing
its answer to a file). Both are archived intact under `runs/*-aborted/` with an
`ABORTED.md` each, and accounted for in `INCIDENTS.md` INC-TA-004. The third is
the run below: `runs/20260728T015354Z-g50t-first-contact/`.

### The run, from its own `MANIFEST.json`

| | |
|---|---|
| actions | **7** successful, 0 failed, 1 RESET |
| HTTP commands | 40 → amplification **5.71** |
| scorecard | `total_actions 7`, `score 0.0`, `levels_completed 0` of 7 |
| ledger `env_step` records | 40 (8 at 200, 32 at 400) |
| **action count reconciles** | ledger 7 = scorecard 7 ✔ |
| **levels reconcile** | ledger 0 = scorecard 0 ✔ |
| score reconciliation | `unavailable` — the API returns no score (INC-TA-002) |
| model calls | **5**, all at `theorize`, $6.32 |
| surprises | **8**, all empirical: 4 `render_mismatch`, 4 `replay_mismatch` |
| constraint 8 | **holds** — 1 bootstrap call + 4 covered by surprises, 0 at any forbidden beat |
| sealing | 0 bypass attempts, 0 credential-in-body, 0 guard blocks |
| sealed pile | **untouched, verified from the bytes** — the only game id anywhere in the records is `g50t-5849a774`; cut digest checked |
| Lean | never available (state space past the ceiling) |
| plan | `no_goal_declared` at close |

### The loop turned, and here is the shape of one turn

theorize (call 1, $1.33, 588s, 46,248 output tokens) → **the compiler refused**
the manual, because an `invariant` carried prose where only a `theorem` may →
theorize again (call 2, $0.87, 333s) → **all four forms generated** →
certify → **69 pixels of frame 0 belong to neither the board nor any declared
object**, and 0 of 7 transitions replay → two surprises → plan →
`no_goal_declared` → probe → **`probe_frontier` reports that no action
separates any two hypotheses**, so the probe is recorded as unrunnable with
that reason and the arm explores the least-tried legal action instead.

Then it went round again, four more times.

### The one number that measures the loop — and it does not say what it first looked like

Unexplained pixels at frame 0, across the four certify rounds:

```
69 → 68 → 69 → 69
```

Read after two rounds this looks like convergence. It is not. **The manual
oscillates**: it gains a pixel, loses it again, and settles back where it
started. Over four rewrites and $6.32 the responsibility failure is exactly
where it began.

That is the real result of this run and it is worth more than a tidier one. The
mechanism is visible in the manual itself: the desk knows *why* those pixels are
unexplained — `theorem colour_nine_collision` says colour 9 paints at least
three distinct things and this arm binds one colour to one object — so the
defect is not one the desk can fix by rewriting. Each round it re-derives the
same diagnosis, rewords the manual around it, and the count returns.

**A loop that re-theorizes against a defect its language cannot express will
cycle, not converge**, and it will spend a model call per cycle doing it. The
four rounds cost $5.00 to establish that. Two changes follow, neither of which
is in this run: the evidence gate is now quantitative, so the desk is not
called until there is materially more world to look at (`inner/loop.py`); and
`E-03` — one colour, one object — is now the top of the expressivity ledger,
because it is the thing standing between this manual and a green
responsibility check.

The number itself is the win here: constraint 2's responsibility pass produced
a real, moving quantity on a real frame, and that quantity was able to say
"you are going in circles". A framework whose checks can only say pass or fail
could not have.

### What the desk got right before certify ran

The manual carries `theorem colour_nine_collision`, in which the desk works out
that colour 9 paints at least three distinct things on this board, that this
arm binds one colour to one object, that the surplus colour-9 pixels will
therefore have no owner — and says so, explicitly, *before* certify reported
the 69. A manual that predicts its own certify failure is a better artefact
than one that passes quietly. Full text and three more like it in
`THEORIZE_LOG.md`.

### Why it stopped

Stopped from outside at a natural close-out point, with 102 actions and ~$10 of
its ceiling unspent. The binding constraint was neither: it was that one turn
costs about seventeen minutes, nearly all of it in a single `claude -p` call
that returns 46,000 output tokens. `inner/loop.py`'s evidence gate is now
quantitative (four new transitions per desk call rather than one) for exactly
this reason, but that change postdates this run and did not affect it.

Because the run was stopped rather than finishing, it never reached
`_finish()`, so `certify.json`, `plan.json` and `turns.json` were never written.
They are reconstructed in `certify_reconstructed.json` by re-running certify and
plan against the archived books and the ledger-rebuilt trace — deterministic,
zero model calls, and **labelled a reconstruction** rather than passed off as
the live report. `run.json` is likewise rebuilt and flagged.

### The confound, stated before the numbers

`INC-TA-001`: another Claude Code session ran a `baseline-arms` `bare_cc`
campaign **on this same game** for the whole of this run — its shard ledger and
this arm's ledger were both being written at `01:28Z`. Every wall-clock and
HTTP-amplification number from this run is therefore an upper bound on this
arm's own cost and not a measurement of it. It may not be compared with
`baseline-arms`' 5.07× or `arc-recon`'s 2.5–10× without that caveat. Neither
session could see the joint total; each gate counted only its own.

### What the engines said on first contact

The dispatch ran before any model call, on 6 states (RESET + one of each legal
action), and three of its results are findings in their own right:

* **The concept account went negative.** `mdl_segmenter`'s six object
  hypotheses carry `gain_bits: -5042`, `ratio 3.55` — the segmentation costs
  more than encoding the pixels raw. A0's Cart earned +2967 on the same
  accounting. On a real 64×64 frame with six states, `Theoria.md` §1.8's ticket
  of admission ("a concept earns its place by making the manual shorter") is
  not merely unmet, it is inverted.
* **One track is not an object.** `obj3` is a 50×38 blob of 1006 cells with
  `color: None` — the segmenter merged the level's structure into a single
  track. This is the degradation the background choice was documented to
  produce, and it produced it: loudly and visibly, which is what was wanted.
* **`zero_space` returned 70 "global laws" from 6 states.** They are
  numerically true and epistemically empty: with a handful of transitions
  constraining a few hundred features, the null space is nearly everything, so
  almost any vector is a "law". A0 read its two laws off 275 transitions. The
  arm now computes this explicitly — `evidence_adequacy.verdict` says `THIN`
  with the rank and the dimension — and hands the verdict to the desk with the
  laws, so a correlation cannot be mistaken for a conservation law.
* **`cegis_miner` emitted nothing.** Its precondition (exactly one `move` event
  per transition) is a claim about the world, and this world does not satisfy
  it. Recorded per track as a refusal, never worked around (D-P8-006).

---

## The archive, read back — which runs a paper may cite (S8, 2026-07-28)

Nine runs are under `runs/`. Before this pass, four had a `MANIFEST.json` and
five did not, and this is the only arm that has ever spent an ARC action, so
the gap was in the one place it mattered. `armtools/backfill.py` wrote the five
from the runs' own ledgers, `armtools/verify_provenance.py` checks the result,
and the table below is what a Phase 4 release manifest may lean on.

| run | kind | billed actions | usable for the paper? |
|---|---|---|---|
| `preflight-20260728T012031Z` | pre-flight, aborted | 0 | **process record only** — opened a scorecard, never closed it, no run_end |
| `preflight-20260728T012057Z` | pre-flight | 0 | **yes**, for the live-chain and retry-envelope findings |
| `20260728T012311Z-…-aborted` | aborted experiment | **5** | **process record only** — INC-TA-004; cite for the cost of the defect, not for a result |
| `20260728T012311Z-…-salvage` | salvage | 0 | process record — all eight close attempts 404ed |
| `20260728T012311Z-…-salvage2` | salvage | 0 | **evidence** — holds the API's own scorecard for the run above (5 actions) |
| `20260728T014402Z-…-aborted` | aborted experiment | **6** | **process record only** — INC-TA-004 |
| `20260728T014402Z-…-salvage` | salvage | 0 | **evidence** — holds that run's scorecard (6 actions) |
| `20260728T015354Z-g50t-first-contact` | experiment | **7** | **yes — this is the run the milestone rests on** |
| `20260728T015354Z-…-salvage` | salvage | 0 | **evidence** — holds its scorecard (7 actions) |

**18 actions is this arm's entire lifetime spend**, and all 18 are now confirmed
twice: once by the ledgers (7 + 6 + 5) and once by the API's own arithmetic in
the four closed scorecards. They agreed exactly. `verify_provenance` asserts it
on every run, so the total cannot drift unnoticed.

**The salvage runs are not filler.** A run that dies before closing its
scorecard leaves `scorecard: null` in its own manifest — which is how both
aborted runs' manifests read — while the number itself sits in the ledger of
the salvage that closed the card afterwards. It was in the archive the whole
time and unreachable from the file that needed it. Each aborted manifest now
carries `scorecard_recovered_by` naming the salvage that holds it.

### Three things this pass found, none of them comfortable

**1. `base_commit` did not mean what it says.** `archive.py` filled it with
`git rev-parse HEAD` at the moment the *manifest* was written, which for a run
archived after its fix was committed is a later commit than the run ran at. The
recorded `arm_version` settles it independently — it is a hash over this arm's
own `.py` sources, so it can be recomputed at any commit and matched
(`armtools/armversion.py`). Of the four manifests that carry a commit, **none
names the tree its run actually ran against**: two name a later commit, two name
one whose tree hashes differently from anything the run recorded.

Said precisely, because the loose version is false: the derived commit is **not
the commit the run was launched from**. Two of them were created *during* the
run — `0f62cf6` 21 seconds after the 01:53 run started, `e3ce4ee` 57 seconds
after the 01:44 one — because the fix under test was committed while the run
was still going. What the hash establishes is that the run's `.py` sources were
byte-identical to the tree that commit holds, which is what reproducibility
needs and is all it claims. Each manifest carries the arithmetic under
`provenance.arm_version_lookup.relation_to_the_run`.

The corroboration is that each derived commit's message places the run exactly
where the narrative already put it: the 01:44 run's sources match `e3ce4ee`, the
commit recording the 01:23 abort; the 01:53 run's match `0f62cf6`, the commit
fixing the 01:44 abort. `archive.py` now runs this check at write time and
records its verdict beside the field.

**2. Two runs ran against files that were never committed.** `preflight-…012057Z`
and `20260728T012311Z-…-aborted` share an `arm_version` (22 files) that no
commit in this repository reconstructs. They are honest runs and their ledgers
are intact, but **they are not reproducible from git** and their manifests now
say so in `provenance.missing` rather than implying otherwise with a commit id.

**3. One scorecard is still open.** `preflight-20260728T012031Z` opened card
`bbbd5b57-de5d-4f14-aa0e-adaedb234fef` and no run in this archive ever closed
it. Its ledger records zero `env_step`s, so the ledger's claim is zero billed
actions — but that claim has never been confirmed against the API, and cannot be
offline. It is declared in that run's manifest under
`scorecards_opened_and_never_closed` and left open rather than quietly assumed
to be zero. Closing it costs no actions and would settle it;
`armtools/salvage.py` is the tool, and it needs the spend gate open.

### What is *not* in the archive any more

Two `pytest-*` directories used to sit under `runs/`. They were gitignored, so
they never reached the repository, but they were indistinguishable by directory
listing from runs that cost money — the probe that opened this item counted
eleven runs where there were nine. Test runs now write to `.pytest-runs/`
(`harness.run.FIXTURE_RUNS_DIR`), and `verify_provenance` fails if a fixture
reappears under `runs/`.

```bash
cd theoria-arm && python -m armtools.verify_provenance   # 9 checks
cd theoria-arm && python -m armtools.backfill --all      # idempotent
```

### What an adversarial review changed

The derivation above was handed to a reviewer told to refute it. The four
verdicts survived — reproduced independently over a 347-commit universe
including reflog-only and dangling commits, and cross-checked by extracting six
commits' trees and running the *real* `_bootstrap.arm_version()` in each, which
agreed exactly. But three defects in the mechanism came back, and all three are
fixed here rather than filed:

* **`matched` did not mean what it said.** The scan walked
  `git log --all -- theoria-arm`, so it saw only commits that *touch* the arm —
  and every commit that leaves the arm alone carries its parent's hash. One arm
  version in this repository is shared by 187 commits while that scan finds one
  of them and called it unique. No manifest here was wrong, by luck of which
  hashes the runs recorded. The scan is now exhaustive over every reachable
  commit, keyed by the arm's subtree so it stays cheap: 350 commits, 24 distinct
  subtrees, 17 distinct arm versions. The four verdicts are unchanged.
* **The reimplementation did not match the walk.** `_bootstrap.arm_version()`
  skips directories with *substring* tests, so `runsim/` and `__pycache__x/` are
  skipped; the git-side reimplementation read them as path components and would
  have counted them. No such directory has ever existed here, so nothing was
  wrong — but the divergence would have been silent, showing up as a run that
  matched no commit for no reason. Pinned by a test now.
* **`arm_version` depended on where the arm was checked out.** The same
  substring test ran against the *absolute* path, so an ancestor directory
  decided it: under `.worktrees/runs-cleanup/` — an ordinary name under
  CLAUDE.md's worktree rule — every file was skipped and the function returned
  `files: 0` and the sha256 of the empty string. Any run made in such a worktree
  records a version that can never be matched to anything. Fixed in
  `_bootstrap.py` and pinned by a test.

A fourth was caught by this arm's own reproducibility check before the review
saw it: `branch` was being filled from `git branch --contains`, which returned
55 branches for one commit and took the alphabetically first — `agent/a2-crosscheck`,
a branch with no relation to the run — and wrote it into a required field. It
also made the manifest drift every time anyone pushed anything.

**`arm_version` covers `.py` files only.** Two commits differing only in a
prompt, a log or a fixture share a hash; four of the seventeen groups are
multi-commit for that reason. A manifest that names a commit is claiming the
sources matched, not that nothing else differed.
