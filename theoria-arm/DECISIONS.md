# DECISIONS — theoria-arm

Every design call that could have gone another way, with the reason it went
this way. Numbered `D-P8-nnn`. A decision that was later reversed keeps its
entry and gains a reversal note; nothing is deleted.

---

## D-P8-001 · This arm composes `proxy/` as a library instead of calling `proxy.runner`

`proxy.runner.run_game()` is the designed entry point and it is not used. Three
reasons, all of which only appear on a live run:

1. **No `try/finally`.** If `arm.play()` raises, `run_game` never reaches
   `run.run_end(...)` and never writes the run record. A first contact with an
   unknown game is precisely where an arm raises, and the result would be a
   ledger with an orphaned `run_start` and no summary. `harness/run.py` writes
   `run_end` from a `finally`.
2. **The env proxy's `max_attempts` is not exposed.** The split between the
   proxy's retry envelope and the arm's matters (see D-P8-003) and `run_game`
   fixes the proxy's at 5.
3. **Its CLI always builds `MockArm`.** There is no `--arm-factory`, so a real
   arm has to come in through Python anyway.

`EnvProxy`, `Ledger`, `RunLedger` and `SealedPileGuard` are **imported and
used**, not copied. The ledger this arm writes is therefore produced by the
frozen writer with the frozen redaction, and satisfies `LEDGER_FORMAT.md` by
construction rather than by imitation. No file under `proxy/` was modified.

## D-P8-002 · The model side is recorded but **not proxied**, and that is a declared gap

`proxy/model_proxy.py` is the designed route for model calls and it cannot
work here. This was established live, before the arm was written, not inferred:

```
ANTHROPIC_BASE_URL=<model proxy>  claude -p --model claude-haiku-4-5 ...
```

The Claude Code CLI authenticates with an OAuth bearer. The model proxy strips
`Authorization` (it is not in `PASSTHROUGH_REQUEST_HEADERS`) and injects
`ANTHROPIC_API_KEY` instead — and this repo's `.env` holds `ARC_API_KEY` and
nothing else. Upstream answered `401 {"message": "x-api-key header is
required"}` to every request and the CLI retried until the subprocess timed
out. The evidence is archived as `evidence/model-proxy-401.jsonl`: **65
`model_call` records, every one at status 401**, alongside 66
`bypass_attempt` incidents recording that the CLI had a credential of its own
which the proxy dropped.

The stripping is **not a bug** — it is the sealing property that makes "no
bypass" structural. Repairing it means either editing `proxy/`, which belongs
to another track, or adding an `ANTHROPIC_API_KEY` this repo does not have.

So the model side takes `baseline-arms`' route (`claude -p --output-format
json`, the same transport the bare-CC arm is measured on) and the record is
written into the same ledger through the same frozen writer. What is preserved:
the record shape, the redaction, the verbatim `usage` block, and `beat` so
constraint 8 is checkable. What is lost, stated plainly: `request` is the
prompt this arm sent to the CLI, not the `/v1/messages` body the CLI sent to
Anthropic (the CLI adds a system prompt this arm never sees), so **no
conclusion about input-token composition may be drawn from this ledger**.
Output usage and cost are unaffected. `http.forwarded` is `false` and
`proxied` is `false` on every such record, so no reader can mistake it for
proxied traffic.

## D-P8-003 · The 400 wave is retried arm-side, at the cost of extra `env_step` records

`arc-recon` established (INC-001b/INC-002a) that ARC's `400 "game <id> not
found"` is a transient fault arriving in 1–3 minute waves off a multi-instance
backend, and that a 40-attempt envelope with linear backoff capped at 5s turns
"0 of 8 actions succeed" into "4/4 dev-pile games PASS determinism". The
pre-flight for this very run needed **18 attempts** for one RESET, so the wave
was active at launch and this is not a historical curiosity.

`proxy/forward.py` does not retry 400 (`RETRY_STATUSES = {429, 500, 502, 503,
504}`), and `proxy/` may not be edited from here. The retry therefore lives in
`harness/arc.py`, on the arm's side of the proxy.

**The consequence, named rather than hidden:** each retry is its own request
through the proxy and therefore its own `env_step` record. The ledger shows
more steps than the scorecard shows actions. This is within
`LEDGER_FORMAT.md` §3 ("`step_idx` increments once per command, including
commands the guard or a variant refused") and it is the honest shape — a
refusal is evidence, not an absence. `MANIFEST.json` records both counts.

500 is deliberately **not** retried arm-side even though the proxy retries it:
`tn36`'s ACTION6 answers a deterministic 500 on every one of 88 attempts, and
an envelope on a certainty spends the wall clock for nothing.

## D-P8-004 · The action ceiling counts successful ACTIONs; RESET is free

`baseline-arms` compared `scorecard.total_actions` against its ledger on four
independent samples across two models and two games and found it equal to the
count of **successful** actions every time; failed 400s did not bill. The 120
ceiling is therefore counted in successful ACTIONs, with a second, looser
ceiling on total HTTP commands so a wave cannot turn into an unbounded run.

RESET is not gated by the action ceiling at all. This was a bug first: the
pre-flight, which is designed to spend zero actions, could not send its RESET.
A run that has spent its last action must still be able to open a session, and
`tests/test_arm.py::test_a_spent_budget_can_still_open_a_session` pins it.

## D-P8-005 · The arena crop, and every other narrowing, is declared with its number

The engines were validated on 12×12 fixtures. A 64×64 ARC frame is 4096 cells;
handing all of them to `mdl_segmenter` buys one enormous track, and
`zero_space` would build tens of thousands of GF(2) features. Two narrowings
are applied:

* `world/adapt.choose_window` crops to the bounding box of cells that have
  **ever changed**, padded by one, and only above 1200 cells. It reports
  `covered`, the fraction of dynamic cells inside the window — 1.0 by
  construction, recorded anyway so a later change cannot silently drop cells.
* `world/frames.cells_of_interest` caps the law search at 240 cells, most-active
  first, and `adapt.laws` reports `cells_dynamic`, `cells_used` and `narrowed`.

A law found over 240 of 900 dynamic cells is a law about those 240. Saying so
in the report is the difference between a narrowing and a lie.

## D-P8-006 · `cegis_miner`'s refusal is recorded, never worked around

`transitions_from_segmentation` raises unless every transition narrates exactly
one `move` event or none. That is a real claim about a world — it says there is
one mover and nothing else changes when it moves — and a real ARC game may
simply not be like that. Reshaping the input until the engine answers would
make it answer a question it was not asked. `adapt.mine` catches the refusal
per track and puts the reason in the report, and the desk sees it.

## D-P8-007 · Planning has three tiers and a fourth outcome that is not UNSAT

`Theoria.md` 1.10(b) says the framework does not write its own planner and
gives a three-rung ladder. Tier 1 is the designed route, PDDL → `fd_adapter`;
it is tried and its refusal is recorded as evidence about `gen_pddl` (the
weakest of the four generators — it ignores the level instance, hardcodes
objects to cell 0,0, and does not expand `forall`). Tier 2 is the ladder's
first rung done exactly: breadth-first over the manual's own `step`, goal test
`is_goal`, length-optimal for unit costs, node cap declared.

The fourth outcome is `no_goal_declared`. On first contact an ARC game does not
tell you what winning is, so `is_goal` compiles to `return False` and no search
can succeed. **That is not unsolvability.** Constraint 6 forbids reading a
failed search as a theorem, so this status is spelled differently from `unsat`
and carries the sentence "this is a gap in the manual, NOT a proof".

## D-P8-008 · Lean is attempted only under a state-count ceiling, and refused loudly otherwise

`gen_lean`'s two developments are the pagoda route (needs a LINE world and an
`lp_potential` certificate) and the enumerative route (executes the generated
predictor over the whole state space and asks the kernel to decide it). A
64×64 grid world is neither a line nor small: with one mover the space is ~4×10³
cells to a power. `books._gen_lean` estimates the count, refuses above 200,000,
and records the estimate and both refusals. **An unavailable proof layer is a
gap to report, never a green tick to award** — `certify.expensive` reports
`available: false` and the run's `green` flag stays false.

## D-P8-009 · The problem instance is computed from frames; only the two books are written by the desk

`Theoria.md` 1.10(a) splits the manual (domain, travels between levels) from
the level layout (problem, per instance). Here that split is mechanical: the
board is the cells that have never varied, and each declared object is located
by its colour in the **first** observed frame. The desk writes neither.

Objects are located in the first frame, not the current one, because
`initial_state()` is where certify starts its replay and where plan starts its
search; locating them in the latest frame would make the manual's t=0 disagree
with the world's t=0 on the very first comparison. This was a bug before it was
a decision.

The one thing the desk must supply is the colour: `# arc-colour: <n>` on each
`object` line. The DSL has no slot for a literal colour in the word table, and
without it the object is located nowhere. An unlocated object does **not**
crash the run — it enters the level at the origin marked absent, and certify's
responsibility pass then reports every pixel it should have explained, which is
the diagnosis the desk needs delivered by the check that exists for it.

## D-P8-010 · The evidence gate: a surprise triggers theorize, but only once per evidence set

Constraint 8 says no surprise, no model call. It does not say every surprise
deserves a fresh call. Certify fails, theorize repairs, certify fails again on
the *same frames* — a third call buys a differently-worded manual against
identical data at full price.

So: at most two theorize calls per turn (theorize → certify → theorize →
certify, which is the arrow A0 reported was never exercised at all), and across
turns a gate on `len(store.steps)`. With surprises pending but no new evidence,
the turn falls through to probe and the manual **stays red** until evidence
arrives that could change it. A red manual carried openly is the correct state;
a manual rewritten until it stops complaining is not.

## D-P8-011 · Probe hypotheses are built by ablation, and probe design spends no model call

The frontier, once a manual exists, is: the manual; the manual with rule *r*
removed, one per rule; and `inert` (nothing changes). The generated predictor
exposes `fired(state, action)`, so the ablation is exact rather than guessed.
`inert` is the hypothesis A0's R-05 needed and could never test — a rule that
is *missing* rather than wrong predicts "nothing happens".

`probe_frontier` then computes entropy per action, priced in actions because
the path costs quota (1.10(b)). This is exact computation on a deterministic
world, so **probe design here spends no model call at all**, even though
constraint 8 would allow one. When nothing separates anything, the arm records
the unrunnable probe with its reason (cold-start-a2 P-3: a probe quietly
dropped is a lie) and then explores the least-tried legal action — and says
that is what it did rather than dressing exploration up as an experiment.

