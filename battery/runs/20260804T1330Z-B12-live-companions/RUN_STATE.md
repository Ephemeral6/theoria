# B12 — the battery's live readings were not stale; the rungs that check them were blind

**Territory:** battery · **Branch:** `q/b12` · **Base:** master `4846e66d` ·
**UTC:** 2026-08-04T13:30Z · **API spend:** 0.00 USD · **Network:** none ·
**Sealed-pile contact:** none (dev-pile `g50t-5849a774` / `sk48-d8078629` legs
read only; the pile guard runs on every id this ticket touched, and one test
constructs a sealed id at run time from `arc-recon/data/piles.json` without
writing it down).

## 0. The brief's premise, tested first

**There is no `B12` item on the board.** `monitor/board/items/` at
`4846e66d` holds A24–A34, S49, S50, V31 and no `B*` item at all; nothing named
B12 appears in `monitor/board/done/`, `monitor/board/claimed/`, `board.log`,
or anywhere in git history. The prompt's own text was the whole brief, so it
was followed as the brief and its premises tested the way an item's would be.
That absence is itself worth the board's attention: this ticket's premise
turned out to be false, and an argued item would have carried the evidence for
it that could have been checked before the work started.

The prompt read: *the archive now holds far more live material than when the
battery last read it — the R1, R1b, R2, R2b rounds and the A26b legs in flight. Bring
the battery's live companions up to the archive and report what moved.*

**Nothing moved, and the premise is false in its main clause.** All six
`battery/artifacts_live/` companions were regenerated in-process and compared
against the committed files by canonical-bytes digest
(`probe_refresh.py` → `refresh.json`): **0 of 6 moved.**

| companion | committed sha256 | recomputed | moved |
|---|---|---|---|
| `live_arm_readings.json` | `a6d26027…` | `a6d26027…` | no |
| `live_economy.json` | `fa23ad80…` | `fa23ad80…` | no |
| `gaming_audit.live.json` | `9ff3c5e7…` | `9ff3c5e7…` | no |
| `frontload_e2l.json` | `6deadace…` | `6deadace…` | no |
| `threat_model.json` | `3182b32b…` | `3182b32b…` | no |
| `live_census.json` (new) | `fa84f426…` | `fa84f426…` | no |

The R1, R1b, R2 and R2b legs were already in: S46 regenerated the companions
on 2026-08-02 (`1efc8dbf`, `7befaef7`) and the readings have carried all
fourteen of them since. **No metric changed, because no input changed.** A
digest is the stronger statement here: listing metrics that "look the same"
would leave the question open, and an unchanged digest closes it.

The **A26b legs are correctly absent**: they are in flight, untracked in the
main tree, and this work ran in a worktree at master, which cannot see them.
Recorded as absence, not as zero.

So the ticket's real question is the one underneath it: *if the readings were
already current, why did anyone think they were not — and would the rungs have
told us if they were not?*

## 1. The finding: fourteen live legs are invisible to every rung

Both live companions read the arm through
`battery/adapters/theoria_live.collect`, which returns the legs it loaded
**and** the legs it refused with reasons. Rungs 7 and 8 gate both lists
against an in-process recompute. That is complete only for legs the adapter's
`discover` hands to `load_leg` — and `discover` filters first:

```python
campaign = (start.get("spend_gate") or {}).get("campaign") or ""
if campaign.startswith(CAMPAIGN_PREFIX):      # "theoria-arm:A3-campaign"
    out.append((name, path))
```

A leg archive that fails that test is **not refused — it is never seen**. It
lands in no `runs` map, in no `excluded` list, in no rung's count, and no
recompute can go red over it, because both walks agree about a thing neither
one looked at. The staleness contract rungs 6–8 carry is real; its domain is
just smaller than it reads.

Measured on this tree:

* `theoria-arm/runs/` holds **79 directories, 37 with a `ledger.jsonl`**;
* the companions score **14** and refuse **9** with named reasons;
* **14 more declare `arm: "theoria"` and are in neither list.**

