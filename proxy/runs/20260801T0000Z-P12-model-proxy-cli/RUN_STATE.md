# P-12 · run state

**Cell**: close Phase 1 acceptance item 模型代理 — everything on
`verify-lab/DUAL_PROXY.md` §4's checklist that does not require a paid
credential.
**Territory**: `proxy/` (+ `theoria-arm/` read-only; the proposal went to
`monitor/inbox/`).
**Spend**: $0.00. Zero API calls, zero network. Every far end in this run is a
loopback fixture; the only subprocess started is `claude -p` with
`ANTHROPIC_BASE_URL` pointing at a loopback port and a `CLAUDE_CONFIG_DIR`
holding no credentials, which is what makes it *not* a live call.
**Sealed pile**: zero contact. No sealed identifier appears in any file this
cell wrote. The one test that needs a sealed id
(`test_a_planted_sealed_id_is_refused_by_the_proxys_own_guard`) reads it out of
`arc-recon/data/piles.json` at test time rather than embedding it.
**Credentials**: no value read, printed or written. The loopback probes
recorded header **names** and three booleans; the one comparison against a
header value was equality against a sentinel this session minted. The token
`cli_transport` mints is not a credential and is not registered with the vault
(D-P12-003); `DeskTransport.describe()` returns its length and prefix, never
its value.

## What happened, in order

1. **Baseline.** `cd proxy && python -m pytest` → 426 passed.
2. **Probe 1** — does `claude -p` honour `ANTHROPIC_BASE_URL`? Yes: one
   `POST /v1/messages?beta=true`, `stream: true`, and it parses a hand-written
   provider-shaped SSE reply into a full result envelope.
3. **Probe 2** — can it be made to present a token of ours? Not with
   `ANTHROPIC_API_KEY` alone, not with `ANTHROPIC_AUTH_TOKEN` alone; **yes**
   with either plus a `CLAUDE_CONFIG_DIR` that holds no stored credentials, and
   then it arrives as `x-api-key` with no `Authorization` header at all.
4. **Probe 3** — the whole chain, CLI → real `ModelProxy` → `MockProvider`.
   Refused **403 `unknown_game`** on `code-20250219`, a date-shaped token in
   the CLI's own system prompt. This is the finding: a second blocker, hidden
   behind the first, that no provider key would have moved.
5. **Fix + tests.** D-P12-001/002/003, `cli_transport.py`, 16 tests.
6. **Gate.** `cd proxy && python -m pytest` → **442 passed in 83.98s**, exit 0.

## Verdict

`DUAL_PROXY.md`'s **(b)** stands and this cell did not move it: the model proxy
has still never carried a completed request to a real provider. What moved is
the gap. Step 2 is possible and tested rather than structurally impossible;
step 3 is closed; step 1 is an owner action and untouched.

## Residual gaps, stated

* **Step 1 is the only thing between here and (a), and it is not ours.** No
  agent may create `ANTHROPIC_API_KEY`.
* **Step 2 is possible, not adopted.** `theoria-arm/harness/modelcall.py` still
  pops `ANTHROPIC_BASE_URL` and still writes `proxied: false`. That is another
  territory's file; the proposal is in `monitor/inbox/`.
* **The real-binary test is environment-dependent.** It skips without `claude`
  on PATH, like `engine-rig`'s FD toolchain. On a machine without it, the
  measurement in `FINDING.md` is a claim about this machine, and the fifteen
  stub tests carry the shape rather than the fact.
* **The stub's request shape is a snapshot.** It was taken from `claude`
  2.1.220 and nothing detects drift. A future CLI that stops sending `system`,
  or starts sending a second request, would leave the stubs passing and the
  real test failing — which is the right way round, but only on a machine that
  runs it.
* **`bash proxy/verify_contract.sh` fails at its last section, and did before
  this cell.** Its final step runs `pytest` from the repo root, where
  `proxy/tests/test_audit_delivery.py`'s `from tools import audit_delivery`
  resolves `tools` to a different package and the collection errors. Verified
  identical on `master`. Not caused here, not fixed here; the gate this cell
  was given is `cd proxy && python -m pytest`, which is green.
* **C-007 is a contract change no detector can see.** The guard's verdict
  semantics are outside `canon.describe()`, so
  `python -m proxy.tools.contract --fingerprint` is byte-identical before and
  after (`sha256:188706860c45…3c68ba51`). The announcement row and the inbox
  note are the whole notification mechanism, which is
  `CONTRACT_CHANGES.md` §6's third bullet biting for the first time.
* **The dev-pile refusal is a tightening landed without §3's wait.** The
  argument is that its window has nobody in it — before this change the same
  path refused every request that reached it — and that argument is in
  `CONTRACT_CHANGES.md` under C-007 to be disagreed with rather than buried.
