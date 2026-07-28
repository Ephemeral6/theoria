# A7 — finishing the variance envelope

Worker `APP-A7` · ticket `A7-envelope-finish` · territory `baseline-arms`
branch `agent/a7-envelope-finish` · base `979e0bc`

The narrative. `MANIFEST.json` is the provenance record and is canonical;
this file is what a person needs in order to read it.

---

## What this run was for

The variance envelope stopped at **1/4 games** (ar25 × haiku × 3, $2.5275),
tripped by G4 and ruled in `BUDGET_REPORT.md` §11 to be a real degradation
under `INCIDENTS.md` INC-BA-003's concurrent-campaign load. §11.5 named two
things that had to be fixed before a re-run. The ticket for this run says the
first is now landed (`proxy/spend_gate.py`) and asks for the remaining three
games — g50t, sk48, tn36 — at three repeats each, followed by the envelope
table and the variance estimate Phase 4 needs to fix its per-cell repeat
count ⟨n⟩.

---

## What had to be built before a single cell could run

Three findings, in the order they were found. Each is a decision record.

### 1. The shared gate was not on this track's spending path at all (D-017)

`proxy/spend_gate.py` had landed, and it is the right instrument — one pool,
one lock, one sum, fail-closed, visible across sessions. But it hangs off **the
proxy's egress path**, and `baseline-arms` uses neither half of it: `bare_cc`
drives `arc_client` straight at `three.arcprize.org`, and the model side is a
`claude -p` subprocess. The pool's own report showed this plainly and nobody
had read it that way:

```
by campaign:
  arc-recon-canary-quick      $0.0000    0 actions
  theoria:r-395ddce163d04d83  $0.0000    7 actions
  ...
```

Every campaign `baseline-arms` had ever run — including the $2.5275 envelope
this ticket is finishing, and the $103 S1 campaign of INC-BA-003 — appears
nowhere. **That is not a small number; it is no number.** The ticket's "every
egress must pass reserve/record" was therefore not a matter of remembering to
call it: there was nothing to call.

So `harness/spend.py` plugs both axes in, and both refusals are functions
rather than paragraphs: `ArcClient.request()` will not open a socket without a
claim, `bare_cc.play()` will not start without one. Charging is per **request**,
not per successful action, so D-005's 5–11× retry amplification is visible to
the pool instead of hidden behind it; and failed requests are charged, because
a 400 crossed the wire and counted against the rate limit.

One reservation **per cell**, not per campaign: the three repeats run
concurrently, and a shared claim would give three threads one set of counters
and leave no cell able to say what it had spent — INC-BA-003's third damage,
one level down.

### 2. The abort rule was not measuring what it claimed (D-016)

`BUDGET_REPORT.md` §11.2 had already done the diagnosis; this run acted on it.
`actions_failed >= 10`, cumulative and absolute, killed all three ar25 cells
with **exactly ten failures each, standard deviation zero**. At a 30-action
budget and ~0.6 action success rate, that verdict was guaranteed by
construction. §7 of the same document had described the rule as "ten
*consecutive* failures" — wrong about the code, and right about what the rule
should be.

Now two rules with two outcome names:

| rule | threshold | outcome | the claim it makes |
|---|---|---|---|
| consecutive | 10 | `api_unusable` | the API is unusable |
| cumulative | `max(10, budget)` | `failure_grind` | this arm fails a lot |

**§11.3 forbids exactly one move here** — raising a threshold so the gate goes
green — and the test it set is whether a real signal is silenced. Point by
point: the degradation those cells genuinely measured (success 0.595,
http/action 9.66, $/action +68%) is measured by **G5, G3 and G2**, and all
three are untouched and still armed. What was removed is an absolute constant
that did not scale with the quantity it judged. What was **added** is a
constraint that did not previously exist — a cumulative counter is never reset
by a success, so nothing had ever been watching whether failures came in a run.
`failure_grind` is deliberately not a dead outcome: a cell that spends its
budget and fails a lot is a *result*, and filing it as an API fault would put a
measurement into G4's streak and stop the campaign for having measured
something.

