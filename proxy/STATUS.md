# `/proxy/` — status

**P-12 delivered: the model proxy has carried a real `claude -p` request, end
to end, into the ledger. Against a loopback provider — no network, no spend —
but with the actual vendor binary at the near end, the real `ModelProxy` in the
middle, and a `model_call` at status 200 with the provider's `usage` verbatim
at the far end. `DUAL_PROXY.md` §4's step 2 said that route was structurally
impossible; it is not, and the reason it looked impossible is now measured
rather than reasoned.** 442 tests pass. Nothing here has spent a dollar or
reached the internet.

## P-12 — two blockers, not one

`verify-lab/DUAL_PROXY.md` rules the model proxy **(b)**: built, never
validated on real traffic, 65 of 65 model calls at HTTP 401. That verdict is
still right and this cell did not move it. What moved is the size of the gap
behind it. The full measurement is
`runs/20260801T0000Z-P12-model-proxy-cli/FINDING.md`; the three results:

1. **`claude -p` is an HTTP client, not a wall.** It honours
   `ANTHROPIC_BASE_URL` — one `POST /v1/messages?beta=true`, `stream: true` —
   and parses a hand-written provider-shaped SSE reply into a complete result
   envelope with `usage` and `total_cost_usd` intact.
2. **Which credential it presents is decided by `CLAUDE_CONFIG_DIR`.** With the
   operator's ordinary config directory visible it sends its stored OAuth
   bearer and ignores both `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` —
   which is what produced the archived 401s. Pointed at a config directory
   holding no stored credentials it sends `x-api-key: <ANTHROPIC_API_KEY>` and
   no `Authorization` at all. So `ANTHROPIC_API_KEY` on the *client* leg does
   not have to be a funded key; it has to be a token the proxy recognises, and
   the funded key stays where the design always put it — injected by the proxy,
   on the far side. `proxy/cli_transport.py:DeskTransport` is that route.
3. **A second blocker the 401s were hiding.** The first real CLI request ever
   put through `ModelProxy` was refused **403 by our own guard** —
   `unknown_game` on `code-20250219`, a date-shaped token inside the CLI's own
   system prompt. `_GAME_ID` matches two-to-six alphanumerics, a hyphen and
   eight hex digits, and `ModelProxyConfig` had inherited the environment
   proxy's `unknown_policy="deny"`. **A funded key would not have moved it by
   an inch**, and nobody could have found it, because nobody had ever got past
   the 401 to look. That is the general lesson worth keeping: "the only missing
   piece is X" is a prediction until X is removed.

What changed here (D-P12-001/002/003, announced as C-007 in
`CONTRACT_CHANGES.md` — it changes the guard's verdict semantics, which §4's
detector cannot see, so the fingerprint is byte-identical before and after):

| | |
|---|---|
| the model proxy's default guard | `unknown_policy="allow"` **on this path only**. Nothing detectable is lost: the sealed set is a fixed enumeration, so an id outside the register is not a sealed game, and `deny` bought a 403 on every request while catching none |
| a **development**-pile id in a prompt | refused `game_id_in_prompt`, 403. `verdict()` allows it — it answers "may this game be played" — and Theoria.md:353's 硬规 is the stricter question about every id. The arm's `ModelDesk._screen_the_pile` already enforced it; enforcing it here makes it a property of the recorded path rather than of one caller |
| `ModelProxyConfig.client_token` | optional, off by default, byte-for-byte the old behaviour when unset. Set, the proxy 401s an unauthenticated caller *before* `_forward` — because an unauthenticated loopback port in front of a funded key is an open relay to that key |
| `proxy/cli_transport.py` | new: mints the token, builds the desk's environment, owns the credential-free `CLAUDE_CONFIG_DIR`. `describe()` never returns the token's value |
| `tests/test_cli_transport.py` | 16 tests. Fifteen run always, against a stub carrying the request shape recorded from the real binary; the sixteenth runs the binary and skips when it is absent, on the same footing as `engine-rig`'s FD toolchain |

**`DUAL_PROXY.md` §4 step 3 is closed here.** The sealed-pile refusal on the
model path was asserted and is now demonstrated:
`test_a_planted_sealed_id_is_refused_by_the_proxys_own_guard` plants an id read
out of the cut at test time — never written into a tracked file — and requires
403, `surface: "model_proxy"`, a `guard_block`, a `sealed_pile_in_prompt`
incident, and zero forwarded calls.

