# Site verification — every `path:line` the section wants to cite

Read-only pass over the worktree at `29f41ea`. Eighteen sites claimed by the
census (via `monitor/inbox/archive/20260729T063000Z-RES-3-...md` and the five
board items derived from it). Verdicts below are from opening each file.

## Summary

| # | Claimed | Actually at | Verdict |
|---|---|---|---|
| 1 | `engine-rig/tools/p13_fd_dividend.py:129` | 129 | EXACT |
| 2 | `engine-rig/tools/p13_fd_dividend.py:53` | 53 | EXACT |
| 3 | `engine-rig/engines/fd_adapter/backends.py:74` | 74 | EXACT |
| 4 | `backends.proves_unsolvable` | def 239, doc 240–265 | EXACT; **not called by p13** |
| 5 | `worldgen/core/truth.py:279` | 279 | EXACT |
| 6 | `worldgen/core/build.py:166` | `worldgen/build.py:166-167` | **PARTIAL — path wrong** |
| 7 | `theoria-arm/inner/plan.py:172` | 171–173 | EXACT |
| 8 | `theoria-arm/inner/certify.py:196,206` | 196–197, 206–207 | **PARTIAL — one half misattributed** |
| 9 | `a0-spike/pipeline/stages.py:260` | 261–264 | **PARTIAL — off by one; quote not emitted** |
| 10 | `release/check_redlines.py:207` | 207–208 | EXACT |
| 11 | `release/enumerate.py:220` | 220–221 | EXACT |
| 12 | `arc-recon/contamination.py:338` | 338 | EXACT |
| 13 | `arc-recon/verify.sh:53` | call at 53; mechanism at 22 | **PARTIAL — wrong line for mechanism** |
| 14 | `engine-rig/engines/lp_potential/potential.py:169-170` | 170–171 | **PARTIAL — off by one** |
| 15 | `engine-rig/engines/zero_space/zerospace.py:141` | 141; `scope="global"` at 174/181 | EXACT |
| 16 | `engine-rig/bench/ladder.py:74-82,226` | 74–82, 226 | EXACT (gold standard) |
| 17 | `cold-start-a0/certify/fd_unsat.py` | regex 37, const 34, doc 24–26, test 241–254 | EXACT, all four parts |
| 18 | `release/MANIFEST.jsonl:290` | 290, sha256 recomputed and matches | EXACT |

## The corrections that change what the section may say

**(i) `certify.py` does not claim an exhaustive reachable set.** The census's
sharpest sentence — "每一次崩溃都让健康证明看起来更好" — was supported by pairing
a swallowed exception with a report declaring exhaustion. `certify.py:210` in fact
emits `"scope": "sampled"`, with a comment at `:189` saying "which is exactly why
this is sampled". The exhaustion string lives in a different file,
`theoria-arm/inner/plan.py:187-191`, and *that* string hedges itself in the same
breath: "Constraint 6: this is a search result, not a theorem".

The emitted clash string is `"no (state, action) among %d x %d admitted two
rules"` (`certify.py:214-215`), not "no pair admitted two rules".

**So the defect is real but one size smaller than reported.** The swallowed
exception at `certify.py:196,206` still silently shrinks the sample that the
`sampled` verdict is computed over, and nothing counts the swallowed crashes —
but the artifact does not claim exhaustiveness, and the one file that does claim
it labels the claim a search result. The paper must say the smaller true thing.

**(ii) `a0-spike/pipeline/stages.py`** — the `except Exception:` is at **261**,
not 260. The phrase "no single conjunctive guard for this transition class"
is **not an emitted string** anywhere in `a0-spike`; the nearest real text is the
code comment at `:254-255`. It must be cited as a paraphrase of the code's
behaviour, never quoted. The substance survives: a CEGIS crash and a genuinely
non-conjunctive class both produce `_1`/`_2`-suffixed DNF rules with nothing
recording which occurred.

**(iii) Three line/path corrections**, all adopted:
`worldgen/build.py:166-167` (not `worldgen/core/build.py`);
`engine-rig/engines/lp_potential/potential.py:170-171` (not 169-170);
`arc-recon/verify.sh:22` inside `step()` is the exit-code-only judgement
(`:53` is merely the call site).

## The sharpest site, confirmed verbatim

`engine-rig/engines/fd_adapter/backends.py:239-265` defines
`proves_unsolvable(tier, returncode, log)`, whose docstring reads:

> The whole unsolvability track hangs on this one bit, so it is decided here
> rather than by string-matching at each call site, and it is decided
> conservatively -- the direction that can only ever refuse a real proof, never
> manufacture a false one.

A repo-wide grep for `proves_unsolvable` hits `backends.py`, `bench/fdrun.py:291`,
`tests/test_fd_ladder.py`, `fd_adapter/__init__.py` — and **zero times** in
`engine-rig/tools/p13_fd_dividend.py`, which is the file that both imports the
module (`:53`) and hand-rolls `unsolvable=done.returncode == 12` (`:129`).

## The gold standard, verbatim

`engine-rig/bench/ladder.py:74-82` — on exhausting the budget it returns
`"solved": False, "proved_unsolvable": False` **and** `"error": "over budget: %s"
% exc`. And `:248`, `failures()`, reads
`if row.get("error") and "over budget" not in str(row["error"]):` — the ceiling is
deliberately excluded from the failure list, so it is recorded as a fact rather
than laundered into either a defect or a negative result.

## The other track's file, read only

`cold-start-a0/certify/fd_unsat.py` — all four claimed parts confirmed: the regex
at `:37` no longer matches the string upstream now raises
(`backends.py:339` interposes ` and no proof`), so the exit-12 branch at `:45-46`
is dead code; the live path is `NoPlanExists`; the wrong constant survives at
`:34` with a docstring at `:24-26` asserting 12 = `SEARCH_UNSOLVABLE` where
`backends.py:72-74` measures 12 = `SEARCH_UNSOLVED_INCOMPLETE`; and
`cold-start-a0/tests/test_followups.py:245-246` asserts the wrong mapping by
hand-constructing a message string the codebase no longer emits.
`release/MANIFEST.jsonl:290` marks it `releasable`, sha256 recomputed and matching.

**Not a byte of `cold-start-a0/` was modified. It is the other track's.**

## The absent source

`find . -iname "SURVEY*"` returns nothing. Confirmed again independently:
`SURVEY-solver-status.md` and `SURVEY-empty-as-negative.md` do not exist on this
branch. The E11 run directory holds `CROSSCHECK.md`, two `ADVERSARIAL-*.md` and
six `partials/*-via-*.md`.