## D-P8-012 · ACTION6 is not offered to the loop

`arc-recon` and `baseline-arms` between them attempted ACTION6 1,254 times
across three games, with and without `data: {x, y}`, and every single one
returned HTTP 500. `g50t` does not offer it (`available_actions` is `[1..5]`),
so this costs nothing here, but `_legal_actions` filters it explicitly rather
than relying on the game not to offer it. The filter is stated in the run
report so it is not mistaken for the world's own answer.

## D-P8-013 · The desk sees the frames, the candidates and the books — and nothing else

`ModelDesk` starts `claude -p` in an empty temporary directory **outside the
repository**, for baseline-arms' D-009 reason: Claude Code walks parent
directories looking for `CLAUDE.md`, and a desk started inside the repo would
read `Theoria.md`'s design, the pile cut, the other arms' traces, the cold
starts' worked answers and this arm's own source. What the desk knows about
the framework is what `inner/theorize.py`'s preamble tells it. `ARC_API_KEY` is
removed from the child environment.

This arm also does **not** read `baseline-arms/schema_traces/` even though those
trajectories cover `g50t` and are on the dev pile and would be legal to read.
Feeding another arm's trace to this one would give Theoria evidence bare-CC
never had, and `Theoria.md`'s Part 2 discipline is that the three arms differ
only in the inner loop. Every frame this arm reasons over, it paid for.

## D-P8-014 · The grammar card is a constraint statement with a test behind it