### 3. A gate that can only stop once cannot be re-adjudicated (D-018)

G4 was still red, and would have stayed red for ever: the gate had no way to
record that an adjudication had happened, so §11.5's "re-runs just append and
`--gate-only` can re-adjudicate at any time" was not reachable.
`out/campaign_barriers.jsonl` is that record. **BAR-001** adjudicates the three
ar25 cells and names its three remediations.

The scope rule is stated once rather than discovered one gate at a time. The
eight thresholds are two kinds:

* **condition clocks** — G4 (consecutive dead cells) and G6a (real time since
  the first cell started). Both claim something about *now*. A barrier restarts
  both, because a campaign that ran 24 minutes, stopped on a correct refusal,
  was diagnosed, and resumed sixteen hours later has neither a live failure
  streak nor a day of running behind it; it has a **gap**, and counting the gap
  is the same unit error that split G6 into two clocks in the first place.
* **cumulative sums** — G1, G1b, G2, G3, G5, G6b, G7. Every one keeps summing
  every cell ever recorded. The $2.5275 is not forgiven and never will be.

The load-bearing test is the negative one: `test_a_barrier_moves_g4_and_nothing_else`
asserts the dollar total is **unchanged** across the barrier. A test that only
checked "the gate goes green" would pass for the forbidden change too.

**BAR-001 explicitly does not**: re-run the ar25 cells, delete them,
reclassify them, or move any threshold in order to make them pass. Their
`degraded` standing is unchanged and they are excluded from the envelope by
name, with the reason printed next to the table.

### One incidental fix

`load_api_key()` looked for `.env` only in the importing checkout, while
CLAUDE.md instructs every agent to work in `.worktrees/<id>/` — where the file
does not exist, because it is gitignored and does not travel with a branch. A
worktree now falls back to the main checkout, the same resolution
`spend_gate.py` already uses for the pool ledger. The key is still read only
from a gitignored file and is still not copied anywhere.

---

## The smoke test, and what it found

$0.05 of insurance before twelve cells went through new wiring
(`smoke.py`, one action on g50t). It verified the gate end to end — the pool
went 48 → 51 actions, with a ledger line per request carrying path, status and
reservation id — and it **failed its own final assertion**, correctly:

```
"error": "You've hit your session limit · resets 8:20pm (Asia/Shanghai)"
"outcome": "model_error",  "model_calls": 3,  "cost_usd": 0.0
```

Two things came out of that:

