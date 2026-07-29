# bus2-ablation-readonly — the read-only gate, and why it kept going red

`base_commit` dc9865a · branch `agent/bus2-ablation-readonly` · 2026-07-28T15:33:07Z

## What was wrong

The gate was intermittently RED with one stage red (`run_arm`), one assertion
red (`read-only`), and always the same evidence:

```
"upstream_files_changed": ["proxy/var/spend_gate.jsonl",
                           "proxy/var/spend_gate.jsonl.lock"]
```

`ablcore/pin.py` lists `proxy` in `UPSTREAM_TREES`, and `SKIP_DIRS` did not
exclude `var`, so `hash_tree()` hashed ~80 files under `proxy/var/` — the
fleet's shared runtime spend ledger, which a **different, concurrent session's**
proxy appends to every few seconds. `grep -rn spend_gate ablation-arm/` finds
nothing: this arm has never touched that file. The instrument was charging this
arm for another session's writes, and the arm's own `verify.sh` verdict followed
the instrument.

Two further defects were sitting on top of it.

**A denylist where attribution was needed.** A partial fix had been applied to
one of the two call sites — `tests/test_readonly.py` grew

```python
CONCURRENT = ("/var/", "/runs/", "/out/", "/artifacts/",
              ".jsonl", ".log", "state.json")
```

and filtered any change matching a token. `ablcore/pin.py` and `run_arm.py`
never got the equivalent, and the gate's red path goes through `run_arm.py`, so
the fix bought nothing for the reported symptom. Worse, it was not sound to
keep: measured against the live repo it masked **650 of 1973 files (32.9%)**
under the watched directories, **201 of them git-tracked** — including
`worldgen/out/**/GROUND_TRUTH.md`, `figures/out/{light,dark}/*`, and
`arc-recon/data/contamination_log.jsonl`, the pile-cut discipline record. It
masked deletions too. Its own comment described it as a tightening
(「收紧」); it was a loosening, applying the same amnesty to this arm's writes
as to everybody else's, with no attribution at all.

**The gate judged the wrong run.** `verify.py::_run_stages` ran `pytest`
*second*, before `run_arm`. So the suite validated the **previous**
invocation's `artifacts/`, and the gate could never see its own tests fail on
its own output. A red left on disk by run N was carried into run N+1's verdict.

## What changed

1. **`ablcore/pin.py`** — new `SKIP_PATHS = ("proxy/var",)`, pruned inside
   `hash_tree`'s `os.walk` by repo-relative posix path. Not a `SKIP_DIRS` entry:
   that set is bare directory *names*, so `"var"` would blanket-skip any
   directory called `var` in any upstream tree. `hash_tree` keeps its
   sorted-by-construction property and its `root` parameter. Measured against
   the main checkout: 556 files hashed before, 476 after, and every one of the
   80 dropped is under `proxy/var/`. `proxy/variants.py` and `proxy/variants/`
   are untouched — the match requires an exact segment boundary.

2. **`tests/test_readonly.py::test_a_full_run_writes_only_inside_this_arm`** —
   the denylist is gone, replaced by attribution. A child process (`-B`, so no
   `__pycache__` noise) puts the arm on `sys.path`, installs `sys.addaudithook`,
   runs `run_arm.run_all(["a0-base"])`, and prints a JSON write-set: `open` with
   a write mode or write flags, `os.remove`/`unlink`/`rmdir`/`mkdir`/`rename`/
   `replace`/`truncate`/`link`/`symlink`, the `shutil.*` mutators, and
   `subprocess.Popen`. A subprocess because an audit hook cannot be removed
   once installed and must not leak into the rest of the pytest session.

   The claim asserted: **no path under the repo, outside `ablation-arm/`, was
   written or deleted.** Paths outside the repo are allowed and the docstring
   says so — `exhibits/e2_a2.py` and `exhibits/e3_charitable.py` legitimately
   call `tempfile.mkdtemp`. The old docstring claimed "nothing outside", which
   was never what any version of the test measured.

   The snapshot diff stays as an independent backstop for what the hook cannot
   see (a C extension, a child process), with a **narrow named prefix** list —
   `("proxy/var/", "monitor/")` — and the incident named in the comment.

3. **`verify.py`** — stages reordered to `build_theory --check` → `run_arm` →
   `run_arm --twice` → `run_exhibits` → `pytest`, with a docstring saying why
   the order is load-bearing. Nothing depended on the old order: the three
   drivers compute their paths from their own `__file__`, and the suite re-runs
   the arm where it needs to.

4. **`tests/test_verify.py` — not edited.** Its three failing parametrizations
   were failing because `artifacts/run_all.json` on disk carried
   `upstream_unchanged=false` from the contaminated instrument; they assert an
   exact red set, so one spurious `read-only` red contaminated all three. Their
   expectations were correct. On regenerated artifacts all ten pass.

## Evidence

Reproduction of the actual flake, in this worktree: a writer appending to
`proxy/var/spend_gate.jsonl` and rewriting `.lock` every 50 ms while the arm
ran. `tests/test_readonly.py` 5 passed; `run_arm.py` reported
`upstream trees unchanged: True (468 files hashed)`. Before the fix this is the
exact condition that produced the red.

| check | result |
|---|---|
| `python -m pytest` (full suite) | 56 passed |
| `python -m pytest tests/test_verify.py` (alone) | 10 passed |
| `bash verify.sh` run 1 | exit 0, GREEN |
| `bash verify.sh` run 2 | exit 0, GREEN |

`artifacts/run_all.json` and `artifacts/verify.json` were regenerated by
`verify.sh` and are now mutually consistent: `upstream_unchanged: true`,
`upstream_files_changed: []`, `green: true`, no failed stages, no failed
assertions. Previously `verify.json` said red while `run_all.json` said green.

## What the new predicate can and cannot do

**Gained.** Concurrency cannot produce a false positive *by construction* —
another session's writes never pass through this interpreter, so no denylist is
needed to excuse them. It also catches two classes a snapshot diff structurally
cannot: write-then-restore, and delete-and-recreate with identical bytes. And
it names the write *and* the writer instead of reporting a bare hash delta.

**Holes that remain, stated rather than papered over.**

* A write from a C extension that bypasses CPython's audit events is invisible
  to the hook. The snapshot backstop is what covers it.
* A child process escapes the hook entirely. The test asserts none is spawned
  rather than trusting silence; if the arm ever legitimately needs one, the
  assertion message is where that has to be argued.
* The backstop excludes `monitor/` wholesale, and `monitor/` contains tracked
  files. That is a real gap in the *backstop* only — the audit hook covers
  `monitor/` completely, so a write there by this arm is still caught by the
  primary check.
* The attribution child runs one world (`a0-base`), not the exhibits. The
  exhibits' upstream surface is covered by
  `test_a_full_run_leaves_every_upstream_tree_byte_identical` and its
  `BLIND_SPOTS` hashing, which are unchanged.

## Adjacent finding, not fixed here

`cold-start-a0/certify/replay.py:103` records `"theory": os.path.relpath(theory_py)`
with no `start=`, so the field is **relative to the caller's cwd**. Artefacts
regenerated by `verify.sh` (cwd = repo root) record
`ablation-arm\artifacts\...`; artefacts regenerated by `python run_arm.py` from
inside the arm record `artifacts\...`. That is a byte-level determinism wart
that will make these files flap depending on how they were regenerated. It is
in the theory-compiler track's tree, so it is reported here and not touched.
