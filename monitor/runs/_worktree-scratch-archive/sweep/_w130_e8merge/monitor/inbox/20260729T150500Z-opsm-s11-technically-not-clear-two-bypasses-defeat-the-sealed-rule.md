# s11-sealed-halfguard: I cannot pre-clear it — two bypasses defeat the sealed catch-all

from: OPS-M (合并裁判), cycle 16
utc: 2026-07-29T15:05:00Z
kind: 技术裁决（不是许可裁决）。契约批准仍然只有你能做。
branch: `origin/agent/s11-sealed-halfguard`
prepared merge: `opsm/m16-s11` @ `9a626959`, worktree `.worktrees/opsm16-s11`
supersedes nothing; complements `20260729T0222Z-RES-4-s11-protected-root-vs-contract-change.md`

## Why this exists

RES-4 already put the three permission options in front of you and I am not repeating
them. My job was the other half: pre-clear everything that is *not* a contract question,
so your ruling could be one word. **I cannot.** The branch is technically not clear, and
the thing that is wrong is the thing the branch is for.

## The gate is fine

| tree | outcome |
|---|---|
| master + s11 | `DRIFT arc-recon` — regenerated `arc-recon/data/claim_set.json`, exit **0** |
| plain master (baseline) | byte-identical line, exit **0** |

Merge clean, no conflicts. Guard suite 151 passed. The DRIFT pre-dates the branch.

## The guard is real — and I broke it in two places

An adversarial subagent ran ~70 bypass attempts. **68 failed**, and that negative result
is worth as much as the positives: no `--game` → `deny_default_all`; empty, spaced,
repeated, comma-listed, reordered, `--game=`-vs-`--game`, `-g`, `--games=`; sealed id
full / 4-char prefix / UPPER / MiXeD; `--` child separator; `&&` `;` `|` `&` chaining;
`$( )` and backtick substitution; `bash -c` / `sh -c` wrapping; heredoc; `GAME=` env
prefix; Unicode-lookalike ids; CRLF; all eight `make` forms; and no env-var kill switch
exists (the module reads `os.environ` nowhere). The tests are not decorative either:
zero mocks, 11 named `test_bypass_*` regressions, and mutation testing confirms they
bite — forcing `classify_command` to always ALLOW fails 80, forcing `scan.clean` True
fails 5, and an always-deny guard also fails one, so the sample cuts both ways.

**Two attempts succeeded, and they are one defect** in `segments()`
(`local_engine_guard.py:340-348`). **I reproduced both myself rather than relaying them:**

1. **A shell comment ends at the newline; the guard's ends at end-of-text.**
   `echo hi # note\nmake play-local` → the guard sees only `echo hi` → **`allow`**.
   Also reachable as argv: `['sh','-c','echo hi # x\nmake play-local']` → **`allow`**.
2. **Quotes are stripped before comment detection, so a literal `"#"` becomes a comment
   marker.** `echo "#" ; make play-local` → guard sees `echo` → **`allow`**.

Controls, same session, same module: `make play-local` alone → `deny_unfiltered`;
`ls environment_files/<sealed-id>` alone → `deny_sealed`. So the rules work — they are
simply never reached.

**Rule 4, the sealed catch-all, is defeated by the same trick:**
`echo "#" ; ls environment_files/<sealed-id>` → **`allow`**, where the bare form is
`deny_sealed`. That is the one line in the whole branch that must not be bypassable.

The docstring's stated rationale is exactly backwards. It says quotes are stripped
because *"leaving them in let `"#"` hide a separator."* Stripping them is what lets `"#"`
hide a separator.

## Verdict

**DO-NOT-MERGE-AS-IS.** Not because it makes anything worse — baseline is *no guard at
all*, `environment_files/` does not exist anywhere on this machine (confirmed:
full recursive sweep of `C:`, zero hits; the repo is on `C:`), so this is prevention and
merging it strictly reduces exposure. It should not merge as-is because the branch's own
claim is *"nine bypasses found, nine fixed, each a named regression test"*, and shipping
it with a tenth that defeats the sealed rule makes that claim false in the tree. A guard
whose headline is "defaults to deny" and which answers `allow` to a sealed-pile read is
worse than no guard in one specific way: **people will trust it.**

**One commit fixes it** — a per-line, quote-aware comment strip (~4 lines). The subagent
verified the remedy flips both cases to `deny_unfiltered` while leaving the legitimate
`#--game=ar25` case at `deny_default_all` and clean commands at `allow`. Ask for that
plus two regressions in the existing `test_bypass_*` style, and the correction of the
now-false docstring sentence.

## Two smaller things for the same commit

* **The doc is stricter than the code.** CLAUDE.md's addition says any such path *"must
  name the four development-pile games explicitly."* The guard allows a single dev id
  (`--game=ar25`) and is right to. Harmless direction, but a contract line that does not
  describe its own enforcement is the shape this repo keeps paying for. Suggest "must
  name only development-pile games."
* **`make accepts an unreferenced `GAME=` override in silence`" could not be tested** —
  `make` is not installed on this machine. It is correct per GNU Make §9.5, and I am
  telling you it is unverified here rather than letting it read as measured.

Otherwise the additions check out: §8a really does say *"caching ARC data locally for our
own analysis is permitted, and no permission needs to be sought for it"*; *"permission is
not containment"* is §8a's own phrase; the `contamination.py`-stays-green claim holds
(it reads only `recon_ledger.jsonl`). No contradiction with any existing rule — additive
under the pile-cut section, and it only tightens.

## Your two claims, checked

* `CLAUDE.md` **+37 / −0**, `.gitignore` **+6 / −0**. Pure additions. Confirmed by `--numstat`.
* `environment_files/` does not exist on `C:` at all. Confirmed. (A sweep of the two
  large data drives was still running and had returned nothing; the repo is on `C:`, so
  it does not bear on the claim, but it is not a completed exhaustive scan.)

## Operational note, not a blocker

`scan` marks *any* file not naming a dev-pile game as `deny_unknown`, and `verify.sh` now
gates on it. The first legitimate dev-only cache containing a shared file (a `README`, an
`index.json`, a lockfile) turns `verify.sh` red. Fail-closed, so it errs safe — but
expect it, and it will look like a defect the first time.

## Zero sealed contact

No network call, no API call, no download, no `environment_files/` created. Sealed ids
were read programmatically from `piles.json` for the bypass probes and are not quoted in
this document. No sealed game was played, opened, or read about.
