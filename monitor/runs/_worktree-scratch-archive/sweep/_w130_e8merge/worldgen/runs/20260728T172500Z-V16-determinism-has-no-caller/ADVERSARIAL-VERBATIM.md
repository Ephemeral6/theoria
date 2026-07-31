# Adversarial review — V16 determinism negative control — verbatim

**Provenance.** The reviewer was given a read-only tree and the harness blocked
it from writing a report file, so its text was returned to the coordinator
(RES-3) and never reached the implementer. The implementer declined to write
this file from a paraphrase — correctly, and for the second time tonight; V13's
implementer made the same refusal. Archived here verbatim by RES-3.

**What the implementer did instead of transcribing.** Every finding below was
**re-verified or re-measured** against the tree rather than copied: `classify()`
rebuilds at a single seed and reads the bytes to decide Class A vs B; the 25/30
figure was reproduced exactly and the 5/10 is an independent draw. The
reviewer's executable probes are committed under `adversarial/`. Read this file
as the state of the tree **before** the nine fixes, not as sign-off on them.

---

Note from the reviewer: the author's session was writing into the run directory
*while* I reviewed (`pytest.txt`, `stability_3x.txt`, `zero_caller_tripwire.md`,
`write_manifest.py` all appeared mid-pass).

---

## A. "The injected generators are really nondeterministic"

### 1. CONFIRMED — two of the four injections are not nondeterministic

`determinism_sandbox.py` claims flatly: *"Every injection here makes the same
code produce different bytes on different runs."* It does not. Two are **pure
deterministic functions of `PYTHONHASHSEED`** — run twice at the same fixed seed
they are byte-identical. I re-ran the author's own oracle with `seeds=("1","1")`:

```
$ python .../adversarial/probe7.py
mechanism_order  guaranteed=False  same-seed(1,1) differing=[]
hash_order_wide  guaranteed=False  same-seed(1,1) differing=[]
unseeded_rng     guaranteed=True   same-seed(1,1) differing=['coverage.json']
wall_clock       guaranteed=True   same-seed(1,1) differing=['coverage.json']
```

`CLAUDE.md` states the requirement as *"byte-reproducible for a fixed seed."*
Under the repo's own written definition, `mechanism_order` and `hash_order_wide`
**do not violate it**. They violate the gate's stronger unwritten definition
(identical across seeds too). The `guaranteed` flag concedes only the seed-luck
issue, not this one.

### 2. CONFIRMED — the "independent oracle" shares the gate's criterion

`divergent_artefacts` is independent in *implementation* (never calls
`check_determinism`, hashes files itself) but not in *criterion*: it hardcodes
`seeds=(PARENT_SEED, "271828")` — the exact pair the gate compares. So:

- It cannot fail while `test_gate_goes_red_on_injected_nondeterminism` passes,
  except through a bug in the gate's 5-line diff loop. It audits that loop, not
  the injections.
- It provably cannot distinguish "nondeterministic" from "deterministic function
  of the hash seed" — the distinction finding 1 turns on. Probe 7 is literally
  the same helper with the pair unhardcoded, and it answers correctly.

