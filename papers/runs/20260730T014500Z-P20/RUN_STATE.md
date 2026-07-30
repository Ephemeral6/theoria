# S-P20-nosecret-noop — the six silent-pass holes in the paper gate

`prompt_id` `S-P20-nosecret-noop` · lane `paper` · territory `papers` ·
RES-2 cycles 36–37 · branch `agent/s-p20-nosecret-noop`

The item is the leftovers of S34: an adversarial audit found six ways
`papers/phase1-workshop/verify_paper.py` reports PASS without having checked
anything, S34 fixed the delegator above it and left these as a separate piece of
work. All six are closed here. **Five of the six were latent** — no live
instance in the paper — which is the cheapest moment to close a hole and the
reason nothing in `sections/` had to be rewritten.

Every closure is verified twice: a negative control in the suite, and a mutation
planted in the **live** tree with the real gate run over it. The second one
matters because four of these six holes were *in* checks whose own tests passed
throughout.

## D — the headline: a no-op everywhere it mattered

`check_nosecret` built its secret list from `ROOT/.env`. `.env` is gitignored,
so it does not exist in the worktree `monitor/ci_merge.py` checks out: the list
came back empty, the comparison loop iterated zero times, and the check returned
True with the note *"no .env present to check against (nothing to leak)"*. That
sentence was false in the only direction that matters — nothing had been checked.
`CLAUDE.md` makes this Phase 1's sealing discipline and notes the Phase 4 release
manifest publishes every tracked file, so this is the check standing between the
credential and publication, and it could only ever fire on a machine that already
had the key on its disk.

Reproduced in CI's exact configuration — the paper directory copied into a root
with no `.env`, a file planted holding `api_key: <a uuid>`:

| | before | after |
|---|---|---|
| planted key, no `.env` in the root | `[PASS] D NOSECRET`, `PASS (6/6)`, exit 0 | `[FAIL] D NOSECRET`, two findings |

Two mechanisms were added, both independent of any untracked file, so they run in
CI, on a fresh clone, and against a release tarball:

* **a credential-named assignment carrying a substantial opaque value**, whatever
  its shape. This is the one that catches the *next* secret: a check that only
  knows today's key shape learns nothing the day the key is rotated.