**What P-12 does not do, stated plainly.** It does not make the verdict (a).
The model proxy has still never carried a completed request to a *real*
provider, and this cell did not spend a cent to find out otherwise. Step 1 — a
funded `ANTHROPIC_API_KEY` in `.env` — is untouched and is an owner action no
agent may take. Step 2 is now possible but **not adopted**:
`theoria-arm/harness/modelcall.py` still pops `ANTHROPIC_BASE_URL` and still
writes `proxied: false`, which is another territory's file; the proposal is in
`monitor/inbox/`. Steps 4, 5 and 6 remain open and belong to theoria-arm and
verify-lab.

One thing found in passing that is a finding about the *arm*, not about this
directory: with the ordinary config directory visible, a `claude -p` subprocess
hands the operator's real OAuth bearer to whatever `ANTHROPIC_BASE_URL` names.
`modelcall.py:SCRUBBED_FROM_DESK_ENV` pops that variable, and A11's comment on
it — "a silently redirected desk is worse than a broken one" — now has a
measurement under it. Any caller that sets the variable deliberately must set
`CLAUDE_CONFIG_DIR` in the same breath; `DeskTransport` does both or neither,
which is why it is a context manager and not a dict.

## S15 — the chain

**S15 delivered: the ledger is a hash chain — each record carries the digest of
the line before it, `tools/verify_chain.py` re-derives the whole chain, and
editing a landed record is now detectable. The half that is not done is the one
that matters most: publishing the head outside the file is still discipline, not
a gate (see RED-40).** 323 tests passed at S15; the count above is current.

Previously: S9 made the canon additive-safe, made canonical the five fields P-8
was already writing, and stopped a change that narrows the shared contract from
arriving on another track unannounced.

Previously: P-9 delivered the frozen scorer, the canon guard, a red team that
landed 29 attacks and now lands none, and the first real data point behind
Phase 1's bit-exact replay line. P-2 built the double proxy, the shared ledger
format, and the checks that make Phase 1's three closure properties falsifiable
rather than asserted.

## S9 — the closure that cost $2.695

`LEDGER_FORMAT.md` §4 closed `model_call`'s field set **after** P-8 began
writing `beat`/`label`/`transport`/`proxied`/`proxy_gap` on that record. Arms
import `proxy/` as a library, so the closure arrived on a commit the `theoria`
arm had never touched. Its first live desk call was refused at serialisation
after the provider had been paid; the reply was discarded and the ledger held
zero `model_call` records (INC-TA-006, reported by W-1521 and fixed on its side).

Three things changed here, and the reasons are D-030 and D-031:

| | |
|---|---|
| `canon.py` is **additive-safe** | an unlisted field on `env_step`/`model_call` is warned about (`UnknownField`, tallied in `Ledger.unknown_fields`) and **written**. A writer that runs after the money is spent may not refuse — a refusal cannot un-spend it, only destroy the evidence. What stays refused is what is *wrong* rather than unknown: v0 spellings, dollar figures (§5), caller-set envelope fields, missing required fields, corrupting types |
| the five fields are **canonical** | §4 lists them, with what each is for. `beat` is the one that matters most: it is why Theoria.md constraint 8 is checkable *from the ledger* rather than asserted in prose |
| tightenings must be **announced** | `CONTRACT_CHANGES.md` is the procedure; `canon_contract.json` pins `canon.describe()` plus `ledger.py`'s three registries; `python -m proxy.tools.contract` diffs and labels each delta `additive`/`tightening`; `tests/test_contract_changes.py` fails the suite when they disagree. **The fingerprint is the authority and the classifier only the explanation** — an unmodelled delta reads as a tightening, because "found no tightening" and "understood the change" are different statements and only the second is a clearance |

The read side moved with it: `validate_ledger.py` reports an unlisted field as a
**notice** and leaves the verdict alone, because the frozen scorer calls it from
S-12 and a scorer that fails a run over a field it could ignore is the same
mistake one direction over.

```bash
cd proxy && bash verify_contract.sh          # the S9 green light, offline
python -m proxy.tools.contract --fingerprint # the line an importing track pins
```

**For a track that imports `proxy/`:** put that fingerprint in your run manifest
and *diff it between runs*. `proxy/` can publish it; only you know which two
runs were supposed to be comparable. A pin that is never compared documents an
incident afterwards instead of preventing one.

Two things an adversarial review of this change caught, kept here because both
are the same mistake wearing different clothes:

* **The warning was itself a refusal.** `warnings.warn` raises whenever the
  ambient filter says `error`, and `UnknownField` is an `Exception` — so under
  `python -W error` the writer raised, the arm's `except Exception` said "the
  desk failed", and INC-TA-006 was rebuilt out of the warning meant to replace
  it. The tally now comes first and cannot raise; the warning is emitted
  defensively. `verify_contract.sh` runs a real subprocess under a real
  `-W error` to keep it that way.
