# runs/p13-fd-real — P-13, Fast Downward really connected

    prompt_id: P-13
    track:     engine-rig
    branch:    agent/p13-fd-real
    date:      2026-07-28
    baseline:  Theoria.md 1.10b ("不自研,白捡二十五年规划工程"; the three-rung ladder)

## What is here

| File | What it holds |
|---|---|
| `TOOLCHAIN_MANIFEST.md` | Provenance for everything fetched: URLs, versions, sizes, sha256s, install paths, the exact build command line, tool versions, the segfault diagnosis, and a from-nothing reproduction script. |
| `DIVIDEND.md` | The two experiments, rendered. |
| `dividend.json` | The same, machine-readable. Byte-stable across runs. |
| `work/` | Raw Fast Downward logs and plan files for the lmcut / ipdb / lama / unsat probes, kept as evidence rather than summarised away. |

Regenerate the two dividend files with:

```bash
export FAST_DOWNWARD="<repo>/engine-rig/.toolchain/downward/fast-downward.py"
cd engine-rig && python -m tools.p13_fd_dividend
```

The toolchain itself (`engine-rig/.toolchain/`, 1.6 GB) is gitignored and not
committed; `TOOLCHAIN_MANIFEST.md` is what makes it reproducible.

## Headline

* **Fast Downward 24.06+ (`7120aa01`) is built from source and connected.** The
  M6 stub is no longer a substitute for a missing planner; it is the ladder's
  bottom rung. Setting `FAST_DOWNWARD` is the whole integration — no caller
  changed. Suite: 255 passed with it, 252 passed / 3 skipped without.
* **The deadlock dividend survives the change of engine.** `open4far`: −31.4%
  expansions on FD against M9's −29.3% on the bundled search, same 11-step plan.
  D-020's honest zero on `open4` replicates too.
* **One M9 number does not survive, and is corrected here.** `ringstuck`'s 44 →
  22 was a fact about the bundled search: FD's translator settles that instance
  by relaxed reachability before search starts and expands 0 states either way.
* **7 of 7 cold-start instances agree** between the two backends on plan length
  and on unsolvability, including three where FD independently proves the UNSAT.
* **A defect the other track reported was real, and the obvious fix was wrong.**
  FD's exit codes cannot tell a proof from a shrug; see D-024.
