# The live probe, prepared and not fired

S31 requirement 2 asks for one minimal real-arm call — budget computed first,
taken through `spend_gate.reserve()` — and then for `proxy/var/ledger.jsonl` to
gain a record whose `arm` is not `mock_arm`. The session owner gates all live
spend, so this pass **prepares** that call instead of making it. Nothing here
opened a socket; the shared pool is byte-identical before and after
(`$36.1423 / $214.90 spent, 0 held, 0 live reservations` — `evidence/pool.txt`,
taken after the three refusal paths below were exercised).

The go-ahead is one command:

```bash
cd C:/Users/user/Desktop/theoria/proxy/runs/20260731T104757Z-S31
python live_probe.py --go --authorised-by "<who approved, and where they said so>"
```

Everything below is what that command does. The script recomputes every number
in this document at run time from the same functions the gate uses, so the
document cannot quietly drift away from the thing it describes — run
`python live_probe.py` with no arguments and compare.

---

## 0. What is already known, so the probe is not asked to prove it

The **write end is not broken**. The offline probe at
`../20260730T043824Z-S31-a10-said-done-prove-it/real_arm_probe.py` drove
`run_game(arm='bare_cc')` against the loopback mocks and wrote **61 records
carrying `arm: bare_cc`**. `proxy/var/ledger.jsonl` holds zero real-arm records
because no caller has ever passed a real arm to it — not because one was passed
and dropped.

So the live probe adds exactly one proposition: **axis 2**, that a run reached an
upstream off this machine. Axis 1 (arm identity) is already satisfiable for
$0.00 by `python -m proxy.runner --mock --arm bare_cc`, which would append
real-arm-looking records to the shared ledger and flip the 2026-07-29 audit from
red to green without one real arm having run. That is the forgery this whole
item exists to name, and it is why the probe reports the two axes separately and
requires **both**.

## 1. Two rungs. Rung 1 is the default because it is the cheaper witness

| | rung 1 (default) | rung 2 |
|---|---|---|
| env upstream | `https://three.arcprize.org` — **live** | live |
| model upstream | loopback `MockProvider` | `https://api.anthropic.com` — **live** |
| model calls | 0 | 1 |
| worst-case model spend | **$0.000000** | **$0.009688** |
| ARC requests | 4 | 4 |
| satisfies axis 2 | **yes** (`env_upstream` is non-localhost) | yes |
| needs `ANTHROPIC_API_KEY` | no | yes |

Rung 1 is the minimum that answers the question. Rung 2 is worth firing only if
the *model* half's live path is specifically what is in doubt; it is
`--rung 2`.

## 2. The budget arithmetic, before anything is reserved

The per-call bound is not a guess and is not copied — `live_probe.ceiling()`
calls `PriceTable.ceiling_for()`, which is the same function `model_proxy.py:218`
uses to decide whether to open the socket at all:

```
model               claude-haiku-4-5     ($1.00 / $5.00 per million, pricing_v1)
max_tokens          256                  (output side, in full)
input estimate      4204 tokens          (a 64x64 frame + the arm's wrapper,
                                          at a pessimistic 3.0 chars/token)
cache multiplier    2.0                  (the 1h-write rate, the dearest line)
                    ----------------------------------------------------------
per-call ceiling    $0.009688
model calls         x 1   (budget=1 -> RESET + one ACTION -> one decide())
                    ----------------------------------------------------------
worst case          $0.009688            (rung 2)   /   $0.000000 (rung 1)
```

Both estimates err upward on purpose. A ceiling that is sometimes too low is not
a ceiling.

The action side is counted in outbound ARC HTTP requests, which is the unit
`spend_policy.json` names and the unit `env_proxy.py:353` charges one at a time:
`scorecard/open`, `RESET`, `ACTION1`, `scorecard/close` = **4**.

## 3. The reservation it will take

```python
gate = default_gate()
run_id = new_run_id()
reservation = gate.reserve(
    "s31-live-arm-probe",          # campaign: names the run, not the process
    0.05,                          # usd_cap    — 5.2x the rung-2 worst case
    10,                            # action_cap — 2.5x the 4 requests it makes
    holder={"run_id": run_id, "arm": "bare_cc", "game_id": "ar25-0c556536",
            "undeclared": False, "authorised_by": <the --authorised-by string>})
```

Then `run_game(..., spend_gate=gate, spend_reservation=reservation)`, so both
proxies charge one claim rather than each taking their own and holding the pool
twice for one run's worth of spending.