* **The frozen scorer was only half frozen.** S-12 delegates to
  `tools/validate_ledger.py`, which consults `canon.py`, so this change moved
  what the scorer returns while `arc_v1.py` hashed exactly as before and
  `verify_frozen()` reported all clear. `frozen.json`'s `arc_v1` entry now
  carries `depends_on` and the check covers it. Freezing the source of a rule
  whose behaviour lives partly in its imports is a half-freeze, and a
  half-freeze reads as a whole one.

## Against P-9's acceptance list

| Required | State |
|---|---|
| frozen scorer wired in and frozen, version + hash into `run.json` | ✅ `proxy/scoring/`, `SCORING.md`. `frozen.json` holds the source hash; drift refuses to score; the fingerprint goes into `run_start` **and** `run.json`, and is verified before the game starts |
| each game scored the moment it ends, reconciled against the scorecard | ✅ `runner.run_game` calls `score_run` after `run_end`; the report lands in `proxy/var/scores/<run_id>.json` |
| a disagreement files an incident automatically | ✅ `score_mismatch`, and `score_unreconciled` when the obligation could not be discharged at all |
| absorb baseline's measured caliber (failed 400s unbilled, `total_actions` = successful actions) | ✅ and **extended**: 32/32 real scorecards, four games, two campaigns — `tests/fixtures/scorecard_corpus.json` |
| independent red team writes an attack set | ✅ 46 attacks in `tests/test_redteam.py`; `REDTEAM.md` is the report |
| the sealed test blocks all of them | ✅ **all 46 blocked**, no `xfail` markers left. 29 landed on first contact; each fix keeps the original finding as a comment on the test that closes it |
| the attack set stays resident in the suite | ✅ 44 tests, run on every `pytest` |
| proxy refuses a non-canonical field (F-16) | ✅ `canon.py`, consulted by the writer before serialisation and by `tools/validate_ledger.py` on read. **Narrowed by S9**: it refuses a spelling the format *forbids*; a field the format does not mention is warned about and kept (D-030) |
| migrator interface document for `baseline-arms` | ✅ `CANON_MIGRATION.md`; the migrator itself is `tools/upgrade_ledger.py`, the migration of the stock ledgers is P-12's |
| bit-exact replay spot check on the envelope's first game | ✅ `runs/p9-shell-harden/replay_spotcheck_ar25.json` — 16 sessions, 9 positions, 372 pairwise comparisons, zero disagreements |

Beyond the list: `LEDGER_FORMAT.md`'s two promised tools now exist
(`validate_ledger.py` §18, `upgrade_ledger.py` §7), `env_step` gained the
`response` field that made "complete record" true, and the mock now returns the
scorecard shape 32 real cards actually have.

## The replay spot check, stated at its real size

`baseline-arms`'s harness opens every session with a fixed probe sweep before
the model chooses anything, and it opened fourteen sessions on `ar25-0c556536`;
`arc-recon`'s determinism precheck ran the same opening on the same game in a
different campaign, on a different day, through a different harness. Sixteen
sessions with an identical opening are sixteen replays of that opening, and
they agree bit for bit on all nine positions.

What that is: cross-session, cross-campaign determinism **of the environment**,
on **one** game, for $0.

What it is not: evidence that these proxies reproduce a run. That needs a live
replay through `replay.py` and is still owed. The acceptance line asks for two
games; this is the first.

## What this does not yet do

* **It has never seen the live API.** Everything runs against `proxy/mock/`.
  One of the two surprises this file used to predict has been spent offline:
  the scorecard's shape is now known from 32 real cards and the mock returns it.
  The other — RESET's cross-session semantics — is still modelled optimistically.
* **The ledger is chained but the head is not yet compulsorily published
  (D-024, RED-40).** The chain itself **landed** in S15 (`cd94e19`,
  2026-07-28): every record carries `prev`, the digest of the preceding line's
  bytes as written, assigned inside the same lock as `seq`; `prev` is in the
  envelope so a caller cannot set it; `proxy/tools/verify_chain.py` re-derives
  the whole chain independently and 28 tests in `tests/test_chain.py` each
  perform a real edit and require red. That closes tampering *within* the file:
  edit, delete, insert, swap, truncate-from-the-front are all caught.
  What it does **not** yet close is the half RED-40 actually turns on. A chain
  an attacker can rewrite end to end proves nothing, so the evidence is the
  head recorded somewhere they cannot reach — and publishing it is still
  documented rather than enforced. `runner.py` writes `ledger_head` into the
  per-run record, whose default location is `proxy/var/runs/`, and `var/` is
  gitignored: **the default path publishes nothing.** Until a gate checks a
  run's published head against a tracked manifest, "the head is published" is a
  discipline, and `test_the_runners_default_head_location_is_gitignored` exists
  precisely because the discipline is easy to skip. Two limits are permanent
  and not defects: rewriting the whole chain is undetectable without a
  published head, and the chain proves record order, never that the records
  describe anything that happened.
