# `/proxy/` — status

**P-2 delivered: the double proxy, the shared ledger format, and the checks
that make Phase 1's three closure properties falsifiable rather than asserted.**
70 tests pass. Nothing here has spent a dollar or reached the internet.

## Against the ticket's acceptance list

| Required | State |
|---|---|
| one arm plays a mock game through both proxies | ✅ `python -m proxy.runner --mock` — 28 actions, WIN, 3 levels |
| the ledger lands on disk | ✅ `proxy/var/ledger.jsonl`, append-only, canonical JSON, LF |
| the run replays from the ledger, frame hashes equal | ✅ `python -m proxy.replay --run-id <id> --mock` → `PASS`, 29 steps compared |
| sealing test green | ✅ `tests/test_seal.py` — 10 tests, including the arm-side and proxy-side halves |
| the guard proves a sealed request is refused **and recorded** | ✅ refused with 403; recorded three ways (`guard_block`, `incident`, and an `env_step` with `frames: null`) |
| `LEDGER_FORMAT.md` written before the code | ✅ normative; `ledger.py` is its executable form |
| environment proxy: base URL only, key injected inside, full traffic recorded | ✅ |
| model proxy: usage verbatim, price table versioned separately | ✅ `pricing/pricing_v1.json`, hashed into every `model_call` |
| variant layer with constructive justification per variant | ✅ 4 specs, loader refuses one without a justification or with an illegal operator |
| score reconciler | ✅ `reconcile.py` — and it also recomputes the derived level fields |

Beyond the list: every check has a companion test that forges the ledger and
asserts the check goes red (D-014).

## What this does not yet do

* **It has never seen the live API.** Everything runs against
  `proxy/mock/`. The first live run should expect surprises in exactly two
  places — the scorecard's shape, which `reconcile.scorecard_score` handles two
  ways and will need a third if the real one differs, and RESET's cross-session
  semantics, which the mock models optimistically.
* **`g50t-5849a774` is registered non-deterministic** in
  `arc-recon/data/precheck.json`. A replay failure on that game means the world,
  not the harness. The other three development-pile games have not been
  prechecked at all, so a replay failure there is genuinely ambiguous until
  they are.
* **Streaming is buffered, not passed through live** (D-012). Correct for
  recording; wrong for an arm that renders tokens as they arrive.
* **Three-arm integration is not done.** The proxies take an arm as a base-URL
  pair and `runner.run_game` takes an `arm_factory`, so wiring `baseline-arms`
  in is configuration rather than code — but it has not been done, and
  `baseline-arms/` belongs to another surface.
* **The v0 → v1.0 ledger lift is specified, not written.**
  `LEDGER_FORMAT.md` §7 describes `tools/upgrade_ledger.py`; the tool does not
  exist yet. Until it does, `baseline-arms/ledger.jsonl` and this one cannot be
  concatenated.

## Where the credential lives

In `.env` at the repo root, read inside the proxies and nowhere else. It is not
in any tracked file here, and `tests/test_seal.py` asserts the ledger never
contains it — including when an arm puts a key-shaped string in a request body,
which is recorded as a `credential_in_body` incident and scrubbed on the way to
disk.
