# RUN_STATE — board hygiene, 2026-08-04

**Territory** monitor · **Branch** `q/board-hygiene` · **Base** master
`4846e66dee64940b3bb457b408db13775728915c` · **UTC** 2026-08-04T13:00Z ·
**Spend** $0.00, 0 API calls, 0 model calls, no network, zero sealed-pile
contact, no credential read.

The task was to keep the queue true while seven agents and a live experiment
change the tree under it. Nothing here is a fix; everything here is either a
measurement of the board against master or an item filed from one.

## The headline, and it is not the one the brief expected

**Seven deliveries landed on master today and not one of them closes a board
item.** Every one is real, large and mostly right — several are better than
the item that provoked them, and two contradicted their brief and were right
to. But each stopped at the seam where its item's acceptance clause begins,
and the acceptance clauses are all the same shape: *put the number where the
next reader will find it.*

| delivery (merge) | item it answers | verdict |
|---|---|---|
| `83f2d8d0` w/a25-action-economy | **A30** | measurement done; `probe_share`, the probe-budget knob and the `spec.py` correction all absent |
| `3a1ee035` w/a27-level-boundary | **A31** | second witness delivered, one premise refuted; `round.py:188`'s `or 0` untouched |
| `b27dd1e2` w/a28-baseline-zero | **A33** | checker done, in-suite; the sentence it refutes is verbatim on `spec.py:525` |
| `366174bc` w/r2b-desk-cost | **A32** | both candidate causes refuted, third found; the two `round.json` columns absent |
| `ceedfaf0` w/exam-class-ii-count | **V31** | the premise "never counted" is now false; the worldgen ticket V31 exists to file is still not filed |
| `421dbdc6` w/freeze-d1 | (none) | U3's D1/D2 were already closed on 2026-08-01 — no board item ever tracked them |
| `f2ac464e` w/monitor-board-blocker | (filed A30–A34, S49, V31) | this morning's filing, reconciled here |

Two further things the brief listed as delivered are not board items at all and
were reconciled in place: the generated frontier (A22, reconciled 2026-08-02 —
`round.json.prediction` is still `null` on both rounds, and `round.py` has no
such field, so A22 stays open on exactly the scope it was narrowed to) and the
anchor work (A23, in `done/` since 2026-08-02T12:07:20Z).

## What was reconciled, with the evidence in the close

Six items got a dated `## 对账 2026-08-04` section appended (the board's own
idiom — A22 shows it). None was closed, because none is done; each was
**narrowed** to the residue, so the next claimant does not redo the delivered
half. The recomputations behind them:

```
$ grep -n "levels_completed" theoria-arm/armtools/round.py
104:        "levels_completed": levels.get("levels_completed"),
188:  "levels_completed": sum((l.get("levels_completed") or 0) for l in legs),

$ grep -n "probe_share|reserve_for_probes|usd_per_desk_call|usd_per_action|prediction" \
      theoria-arm/armtools/round.py
(no output)

$ grep -c "46 条基线臂 run" monitor/spec.py
1

$ find theoria-arm/runs -name levels.jsonl | wc -l ; \
  find theoria-arm/runs -name levels.jsonl -size +0 | wc -l
22
0
```

and A29's two named tests, re-run on a clean worktree of `4846e66d`:

```
FAILED tests/test_arm.py::test_the_archive_stays_accountable
FAILED tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive
E   AssertionError: claude-opus-5: ceiling $15.00 is below $18.7391
```

A29's own text says `$12.00` against `$13.4480`. **Both ends moved and the gap
widened from $1.45 to $3.74** while the item sat unclaimed. Recorded on the
item so the next claimant does not fix yesterday's number.

## What was filed, and why each one traces to a measurement