The binding authority on what a manual may say is `gen_python`'s vocabulary —
`CONTRACTS/dsl_grammar_v0.2.md` says so itself ("Where this document and that
parser disagree, the parser is the defect"). `inner/grammar_card.py` states
that vocabulary exhaustively, and
`tests/test_arm.py::test_the_grammar_card_example_actually_compiles` compiles
its worked example every run. A desk told about a clause the backend will
refuse writes a manual that dies at compile, spends a call on the repair, and
reports an expressivity gap that is really a prompt bug. The first dry run
produced exactly that failure — the card had never mentioned `# arc-colour:` —
and the card, not the arm, was the fix.

## D-P8-015 · Two cost figures are kept on purpose

The CLI reports `total_cost_usd`; `proxy/cost.py` derives a cost from the
recorded `usage` against `pricing_v1.json`, a table that has never been checked
against a real bill. Both are recorded so they can be compared. Agreement is
the first validation of that price table on real data; disagreement is a
finding about the table. No dollar figure is written into the ledger itself
(`RunLedger.model_call` refuses `cost`/`cost_usd`, D-004) — the CLI's number
rides inside the recorded response envelope, which is recorded whole because
that is what the format says to do.

## D-S8-016 · A backfilled manifest derives or abstains — it never fills in

Five runs had no manifest and had to be given one months of commits later. The
tempting shortcut is to run `archive.build` over them, because it produces a
complete-looking file. It also calls `git rev-parse HEAD` and
`_bootstrap.upstream_pin()`, both of which describe the machine writing the
manifest rather than the run being described, so the result is a confident
record of the wrong thing — which is strictly worse than a gap, because a gap
is visible and a wrong number is not.

`armtools/backfill.py` therefore takes every field from the run's own ledger or
from git, and where the evidence does not reach, writes `null` with an entry in
`provenance.missing` saying what is absent and why. `provenance.status` is
`complete` only when CLAUDE.md's four required fields are all derived. Two of
the five are `complete`; three are not, and say so.

Two consequences worth naming, because both were tempting and both are wrong:

* **`git branch --contains` is not a source.** It answers which branches hold a
  commit *today*, so a manifest built on it changes whenever a colleague pushes.
  The reproducibility check caught it doing exactly that. `branch` now comes
  from the parent run's contemporaneous manifest, labelled as inherited, or is
  absent.
* **A manifest this tool wrote is rebuilt, not amended.** Amending its own
  output would relabel a derived manifest as a generator-written one and the
  second run would not reproduce the first.

## D-S8-017 · `base_commit` is checked against the run, not trusted

`arm_version` — a sha256 over this arm's `.py` sources, recorded in every
`run_start` — is a function of the tree alone, so it can be recomputed at any
commit and matched (`armtools/armversion.py`). That makes `base_commit`
falsifiable, and when the four existing manifests were checked, all four failed:
two named a commit later than the one whose tree their run's sources match, two
named a commit whose tree the run's own hash contradicts.

Three limits, all of which an adversarial review had to find before they were
written down, and each of which would have produced a confident wrong answer:

* **The scan must cover every reachable commit, not the arm's own log.** A
  commit that does not touch the arm carries its parent's hash and is invisible
  to `git log -- theoria-arm`; one arm version here is shared by 187 commits.
  Scanning only the arm's log reports `matched` and names one of them. The scan
  is now over `rev-list --all`, keyed by the arm's subtree so it stays cheap.
* **`matched` is a claim about `.py` files.** Two commits differing only in a
  prompt, a log or a fixture are indistinguishable; four of seventeen groups are
  multi-commit for that reason.
* **The commit is not "where the run was launched from".** Two of these commits
  were created 21 s and 57 s *after* their run started — the fix under test was
  committed mid-run. The hash says the sources were byte-identical to that
  tree, which is what reproducibility needs, and the manifest says exactly that
  and gives the arithmetic.

`archive.py` now runs the check at write time and records the verdict beside the
field rather than leaving a future audit to discover it. It does not *correct*
`base_commit` — HEAD at archive time is a real fact and worth keeping — it puts
the reproducible commit next to it and says which is which. A check that can
only be run by someone who already suspects the answer is not a check.

## D-S8-018 · A test's run directory is not archive material

`runs/` is what Phase 4 reads to account for every action this arm spent. Two
`pytest-*` directories sat in it. They were gitignored and so never reached the
repository, but a directory listing could not tell them from runs that cost
money, and the audit that opened this item counted eleven runs where there were
nine. Ignoring a thing in git is not the same as keeping it out of the archive.
Fixtures now write to `.pytest-runs/` and `verify_provenance` fails if one
reappears under `runs/`.

## D-S8-019 · `arm_version` is computed below the arm root, not on the absolute path

`_bootstrap.arm_version()` skipped a directory when `os.sep + "runs" in root` or
`"__pycache__" in root`, applied to the **absolute** path. An ancestor directory
therefore decided the answer: under `.worktrees/runs-cleanup/theoria-arm` — a
perfectly ordinary name under CLAUDE.md's worktree rule — every file was
skipped, and the function returned `files: 0` and the sha256 of the empty
string. A run made in such a worktree records a version that matches nothing and
never can.

The tests are now applied to the path below the arm root. They remain substring
tests, so `runsim/` and `__pycache__x/` are still skipped: making them
component tests would change the hash of any tree containing such a directory,
and every hash already recorded has to keep reconstructing. No tree in this
arm's history contains one (`git log --all --full-history --name-only`), which
is what makes the narrow fix safe and the wide one unnecessary.

Two tests pin it: one that the git-side reimplementation in
`armtools/armversion.py` agrees with the walk on exactly the cases that separate
the two readings, and one that the hash is the same wherever the arm is checked
out. The reimplementation had in fact diverged — it read the rule
component-wise — and the divergence was silent: it would have surfaced as a real
run reporting that it matched no commit, for no reason.

## D-A3-001 · A level boundary segments the trajectory; it is not a transition

The beats that reason over the trace — `certify`'s replay, `commit`'s and
`probe`'s roll-forward, `theorize`'s evidence brief, `books.problem_from_frames`
— now take `store.since(levels.start)` rather than the whole store
(`inner/loop.py:_level_store`). The whole store is still what `trace.jsonl`
records: the boundary is a fact about the run and is kept.

The reason is arithmetic, not taste. ARC advances a level in-band: no action
causes it, the envelope's `levels_completed` increments and the next frame is a
different board. `certify.cheap` replays the manual's `step` over every recorded
action and compares grids, so across such a jump it predicts level N's next
state and observes level N+1's opening board. That is a `replay_mismatch`; a
`replay_mismatch` is a surprise; and a surprise is the only thing that calls the
desk. Left alone, the arm would pay opus prices, twice per level, to repair a
manual that was never wrong. `problem_from_frames` has the matching defect:
pooled across a boundary, "the cells that never varied" is the intersection of
two unrelated boards, which describes neither.

**The alternative that was not taken.** A level advance could be modelled
*inside* the manual, as an event with a precondition and an effect. That is a
stronger claim and a more interesting one — it would let the playbook plan
*through* a boundary. Segmenting is the conservative reading: it says the domain
is silent about level advance rather than saying something no evidence supports.
If a later run produces evidence about what completing a level requires, that
evidence belongs in the playbook and this decision should be revisited.

**What this costs.** Restricting `theorize`'s evidence to the current level
means the frames of level 1 are not re-shown on level 2. The knowledge is meant
to survive in the books rather than in the frames — which is Theoria's thesis,
not a workaround — but it is a real narrowing and the engines see a shorter
trace at the start of every level. It is recorded here so that a run where the
manual visibly forgets something is read as evidence about this decision.

## D-A3-002 · Two files travel between levels, and their hashes say so

`Books(root, seed_from=...)` copies exactly `theory.dsl` and `playbook.dsl`, and
records the sha256 of each in `CARRIED.json`. `problem.json` deliberately does
not travel: it is computed from the frames of the level being played, so
carrying it would carry an answer to a question the new level has not asked.
`generated/` does not travel because the four forms are re-derived from the
domain, which is what co-derivation means; `snapshots/` does not travel because
a revision history belongs to the run that made it.

The discipline is `cold-start-a3/a3pipeline/transfer.py`'s, which asserts
byte-identity by sha256 rather than by inspection. "The manual that played level
2 is the manual level 1 wrote" is then a checkable claim about artefacts rather
than a sentence in a report — which is the only form in which C3's transfer
claim can appear in the paper.

## D-A3-003 · Surprises pending at a boundary are carried, not retired

**Superseded within the same branch, before merge.** The first version of this
decision retired them: `Register.retire_pending` marked them
`handled_by = "retired: <reason>"` on the argument that a surprise fired against
a trajectory the arm can no longer show would buy a model call adjudicating
evidence that no longer exists.

An adversarial pass took the argument apart, and it does not survive contact
with the loop. `need` in `_theorize_and_certify` is a *boolean*, and
`Register.handled` closes **all** pending surprises in one call -- so one
pending surprise costs exactly what three do. Retiring bought nothing
measurable.

It was also load-bearing in the wrong direction. Emptying `pending` was one of
three mechanisms that, together, left a run unable to notice its own manual had
gone stale: the evidence gate was re-armed (so theorize was skipped), certify's
guards asked "has certify ever run" rather than "has it run on this level" (so
certify never ran again at all), and `pending` was empty (so `need` was False).
With all three closed at once, an arm could play out its entire remaining budget
on round-robin exploration with a dead book, zero model calls, and a green
`constraint_8` -- a perfect tick on a dead run.

So: pending surprises **cross the boundary untouched**, and the event records
how many did (`pending_surprises_carried`). A boundary should make the desk look
*again*, not look away. `Register.retire_pending` remains, unused by the loop:
its accounting is still worth having correct, and a caller may yet want it.

The related defect is worth recording next to it, because it is the one that
cost real money to find in principle: `armtools/archive.constraint_8` never
reads `handled_by`, so a retired surprise *raised the ceiling* on unexplained
model calls by one. Three boundaries retiring two each bought six free
unexplained calls with `holds` still True -- a false negative in exactly the
direction that hides a violation of the arm's central claim. That is now moot on
this code path and is still an open defect in the audit itself.

## D-A3-004 · A level advance is proved by the board, not by a state string

`_try_advance_level` sends RESET after a `WIN` that the roster says is not the
last level, and then compares the returned frame's `grid_hash` against this
level's opening frame. Identical means the level did **not** advance.

The first version compared `state != "WIN"` and would have been wrong on the
likeliest path. `arc-recon/ACCESS_CHECK.md:24-25`, verified by precheck on all
four development-pile games, records that `POST /api/cmd/RESET` returns
`full_reset: false` and that RESET resets to *the level the session is on*. So
RESET-after-WIN most likely restarts the same level and returns `NOT_FINISHED`
-- which the state check passes. The arm would have recorded a level completion
that never happened, cut the trajectory, and fed a fabricated boundary into the
series behind the paper's figure. A fabricated level completion in a figure is
worse than stopping.

The frame comparison is a real measurement rather than an inference because
`ACCESS_CHECK.md` §2 establishes RESET frames are byte-identical across six
replays in four sessions. Whichever way it goes, the arm records what it saw
under `levels.reset_probes` -- this branch is the first thing in the repository
that will ever observe a level completion, and it should come back with data.

The advance budget is spent **per boundary, not per run**: it was never reset on
success, so a run that advanced twice stopped at the third boundary reporting
`level_advance_unknown` immediately after advancing twice. g50t has seven
levels.

---

## D-A3-005 · The environment proxy is a child process, because the seal is a boundary and not a discipline

`Run.__init__` used to build an `EnvProxyConfig`, and that constructor's second
statement is `read_secret("ARC_API_KEY", ...)`. So the live game credential was
resident at `run._cfg.api_key`, and in the process-wide `VAULT`, inside the same
interpreter that runs the inner loop, the engines and every line of
model-facing code. Nothing leaked it. It was simply *there*, and `Theoria.md`
Phase 1's 臂进程摸不到环境凭据 was false as written -- measured with a sentinel
key in `runs/20260730T1020Z-A3-SEAL-CONJUNCT-ONE/`, not argued about.

`python -m proxy.env_proxy` is now started as a child (`harness/proxy_process.py`)
and this process holds a `http://127.0.0.1:<port>` URL and nothing else. The
child reads `.env` itself. **The parent neither passes the credential nor reads
it**, which is what makes this a seal: an arm-side bug cannot leak a value its
process never held, and no amount of care in the parent was ever going to be
checkable the way a process boundary is.

Three things were deliberately *not* done.

`proxy/env_proxy.py`'s in-process `EnvProxy` class is untouched. `proxy/runner.py`
runs the env proxy, the model proxy and a mock arm in one interpreter and the
proxy track's tests assert against handler objects directly; the "arm" there is
the test, so there is nothing to seal and forking those flows would cost the
ability to poke at internals for no property gained. The standalone CLI is
additive: a `--port-file` handshake, `--campaign`/`--reservation-id` to attach
to a claim the parent already opened, `--api-key-env` for stubs, and
`POST /__proxy/shutdown`.

The credential is never a command-line argument, only a variable *name*. On
Windows any user can read another process's command line, so a `--key` flag
would publish to the whole machine what this decision exists to contain. The
stub channel is a different variable name from `ARC_API_KEY` as well, so a mock
run cannot silently fall back to the real credential and inject it into a
request bound for a loopback stub -- a leak with a green test beside it.

The reservation is **attached, not owned**. The parent opens one claim on the
shared pool and passes its id; the child rebuilds a handle and `EnvProxyConfig`
marks any reservation it was handed as one it does not release. A child that
released it would hand back headroom the desk is still spending under. That is
also what makes hard-killing the child safe, which matters because Windows has
no SIGTERM: `stop()` asks over HTTP, waits, and only then insists.

What it costs: about a second of child startup per run, and the ledger now has
two writers. `proxy/ledger.py` takes a cross-process lock on a sidecar file and
re-reads the tail inside it, and the step and call counters are disjoint by
writer, so one hash chain with two writers is exactly as sound as one with one.
`tests/test_seal_process.py` verifies a real two-writer run's chain rather than
citing the lock.

The instrument matters as much as the fix. `tests/test_seal_process.py` plays a
whole mock game in a fresh interpreter with `ARC_API_KEY` removed *and*
`read_secret` replaced by something that raises, and asserts the positive half
too -- a sentinel arriving at the upstream as `X-API-Key` -- because "the
sentinel is nowhere in the parent" is also satisfied by a proxy that injects
nothing, which is not a seal but a broken proxy.

---

## D-A3-006 · The pile cut is screened by the desk, not by whoever built it

`inner/loop.py` hands `ModelDesk(forbid_in_prompt=...)` every sealed id and
stem, tested with a bare `in`. Two failures pull in opposite directions and
both are real.

It is only as good as the caller: a `ModelDesk` built anywhere else -- a smoke
script, a new beat, a test -- gets the default empty tuple and screens nothing.
And a bare `in` over twenty-five stems refuses ordinary English (`sk48` fires
inside `task48`), which is how a guard ends up switched off, taking the
twenty-one that matter with it.

So `ModelDesk` now loads the cut itself and scans with the proxy's own
`SealedPileGuard.game_ids_in_text` -- token-bounded against the register,
percent-decoding, NFKC-normalising, zero-width-stripping, one level of base64.
All properties the red team already paid for on the request path; reusing the
scanner rather than writing a second one is the point of the change.

The ids are read from `arc-recon/data/piles.json` at construction and **never
hard-coded**. Writing twenty-one sealed identifiers into this arm's source
would put the exam set in a tracked file, and a copy of a cut is a second cut
that can disagree with the first. Fail-closed: a desk that cannot enumerate the
sealed pile cannot promise it kept the pile out of a prompt, so it does not get
built.

Three outcomes, and the middle one is why this is not one `if`. A sealed id or
bare stem raises `SealedPileBreach`; a development id raises `AnonymityBreach`;
an id-*shaped* string that is in neither pile is allowed through. That last one
is deliberate: `<2-6 alphanumerics>-<8 hex>` is a shape ordinary prompt text
hits by accident -- a branch name, a run slug, half a digest -- and the sealed
pile is a fixed enumeration, so a shape absent from the register is not a
sealed game. The request path can afford `unknown_policy = deny` because a
request names one game on purpose; a 20,000-character prompt does not.

`SealedPileBreach` subclasses `AnonymityBreach` so `inner/loop.py`'s
`except (AnonymityBreach, CredentialBreach): raise` keeps the stricter case
fatal without editing another agent's file. The two still need separate names:
an `AnonymityBreach` says a run is inadmissible and is undone by repeating it
with a game-free slug, while a sealed leak teaches a model a game the exam has
not run yet -- `piles.json` rule 3, the class of event INC-BA-001 is -- and no
repetition un-teaches it. They must be distinguishable in a ledger and in a
traceback. The subclassing is load-bearing enough that `tests/test_arm.py`
drives both through the real loop: making them siblings is the obvious refactor
for "different incidents", and it would drop the stricter one into the broad
`except Exception` handler.

The incident is written **before** the raise. An incident recorded only by a
traceback is an incident in a terminal somebody has already closed, and the
record uses `sealed_pile_in_prompt`, which was already in `proxy/canon.py`'s
open set and had never been raised by anything.
# E3 — the second online game

## D-E3-001 · The manual travels; the level instance never does

> Ported 2026-07-31: the flag is spelled `--seed-books` on master (the E3
> spelling still works as an alias, because it is in the archived run records),
> and the copy itself is done once, by `Books(seed_from=...)`. Master had
> independently built the same carry for the level boundary; two writers for one
> carry is a provenance record that can disagree with itself, so
> `transfer.carry` now adorns that record rather than making a second one.
> Nothing below changes about *what* travels.

`--seed-books` copies `theory.dsl` and `playbook.dsl` and refuses to copy
`problem.json`. That is not tidiness — it is the whole content of the transfer
claim. `inner/books.py` already draws the domain/problem split by arithmetic:
the manual is the domain, and the level is computed from the frames of the game
being played. So "the same `theory.dsl` against a different computed problem"
is what C3 transfer *means* here, and carrying the level file would import
g50t's board into sk48 and leave the manual being checked against a world it
was written for while appearing to be checked against a new one. The exclusion
is a named entry in `transfer.json` rather than an absent line of code, and a
test asserts the file does not arrive.

A carry from a source with no `theory.dsl` **raises**. A failed carry and a
cold start produce the same empty book, so every artefact downstream would be
uninterpretable; refusing is the only way the difference stays visible.

## D-E3-002 · The cold beat runs before the first model call, and its prediction is written first

The transfer datum has to be taken on an *unrepaired* manual. Once the desk has
been called on the new game, what is being measured is a repaired manual, which
is a much weaker claim and one the run cannot distinguish afterwards. So
`_cold_transfer` sits between the opening sweep and the main loop: compute this
level's problem from the carried manual's own declarations, compile, certify,
and record — with `model_calls_so_far: 0` in the report as the assertion that
this is what happened.

The ordering *inside* the beat matters as much. The carried manual's own
render-accounting formula is evaluated and written to disk as a
`prediction-only` revision of `transfer.json` **before** certify runs, on the
same discipline `probe` already follows: a prediction recorded after its result
is not a prediction. A test spies on the writes and asserts the first one
carries a prediction and no certify result.

## D-E3-003 · The formula is the part of a game-specific manual another game can test

Almost everything in the g50t manual is about g50t — its lattice, its gate, its
HUD — and carrying those to sk48 tests nothing except that they are wrong.
One clause is different. `render_accounting_closed` states a *formula*,
`unexplained(frame_0) = D0 - K`, and claims it is arithmetic that can be run in
advance. That claim is not about g50t; it is about how this framework's
renderer and its responsibility checker interact. A different game can
therefore genuinely confirm or refute it, and that is the one honest
cross-game test available at zero model cost.

It is evaluated strictly inside its stated domain. `arc-instances: all` spreads
one declaration over every dynamic cell of its colour and breaks the formula's
"one colour, one pixel" step outright, so when a spread declaration is present
the prediction is **withheld** rather than reported wrong: a formula applied
outside its stated domain is not a test of it. `verdict` is one of `held`,
`refuted`, `withheld`, `unscorable` — the last for a manual whose `render`
raised, where certify reports no count at all and scoring it as a refutation
would be a second error on top of the first.

## D-E3-004 · Retention is measured by name, and says that is all it measures

What survived the new game is counted over declared names — objects,
landmarks, events, rules, invariants, theorems — kept, dropped and added.
Names are a mechanical proxy for content and the report labels itself as one:
a kept name may have a completely rewritten body. The snapshots under
`books/snapshots/` are where bodies are compared, and every revision is kept
for exactly that reason. Reporting a retention rate without the caveat would
be the kind of number that gets quoted without its scope.

## D-E3-005 · A refusal is a delivery; an error is not

`engines_online.jsonl` gets one row per dispatch per engine, and `delivered`,
`error`, `skipped` and `n_refusals` are four separate columns. `cegis_miner`'s
precondition — exactly one `move` event per transition — is a real claim about
a world, and a real game need not satisfy it; an engine that refuses with its
reason is an engine working correctly. What would falsify E3's supply-chain
claim is an engine that raises, hangs, or comes back empty without saying why.
Conflating the two would turn a measurement of the engines into a measurement
of the game.

The dispatch was lifted out of `theorize.run` into the loop so that every sweep
gets a row whether or not a desk call follows it. The cold beat makes no model
call at all, and its sweep is still on the record; a desk call that fails still
had its engines run.

Each row carries `run_id`. The file is append-only and sits beside a ledger
that partitions by `run_id` for the same reason: a slug reused across runs must
stay readable. Real slugs are UTC-stamped so it should not happen — but "should
not happen" is not a partition key, and the test suite hit exactly this on its
second consecutive run.

## D-E3-006 · The bill's x-axis is sampled when the money is spent

`ModelDesk` takes an optional `context` callable and stamps whatever it returns
onto each log entry. The loop supplies the billed-action count, the command
count, the transition count and the turn index, sampled at the moment of the
call. Reconstructing that axis afterwards from timestamps guesses, and a
guessed x-axis is not a measurement.

`bill_shape.json` is deliberately **not** `cost_curve.json`: `armtools/archive.py`
owns that name and writes a flat per-call list rebuilt from the ledger. Two
artefacts, two names, no race. The file also states in its own text that
`actions_at_call` counts billed actions while `commands_sent` counts HTTP
requests, and that a curve against one is not a curve against the other —
because on this API the two differ by the 400-wave retry envelope.

## D-E3-007 · The spend gate is checked for, used if present, and reported absent if not

E3's brief makes `proxy/spend_gate.py` mandatory *once S3 has landed*. It has
not: the file does not exist on this commit and `agent/s3-spend-gate` carries
nothing under `proxy/` matching `*spend*`. `armtools/spend_check.gate_status()`
therefore looks for it every time, loads and calls `reserve()` if it is there,
and otherwise records `absent` with that reason and holds no reservation.

Fail-closed is S3's rule for the gate's own callers, and it cannot bind a
caller that runs before the gate exists — there is nothing to fail closed
against. What *can* be required is that the situation is never recorded as a
pass, and a test pins that: an absent gate must report `absent` and
`reservation.held == False`, never `ok`. Every plan already carries the
`campaign` field S3's `reserve(campaign, usd_cap, action_cap)` will want, so
adopting the gate is a wiring change rather than a rewrite.

## D-E3-008 · The action budget is not this arm's binding constraint, and the plan says so first

Measured on the first live contact: $1.2635 per desk call, 516 seconds per
call, five calls for $6.32. The evidence gate holds the desk back until four
new transitions have arrived, so one cycle is roughly four actions and one to
two calls. Reaching a 120-action budget therefore costs about **$35** and most
of a day, and an $18 ceiling stops the run at roughly **29–61 actions**.

That arithmetic is computed from the prior run's measured cost — never
hardcoded, because a hardcoded price is a number nobody re-derives when the
model changes — and written to `BUDGET_PLAN.json` before the first action is
spent. Stating it in advance is what makes the outturn a measurement of the
bill's shape rather than a shortfall against 120.

## D-E3-009 · sk48, not tn36, and the reason is mechanical

Both passed `arc-recon`'s determinism pre-check, so either was eligible. But
`precheck.json` records tn36's `available_actions` as `[6]`, and every one of
its sixteen probe actions returned an identical frame hash — ACTION1–4 do
nothing there because they are not offered. ACTION6 is the click family, whose
payload shape is unsolved in this repo (1,254 attempts, every one HTTP 500) and
which `_legal_actions` filters out by D-P8-012. The arm would have found no
legal action and stopped before its first turn. sk48 offers `[1, 2, 3, 4, 6, 7]`
and its actions visibly change the frame, so it is the only one of the two this
arm can actually play.

A consequence worth naming: sk48 offers **ACTION7**, which g50t never did. The
carried manual contains a theorem, `two_action_keys_have_never_been_pressed`,
whose whole content is that keys 6 and 7 are unknown and must be held in
reserve. The opening sweep presses 7 on the first turn, because the sweep
predates any manual and takes the world's word for what is legal. The manual's
advice and the arm's behaviour disagree on turn one, in the record, for free.

## D-E3-010 · The five extra fields ride inside `request`, and a paid reply outranks a tidy ledger

`LEDGER_FORMAT.md` §4 closed `model_call`'s field set after P-8 landed, and P-8
wrote `beat`, `label`, `transport`, `proxied` and `proxy_gap` straight onto that
record. `canon.py` refuses all five (INC-TA-006).

Dropping them was not available. `beat` is what makes constraint 8 checkable
from the ledger rather than asserted in prose, and `proxied`/`transport` are
what stop a reader mistaking this arm's CLI traffic for proxied traffic. §4's
own refusal text points at §6 — "put it on an auxiliary record instead" — but
that route is closed here: `EVENTS` in `proxy/ledger.py` admits exactly seven
names, and none of them fits a model call's metadata (`env_meta` requires
`http` and means the environment side, `guard_block` requires `rule`/`path`,
`incident.kind` has a whitelist). Adding an eighth means editing another
track's directory.

