# S17 day-2 delta — 2026-07-28T21:09Z → 23:45Z

Cutoff `29f41ea` (21:09:10Z); newest commit anywhere `c343976` (23:41Z). **The
window is 2 h 32 min**, not a day: 33 commits carry a committer date after the
cutoff (92 appear in `29f41ea..bac8282`, but ~60 were authored earlier on
branches and only *merged* here).

| file | rows | ids |
|---|---|---|
| `failures_new.jsonl` | 20 | F-97 … F-116 |
| `timeline_new.jsonl` | 9 | T-46 … T-54 |
| `counterevidence_new.jsonl` | 8 | **C-50 … C-57** (see id collision below) |
| `deliveries_new.jsonl` | 21 | board slugs |

`verify.py --data <copies renamed to canonical names>` → **GREEN**, 58 rows,
33 commits resolved, 48 files present, 5 deleted-but-in-history, **0 unresolvable**.

## What actually changed in the window

One loop: **three instruments were lying in the reassuring direction, each for
about a day** (`cbf3535`) — the board's lane guard, the quota breaker, the verify
gate. All three were repaired inside the window, the merge queue thawed after
~4 h dead, 12 branches merged, and the blocker moved from "a tool is broken" →
"a referee is absent" → "nine merge conflicts". Alongside it, three territories
delivered the same *class* of finding independently: theoria-arm (E14),
engine-rig (C11) and worldgen (V19) each found code that read a crash, an exit
code, or a missing dict key as a fact about the world, biased toward comfort.

1. **F-102 / T-47** — the 31-line `gates.py` fix that ended the stoppage ran for
   34 minutes while existing *only* in one machine's working tree. Local reflex
   and ci_merge execute the worktree, so the thaw was real but unreproducible,
   and the auditor had twice `--autostash`ed the only copy without knowing.
2. **F-103 / F-104** — six run directories dated **up to 18.7 h in the future**,
   two `MANIFEST.utc` fields copying the fabricated value, and the same drift in
   `ops-status`, in both new `PARTNER_SYNC` paragraphs and in inbox filenames.
   `board.py`'s new staleness check had to route around it by reading file mtime.
3. **F-113** — grepping engine-rig for held-out validation returns nothing, and
   `zero_space.verify` re-checks on the trajectory it was fitted to. "Verified",
   in several cells of the engine table, currently means "self-consistent on the
   data it was fitted to". Boarded as E17, unclaimed.

Counter-evidence worth the same weight: the quota breaker's **first real outage**
(session limit 21:39Z → auto-released 22:22:20Z, zero human actions, C-50), and
the sweep built for F-02 releasing four workers that outage killed (C-51).

## Could not determine

* **Day-1's content frontier is ~15:48Z, not 21:09Z.** Ten `DRIFT-*.md` reports
  (`1537Z` … `2107Z`) were committed *before* the cutoff and are cited by no row
  in `data/*.jsonl` — out of scope here, but a real gap: the merge-queue stall,
  "91 commits stranded" and "41 % of done never reached master" all live there.
* **Id collision.** A concurrent session is writing the day-1 gaps into this same
  directory (`human_actions.jsonl` 26 rows, `bus.jsonl` 111, `assembly_new.jsonl`
  16) and had already allocated **C-44 … C-49**. I moved mine to C-50 … C-57.
  Whoever appends must re-sequence; the two sets were produced without contact.
* Whether the six future-dated stamps were corrected — none backfilled by the end
  of the window, and no probe checks for it yet.
* `V19` (F-112, T-52) is **branch-only**: `23ec179` was not on master at 23:45Z.
* C-54 (E14's reconciliation = 0) and C-55 (worldgen's own negative control) are
  read from the delivering sessions' run records; I did not re-run either.
* No `INC-*` incident file was created in the window — the audit's `DRIFT-*.md`
  records are the only incident channel that fired.
