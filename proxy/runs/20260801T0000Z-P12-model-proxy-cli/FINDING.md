# P-12 · The model proxy's transport, measured instead of assumed

**Verdict: `DUAL_PROXY.md` §4 step 2 is wrong on its facts, and step 1 is not
the only blocker. Both are now measured. Everything below ran on loopback:
zero network, zero spend, zero sealed-pile contact.**

`verify-lab/DUAL_PROXY.md` rules the model proxy **(b)** — built, never
validated on real traffic, 65 of 65 requests at HTTP 401 — and gives a
six-step checklist to (a). Step 2 reads:

> **`ModelDesk` gets a proxied transport.** Today `harness/modelcall.py` spawns
> `claude -p`, whose OAuth bearer the proxy strips by design, so pointing
> `ANTHROPIC_BASE_URL` at the proxy reproduces exactly the archived 401s.
> Reaching (a) needs a direct `/v1/messages` client behind the proxy.

That is right about what happens by default and wrong about the conclusion. It
was written from the archived 401s, and the 401s were produced by a
configuration nobody varied.

## 1. What was run

Three probes, in order, each answering the question the previous one raised.

| # | question | method |
|---|---|---|
| P1 | does `claude -p` honour `ANTHROPIC_BASE_URL` at all? | CLI → a loopback recorder that answers `/v1/messages` in the provider's shape |
| P2 | which credential does it present, and can it be made to present ours? | same, varying `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` / `CLAUDE_CONFIG_DIR` |
| P3 | does the whole chain work? | CLI → the real `proxy.model_proxy.ModelProxy` → `proxy.mock.model_mock.MockProvider` |

The recorder in P1/P2 stored **header names only** plus three booleans; no
header *value* was written, printed or compared except by equality against a
sentinel this session minted. `claude` version 2.1.220.

## 2. Result 1 — the CLI is an HTTP client, not a wall

One request, and only one:

```
POST /v1/messages?beta=true        stream: true
headers: accept, accept-encoding, anthropic-beta,
         anthropic-dangerous-direct-browser-access, anthropic-version,
         authorization, connection, content-length, content-type, host,
         user-agent, x-app, x-claude-code-session-id, x-stainless-*
body keys: context_management, max_tokens, messages, metadata, model,
           stream, system, thinking, tools
```

Handed a hand-written provider-shaped SSE reply it produced a complete result
envelope — `"result"` carrying our text, `usage.input_tokens: 11`,
`usage.output_tokens: 7`, `total_cost_usd: 4.6e-05` — from a server that has
never spoken to Anthropic. So the desk's transport **is** HTTP, `claude -p` is
a client, and "the transport is CLI not HTTP" is a statement about the process
boundary rather than about the protocol.

## 3. Result 2 — the credential depends on `CLAUDE_CONFIG_DIR`, not on `ANTHROPIC_API_KEY`

| configuration | header sent | is it ours? |
|---|---|---|
| `ANTHROPIC_API_KEY=<sentinel>` | `authorization` | no — the stored OAuth bearer |
| `ANTHROPIC_AUTH_TOKEN=<sentinel>` | `authorization` | no — the stored OAuth bearer |
| `ANTHROPIC_API_KEY=<sentinel>` **+ `CLAUDE_CONFIG_DIR=<empty dir>`** | `x-api-key` | **yes**, and no `authorization` at all |

The CLI prefers stored credentials over both environment variables. Point it at
a config directory that has none and it falls back to `ANTHROPIC_API_KEY` and
presents it as `x-api-key` — which is exactly the header the model proxy
already strips and replaces.

**This is the whole of step 2.** No direct `/v1/messages` client is required.
`ANTHROPIC_API_KEY` on the *client* leg does not have to be a funded provider
key; it has to be a token the proxy recognises. The funded key belongs on the
far side, injected by the proxy, where the design always put it.

### The corollary is a finding about the existing arm

With the ordinary config directory visible, a `claude -p` subprocess hands **the
operator's real OAuth bearer** to whatever `ANTHROPIC_BASE_URL` names.
`theoria-arm/harness/modelcall.py:SCRUBBED_FROM_DESK_ENV` pops that variable
before the subprocess starts, and A11's comment on it — "a silently redirected
desk is worse than a broken one" — is now measured rather than reasoned. Any
caller that sets `ANTHROPIC_BASE_URL` deliberately **must** set
`CLAUDE_CONFIG_DIR` in the same breath, or it has redirected a live credential
to a host of its choosing. `proxy/cli_transport.py:DeskTransport` does both or
neither, which is why it is a context manager and not a dict.