So they went into `request`, which is a caller-owned object on the canonical
record and already carried three of the five. Nothing is lost, no event is
invented, no upstream file is touched, and `beat` stays on the ledger one level
deeper. `armtools/archive.py` reads both depths, because a constraint-8 check
that silently read `unknown` off every record of a P-8-era run would report a
violation that is really a schema migration.

The second half of this decision matters more than the first. **By the time the
ledger is written the provider has been paid**, so the arm's own log entry and
the transcript are written *first*, the ledger write is wrapped, and a refusal
is recorded in `desk.ledger_failures` and surfaced in
`summary()["calls_missing_from_ledger"]`. An incomplete ledger that says exactly
where it is incomplete is strictly better than a call that cost $2.70 and left
nothing behind. The old ordering turned a schema mismatch into a lost purchase.

And the test that pins it drives `ModelDesk` into a **real** `RunLedger` with
only the CLI stubbed. P-8's tests checked the record's shape against hand-built
dictionaries and passed while the live writer refused the real thing; the gap
was not a missing assertion but a missing subject.

## D-E3-011 · Landmark coordinates are level data, so they are stripped on carry

Excluding `problem.json` from the carry turned out to be an exclusion drawn
around a filename when the thing to exclude was a kind of content. Seven of
g50t's landmark coordinates reached sk48's computed level verbatim through
`# arc-cell: (r, c)` comments **inside the manual**, which is exactly what does
travel (INC-TA-007).

`transfer.strip_level_data` removes the hints at carry time. Three details are
deliberate:

* **On carry, not on write.** The source run's books are untouched, and the
  stripping is visible as a diff in the `rev01-carried` snapshot rather than
  being a silent difference between two files that claim the same provenance.
* **Both hashes are recorded.** `sha256` and `sha256_before_stripping` sit side
  by side in `CARRIED.json`, so a reader checking what was carried cannot miss
  that the text was modified in transit.
* **The landmark still declares itself.** Only the coordinates go. The level
  then places it at the origin and lists it under `landmarks_defaulted`, which
  is the pre-existing and visible failure mode for a coordinate the level cannot
  supply — not a new silent one.

## D-E3-012 · The first cold-transfer reading was wrong, and the run record keeps both

An adversarial review refuted E3's first headline, and every one of its points
was verified independently before being accepted.

The claim was that the carried manual predicted its own responsibility number on
sk48 (70 against an observed 72) and that the +2 was a mechanically explained
transfer result. What is actually true is that `certify`'s `cells_unexplained`
is **identically** `D0 − covered_by_objects`, given how `problem_from_frames`
builds the board and how the generated `render` paints one pixel per object. So
the prediction error is identically `K − covered_by_objects`, **D0 cancels**, and
the agreement could never have failed. The "corrected formula" derived from it is
`n_unexplained_at_t0`'s own definition written backwards — unfalsifiable, and
right on every game forever.

