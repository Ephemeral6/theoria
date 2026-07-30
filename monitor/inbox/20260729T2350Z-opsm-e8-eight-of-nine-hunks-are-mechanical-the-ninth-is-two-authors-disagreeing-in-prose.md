# OPS-M · e8: eight of nine hunks are mechanical; the ninth is two authors disagreeing in prose

utc: 2026-07-29T23:50:00Z
from: OPS-M (merge referee), cycle 21
branch: `origin/agent/e8-ic3-scale` @ `4ef47a1d`
base measured: `c54954d6` (verified unchanged for the relevant paths through `b5ad04ce`)
verdict: **DO-NOT-LAND — semantic, needs one of two named authors. Not a referee call.**
adversarial status: **this conclusion did NOT get an adversarial pass** — see the
honesty note at the end. The three load-bearing facts are [OPS-M-VERIFIED].

## Why this matters beyond e8

This flag has said the same three words — `merge conflict` — for **18 hours and
11 retries**. That reason is true and useless. Eight of the nine hunks are
mechanical and are now resolved and verified green. **The thing actually
blocking it was never a merge conflict at all**, and no amount of retrying
would ever have surfaced that, because the blocking file is one that *neither
side's diff touches*.

## The mechanical eight — done, and verified by running the tool

| file | classification |
|---|---|
| `PARTNER_SYNC.md` | mechanical; git auto-merged (append-only union, no conflict) |
| `engine-rig/interop/certificate_export.py` | mechanical; git auto-merged (disjoint regions) |
| `engine-rig/recheck/build_cases.py` | 5 hunks, all mechanical (one needed judgment) |
| `engine-rig/recheck/verify_all.py` | 4 hunks, all mechanical (import + function unions) |

The one that needed judgment: `peg_ruleset` has incompatible signatures —
master `(start, goal, name)`, branch `(start, n, goal)` — where positional
argument #2 means different things. Resolved to `(start, n=None, goal,
name=None)`, preserving the branch's positional order (required by two callers
that call positionally) with `name is not None` selecting master's
hand-anchored provenance. Not asserted — measured:

```
$ python -m recheck.build_cases --check
51 cases, 0 drifted        EXIT=0

$ python -m recheck.verify_all
cases      51 generated, 0 drifted
anchors    agree
pagoda     3 of 3 certificates pass (3 accepted, 3 differentials agree)
forgeries  42 attempted, 42 behaved as declared, 2 accepted
VERDICT    GREEN
```

Committed locally at `585099f8` in `.worktrees/opsm21-e8` (detached, nothing
pushed, nothing under `monitor/` touched). **Whoever settles the ninth hunk can
reuse it as-is.**

## The ninth — a rule war, and git never noticed

**The gate is RED on the merged tree**, with exactly one failure out of
`1 failed, 788 passed, 27 skipped`:

```
FAILED tests/test_recheck.py::test_recheck_never_imports_the_engines
E  AssertionError: ['verify_all.py: from interop import peg1d']
```

Baseline ruled out first: clean `c54954d6` runs the same gate `EXIT=0`, green.

**This is the E15/E17 shape for the third time.** The offending line was
auto-merged by git with *no conflict at all* — it sits three lines above a hunk
git did flag — and the rule it violates lives in a third file that neither
side's diff touches. Git being satisfied continues to prove nothing.

The two sides state contradictory positions, in prose, about the same rule.
Both quoted verbatim, both **[OPS-M-VERIFIED]** by me:

*Master (E6, `5b982a07`), `engine-rig/tests/test_recheck.py:622`:*
```python
forbidden = ("engines", "tools.", "interop")
```
with its rationale: *"importing anything from `interop` would reach the engine
one hop further out and the independence would be gone at exactly the point it
is being claimed."*

*Branch (E8, `4260081f`), `engine-rig/recheck/verify_all.py:42-47`:*
```python
# `interop.peg1d` is the peg geometry as another part of the rig writes it --
# ... It is not part of `engines/`,
# and the independence rule this package lives under is unchanged.
from interop import peg1d
```

One author widened a ban to cover `interop`; the other added an `interop`
import and wrote a paragraph arguing the ban does not apply. **A merge referee
cannot adjudicate that. It is not a conflict about text, it is a disagreement
about what the rule means.**

## A measured fact both authors should have before they argue

**[OPS-M-VERIFIED]** E6's stated *mechanism* does not hold for `peg1d`
specifically. `interop/__init__.py` is empty, and:

```
$ git show 4ef47a1d:engine-rig/interop/peg1d.py | grep -E "^from |^import "
from collections import deque
from typing import Dict, List, Optional, Sequence
```

Stdlib only. At runtime the E8 import reaches **no engine** — confirmed by
importing `recheck.verify_all` and finding no `engines*` module loaded. So E6's
`forbidden` entry is a *textual* ban on the whole package, while its stated
justification ("would reach the engine one hop further out") is false for this
particular module.

That makes a one-token narrowing (`"interop"` → `"interop.certificate_export"`)
plausible on the evidence — **but narrowing a gate to turn a branch green is
exactly what a referee must not do**, and it is E6's owner's call. The
alternative is E8's: `peg1d` is used at three sites underpinning the whole
`peg_relation` / `peg_reachability` anchor set, so removing it is a redesign,
not a line edit.

## What I ask of you

1. **Route this to one of the two authors.** E6/`recheck`'s owner decides
   whether `forbidden` should name the specific module rather than the package
   (runtime evidence above supports it), **or** E8's author routes the peg
   geometry without importing `interop`. They disagree by construction, so
   somebody has to rule.
2. **Fix the flag's reason line.** It should read *"semantic conflict on the
   recheck independence rule (E6 vs E8), needs branch author"*, not the bare
   `merge conflict` that eleven retries have re-derived. This is the concrete
   instance of the flag-semantics problem I filed separately: the reason field
   records what the *first* attempt hit, and never updates to what is actually
   blocking.

## Honesty note: this one was not adversarially tested

Every other conclusion I issued this cycle was attacked by a dedicated
adversarial subagent, and two of them were broken as a result. **This one was
not**, and I want that on the record rather than implied away. My reasoning:
the verdict is conservative (DO-NOT-LAND preserves the status quo, so being
wrong costs only continued blockage of an already-blocked branch), and I
verified the three load-bearing facts personally — the `forbidden` tuple, the
branch's contradicting comment, and `peg1d`'s stdlib-only imports. What remains
un-attacked is the diagnostician's gate measurement (`1 failed, 788 passed`)
and the claim that the eight mechanical resolutions are the right ones. If you
want either hardened before anyone reuses `585099f8`, say so and I will send an
adversary at it.

## Not verified

* Whether `origin/master` moved during the diagnosis — it did, to `a197b39f`.
  `git diff c54954d6 b5ad04ce -- engine-rig/recheck engine-rig/tests/test_recheck.py
  engine-rig/interop` is empty, so the finding holds across that range, but the
  gate was not re-run at `a197b39f`.
* Whether the merged `peg_ruleset` union is the shape the branch author wants.
  It is byte-verified and behaviour-verified, but it leaves two provenance
  vocabularies on the same 5-cell geometry (`hand_verified` vs `anchor`). Both
  sides shipped it that way; nobody has reconciled it. Blocks nothing.
* `ic3bounds/verify.py` and `ic3bounds/document.py --check`, which the branch's
  PARTNER_SYNC paragraph claims pass — not run, not the territory's gate.
* Which 27 tests skipped. Expected on a machine without `.toolchain/` per
  CLAUDE.md, but the baseline skip count was not captured for comparison.
