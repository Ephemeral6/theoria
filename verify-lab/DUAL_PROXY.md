# DUAL_PROXY — how much real traffic each proxy has carried, and what the paper may say

S32. `Theoria.md` Phase 1 seals the arm behind two proxies, and the paper has
been writing "dual-agent" as though both had been demonstrated. The
2026-07-29 audit quoted *65 `model_call` records, every one 401* against that.
A count with no denominator settles nothing — 65 of 65 and 65 of 65,000 are
different worlds — so this cell produces denominators first and adjudicates
second.

Everything below is recomputed by `verify-lab/dualagent/count.py` on every run
of the territory's suite; the numbers are not transcribed from any README.
`theoria-arm/` and `proxy/` are read-only evidence here and were not touched.

## 1. The two denominators

### Environment proxy — **1009 requests, 924 of them against the live endpoint**

| | requests | runs |
|---|---:|---:|
| forwarded to the **live** game endpoint | **924** | 17 |
| forwarded to a **loopback fixture** | 85 | 7 |
| **total legs written by the proxy** | **1009** | 24 |

All 1009 carry `http.forwarded: true`. The live 924 break down by status as
**200 × 114, 400 × 726, 404 × 84**. The 400s count: the proxy forwarded them,
the credential was applied, and the upstream answered — a rejected *game
action* is not a rejected *request*, and dropping them would understate the
denominator by three quarters. (`dualagent/tests/test_count.py` pins this in
both directions.)

A "request the proxy handled" here means a record written by
`proxy.ledger`'s writer in `LEDGER_FORMAT v1.0` shape with an `http` leg —
`env_meta` or `env_step`. That is deliberately narrower than "a request this
repository made", and the two largest request logs in the tree are **named
exclusions rather than silent ones**:

| ledger | records | proxy legs | why it is not proxy traffic |
|---|---:|---:|---|
| `baseline-arms/ledger.jsonl` | 656 | 0 | the baseline arms' own client format — no `event`, no `http.forwarded` |
| `arc-recon/data/recon_ledger.jsonl` | 1273 | 0 | `arc-recon/client.py` talks to `BASE_URL` directly with its own key |

Folding either in would push the environment proxy's denominator past 2900 and
would be a different claim. The exclusion is checked, not asserted:
`test_the_named_exclusions_really_carry_no_proxy_leg` measures that neither
file contains a single proxy `http` leg.

### Model proxy — **131 requests, 65 model calls, 0 answered**

Its entire recorded history against a real provider is one archived file,
`theoria-arm/evidence/model-proxy-401.jsonl`, written before the arm existed
(`arm: "probe"`, `run_id: "probe-model-proxy"`):

| | count |
|---|---:|
| records total | **131** |
| `model_call` | **65** |
| `model_call` at HTTP 401 | **65** (all of them) |
| `model_call` that succeeded (2xx) | **0** |
| `incident` / `bypass_attempt` | **66** |

So the audit's figure is right and its denominator is the same number: **65 of
65**, not 65 of many. The model proxy has never carried a completed request to
a real provider.

It has completed requests against a *fixture* provider — 32 `model_call`
records at 200, `arm: "mock_arm"`, `model: "mock-model-1"`, from
`proxy/runner.py`'s end-to-end flow. That evidence lives in `proxy/var/`,
which is **gitignored** (`proxy/.gitignore:3`), so it is present on the census
machine and absent from a fresh clone; the tracked, reproducible form is the
proxy track's own suite (`proxy/tests/test_e2e.py`). It is reported separately
and never summed with the 65, because a fixture answering 200 proves the
forward path, the ledger write and the pricing hook execute — and proves
nothing about a real provider.

## 2. The verdict: **(b)**, and why not (a) or (c)

> **(b) The environment proxy is built and validated on real traffic. The model
> proxy is built, and its boundary behaviour is recorded, but it has never been
> validated on real traffic.**

**Not (a).** 0 of 65. And the design no longer even attempts it: `theoria-arm`
DECISIONS **D-P8-002** makes the model path `claude -p` directly, and every
call records `request.proxied: false` with a `proxy_gap` string naming the
reason. An (a) sentence would be false about both the history and the present.

**Not (c), and this is the correction the item invited.** "(c) the design
exists but the current link is broken" overstates it. The link is not broken;
it is unfunded. `proxy/model_proxy.py:176-181` records the `bypass_attempt`
incident and **does not return** — control falls through to `_forward`, which
copies four whitelisted headers and injects `x-api-key` *only if*
`cfg.api_key` is set. All 65 requests were therefore forwarded to the real
upstream and the real upstream answered them; the 401 is an authentication
failure at the provider, not a refusal by the proxy. A11 measured the
consequence and it is worth stating plainly: **had this repository held an
`ANTHROPIC_API_KEY`, those 65 requests would have returned 200 with byte-identical
incident records.** The missing element is a provider credential the repo does
not have, not a defect in the chain.

