# S20 — "19 gated" was never "19 gates known to work"

## The finding

A completion gate nobody has ever made fail on purpose is indistinguishable from
one that works. It is not evidence about the territory; it is evidence that
nothing has broken **yet**, and those two look identical right up until the day
they do not. Adopted from the audit's advice on S13, and the same line as drift
dimension 7: *does this check still have a negative sample that turns it red.*

**Baseline when this landed: 18 of 19 gated territories were decorative** — not
one gate in the repository declared a way to make it fail.

## Item 1 — the column, and why it is a declaration

A gate declares its negative sample on a line of its own:

```sh
# negative-sample: monitor/tests/test_probes_injection.py
```

`gates.py` reads it and **checks the declared path exists**, because otherwise
the cheapest way to clear the check is to declare a file nobody ever wrote —
which is the same shape as the defect being fixed. `gate_for()` gains
`negative_sample` and `decorative`; `survey()` reports `decorative` beside
`gated`, since those are two different claims and the survey only ever supported
the first.

**Declared, not sniffed.** Guessing from filenames — anything matching
`test_*negative*`, say — would let a gate acquire a negative sample because
somebody named an unrelated file well, and would miss every real one named
something else. A declaration is a claim its author can be held to.

`decorative` does **not** mean the gate is broken. It may check plenty. It means
nobody has shown it can go red.

## Item 3 — written into METHOD.md

The gate section gains the requirement and the current baseline, and the
ticket-tail line now says a negative sample is part of accepting a new gate: a
test that builds a failing world and requires the red, **plus a companion
green** — because "always reports red" satisfies the red half and is equally
useless.

## Item 2 — done for monitor only, and this is a scope boundary not an omission

The ticket asks for negative samples on five gates: exam, worldgen, proxy,
ablation-arm, monitor.

**Only `monitor` is delivered.** This item declares `territory: monitor`, and
the other four gates live in four other territories. Writing tests into them
would walk around the board's one-worker-per-territory guard — the same trade I
declined on `battery/verify.py` in S25 earlier today, for the same reason: the
guard is the only thing standing between two sessions editing the same file, and
stepping over it to finish my own ticket faster is precisely what this lane
exists to refuse.

`monitor/verify.sh` now declares `monitor/tests/test_probes_injection.py`, which
is a real negative sample: it manufactures a heartbeat from the future, a
never-started session, and other failing worlds, and requires the red. The
enforcer goes first — S13's whole finding was that a self-discipline clause is
not a mechanism, and the rig exempting itself would be that mistake one level up.

The remaining four are reported to the monitor for their owners. Each needs the
same two things: a test that makes that gate red on purpose, and one line in the
gate script pointing at it.

## Verification

* `python -m pytest monitor/tests -q` → all pass (2 xfail, pre-existing).
* `bash monitor/verify.sh` → **GREEN**, and monitor is no longer decorative.
* Seven new tests, including the two that matter: a declaration pointing at a
  file that does not exist must **not** count, and an ungated territory must not
  read as "not decorative".

## Caveat on what the column proves

It proves a gate *names* a negative sample that exists. It does not run it, and
it does not check that the named test actually exercises that gate — a
declaration pointing at a real but irrelevant test would pass. Closing that
means running the named test and requiring it to fail against a deliberately
broken gate, which is a second item's worth of work and is not claimed here.
