# WIP — cycle 50 evidence (write-as-you-go; not a report)

Pin: `origin/master = 13bbcad9`, pinned **07:46:41Z**.
`HEAD = 60def5cb`, **7 commits behind the pin** — disk != pin for tracked files this cycle.
Range `304ad651..13bbcad9` = 13 commits / 47 files / +3269 −255, 5 on first-parent.
Boot: bus `NO-NEW-MESSAGES`, no `URGENT`. `ALL.md`'s 5 `status: OPEN` are 07-28 broadcast
rulings — not flipped, per prior lives.

## Dispatched (7 gatherers + refuters as conclusions form)

1. master green? / `monitor/` deadlock — **RETURNED 07:53:56Z**
2. exam V23 cluster (owed from c49) — in flight
3. sealed-pile discipline in the range (dim 1) — in flight
4. one-way doors in new range code (dim 7) — in flight
5. evidence drift + `PARTNER_SYNC:1654` owed item (dim 3) — in flight
6. monitor self-drift + orphan-field sweep (dim 8) — in flight
7. do fleet instruments walk stale worktree copies? — in flight
R1. adversarial refuter at gatherer 1's four new claims — in flight

## Settled by me, before any subagent

### KILLED — the mangled root filename is prior art, found in 3 minutes
`C:UsersuserDesktoptheoriamonitorpermtest.txt` (`:` = U+F03A, 8 bytes, 07-28 11:44, disk)
is `monitor/prompts/Z0-permprobe.md`'s permission probe writing an absolute path as a literal
filename. **OPS-R filed this 2026-07-28T03:48Z** —
`monitor/inbox/archive/20260728T034833Z-OPS-R-optional-checks-fail-open.md:36-40`, and it is
written into `PARTNER_SYNC.md:570`. Not re-filed.

### KILLED BY MYSELF — the credential alarm I raised and then destroyed
Four full repo checkouts live inside the working tree at `.claude/worktrees/`:
`agent-a84bd79e7c2e1dca9`, `agent-ac6a3655b65f2e012`, `agent-ac847fd12b35baecb` (Jul 29),
`p11-arc-hygiene` (Jul 28). **`p11-arc-hygiene/.env` exists** (49 bytes, 07-28 08:25, disk).

It is **ignored twice over**, so there is no publication risk and no finding:
- `git check-ignore -v` attributes it to `.git/info/exclude:11:**/.claude/worktrees/`;
- `.gitignore:3`'s bare `.env` has no slash, so it matches at **any depth** independently.

I never opened any `.env`, and told no subagent to. Recorded because the *refutation* is the
result: this is the shape my `self_correction_rule` names first — "prove you are not looking
at a second copy."

### OPEN, dispatched as gatherer 7 — the residue that points the other way
The four copies are invisible to git and **fully visible to every recursive filesystem walk**
(one `grep -rn` of mine returned three stale duplicates). Question: which discipline
instruments enumerate via `os.walk`/`glob`/`find` rather than `git ls-files`? The load-bearing
one is `arc-recon/local_engine_guard.py scan` — per `CLAUDE.md` it is the **only** instrument
that can detect a locally cached sealed game, because a local run makes no API call and leaves
no ledger trace. Sharpest possible form: an exclusion list naming `.worktrees/` (the tracked
`CLAUDE.md`/`.gitignore:16` convention) but **not** `.claude/worktrees/` (where the harness
actually writes them).

### NOT a finding — bus file encoding
`monitor/bus.py say` rendered as mojibake in my terminal. `monitor/bus/OPS-A/out.jsonl`
**decodes as UTF-8 in full** (gbk fails at byte 131), so the file is clean and the mangling was
my own terminal codepage. Checked because a mixed-encoding append-only log would be a real
defect; it is not one.

## Gatherer 1 result — the operational emergency, LIVE and UNATTENDED

Measured 07:53:56Z. **Prior art for the mechanism is `DRIFT-20260730T0656Z` (mine, 06:56Z);
what is new is the persistence and the non-response.**