* **a key-shaped token in a credential context** — the promise the module
  docstring has carried since it was drafted (*"nothing shaped like the ARC
  key"*), which until now existed only in the docstring: there was no shape or
  entropy test in `check_nosecret` at all.

The exact-value scan is kept, still runs when `.env` is present, and is now
reported as what it is — a bonus available on the author's machine, printed as
`exact-value scan SKIPPED` when it does not run, rather than as a green.

**What the key's shape cost to encode, and why it is not a leak.** The ARC key is
a canonical UUID (36 chars, dashes at 8/13/18/23). That was established by
reading `.env` through `arc-recon/client.py` and printing *properties only* —
length, charset predicates, dash positions. The value was never printed, written,
or committed. A 36-character UUID mask discloses no part of the 128 bits inside
it; the format is public and shared with 4467 other UUID-shaped tokens in 140
tracked files, which is exactly why shape alone cannot be the trigger.

**The residual gap, stated rather than papered over.** A *bare* key-shaped token
with no credential word within 40 characters is not flagged. Flagging it would
red the gate on arrival — two of those 4467 are inside this directory already,
both a Texas library URL in P7's search traces — and check E's reasoning applies
with more force here: a permanently red gate is one somebody switches off, and
this is the last gate before publication. The exact-value scan covers that case
and only runs where `.env` exists. That is the hole that remains.

**The negative control does not contain the key.** Its fixtures are assembled at
runtime from string concatenation, because check D reads its own test file:
written out as literal `secret=...` lines they took the check red on its own
negative control, which is how the first run of the suite failed. The
alternative — exempting the filename — would have been a place to hide a key from
the scanner.

## B — three ways a citation was skipped rather than judged

`check_paths` had one word, `ok`, covering several different ways of not
resolving for a reader. It now has seven verdicts. All three additions were
latent (`0 miscased, 0 paper-local, 0 unshareable` on the live paper), and there
is a test asserting that, because it is the reason they were cheap.

* **`MISCASED`.** `(ROOT / token).exists()` asks the filesystem, and this one is
  NTFS, which ignores case. `Engine-Rig/STATUS.md` was `ok` here and BROKEN on a
  Linux clone: the verdict depended on the machine, and the machine it ran on is
  the one where the answer is always yes — while everything the gate protects
  (CI, a fresh clone, the release tarball) is somewhere else. `exists_exact()`
  walks the components against `os.listdir`, which is the portable form of the
  question.
* **`LOCAL`.** A path resolving beside `PAPER.md` and not from the repository
  root was `ok`. The paper's own binding rule asks for *"the repo-relative path
  of the artefact it came from"*, and a reader standing where the paper says to
  stand lands nowhere. The finding names the replacement path.
* **`UNSHAREABLE`.** `.worktrees/` was on the *gitignored-by-design* exemption
  list beside `.toolchain/` and `figures/.verify/`. It does not belong there:
  those two name something a reader can rebuild from documented commands, a
  worktree path names one machine's scratch at one moment. It was also **the one
  prefix all three path checks agreed to ignore** — B skipped it by exemption, F
  skips anything with a `/`, E only asks that *a* citation be present — so
  `.worktrees/anything/at/all.md` satisfied the paper's binding rule against
  every check in the file at once. §10.7 already concedes the paper's least
  resolvable citations are exactly of this kind.

Plus a **stale detector for `ADJUDICATED_AMBIGUITY`**, which checks E and F have
each had for their own ruling tables and this one did not. A ruling is written
about a live ambiguity; when the ambiguity goes the ruling stays behind and
silently excuses the next token that arrives under that name. All 10 entries
currently match, so this too is latent.

## A — the floor

`sections/` emptied gave `PASS (6/6)`: `parts` is `[]`, `expected` is the banner
alone, and a `PAPER.md` holding just the banner is byte-identical to it, so the
strictest check in the file passed a paper with no paper in it and the other five
passed by having nothing to iterate over. Check E printed `-1 body sections` on
the way past, on a PASS line, because it subtracted the exempt abstract from a
count of zero.

`MIN_SECTIONS = 2` is the same device and the same reasoning as `MIN_PAPERS` in
`papers/verify.py` one directory up — that file refuses an empty `papers/`, this
one refuses an empty `sections/`. The count is now of what was actually walked
(`body_sections()`), which cannot go negative and cannot disagree with the loop
above it.

## C — the payload was compared against itself

The snapshot was taken from the committed files, the extractor then ran *in
place*, and the comparison read the same file back. An extractor producing
nothing at all left the committed payload sitting there untouched: `exists()` was
true, the bytes matched, and the `was not regenerated` branch could never
execute. A gutted extractor was reported as `reran in place`. Payloads are now
removed before the rerun — the extractor has to produce its own output, which is
the property the check claims to test — and restored from memory in the `finally`
either way, so an extractor that dies halfway does not damage the tree (there is
a test for exactly that).

Separately, `scripts` and `before` were counted independently and printed side by
side (`2 extractors reran in place, 3 payloads unchanged`): two numbers that must
agree, compared by nobody. Renaming one script out of the `fig[0-9]*.py` glob
passed. An orphan payload now fails.

## The six verdicts describe two different documents

The checks are independent and their verdicts are printed together as though they
were about one object. They are not: A is the only check that reads `PAPER.md`,
and B, E and F read `sections/`. When A fails those are two different documents,
so `[PASS] E` is a true statement about a file the reader will not be handed.
Each such verdict now carries a caveat line, and the summary names them.

## Verification

Nine mutations planted in the **live** tree, gate run, tree restored — not one of
them in a fixture:

| # | mutation | verdict |
|---|---|---|
| 1 | `` `Engine-Rig/STATUS.md` `` into a section | `[FAIL] B` MISCASED |
| 2 | `` `.worktrees/p20-nosecret/papers/SURVEY-A.md` `` | `[FAIL] B` UNSHAREABLE |
| 3 | `` `sections/00_abstract.md` `` | `[FAIL] B` LOCAL, names the replacement |
| 4 | a ruling for a token nobody cites | `[FAIL] B` STALE |
| 5 | `sections/` emptied | `[FAIL] A`, and the caveat printed on B and E |
| 6 | `fig1_concept_timeline.py` gutted to `raise SystemExit(0)` | `[FAIL] C` was not regenerated |
| 7 | an orphan `fig99_orphan.json` | `[FAIL] C` no extractor |
| 8 | `ARC_API_KEY=<uuid>` planted, `.env` present | `[FAIL] D`, both mechanisms |
| 9 | `api_key: <uuid>` planted, **no `.env`** (CI's configuration) | `[FAIL] D` — the item, closed |

Suite: **171 passed** under `python papers/verify.py`, up from 141 (three new
files: `test_paths_gate.py` 15, `test_gate_floor.py` 14, plus one added to
`test_nosecret_gate.py`). Gate itself: `verify_paper: PASS (6/6)`, exit 0.

One incidental fix, found by a probe rather than by the item: `check_nosecret`
called `path.relative_to(ROOT)` to name its findings, which raises when ROOT is
not an ancestor. ROOT always is in production, so this is a crash path and not a
verdict path — but a leak detector that raises while naming what it caught has
caught nothing anybody reads. It falls back to the absolute path, with a test.

## What is not closed

* the bare-shaped-token gap in D, above — the reason is in the docstring beside
  the code, not only here;
* the known gaps in E and F that the module docstring already enumerates: this
  item did not touch them;
* `LOCAL` is a hard refusal with no ruling table. Nothing in the paper stands in
  it today. If a legitimate paper-local citation ever appears, the choice is a
  ruling table like `ADJUDICATED_AMBIGUITY`'s, not an exemption — recorded here so
  the next session does not reach for the exemption first.