## 4. Result 3 — the second blocker, which the 401s were hiding

The first real `claude -p` request ever put through `ModelProxy` was not
answered 401. It was answered **403 by our own guard**:

```json
{"error":"refused by the sealed-pile guard","rule":"unknown_game",
 "game_id":"code-20250219",
 "detail":"code-20250219 is in neither pile of cut v1. The guard fails closed:
           widen the cut deliberately rather than by accident."}
```

`code-20250219` is a token inside the CLI's own system prompt. `guard._GAME_ID`
matches two-to-six alphanumerics, a hyphen and eight hex digits; `20250219` is
eight hex digits. `ModelProxyConfig` built its guard with the default
`unknown_policy="deny"` — correct for the environment proxy, where a request
*addresses* one game named on purpose, and a false-positive machine on a
20,000-character prompt. `theoria-arm`'s `ModelDesk._screen_the_pile` docstring
had already reasoned its way to this ("The proxy's request path can afford
`unknown_policy = deny` because a request names one game deliberately; a
20,000-character prompt is not that") — for the arm's own screen, without
noticing it condemned the proxy's.

**A funded `ANTHROPIC_API_KEY` would not have moved this by one inch.** The
request never reached `_forward`. Nobody could have found it, because nobody
had ever got past the 401 to look — which is the general lesson: a blocker
downstream of another blocker is invisible until the first one is removed, and
"the only missing piece is X" is a prediction until X is removed.

## 5. What changed in `proxy/`

| | |
|---|---|
| `model_proxy.py` | the default guard is `unknown_policy="allow"` on this path only (D-P12-001); a **development**-pile id in a prompt is refused `game_id_in_prompt` (D-P12-002); an optional `client_token` authenticates the caller before the injected provider key can be spent (D-P12-003) |
| `cli_transport.py` | new. Mints the token, builds the desk's environment, owns the credential-free `CLAUDE_CONFIG_DIR`. Never returns the token's value from `describe()` |
| `tests/test_cli_transport.py` | 16 tests. Fifteen run always, against a stub carrying the request shape recorded above; the sixteenth runs the real binary and skips when it is absent |

Nothing given up by the guard change: the sealed set is a fixed enumeration, so
an id outside the register is not a sealed game. `deny` bought a 403 on every
request and caught none. The sealed refusal is unchanged and is now
**demonstrated** rather than asserted —
`test_a_planted_sealed_id_is_refused_by_the_proxys_own_guard` plants an id read
out of the cut at test time (never written into a tracked file) and requires
403, `surface: "model_proxy"`, a `guard_block`, a `sealed_pile_in_prompt`
incident, and zero forwarded calls. That is `DUAL_PROXY.md` §4 step 3, closed.

## 6. Where the checklist stands now

| step | before | after | owner |
|---|---|---|---|
| 1 · a funded `ANTHROPIC_API_KEY` in `.env` | open | **open — unchanged, and no agent may create it** | owner |
| 2 · `ModelDesk` gets a proxied transport | "structurally impossible without a new client" | **possible; the mechanism exists and is tested. The arm still has to adopt it** | theoria-arm |
| 3 · the guard exercised on the model path through the proxy | asserted | **closed** | proxy |
| 4 · a live ledger record: `model_call`, 2xx, `proxied: true`, no `proxy_gap` | open | **open — every part but the funded key is now demonstrated against a loopback provider** | theoria-arm + owner |
| 5 · `count.py`'s `model_proxy_succeeded` non-zero | open | open | verify-lab |
| 6 · the two prose corrections | open | open (this file supersedes §4 step 2's reasoning; §2's verdict **(b)** still stands) | verify-lab |

**The verdict does not move.** (b) is still the honest word: the model proxy
has still never carried a completed request to a *real* provider, and this cell
did not spend a cent to find out otherwise. What moved is the size of the gap.
Before: one blocker, believed to require a new HTTP client in another
territory. After: two blockers found, one closed here, and the remaining one is
a single owner action with a tested path waiting on the other side of it.
