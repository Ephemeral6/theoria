# The probe fired — 2026-07-31T12:19Z, rung 1

Authorised by the owner in chat ("放行包批准，level2 和 S31 探针都烧"),
registered first as `monitor/spec.py` row **#9**.

## Verdict: both axes witnessed. The item's question is answered yes.

From `proxy/var/ledger.jsonl` (gitignored by design; records quoted here):

* **axis 1 — real arm identity on a non-incident record**:
  `env_step` carrying `"arm": "bare_cc"`, `"game_id": "ar25-0c556536"`.
* **axis 2 — real upstream**:
  `run_start` carrying `"env_upstream": "https://three.arcprize.org"`,
  run id `r-1423000575c34ccd`.

Spend, from `proxy/var/spend_gate.jsonl` (campaign `s31-live-arm-probe`,
reservation `res-6ff9e7205c0742f2`, caps $0.05 / 10 actions):

| seq | what | actions | usd |
|---|---|---|---|
| 14713 | `/api/scorecard/open` (env) | 1 | 0.00 |
| 14714 | `/api/cmd/RESET` (env) | 1 | 0.00 |
| 14715 | `/v1/messages` (model, loopback) — raised before a price | 0 | 0.00 |
| 14716 | release — "s31 live probe finished" | — | — |

**Total: 2 ARC actions, $0.00, reservation released.** The scorecard was
left open by the crash and auto-closes server-side (~15 min,
ACCESS_CHECK §3); its total is 2 requests inside the registered cap.

## The crash, honestly

The probe exited nonzero on `http.client.RemoteDisconnected` — thrown by
the **loopback MockProvider** during the single `decide()` (rung 1 keeps
the model half on loopback; the mock closed the connection mid-response).
The live env path had already done its work. So: a rung-1 harness defect
in the mock's lifecycle, *after* both witnesses landed — not a live-path
failure, and nothing about it weakens the verdict above. ACTION1 was
never sent; the pass criteria do not require it.

## The `credential_in_body` incident, adjudicated

The env proxy recorded `kind: credential_in_body` on `/api/cmd/RESET`:
"a key-shaped string appeared in a request body". The RESET body
legitimately carries the scorecard `card_id` — a 36-character GUID, the
same shape as `ARC_API_KEY` (CLAUDE.md masks it as `len 36`). The guard
distinguishes value from shape: a **value** match (the registered secret,
known to `redact.VAULT`) refuses the request; a **shape** match records
and forwards — which is what happened, and the request was forwarded and
billed. Ruling: shape collision, working as designed, no credential left
this machine. A follow-up for the proxy territory: teach the body guard
that `card_id` fields are expected GUIDs, so this incident class stops
firing on every RESET.

## What a green axis pair does not mean (restating the plan's §6)

One probe record makes the shared ledger's real-arm histogram read `1`;
it does not mean the arms are running through it routinely. The
three-territory wiring gap of `DELIVERY_RULING.md` §4 stays open and
owned.
