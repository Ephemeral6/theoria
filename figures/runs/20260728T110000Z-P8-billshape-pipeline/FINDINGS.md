# P8 — findings, written as they were found

Incremental log. The manifest is the machine record; this is the part it cannot
carry. Written before the fix, so the reasoning survives even if the fix is
reverted.

## The work order's premise is one revision stale

`monitor/board/items/P8-billshape-pipeline.md` says the theoria column of fig02
is empty. It is not: `P4-figures` (merged, `figures/RUN_STATE.md`) already draws
the theoria arm, reading `cost_curve.json` because the arm's `ledger.jsonl` is a
third record dialect whose dollars are nested under `response`.

That does not make the work order wrong, it makes it *aimed one step short of
where the defect is*. What P4 shipped is three **hand-declared** run paths:

```
THEORIA_RUNS = (("theoria_cost_curve_first_contact", "theoria_manifest_first_contact"), ...)
```

plus three matching pairs of `Source` entries in `sources.py`. A run that lands
on disk does **not** enter the figure; it enters when a human edits two files.
The work order's real ask — "a ledger enters the figure the moment it lands,
without anyone editing code" — is therefore still open, and it is open in a
sharper form than the order states.

## Two live drifts, both the shape P4 named

`figures/RUN_STATE.md` records P4's three defects as one shape: *an upstream
artefact moved and the figure code did not know*. Both drifts below are that
shape again, and both were found by listing a directory and diffing it against a
hand-maintained tuple.

### D-1 — two tracked roll-ups exist and are not read

`ROLLUP_KEYS` names four files. `baseline-arms/out/` holds **six**:

| file | tracked | in `ROLLUP_KEYS` |
|---|---|---|
| `pilot_ar25-0c556536.json` | yes | yes |
| `pilot_g50t-5849a774.json` | yes | yes |
| `pilot_sk48-d8078629.json` | yes | yes |
| `pilot_tn36-ef4dde99.json` | yes | yes |
| `pilot_g50t_sonnet_rerun.json` | **yes** | **no** |
| `pilot_sk48_sonnet_rerun.json` | **yes** | **no** |

The consequence is on the plate, not in a note. `outcome` drives line style:

* `bare_cc-g50t-claude-sonnet-5-ddabe772` — 45 ledger rows, drawn **dotted**
  ("no roll-up record: outcome unknown, not 'fine'"). The tracked roll-up on
  disk says `budget_exhausted`, i.e. solid.
* `bare_cc-sk48-claude-sonnet-5-9022a076` — 17 ledger rows, drawn **dotted**.
  The tracked roll-up says `model_error`, i.e. **dashed** — and dashed is the
  plate's own warning that *a curve which stops early stopped because the API
  died, not because the run was thrifty*.

So the figure currently withholds one of the two warnings it exists to draw, on
a run for which the evidence is committed to the repository. Verified in the
built artefact: the `outcome` column is empty for both run ids in
`figures/csv/fig02_bill_shape.csv` as committed.

### D-2 — a fourth theoria run directory carries a cost curve and is not read

`theoria-arm/runs/` holds nine directories. Four carry `cost_curve.json`:

| directory | calls | USD | in `THEORIA_RUNS` |
|---|---|---|---|
| `20260728T012311Z-g50t-first-contact-aborted` | 1 | 1.307727 | yes |
| `20260728T014402Z-g50t-first-contact-aborted` | 1 | 0.730485 | yes |
| `20260728T015354Z-g50t-first-contact` | 5 | 6.317658 | yes |
| `preflight-20260728T012057Z` | **0** | **0.000000** | **no** |

The fourth is a preflight whose curve is empty. It costs the bill nothing, which
is exactly why it is worth drawing as present-and-empty: `_load_theoria_curves`
already carries a branch for it ("cost_curve.json is empty — no model call was
billed, so no curve. Not a zero-cost run; a run with no calls") and that branch
has **never executed**, because the only run that would trigger it is not in the
tuple. A hand-maintained list does not just miss data; it leaves the code that
handles the missing case unexercised, so nobody finds out it was wrong.

The other five directories carry no `MANIFEST.json` and no `cost_curve.json`
(`-salvage`, `-salvage2`, one preflight). They are not runs of the arm in the
sense the bill means, and discovery must skip them **by a stated rule**, not by
being absent from a list.

## What the shape metrics are, and where they come from

The work order asks for the front-load exponent, the convergence point and the
context-growth fit on the plate. All three already exist, defined, with
anti-gaming floors, in `battery/metrics/economy.py`:

* **E2 front-load index** — share of total cost in the first 25 % of turns,
  head interpolated, not rounded (`FRONTLOAD_K = 0.25`); `thin` below
  `MIN_TURNS_FOR_SHAPE = 8` turns, because a run that ended on turn four is
  trivially front-loaded.
* **E3 convergence point** — fraction of turns needed to reach 90 % of total
  cost (`CONVERGENCE_SHARE = 0.9`); same floor.
* **E4 context growth** — R² of a quadratic fit to context tokens per turn
  minus R² of a linear fit. Positive means context is accelerating. Reads the
  *token* series, not the priced one, so it survives a change in the price list.

fig02 does **not** recompute them. It reads the values the battery published in
`battery/artifacts/capability_spectrum.json` (battery v2, 95 runs). Recomputing
would create a second definition of a Phase 4 primary endpoint that could drift
from the first — the precise failure `figures/SOURCES.md` exists to prevent.

Two consequences that must be said on the plate rather than smoothed over:

1. **The turn axes are not the same.** The battery's turn axis is *model-call
   order* (`INPUT_FORMAT.md` gap 5: the ledger has no explicit turn index).
   fig02's x-axis is `step_idx`. For most runs the two agree; for
   `ddabe772` the battery counts 20 turns over 24 billed calls, and for
   `9022a076` 7 turns over 10 calls. Where they disagree, E3's crossing is
   **not** drawn as a position on fig02's axis; the value is reported and the
   disagreement is named.
2. **The theoria arm has no E2/E3/E4 at all.** Battery v2's five arms are
   `bare_cc`, `schema_repro`, `theoria_a0`, `theoria_a0_spike`, `theoria_a2`.
   The theoria arm fig02 draws — the live ARC run — is in none of them, so its
   shape metrics are absent, not zero, and the plate says which.

## The claim that gates 1-7 were green on the drifted tree is measured, not asserted

A detached worktree at the base commit `98593a0` -- the tree carrying both drifts
-- was built and verified in full:

```
git worktree add --detach .worktrees/p8-baseline-check 98593a0
cd .worktrees/p8-baseline-check/figures && bash verify.sh
```

**All seven gates green.** Two builds byte-identical, 43 sources hashed and
unchanged, committed tree equal to a fresh build, 24 images and 6 CSVs present,
no figure reading an undeclared path. And in that same tree's committed CSV:

```
bare_cc-g50t-claude-sonnet-5-ddabe772, outcome=[]
bare_cc-sk48-claude-sonnet-5-9022a076, outcome=[]
```

Two runs with committed outcomes, drawn as outcome-unknown, in a tree that
passes every gate it has. That is the argument for gate 8 in one screen, and it
is a measurement rather than a plausible story about what the gates would have
done. The check worktree was removed after the run.
