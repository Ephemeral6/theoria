# REPRODUCING.md — how to check this release for yourself

You have been handed a repository and a set of claims about it. This tells you
how to check them without trusting us, and — just as importantly — **which
claims you cannot check**, and why.

Read the second part. A reproduction guide that only lists what works is
advertising.

---

## 0. What you need

* **Python 3.13**, with `numpy`, `scipy` and `pytest`.
* **git**, because every check reads the tracked file list rather than walking
  directories. An unpacked tarball without `.git` will not work.
* Nothing else, for everything in this document.

You do **not** need an API key. You do not need `.env`. You do not need network
access. If any step here asks you for one of those, that is a defect in this
document — see §6.

Two optional toolchains matter only for claims that name them: **Lean** (the
machine-checked proofs; without it the proof tests skip rather than pass) and
**Fast Downward** (`engine-rig`'s optimal-planning rung; without it the adapter
falls back to a BFS stub and 3 tests skip). Both absences are expected and are
reported as skips, not as passes.

---

## 1. Check the red lines

```bash
python release/check_redlines.py --mode verify
```

This scans every tracked file for two things that must not be in a public
release: the project's API credential, and material from the **sealed pile** of
benchmark games the project committed to never looking at.

`--mode verify` is the flag for you. Without it the script runs in `generate`
mode, which requires the credential to be present so it can search for it — that
is the mode the maintainers use before publishing, and in your checkout it will
fail, correctly, because you have no key. In `verify` mode the credential check
reports **not applicable**: the credential was never shipped, so there is nothing
to search for.

Expect: `Both red lines clear.` You will also see a list of files that *name* a
sealed game. Those are guards, tests and audit records that name those games in
order to keep them out — naming is not contact, and a release that stripped them
would be hiding the ledger that proves the seal held.

## 2. Rebuild the manifest and confirm it matches

```bash
python release/enumerate.py
git diff --stat release/MANIFEST.jsonl
```

`MANIFEST.jsonl` is one line per tracked file: path, sha256, size, and a
**licence class**. Regenerating it in your checkout should produce no diff. If
it does, either the tree moved or the classification rules changed, and either
way the diff tells you exactly which files.

## 3. Read what may and may not be redistributed

```bash
cat release/LICENCE_POSTURE.md
```

The short version, because it constrains everything below:

* **Class A — self-built.** Ours, freely redistributable. It is the bulk of the
  repository and it carries the research claim: the synthetic worlds, the
  engines, the two books, the proofs, the figure pipeline.
* **Class B — API-derived compilations.** The ledgers, probe logs and run
  archives. These exist and are complete, and the benchmark's terms forbid
  republishing them without written permission we have not sought. You get their
  **sha256 and the code that regenerates them**, not the files.
* **Class C — statistics derived from B.** Metric cells, counts, the figures.
  Redistributable, with one flagged uncertainty noted in that file.
* **Class D — upstream third-party payload.** Not present, because its upstream
  declares no licence at all, and silence is not a grant.

## 4. Cross-check the release list

```bash
python release/checklist.py
cat release/CHECKLIST.md
```

This walks the release list from the design document item by item. Three of the
ten items are `WITHHELD` — they exist, they are complete, and you cannot be
handed them (class B, above). One is `ABSENT`. Two more matched and are still
not quite what the list asks for, and the report says which and why rather than
ticking them.

## 5. Reproduce what can be reproduced

```bash
python release/reproduce.py --list      # what will run, and what will not
python release/reproduce.py             # the default set
python release/reproduce.py --all       # plus the slow targets
cat release/REPRODUCTION_REPORT.md
```

Each territory that publishes a regeneration command has it run, and the
resulting artefacts are hashed against the manifest. **Run this after step 2**,
not before: against a manifest older than the tree, every target is graded
`manifest-stale` and nothing is regenerated, because comparing a fresh build to
a stale baseline measures the baseline.

The grades you should expect, and how to read them:

| grade | what it means for you |
|---|---|
| `reproduced` | you rebuilt it and got byte-identical output |
| `drifted` | you rebuilt it and did not. **Tell us** — this is a real finding |
| `manifest-stale` | you skipped step 2; do it and re-run |
| `declared-not-run` | a real command, skipped as slow. Use `--all`. **Not a pass** |
| `needs-api` | regenerating means replaying games against the live benchmark: real money, and the sealed-pile discipline applies to every call. You cannot do this and neither should you |
| `needs-ground-truth` | the input is not in this release and cannot be |

The strongest single check in the repository is the figure pipeline's, and you
can run it directly:

```bash
bash figures/verify.sh
```

Eight gates, including two builds diffed byte-for-byte, the committed tree
compared against a fresh build, and a coverage probe that runs its own negative
control first. It takes a couple of minutes.

## 6. When something does not work

**The document is wrong, not you.** That is the standing rule here: this file
was tested by handing it to someone with no context and watching where they got
stuck, and every place they got stuck was fixed here rather than explained to
them. If you get stuck, the same applies — the fix belongs in this file.

Known-good expectations, so you can tell a defect from a design decision:

* Tests that **skip** without Lean or Fast Downward are expected. Tests that
  **fail** are not.
* `needs-api` targets not running is expected and permanent.
* A sealed-game name appearing in a guard or a test is expected; sealed-game
  *content* is not, and `check_redlines.py` distinguishes them by looking at
  whether any record pairs the id with payload.

## 7. What this release does not let you check

Stated plainly, because it is the honest limit of the whole exercise:

**You cannot independently verify the benchmark results.** The ledgers that
record what each arm did and what it cost are class B. You get their hashes and
the harness that produced them; you do not get the ledgers, and regenerating
them requires an API key, real spend, and playing games the project's own
discipline seals off. If you want to check that the numbers in the paper follow
from the ledgers, you can check the *derivation* — the figure pipeline and the
metric battery are class A and C and run offline — but the ledgers themselves
you must take on trust or reproduce at your own cost.

The design document's stated ambition was openness matching the benchmark's own
floor: the full public set plus artifacts. **On this class that ambition is not
met, and cannot be under the current terms.** That is a limitation of the
release, not a detail of its packaging, and it is written here rather than left
for you to discover.
