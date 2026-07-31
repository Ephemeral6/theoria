r"""S31 requirement 2, prepared as one command and left unfired.

The ticket asks for one minimal real-arm call, budget computed first, taken
through `spend_gate.reserve()`, and then for `proxy/var/ledger.jsonl` to be
checked for a record whose `arm` is not `mock_arm`. The session owner gates all
live spend, so this script **does not spend by default**: run with no arguments
and it computes every number the live run would use, prints the exact
reservation it would take and the record shape that would prove success, and
opens no socket.

    python live_probe.py                       # dry run. no network, $0.00
    python live_probe.py --go --authorised-by "<who said yes, and where>"

The offline half of requirement 2 is already answered and is not re-run here:
`../20260730T043824Z-S31-a10-said-done-prove-it/real_arm_probe.py` drove
`run_game(arm='bare_cc')` against the loopback mocks and wrote 61 records
carrying `arm: bare_cc`, so **the write end is not broken**. What is still
unwitnessed is axis 2 -- that a run reached an upstream off this machine -- and
axis 2 is the only thing this script exists to add.

## Two rungs, and rung 1 is the default because it is the cheaper witness

  rung 1  ARC live, model on the loopback mock.  **$0.0000 of model spend.**
          Produces `run_start.env_upstream = https://three.arcprize.org`, which
          is a non-localhost upstream, which is axis 2. This is the minimum that
          answers the question, and it is the default.

  rung 2  both upstreams live.  Adds a real `/v1/messages` call and its bill.
          Only worth firing if the *model* half's live path is what is in doubt.

## What this refuses, and why the refusals are the point

* `--go` without `--authorised-by` -- a live call needs a name attached to it.
* any game outside the development pile of four -- read from
  `arc-recon/data/piles.json` as a positive whitelist. The sealed pile's ids
  are never loaded, never printed and never compared against; the check is
  membership in the dev list, so an id that is not on it is refused without
  anyone having to look at what it is.
* rung 2 with no `ANTHROPIC_API_KEY` in the environment -- refused *before* the
  reservation is taken, so a run that cannot pay does not first take the pool's
  headroom and then fail.

No credential value is read, logged or written by this file. The proxies read
their own keys inside themselves (`env_proxy.py:123`, `model_proxy.py:74`) and
`redact.VAULT` masks them in every record; this script only reports whether a
variable is *present*.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

#: The arms the ledger recognises as experimental, per `proxy/ledger.py:37`.
#: `mock_arm`, `replay` and `probe` are deliberately not here.
REAL_ARMS = frozenset({"bare_cc", "schema_repro", "theoria"})

#: Campaign name for the reservation. It names the run, not the process --
#: `baseline-arms/ledger.jsonl` is the file that had two campaigns in it and no
#: line able to say which was which.
CAMPAIGN = "s31-live-arm-probe"

#: What the run is allowed to spend, declared rather than defaulted. See
#: LIVE_PROBE_PLAN.md for the arithmetic; `default_run_caps` would have given
#: this run $5.00 and 600 actions, which is 500x the ceiling it can reach.
USD_CAP = 0.05
ACTION_CAP = 10

#: One RESET plus one ACTION. The smallest game that still produces an
#: `env_step` sequence a reconciler can key on.
BUDGET = 1

#: Cheapest model in `pricing_v1.json` that is a real model. Only reached on
#: rung 2.
MODEL = "claude-haiku-4-5"


def dev_pile():
    """The four development-pile ids, as a positive whitelist.

    Only the `development` list is read. The sealed list is not loaded, so a
    typo cannot accidentally match one.
    """
    path = os.path.join(REPO, "arc-recon", "data", "piles.json")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    pile = doc.get("dev_pile")
    if not isinstance(pile, list) or not pile:
        raise SystemExit("piles.json has no `dev_pile` list; refusing rather "
                         "than falling back to something wider")
    return [g if isinstance(g, str) else g.get("game_id") for g in pile]


def ceiling(model, max_tokens=256, frame_cells=64 * 64):
    """The pre-flight bound `model_proxy.py:218` will compute for one call.

    Recomputed here from the same table and the same function, not copied, so
    the plan's number cannot drift away from the gate's.
    """
    from proxy.cost import PriceTable
    frame = [[[0] * 64 for _ in range(frame_cells // 64)]]
    observation = json.dumps({"frame": frame, "state": "NOT_FINISHED",
                              "score": 0,
                              "available_actions": [1, 2, 3, 4, 5, 6]},
                             sort_keys=True)
    body = {"model": model, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": observation}]}
    return PriceTable.load().ceiling_for(body)


def live(url):
    return bool(url) and "127.0.0.1" not in url and "localhost" not in url


def census(records):
    """The two axes the failed audit collapsed into one word.

    `event: incident` records are excluded from axis 1: `reconcile.py:521`
    stamps an incident with the arm of the run it is complaining about, so
    counting by `arm` otherwise counts the auditor's own footprints.
    """
    starts = {r["run_id"]: r for r in records if r.get("event") == "run_start"}
    axis1 = [r for r in records
             if r.get("event") != "incident" and r.get("arm") in REAL_ARMS]
    axis2 = [r for r in starts.values()
             if live(r.get("env_upstream")) or live(r.get("model_upstream"))]
    return axis1, axis2, starts


def plan(args):
    """Every number the live run would use, with nothing sent."""
    from proxy.paths import LEDGER_PATH, UPSTREAM_ARC, UPSTREAM_MODEL
    from proxy.spend_gate import SpendGate

    per_call = ceiling(MODEL)
    calls = 0 if args.rung == 1 else BUDGET
    worst = round((per_call["usd"] or 0.0) * calls, 6)

    out = []
    w = out.append
    w("S31 live-arm probe -- DRY RUN. Nothing was sent; $0.00.")
    w("=" * 70)
    w("")
    w("rung %d: env upstream %s" % (args.rung, "LIVE" if args.rung >= 1 else "mock"))
    w("         model upstream %s" % ("LIVE" if args.rung >= 2 else "loopback mock"))
    w("")
    w("the call")
    w("  game        %s   (development pile; whitelist from arc-recon/data/piles.json)"
      % args.game)
    w("  arm         %s" % args.arm)
    w("  budget      %d action(s) -> RESET + %d ACTION, %d model call(s)"
      % (BUDGET, BUDGET, calls))
    w("  env_upstream    %s" % (UPSTREAM_ARC if args.rung >= 1 else "loopback"))
    w("  model_upstream  %s" % (UPSTREAM_MODEL if args.rung >= 2 else "loopback"))
    # Relative to the checkout root, so an archived dry run does not pin one
    # machine's home directory into a tracked artefact.
    w("  ledger      <checkout>/%s"
      % os.path.relpath(LEDGER_PATH, REPO).replace(os.path.sep, "/"))
    if os.path.sep + ".worktrees" + os.path.sep in LEDGER_PATH:
        w("")
        w("  !! THIS IS A WORKTREE. `paths.py` resolves LEDGER_PATH and .env from")
        w("     __file__, so both are worktree-local -- but `SpendGate` walks to the")
        w("     MAIN checkout on purpose, so the pool is genuinely shared. Firing")
        w("     from here would charge the shared pool and write the evidence into a")
        w("     gitignored file nobody audits. Run the live rung from the main")
        w("     checkout. (It would in fact refuse first, on the absent key -- the")
        w("     fail-closed order is right, but do not rely on it.)")
    w("")
    w("the budget, computed before anything is reserved")
    w("  per-call ceiling  $%.6f   (%s, max_tokens=%d, %d input tokens estimated"
      % (per_call["usd"], MODEL, per_call["basis"]["max_tokens"],
         per_call["basis"]["estimated_input_tokens"]))
    w("                     at %s chars/token, cache multiplier %s -- "
      % (per_call["basis"]["chars_per_token_assumed"],
         per_call["basis"]["cache_multiplier_applied"]))
    w("                     cost.py:163, the same function the gate will use)")
    w("  model calls       %d" % calls)
    w("  worst case        $%.6f" % worst)
    w("  ARC requests      4  (scorecard/open, RESET, ACTION, scorecard/close)")
    w("")
    w("the reservation it will take")
    w("  spend_gate.reserve(%r, usd_cap=%.2f, action_cap=%d," % (CAMPAIGN, USD_CAP, ACTION_CAP))
    w("                     holder={'run_id': ..., 'arm': %r, 'game_id': %r,"
      % (args.arm, args.game))
    w("                            'undeclared': False})")
    w("  headroom over worst case: %s"
      % ("n/a -- rung 1 spends no model dollars"
         if not worst else "%.1fx" % (USD_CAP / worst)))
    w("  NOT the default. `default_run_caps` is $5.00 / 600 actions "
      "(spend_policy.json),")
    w("  which is what `python -m proxy.runner` would take, because its CLI has "
      "no")
    w("  --usd-cap flag. Declaring is why this is a script and not that command.")
    w("")

    try:
        gate = SpendGate()
        totals = gate.totals()
        w("the pool, right now")
        w("  pool      %s" % gate.policy.pool)
        w("  spent     $%.4f / $%.2f   %d / %d actions"
          % (totals.usd, totals.ceiling_usd, totals.actions,
             totals.ceiling_actions))
        w("  free      $%.4f            %d actions"
          % (totals.free_usd, totals.free_actions))
        w("  this run would take $%.2f of that hold, and give back the unspent "
          "remainder" % USD_CAP)
    except Exception as exc:                                # noqa: BLE001
        w("the pool could not be read from here: %s" % exc)
        w("  (expected in a worktree -- spend_policy.json's `ledger` is "
          "relative to the MAIN checkout)")
    w("")
    w("credentials, by presence only -- no value is read or printed here")
    for name, needed in (("ARC_API_KEY", args.rung >= 1),
                         ("ANTHROPIC_API_KEY", args.rung >= 2)):
        w("  %-18s %-8s %s" % (name,
                               "present" if _present(name) else "ABSENT",
                               "required for this rung" if needed
                               else "not needed at this rung"))
    w("")
    w("what would prove it worked: a run_start record of this shape")
    w(json.dumps({
        "v": "1.0", "event": "run_start", "arm": args.arm,
        "run_id": "r-<minted>", "game_id": args.game,
        "env_upstream": UPSTREAM_ARC if args.rung >= 1 else "<loopback>",
        "model_upstream": UPSTREAM_MODEL if args.rung >= 2 else "<loopback>",
        "spend_gate": {"pool": "theoria-shared-2026-07",
                       "campaign": CAMPAIGN,
                       "reservation_id": "res-<minted>"},
    }, indent=2, sort_keys=True))
    w("")
    w("  axis 1 is `arm` in %s on a non-incident record."
      % sorted(REAL_ARMS))
    w("  axis 2 is `env_upstream` or `model_upstream` off this machine.")
    w("  BOTH must be yes. Axis 1 alone is satisfiable for $0.00 by "
      "`--mock --arm bare_cc`,")
    w("  which is the forgery this item exists to name.")
    return "\n".join(out) + "\n"


def _present(name):
    """Whether a variable has a value. The value itself is never touched."""
    if os.environ.get(name):
        return True
    path = os.path.join(REPO, ".env")
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("%s=" % name) and line.split("=", 1)[1].strip():
                return True
    return False


def go(args):
    """The live run. Reached only with --go and a name attached."""
    from proxy.paths import LEDGER_PATH, UPSTREAM_ARC, UPSTREAM_MODEL
    from proxy.reconcile import reconcile_run
    from proxy.runner import new_run_id, run_game
    from proxy.spend_gate import default_gate

    if args.rung >= 2 and not _present("ANTHROPIC_API_KEY"):
        print("REFUSED: rung 2 needs ANTHROPIC_API_KEY and it is not set. "
              "Refusing before the reservation, so a run that cannot pay does "
              "not first take the pool's headroom.")
        return 2
    if args.rung >= 1 and not _present("ARC_API_KEY"):
        print("REFUSED: ARC_API_KEY is not set; see CLAUDE.md.")
        return 2

    before = _read(LEDGER_PATH)
    gate = default_gate()
    run_id = new_run_id()
    reservation = gate.reserve(
        CAMPAIGN, USD_CAP, ACTION_CAP,
        holder={"run_id": run_id, "arm": args.arm, "game_id": args.game,
                "undeclared": False, "authorised_by": args.authorised_by})
    print("reserved %s  $%.2f / %d actions  on pool %s"
          % (reservation.reservation_id, USD_CAP, ACTION_CAP, gate.policy.pool))

    kwargs = dict(arm=args.arm, budget=BUDGET, run_id=run_id, model=MODEL,
                  ledger_path=LEDGER_PATH, campaign=CAMPAIGN,
                  spend_gate=gate, spend_reservation=reservation,
                  env_upstream=UPSTREAM_ARC)
    try:
        if args.rung >= 2:
            record = run_game(args.game, model_upstream=UPSTREAM_MODEL, **kwargs)
        else:
            from proxy.mock.model_mock import DEFAULT_KEY as MODEL_KEY
            from proxy.mock.model_mock import MockProvider
            with MockProvider(api_key=MODEL_KEY) as provider:
                record = run_game(args.game, model_upstream=provider.base_url,
                                  model_key=MODEL_KEY, require_keys=False,
                                  **kwargs)
    finally:
        try:
            gate.release(reservation, reason="s31 live probe finished")
        except Exception:                                   # noqa: BLE001
            pass                       # `_run_game` already released it

    after = _read(LEDGER_PATH)
    fresh = after[len(before):]
    axis1, axis2, _ = census(fresh)
    print("")
    print("records appended: %d" % len(fresh))
    print("AXIS 1 real-arm records (non-incident): %d" % len(axis1))
    print("AXIS 2 runs with a non-localhost upstream: %d" % len(axis2))
    for r in fresh[:3]:
        print("  " + json.dumps({k: r[k] for k in
                                 ("seq", "event", "arm", "run_id",
                                  "env_upstream", "model_upstream") if k in r},
                                sort_keys=True))
    print("")
    print(json.dumps(reconcile_run(record["run_id"], LEDGER_PATH,
                                   write_incident=False),
                     indent=2, sort_keys=True))
    print("")
    print("report the amount in monitor/inbox/ per the ticket.")
    return 0


def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", default="ar25-0c556536")
    ap.add_argument("--arm", default="bare_cc", choices=sorted(REAL_ARMS))
    ap.add_argument("--rung", type=int, default=1, choices=(1, 2))
    ap.add_argument("--go", action="store_true",
                    help="actually run. Requires --authorised-by.")
    ap.add_argument("--authorised-by", default=None,
                    help="who approved this spend, and where they said so")
    args = ap.parse_args(argv)

    allowed = dev_pile()
    if args.game not in allowed:
        # The rejected id is deliberately NOT echoed. If it were a sealed-pile
        # id, echoing it would write one into whatever captured this output --
        # and a refusal that leaks the thing it refused is not a refusal.
        print("REFUSED: the id given is not in the development pile. The "
              "whitelist is positive and holds exactly: %s. The sealed list is "
              "never loaded, so this refusal does not depend on knowing what "
              "was asked for -- and the id is not repeated here for the same "
              "reason." % ", ".join(sorted(allowed)))
        return 2

    if not args.go:
        sys.stdout.write(plan(args))
        return 0
    if not args.authorised_by:
        print("REFUSED: --go needs --authorised-by. A live call carries a name.")
        return 2
    return go(args)


if __name__ == "__main__":
    raise SystemExit(main())