That correction cuts the other way too, and the paper should not repeat the
older gloss. `theoria-arm/evidence/README.md` calls the 401s "the sealing
property working"; the property that actually held is the
`PASSTHROUGH_REQUEST_HEADERS` whitelist stripping the client's credential, and
`bypass_attempt` is an **observation point, not an enforcement point**. Both
sentences are about the same event and only one of them is about a mechanism.

### The post-campaign fact the verdict has to absorb

The 2026-07-31 seal work (merge `b375a9bd`) changed the environment half and
left the model half alone, on purpose:

* `theoria-arm/harness/proxy_process.py` moved `EnvProxy` **out of the arm's
  interpreter into a spawned child**. The child reads `.env` itself; the parent
  is handed only `http://127.0.0.1:<port>` and never passes or reads the key.
  So the environment proxy is now a process boundary, not a discipline — which
  strengthens the (b) reading of the environment half rather than changing it,
  since the 924 live requests predate the change and were carried by the
  in-process proxy.
* The model half stayed direct **by design**, per D-P8-002, with
  `proxied: false` recorded per call. A reader who knows only the seal
  paragraph could easily infer both halves were sealed together. They were not.

## 3. For the paper — the sentences RES-2 can lift verbatim

> The environment proxy carried **924** of the arm's requests to the live game
> endpoint — of **1009** proxy-forwarded requests across **24** run ledgers, the
> remaining **85** going to loopback fixtures — so the environment half of the
> seal is validated on real traffic. The model proxy is built and its boundary
> behaviour is recorded, but **0 of the 65** model calls ever put through it were
> answered: all **65** returned HTTP 401, because the proxy strips a client's own
> credential by design (**66** `bypass_attempt` incidents record it doing so) and
> this repository holds no provider key to inject in its place. We therefore
> describe the system as **one proxy validated on real traffic and one built but
> unvalidated**; since 2026-07-31 the arm's model calls are made through the
> vendor CLI directly and each is recorded `proxied: false`.

Three sentences, four denominators, no claim that the count does not carry.
If a shorter form is needed, the middle sentence is the one that must survive
intact — it is the only one that states the gap.

## 4. Minimal checklist to reach (a)

What would have to be true for "both proxies validated on real traffic" to be
an honest sentence. Ordered; each line is a separate, checkable state.

1. **A provider credential exists in `.env` as `ANTHROPIC_API_KEY`**, with the
   variable name documented in `.env.example` and the value nowhere in the
   tree. This is the whole blocker for the 65 401s and it is an owner action,
   not an engineering one — no agent may create it.
2. **`ModelDesk` gets a proxied transport.** Today `harness/modelcall.py`
   spawns `claude -p`, whose OAuth bearer the proxy strips by design, so
   pointing `ANTHROPIC_BASE_URL` at the proxy reproduces exactly the archived
   401s. Reaching (a) needs a direct `/v1/messages` client behind the proxy —
   which also closes the recorded gap that the CLI's own system prompt is
   invisible to the ledger, so input-token composition becomes analysable.
   Cross-territory: this is `theoria-arm`'s file.
3. **The sealed-pile guard is exercised on the model path through the proxy.**
   `ModelDesk._screen_the_pile` screens arm-side today; a proxied route must
   show `model_proxy`'s own `check_request` refusing a planted sealed id
   (surface `model_proxy`, 403) at least once, or the proxy's guard is
   asserted rather than demonstrated.
4. **At least one live run's ledger carries `model_call` with a 2xx status,
   `request.proxied: true`, and no `proxy_gap`.** That record is the artefact
   that makes (a) sayable; nothing short of it is.
5. **`dualagent/count.py`'s `model_proxy_succeeded` goes non-zero on the
   repository**, and `test_the_repository_still_supports_the_verdict` is
   updated in the same commit that makes it true — so the verdict cannot drift
   silently in either direction.
6. **`theoria-arm/evidence/README.md:30` and this file's §2 are corrected
   together**, since both would then be describing history rather than the
   present.

Steps 2–4 are `theoria-arm` work and step 3 touches `proxy/`; neither belongs
to verify-lab. This cell adjudicates and hands over; the inbox note beside it
is the handover.

## 5. Red lines observed

No credential value is read, printed or written by anything in this cell.
`dualagent/count.py` reports header **names** only (`authorization`), and
`test_no_header_value_can_reach_the_output` hands the census a
credential-shaped sentinel in every plausible field and asserts nothing it
returns contains it. Zero API calls, zero spend, zero sealed-pile contact — no
sealed identifier appears in any file this cell wrote, and the census reads
ledgers only, never `.env`.
