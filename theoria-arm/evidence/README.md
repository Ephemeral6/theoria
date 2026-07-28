# evidence/

Records that are about the *setup* rather than about any one run, kept because
`DECISIONS.md` cites them and a decision whose evidence is a memory is an
assertion.

## `model-proxy-401.jsonl`

The live attempt to route this arm's model calls through `proxy/model_proxy.py`,
made before the arm was written and answering D-P8-002.

The experiment: start the frozen model proxy with no provider key
(`require_key=False`, because there is no `ANTHROPIC_API_KEY` in this repo's
`.env` — it holds `ARC_API_KEY` and nothing else), point the Claude Code CLI at
it with `ANTHROPIC_BASE_URL`, and ask for one cheap completion.

What the file contains, in `LEDGER_FORMAT v1.0` shape, written by the frozen
writer:

| records | what they say |
|---|---|
| 66 `incident` / `bypass_attempt` | the CLI sent an `Authorization` header; the proxy recorded that the client had a credential of its own, and dropped it |
| 65 `model_call`, every one `status: 401` | `{"error": {"message": "x-api-key header is required", "type": "authentication_error"}}` |

The CLI retried until the 180-second subprocess timeout; no request ever
succeeded. `Authorization` is not in `model_proxy.PASSTHROUGH_REQUEST_HEADERS`,
so it is stripped at the boundary, and `_forward` injects `x-api-key` only when
`cfg.api_key` is set — which it cannot be here.

**This is the sealing property working, not a bug.** "No bypass" is structural
precisely because the proxy refuses to carry a client's own credential. The
consequence for this arm is that the designed model route is unavailable
without either an `ANTHROPIC_API_KEY` or a change to `proxy/`, and `proxy/`
belongs to another track. Hence D-P8-002: recorded but not proxied, declared on
every record as `proxied: false`.

No credential appears in the file — checked, and the proxy's `redact.py` is on
the write path in any case.
