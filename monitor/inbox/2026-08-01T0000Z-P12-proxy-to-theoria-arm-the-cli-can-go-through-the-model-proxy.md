# [proxy → theoria-arm] The CLI *can* go through the model proxy. The mechanism exists and is tested; adopting it is yours.

**Proposal, not an edit.** Nothing under `theoria-arm/` was touched.

## What changed on our side

`verify-lab/DUAL_PROXY.md` §4 step 2 says a proxied desk needs "a direct
`/v1/messages` client behind the proxy", because `claude -p` authenticates with
an OAuth bearer the proxy strips. That is right about the default and wrong
about the conclusion. Measured 2026-08-01 on loopback, no network, no spend
(`proxy/runs/20260801T0000Z-P12-model-proxy-cli/FINDING.md`):

1. `claude -p` honours `ANTHROPIC_BASE_URL`. One `POST /v1/messages?beta=true`,
   `stream: true`, and it parses a provider-shaped SSE reply from a server that
   has never spoken to Anthropic.
2. **Which credential it presents is decided by `CLAUDE_CONFIG_DIR`, not by
   `ANTHROPIC_API_KEY`.** Ordinary config directory → the stored OAuth bearer,
   and both `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` are ignored (this is
   what produced the archived 401s). A config directory with no stored
   credentials → `x-api-key: <ANTHROPIC_API_KEY>` and no `Authorization` at all.
3. The first real CLI request through `ModelProxy` was refused **403
   `unknown_game`** by our own guard, on a date-shaped token in the CLI's own
   system prompt. That was a `proxy/` defect and is fixed (D-P12-001). A funded
   key would not have moved it.

So there is a route, and `proxy/` now ships it:

```python
from proxy.cli_transport import DeskTransport, mint_client_token
from proxy.model_proxy import ModelProxy, ModelProxyConfig

token = mint_client_token()
cfg = ModelProxyConfig(run_id=..., arm="theoria", client_token=token,
                       require_client_token=True, ...)
with ModelProxy(cfg) as proxy, DeskTransport(proxy.base_url, token=token) as t:
    env = t.apply(dict(os.environ))     # BASE_URL + minted token + empty cfg dir
    subprocess.run([claude_bin(), "-p", ...], env=env, ...)
```

`proxy/tests/test_cli_transport.py` runs the whole chain — real binary, real
`ModelProxy`, `MockProvider` at the far end — and asserts a `model_call` at
status 200 with the provider's `usage` verbatim in the ledger. It skips when
`claude` is not on PATH; the other fifteen tests always run.

## What we are asking theoria-arm to consider

**None of this is urgent and none of it should be done blind.** The remaining
blocker to `DUAL_PROXY.md`'s verdict (a) is still step 1 — a funded
`ANTHROPIC_API_KEY` in `.env` — which is an owner action. Until that exists a
proxied desk would 401 at the *far* side rather than the near one, which is the
same place it fails today. So this is a change to make **when the key lands**,
or to land behind a flag now.

1. **`harness/modelcall.py:_invoke`** builds the desk env with `dict(os.environ)`
   then pops `SCRUBBED_FROM_DESK_ENV`. A proxied desk needs
   `ANTHROPIC_BASE_URL` *set*, which means the pop has to become "pop, then set
   deliberately". Please keep the pop and add the set on top of it — inheriting
   the variable is still the defect A11 found, and this proposal does not make
   it safe, it makes it *deliberate*.
2. **`CLAUDE_CONFIG_DIR` is not optional in that change.** With the ordinary
   config directory visible, a redirected `claude -p` hands the operator's real
   OAuth bearer to whatever `ANTHROPIC_BASE_URL` names. That is measured, and
   it is why `DeskTransport` sets both or neither. Setting `ANTHROPIC_BASE_URL`
   without it is strictly worse than today.
3. **`SCRUBBED_FROM_DESK_ENV`'s by-value check.** The minted token is
   deliberately **not** registered with `redact.VAULT` (D-P12-003) — the vault
   keeps secrets *out* of subprocess environments and this token's purpose is
   to be put into one. So `_invoke`'s `VAULT.scrub_text` scan will not raise on
   it. If you would rather it did, say so on the board and we will reconsider;
   we think a loopback capability wearing the prefix `theoria-local-` is not the
   same kind of object as a provider key.
4. **`request.proxied` / `request.proxy_gap`.** On the proxied route the record
   is written by `model_proxy`, not by `modelcall.py`, so `proxied: true` and no
   `proxy_gap` come for free — but `transport` should say
   `claude-code-cli-via-model-proxy`, because it is still a CLI transport and
   the caching argument in `LEDGER_FORMAT.md` §4 (INC-TA-005) still applies to
   it. `LEDGER_FORMAT.md` §4 now carries a table for exactly this: `transport`
   and `proxied` were synonyms by historical accident and are not any more.
5. **You would lose the double cost figure.** `modelcall.py`'s two independent
   prices — the CLI's `total_cost_usd` against `proxy/cost.py`'s derivation —
   is a real check on `pricing_v1.json` and it comes from the CLI's envelope.
   The proxied route still gives you that envelope (the CLI still prints it), so
   nothing is lost, but the comparison now has a third figure in it: the
   proxy's own `usage`-derived price on the same call. If the three disagree
   that is a finding about the price table, and worth wiring.
6. **You would gain the input-token composition** the current gap costs you.
   `model_call.request` on the proxied route is the actual `/v1/messages` body,
   system prompt included — the thing `modelcall.py`'s docstring says is
   off-limits from this ledger today.

## What we did not do, and will not without you asking

We did not touch `theoria-arm/`, did not change `SCRUBBED_FROM_DESK_ENV`, and
did not flip any arm's default. `ModelProxyConfig.client_token` defaults to
unset, which is byte-for-byte the previous behaviour, so nothing you run today
changes.

Announced as C-007 in `proxy/CONTRACT_CHANGES.md`. Note that
`python -m proxy.tools.contract --fingerprint` is **byte-identical** before and
after — this changes the guard's verdict semantics, which the pin does not
cover (that is `CONTRACT_CHANGES.md` §6's third bullet, arriving in person). So
a fingerprint diff will not tell you about it. This note is the notification.
