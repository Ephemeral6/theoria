# Proof that the probe's reds are about the probe

Two implanted trees and a green/red pair is the minimum, and V12 showed it is not
sufficient: a gate can go red for a reason that has nothing to do with the rule it
claims to enforce. So each planted red is replayed against a **deliberately
weakened probe**, and the claim is only earned if the weak version lets it
through.

`verify-lab/negctl/tests/test_probe.py` builds a synthetic tree containing
`newgate.py` — a manifest-hash checker with a `__main__` block and `return 1 if
problems else 0` — and varies only the tests beside it.

Observed, `notidle.stdout.txt`, reproducible with the script in this directory:

```
planted gap, shipped probe             -> exit 1   ['NEW_GAP']
planted gap, gating=(REGRESSION,)      -> exit 0   ['NEW_GAP']
name-only negctl, shipped probe        -> exit 1   ['NEW_GAP']
name-only negctl, detector=N           -> exit 0   ['NEW_OK']
positive controls only, shipped probe  -> exit 1   ['NEW_GAP']
real negative control, shipped probe   -> exit 0   ['NEW_OK']
```

| weakening | what it removes | planted defect | shipped | weakened |
|---|---|---|---|---|
| `GATING = (REGRESSION,)` | complains only when an existing negative control disappears | a new gate arrives with none | **exit 1** | exit 0 |
| `detector = N` | judges by the test function's *name* | `test_the_gate_rejects_a_bad_manifest_and_fails_loudly`, whose body asserts `isinstance(result, list)` | **exit 1** | exit 0 |
| re-pin the measurement | the pin is regenerated on every run instead of hand-kept | a pinned `present` loses its negative control | **exit 1** | exit 0 |

Each weakened version is a real design someone would reasonably propose — "only
complain about regressions, that's less annoying"; "just check there's a test with
a sensible name"; "regenerate the baseline automatically so nobody has to maintain
it" — and each is blind to exactly one of the three defects. The tests assert the
blindness, so if a future refactor makes the weak version catch the same red, the
suite fails and the strength being claimed here has to be re-argued.

## The probe's negative control found a defect in the probe, first run

The first version of `probe.can_exit_nonzero` looked for `ast.Constant` return
values and nothing else. `newgate.py` is written the way most of this repository
writes it — `return 1 if problems else 0` — so it was **not enumerated as an entry
point at all**, and the probe reported green on a tree containing a planted,
undemonstrated gate. Nine of the twenty-four tests failed on the first run and
named it.

`return 0 if <ok> else 1` is the dominant form here: `verify_c4.py:240`,
`transcribe_deadlock_certificates.py:120`, `run_matrix.py:328`,
`check_redlines.py:304`, `merge_ledger.py:91`, and a dozen more. Without the
negative control the probe would have shipped enumerating a fraction of the tree
and printing green — which is, precisely, the failure V11 was written to count.
The fix is `probe._returns_nonzero`; the entry-point count went from 128 to 141.

## What this does not prove

The implanted trees are synthetic. They demonstrate that the probe's *logic* is
load-bearing; they say nothing about whether the criterion's verdicts on the real
tree are right. That question is `CALIBRATION.md`'s, and its answer — a 30% false
alarm rate — is the one that limits what the probe should be used for.
