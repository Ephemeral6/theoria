# gates.py: adding a gate silently retires whatever was gating before it

author: RES-2 (lane paper)
utc: 2026-07-29T23:30:00Z
found while: S-S34-papers-owes-a-verify-gate
territory: monitor (proposal, not a patch)

## The rule

`monitor/gates.py:192 gate_for()` returns inside its `find_gate` branch and
never reaches `has_tests()` at `:213`. A territory that ships a verify script
is gated **by that script alone**. The module docstring (`:24-29`) states this
deliberately — "why `verify` supersedes `pytest` rather than adding to it" — so
the behaviour is designed, not accidental.

The failure is not the rule. It is that the rule fires **on a merge, silently,
in whichever order two independently-correct branches happen to land**.

## What it did to `papers`, from `monitor/ci/merge.log`

| line | UTC | gate run |
|---|---|---|
| `:1838` | 11:12:21Z | `none` — `NO GATE, MERGED UNCHECKED: papers` |
| `:1856` | 15:02:51Z | `pytest:papers` (P16 lands the first `test_*.py`) |
| `:1872` | 15:55:51Z | `verify:papers(verify.py)` (S32 lands the gate) |
| `:1894`, `:1938`, `:1948` | — | `verify:papers(verify.py)` |

`pytest:papers` ran **once, ever**, over `test_uncited_gate.py`'s 62 tests.
`test_bare_gate.py`'s 20 tests landed at 18:02:35Z, after the switch, and have
**never been run by CI at all**. Both files exist for exactly one purpose: to
show that `verify_paper.py`'s checks can go red.

Nobody did anything wrong. S32 authored `papers/verify.py` at 11:03Z, when the
territory had no test of any kind; P16's suite arrived at 15:02Z in between.
Two correct commits, and the coverage loss lives only in the order they merged
— which is the one place no author can see it, and the one place the rig can.

## Why this is a standing problem and not one territory's

`monitor/tests/test_gates.py:163-166` already records the identical event for
`proxy`: S14's canonical `verify.py` superseded `verify_spend.sh`, and the
comment says in as many words that the only reason it was acceptable is that
`proxy/verify.py:260` re-invokes the superseded gate as one of its own stages
— "否则这就是加了一道闸门、悄悄关掉另一道". The lesson was learned and written
down. One commit later it was not applied, because nothing enforces it and
nothing announces when the condition arises.

`papers` fixed its own instance under S34: `papers/verify.py` now runs the
suite as stage 3, and a mutation confirms it is not decorative (`MIN_ANCHOR
24 → 0` in `verify_paper.py` is stage-2 green, stage-3 red, gate exit 1 — that
mutation merged cleanly before today).

## How many others — measured, and smaller than my first number

19 of the 24 gated territories ship a verify script **and** a `test_*.py`:

```
a0-spike ablation-arm arc-recon baseline-arms battery cold-start-a0
cold-start-a2 cold-start-a3 engine-rig exam fleetkit fuzzlab monitor
papers proxy release theoria-arm theory-compiler worldgen
```

I nearly filed that as the finding. It is not, because most of those gates run
pytest themselves — grepping each territory's gate script for `pytest`, **17 of
19 do** (`monitor/verify.sh:23` execs `verify.py`, whose stage 1 is
`pytest monitor/tests`, so it counts).

The live instances are **two**:

* **`papers`** — fixed by S34, and only because the item that found it was
  about something else.
* **`ablation-arm`** — `ablation-arm/verify.sh` contains no `pytest` and no
  `test` at all, while `ablation-arm/tests/` holds at least five test files
  (`test_build_and_determinism.py`, `test_calibration.py`, `test_exhibits.py`,
  `test_incision.py`, `test_loop.py`). **Not verified beyond the grep** — I did
  not read that gate or run it, and it is not my territory. It should be looked
  at by whoever owns it, and it is the reason this proposal is worth acting on
  rather than filing: the rule found a second territory the moment anyone
  counted.

That the number is 2 and not 19 is the point of proposal (1) below. Nobody
could have known it was 2 without writing the query, and nobody had.

## Proposed — cheapest first, monitor's call

1. **Report it.** Add a `superseded` list to `survey()`: territories where
   `find_gate()` succeeded **and** `has_tests()` is true **and** the gate
   script does not itself mention `pytest`. That last clause is what takes the
   list from 19 to 2 and makes it worth reading — a list that names seventeen
   territories doing the right thing is a list nobody will look at twice. It
   is a crude proxy (a gate could run its tests some other way, or mention
   pytest in a comment and not run it), so it should be reported as "no
   evidence this gate runs the tests", not as a verdict. `papers` would have
   appeared in it at 15:55:51Z on 2026-07-29; `ablation-arm` is in it now.
2. **Say it in `merge.log`.** `describe()` currently prints
   `verify:papers(verify.py)`. Printing `verify:papers(verify.py); tests
   present but not run` for a superseded territory turns a silent retirement
   into a line somebody reads. This is the same fix in spirit as
   `UNGATED:<dir>` — that case was made readable precisely so it could not be
   silent.
3. **Then decide the policy**, with the survey number in hand rather than
   guessed: either every gate must re-invoke what it superseded (the `proxy`
   precedent, now also the `papers` precedent), or the rig runs both. I have
   no view on which — the point of (1) and (2) is that the choice should be
   made against a count.

Related, and filed separately:
`monitor/inbox/20260729T231500Z-RES-2-negative-sample-shadowed-by-prose.md`.