Those fourteen are not junk. Every one of them ran against the live upstream
`https://three.arcprize.org`; eight recorded env steps; between them they
bill **42 model calls and 23.855414 USD of real spend, over 682 env steps**.
They are the pre-A3 legs — first contact, the E3 sk48 carries, the preflights
— archived before the campaign's spend gate existed, so they carry no
campaign label at all.

**And the pile guard sits downstream of that filter.** `load_leg` calls
`piles.assert_playable` (default deny, raises on sealed or unknown), but
`discover` decides what reaches `load_leg`. Before this ticket, an unlabelled
leg naming a sealed game would have been dropped without ever meeting the
guard. On this tree all fourteen name development-pile games — a fact about
the material, not a property of the code, which is exactly why it needs an
instrument rather than a sentence.

## 2. What was built

* **`battery/audit/live_census.py`** (freeze `code` bucket) — walks the
  archive with no filter and gives every `ledger.jsonl` a named disposition:
  `scored` / `excluded` (the adapter's own reason, verbatim) / `invisible` /
  `foreign` / `unreadable`. Runs `piles.assert_playable` over the **whole**
  archive. Pins the sha256 of every ledger it read. Byte-reproducible for a
  fixed tree; refuses any destination inside `battery/artifacts/` by reusing
  `live_tiers.refuse_frozen_destination` (one definition, not two).
* **`battery/artifacts_live/live_census.json`** (freeze `readings` bucket) —
  the companion. Written alongside; nothing under `battery/artifacts/` was
  touched.
* **`battery/verify.py` rung 9** (the eight existing rungs renumbered `/9`) —
  RED on: census vs in-process recompute; a committed row outside the
  development pile; the census's `scored` count disagreeing with rung 7's
  `n_runs`; a walked ledger that got no disposition. The invisible legs
  themselves are **reported, not gated** — the campaign label belongs to
  `theoria-arm`, and a rung that is red for another territory's labelling
  decision is a rung this territory cannot clear (rung 8's reasoning about
  the three-way money disagreement, applied again).
* **`battery/tests/test_live_census.py`** (freeze `suite` bucket) — 21 tests.
* **`battery/BATTERY_V1.md`** — dated amendment (2026-08-04, third), blocks
  re-rendered block-by-block with `freeze.render_blocks()`.

**A census is not a promotion.** Nothing here loads an invisible leg as a
`Run`, evaluates a metric on it, moves a tier, or scores a prediction.
Whether the pre-campaign legs belong in a reading `BATTERY_V1.md` describes as
the A3 campaign's is a question about the arm's campaign labelling and belongs
to `theoria-arm`. The census reports the difference and names the owner.

## 3. Negative controls (acceptance, not garnish)

`battery/tests/test_live_census.py`, 21 tests, all required to be seen red the
way `test_freeze.py`'s are:

| control | requires |
|---|---|
| unlabelled leg in a synthetic archive | disposition `invisible`, **and** `theoria_live.collect` returns `([], [])` — the gap asserted, not narrated |
| unlabelled leg naming a **sealed** id | `SealedPileError` from the census while the adapter stays silent. The id is read from `piles.json` at run time; no sealed id is written into the test file |
| tampered census (invisible list emptied) | rung 9 names "recompute" |
| a committed row with `pile: sealed` | rung 9 names "development-pile" |
| census and readings disagree on how much was read | rung 9 names "disagree" |
| census absent / unparseable | rung 9 names "absent" / "not JSON" |
| write into `battery/artifacts/` | `ValueError`, CLI exit 2, no file created |
| foreign arm / ledger with no `run_start` / directory with no ledger | named dispositions, never a silent skip |
| absence is not zero | every disposition with `model_calls == 0` carries `billed_usd: null` |

## 4. The economic family — the honest answer is no

The census's second half records, per scored leg, the decision turns on the
archive's exact `bill_shape.json` axis against
`battery/metrics/economy.py`'s `MIN_TURNS_FOR_SHAPE = 8`. `probe_shape_floor.py`
walks them in archive order (`shape_floor.json`):

| n | leg | decision turns | clearing the floor | cumulative USD |
|---|---|---|---|---|
| 4 | `…1310Z-A3-level2-carried-r2` | 3 | 0 | 9.56 |
| 5 | `…1430Z-A3-level2-carried-r3` | **8** | **1** | 23.00 |
| 6 | `…1500Z-A3-sk48-carried-l1` | 4 | 1 | 35.25 |
| 7–8 | R1 g50t / sk48 | 2 / 1 | 1 | 50.46 |
| 9–10 | R1b g50t / sk48 | 6 / 2 | 1 | 85.60 |
| 11–12 | R2 g50t / sk48 | — (no billed call) | 1 | 85.60 |
| 13–14 | R2b g50t / sk48 | 7 / 2 | 1 | **124.64** |

**No — the bill shape says nothing at fourteen legs that it did not say at
four.** `1 of 14` legs clears the floor, and it is the same leg (r3) that
cleared it before the R rounds landed; the longest leg since is 7 turns. The
floor is **per-leg**: it is cleared by a longer leg, never by more legs. The R
rounds bought roughly 100 more dollars and eight more legs and zero more bill
shape. This is the same shape as the finding `figures/` already carries — all
legs are cold starts of level 1 — and it is reported as a reading, not
repaired.

Falsifiable by exactly one observation, which is the negative control for the
claim: a scored leg with ≥ 8 decision turns that is not r3. If one lands,
`n_clearing_floor` moves, rung 9 goes red until the census is regenerated, and
`shape_floor.json`'s answer must be rewritten. The A26b legs in flight (500
actions per leg) are the first material with any chance of producing one —
which is the argument for the census rung existing *before* they land, not
after.

