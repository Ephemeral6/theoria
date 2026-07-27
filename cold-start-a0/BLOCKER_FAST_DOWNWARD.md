# BLOCKER · Fast Downward needs a C++ compiler

**What is missing: a C++17 compiler. Nothing else.** Everything else Fast
Downward needs is already in place in this checkout.

**A correction to what I reported earlier.** My first write-up said the
winlibs / mingw-builds download URLs "404". That was wrong, and it matters
because it made option B below look like a dead end. The URLs are fine — I
guessed release tags instead of looking them up, and the GitHub API was
rate-limited so I could not enumerate the real ones. The verified URL is in
option B and it answers `HTTP 206` to a range request. The other two attempt
records (Lean's clang, conda) are accurate.

---

## 1 · What is already done

| | state |
|---|---|
| `aibasel/downward` source | cloned at `.toolchain/downward` (commit `7120aa0`, 5.2 MB) |
| CMake | `4.4.0` at `D:\Miniforge3\Scripts\cmake.exe` — FD needs ≥ 3.16 ✅ |
| Ninja | `1.13.0` at `D:\Miniforge3\Scripts\ninja.exe` ✅ |
| Python 3 | 3.13.13 ✅ |
| **C++ compiler** | **absent — this is the whole blocker** |

`.toolchain/` is gitignored, so nothing you install there enters the repository.

## 2 · What failed, and why

Three attempts, all at getting a C++ compiler:

1. **Lean's bundled clang 15** (`.toolchain/lean-4.9.0-windows/bin/clang.exe`).
   It exists and targets `x86_64-w64-windows-gnu`, but it ships only the headers
   Lean's own codegen needs — no C++ standard library:

   ```
   t.cpp:1:10: fatal error: 'vector' file not found
   ```

2. **`conda install -c conda-forge m2w64-toolchain`** into the base Miniforge
   environment:

   ```
   RemoveError: 'setuptools' is a dependency of conda and cannot be removed
   from conda's operating environment.
   ```

   Installing into base is what breaks. A *separate* env would work — option C.

3. **Direct winlibs / mingw-builds release URLs.** I guessed tags, got 404s, and
   could not enumerate the real ones because the GitHub API rate-limited this
   host. **My error, not a real dead end.** See the correction above.

---

## 3 · Three ways to unblock it, best first

### Option A — MSVC Build Tools ✅ recommended

This is what Fast Downward's own `BUILD.md` documents for Windows ("install
Visual Studio >= 2017"), so it is the path most likely to compile without
patches. `winget` is available on this machine.

```bash
winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Roughly 2–4 GB. Afterwards, build from a **Developer Command Prompt / x64 Native
Tools Command Prompt** (not Git Bash — MSVC needs its environment variables):

```
cd C:\Users\user\Desktop\theoria\cold-start-a0\.toolchain\downward
python build.py
```

### Option B — winlibs mingw-w64, no installer

A zip you unpack; nothing touches the registry. **Verified reachable** (`HTTP
206` to a range request on 2026-07-28):

```bash
cd C:/Users/user/Desktop/theoria/cold-start-a0/.toolchain
curl -sSL -o mingw.zip "https://github.com/brechtsanders/winlibs_mingw/releases/download/16.1.0posix-14.0.0-ucrt-r3/winlibs-x86_64-posix-seh-gcc-16.1.0-mingw-w64ucrt-14.0.0-r3.zip"
unzip -q mingw.zip
export PATH="$PWD/mingw64/bin:$PATH"
g++ --version
cd downward && python build.py
```

**Caveat, stated up front:** mingw is *not* an upstream-supported Windows
toolchain for Fast Downward, and gcc 16 is very new. If the build errors out
inside FD's own sources rather than in the toolchain, that is this caveat
biting, and option A is the answer rather than a patch.

### Option C — WSL

`wsl.exe` exists on this machine (a distro may still need installing).

```bash
wsl --install -d Ubuntu           # if no distro yet
wsl sudo apt install -y cmake g++ make python3
wsl bash -c "cd /mnt/c/Users/user/Desktop/theoria/cold-start-a0/.toolchain/downward && python3 build.py"
```

**Caveat:** this produces a *Linux* binary. `fd_adapter` shells out with
`python fast-downward.py …` from Windows, so it would not run it directly — you
would need a `.bat`/`.py` shim that forwards to `wsl`. Fine as a fallback, more
moving parts than A or B.

---

## 4 · How to tell me it worked

One environment variable, then one command:

```bash
cd C:/Users/user/Desktop/theoria/cold-start-a0
export FAST_DOWNWARD="$PWD/.toolchain/downward/fast-downward.py"
python -m certify.fd_conformance
```

`fd_adapter.find_fast_downward()` accepts `$FAST_DOWNWARD` as either the
executable itself or a directory containing `fast-downward.py`, and prepends
`python` when the path ends in `.py`. **No code changes anywhere** — that is the
claim being tested.

With a real Fast Downward reachable, `fd_conformance` switches out of stand-in
mode and re-runs M4 through it on all three compiled instances, writing
`artifacts/fd_real.json`:

| instance | expected |
|---|---|
| `a0-base` | SAT, **length 12**, `backend: fast-downward` |
| `a0-no-button` | **UNSAT** — and it must stay UNSAT, or the unsolvability theorem is in trouble |
| `a0p-base` | SAT, **length 10** |

Exit code 0 means every instance agreed with the bundled BFS on status and on
optimal length. The actions themselves may differ — both backends are optimal
for unit costs, and more than one optimal plan can exist, so only the length is
required to match.

If it comes back non-zero, that is a real finding and I would want the JSON.

---

## 5 · What this unblocks, and what it does not

**Unblocks:** the untested half of `A0_REPORT.md` §7.4 — Fast Downward's own
search agreeing with the bundled stub on A0's instances. The other half (the
adapter's plumbing: discovery, invocation, `sas_plan` parsing, independent
validation, `backend` reporting) is already verified against a protocol stand-in
and is green; see `certify/fd_conformance.py`.

**Does not unblock:** anything about scale. A0's instances are 36–38 arena cells
and the bundled BFS solves them instantly, so FD will too. Whether the planner
path holds up on a real ARC-sized problem is a separate question that these
instances cannot answer either way.