* **A35** (theoria-arm) — `levels.jsonl` has exactly one writer,
  `inner/loop.py:1989`, mode `"w"`, in `_save_all` at the end of the leg.
  Boundary events sit in memory until then. Two live legs have already died
  in flight (`loop.py:1951`'s own docstring names them), and A27's delivery
  wrote the *opposite* rule for its new `witnessed_wins.json` — recognised the
  hazard, left the old path alone. 22 files, 0 non-empty: the cheapest moment
  this will ever be fixable.
* **A36** (theoria-arm) — the desk-waste share, straight off the A25 delivery:
  24/73 zero-gap adjudications cost **$42.40** (28%), 31/104 repair
  invocations **$32.53** (22%), together **$74.93 of $148.89 = 50.3%**. The
  measurement landed with tests; moving the gate inside the `while` loop did
  not, and no item asks for it.
* **S51** (freeze) — the ceiling raise and what it obliges. Answering the
  brief's question directly: **no, the balance is not still negative under the
  new ceiling — but the published one is, because the table has not been
  regenerated.** `700 − 250.0687 = +449.9313` measured, `+445.9214` nominal,
  actions remaining `14510 → 30510`. And the hold on freeze item 12 comes off
  *arithmetically* while item 12 stays `blocked` on its own unrelated reason
  (three of `Theoria.md:377`'s numbers are still `⟨…⟩`). The item's first
  negative control is exactly that: a regeneration that reads only the hold
  flag would flip item 12 to ready on the strength of a budget change that has
  nothing to do with why it is blocked.
* **S52** (monitor) — the inbox. See below.

## The inbox: worse, and worse in a way the morning count could not see

`monitor/inbox_recon.py` (this run's only new instrument, 7 tests including
three negative controls) on master `4846e66d`:

```
open asks 235 · archived 37 · addressed by name 10 · no addressee 225
cited elsewhere 225 · uncited 10
seen by addressee 1 · NOT seen by it 9 · no addressee named 225
```

The morning's hand count was 21 files, 11 unseen. By the same yardstick — did
the addressee's own territory ever name the file — today is **9 of 10 unseen**.
Four are piled at theoria-arm's door, three at exam's. The one that got through
is `20260801T0400Z-exam-to-freeze-u3-vacuous-label.md`.

The heavier number is the other one: **225 of 235 open asks carry no addressee
in the filename at all.** They are not being ignored; there is nobody who could
ignore them. They are recorded as `None`, never `False` — an ask nobody was
named on cannot have been failed by its addressee, and a `False` there would
manufacture nine negligent territories out of a naming convention.

**The tool measures citation, not reading, and it overcounts unseen by
construction.** Today supplies its own counter-example, which is why it is
written into the item rather than hidden: battery's
`20260731T1731Z-...-curves-shortfall.md` reads UNSEEN, and yet
`theoria-arm/armtools/curves.py` commit `82e8e25e` (2026-08-01) is titled *the
turn that died in flight took the leg's most expensive call with it* — the arm
fixed it and never cited the letter. That is not a defect in the tool. It is
the defect being measured: **battery still has no way to know.**

Is the mechanism still a drop box nobody sweeps? Yes. What would change it is
in S52 and only the third of the three is mechanism: put
`unseen_by_addressee` and the age of the oldest unseen ask into `scan.py`'s
regular sweep, so a backlog opens a board item by itself. The first two
(addressee mandatory in the filename; a citation in your own territory *is* the
receipt) only make it measurable. S45 is the clinical sample: exam handed
freeze the 9.15/9.16 implementation with the commands on 2026-08-01T00:00Z and
the whole freeze queue has been stopped behind it since, because the only thing
that carried that letter was somebody happening to read it.

## Honest residue

* **Nothing was closed.** If the expectation was closes, the evidence did not
  support any. Six narrowings and four filings is what the tree actually says.
* **A24 and A33 are claimed in the main tree right now** (`W-9202`, `W-9207`,
  uncommitted). A24 was not touched. A33's reconciliation section says so and
  scopes itself to not collide; if W-9207 is doing the `spec.py` correction,
  that section closes with their delivery.
* **The main tree is mid-merge with `UU monitor/spec.py`.** Nothing here edits
  `spec.py`; the register #14 correction is A34's, and three separate items now
  point at that one sentence. Whoever moves first writes it and the other two
  cite it — two versions of that sentence would be worse than the wrong one.
* **`seen_by_addressee` is an approximation with a known direction.** It cannot
  see a territory that read an ask, agreed, and fixed the code silently. The
  count is an upper bound on asks that went nowhere and is labelled as one
  everywhere it is printed.
* **The 21/11 figure from this morning could not be reproduced** — it was
  produced by reading and no artefact of it is on disk. This run does not claim
  to have recomputed it; it states its own population and yardstick and reports
  the direction. That is the whole reason the instrument exists.
