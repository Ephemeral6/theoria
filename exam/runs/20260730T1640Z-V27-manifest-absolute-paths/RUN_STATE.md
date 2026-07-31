# V27 — a tracked generated artefact recorded where its builder stood

RES-3, 2026-07-30/31, cycle 109. Branch `agent/v27-manifest-absolute-paths`,
base `8a5a83f9`. Territory `exam`. Zero API, zero network, zero sealed-pile
contact.

The ruling is `exam/DECISIONS.md` D-EX-031. This file is what was done and what
changed my mind.

## The defect, measured on a fresh checkout of master

`exam/artifacts/build_manifest.json` held **twelve** absolute paths — four papers
× `sheet_path` / `key_path` / `cheater_brief_path`. On a worktree created from
`origin/master` at `8a5a83f9` they read
`C:\Users\user\Desktop\theoria\.worktrees\v6-v23-large-space\exam\artifacts\…`,
which is **this session's own V6-V23 delivery**, merged hours earlier. The churn
is not historical and not hypothetical: the paths name whoever most recently ran
`build_papers`, so two branches that agree about every number still disagree
about twelve lines.

`write_json` returns an absolute path and `os.path.join(ARTIFACTS, …)` builds
one. Neither was relativised. `_repo_rel` in `exam/tools/build_papers.py` now
does it, forward slashes, and the artefacts were **regenerated** rather than
edited.

## What the ticket got right, and the one thing it corrected in itself

The ticket's own correction — written by its author ten minutes after filing —
is the load-bearing part, and I confirmed it rather than inheriting it:
`grep -n build_manifest exam/verify.py` was **empty** before this change. The
determinism stage builds in-process and digests
`module_for(t).build().sheet(digest())`; it never opens the build manifest. So
the graded sheets were always location-independent and the stage was **not**
falsely green. A dimension went unmeasured. Saying "the determinism gate is
fake green" would have been a worse sentence than the defect it described, which
is why the ticket says so in bold and why D-EX-031 repeats it.

## The gate, and it was seen red first

`exam/tools/check_artefact_locations.py` scans every tracked file under
`exam/artifacts/` for Windows and POSIX absolute paths, the building user's
name, temp directories and `.worktrees/` segments. Wired into `exam/verify.py`
as the `artefact_locations` stage.

`GATE-SEEN-RED.md` in this directory records it failing on the pre-fix
`build_manifest.json`: **four independent patterns on that one file, and no other
file matching any of them**, exit 1. After the fix, `41 tracked files … none
records where it was built`, exit 0. A gate nobody has watched fire is not a
gate.

## The scanner's first version was wrong, and wrong in the direction that gets a gate deleted

It searched raw file bytes and reported **seven findings across four exam
papers, every one false**. JSON escapes a newline as backslash-n, so a paper
whose prose reads "four things are asked:" before a line break literally holds
`asked:\n` on disk — which matches a drive-letter pattern *and* a
backslash-separator pattern. The scanner decodes JSON and searches the values a
reader would actually see. This is pinned by
`test_json_escapes_are_not_mistaken_for_paths`, because a location scanner that
fires on ordinary prose is switched off within a day, and a switched-off gate is
indistinguishable from no gate while looking like one.

Both directions are pinned: the clean case, the pre-fix bytes (read out of git
at `8a5a83f9`, not mocked), the JSON-escape false positive, and a repo-relative
path — which must **not** fire, or the fix would trip the gate that motivated it.

## Scope: single-file repair plus a gate, not a sweep

All 41 tracked files under `exam/artifacts/` scanned. Every hit is in
`build_manifest.json` and in those twelve values; the other 40 are clean. That
matches the scan the ticket recorded and reproduces it rather than trusting it.

## State

`python -m pytest exam/tests -q` **475 passed, 2 xfailed**.
`python exam/verify.py` **GREEN**, six stages, `artefact_locations ok`.

## Open, and deliberately not done here

* **`archive_run.py` still hashes the working copy.** `_digest_tree` reads
  `open(path, "rb").read()`, which under an `eol=lf` pin can differ from the
  bytes git publishes without `git diff` showing anything in stdout. V6-V23
  measured six such stamps across four sessions' runs. It is the same file this
  ticket is about, but a different defect, and it belongs with
  `V2-V25-verify-does-not-check-what-is-committed`; requested in
  `monitor/inbox/20260730T1625Z-RES-3-two-tickets-…md`.
* **The cross-location build comparison.** The ticket's step 2 asks for two
  builds in two different directories compared byte for byte. What is delivered
  is the *sound and complete detector for the channel that actually leaked* —
  absolute paths in tracked artefacts — plus its negative controls. The
  empirical version catches channels nobody enumerated (cwd, hostname, locale)
  and is strictly stronger; it is not here, and this file says so rather than
  letting the scan stand in for it silently. Anyone picking it up: the honest
  form is a second `git worktree` at a different path, build in both, diff
  `exam/artifacts/` — and it must be watched red on this commit's parent before
  it is believed.

## The instrument from the previous ticket caught something on its first outing here

`stamp_manifest.py` is carried over from V6-V23, where cycle 107 found that run
manifests were being stamped from the working copy rather than the bytes git
publishes. Its guard refused the very first stamp attempted in this directory:
`GATE-SEEN-RED.md` had CRLF on disk, written by a shell pipeline capturing a
Python program's output on Windows, against `exam/.gitattributes`'s LF pin.

Worth recording because it is the cheapest possible evidence that the guard is
not ceremonial. Nobody was looking for it, it fired on a file created ten
minutes earlier by an ordinary command, and the file it protected is the one
holding this ticket's negative-control evidence — a provenance record of a gate
going red, which would itself have been stamped wrong.
