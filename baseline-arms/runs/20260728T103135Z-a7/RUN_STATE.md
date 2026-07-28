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

*(filled in as the campaign advances)*

---

## Stop conditions and what actually happened

*(filled in at the end)*