**Why this is a script and not `python -m proxy.runner --game ... --arm bare_cc`.**
That command works, and it is the wrong command. `runner.main()` exposes
`--game / --arm / --budget / --variant / --ledger / --stream / --mock` and **no
`--usd-cap` or `--action-cap`**, so a CLI run falls through to
`spend_policy.json`'s `default_run_caps` — **$5.00 and 600 actions**, stamped
`undeclared: True`. That is 500x the ceiling this probe can actually reach.
The policy's own provenance note says the defaults exist to make *not* declaring
inconvenient; taking them for a probe whose bill is computable to six decimal
places would be exactly the "process believing it may spend a number nobody
wrote down" the file was written to stop. Declaring the caps is one argument, so
this declares them.

`gate.release()` runs in a `finally`, and `run_game`'s own `_release_on_exit`
wrapper is underneath that, so a crash cannot strand the shared pool for the
full hour TTL. Only the *unspent hold* comes back; what was spent keeps counting
forever.

## 4. What proves it worked

A `run_start` record of this shape, appended to `proxy/var/ledger.jsonl`:

```json
{
  "v": "1.0", "event": "run_start", "arm": "bare_cc",
  "run_id": "r-<minted>", "game_id": "ar25-0c556536",
  "env_upstream": "https://three.arcprize.org",
  "model_upstream": "<loopback on rung 1, https://api.anthropic.com on rung 2>",
  "spend_gate": {"pool": "theoria-shared-2026-07",
                 "campaign": "s31-live-arm-probe",
                 "reservation_id": "res-<minted>"}
}
```

and, in the same run's records, `env_step` rows carrying `"arm": "bare_cc"`.
The script reports the two axes separately and prints the first three fresh
records plus `reconcile_run(..., write_incident=False)` for the new run id.

**Pass is both axes, not either.** Restated because collapsing them is the
defect this item was opened on:

* **axis 1** — `arm` in `{bare_cc, schema_repro, theoria}` on a record whose
  `event` is not `incident`. Incidents are excluded because `reconcile.py:521`
  stamps an incident with the arm of the run it complains about, so counting by
  `arm` otherwise counts the auditor's own footprints.
* **axis 2** — `run_start.env_upstream` or `.model_upstream` is not
  `127.0.0.1` / `localhost`.

`--no-incident` is passed to the reconciler deliberately: `reconcile.py:549`
makes incident-writing opt-*out*, and an audit that appends to the file it is
auditing is not a read.

## 5. Preconditions, and the order they are checked in

1. **Run it from the MAIN checkout, not a worktree.** `proxy/paths.py` resolves
   `LEDGER_PATH` and `.env` from `__file__`, so both are worktree-local — but
   `SpendGate` walks to the main checkout on purpose, so the *pool* is genuinely
   shared. Firing from a worktree would charge the shared pool and write the
   evidence into a gitignored file nobody audits. The dry run prints a banner
   when it detects this.
2. **`ARC_API_KEY`** must be set (repo-root `.env`, per CLAUDE.md). Both rungs.
3. **`ANTHROPIC_API_KEY`** must be set for rung 2 — and it is **not in
   `.env.example`**, so it is likely absent. Checked *before* the reservation is
   taken, so a run that cannot pay does not first take the pool's headroom and
   then fail. Verified: `refusals.txt` line 3.
4. **The game must be in the development pile.** The whitelist is read from
   `arc-recon/data/piles.json`'s `dev_pile` and is positive; the sealed list is
   never loaded. A refused id is **not echoed** — a refusal that repeats the
   thing it refused would write a sealed id into whatever captured the output.
5. **`--go` requires `--authorised-by`.** A live call carries a name.

The script only ever reports whether a credential variable is *present*. No
value is read, logged or written by it; the proxies read their own keys inside
themselves and `redact.VAULT` masks them in every record.

## 6. Afterwards

Report the amount in `monitor/inbox/`, per the ticket. Expect the record to be
witnessed on **both** axes or it proves nothing the offline probe has not already
proven.

And note what a green rung 1 does *not* mean: it witnesses that a real arm
identity reached the real ARC environment through this proxy. It does **not**
close the gap `DELIVERY_RULING.md` §4 records — the three arm territories
billing their own inner loops into the shared ledger. One probe record would
make the ledger's histogram read `1` and still not mean the arms are running,
which is why the probe is a witness for axis 2 and not a fix for anything.

---

## Files

| file | what it is |
|---|---|
| `live_probe.py` | the command. Dry run by default; `--go` fires it |
| `dry_run.rung1.txt` | archived dry run, rung 1 |
| `dry_run.rung2.txt` | archived dry run, rung 2 |
| `refusals.txt` | the three refusal paths, exercised |
| `evidence/pool.txt` | the shared pool after this pass: 0 held, 0 live reservations |
