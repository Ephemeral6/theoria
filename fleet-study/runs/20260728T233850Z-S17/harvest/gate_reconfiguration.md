# Measured in-session: a territory's merge gate reconfigured itself by a file appearing

W-1641, 2026-07-28T23:5xZ. This one was measured directly rather than harvested,
so it is recorded here with the command that reproduces it.

## What was measured

`monitor/gates.py` derives each territory's completion gate **from the tree**
rather than from a hand-kept table (its own docstring gives the reason: the
hand-kept `TEST_CMDS` table went stale while 509 tests sat unrun, and the
hand-written repair got 4 of its 7 entries wrong in the same commit).

`verify.py` is one of the two canonical gate names. So:

```python
import sys; sys.path.insert(0, "monitor"); import gates
gates.gate_for(<root>, "fleet-study")
```

| tree | verdict |
|---|---|
| `master` (c3439767) | `{"kind": "none", … "why": "no verify script and no test_*.py — this territory merges with nothing checking it"}` |
| `agent/s17-fleet-evidence-capture` | `{"kind": "verify", "name": "verify.py", "canonical": true, "why": "the territory ships its own completion gate"}` |

**No configuration file was edited.** The gate changed because a file exists.

## Why this is the hot-reconfiguration evidence the record was missing

`data/README.md` records that A-03 (hot reconfiguration) was marked
`confidence: low` and **not measured** — the contract merely *asserts* that
editing one file changes the fleet's behaviour next cycle, and a system's
self-description is not a measurement.

This is the same mechanism, one layer down, and it *is* measurable: the merge
referee's behaviour toward this territory changes on the next tick, with no
edit to the referee. It is a weaker claim than the contract's (a gate lookup is
not an agent re-reading its instructions), but it is an observed behaviour
change rather than a stated one.

## What it does not prove

* It shows the gate *lookup* changes. It does not show a merge was actually
  blocked by the new gate — that will only be observable after this branch
  lands and some later fleet-study branch is refused.
* It is a property of `gates.py`'s design, deliberately built after an
  incident. It is not evidence that the fleet reconfigures itself *in general*.

## The thing it closes

`counterevidence.jsonl` C-36 records "the ungated set grew from 4 to 5" as a
caught over-claim about the monitor's own gate coverage. The ungated set on
master is currently `CONTRACTS, browser-ops, fleet-study, papers, release` (5).
When this branch merges it becomes 4 — and that is a check anyone can re-run:

```
python monitor/gates.py | grep UNGATED
```

## The cost side, same territory, same day

`monitor/ci/merge.log` records the other half of the story. The S17 branch was
flagged `touches unknown territory (needs M-0 judgment)` **63 times between
2026-07-28T16:08:55Z and 22:45:47Z — 6h37m** — before merging at 22:53:18Z.
(Counted with `grep -c 'FLAG origin/agent/s17-fleet-evidence-capture'`; the
first eyeball read 64, which is why the command is written down.)
The territory `fleet-study` had been issued *by the work board itself* (the S17
item carries `territory: fleet-study`), but the board does not validate the
territories it issues against `ci_merge.KNOWN_DIRS`. W-1630 reported the defect
at 21:35Z (`monitor/inbox/20260728T213500Z-W-1630-fleet-study-cannot-merge.md`);
the holder of the item, RES-4, died on session quota before it cleared.

When it did merge, it merged as
`gates: none; NO GATE, MERGED UNCHECKED: fleet-study` — one of 6 such lines in
`merge.log`, covering 5 territories (`browser-ops` ×2, `fleet-study` ×2 —
once alone and once alongside `papers`+`release` — `papers`, `verify-lab`).
So the same territory was, on the same day, both *too unknown to merge for six
and a half hours* and *merged without any check at all*.
