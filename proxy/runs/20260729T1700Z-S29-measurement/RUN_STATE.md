# S29 — "not measured" and "measured, and it was zero" were the same literal

RES-4, 2026-07-29, branch `agent/s29-measurement-missing`, base `7852ef30`.
Zero API calls, $0.00, zero sealed-pile contact — everything offline.

## Defect 1 — a call nobody measured came back as a well-formed $0.00

`PriceTable.cost` had a refusal branch and used it for exactly one reason: an
unknown **model**. A known model with a *missing measurement* walked straight
through the fully-priced path, because every line was read as
`int(usage.get(key) or 0)` — and `or 0` turns "the provider did not send this"
into "the provider sent zero". `price_run` then added $0.00, incremented
`calls`, and reported `unpriced_models: null`, which is a positive assertion
that nothing was missed.

Fixed by making the two halves of every bill a precondition:
`REQUIRED_USAGE_KEYS = ("input_tokens", "output_tokens")`. Absent, or present as
`None`, and `cost()` returns `usd: None` with `missing_usage_keys` — the same
refusal the unknown-model branch already returned, for the same reason.

Three deliberate calls inside that:

* **`None` counts as missing, not as zero.** That is one notch stricter than the
  `key in usage` test `proxy/model_proxy.py` applies at its own call site. A
  provider that serialises `"output_tokens": null` has told us it did not
  measure, and `int(None or 0)` read that as a measurement of zero.
* **`int()` runs before the absence check, and the order is load-bearing.** A
  usage value `json.loads` accepts and `int()` does not (`1e999`, `"1e5"`) is a
  loud failure and has to stay one — five real calls once produced no ledger row
  at all when that raise was swallowed. Testing absence first would demote it to
  a quiet `usd: None` and throw away the difference between *the provider sent
  nonsense* and *the provider sent nothing*.
* **A measured zero is still a price.** `{"input_tokens": 0, "output_tokens": 0}`
  returns `usd: 0.0`, not `None`. The whole point is that the two are different.

`proxy/model_proxy.py` had enforced this at its own call site since the
SSE-truncation finding (`input_tokens` arrives in `message_start`,
`output_tokens` only in `message_delta`). It enforced it *there* and not in the
conversion, so every other reader — `price_run`, `proxy/reconcile.py`,
`theoria-arm/armtools/archive.py` and the figures downstream of them — re-priced
history without it. The rule belongs to the conversion, not to one caller.

`proxy/reconcile.py` is changed as a consequence, not as scope creep. Both holes
reach the same `priced["usd"] is None` branch, and only one is about the model.
Filing an unmeasured call under `unpriced` would print *"model 'claude-opus-5'
is not in the table they name"* about a model that is right there in
`pricing_v1.json` — a true finding under a false heading, which is how a
reconciliation report gets ignored. Unmeasured calls now get their own
`unmeasured_calls` count and their own sentence in `not_derivable`.

### Measured, before and after

`proxy/tests/test_cost.py` cannot be its own fail-before evidence: it imports
`REQUIRED_USAGE_KEYS`, which does not exist on master, so against master code it
raises `ImportError` at collection. That is a failure *caused by* the change
that never reaches the claim the tests are about — the same trap recorded below
for the two crash tests. So `defect1_before_after.py` in this directory asks
`PriceTable.cost` the questions directly. Both outputs are archived
(`defect1.before.txt`, `defect1.after.txt`):

| usage block | master | branch |
|---|---|---|
| `{}` — never measured | **`usd=0.0`** | `usd=None`, `missing_usage_keys=['input_tokens','output_tokens']` |
| `{"input_tokens": 1000}` — truncated stream | **`usd=0.005`** | `usd=None`, `missing_usage_keys=['output_tokens']` |
| `{"input_tokens": 1000, "output_tokens": null}` | **`usd=0.005`** | `usd=None`, `missing_usage_keys=['output_tokens']` |
| `{"input_tokens": 0, "output_tokens": 0}` — measured zero | `usd=0.0` | `usd=0.0` (unchanged, by design) |
| `{"input_tokens": 1000, "output_tokens": 5000}` — control | `usd=0.13` | `usd=0.13` (unchanged) |

The second row is the one worth staring at. The same call, fully measured, costs
**$0.13**. Master reported **$0.005** for it — not a refusal, not a warning, a
confident number **26× under** the real bill, because output tokens on every
model in `pricing_v1.json` are billed at five times the input rate and the
truncated block dropped the whole output side. A partial measurement was worse
than no measurement: `{}` at least came back as a suspicious round zero.

`python -m pytest proxy/tests/test_cost.py -q` → **12 passed** on the branch.

## Defect 2 — a ceiling no comparison could reach