Worse for the claim: the correction was already in the carried manual, one
theorem below the formula. `responsibility_ceiling_is_two_pixels` says colours
whose raster-first cells are constant board cells "would explain nothing they
were not already given" — precisely sk48's condition on two of three objects. A
reading faithful to the theorem *cluster* predicts 72, exactly right. The
refutation was of `inner/transfer.py`, which implements the formula's
one-sentence summary and drops the qualifier beside it.

And no theory content transferred at all: the carried manual's only declared
action is `('key', 5)`, sk48 does not offer ACTION5, so every rule is unreachable
and `step` is the identity for every action the arm can send.

Two decisions come out of this.

**The run record keeps the original reading verbatim, under the correction.** A
run that quietly rewrote its own first conclusion would be the exact failure this
repository keeps writing incident reports about, and the superseded text is the
evidence that the review did work rather than a claim that it did.

**A carry should check the action-vocabulary intersection before it spends
anything.** It is free to compute — the manual's declared actions against the
game's `available_actions` — and it is the difference between a transfer
experiment and a manual that cannot be tested on the game it was carried to.
Recorded here as the next run's first requirement rather than implemented in the
middle of a live run.

## D-A3-B-001 · Goal-absence is a state, and it gets a rung ladder rather than a flag flip

Change B's reading is in `inner/goal.py`'s docstring and in
`runs/20260731T1740Z-A3-change-b-goal-state/RUN_STATE.md`. In one line: across
the four live carried legs of 2026-07-31, `plan()` was called 56 times and
returned `no_goal_declared` 56 times, `tiers` is `[]` in every one of them, and
`commit.json` is `[]` in all four. The arm was not searching and losing. It was
never searching.

Three decisions come out of that, and each of them could have gone another way.

**1. The fix goes above `plan`, not inside it.** `inner/plan.py` already reports
this exactly right — its `no_goal_declared` detail says in so many words that
this is a gap in the manual and not an unsolvability claim, which is
constraint 6 observed. Nothing in that file is wrong. What is missing is that
its output is a leaf: `inner/loop.py` compares it against `"sat"` and drops it,
so no artefact anywhere accumulates it. Changing `plan` would have meant
changing a beat that is behaving correctly in order to fix a recorder that is
not.

**2. No surprise of its own — and by the time this landed, none was needed.**
The obvious wiring is to make goal-absence fire a surprise, because a surprise
is the only thing in this loop that calls the desk. `inner/surprise.py` closes
the set at seven and says in its own constructor that an eighth is a change to
`Theoria.md` 1.10(d) rather than to a file, so an eighth was never on the table.

While this branch was being written, a parallel session reached the same
diagnosis from the same artefacts and answered it at the other end: commit
`79b948a1` makes `plan.surprises_from` fire `heuristic_miss` on
`no_goal_declared`, once per playbook token. This branch was rebased onto it
rather than argued against it. Two consequences, both recorded rather than
smoothed over.

The claim "nothing ever asks for a goal" was true when this branch was cut and
is **no longer true**. It is corrected here rather than quietly rewritten. What
remains true is the recording half: after `79b948a1` a leg that never holds a
goal still reports `levels_completed: 0` beside a plan history a reader must
reconstruct from `plan.json` by hand, and the campaign scoreboard still cannot
tell a campaign that searched and lost from one that never searched.

And the one legitimate reuse of an existing kind is now spent. `heuristic_miss`
is the computational family, whose book is the playbook, which is where a goal
belongs — that is the reuse, and it is a fair one. Firing a *second* surprise
for the same fact would call the desk twice for one gap. So the `propose` rung
buys no model call at all: it parks a *rider* that travels on the next theorize
call a surprise — `heuristic_miss` among them — has already paid for. The
model-call count does not move, constraint 8 is untouched, and a leg where no
further surprise fires simply never sends the ask, which the record shows as a
booked proposal with `answered: null` rather than hiding.

The two also differ on *when*. `79b948a1` keys its firing on the playbook token,
so a rewritten playbook that still has no goal speaks up again whether or not
any new world arrived to change the answer. `proposal_due`'s third conjunct is
exactly the refusal for that case: distinct states, not revisions.

**3. The default is `off`, and `off` means byte-identical.** The temptation is
to make `record` the default: it changes no decision and spends nothing, so it
looks free. It is not free — it adds a key to every turn record, to `run.json`
and to `RUN_STATE.json`, and this arm's archive is byte-compared. Preparing a
change and adopting it are separate acts with separate evidence, and this ticket
only did the first. `off` therefore writes no key at all: absent, not `null`, so
a default run's artefacts are indistinguishable from ones written before this
module existed.

**The criterion counts distinct states, not turns or dollars.** This is taken
from what the two live manuals said they were waiting for, in their own words:
one, that the goal could be stated only "after the body has once stood in the
socket and those pixels have become dynamic"; the other, that "the objective
lives in the twenty-nine rows I have never been shown". Both are claims about
unseen *world*. A toggle pressed forty times produces forty frames and two
states; re-asking the desk against evidence it has already refused on returns a
differently-worded refusal at full price, which is the same failure
`MIN_NEW_FRAMES_BETWEEN_THEORIZE` was introduced to stop. Four, and at most
three asks per leg, are judgement — nothing has been run that calibrates either,
and that is recorded as a gap rather than dressed up as a measurement.

**A signed absence is not silence, and the record now separates them.** Both
live manuals argued for having no goal and named a theorem for it. That is a
position, and a defensible one — a goal true in the wrong states stops the
planner at the first node. A manual with neither a goal nor an argument is a
different thing entirely, and until now the two produced identical artefacts.
The detector is deliberately narrow (the theorem's name must mention a goal
*and* absence), because a broad one that fired on
`theorem the_goal_is_probably_the_socket` would credit the manual with a
position it never took.

**What it costs.** `armtools/archive.py`'s `turn_series` rows gain three keys
and `campaign_series`'s totals gain four. No archived manifest is disturbed:
`turn_series.json` is not listed in the four legs' `files[]`, and check 8's
re-derivation goes through `armtools/backfill.py`, which does not regenerate it.
A run re-archived through `archive.build` after this change will write a
different `turn_series.json` than it would have before, and that is the declared
price — the same one `ARCHIVE_COST_FIELDS` names for a shape change, paid in the
open rather than avoided by keeping a column the scoreboard needs out of it.

## D-C-MERGE-001 · Three knobs, one prompt builder: the union, and the instrument that could not see it

`goal_protocol` (`inner/goal.py`), `probe_economy` (`inner/probe.py`) and
`desk_diet` (`inner/deskdiet.py`) were prepared by three sessions inside two
days, each default-off, each with its own proof that its own default moves
nothing. They are independent in intent. They are not independent in code: two
of the three meet inside `theorize.build_prompt`, and the merge of
`ep/c-desk-diet` had to say what that function is.

**1. The prompt is built inside the repair loop, once per attempt, and the
rider is threaded into it.** The `goal_protocol` side built the prompt once
before the loop and rebuilt it at each `continue`, passing `goal_rider=` to all
three call sites. The `desk_diet` side deleted all of that and moved
construction to the top of the loop, because `allow_patch` is a per-attempt
decision -- the last repair attempt withdraws the patch contract. The diet's
shape wins: it is strictly more general, and one call site cannot drift from
another. The rider becomes a `build_prompt` keyword on that single site.

The failure this avoids is quiet. A resolution that keeps the deletion and
forgets the keyword sends attempt 1 with the goal ask and attempts 2 and 3
without it; nothing raises, no existing test looks, and a `propose` leg would
report a rider it half-delivered. `tests/test_three_knobs_default_off.py`
compares the beat's actual prompts, attempt by attempt, against `build_prompt`
called with no knobs at all -- not against a golden string, which would only
prove that two copies of one mistake agree.

**2. `armtools/prompt_census.py` gets a `goal_rider` row, classified
`feedback`.** This is the defect the merge created and neither branch could
see. The census cuts a prompt at literal anchors and gives every unclaimed byte
to the section that opened last. It shipped knowing the twelve sections
`build_prompt` emitted on its own branch; the rider was a thirteenth. Total
chars are conserved either way, so nothing raises -- the ~1.4 kB ask is simply
billed to `engine_proposals` and reads as evidence growth that never happened.
That is the one direction that would flatter the diet, which is the measurement
the whole `desk_diet` change is judged by.

`feedback` rather than `boilerplate` was a real choice. The rider is near-fixed
text, which argues for `boilerplate`; but `boilerplate` is defined in that file
as text identical on every call of every leg forever, and the rider carries this
leg's own turn and action counts. Of the four kinds it is the arm telling the
desk about the arm's position -- not the world (`evidence`), not the desk's own
output handed back (`books`). A fifth kind was not added: `KINDS` is consumed by
every rollup in that file and by the shipped `bench.json`.

Adding the row moves no published number: it is optional, absent from every
archived prompt, and the per-section rollup skips names absent from both ends,
so `runs/20260801T0200Z-C-desk-diet/prompt_census.txt` and `bench.txt` both
re-derive byte for byte after the change (checked by re-running the MANIFEST's
own `reproduce` commands, not by reading the code).

**3. Nothing was reconciled away.** Unlike `merge-ep-probe-econ`, where two
sessions had built two mechanisms for one defect and the merge had to choose,
these three changes touch disjoint machinery: what the desk is asked about the
goal, which hypotheses the probe designer reasons over, and what the desk is
shown and asked to write back. Every conflicted hunk is a union -- import list,
constructor parameters, constructor body, and the `theorize.run` call site --
and the resolved `inner/loop.py` differs from master only by the branch's four
edits and from the branch only by master's. The claim each side made separately,
that its default is today's arm, is re-asserted for the conjunction rather than
inherited from the three halves.

## D-A8-001 · A billed call with no turn is recorded as one, never dropped

`battery/audit/live_economy.py`'s live-economy rung found two legs whose
`curves.json` billed fewer calls than the proxy ledger did:
`20260731T1310Z-A3-level2-carried-r2` accounted for 4 of 5 calls and $7.926367
of $9.556852; `...T1430Z-...-r3` for 7 of 8 and $11.761053 of $13.439862. Both
ended `spend_gate_tripped`.

