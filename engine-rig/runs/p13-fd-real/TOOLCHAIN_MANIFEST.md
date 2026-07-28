# P-13 — Fast Downward, really built, on this Windows machine

Status: **built and planning.** Fast Downward 24.06+ (rev `7120aa0`) compiles clean
with winlibs GCC 16.1.0 and plans on the rig's own PDDL instance. The BFS stub is
no longer the only option; `engines/fd_adapter` drives the real planner as soon as
`FAST_DOWNWARD` is exported.

Date: 2026-07-28. Host: Windows 11 Home China 10.0.26200, x86-64.
Worktree: `C:\Users\user\Desktop\theoria-p13` (branch `agent/p13-fd-real`).

## The one line another agent needs

```bash
export FAST_DOWNWARD="C:/Users/user/Desktop/theoria-p13/engine-rig/.toolchain/downward/fast-downward.py"
```

Point it at the **driver** (`fast-downward.py`), not at `downward.exe`. The adapter's
`has_driver()` keys the satisficing rung on the basename starting with
`fast-downward`; given the bare binary it would silently fall back off LAMA,
because only the driver understands `--alias`.

Nothing needs to be added to `PATH` — see "The one real defect" below for why that
took a static link to become true.

## Artifacts

### 1. Compiler — winlibs mingw-w64, GCC 16.1.0

| | |
|---|---|
| Source URL | `https://github.com/brechtsanders/winlibs_mingw/releases/download/16.1.0posix-14.0.0-ucrt-r3/winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip` |
| Version | GCC 16.1.0 + MinGW-w64 14.0.0, UCRT runtime, POSIX threads, SEH, release 3 |
| Download size | 272,687,771 bytes |
| sha256 | `4273565109cd8ab8ecef1b0dc2a56fd7f5c7ee0885840a1c011b9325160ec0c3` |
| Install path | `engine-rig/.toolchain/mingw64/` (958,223,579 bytes unpacked) |
| Provenance | **First-hand.** Downloaded directly from the upstream release in this session. |

The checksum was verified against upstream's own published
`…-r3.zip.sha256` companion asset, fetched from the same release:

```
4273565109cd8ab8ecef1b0dc2a56fd7f5c7ee0885840a1c011b9325160ec0c3  winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip
```

It also matches, byte for byte, the copy the sibling `cold-start-a0` track already
had on disk — independent corroboration that both tracks are on the same compiler.
The fallback permitted by the task brief (copying the sibling tree) was **not**
needed and was not used.

Two notes on how this was obtained, since they will bite whoever repeats it:

* `winlibs.com` does not resolve from this host (`Could not resolve host: winlibs.com`),
  so the human-facing download page is unreachable. The GitHub release assets are.
* The GitHub **API** is rate-limited from this host
  (`API rate limit exceeded for 45.123.193.234`), so the release cannot be
  enumerated programmatically. Asset *downloads* do not go through the API and
  work fine — construct the URL from the tag `16.1.0posix-14.0.0-ucrt-r3` and the
  filename directly, as above.

The `.zip` was deleted after unpacking: this volume is at 99% capacity (~5 GB free)
and the URL plus sha256 above are enough to re-acquire and re-verify it.

### 2. Planner — Fast Downward

| | |
|---|---|
| Source URL | `https://github.com/aibasel/downward.git` (shallow clone, depth 1) |
| Commit | `7120aa01704bfe8e3b9b92c062a4f775bc89c7bd` |
| Commit date | 2026-07-27T13:52:23+02:00 |
| Subject | `[issue1223] Document translator options on the Fast Downward website.` |
| Reported version | `Fast Downward 24.06+`, `git revision [release]: 7120aa0` |
| Install path | `engine-rig/.toolchain/downward/` |

The working tree is **unmodified** — `git status` in the clone is clean. No patches
were needed to compile, and none were left behind. (Two files were temporarily
instrumented with `fprintf` markers while diagnosing the defect below; both were
restored from backup before the final build, and the clean tree is the evidence.)