`proxy/spend_gate.py` has had a `finite()` since it was written, and its
docstring already explains this exact failure: NaN is not `< 0`, so every later
`>` against it is False and the ceiling is silently void; `json.dumps` writes
`NaN` and `json.loads` reads it back, into an append-only ledger.

It was applied to every amount a *caller* passes in, and to none of the policy's
own fields. `SpendPolicy.__init__` did `float(spec["usd_ceiling"])` and then
checked `usd_ceiling <= 0` — which is False for NaN and False for `+inf`. So a
policy with a non-finite ceiling loaded cleanly, and `check`, `reserve` and
`_first_breach` then compared against it forever without tripping.
`proxy/verify_spend.sh:83-94` — the dedicated "the shared pool policy is
readable and has a ceiling" check — would print `inf` and exit 0.

Fixed by using `finite()` at the two money fields. `SpendGateError` joins the
constructor's `except` tuple so the refusal still surfaces as
`SpendGateUnavailable`; callers catch that, and a gate that cannot load must
fail closed as unavailable rather than as a bare `RuntimeError`.

**Found while fixing it, beyond the item's letter:** `default_run_caps["usd"]`
is the same hole by a second route. Its guard is `< 0`, which NaN also passes,
and it is the cap given to a run that declares no budget of its own — so
"no declared budget" could resolve to "unlimited" past the message that already
exists to prevent exactly that. Fixed in the same edit.

`action_ceiling` is deliberately untouched: `int()` raises on NaN first, which
is a loud failure. The board item flagged that half of the original report as
wrong, and it is.

Note the shell check needed no change and is now load-bearing: its claim
("has a ceiling") became true because the constructor enforces it, not because
the script started checking more.

## Defect 3 — the crash cleanup released other sessions' claims

`proxy/runner.py`'s `run_game` wraps `_run_game` in a `finally` that returns
headroom a crashed run never released. It compared the live reservation set
against a snapshot and released everything new, narrowed — supposedly — by:

```python
if entry["holder"].get("run_id") != kwargs.get("run_id") \
        and kwargs.get("run_id") is not None:
    continue
```

`run_id` was minted **inside** `_run_game` (`run_id = run_id or new_run_id()`),
so an ordinary caller never passed one, `kwargs.get("run_id")` was always None,
the second conjunct was always False, and the `continue` never fired. A crash
released **every** reservation that appeared in the shared pool while the run
was alive, including other sessions'. `SpendGate.release` validated nothing —
it appended a release record for any id at all — and the line it left behind
read `run ended without releasing its claim`, which is exactly what the cleanup
was written to do. Nothing about it looks wrong in the ledger.

**Deleting the dead conjunct alone inverts the bug.** With `kwargs["run_id"]`
still None, every entry's holder would mismatch, every iteration would
`continue`, and the cleanup would release nothing — back to the 43 stranded
pools this code was written for. Both halves are needed, so the run id is now
minted in `run_game`, one level up, and passed down. `_run_game` still does
`run_id or new_run_id()`, and `run_id` is keyword-only, so nothing else changes.

`SpendGate.release` gained the ownership check it never had:

* a reservation id that is not in the pool ledger now **raises** instead of
  appending a record that reads like a successful release;
* an optional `expect_holder` states whose claim the caller believes this is,
  and the gate refuses if it disagrees. Opt-in rather than always-on, because a
  supervisor clearing a reservation stranded by a dead process is a legitimate
  caller that does not hold the run; what must not happen is a caller that
  *thinks* it is releasing its own silently releasing someone else's.

The runner passes `expect_holder={"run_id": run_id}` — belt and braces, since
this filter has already been silently wrong once and the cost of being wrong is
another session losing its headroom.

## The test that was vacuous twice, and pointed green both times

`proxy/tests/test_spend_gate_egress.py::test_a_crashed_run_does_not_strand_the_pools_headroom`
monkeypatched `_run_game` to raise **immediately**, so no reservation was ever
taken. `assert gate.totals().held_usd == 0.0` was true before the cleanup code
existed and stayed true regardless of what it did — a test for "the crash
cleanup gives the headroom back" that never put any headroom out. It also passed
`run_id="r-crash"`, which no real caller passes: the single input that decided
whether the ownership filter ran at all was supplied only by the test.

Rewritten so the fake does what the real `_run_game` does before it dies —
reserve, with the same `holder` shape — and called without `run_id=`, which is
the shape a real caller uses and the shape the old filter could not see.

## Negative samples: measured fail-before / pass-after

Run against clean `origin/master` in a throwaway checkout with only the test
file copied in, then against the branch:

| test | on master | on branch |
|---|---|---|
| `test_crash_cleanup_releases_only_the_crashing_runs_own_claim` | **FAIL** | pass |
| `test_release_refuses_a_claim_the_caller_does_not_hold` | **FAIL** | pass |
| `test_a_policy_with_a_non_finite_ceiling_refuses_to_load` | **FAIL** | pass |
| `test_a_crashed_run_does_not_strand_the_pools_headroom` | pass | pass |

