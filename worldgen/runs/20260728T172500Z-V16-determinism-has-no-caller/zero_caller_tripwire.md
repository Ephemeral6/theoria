# V16 step 1 — is `check_determinism` really uncalled?

V11's census and V14's adversarial pass both said *zero test callers*, both by
static scan. The ticket asked for a measurement instead, and allowed the answer
"the scan was wrong".

**It was not wrong about tests. It was incomplete about production.** There is
one caller chain, and it does not pass through any test:

```
worldgen/verify.py:42   ("catalogue build + determinism",
                         (sys.executable, "-m", "worldgen.build", "--check"), True)
        -> worldgen/build.py:main()          # argparse --check
        -> worldgen/build.py:344             #   check_determinism(ids)
```

`build.main` guards the call with `args.check and into_default`, so it fires
only when `--build --check` is run against the *default* out root. Nothing runs
`worldgen/verify.py` automatically: it is a hand-run command, and V12's
`test_verify_qc_gate.py` (which spawns `verify` for the QC stages) is on its own
branch, not on `master` — `git ls-tree master worldgen/tests/` at base commit
`91d3a86` lists eleven test files and none of them is it.

## The measurement

A tripwire was inserted as the first statement of `check_determinism` — it
appends to `$V16_TRIPWIRE` and then raises — and the suites were run. Any
caller, in-process or through a subprocess, would have turned something red:
an in-process caller gets the `AssertionError`, a subprocess caller gets a
non-zero exit from `python -m worldgen.build --check`.

```python
    # --- V16 TRIPWIRE (temporary, reverted before commit) ---
    _sentinel = os.environ.get("V16_TRIPWIRE")
    if _sentinel:
        with open(_sentinel, "a", encoding="utf-8") as _t:
            _t.write("check_determinism reached: argv=%r ids=%r pid=%d\n"
                     % (sys.argv, ids, os.getpid()))
    raise AssertionError("V16 TRIPWIRE: check_determinism was reached")
```

### baseline, no tripwire

```
$ python -m pytest worldgen/ -q
412 passed, 13 skipped in 5.37s
```

### with the tripwire installed

```
$ export V16_TRIPWIRE=".../tripwire.log"; rm -f "$V16_TRIPWIRE"
$ python -m pytest worldgen/ -q
412 passed, 13 skipped in 5.05s
worldgen_exit=0
$ ls -la "$V16_TRIPWIRE"
ls: cannot access '.../tripwire.log': No such file or directory
SENTINEL ABSENT -- never reached
```

The two other suites that mention `worldgen` at all
(`grep -rln worldgen --include=test_*.py` over the tree returns exactly
`exam/tests/test_worldgen_papers.py`, `theory-compiler/tests/test_count_guard.py`
and `worldgen/tests/*`):

```
$ python -m pytest exam/tests/test_worldgen_papers.py \
                   theory-compiler/tests/test_count_guard.py -q
110 passed in 12.13s
```

### the tripwire itself was alive

Otherwise the green above would mean nothing — the same failure mode this
whole ticket is about.

```
$ python -c "import worldgen.build as b; b.check_determinism(['t1-walk-maze'])"
RAISED: V16 TRIPWIRE: check_determinism was reached
$ cat "$V16_TRIPWIRE"
check_determinism reached: argv=['-c'] ids=['t1-walk-maze'] pid=2668
```

The tripwire was then reverted (`worldgen/build.py` is byte-identical to
`91d3a86`; `git status worldgen/` clean apart from this run directory and the
two new test files).

## Verdict

**The premise holds.** 522 tests across three suites, none of which reaches the
repository's strongest determinism claim, in-process or by subprocess. The one
thing the static scans missed is that the function is not dead code in
production — `worldgen/verify.py` gates on it — which is why
`test_determinism_gate.py` also pins that wiring: if the `--check` flag is ever
dropped from `verify.STAGES`, the gate becomes unreachable everywhere at once
and no other test would notice.