Also, the failure mode its docstring says it rules out ("an injection that
merely made the comparison build differ from the committed one") is **not
reachable in this sandbox at all**: `out/` is in `SKIP`, so there is no
committed artefact; `main` builds the A-side itself.

### 3. CONFIRMED — `PARENT_SEED = "1"` is load-bearing; the `mechanism_order` red is 5-in-6

`t3-latch-maze` binds 3 mechanisms → 6 set orders, roughly uniform over seeds
(200-seed census): `count_lock|switch_door|consumable` (271828's order) occurs
31/200. Whenever the parent seed lands there, the defect is invisible:

```
$ python .../adversarial/probe3.py
seed=1        order=count_lock|consumable|switch_door   rc=1 red=True  green=False
seed=4        order=count_lock|switch_door|consumable   rc=0 red=False green=True   <-- MISSED
seed=0/2/6/999/13/271827                                rc=1 red=True  green=False

$ python .../adversarial/probe6.py     # 30 consecutive seeds
{'RED-diff': 25, 'MISSED': 5, 'other-nonzero': 0}      # 16.7% = 1/6
```

The committed `weakening_table.md` prints `mechanism_order | none | **RED**` as
a determinate fact. It is a 5-in-6 outcome at a seed picked from the winning
branch. The prose discloses the shape ("reproducible rather than guaranteed");
the number appears nowhere and the table carries no caveat.

Structural aggravation — mechanism counts over the 20 catalogue worlds:
`{0: 1, 1: 11, 2: 4, 3: 4}`. Twelve worlds have ≤1 mechanism, where a `set`
reaching an output is **undetectable in principle**; four have exactly 2 (~1/2
miss per seed).

Stated fairly for the author: production runs `--check` over all 20 worlds at
once, so the joint miss probability is ~1e-4 and the *production* gate is fine.
The point is that the negative control is a single-world instance, materially
weaker than the gate it stands in for, and does not say so.

### 4. CONFIRMED — three of four injections never touch a generator

`hash_order_wide`, `unseeded_rng`, `wall_clock` are the same edit: hang a
`v16_probe` key off the dict `coverage_report` returns, which `build_world`
immediately `json.dumps`es into `coverage.json` — one of the six diffed files.
Nothing propagates. That is a test of the byte diff with a freshly planted
value, which is a smaller step from "changing a constant" than the docstring's
discipline #1 implies. Only `mechanism_order` must survive the pipeline — and it
is the probabilistic one. The 4×4 grid is 1 structural injection + 3 planted
values.

### 5. CONFIRMED — `mechanism_order`'s stated mechanism is false

Its `why` (reproduced **verbatim in the committed `weakening_table.md`**) says
"the variable layout, every `State.key()` and therefore **the whole trace** move
with the hash seed."

```
$ python .../adversarial/probe5.py
mechanism_order differing artefacts: ['ground_truth.json', 'GROUND_TRUTH.md', 'reversibility.json']
  -> raw_trace.jsonl moved? False
```

`raw_trace.jsonl`, `spec.json`, `coverage.json` are byte-identical. The trace
does not move. The author's own `weakening_table.console.txt` already shows the
three-artefact list; the prose was never reconciled with it.

### 6. CONFIRMED — a crashed comparison build *does* print the RED banner

`determinism_sandbox.py` L73-75: *"Asserting on this and not merely on a
non-zero exit is what separates 'the determinism gate fired' from 'the build
crashed'."* False. `check_determinism` returns `["the comparison build
failed:\n"+tail]` on a non-zero child (`build.py:251-253`), and `main` prints
that under `NOT DETERMINISTIC:`. I built a defect that raises only in the child
(PYTHONHASHSEED 271828):

```
$ python .../adversarial/probe5.py
crash-only: rc=1 banner=True named=[]
tail: [... 'RuntimeError: boom']
```

The test is nevertheless **sound**, because of its third assertion (`named`,
requiring `"differs between runs"`). But the documented reason is wrong — the
reader is told the wrong assertion does the work.

Knock-on, a live defect rather than a doc bug: `weakening_table.py:verdict()`
uses `red = proc.returncode != 0 and ds.RED_BANNER in out` with **no `named`
requirement**. The committed weakening table would score a crashed comparison
build as RED. It does not bite for these four injections, but the table's
classifier embodies exactly the confusion the sandbox's prose claims to have
excluded.

## B. "Constructively bound to go red"

### 7. NOT CONFIRMED — I tried every bypass in the brief and could not land one

- **`--check` branch really taken:** `into_default` is true (no `--into`); the
  clean sandbox prints the GREEN banner.
- **The subprocess imports the sandbox, not the checkout:**
  ```
  $ python .../adversarial/probe1.py
  BUILD FILE: C:\Users\...\Temp\v16-adv-ij5os43z\clean\worldgen\build.py
  OUT:        C:\Users\...\Temp\v16-adv-ij5os43z\clean\worldgen\out\worlds
  sys.path[0]:
  ```
  (`cwd=root` alone suffices; `PYTHONPATH` is belt-and-braces.)
- **Every red is a byte diff, never "the comparison build failed"** — probe2
  shows all four ending in `NOT DETERMINISTIC:` + named artefacts.
- **No build-gate failure ever pre-empts `--check`:** 30-seed sweep gave 0
  "other-nonzero".

### 8. CONFIRMED — the production `--check` path is never exercised

`verify.STAGES` runs `--check` with **no world ids**. That branch builds
mutants, writes descriptors, runs `mutation_gate_failures`, and adds
`INDEX.json` + `MUTATIONS.json` to the diff pairs. `build.py:266-268` says of
the latter: *"exactly the shape of artefact where a `set` reaching an output
would hide."* `run_gate(root, world)` always passes exactly one id, so `ids is
None` is never reached by any test. The two roster diffs the code's own comment
flags as risky, and the entire mutant half, are untested.

### 9. CONFIRMED — a committed table cell is a coin flip published as a fact

`unseeded_rng × size_only = **RED**`. `json.dumps(random.random())` has a
variable-length repr: `P(two draws same length) = 0.45828` over 200k pairs. Ten
reruns of that exact cell:

```
$ python .../adversarial/probe4.py
MISSED RED MISSED MISSED RED MISSED RED RED RED RED
summary: {'RED': 6, 'MISSED': 4}
```

Not a CI flake (not in `MUST_BE_MISSED`), but the committed artefact is not
reproducible. In a run whose subject is byte-determinism, `weakening_table.md`
also ends with `Elapsed 13.9 s.`

### 10. `test_verify_still_runs_the_determinism_gate` — meaningful but thin, and its premise undercuts the ticket

Not tautological (it would catch dropping `--check` from `verify.STAGES`), but
it pins a tuple literal. Nothing runs `verify.py` automatically — the author
says so himself in `zero_caller_tripwire.md:19`: *"it is a hand-run command."*
So the honest scoreboard after V16: automated executions of the real
`check_determinism` against the real catalogue are still **zero**; the 16 new
tests exercise a *copy* of the source in a temp dir. A legitimate demonstration
that the gate can fire — not the gate firing.

Minor: `stages = {label: ... }` collapses duplicate labels, so
`len(matching) == 1` could pass with two build stages sharing a label.

### 11. "Zero test callers" — CONFIRMED CORRECT, independently

I did not trust the author's tripwire. Mine is a pytest plugin that
monkeypatches the module attribute (no source edit):

```
$ V16_TRIP_LOG=... PYTHONPATH=.../adversarial python -m pytest worldgen/tests -q -p v16trip
428 passed, 13 skipped in 19.35s
=== trip log ===
(tripwire never fired)
```

Zero in-process callers, still zero after V16. The author's 412 baseline
reconciles: 412 + 16 = 428.

## C. Hygiene / flakiness

### 12. CONFIRMED CLEAN — nothing dirties the real tree

`git status --porcelain worldgen/` byte-identical before and after
`pytest worldgen/ -q`; all 231 files under `worldgen/out/` sha256-identical
before and after the suite and after all seven probes (~70 sandbox builds):
`files: 231 same set: True changed: []`. `OUT` inside the sandbox resolves into
the temp dir; `catalog/` (rewritten by `write_catalogue` under `into_default`)
stays inside the sandbox too.

### 13. Could not make the new tests flaky

Ambient `PYTHONHASHSEED` is irrelevant (`_env` pins both sides). `pytest-xdist`
is not installed. `core.autocrlf = true` on this machine, but
`worldgen/.gitattributes` pins `*.py text eol=lf` and both patch reads and
writes use `newline=""`, so the `\n`-anchored injections survive a Windows
checkout — and if they ever did not, `InjectionFailed` raises loudly rather than
no-opping. That discipline is real and it works. Cost: the suite goes 5.4s →
~19s (3.5x) for 16 tests.

---

**Verdict:** the control fires, and for the right reason — but it does not
establish what it claims: two of four "nondeterminisms" are seed-dependence that
satisfies the repo's own written determinism requirement, the "independent
oracle" hardcodes the gate's seed pair and provably cannot see that, the single
structural injection is a 5-in-6 outcome published as a fact, `RED_BANNER` does
not separate a caught defect from a crashed comparison build (and
`weakening_table.py`'s classifier is unsound for exactly that reason), and the
production `--check`-with-no-ids path — including the two roster diffs the
code's own comment flags as riskiest — is never run.