### 3. Built binary

| | |
|---|---|
| Path | `engine-rig/.toolchain/downward/builds/release/bin/downward.exe` |
| Size | 280,538,976 bytes (large because FD's Release adds `-g`) |
| sha256 | `645671ae40d825478a043a9f94c856dc6130a11c166b3393837c153c5020aee1` |
| Translator | `engine-rig/.toolchain/downward/builds/release/bin/translate/` (Python, copied in by the build) |

## Build

`build.py` was **not** used, exactly as the brief warned: under `os.name == "nt"` it
hardcodes the `NMake Makefiles` generator and demands MSVC. Driving CMake directly
puts the binaries where `driver/util.py` looks for them (`builds/release/bin/`)
with no other adjustment.

```bash
export PATH="C:/Users/user/Desktop/theoria-p13/engine-rig/.toolchain/mingw64/bin:$PATH"
cd C:/Users/user/Desktop/theoria-p13/engine-rig/.toolchain/downward

cmake -G Ninja -S src -B builds/release -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=".../.toolchain/mingw64/bin/gcc.exe" \
  -DCMAKE_CXX_COMPILER=".../.toolchain/mingw64/bin/g++.exe" \
  -DCMAKE_EXE_LINKER_FLAGS="-static"

cmake --build builds/release
```

235 targets, **61.8 s**, zero warnings-as-errors, zero patches. Effective compile
flags, from `builds/release/build.ninja`:

```
-O3 -DNDEBUG -O3 -g -DNDEBUG -fomit-frame-pointer -Wall -Wextra -Wpedantic
-Wnon-virtual-dtor -Wfloat-conversion -Wmissing-declarations
-Wzero-as-null-pointer-constant
```

### Tool versions actually used

Beware: **winlibs ships its own cmake and ninja**, and putting `mingw64/bin` at the
front of `PATH` — which the build requires — shadows the Miniforge ones. The build
above therefore used the winlibs pair, not what a bare `cmake --version` reports.

| Tool | Version used | Path |
|---|---|---|
| g++ | 16.1.0 (`MinGW-W64 x86_64-ucrt-posix-seh, built by Brecht Sanders, r3`) | `.toolchain/mingw64/bin/g++.exe` |
| cmake | **4.3.3** | `.toolchain/mingw64/bin/cmake` |
| ninja | **1.13.2** | `.toolchain/mingw64/bin/ninja` |
| python | 3.13.13 | `D:\Miniforge3\python.exe` |

For contrast, without `mingw64/bin` on `PATH` the same commands would have used
Miniforge's cmake 4.4.0 and ninja 1.13.0 from `D:\Miniforge3\Scripts`. Either pair
works; this records which one produced the binary hashed above.

## The one real defect, and why `-static` is load-bearing

The first build — the plain recipe, no linker flags — compiled and searched
correctly but **segfaulted while writing the plan file**, deterministically, 15 runs
out of 15:

```
[t=0.002456s, 2820 KB] Actual search time: 0.000084s
Peak memory: 2832 KB
caught signal 11 -- exiting
```

Exit code 3, no `sas_plan` produced, and the driver then died on its own assertion:

```
AssertionError: got returncode < 10: 3
```

Diagnosis, in the order it actually came out:

* The unsolvable instance was **fine** (exit 12). Only the solution-found path died,
  which puts the fault in `PlanManager::save_plan`.
* The plan file was never even created, so the fault is at or before the
  `ofstream outfile(filename.str())` construction.
* Under gdb it never reproduced — not with the Windows debug heap disabled
  (`_NO_DEBUG_HEAP=1`) either.
* A `-O0` Debug build crashed identically, which rules out an optimiser bug and
  rules out `-fomit-frame-pointer`.
* The actual correlation was **`PATH`**: every run that worked had
  `.toolchain/mingw64/bin` exported; every run that crashed did not. gdb only
  "fixed" it because I had exported `PATH` in those invocations.

Root cause: the dynamically linked binary imported `libstdc++-6.dll` and
`libgcc_s_seh-1.dll`, and Git Bash puts `/mingw64/bin` —
`C:\Program Files\Git\mingw64\bin`, **Git for Windows' own bundled GCC runtime** —
at the very front of `PATH`. That older, ABI-incompatible `libstdc++-6.dll`
(2,462,716 bytes) loaded instead of GCC 16's. Header-inlined code ran fine; the
first call into the DLL's out-of-line locale/`filebuf` machinery — constructing the
output `ofstream` — went off a cliff.

`-DCMAKE_EXE_LINKER_FLAGS="-static"` removes the entire failure class. The binary
now imports only Windows system DLLs:

```
KERNEL32.dll, api-ms-win-crt-{convert,environment,filesystem,heap,locale,math,
private,runtime,stdio,string,time,utility}-l1-1-0.dll
```

No `libstdc++-6.dll`, no `libgcc_s_seh-1.dll`, no `libwinpthread-1.dll`. It is
correct from any shell with any `PATH` — verified from Git Bash (with Git's mingw
still shadowing) and from PowerShell. **Do not rebuild without `-static`** unless
you also intend to control `PATH` at every call site, which for a planner invoked
from a Python subprocess is not a promise worth making.

## Proof that it plans

Instance: the rig's own `engine-rig/engines/fd_adapter/domain.pddl` +
`problem.pddl` (gripper, 2 balls / 2 grippers / 2 rooms). The file's own comment
records a hand-verified optimum of **5 actions**; all three configurations agree.

FD's translator accepted both files with **no complaint** — no undeclared parent
type, no strictness problem. Nothing in the repo's PDDL was modified.

| Configuration | Exit code | Plan length | Plan cost | Optimal |
|---|---|---|---|---|
| `--search "astar(lmcut())"` | **0** | **5** | 5 | yes |
| `--search "astar(ipdb())"` | **0** | **5** | 5 | yes |
| `--alias lama-first` | **0** | **5** | 5 | (satisficing, hit 5 anyway) |

All three return the same plan:

```
(pick ball1 rooma left)
(pick ball2 rooma right)
(move rooma roomb)
(drop ball1 roomb left)
(drop ball2 roomb right)
; cost = 5 (unit cost)
```

Translator output for the instance: 5 variables, 14 facts, 18 operators, 2 mutex
groups, task size 121. `lmcut` reports initial h = 5 — tight against the optimum,
so A\* expands 8 states.

Logs and plan files: `runs/p13-fd-real/work/{lmcut,ipdb,lama}/`.

### Unsolvable instance

Written for this run at `runs/p13-fd-real/work/unsat/problem_unsat.pddl` — the same
gripper domain, goal `(and (at ball1 rooma) (at ball1 roomb))`. It is genuinely
unreachable: `drop` adds `(at ?b ?r)` without deleting the ball's other location,
but `pick` deletes `(at ?b ?r)`, so a ball must leave a room before it can be
carried anywhere, and no reachable state satisfies both goal atoms.

| Configuration | Exit code | stderr / stdout line |
|---|---|---|
| `--search "astar(lmcut())"` | **12** | `Search stopped without finding a solution.` |
| `--alias lama-first` | **12** | `Search stopped without finding a solution.` |

With `lmcut` the proof is immediate — `Initial heuristic value for lmcut: infinity`,
then `Completely explored state space -- no solution!`, 0 states expanded. The
driver then prints `search exit code: 12` and `Driver aborting after search`.

Exit 12 is `SEARCH_UNSOLVED_INCOMPLETE` ("search stopped without finding a
solution"), which is what an A\* that exhausts its state space returns. It is
**not** 11 (`SEARCH_UNSOLVABLE`, "task is provably unsolvable"), which FD reserves
for a proof produced by an unsolvability-certifying configuration. A caller that
wants to distinguish "no plan" from "gave up" should treat 11 and 12 together as
"no plan found" and not read 12 as a hard proof.

### End to end through the rig's own adapter

With `FAST_DOWNWARD` exported as above, `engines/fd_adapter` selects the real
planner on every rung — note `backend` is `fd-optimal` / `fd-satisficing`, not
`stub-bfs`:

```
prefer="fd-optimal",     heuristic="lmcut" -> length=5, search='astar(lmcut())',   optimal=True
prefer="fd-optimal",     heuristic="ipdb"  -> length=5, search='astar(ipdb())',    optimal=True
prefer="fd-satisficing"                    -> length=5, search='--alias lama-first', optimal=False
```

### The rig's own suite

`python -m pytest` from `engine-rig/`, same worktree, nothing else changed:

| | Result |
|---|---|
| without `FAST_DOWNWARD` | 249 passed, **3 skipped** |
| with `FAST_DOWNWARD` exported | **252 passed, 0 skipped** |

Installing the planner un-skips exactly three tests and they pass. No regressions
either way, so exporting the variable is safe for every other engine in the rig.

### Fast Downward's own test suite

`misc/tests/test-exitcodes.py`: **38 of 42 passed**. The 4 failures are all the same
pre-existing Windows driver limitation and are unrelated to this build:

```
ValueError: preexec_fn is not supported on Windows platforms
```

FD's driver enforces `--translate-time-limit` / memory limits via `preexec_fn`,
which does not exist on Windows. The test file says so itself in a comment — "We
cannot set time limits on Windows and thus expect DRIVER_UNSUPPORTED" — but the
driver raises `ValueError` before reaching that path. Consequence for callers:
**time and memory limits cannot be enforced on this platform.** Budget planner runs
externally (e.g. `subprocess` timeout) rather than through FD's own flags.

## Known limitations of this install

* **No LP solver.** CMake reported `Could NOT find Cplex`. Configurations that need
  an LP — `seq-opt` operator-counting, `diverse_potentials`, and friends — are not
  available. `lmcut`, `ipdb`, and `lama-first` do not need one, so nothing above is
  affected.
* **No time/memory limit enforcement**, per the `preexec_fn` note.
* **Not committed, by design.** `.toolchain/` is gitignored (added to
  `engine-rig/.gitignore` in this worktree, LF preserved). Roughly 1.6 GB of
  compiler + planner + build tree lives there; it is a machine-local artifact and
  this manifest is the reproducible recipe for rebuilding it.
* This volume is at **99% capacity (~5 GB free)**. The `builds/debug` and
  `builds/relnofp` trees used during diagnosis were deleted; only
  `builds/release` (616 MB) remains.

## Reproducing from nothing

```bash
mkdir -p engine-rig/.toolchain && cd engine-rig/.toolchain

curl -L -O https://github.com/brechtsanders/winlibs_mingw/releases/download/16.1.0posix-14.0.0-ucrt-r3/winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip
sha256sum -c <<< "4273565109cd8ab8ecef1b0dc2a56fd7f5c7ee0885840a1c011b9325160ec0c3 *winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip"
unzip -q winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip   # -> ./mingw64

git clone --depth 1 https://github.com/aibasel/downward.git downward
cd downward && git checkout 7120aa01704bfe8e3b9b92c062a4f775bc89c7bd   # needs a full clone to pin

export PATH="$PWD/../mingw64/bin:$PATH"
cmake -G Ninja -S src -B builds/release -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER="$PWD/../mingw64/bin/gcc.exe" \
  -DCMAKE_CXX_COMPILER="$PWD/../mingw64/bin/g++.exe" \
  -DCMAKE_EXE_LINKER_FLAGS="-static"
cmake --build builds/release

python fast-downward.py --version
```
