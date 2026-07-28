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

## D-A3-003 · Surprises pending at a boundary are retired, not carried

`Register.retire_pending` marks them `handled_by = "retired: <reason>"`. They
were fired against a trajectory the arm can no longer show, and carrying them
would spend a model call adjudicating evidence that no longer exists. Retiring
is not deleting: the items stay in the register, so `counts()` is unchanged, all
seven kinds still report (a zero is a measurement), and the constraint-8 audit
still adds up. What changes is only who closed them — which is itself a datum,
since "how many surprises died at a boundary rather than being theorized" is a
number the bill-shape figure can use.
