# INCIDENTS — theoria-arm

Things that went wrong, or that make a number in this track's reports mean less
than it appears to. Numbered `INC-TA-nnn`. An incident is recorded when it is
noticed, not when it is resolved.

---

## INC-TA-001 · Two arms played `g50t` concurrently, on one quota — severity: high

**What.** The Theoria arm's first live contact on `g50t-5849a774` ran at the
same time as another Claude Code session's `baseline-arms` `bare_cc` campaign
**on the same game**. Both were in flight at `2026-07-28T01:28Z`:

* this arm: `runs/<slug>/ledger.jsonl`, ACTION4, a run of consecutive HTTP 400s;
* the other session: `baseline-arms/out/shards/ledger.g50t.jsonl` last written
  `01:28:59Z`, and `baseline-arms/out/campaign/g50t.log` reading
  `episode 10 died (api_unusable); restarting from level 1` /
  `episode 11, 444 actions left, $13.64 of $48.10 spent`.

**How it was found.** Not by design. This arm's HTTP amplification was running
at 15–19 commands per successful action, far above the 5.07 `baseline-arms`
measured on its own confirmation run, so the repo was checked for other writers.
`find -newermt '-10 minutes'` found the other campaign's shard ledger.

**Why it matters, precisely.** This is `baseline-arms`' own INC-BA-003
recurring, with this track as the second party. Three consequences:

1. **Every wall-clock and amplification number this track reports is
   confounded.** `attempts`, `commands_sent`, `http_amplification` and
   `elapsed_s` in this run's `MANIFEST.json` were measured against a backend
   that another session was also driving. They are an upper bound on this arm's
   own cost, not a measurement of it, and they may not be compared with
   `baseline-arms`' 5.07 or `arc-recon`'s 2.5–10× without this caveat.
2. **Neither side can see the joint total.** Two gates, two ceilings, one
   quota, one bill. This arm's ceilings (120 actions, $20) bound *this arm*
   and nothing else.
3. `episode 10 died (api_unusable)` on the other side is consistent with
   contention but is **not** attributed to it here — the 400 wave is a
   documented property of ARC's multi-instance backend (INC-001b/INC-002a) and
   was already observed in this repo during quiet periods. No causal claim is
   made in either direction.

**What was done.** Nothing to the other session. Its process was not killed,
its files were not touched, and `baseline-arms/` was read only. That is the
discipline that track kept when it found this arm's predecessors, and it is
kept here for the same reason: a run destroyed to make another run's numbers
prettier is worse than a run with a caveat.

This arm continued. Stopping would have delivered nothing, and the action
budget it was given is its own — the contention costs time and inflates the
retry count, but it does not spend another arm's actions.

**What would fix it.** The same thing `baseline-arms` asked for and did not
get: a cross-session gate — a lock file or a shared counter under `arc-recon/`
that any arm must take before opening a scorecard, so that two sessions
serialise instead of interleaving, and so that one of them can see the joint
total. That belongs in shared ground (`arc-recon/`), not in either arm, and
is not built here because building it would mean writing into a directory this
track is read-only in.

---

## INC-TA-002 · The score obligation is undischargeable against the live API — severity: medium

`LEDGER_FORMAT.md` §3 states as a **hard obligation**, not a diagnostic, that
the score derived from `env_step` records must equal the score the scorecard
reports, and that inequality is an incident.

It cannot be computed. Live ARC command responses carry no `score` field at
all. The complete key set, confirmed on this run's own RESET and consistent
with `arc-recon`'s 84 successful command responses, is:

```
action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels
```

Score exists only inside a successful `POST /api/scorecard/close` response.
`proxy/env_proxy.py` reads `response_body.get("score")` and therefore writes
`score: null` into every `env_step`, and `proxy/reconcile.py` compares that to
the scorecard's number.

**Recorded as an incident rather than waived.** `tools/archive.py` reports
`score_reconciliation: "unavailable"` with this reason, and reconciles the two
quantities the API *does* return — `levels_completed` and the successful action
count — in its place. The obligation as written in `LEDGER_FORMAT.md` needs
either a new derivation (the scorecard's per-run `level_actions` may support
one) or an amendment. Both are decisions for the track that owns `proxy/`;
this is a report, not a request.
