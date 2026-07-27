# ~~BLOCKER~~ · Fast Downward is connected (2026-07-28)

**Resolved.** Fast Downward is built and wired in. This file is kept as the
install record and the reproduction recipe, not as an open blocker.

```bash
cd cold-start-a0
export FAST_DOWNWARD="$PWD/.toolchain/downward/fast-downward.py"
export PATH="$PWD/.toolchain/mingw64/bin:$PATH"
python -m certify.fd_conformance      # exit 0
```

| instance | Fast Downward | bundled BFS | agree |
|---|---|---|---|
| `a0-base` | SAT, length **12** | SAT, length 12 | ✅ identical plan |
| `a0-no-button` | **UNSAT** — *"Completely explored state space — no solution!"* | UNSAT | ✅ |
| `a0p-base` | SAT, length **10** | SAT, length 10 | ✅ identical plan |

`artifacts/fd_real.json`. **No caller code changed** — setting `FAST_DOWNWARD`
was the entire integration, which is the claim `A0_REPORT.md` §7.4 asked to test.

The `a0-no-button` row is the one that matters: Fast Downward independently
*proves* the variant unsolvable, so the impossibility theorem of M5 and the
planner now agree rather than one of them being taken on trust.

---

## How it was installed

Option B from the original write-up — a no-installer zip, everything under the
gitignored `.toolchain/`, nothing touched system-wide.

```bash
cd cold-start-a0/.toolchain

# 1 · compiler: winlibs mingw-w64, gcc 16.1.0 ucrt posix seh (273 MB)
curl -sSL -o mingw.zip "https://github.com/brechtsanders/winlibs_mingw/releases/download/16.1.0posix-14.0.0-ucrt-r3/winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip"
unzip -q mingw.zip
export PATH="$PWD/mingw64/bin:/d/Miniforge3/Scripts:$PATH"

# 2 · build.  NOT via build.py -- see below.
cd downward
cmake -G Ninja -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -S src -B builds/release
cmake --build builds/release          # 235/235, ~90 s
```

**Why not `build.py`.** It hard-codes the generator by platform:

```python
elif os.name == "nt":
    CMAKE_GENERATOR = "NMake Makefiles"
```

`nmake` is MSVC's. With a mingw toolchain the configure step fails before it
starts, so CMake is invoked directly with the Ninja generator instead. The
output lands in `builds/release/bin/`, which is exactly where
`driver/util.py`'s `BUILDS_DIR / build / "bin"` looks, so `fast-downward.py`
finds it with no further configuration.

Contrary to the caveat in the original write-up, gcc 16.1.0 compiled Fast
Downward's sources clean — no warnings-as-errors, no patches. MSVC Build Tools
(option A) remains the upstream-documented route and is still the safer answer
if a future FD revision stops building under mingw.

Toolchain sizes, all gitignored: `mingw64/` ≈ 1.4 GB, `downward/` ≈ 5 MB source
plus ~40 MB of build output.

---

## Two defects the real planner found immediately

Both were invisible while only the bundled BFS ran, which is the argument for
connecting a second implementation at all.

### D-A0-019 — our PDDL was not standard-conformant

The generated domain declared

```
(:types buttoncell doorcell markedcell - cell)
```

and never introduced `cell` itself. `fd_adapter`'s parser is lenient — it just
records `child -> parent` and walks it — so the stub accepted this for the whole
sprint. Fast Downward's translator does not:

```
File ".../translate/pddl_to_prolog.py", line 146, in translate_typed_object
    supertypes = type_dict[obj.type_name].supertype_names
KeyError: 'cell'
```

Fixed in `compile/gen_pddl_a0.py`; the domain now emits

```
(:types cell - object
        buttoncell doorcell markedcell - cell)
```

**The stub had been masking a portability bug in our generator.** Any PDDL we
emitted before this point would have been rejected by any standards-conformant
planner.

### D-A0-020 — `fd_adapter` cannot say "proved unsolvable" on the FD path

**上游缺陷 (engine-rig).** The two backends spell unsolvability differently:

| backend | how it says "there is no plan" |
|---|---|
| bundled BFS | `RuntimeError("no plan exists for <problem>")` |
| Fast Downward | exit code **12**, no plan file → `RuntimeError("Fast Downward produced no plan file (exit 12): …")` |

The second is the *same* `RuntimeError` the adapter raises when FD genuinely
crashes, so a caller on the FD path cannot distinguish

* *the planner proved there is no plan* — the branch that under constraint 6
  triggers the certificate obligation and the whole M5 machinery, from
* *the planner fell over* — an incident.

That is precisely the distinction the unsolvability work exists to make, so it
cannot be left to an ad-hoc string match at each call site.
`certify/fd_unsat.py` owns the predicate here; `engine-rig` is not modified.
FD exit **13** (`SEARCH_UNSOLVED_INCOMPLETE`) is deliberately *not* treated as
UNSAT — it is "my search was incomplete and found nothing", which is not a proof.

**Suggested upstream fix:** `solve()` should return `None`, or raise a
distinguishable `NoPlanExists`, on exit 12 — matching what the stub already
means by its message.

---

## What is still not established

Scale. A0's instances are 36–38 arena cells; Fast Downward expands 53 states and
finishes in 2 ms. Whether the planner path holds up on a real ARC-sized problem
is a question these instances cannot answer either way, and connecting FD has not
changed that.

The reproducible pipeline (`run_all.py`, `prime.run_prime`) still calls
`solve(..., prefer="stub")` **on purpose**, so its checked-in artefacts stay
byte-identical whether or not a planner is installed. The Fast Downward
comparison is its own artefact, `artifacts/fd_real.json`, produced by
`certify/fd_conformance.py`.