## 5. The freeze

`battery/artifacts/` was not written to. `freeze.check()` returns **empty**;
`freeze.readings_drift()` returns **empty**. `gaming_audit.json` is still
`191c0ee8cf2c…` and the cut digest is still `3feca53e…`. Buckets: `code`
53 → 54, `suite` 26 → 27, `readings` 12 → 13; `freeze:*` blocks re-rendered
block-by-block by `freeze.render_blocks()`; `freeze.py` and `verify.py` are in
the `freeze` bucket and their own digests updated with them — the freeze
machinery itself is the only frozen code edited, which is the path the
`live_tiers` amendment set on 2026-07-31 and the `live_arm` amendment
followed.

## 6. Gates

```
cd battery && python -m pytest -q     ->  491 passed in 36.71s
python -m battery.verify              ->  battery: green (9/9 rungs)
```

Verbatim output in `gate_pytest.txt` and `gate_verify.txt`.

## 7. Residual gaps, stated

1. **The census does not close the gap it found.** Fourteen live legs, 682 env
   steps and 23.86 USD remain outside every reading. Whether they should enter
   is `theoria-arm`'s call: the labelling is theirs, and folding pre-campaign
   legs into a reading documented as the A3 campaign's would silently redefine
   what the published numbers cover. Raised to them via `monitor/inbox/`.
2. **The same blind spot exists wherever else a content filter precedes a
   refusal.** This ticket instrumented one adapter. `baseline-arms` and
   `ablation-arm` have their own discovery paths and were not audited — out of
   territory, and stated rather than assumed clean.
3. **The A26b legs were deliberately not read.** They are in flight. When they
   land, rung 9 and rungs 7–8 all go red until the companions are regenerated,
   which is the designed behaviour and the cheapest possible reminder.
4. **`n_dirs` counts directories, not leg archives.** 42 of the 79 carry no
   ledger (analysis runs, `_rounds`, `_round_logs`); they are counted and not
   classified. If a future leg archive ever ships its ledger under a different
   name, the census would miss it exactly the way `discover` misses an
   unlabelled one. The census pins ledger digests, not directory shapes.
5. **Rung 9 cross-checks the census against rung 7's companion only.** A
   disagreement between the census and `live_economy.json`'s `n_legs` would
   not be caught directly; it is caught transitively because rung 8 pins that
   file to its own recompute.
