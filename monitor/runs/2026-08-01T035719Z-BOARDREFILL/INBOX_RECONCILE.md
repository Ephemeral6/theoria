# Inbox reconciliation — asks filed to territories that never saw them

Method: for each ask in `monitor/inbox/` filed 2026-07-31 or later, take the
file it names as the thing to change and ask git whether that path has a commit
**since the ask's own timestamp**. A territory that received an ask and acted on
it leaves a commit; one that never saw it leaves nothing. Commands run at
`base_commit` `e8345aff` on `master`'s tree:

```
git log --since=<ask utc> --oneline -- <named path>
```

This is a **detector with a known blind spot**, stated so it is not read as
proof: work on an unmerged branch is invisible to it, and an ask answered by a
*decision* rather than a *commit* would also read as untouched. It cannot
manufacture a false "unclaimed" from an ask that did land on master, which is
the direction that matters for refilling a board.

## Unclaimed — 8 asks, with where each should land

| ask (`monitor/inbox/`) | filed | addressee | path checked | commits since | lands as |
|---|---|---|---|---|---|
| `2026-08-01T0000Z-P12-proxy-to-theoria-arm-the-cli-can-go-through-the-model-proxy.md` | 2026-08-01T00:00Z | theoria-arm | `theoria-arm/harness/modelcall.py` | **0** | board **A28** |
| `20260801T0000Z-exam-endpoint2-prereg-and-two-launch-blockers.md` | 2026-08-01T00:00Z | freeze | `freeze/launch_blockers.json`, `freeze/STATS_RULES.md` | **0** | board **S45** |
| `2026-08-01T0300Z-freeze-to-battery-e2-withdrawn-and-turn_costs-mixes-two-axes.md` | 2026-08-01T03:00Z | battery | `battery/model.py` | **0** | board **S46** |
| `20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md` | 2026-08-01T04:00Z | proxy | `proxy/forward.py` | **0** | board **S47** |
| `20260801T0600Z-PROP-schema-column-withdrawal.md` | 2026-08-01T06:00Z | theory / freeze / battery / papers | `Theoria.md`, `freeze/CLAIMS_TEXT.md`, `papers/`, `battery/` | **0** | board **S48** (freeze half only) — see below |
| `20260801T0700Z-freeze-to-exam-e1-keys-on-the-statement-now-four-of-your-tests-must-flip.md` | 2026-08-01T07:00Z | exam | `exam/` (whole territory) | **0** | board **V28** |
| `20260731T1800Z-S32-to-RES-2-one-proxy-validated-not-two.md` | 2026-07-31T18:00Z | papers (RES-2) | `papers/` (whole territory) | **0** | board **V29** |
| `20260731T1830Z-P12-to-theoria-arm-freeze-gate-reads-only-the-rewritable-half.md` | 2026-07-31T18:30Z | theoria-arm | `theoria-arm/harness/freeze_gate.py` | **0** | board **A27** |

## Claimed — 1 ask, closed, no board item

| ask | filed | addressee | evidence it landed |
|---|---|---|---|
| `20260731T1731Z-battery-to-theoria-arm-curves-shortfall.md` | 2026-07-31T17:31Z | theoria-arm | `theoria-arm/armtools/curves.py` @ `82e8e25e` *"the turn that died in flight took the leg's most expensive call with it"* — the last-turn row that dropped the leg's most expensive call, which is exactly what battery reported (r2 −$1.630485, r3 −$1.678809) |

That one is the negative control for the method above: the same query that
returns nothing for eight asks returns a commit, with a subject naming the same
defect, for the ninth. A detector that had never been seen to say "claimed" is a
detector that has not been shown to distinguish anything.

## The one ask that cannot land on a single board item

`20260801T0600Z-PROP-schema-column-withdrawal.md` names **four** addressees, and
`territory:` on a board item is the single directory the item may write. Split:

* `freeze/CLAIMS_TEXT.md` — the premise-correction paragraph, C1's scope, C2 →
  board item **S48**, territory `freeze`.
* `Theoria.md:271` — moving the Schema row out of the main table is a change to
  the baseline document. **Not a board item**: `Theoria.md` is the baseline every
  territory is measured against, and no worker should edit it off a proposal.
  This needs an owner ruling. Routed here, not queued.
* `battery/` — renaming the arm to `schema_upstream`. Belongs to battery; it is
  cosmetic-looking but it is an arm name that appears in frozen artefacts, so it
  should follow the `Theoria.md` ruling rather than precede it.
* `papers/` — phase1-workshop sync, downstream of both of the above.

## Two more that are not inbox asks but have no queue entry either

Recorded so the next session does not have to rediscover them; **not** turned
into board items, because neither is a request anyone filed:

1. `fleet-study/ITERATION_PROTOCOL.md` §4.4 says `Theoria.md:340-349`'s taxonomy
   has no row whose symptom column cleanly receives a mass of
   `probe_refutation`, and that the fix "goes to `monitor/inbox/`, not into the
   baseline" — **and it never was filed**. Same class as the row above: a
   baseline change needing an owner, not a worker.
2. `fleet-study/ITERATION_PROTOCOL.md` §4.7: §2.7 was written for Design A
   (crossover within a round) and `theoria-arm/armtools/round.py` landed Design B
   (one configuration per round, account pinned per game). The author states the
   swap instruction "must not be applied" if the fleet has committed to Design B.
   The fleet has: R1 and R1b both ran Design B. So §2.7's swap instruction is
   already void, and the document does not say so — a documentation correction in
   `fleet-study/`'s own territory, for whoever next opens it.