The ownership failure on master is the whole defect in one line:

```
E  AssertionError: the crashing run released a claim it did not hold
E  assert 'res-10ba21b04a3241d6' in {}
```

The live set is **empty** — the crashing run released both its own claim and the
other session's.

The last row is honest bookkeeping: releasing *its own* claim always worked, so
that test is a regression guard, not a negative sample. It is listed because a
rewritten test that passes both before and after is exactly the kind of thing
that gets quietly counted as evidence, and it is not.

An earlier draft of the two crash tests wrote `k["run_id"]`, and both failed on
master with `KeyError: 'run_id'` — a failure caused by the defect but never
reaching the claim the test is about. Changed to `k.get("run_id") or ...` so the
fake stands in for the level that used to mint the id, and the assertion that
fires is the one about ownership.

## The theoria-arm gate this turns red, and why it is NOT a repricing

`theoria-arm/tests/test_arm.py::test_the_archive_stays_accountable` fails on this
branch and passes with the four `proxy/*.py` changes stashed. It was put to an
independent adjudicator with two hypotheses — *legitimate red, the archive really
was priced from unmeasured usage* versus *over-strict, my rule misfires on a
shape that is legitimately complete*. **Neither is right, and the answer matters
because the first one would have been a much bigger claim than the truth.**

Not one archived usage block trips `missing_usage_keys`. The five drifting runs
contain **zero `model_call` records at all** — they are the salvage and preflight
runs, which make ARC HTTP calls and no model calls. The drift is a pure
*schema-shape* change: `price_run`'s return dict gained three keys, and
`armtools/archive.costs()` embeds that dict verbatim into `MANIFEST.json`, which
`verify_provenance._idempotence` compares **byte for byte** against manifests
written before those keys existed. Flattened leaf by leaf, the difference is:

```
/cost/from_price_table/unmeasured_calls       absent -> 0
/cost/from_price_table/missing_usage_keys     absent -> null
/cost/from_price_table/unpriced_usage_keys    absent -> null
```

Three leaves, identical in all five. `usd_total`, `per_model`, `model_calls`,
`pricing.sha256` and `unpriced_models` are byte-identical. Monkeypatching
`price_run` to drop exactly those three keys turns the check green — *"9
manifests, all byte-stable under re-derivation"*. So 100% of the drift is the
added keys and 0% is repricing.

**Two corrections to what this file and the commit message say elsewhere:**

* It is **five** runs, not four. Pytest's assertion repr truncated the middle of
  the list; `20260728T012311Z-g50t-first-contact-salvage2` is the fifth. A
  failure message that elides part of its own evidence is worth writing down in a
  run whose subject is exactly that.
* `unpriced_usage_keys` is a **second, independent** schema addition riding in
  this commit. `cost()` had always computed it and `price_run` dropped it on the
  floor; surfacing it is a good change and it is not the one the work order
  asked for. It contributes to the drift as much as `missing_usage_keys` does.

**What is not being done, and why.** The fix is to regenerate the five
backfilled manifests (`cd theoria-arm && python -m armtools.backfill --all`) —
the path the archive's own tooling advertises, and provably safe here because the
re-derived bytes differ only in the three leaves above. **`theoria-arm` is
RES-1's territory under `A3-campaign-devpile`**, so it is handed over on the bus
with this evidence rather than done here.

The tempting alternative — emit the new keys only when non-empty, so the old
bytes reproduce and nothing goes red — is **refused**. It would make "priced
under the S29 rule, nothing unmeasured" indistinguishable from "priced under the
old rule, which never looked", which is the same collapse the whole item is about.

**One piece of evidence for keeping the rule as it is.**
`theoria-arm/evidence/model-proxy-401.jsonl` holds **65 `model_call` records with
`"usage": {}`** — HTTP 401s against `claude-haiku-4-5-20251001`, both required
keys absent. Under master's `cost()`, `price_run` reports those as 65 calls
totalling `$0.00` with `unpriced_models: null`. That file is not under `runs/`
and not in any manifest, so it does not affect this test — but it is precisely
the shape this item exists to stop, and it is real, not hypothetical.

## Result so far

```
python -m pytest proxy                 ->  392 passed
python -m pytest proxy/tests/test_cost.py  ->   12 passed
bash proxy/verify_spend.sh             ->  VERIFY: green
```

All three defects are folded in. Zero API calls, $0.00, zero sealed-pile
contact. The one gate that goes red because of this branch is in `theoria-arm`
and is a schema addition, not a repricing — see the section above, and the bus
handover to RES-1.
