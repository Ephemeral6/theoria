# A19 — bare_cc seal split (GAP-5 closed)

Ticket: `A19-bare-cc-seal-split` · territory `baseline-arms` ·
branch `agent/a19-bare-cc-seal-split` · base `4c08ea6be6ff480d9b7cfcd6be8bd17c2e9e3749`

## What was delivered

`STATUS.md` GAP-5 registered that this track satisfied neither half of
`Theoria.md` Phase 1's seal: `arc_client.py:137 load_api_key()` opened `.env`
inside the arm, `arc_client.py:199` parked the value in `self._key` for the
whole run, and calls went straight to ARC with no proxy. The credential is now
out of the arm process.

**New — the credential's own process**

* `baseline-arms/harness/key_proxy_server.py` — a transparent forwarder. The
  **only** code left in this track that reads `.env`, and it runs in a child
  process. Injects `X-API-Key`; passes method, path, query, body, cookies,
  status and response body through unaltered.
* `baseline-arms/harness/key_proxy.py` — the parent-side supervisor, which
  contains **no credential reader at all**. That is the mechanism, not a
  convention: the arm imports this module and cannot reach a key through it.
  File handshake (not stdout — cp936 mangles the child's banner), HTTP
  shutdown before `TerminateProcess`, `atexit` hook, and a `--parent-pid`
  watchdog in the child for a hard-killed parent. Shapes taken from
  `theoria-arm/harness/proxy_process.py`, read only.

**Changed — the arm**

* `arc_client.load_api_key()` raises `CredentialInArmError`. Kept rather than
  deleted because GAP-5 names it by line number; a reader following that
  pointer lands on the explanation.
* `ArcClient.__init__`: `self._key = api_key` — no fallback read. Default
  base URL comes from `ARC_BASE_URL` (set by `key_proxy.sealed_upstream()`).
* Second conjunct, made local: a keyless client pointed at the real upstream
  raises `UnproxiedEgressError` **before** the socket and **before** the
  shared pool is charged. Mirror-image guard in the child: a request arriving
  with an `X-API-Key` header is answered `400 ARM_SENT_A_KEY` and never
  forwarded, so the proxy cannot become the thing that hides GAP-5.
* All five spending entry points wired: `run_pilot.py`, `run_campaign.py`,
  `campaign.py`, `probe_api.py`, `probe_action_variants.py`.

**Deliberately unchanged**: the cookie jar, the probe log, the spend gate and
the sealed-pile guard all stay in the arm, because every figure
`BUDGET_REPORT.md` must re-derive was measured on them. The jar survives the
extra hop because the child strips `Domain=` and `Secure` from `Set-Cookie`
(the loopback hop is neither that host nor https) and touches nothing else.
`probe_log.jsonl`'s `url` still names the canonical upstream; `wire_url` and
`proxied` are new fields recording the actual hop, so lines written after this
ticket stay comparable with every line written before it. A transport failure
is still `-1`, not the child's 599.

**Numbers**

| | |
|---|---|
| territory suite, before A19 (this worktree) | 533 passed, 1 skipped, 0 failed |
| territory suite, after A19 | **552 passed, 1 skipped, 0 failed** |
| new tests | 19, all in `tests/test_seal_process.py` |
| network calls / API calls / spend | 0 / 0 / $0.00 |

The headline test plays a **whole mock game** — scorecard open, RESET, three
model-driven ACTIONs, scorecard close — in a *fresh interpreter* with
`ARC_API_KEY` removed from the environment, asserting by variable **name** that
it is absent, that `load_api_key()` raises, that the supervisor never imported
the reader module, and that the mock upstream nonetheless received the sentinel
on every one of its hits. `bare_cc.call_model` is replaced by a canned envelope,
so no `claude -p` runs and nothing is billed.

Negative controls, since a check never seen to fail is not evidence: a proxy
started with no key injects nothing; a client holding a key is refused rather
than forwarded; the keyless-egress refusal is shown to be about the destination
by allowing the same client through the proxy; `rewrite_set_cookie` is asserted
to drop only the two attributes it must, and the input is asserted to have
contained them.

Artefacts: `MANIFEST.json` (14 files, 264057 bytes), `verify.sh`, `NOTES.md`,
`results.json`, this file.

## A defect this ticket introduced and caught

`resolve_key` was first written as "read `.env`, fall back to keyless if it is
missing". The negative control whose entire purpose is to show a keyless proxy
injecting nothing therefore started a child **holding the live credential** on
any machine that has a `.env` — which is every developer machine here. The
control caught it within the hour; the assertion failed before any request was
made, and no value was printed, logged or written. `--no-require-key` now means
keyless outright and never consults `.env`, pinned by a machine-independent
`resolve_key` unit test. Recorded in `DECISIONS.md` D-026: an optional
credential is not a credential policy.

## Inputs read, read-only

`theoria-arm/harness/proxy_process.py` and `theoria-arm/tests/test_seal_process.py`
(the templates), `proxy/env_proxy.py` (to decide against routing through it),
`Theoria.md` Phase 1, `baseline-arms/STATUS.md`, `BUDGET_REPORT.md` §9.
No file outside `baseline-arms/` was modified.

## Gaps and disclosures

1. **The two `--allow` paths on the sealed-pile check are disclosed here.**
   `verify.sh` was regenerated with `--allow baseline-arms/STATUS.md --allow
   PARTNER_SYNC.md`. Both files already contained sealed-pile identifiers
   before this branch existed — `STATUS.md` in its pre-existing INC-BA-001
   contamination-registration paragraph, `PARTNER_SYNC.md` in paragraphs other
   territories wrote — which is the documented exception. Proven mechanically
   rather than asserted: over all files this branch changes, the number of
   **added** lines containing any sealed identifier is **zero**, and both of
   these files are pure appends (51 and 6 added lines, 0 removed). The three
   new source files contain zero. The identifiers themselves are deliberately
   not written here.

2. **The red baseline `start_ritual` reported was a worktree artefact, not
   master.** Master in the main checkout runs 534 passed / 0 failed. Two
   separate causes, neither introduced by A19, both pre-existing:

   * `baseline-arms/schema_traces/**` is gitignored, so a linked worktree never
     checks it out and 3 tests in `test_schema_column.py` fail instead of
     skipping. `schema_column.resolve_root()` documents the escape hatch for
     exactly this case; every suite number above was measured with
     `THEORIA_SCHEMA_TRACES` pointed at the main checkout's payload. The skip
     guard keys on the container directory, which exists, rather than on the
     payload, which does not — so it fails where it means to skip. Not fixed
     here: it is not this ticket's file.
   * `baseline-arms/runs/` **is not worktree-reproducible.** The committed
     `runs/MANIFEST.json` records evidence hashes computed in the main
     checkout, where tracked files still sit on disk with CRLF
     (`out/pilot_g50t_sonnet_rerun.json`: 28 CRLF, 811 bytes). A fresh worktree
     checks the same file out with LF (783 bytes, byte-identical after newline
     normalisation), so `archive_runs.verify()` computes different digests and
     3 tests in `test_archive_runs.py` go red on the **first** suite run in any
     new worktree. The suite then self-heals, because
     `test_rebuilding_produces_the_same_digest` calls `archive_runs.build()`,
     which rewrites ~21 tracked files.

     **A19 deliberately does not commit that rebuild.** It would put
     worktree-local provenance (`branch: agent/a19-…`, `worktree:
     …\.worktrees\a19`) onto master and break again for the next worktree.
     Those files were restored with `git checkout --` before the commit, so the
     diff contains only this ticket's work. A monitor re-running the suite on a
     fresh worktree will see the 3 archive failures once, then green.

3. **Flight resumption is not adjudicated here, by design.** This ticket
   delivers the split and the evidence. Whether `bare_cc` regains flight
   status, and whether `p1-seal-test`'s left conjunct now holds for all three
   arms, is the monitor's re-adjudication.

4. **`api_key=` survives as a constructor parameter**, used by 13 existing
   tests as the literal `"x"`. It is not a path that can *obtain* the real
   credential — nothing in the arm reads `.env` any more — and the two guards
   above mean a stub cannot turn into live egress. Stated rather than hidden.

5. Not attempted: sharing `theoria-arm`'s `EnvProxyProcess` instead of writing
   this track's own supervisor. The reasoning and its cost (duplicated Windows
   lifecycle code in two territories) are in `DECISIONS.md` D-026.

## Gate output, verbatim

```
== verify.sh :: A19 :: agent/a19-bare-cc-seal-split ==
[PASS] tests -- baseline-arms
[PASS] MANIFEST hashes reproduce
[PASS] boundary -- only baseline-arms changed
[PASS] sealed pile untouched
[PASS] credential never entered a tracked file
[PASS] delivered: baseline-arms/runs/2026-08-01T044513Z-A19/MANIFEST.json
-- 6/6 green
```
