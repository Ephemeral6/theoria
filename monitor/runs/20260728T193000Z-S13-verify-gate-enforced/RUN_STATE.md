# S13-verify-gate-enforced — RUN_STATE

Worker RES-1, lane `campaign`, territory `monitor`, branch
`agent/s13-verify-gate-enforced` off `d751ccd`.

## The item's three asks, and what each became

| ask | done |
|---|---|
| (1) `ci_merge` runs a territory's gate before merging; prints explicitly when there is none | **yes** — via `gates.py`, and `merge.log` now carries `NO GATE, MERGED UNCHECKED: <territory>` plus `a gate dirtied the worktree: <files>` |
| (2) add a minimal gate to every ungated territory | **partly, and deliberately** — `monitor`'s own gate is built; the remaining four are proposed per-territory in `monitor/inbox/` rather than written into other people's territories |
| (3) ticket template says "create one if the territory has none"; the probe separates the two diseases | **yes** — `METHOD.md` row 2 and a new §收工闸门; the probe now reports `risk` and `amber` for different things |

### Why (2) is a proposal and not four files

The item's `territory` is `monitor`. Adding gates to `CONTRACTS`, `browser-ops`,
`papers` and `release` means writing into territories this item does not own —
and `release` is claimed by `RES-2` right now. The board's territory exclusivity
is the conflict guard, and reaching across it is exactly what it exists to
prevent. So the **mechanism** is built to completion here and the four are handed
to the monitor as one item each, with a one-line spec apiece
(`monitor/inbox/20260728T194500Z-RES-1-four-territories-still-ungated.md`).

No generator was written either. A skeleton emitted for nobody to run is the
same disease S13 is about.

## What the survey actually found

The item's premise was stale in three ways at once, and the corrected numbers
are the useful part:

```
before:  21 territories -- 7 gated, 9 tests-only, 5 UNGATED
after:   21 territories -- 8 gated, 9 tests-only, 4 UNGATED
```

* the item says *"ten territories, only three have a real gate
  (exam/worldgen/proxy)"*. Seven already did — `ablation-arm`, `arc-recon`,
  `exam`, `figures`, `fuzzlab`, `proxy`, `worldgen`;
* `proxy`'s is `verify_spend.sh`, a **non-canonical name**. A matcher knowing
  only the two canonical names would have called `proxy` ungated — false,
  confident, and exactly the sort of report that gets a probe switched off;
* nine territories have no verify script but do have a test suite, so they are
  gated by pytest. Counting them as ungated overstates the exposure by more
  than double. **Four territories genuinely merge with nothing checking them.**
* the item also says A4a claimed a `ablation-arm/verify.sh` it never built.
  True when the item was written; A4a has since delivered and the file is on
  the tree and green.

## The three defects this item found in `monitor` itself

`monitor` was **ungated and had zero tests**. The rig that decides whether
everyone else's gate ran was the one place in the repository where a defect
could hide from every check — and one was hiding there.

1. **The board panel was silently empty.** `subprocess.run(..., text=True)`
   decodes with the locale codec, which on this machine is GBK, and the board
   listing is UTF-8 Chinese. The decode threw inside a reader thread and the
   panel rendered blank. A blank panel looks like an empty board. Six call
   sites fixed with `encoding="utf-8", errors="replace"`.
2. **`scan.build` wrote three files into `monitor/` unconditionally**, so this
   territory's gate could not run a real scan without dirtying the tree it was
   gating. `build(out_dir=…)` now redirects `state.json`, `index.html` and
   `history.jsonl`; the gate writes into a `mkdtemp` and the workspace is
   untouched. This is the item's own warning, made executable.
3. **The probe false-positived on this item's own ticket text.** The sentence
   *若该领地存在 `verify.sh`/`verify.py` 就必须跑它* was read as a claim that a
   file named `verify.sh/verify.py` exists. The matcher now requires the first
   path component to be a real territory. A checker that cries wolf is a checker
   that gets switched off, and a switched-off checker and an absent one are the
   same thing.

## The design call worth reading

**`gates.py` is the single source of truth, and both callers read it.**
`ci_merge` and `scan.probe_verify_gates` need the same answer to "what is this
territory's gate", and two implementations drift. This repository has already
paid for that once: `ci_merge`'s hand-maintained table went stale while 509
tests sat unrun, and the hand-written repair got four of its seven entries wrong
in the same commit. Its own comment draws the conclusion — *ask the tree* — and
this is where the tree gets asked, once.

**`verify` supersedes `pytest` rather than adding to it.** Every gate in this
repo already runs its own suite as its first stage, so running both would double
the slowest part of a merge to re-check what the gate just checked. A merge rig
that is slow gets bypassed.

**An ungated territory still merges.** Refusing would stop the repository dead.
Making the openness *visible* is the fix — one line, every time, in the log.

## Tests and the gate

```
monitor/tests            20 passed   (there were none)
bash monitor/verify.sh   GREEN       tests + one real scan + artifact fields
```

The gate's third stage checks the field that was silently empty: `state.json`
must carry a non-empty `board.listing`, because that is the exact shape the GBK
bug produced — the page renders and the panel is simply blank.

## Gaps

1. **Four territories still ungated** — proposed, not built, for the territory
   reason above.
2. **`ci_merge`'s new paths are tested at the source level, not by merging.**
   `test_ci_merge_still_refuses_a_red_verify_gate` asserts the strings exist in
   the file; proving the behaviour would mean driving a real merge, which needs
   a scratch remote. The log-line shape is assembled and asserted the way
   `try_merge` assembles it, which is closer but still not the rig itself.
3. **`CONTRACTS` may not deserve a gate at all** — it is frozen documents. The
   inbox note proposes a hash check rather than assuming a test suite belongs
   there, but that is a judgement for whoever owns it.
