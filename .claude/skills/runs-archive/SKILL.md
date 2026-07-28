---
name: runs-archive
description: 留痕 for a Theoria ticket — create <territory>/runs/<UTC>-<slug>/, append running notes and results while the work happens, and generate the MANIFEST.json that carries prompt_id, prompt path, branch, base_commit, seed and a per-file sha256 of every delivered artefact. Use as soon as a ticket starts producing output, whenever the user says 留痕 / 归档 / 建 runs 目录 / 写 MANIFEST / "archive this run" / "record the numbers", and again before 收工 to hash the deliverables. Also use to re-verify an existing MANIFEST (`check`) when a reviewer asks whether the published hashes still reproduce.
---

# runs-archive

A claim in PARTNER_SYNC that no artefact backs is an assertion. This skill is
the cheap way to make every number in your report traceable: METHOD.md #8
(prompt ↔ session ↔ commit ↔ artefact) and #9 (a failure must replay from a
seed) are both discharged by one MANIFEST.

Run everything from **your worktree root**.

## 1 — open the archive, first, not last

```bash
python .claude/skills/runs-archive/scripts/runs_archive.py new --slug canary-replay
```

Creates `<territory>/runs/2026-07-28-canary-replay/` (territory comes from the
ticket context `fleet-branch-ritual` left; pass `--territory` if you skipped
it), seeds `NOTES.md`, and remembers the path so no later command needs it.
`--precise` stamps to the second when a ticket opens several runs a day.

## 2 — write as you go, not from memory at the end

```bash
# prose: what you tried, what it did, what surprised you
python .claude/skills/runs-archive/scripts/runs_archive.py note \
  --text "Cookie jar A/B: 20/20 first-attempt RESETs with the jar, 0/20 without."

# numbers: merged into results.json, dotted keys, JSON values
python .claude/skills/runs-archive/scripts/runs_archive.py record \
  --key probes.stickiness --json '{"with_jar": 20, "without": 0, "runs": 3}'
python .claude/skills/runs-archive/scripts/runs_archive.py record \
  --key tests --value "40 passed, offline"
```

`results.json` is folded into the MANIFEST automatically. **Archive the failed
runs too** — METHOD.md #9 is explicit that a failure you cannot replay is worse
than one you can.

## 3 — the MANIFEST, before you close

```bash
python .claude/skills/runs-archive/scripts/runs_archive.py manifest \
  --title "canary replay + cookie fix, before/after" \
  --tests "40 passed (offline)" --seed 1729 \
  --include 'arc-recon/canary.py' --include-tracked arc-recon/data
```

* `prompt_id`, `prompt`, `branch`, `base_commit` come from the ticket context —
  do not retype them; if they are missing the command **refuses**, because a
  MANIFEST without them cannot be traced back to the工单.
* `--seed` is mandatory in spirit: leave it null only when nothing stochastic
  ran, and the script says so out loud when you do.
* `--include` takes repo-relative globs, `--include-tracked` hashes every
  git-tracked file under a directory (the P-11 pattern). Run-dir files are
  hashed by default.
* An `artifacts_note` about `core.autocrlf` is added automatically when your
  checkout would make these file-level hashes unportable — the caveat P-11 had
  to add by hand.
* Output is sorted-key, LF, UTF-8: rerun with the same `--now` and you get the
  same bytes.

## 4 — check, when someone doubts it

```bash
python .claude/skills/runs-archive/scripts/runs_archive.py check
```

Recomputes every hash, reports missing and drifted files as a checklist, exits
non-zero if anything moved. `verify-gate` calls exactly this.

## Rules

* The run dir lives **inside your territory**. Never write another track's
  `runs/`.
* Artefacts are evidence, so they are committed. Do not `--include` anything
  under `.env`, and never record a credential value in `NOTES.md` or
  `results.json`: Phase 4 publishes every tracked file. Read the key through
  `arc-recon/client.py`'s `load_api_key()`, log it through `mask()`.
* If a number in PARTNER_SYNC is not in `results.json` or an artefact, it is
  not yet evidence — either archive it or drop the claim.
