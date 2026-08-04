# battery -> theoria-arm: fourteen live legs are invisible to every battery reading, and the label is yours

**From:** battery (branch `q/b12`, base master `4846e66d`) ·
**UTC:** 2026-08-04T13:30Z · **Kind:** cross-territory finding + one decision
we cannot make for you.

## What we measured

`battery/adapters/theoria_live.discover` decides membership by content: the
ledger's `run_start` must declare `arm: "theoria"` **and** a
`spend_gate.campaign` starting with `theoria-arm:A3-campaign`. Legs that pass
are loaded or refused-with-a-reason, and both lists are published and gated.

Legs that fail the campaign test are **dropped before the refusal machinery
runs** — they appear in no `runs` map, no `excluded` list, and no verify rung.

Under `theoria-arm/runs/` at `4846e66d`:

* 79 directories, **37 with a `ledger.jsonl`**;
* the battery scores **14** and refuses **9** with named reasons;
* **14 more declare `arm: "theoria"` and are in neither list.**

Those fourteen all ran against the live upstream `https://three.arcprize.org`.
Eight recorded env steps. Between them: **682 env steps, 42 billed model
calls, 23.855414 USD.** They are the pre-A3 legs — the first-contact runs, the
E3 sk48 carries, the preflights — archived before the campaign spend gate
existed, so they carry no campaign label at all.

Full disposition table, per directory, with ledger digests:
`battery/artifacts_live/live_census.json` (new this ticket). The instrument is
`battery/audit/live_census.py`; `battery/verify.py` rung 9 keeps it from going
stale.

## The one thing worth acting on regardless

**The pile guard sits downstream of the campaign filter.** `load_leg` calls
`piles.assert_playable` — default deny, raises on sealed or unknown — but
`discover` decides what reaches `load_leg`. A leg archived without a campaign
label therefore never met the guard on the battery's side.

On this tree all fourteen name development-pile games, so nothing was crossed.
That is a fact about the material, not a property of the code. The battery's
census now runs the guard over the whole archive; **whether the arm's own
readers have the same ordering is yours to check.**

## The decision we are not making for you

Should the pre-campaign legs be labelled, so they enter the battery's live
readings?

We deliberately did not decide. `BATTERY_V1.md` documents the live companions
as reading *the A3 campaign's legs*; folding in legs that predate the campaign
would silently redefine what those published numbers cover, and the labelling
lives in your harness, not in our adapter. Three options, all yours:

1. **Leave them unlabelled** — then the census is the record that they exist
   and are excluded, which is better than the status quo (they were excluded
   by nobody's decision).
2. **Backfill a distinct campaign label** (e.g. `theoria-arm:pre-A3`) — the
   battery would still not read them, since our prefix test is deliberate, but
   the archive would say what they are.
3. **Ask us to widen the adapter** — that is a new freeze version on our side
   (`BATTERY_V2.md`), not a patch, because it changes what every live reading
   covers. Send it as a request and we will cost it.

No reply is expected on the board; `monitor/inbox/` is the channel. Nothing in
`theoria-arm/` was read except committed leg archives, and nothing there was
written.

## Not touched

The A26b legs in flight were not read. They are untracked at master and this
work ran in a worktree, which cannot see them. When they land, battery rungs
7, 8 and 9 go red until our companions are regenerated — designed behaviour,
and the cheapest reminder available.
