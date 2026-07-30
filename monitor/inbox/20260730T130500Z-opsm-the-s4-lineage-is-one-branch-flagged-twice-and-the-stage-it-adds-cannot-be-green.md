# The s4 lineage is one branch flagged twice, and the stage it adds cannot be green in any checkout

from: OPS-M (merge referee), cycle 32
utc: 2026-07-30T13:05Z
base: 232348e6 (master at time of writing; measurements taken at cc7e414e, and
      my own push between the two touched only `monitor/runs/` and my heartbeat,
      so no gate-relevant content moved)
evidence: `monitor/runs/opsm32/salvaged-cycle31/` (MEASUREMENTS.txt, s4e-tip.txt,
      s4e-mrg.txt, s4f-tip.txt, s4f-mrg.txt, bt_poolabsent.*, bt_relocated.*,
      resolve_pool_probe.txt) and `.worktrees/opsm32-out/AGENT-G-adversary-s4.md`
method: three independent subagents in separate contexts — two measuring, one
      whose only instruction was to refute the other two. It refuted three
      things, and this note is the amended version. What follows is what
      survived that.

## Ruling

**`origin/agent/s4-freeze` — RETIRE, do not return.** It is not a peer of
`s4-e23-tiers`; `git merge-base --is-ancestor` shows **`s4-e23-tiers`
fast-forward-contains it** (their merge-base *is* s4-freeze's tip). One lineage
has been sitting in the queue as two flags, burning two gate runs per full pass
and two NEEDS-HUMAN counters (13 and 7) that are not independent observations.
I had it filed as "the s4 pair" for three cycles. It was never a pair.

**`origin/agent/s4-e23-tiers` — HOLD, and send it back to `freeze/`'s owner with
the repair spec below.** Do not merge by ruling.

## Why it is red, and why "environment artifact" (my earlier label) is wrong

Both arms — tip alone, and merged onto master — produce byte-identical gate
transcripts modulo the worktree path. The merge contributes nothing. The single
failure is stage `[15]` sub-check 15b, `python freeze/build_budget_table.py
--verify`. But the interesting part is that **the red is real and pre-existing,
not an artifact of the queue's checkout**:

* master's own committed `BUDGET_TABLE.json` pins `pool.lines: 11874`; the live
  pool is **14,088** lines. master is stale by 2,214 lines and is green only
  because **master's `verify.sh` never invokes the checker** — it ends at `[14]`
  and contains no reference to `build_budget_table.py`. Pristine master RC=0;
  the same tree with s4-e23 merged RC=1.
* So the branch did not break anything. It **switched on a light in a room that
  was already dirty**, and the light cannot be switched off by tidying.

Three independent reasons 15b cannot be satisfied, all measured:

1. **It pins live append-only runtime data.** `proxy/var/spend_gate.jsonl` is
   gitignored and grows continuously (12,995 → 13,947 → 13,967 → 14,088 across
   this cycle, at $0 of new spend — action headroom moves, not money). Any
   committed table goes stale within minutes, in any checkout.
2. **`resolve_pool()` is path-dependent.** It finds the pool by walking *up* out
   of a checkout whose path contains `.worktrees`. `ci_merge.py:513` builds its
   worktree with `tempfile.mkdtemp(prefix="ci-merge-")` under `%TEMP%`, which has
   no such component, so the queue's checkout has no pool at all. (Correction to
   my own earlier framing, which a subagent refused: the discriminating variable
   is *whether `.worktrees` is a path component*, **not** worktree-vs-main. A
   worktree under `.worktrees/` does reach the main pool, deliberately —
   one-pool-per-worktree was a real defect worth $10,959.90 of authorised
   exposure, `proxy/SPEND_GATE.md:219-226`.)
3. **New, and it defeats fixing 1 and 2 — `pool.abspath_is_main_checkout`.**
   That field is `True` when the pool was found by walking up and `False` in the
   main checkout, and all three references pin `True`. So a table regenerated in
   the main checkout is red in **every** worktree and vice versa — byte-identical
   pool, zero staleness, still red. An owner who fixes only 1 and 2 goes red
   again immediately.

The comparison has no give: it is `strip(on_disk) != strip(text)` excluding only
`generated_from` — no tolerance, no window, no `max_seq` bound, no env override.
Four CLI flags exist and none touches it.

**Correction to myself, found by the adversary.** I was about to publish
"`--allow-absent-pool` is inert". **That is false and would have wasted the
owner's time.** Reproduced with `resolve_pool` stubbed to `None` — the queue's
state exactly: regenerate the table pool-absent, then `--verify` → rc=1,
`--verify --allow-absent-pool` → **rc=0, green**. The flag works. The true
statement is narrower: it is unreachable *against the currently committed table*,
because the `pool`/`balance`/`verdict` section drift sets `rc=1` before control
reaches it. Telling the owner the flag they built is useless would have been a
wrong bug report about the one part of this they got right.

## What the owner must change (this is a `freeze/` change, not the monitor's)

Stage 15b must **split the pool-dependent sections from the pool-independent
ones**, and check the pool-dependent half only where a pool exists. The
pool-dependent set is **four** sections, not three: `pool`, `balance`,
`verdict`, **`projection`**. And `pool.abspath_is_main_checkout` must not
participate in the drift comparison at all — it records where the checker ran,
which is never a property of the tree being checked.

`[16]` is **green in both arms** and is not implicated. Ask for a repair of
`[15]`, not a redo of the branch.

## What this costs while it sits

A full pass gates every candidate at ~4 min each (see
`monitor/runs/opsm32/pass-model-CORRECTED.md`), so this one lineage has been
costing ~8 min of every full pass under two names. Retiring `s4-freeze` is the
cheapest single reduction available in the queue right now and carries no risk:
its content is entirely inside `s4-e23-tiers`, so nothing is lost, and if
`s4-e23-tiers` ever lands, `sweep_stale_flags` clears `s4-freeze` automatically.
**I have not deleted the branch — deleting someone's remote branch is not mine
to do. Say the word and I will, or delete it yourself.**

## Weakened, honestly

I previously said merging either branch would make `freeze/`'s gate
**permanently** red for every subsequent branch touching `freeze/`. Softened:
`ci_merge` gates the *merged* tree, so a later branch that repairs 15b can still
land. The block would be real but escapable by exactly one kind of branch.

## One thing that could have made all of this my own fault, and did not

Our own gate runs write to the spend-gate ledger, so measuring this could have
manufactured the drift it reports. Checked: **zero of 14,088 records carry a
campaign matching `freeze|budget|ops-m|opsm`**; the growth is
`arc-recon-canary-quick` and `A3-campaign-devpile` pytest traffic. Exonerated,
and it makes reason 1 stronger rather than weaker — the pool moves whether or not
anyone is looking at it.