1. **The assertion was wrong, not the code.** It demanded `after.usd >
   before.usd`. All three model retries were refused and billed nothing, and a
   refused call that cost nothing is a *priced* call worth zero — which is what
   the gate recorded, exactly as `spend_gate`'s own docstring says it should
   ("a model legitimately priced at $0.00 with a complete usage block is
   priced, not blind"). The assertion now checks that the pool and the episode
   *agree*, and that no call went unpriced.
2. **The arm's model side was unavailable.** Not a budget gate and not an API
   fault: the 5-hour session window, which `SPEND_GATE.md` §5 lists explicitly
   as a resource the shared pool does not watch. Nothing could be measured
   until it reset, so `await_quota.py` waited for it — itself gated, because a
   probe is a real `claude -p` call and this ticket's rule has no exceptions.

---

## Cells

Nine, all three games, three repeats each. Budget 30 actions, haiku-4.5,
cookie jar on. Every cell audited before the next game started.

| game | rep | outcome | ok | fail | longest run | http/a | $ | wall s |
|---|---|---|---|---|---|---|---|---|
| g50t | 1 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.1468 | 1038 |
| g50t | 2 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.0675 | 848 |
| g50t | 3 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.1277 | 991 |
| sk48 | 1 | budget_exhausted | 26 | 4 | 2 | 2.50 | 1.3138 | 1412 |
| sk48 | 2 | budget_exhausted | 28 | 2 | 1 | 1.61 | 1.3441 | 1396 |
| sk48 | 3 | budget_exhausted | 27 | 3 | 2 | 1.93 | 1.3897 | 1513 |
| tn36 | 1 | gave_up | 23 | 5 | 2 | 3.35 | 1.0127 | 1001 |
| tn36 | 2 | gave_up | 24 | 5 | 2 | 2.96 | 1.0948 | 1109 |
| tn36 | 3 | budget_exhausted | 24 | 6 | 2 | 3.21 | 1.0393 | 1026 |

**Nine live cells, zero dead.** `levels_completed` is 0 in all nine, as it was
in all twelve pilot cells — 30 actions is not enough to finish a level in any
of these games, and that fact is the single most important thing in this report
(see ⟨n⟩ below).

Totals for this run: **$10.5364 · 242 ok / 25 failed · 477 gameplay HTTP ·
2.87 compute-hours · 504 pool actions.**

### The audits

Two per game, both required to pass before the next game started, plus one
independent adversarial review of g50t.

* `audit_cells` — cell summary vs harness ledger vs API scorecard, plus a
  sealed-pile sweep over every record. **9/9 clean**, sealed check PASS across
  1111 records. All nine scorecards reconcile as *successful actions only*,
  which raises BUDGET_REPORT §4.1's sample for that finding from 4 to 13.
* `audit_pool` — the new one (D-017 created the obligation). **9/9 clean.**
  The pool's $10.5364 equals the cells' $10.5364 exactly, and the action
  identity closes on every cell.

Both audits found real defects, which is the only reason to run them:

1. **`audit_pool --game` filtered the record, not the view.** Auditing sk48
   reported g50t's three reservations as ORPHAN — "unattributable spend", the
   most serious verdict the tool has — because `--game` had removed their cells
   from the comparison. Attribution is a property of the whole campaign or it is
   nothing. `--game` is now a focus on what is printed; the count of what was
   hidden travels with the verdict.
2. **`audit_cells` read a model's decision as a server's refusal.** The two
   `gave_up` tn36 cells reported "actions_failed: summary 5, ledger 6". The
   summary was right. A GIVE UP is written `failed=True` with a null frame
   because it produced no frame (D-006) — but it never reached the server, so it
   is not what `actions_failed` counts and it says nothing about the API. Same
   distinction D-016 drew between `api_unusable` and `failure_grind`, one level
   down. Fixed at read time (the ledger is append-only and the evidence — an
   absent `http_status` — was already in the record), and new records now state
   `reached_api` outright so no future reader has to infer it.
3. **The adversarial review of g50t found D-019**, below, which is the largest
   finding of the run.

---

## The result: within-cell spread is small, and between-game spread is not

Pooled within-cell coefficient of variation, 3 games × 3 repeats, 6 df:

| metric | CV | n for ±10% CI | n for ±20% CI | n to detect 25% | n to detect 50% |
|---|---|---|---|---|---|
| action_success_rate | 0.018 | 3 | 2 | 3 | 3 |
| actions_ok | 0.021 | 3 | 2 | 3 | 3 |
| usd_per_action | 0.033 | 3 | 3 | 3 | 3 |
| cost_usd | 0.035 | 3 | 3 | 3 | 3 |
| wall_seconds | 0.067 | 5 | 3 | 4 | 3 |
| http_per_action | 0.096 | 7 | 4 | 5 | 3 |
| **levels_completed** | **—** | **—** | **—** | **—** | **—** |

**⟨n⟩ = 3 for the economic metrics, 5–7 if `http_per_action` has to be pinned
down.** The two-sample columns are the ones Phase 4 actually needs — the
envelope is not bought so a bare-CC mean can be quoted, but so a bare-CC cell
and a Theoria cell can be told apart — and they say **n = 3 per arm** detects a
25% difference in cost or success rate at 80% power.

Three things that must travel with that number or it will be misused:

1. **`levels_completed` has no CV, and that is not a formality.** It is
   identically zero in all nine cells and was zero in all twelve pilot cells. It
   is the metric Phase 4 would most want to compare, and at a 30-action budget
   **no repeat count whatsoever makes it comparable** — n does not fix a metric
   with no signal. If Phase 4 intends to compare capability rather than
   economics, it needs a larger action budget first, and this envelope says
   nothing about the variance it would then have.
2. **Between-game spread dwarfs within-cell spread.** actions_ok runs 30 / 27 /
   23.7 across the three games and http_per_action runs 1.00 / 2.01 / 3.17 —
   between-game ratios of 3× against within-cell CVs under 0.10. Repeats are
   cheap insurance; **game coverage is where the uncertainty actually lives.**
   Three repeats on four games is a better buy than nine on two.
3. **Six degrees of freedom.** A CV from three samples is a noisy estimate of a
   CV, and these are pooled from three of them. The n values are the right order
   of magnitude, not three significant figures.

---

## Stop conditions and what actually happened

**Nothing tripped. The campaign ran to completion and stopped because it was
finished.**

| gate | limit | final | |
|---|---|---|---|
| G1 campaign cost | $50.00 | **$13.0639** | 26% |
| G1b haiku tier | $20.00 | $13.0639 | 65% |
| G2 cell cost | $3.078 | max $1.3897 | 45% |
| G3 http/action | 20.0 | 3.15 | |
| G4 consecutive dead | 2 | **0** | nine live cells |
| G5 action success | ≥ 0.35 | 0.839 | |
| G6a elapsed | 8 h | 1.2 h | |
| G6b compute | 20 h | 3.8 h | |
| G7 sealed contact | any | **none** | 1111 records swept |

Shared pool after the run: **$10.5564 of $214.90, 587 of 24,000 actions**, no
live reservations. The theoria arm was drawing on the same pool throughout and
is visible in the same report — which is the whole of what INC-BA-003 could not
do.

The one thing that did stop this run was not a gate: the `claude -p` **session
window**, which cost 105 minutes between the smoke test and the first cell. It
is not in the pool and cannot be, and `SPEND_GATE.md` §5 already says so. If a
future campaign is scheduled rather than run by hand, that window is the
constraint to schedule around.

---

## D-019 — the finding that changes numbers outside this run

The adversarial review was asked to falsify "30 successful actions, 0 failed",
a result too good against ar25's 0.595. It found no mechanism for silently
dropping failures — `resilient()`, the action loop and `request()` all account
honestly, and 99 of 99 g50t HTTP calls really did return 200. It found the
cause instead:

| transport | calls | 200 | 400 | 404 | 500 | error |
|---|---|---|---|---|---|---|
| jar **off** — M4 pilot + ar25, all history | 1922 | 249 | 1315 | 147 | 208 | 3 |
| jar **on** — this campaign | 99 (g50t) | 99 | 0 | 0 | 0 | 0 |

`arc_client.py` stated that `cookies=False` was kept precisely so
BUDGET_REPORT's figures would stay re-derivable. The constructor had defaulted
to `cookies=True` since the jar landed six hours before these cells ran, and no
caller but `transport_ab` overrode it. **The campaign changed transport
mid-flight and the docstring asserted it had not.** Nothing in the harness
would have caught this; only an audit told to disbelieve a good result did.

Consequences, kept apart rather than blended:

* **ar25 vs the rest is separated by two variables, not one** — contention *and*
  transport. They are not separable. This strengthens the exclusion of ar25
  rather than weakening it.
* **The envelope is unaffected.** All nine cells share the jar, and the question
  is within-cell spread.
* **BUDGET_REPORT §2.1 and every extrapolation on it are stale.**
  `http_per_action` is 1.00–3.17 on the jar, against a pilot figure of 7.11. The
  §3 HTTP and action-quota numbers (87k–175k requests) are high by roughly 2–7×.
  Dollars do not move with it — model pricing is transport-independent. Logged
  here; re-deriving §3 is not this ticket's call.
