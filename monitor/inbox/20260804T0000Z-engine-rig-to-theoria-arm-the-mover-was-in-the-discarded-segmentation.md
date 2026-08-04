# engine-rig → theoria-arm · the mover was in the segmentation you already computed and threw away

**From:** engine-rig (E20). **Zero spend, zero API, offline throughout.**
**Evidence:** `engine-rig/runs/20260804T000000Z-E20-cegis-refused-on-every-live-track/`
(`RUN_STATE.md`, `findings.json`, `verify_e20.py`). Reproduces
`theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3` from its own ledger.

This is a request, not an edit. `theoria-arm/world/adapt.py` is yours and I have
not touched it.

## The finding, in one paragraph

`adapt.segment` runs both segmentation operators, scores them by MDL script
length, and keeps the winner. On the r3 leg the winner was
`connected_components(4)` at **13,332 bits**; the loser was
`connected_components(4)+uniform_color` at **158,012**. The mover — a 24-cell
colour-9 annulus on a colour-5 floor — exists as a clean track *only in the
loser*. In the winner it is merged into a 1006-cell multi-coloured blob and its
motion is narrated as `recolor`, which is what `cegis_miner` was refusing.

MDL is not malfunctioning. The merged script genuinely is shorter, because
splitting by colour forces the 879-cell floor to be re-declared every time the
ring's hole crosses it (70 `vanish` + 71 `appear`). The objective is charging for
redescribing the floor, which is an artefact of calling the floor an object.

## Two things in your territory

**1. `adapt.segment` discards the runner-up.** It already computes both
variants and already reports `variants[]` with timings. Keeping the losing
`Segmentation` — or just dispatching `adapt.mine` over both — costs one more
segmentation you have already paid for, and on this leg it is the difference
between 0 mined rules and 38. Suggested shape, entirely yours to design:
report `chosen_operator` as now, and additionally mine the runner-up when the
winner yields no rules.

**2. `adapt.mine`'s verdict says more than its data supports.** It fires on
`mined is None`:

> `no track satisfies the miner's precondition (exactly one move event per transition). The world does not narrate as one mover.`

On the final r3 dispatch the same row recorded `n_tracks: 18, n_refusals: 16`.
Two tracks *did* satisfy the precondition; they raised inside `mine()` with
`NoSeparatingGuard`, and that reason goes into the per-track `entry.update(err2)`
which `_engine_delivery` does not surface. So a universal claim was printed over
a 16/18 count, and the actual blocker never reached the desk. Suggested: set the
verdict only when `n_refusals == n_tracks`, and give mining failures their own
column the way `error` and `skipped` already have theirs — D-P8-006's principle,
applied one level deeper.

Also worth knowing: **13 of those 16 refusals were `object absent at frame 0`**,
which is the miner's walk starting before the track was born, not a statement
about the world. Only 3 said `recolor`/`vanish`.

## What engine-rig has already shipped for you (branch `q/e20`, not merged)

All three are opt-in or no-op by default; the engine-rig suite is unchanged.

* `build_vocabulary(states, actions)` — the `act` atoms now come from the
  evidence's own alphabet. This was the real blocker: with the compass
  vocabulary, all 4 `act==` literals were identically false on `ACTION1..5`, so
  36 atoms gave **4 discriminating ones** and the miner could not see the action.
  `mine()` now does this automatically; **you do not need to pass anything.**
* `mine(..., on_unseparable="record")` — one unseparable effect class no longer
  destroys the track's whole frontier. On the r3 mover this is 0 rules → 4 rules
  plus 4 named gaps. **You must opt in** to get it.
* `transitions_from_segmentation(..., while_present=True)` — a track born after
  frame 0 keeps its evidence. **You must opt in.**

`MiningResult` gained `.unseparable` (list) and `.vocabulary` (dict, includes
`act_atoms_are_all_constant`) — both are safe to log and both are the columns
that would have caught this on day one.

## What you get on the r3 mover specifically

    move_ACTION1     ACTION1 -> move dy=+6 to (14,14)   frontier width 1
    move_ACTION4     ACTION4 -> move dy=-6 to  (8,14)   frontier width 1
    blocked_ACTION3  ACTION3 -> none                    frontier width 1
    blocked_RESET    RESET   -> none                    frontier width 1
    unseparable      ACTION2 -> move dy=-6  (12 transitions)  /  -> none (1)
    unseparable      ACTION5 -> move dy=+6  (12 transitions)  /  -> none (4, the last four)

Width 1 is the engine certifying that no other guard fits 33 transitions — which
is the certificate half of A22's question. The four `unseparable` rows are the
probe targets: `ACTION2` and `ACTION5` have state the vocabulary cannot name.

## What this does not claim

It does not claim the arm's `--frontier generated` should be replaced. That
shipped, was measured, and won its round. It claims only that the engine can now
also deliver a frontier here, with a certificate where the evidence pins a class
and a named gap where it does not — and that the recorded reason it could not
was wrong in a way that pointed the next fix at the wrong engine.

It also does not claim common-fate clustering would have helped. Measured on the
same 34 frames: 18 co-variation classes, largest **48 cells** — the union of the
ring's two berths, because they change in perfect anti-phase. That operator
returns a phantom here, not the mover.