- **Master is red AT THE PIN.** Independent instrument, not a restatement: `git archive
  13bbcad9 | tar -x -C /tmp/pinchk`, then `python -m pytest -q tests/` in
  `%TEMP%` → **3 FAILED**, the same three test names verbatim. `monitor/reflex.py` is md5
  `0930061015e38c9d189fd5e82d671984` **identically** at `7c1dd89b`(04:56:22Z), HEAD, pin, disk —
  untouched on **any ref** since 04:56:22Z.
- `.mongate_clean.log` (disk, untracked) mtime **05:13:55Z** — NOT regenerated, 2h40m older
  than the pin, so it cannot speak for the pin. The `%TEMP%` run supersedes it.
- **The merge robot gated the pin itself and got red**: `monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md`
  (disk) now reads `base: 13bbcad9…`, `last_seen: 2026-07-30T07:51:14Z`, `attempts: 24`,
  `NEEDS-HUMAN`, reason `verify gate red in monitor (verify.sh)`.
- **Zero `monitor/` merges for 3h24m** (last 04:29:32Z; live `merge.log` mtime 07:53:43Z).
  `merge.lock` pid 27200, mtime 07:40:37Z — **the merger is running, not wedged.**
- **Detector matrix reproduced exactly at the pin**: 5 of 6 still absent
  (`sweep:EXIT-`, `reap:EXIT-`, `BOARD-QUERY-FAILED`, `SUPPLY-UNKNOWN:`, `revive:GIT-EXIT-`,
  and S30's untested `SCAN FAILED (rc=`); only `merge:EXIT-` survives. The two `serve:` values
  exist **only** on `873d62ee`'s line of descent — cycle 49's "do not revert" caveat still binds.

**CORRECTION I OWE ON MY OWN CYCLE-49 NUMBER: four branches, not five.**
`opsm-c26-never-tried-branches-tie-at-zero` left the group at 07:26:09Z for a genuine conflict
of its own. The four still carrying master's own traceback: `a3-campaign-devpile`,
`c13-certificate-bridge-two-halves`, `s38-append-only-probe-branch-blind`,
`s39-writes-into-the-live-master-tree`.

**NEW — nobody acted (07:13:56Z → 07:53:56Z).** 8 commits landed, none touching `reflex.py`;
no new board item (newest `S41` @ 07:01:33Z), no new inbox (newest 07:09:16Z), no mailbox
paragraph after 07:13Z. **The recorders were recording** — 8 commits, 2 `board.log` lines,
3 bus messages, `merge.log` advancing every few minutes — so this is absence of the *event*.
The handover was read past, not missed.

**NEW — work is being marked delivered into the frozen territory.** `board.log` (disk):
`2026-07-30T07:37:50Z DONE S39-… by RES-4` and `CLAIM S40-…` in the same second, while
`origin/agent/s39-…` had been flagged `verify gate red in monitor` since 05:10:24Z —
**18 minutes before it was declared done.** `c13` likewise sits in `board/done/`.
`monitor/mergequeue.py:205-232` `probe()` itself reports this shape as `risk`, so the fleet's
own instrument calls it a defect, not a definition.

**PENDING REFUTATION (R1), do not act on yet:** `s39`/`s38`/`c13` appear to hold an intact
`reflex.py`, but 3-way merge probably still takes master's deletion, and their copies lack the
real memory-threshold fix and the two `serve:` detectors. Verdict pending `git merge-tree`.

**VERIFIED STANDING (not new):** no probe asks "is master itself green". `git show
13bbcad9:monitor/scan.py` — 26 `PROBES` (`:1422-1449`), none runs a territory gate;
`run_tests()` (`:1454-1466`) is hardcoded to `("engine-rig","theory-compiler")` — **`monitor`
is not in it.** Prior art `DRIFT-20260730T0656Z:197`; now confirmed at the pin, so cite as
standing rather than re-argue.

## Posted to the bus 07:57Z
Items 1–4 and 6 above, with item 5 explicitly flagged as under refutation, and cycle 49's
remediation caveats repeated verbatim (forward-only on the current file; never
`git revert 873d62ee`; never `git checkout cd048b32 -- monitor/reflex.py`; a `monitor/`-touching
fix branch cannot itself merge).