* **Three guard limits, stated rather than implied (D-022, D-023).** The
  value-join that catches an id split across two fields depends on key order;
  base64 is chased one level; a secret the writer has never seen and that does
  not look like one cannot be redacted — `LEDGER_FORMAT.md` §4 now says so
  instead of claiming otherwise.
* **`g50t-5849a774` is registered non-deterministic** in
  `arc-recon/data/precheck.json`. A replay failure on that game means the world,
  not the harness.
* **Streaming is buffered, not passed through live** (D-012).
* **Three-arm integration is not done.** Wiring `baseline-arms` in is
  configuration rather than code, and it has not been done.
* **Two things the Phase 2 battery still cannot get.** An independent review
  from the battery author's viewpoint closed four of its five stated gaps
  (`arm` and `game_id` on `model_call`, `pricing_ref` in place of a scalar
  cost, `level_boundary` as a recorded field) and left the fifth open: there is
  no turn index distinct from `step_idx`. It also found that `cost.py` never
  reads a record's own `pricing_ref`, so a stream priced under a different
  table yields plausible wrong dollars, and that nothing writes a **per-call**
  cost series — which is the shape the economy metric family is made of. Both
  are registered here and neither is fixed; they are the first items for the
  next pass on this surface.
* **The contract detector sees the pinned contract and nothing else.** The rule
  in `CONTRACT_CHANGES.md` §2 — widening is free, narrowing is breaking —
  applies by its own terms to the spend gate's protocol, the guard's verdict
  semantics and `cost.py`'s pricing tables, and **no code checks any of them**.
  Nor can any test verify that an announcement was written or that the wait
  happened; the board is a board, not a scheduler. Widening the pin is the
  obvious next thing and is not done.
* **§5's dollar ban is a list of names, not a price detector.** `usd_spent` is
  not on the list and is written. That was already true of auxiliary payloads,
  which have always been open; what S9 changed is that the two shapes now
  behave like them. Recorded as a test so it cannot be read as a guarantee.
* **One pinned P-9 artefact no longer reproduces.** `validate_file`'s report
  gained a `notices` key, so the output hashed in
  `runs/p9-shell-harden/MANIFEST.json` differs. Nothing recomputes
  `proxy/runs/*` hashes, so this would have failed silently and only for
  whoever tried to reproduce P-9. Left as documented drift: rewriting a past
  run's manifest to match a later format is the manoeuvre `CANON_MIGRATION.md`
  §7 declines for the same reason.

## Where the credential lives

In `.env` at the repo root, read inside the proxies and nowhere else. It is not
in any tracked file here. Since P-9 the protection runs in both directions: a
credential cannot reach the ledger, and a credential an upstream reflects back
cannot reach the arm either — that leak used to leave the ledger clean, so it
was unrecorded as well as unstopped.

## `credential_in_body` 的误报率已测（S27，2026-07-29）

审计把这条列在「还不能证实」是对的：判断真伪要读请求体，而读请求体本身有风险。
`proxy/tools/triage_credential_incidents.py` 用不读内容的办法把它结了——
每个命中片段只导出形状元信息与 sha256，真伪靠
`sha256(片段) == sha256(活钥匙)` 判定，两边都不需要把值显示出来。

测量（主 checkout + 全部 worktree，1033 个 `.jsonl`）：

* `credential_in_body` incident **2439 条**，其中 `detail` 的互异取值 **1 个**
  ——不是 2439 个发现，是同一条判断被记了 2439 次；
* 启发式全语料命中 394,352 次，**哈希命中活钥匙的：0**；
* 成因：检测器的 UUID 分支匹配到代理自己放进请求体的 `guid` / `card_id`
  （二者实测都是标准 UUID），而每个 ACTION 请求体都带 `guid`。

**误报率实测为 100%（2439/2439），真泄漏 0。**

`redact.py:258-262` 的注释早就写明这个误报是设计时接受的代价，
而那个取向（宁可误报）依然正确。变的是量：2439 条同源误报会让人关掉告警，
而那正是真泄漏溜过去的方式。

**收紧应改调用侧，不要改 `looks_like_credential`**：`env_proxy` 抬 incident 前
排除「命中片段恰好等于本次会话自己的 `guid`/`card_id`」——拿代理自己刚发出去的值
去比，不可能把真钥匙判成良性。**本轮未实施**，理由与判据见
`proxy/runs/20260729T1020Z-S27-credential/FINDING.md`。