**The mechanism, at the record level.** `inner/loop.py` builds a turn's
`record` at the top of the loop body (`loop.py:869`) and appends it to
`self.turns` only at the bottom, after `_commit` or `_probe_or_explore`
(`906`/`911`). Both send an ARC command; `ArcThroughProxy` raises
`SpendGateStopped` once the pool is red. So the last turn of a gate-tripped leg
runs its theorize, is billed, and dies on the next command -- above the append.
The turn was **opened and never closed**: not "never opened" (the desk call and
`desk_failures.json`'s `SpendGateTripped` at the same `step_idx` prove it ran)
and not "closed before the call was recorded" (the ledger's `model_call` is
`seq=205` for r2, the last `env_step` is `seq=204`, and nothing but scorecard
traffic follows).

`archive._turn_spine` then deals invocations to recorded turns
`theorize_rounds` at a time. The orphan had no turn to be dealt to, landed in
the `unclaimed` queue -- which it *reported*, correctly lowering
`join_confidence` to `degraded` -- and was then discarded.

**Why the A8 self-check did not catch it.** `curves.py` compared
`http_commands` summed over the curves against `env_step` records in the
ledger. The vanished turn had issued no environment command, because the gate
killed it before it could. The equality therefore held exactly (99 = 99 and
234 = 234) while 17% and 12.5% of the money was missing. A check on commands is
blind to a hole in the money; the two are now counted separately, along with
billed calls, and each raises.

**The call.** Three positions, and the third is the one worth arguing.

1. *The archive reconstructs the lost turn* rather than dropping it
   (`archive._unrecorded_turn_rows`). The row carries the calls and the
   dollars, owns **no** ARC command -- reassigning commands already attributed
   to a recorded turn would trade the money hole for a count hole, and
   `curves.py`'s first equality would then refuse the file -- and is flagged
   `turn_record_missing` on a column present, `False`, on every ordinary row.

2. *The confidence is not laundered.* A leg with such a row stays `degraded`.
   Making the money add up is not the same as having the run's own record, and
   the check that lowered the verdict is still emitted; it now says the
   leftover was kept rather than dropped.

3. *The row carries an integer `turn`, continuing the recorded sequence, rather
   than `null`.* `null` was the first instinct and it is wrong twice over.
   `_desk_context` stamps every desk call with `len(self.turns)` and
   `bill_shape.json` publishes it, so the archive can be checked against an
   independent artefact: r2's orphan is `turn: 10` there, its row is the
   eleventh, and 2 turn-0 rows + turns 1..8 puts the loop's own counter at 9 --
   which is what the reconstruction writes. And `null` is not free: at least
   one downstream reader does `int(row["turn"])`
   (`battery/adapters/theoria_live._turn_map`) and would raise on it. A crash
   is not a better record than a labelled inference. What makes it honest is
   that the label travels with it -- `turn_record_missing`,
   `turn_record_missing_why`, `turn_source`, and a
   `turns_with_no_record_of_their_own` block in the join.

**And the same fact is recorded at the source.** `inner/loop.py` now parks the
open turn in `_turn_in_flight` and `_save_all` adopts it
(`_adopt_the_turn_in_flight`), stamping `turn_aborted` with
`stopped_because`. Future gate-tripped legs record their own turn with their
own number and need no reconstruction. The record is not appended at the top of
the loop body, which would have been simpler: `_desk_context` publishes
`len(self.turns)` as the index the record will occupy, and that number is
already on disk in four legs' `bill_shape.json`.

# D-R2-001 · The frontier's anchor is a measurement nobody was taking, and it decided this ticket

R2 was chartered to replace the ablation frontier with a generated one, on a
structural argument that is correct: `manual`, `inert` and one
`without_<schema>` per rule are all *deletions* of the manual, the family is
closed downward, and it therefore cannot contain a mechanism the manual lacks.
`Theoria.md`'s engine table asks the rule miner for 全体一致假设的前沿 for
exactly this reason.

The brief also said: measure first, and if no generated frontier could have
contained the observed successors, say so instead of shipping one that also
cannot. Measuring first changed what got built.

**What the grids say that the hashes did not.** `20260801T0000Z-A-probe-
economics` measured the four legs of 2026-07-31 out of `probes.jsonl`, which
carries hashes. Reading `trace.jsonl` beside it makes one comparison available
that nobody had made: `predictions["inert"]` is the manual's rolled-forward
state, rendered -- and it is therefore *the anchor every hypothesis in the
frontier is a successor of*. `trace.before_hash` is the frame the world was
actually showing. They disagreed on **35 of the 52** completed probes, and
**all 35 of those landed off the frontier**. `inner/loop._roll_forward` replays
`step` from `initial_state()` over every recorded action, so one mispredicted
transition desynchronises the manual's state permanently and every probe after
it is an experiment about a frame the world left behind.

Of the 17 that *were* anchored, 12 still landed off-frontier, and every one of
those 12 missed by a delta containing **exactly one cell that had never changed
before in the run** -- 49 cells with 1 virgin on r3, 13 with 1 virgin on
`sk48-l1`, against 12 with 0 virgin on the 5 probes that landed on. A cell that
has never varied is board; the arm seats no object instance there; no
`forall ?p in <Type>` rule can name it.

**So the 47 decompose exactly: 35 state drift, 12 expressivity, 0 action
choice.** Generating near-miss *rules* -- from the DSL grammar, or from
`cegis_miner`'s version space -- would have recovered none of them. That is the
finding, and it is not the finding the ticket expected.

**What was built, and why it is not a contradiction.** One of the two causes is
reachable without touching the grammar, so `--frontier generated` (default
`ablation`, byte-identical) adds successor hypotheses anchored on the *world's*
last observed frame rather than on the manual's state. They are predictions,
not proposals for the manual, which is all a frontier has to be. Replayed
through the real builder against manuals recompiled from each leg's own
snapshots -- 52 of 52 reconstructed exactly -- ablation contains the world's
answer 5 times of 52 and generation 43.

**Three decisions inside that are worth the ink.**

1. `next_unnameable_cells` returns **every** leading-edge chain the evidence
   supports (one per colour, plus the colour-blind one), not the best. The
   draft that chose the longest chain recovered 32 of the 47; returning all of
   them recovers 38. Choosing is a point guess, and this whole change is an
   argument against point guesses.
2. A fifth generator, `action_replay`, was **built, measured and cut** -- 15
   hits of 52, and **0 marginal**: every one was an answer
   `world_anchored_manual` already had, and it recovers none of the 9 still
   missed. `replay_frontier.py --with-cut-generators` keeps the number
   checkable rather than remembered.
3. The drift is **diagnosed, not repaired**. Re-seating the manual's state on
   the world's frame is the actual fix, and it would make certify's replay
   trivially green -- destroying the only instrument that currently detects a
   wrong manual. That is somebody else's call, made deliberately, not skipped.


## D-R3-001 · `no THEORY block in the reply` named three events, and only one of them was the desk

R1b was read to establish which of four things happened to the goal rider, and
the reading turned up a fifth thing that was not being looked for.

`inner/theorize.py` writes one error for a reply it cannot use. It has written
it 32 times. Against the transcripts it separates into a provider refusal (24
-- `You've hit your session limit`, the desk never ran), an empty reply (1), and
**11 replies that were complete and arrived with their beginning missing**.
`harness/modelcall.py:561` keeps `envelope["result"]`, which is the CLI's last
assistant message; a reply spanning messages loses the earlier ones.
`R1b-sk48-b/desk/call-002` begins at `=== THEORY (continued -- the remainder of
theory.dsl, appended to the block above) ===` and `call-006` begins mid-word.

**The discriminator is structural and the arithmetic one was tried and
rejected.** Output tokens against reply characters is the obvious test; it does
not work, because `claude -p` bills thinking tokens that never reach `result`
and the ratio sits under 1.0 on 39 of 88 archived calls, most of which parsed
perfectly. What separates them exactly: all 53 accepted replies begin with the
marker, and none of the 35 rejected do. `tests/test_reply_loss.py` asserts both
halves and attaches the same useless ratio to a good reply and a bad one, so
the threshold is not reintroduced.

**Why the detector is in `armtools/` and the fix is not attempted.** Both
candidate repairs change what a live subprocess returns and neither can be
exercised offline. A change to the live path that no test can reach is worth
less than a measurement that runs on every suite.

## D-R3-002 · Booked is not posted, and `answered: null` was saying both

`GoalState` recorded when an ask was created and never when it went out, so
`"answered": null` covered an ask the desk refused to answer and an ask the
desk was never shown. R1b's two legs are one of each -- `g50t-a` delivered
three and was refused three, `sk48-b` booked one that never left the peg -- and
the round reported a single outcome for the pair.

`record_proposal` now writes `delivered_on_turn: null`; `mark_delivered` fills
it from `inner/loop.py` at the one place the rider is taken off the peg; and
`summary()` carries `proposals_delivered` and `proposals_answered` beside
`proposals_made`. `_reading` says which happened, in words, including the case
where nothing was delivered: *NOTHING HERE IS EVIDENCE ABOUT THE DESK: it was
not asked.*

The same pass fixed `refused_because`, which quoted each failed check verbatim
-- and every check is phrased as the condition that must HOLD, so R1b's records
give `enough new world has arrived to change the answer ... >= 4` as the reason
nothing happened. The substring is kept for callers that match on it and the
verdict is now negated in front of it, with the number it read.

## D-R3-003 · The rider engaged half the desk's argument, and the missing half was the whole case

The two manuals sign the goal's absence with good arguments, and the ticket
asked whether the rider engages them or talks past them. It does both, and the
split is clean.

**Engaged: soundness.** "It must be false in the states you have already seen
-- a goal satisfied by the current board stops the planner at the first node
and is worse than no goal at all." That is the manuals' own argument in their
own terms, and the desk quotes it back approvingly and uses it to reject
`count(Glyph9, color = 9) = 11`.

**Talked past: reach.** All three refusals are demonstrations that the section
*cannot say the thing*: `Cart.pos = <landmark>` and `count(<Type>, color = c) =
n`, `=` only, one equation, no conjunction, against a target whose cells are
board and carry no instance. Offered only "write one" or "argue why not", the
desk put its actual target in prose of its own naming --
`the_socket_is_a_keyhole_and_names_the_winning_position`, verified cell by cell
against the frame -- where nothing in the arm reads it. The most valuable claim
either manual made was written down and never picked up.

So a third channel, under a fixed prefix `the_goal_i_cannot_write_is` so it can
be found, asking for the target and for which forms were tried and what each
lacked. It is explicitly not a substitute for the second channel and does not
soften it; it buys no model call, riding the same already-paid-for turn.

**How a prompt change is judged with no live leg, since `Theoria.md:355` says
it is movable and does not say it is free.** Three things are settled offline:
the channel asks for a `theorem`, which is the DSL's own home for a belief that
is not an equation, so it cannot request a form the compiler refuses; its base
rate is measured rather than assumed, because the desk produced the artefact
unprompted on 2 of 2 legs that reached that point; and the reading half --
`goal_forensics.extract_target_theorems`, fixture-tested, correctly returning
`[]` on both R1b manuals -- improves the record whether or not the desk ever
adopts the prefix. What is **not** settled is whether the desk uses it, and
that needs one carried leg. It was not run.

---

## D-R3-001 · One state was doing two jobs; the repair gives the second job its own anchor and leaves the first alone

`inner/loop._roll_forward` answers "where would the manual be if it were
right?", and this arm spends that one answer on two jobs whose requirements are
opposed.

**Job A, audit.** `certify.cheap` replays the manual open-loop from
`initial_state()` over the whole recorded action sequence. It is a test of the
manual **because** it is allowed to drift; a replay re-seated on the world each
turn cannot diverge by more than one step, so it goes green on a manual that is
wrong everywhere. `Theoria.md` 1.3 makes this the detector of 写错的规则, and
`GAPS.md` GAP 3 records that both Lean routes are shut on a real ARC level --
so it is not one instrument among several, it is the only one.

**Job B, experiment design.** Every hypothesis in the probe frontier is a
successor of that same state, so it had better be the frame the world is
showing. R2 measured that it was not, on 35 of 52 completed probes, all 35 of
which landed off-frontier.

One variable, two jobs, and Job A wins silently. **The obvious repair --
re-seat the state on the world's observed frame each turn -- fixes Job B by
destroying Job A's instrument**, which is why R2 filed it rather than doing it.
It is also not available on its own terms: `render` is not injective (the
generated `State` is one `_pos`/`_color` pair per instance and many assignments
paint the same grid), so "the state the world is in" would have to be *guessed*
and the guess seated inside the manual's own state, where nothing downstream
could distinguish it from something the manual derived.

**What was decided.** Job B does not need a *state*; it needs the *frame its
successors succeed*. The world's own last observed frame is that frame exactly,
with nothing inferred. So `--anchor observed` keeps every hypothesis's
mechanism -- still the manual's `step` from the rolled-forward state -- and
moves only the frame the answer is read against:

    prediction = hash( world ⊕ ( render(h(state, a)) − render(state) ) )

Same ids, same order, same width. `certify` is untouched and
`tests/test_anchor.py::test_certify_never_reads_the_anchor` fails the day
anybody wires them together.

**Three alternatives, and why each traded one blindness for another.**

1. *Add world-anchored hypotheses beside the ablations* -- this is R2's shipped
   `--frontier generated`, and it works (43 of 52). But it delivers the
   anchoring as two extra hypotheses, widening the frontier from 2 distinct
   predictions to 5--10, which lowers the split entropy of every action and
   prices every probe higher. Measured here: the anchor switch **subsumes**
   both of them exactly -- `manual` anchored on the world is right on 25 probes
   and so is `world_anchored_manual`; `inert` anchored is right on 4 and so is
   `world_inert` -- and `observed × generated` reaches the same 43 at widths
   `[3, 6, 8]` rather than `[5, 6, 8, 10]`.
2. *Re-anchor for probe design only, discard the rolled state, log each
   re-anchor.* Rejected on a measurable ground, not a taste: a re-anchor event
   is a bit, and this run's finding is a magnitude. 20 of the 35 drifted probes
   were off by **one cell in 4096**; 8 were off by 23--25. "The anchor was
   wrong" cannot distinguish "the manual is nearly right and the frontier
   compares whole-frame hashes" from "the manual is lost". Keeping both states
   subsumes everything this records and adds the size -- and does not need the
   ill-posed inversion.
3. *Drift as an eighth surprise.* Rejected twice. `Theoria.md` 1.9 closes the
   taxonomy at seven and `inner/surprise.py` raises on an eighth by
   construction, so this is a design change and would have to be argued as one.
   It is also the wrong eighth on the merits: drift is not a new **kind** of
   evidence, it is the accumulated consequence of a `replay_mismatch` that has
   already fired and already paid for a desk call. A second surprise for the
   same defect double-counts against constraint 8's arithmetic, which
   `Register.audit` checks, and buys a paid call to hear the same news twice.
   Its home is a measurement attached to the surprise that already exists.

**Two corrections this turned up, both to sentences this arm had been
repeating.**

*The arm has been computing the drift all along.* `certify.cheap` writes
`entry["cells_wrong"]` per transition, and that series **is** the anchor's
drift -- same walk, same origin, same actions. `certify.json` archives the
summary line and the first divergence; `replay_steps`, where the counts live,
never reaches disk. `GAPS.md` R2-1 says a default leg cannot see its own drift;
in fact every leg has measured it every certify beat since P-8 and filed it as
an audit line nobody read as the error of the frame the probes were designed
against.

*"One mispredicted transition desynchronises the state permanently" is false.*
It is in R2's README and in this ticket's brief. The archive refutes it: drift
**recovers**, 8 recovery events across the 8 live legs, on 4 of the 6 that ever
drifted, with a non-monotone series on those 4 (`sk48-carried-l1` runs
`[96, 0, 0, 0, 0, 0, 1, 0, 1, …]`). The manual's `step` is not injective, so a
capped mover or a set-rather-than-toggled cell re-converges. The case for the
change survives intact -- what matters is whether the anchor was wrong *when a
probe was designed*, and it was, 35 times of 52 -- but the sentence would have
been repeated into the next round unchallenged.

**And R2's own harness was checked before its number was built on.** R2's
replay rolls the manual over `[s.action for s in prefix.steps]`, beginning with
`RESET`; `_roll_forward` rolls it over `store.actions`, that list shifted by
one. Different sequences; had they produced different states, R2's 35 would
have been an artefact of its own harness. Recomputed on every probe: equal on
52 of 52.

Full account and the four-cell table:
`runs/20260801T1200Z-R3-anchor-duality/`.
## D-A18-001 · The run scores itself, in production mode, and an unscoreable run says so

Phase 1 (5) asks for 逐局跑完即打分入库、与 scorecard 对账 and `Theoria.md:371`
for 跑完一局即打分. Half of it was true and had been for a while: the frozen
scorer works, and a monitor replay put 37 archived runs through it — 26 PASS,
0 FAIL, 11 with no surviving card, this arm's four live legs all PASS. The
other half had never happened. **No arm had ever called the scorer from a
run.** The only live run that went through `proxy/runner.py` crashed before
`run_end`, and every number anybody quoted came from a sweep afterwards — which
is precisely the reading `Theoria.md:371` forbids, because Phase 3 audits the
order results arrive in and a batch scored later is a batch somebody could have
scored after seeing it.

So `proxy.scoring.score_run` is called from `play()`'s `finally`, between
`run_end` and `run.json`. Three calls inside that, each of which could have
gone the other way:

**Production semantics, not audit semantics.** `write_incident` and
`write_artifact` are both left on. `proxy/DELIVERY_RULING.md` §5 is a warning
about the opposite mistake — running the *auditor* with incidents on twice put
six duplicate `score_mismatch` records into the shared ledger, and the flags
exist so that looking at a ledger does not modify it. A **run** with them off
is the more expensive error: the mismatch it found would be recorded nowhere,
and the run would be over by the time anyone noticed.
`tests/test_score_at_run_end.py` asserts the two arguments at the call itself
rather than grepping the source, because the spelling is not the property.

**The verdict is filed, never raised.** A scorer whose freeze no longer
verifies, a ledger that cannot be read, a scorecard that never arrived: each
lands as `UNDETERMINED` in `runs/<slug>/score.json` with the reason attached,
and the first two also file a `score_unreconciled` incident. `UNDETERMINED` is
not `PASS` — `baseline-arms` lost 22 of 23 scorecards to a transient 404 and
**the loss was silent**, so the reconciliation obligation was quietly not being
performed at all. A harness that let a scoring failure take down a run that had
already spent its actions would be the same defect wearing a louder coat.

**The score is not written into the ledger.** `LEDGER_FORMAT.md` §5 and D-004's
argument about dollars: a derived number in an append-only file is wrong the
day the rule that produced it changes and cannot be corrected. `score.json`
beside `run.json`, the scorer's fingerprint inside both, and the *failure* —
not the score — in the ledger as an `incident`.

One consequence worth stating because it looks like an omission: a run that is
not archive material keeps its copy out of `proxy/var/scores/`
(`_scores_dir_for`). The artefact is still written — that directory is the
index that accompanies the shared ledger, and a rehearsal's score beside the real
ones is indistinguishable from the score of a game that cost money. It is
`FIXTURE_RUNS_DIR`'s argument, one directory over.

## D-A18-002 · A live leg bills into the shared ledger; a rehearsal does not

`proxy/DELIVERY_RULING.md` §4 lists axis 1 — arms billing into the shared
ledger — as needing **configuration only** from this territory: `Run` and
`play()` have taken `ledger_path` since they were written, and `main()` never
forwarded it. So there was no way to invoke this arm that put its records in
`proxy/var/ledger.jsonl`, and axis 1's zero was a plumbing gap rather than a
finding. `main()` now forwards it, with `--ledger` to override.

The default is asymmetric on purpose: **the shared ledger for a live leg, the
run's own directory under `--mock`.** The symmetric choice — everything into
the shared file — is the tempting one and it is wrong for the reason
`DELIVERY_RULING.md` was written about, running in the other direction.
`tools/audit_delivery.py` counts axis 1 by `arm` alone (`REAL_ARMS`, incidents
filtered out) and counts liveness as a *separate* axis that it never sums with
it. A mock run writes `arm: theoria` records exactly like a live one, so
defaulting rehearsals into the shared file would make "this arm's records reach
the shared ledger" read as satisfied by a run that never left this machine —
one number that is nonzero for the wrong reason, which is the same failure as
the one number that was zero for two reasons.

Nothing is hidden by this: `run_start` records which ledger the run wrote to,
`run.json` carries its absolute path, and `--ledger` puts a rehearsal in the
shared file for anyone who actually wants that. What the default protects is
the reading of a census nobody has re-run yet.

This closes the configuration half only. Axis 2 — a run whose `run_start` names
a non-localhost upstream — costs money and is not this item's to authorise; the
first live leg after this lands is where "跑完即打分" produces its first live
evidence, and it will produce it without anyone remembering to ask.

## D-A27-001 · The arm was never blind to a win; it was blind to the price of one

The board item says "the arm cannot see a win even if it gets one". Read against
the code that is half right, and the half that is right is the expensive half.
Both halves are recorded here rather than the one that makes a better story.

**What the arm already read, before this ticket.** `inner/loop.py:_record`
passes `levels_completed` off *every* gameplay envelope into
`LevelLog.observe`, and an increase fires `_on_level_boundary` on that same
call, mid-leg, before `_record` returns. `_main_loop` reads `state == "WIN"` at
the top of every turn and drives `_try_advance_level`. Both of ARC's two
plausible level signals are handled and have been since `inner/levels.py` was
written; `LEVEL_SIGNAL_UNKNOWN` is a note about which one fires, not about
whether either is watched. Nothing in this ticket changes that path, and the
detector added here deliberately does **not** feed it — see the third decision
below.

**What the arm did not read, at any point in a leg.** `score`, `level_scores`,
`level_actions`, `level_count`, `level_baseline_actions`. Not one of these
appears on any ARC gameplay response — the key set is `action_input,
available_actions, frame, full_reset, game_id, guid, levels_completed, state,
win_levels`, and `_summary` states the consequence in a single line, `"score":
None`. All five exist only on a scorecard, and the only code path that fetched
one was `close_scorecard`, called from `_finish`, **after `_main_loop` has
returned**, on a card that D-015 records as unrecoverable once closed. Every
scorecard-side fact about a leg therefore arrived strictly after the leg could
use it.

**The number that makes this matter.** The closed g50t card in
`runs/20260728T012311Z-g50t-first-contact-salvage2/ledger.jsonl` carries
`level_baseline_actions: [78, 175, 179, 230, 96, 54, 67]`. Level 1 costs a
reference solver 78 actions; the best leg this arm has ever run spent 33 in
total, and a $25 leg buys about 32. That ratio was legible from the first RESET
onward, in a document the arm could have asked for at any moment without
spending an action, and the arm asked for it once — at the end, where it is a
post-mortem. The blindness is real and it is narrower and worse than the board
item's wording: not "a win would go unnoticed", but "the leg never knew what a
win costs".

Four decisions, each of which could have gone another way.

**1. `GET /api/scorecard/{card_id}`, not an earlier close.** The obvious way to
see a score mid-leg is to close the card and open another. That is wrong twice:
D-015 makes a close irreversible, and `Theoria.md` Phase 2 layer 4 fixes 一局一张
scorecard — a leg that closes three cards has three partial scores and no
scorecard to reconcile against, which breaks the 对账义务 in the same paragraph
that asks for it. The GET has been in `arc-recon/client.py` the whole time,
under a heading that reads "read-only surface (costs no action quota)". It is
non-destructive, it does not consume the action budget, and it returns the same
document. `Budget.check_readonly` is a separate method rather than
`check(is_reset=True)` so that `resets` stays a count of RESETs, and
`budget.reads` is reported separately as well as inside `commands_sent` so a leg
whose command count is lifted by scoreboard reads cannot be mistaken for a leg
whose retry envelope ran away.

**2. One attempt, and the read may never end a leg.** Every other endpoint in
`harness/arc.py` retries into the 400 wave with a 40-attempt envelope, because
losing a command loses an action. Losing a reading loses nothing: the next turn
asks again. Retrying would spend up to 40 requests to learn a number that has
not moved in 2,700 recorded steps. And `read_scorecard` swallows every failure
and returns `None` — an instrument that can kill a run is a liability, not an
instrument. The single exception is the spend gate, which is asked *first*: a
read must not be the thing that spins against a red gate.

**3. The watch is a witness, not a trigger.** `ScoreWatch` never calls
`_on_level_boundary`. `LevelLog` remains the sole authority over `starts`,
snapshots and the dropped problem. The alternative — letting a score jump cut
the trajectory — would mean a scorecard glitch, a mis-selected run row, or a
resumed card could manufacture a level completion in the arm's own record, and
`_try_advance_level` already says at length why a fabricated boundary is the
worst outcome available here, worse than stopping. What the watch does when the
two witnesses disagree is **report it** (`corroborate`) and pick neither.

**4. The default rung is `envelope`, not `off`.** `inner/goal.py` defaults to
`off` so a run's artefacts stay byte-identical, and that discipline is right for
a change that spends. It is the wrong default here for the free rung, and D-A3-B
is the evidence: change B has been prepared-and-not-adopted since 2026-07-31 and
has never run, which is GAP A3-B-1. The `envelope` rung opens no socket, spends
no action, buys no model call and reads only fields already sitting on every
recorded `Step`; the only thing it changes is that the record now says what it
saw. A27's whole finding is that the record was silent. `off` is kept and does
restore byte-identical artefacts; the paid rung, `scorecard`, defaults off,
because spending against the shared pool is not a decision this file gets to
make on its own.

**What is deliberately not built.** The path from "a boundary was observed" to
"the manual may now state a goal" is designed and half-built.
`witness_from_boundary` and the `witnessed_wins.json` artefact are the
observation half and they are complete: at a boundary the arm now keeps the last
frame of the level it cleared, its hash, the level's opening hash, the action
that carried the signal, the actions the level cost it, and the reach reading
that stood at that moment. That frame is the evidence R1b measured the desk
waiting for — three refusals in three asks, each resting on the fact that no
winning state had ever been seen. `witness_rider` renders it as a prompt block
and is a pure function that costs nothing.

Wiring that rider onto a theorize call is **not** done, and the seam is drawn
where the evidence stops. A rider must ride on a call some surprise has already
bought (`inner/surprise.py` closes the set at seven; an eighth is a change to
`Theoria.md` 1.10(d), not to a file). The call it should ride on is the one a
boundary itself provokes — and since no live leg has ever crossed a boundary,
the shape of that call has never been observed. Every claim about which turn it
lands on, and about what the desk does with a positive example, would be a guess
dressed as a design. The first recorded boundary is the evidence that decision
needs. Until then the arm keeps the frame, which is the part that cannot be
recovered afterwards.

**Absence is absence.** `boundary_verdict` returns `not_measured` /
`boundary_observed: null` when fewer than two readings have been taken, and
`measured_absent` / `false` when readings were taken and nothing moved. Every
live leg in this repository's history is in the first category, and reporting it
as the second would turn "we did not look" into "we looked and there was
nothing". `tests/test_scoreboard.py` is mostly about that distinction, and
`test_no_recorded_leg_contains_a_real_boundary` states the caveat as a test so
that it fails on the day it stops being true.

## D-A34-001 · The win was the one completion `levels.jsonl` was coded never to record

`inner/levels.LevelLog.observe` returns `None` when the counter reaches the
game's last level, and the reason it gives is sound: the caller's boundary
handling drops `problem.json` and wipes `generated/`, so firing it on a winning
run would delete exactly the artefacts that say how it was won, and `starts`
would be cut into a level that does not exist. `test_winning_the_last_level_
does_not_open_an_eighth` has pinned that since A3 and it still does.

What that argument covered is the **handling**. What it was silently extended to
is the **record**, which it never covered — and the record was the whole point
of the file. Measured on a synthetic three-level win (A34,
`runs/20260804T131652Z-A34-levels-recording-path/MEASUREMENT.json`):
`levels.jsonl` two rows, `inner/scoreboard.ScoreWatch` three `level_boundary`
events and a verdict of `observed`, `witnessed_wins.json` two witnesses. The row
that was missing was the win. Scaled to g50t, a seven-level win writes six rows
and leaves the seventh off disk while the second instrument records all seven.

Two instruments, one event, silently different answers, on the single run this
project exists to produce. A27's `corroborate()` cannot catch it: it compares the
envelope counter against a *scorecard* reading and never compares its own event
list against `LevelLog`'s.

So the two halves are separated rather than the suppression removed.
`LevelLog.finals` holds the winning increment as a `game_won` event and
`records()` — not `events` — is what `levels.jsonl` is written from;
`observe` still returns `None`, which is still what tells `_record` to keep its
hands off the trajectory. `loop._on_game_won` is the non-destructive half of the
boundary handler and nothing else: snapshot the books that won, witness the
winning frame, append a turn row. `problem.json` and `generated/` stay.

`finals` is a second list and not an entry in `events` because `events` and
`starts` are one structure written down twice — `starts[i+1]` is where the
trajectory after `events[i]` begins, and every reader that segments a run relies
on the pairing. A win appends to neither. Putting it in `events` would break
every one of those readers at once, on the one run where getting the record right
matters most.

`_witness_the_win` gains `segmenting` for the same reason the event is separate.
At a boundary the step carrying the increment is the *first* frame of the next
level, so the cleared level's last frame is the step before it and its opening is
`starts[-2]`. At a win there is no next level: that step **is** the final frame,
and the opening is `starts[-1]`. Reading a win with the boundary's arithmetic
returns the second-to-last frame of a won game and the opening board of the wrong
level — worse than no witness, because it looks like one.

## D-A34-002 · A lost completion record is not a completion of zero, and `or 0` said it was

`armtools/round.py` totalled a round with `sum((l.get("levels_completed") or 0)
for l in legs)`. That one character makes three different facts the same integer:
*completed none*, *never looked*, and *completed one and lost the record*. A34's
negative control is the third, built deliberately — a mock leg that genuinely
crosses a boundary, with its `levels.jsonl` truncated to zero bytes, which is the
exact byte state of all twenty-two archived files. Under the old rule it
contributed what a leg that completed nothing contributed, and while that holds,
"nothing has ever completed a level" is a sentence no measurement can refute.

`armtools/level_evidence.py` is the readback, and its whole design is that
`levels_completed` is `None` in three of its five verdicts. `observed` carries a
number; `measured_absent` — the counter was read on every envelope and never rose
— is the **only** verdict under which a zero is honest; `unmeasured`,
`evidence_missing` and `no_run` carry `None`. `total()` sums the legs that
reported and names the ones that did not, rather than adding their absences to
the numerator's denominator.

Note what `evidence_missing` does **not** do: it does not fall back on the
counter in `RUN_STATE.json` and publish that number instead. A completion whose
event record is not on disk cannot be audited, and a figure no artefact supports
is worse than a gap that is named.
