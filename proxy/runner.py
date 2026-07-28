"""Orchestrate one game: open a scorecard, RESET, run the outer loop, close.

One game is one run and one scorecard. Both proxies share a single `RunLedger`,
so `step_idx` and `call_idx` come from one counter and a model call can name
the environment step it was deciding.

    python -m proxy.runner --mock                       # the whole loop, offline
    python -m proxy.runner --game ar25-0c556536         # against the real API
"""

import argparse
import json
import os
import sys
import uuid
from typing import Any, Dict, Optional

from .env_proxy import EnvProxy, EnvProxyConfig
from .guard import SealedPileGuard
from .ledger import Ledger, RunLedger, canonical, sha256
from .model_proxy import ModelProxy, ModelProxyConfig
from .paths import LEDGER_PATH, RUNS_DIR, UPSTREAM_ARC, UPSTREAM_MODEL
from .spend_gate import default_campaign, default_gate
from .variants import Variant
from . import scoring


def new_run_id() -> str:
    return "r-" + uuid.uuid4().hex[:16]


def _run_game(game_id: str, *,
             arm: str = "mock_arm",
             budget: int = 40,
             run_id: Optional[str] = None,
             env_upstream: str = UPSTREAM_ARC,
             model_upstream: str = UPSTREAM_MODEL,
             env_key: Optional[str] = None,
             model_key: Optional[str] = None,
             require_keys: bool = True,
             variant: Optional[Variant] = None,
             guard: Optional[SealedPileGuard] = None,
             ledger_path: str = LEDGER_PATH,
             model: str = "mock-model-1",
             stream: bool = False,
             arm_factory=None,
             scorer_id: str = scoring.DEFAULT_SCORER,
             campaign: Optional[str] = None,
             spend_gate=None,
             spend_reservation=None,
             usd_cap: Optional[float] = None,
             action_cap: Optional[int] = None,
             runs_dir: str = RUNS_DIR) -> Dict[str, Any]:
    run_id = run_id or new_run_id()
    ledger = Ledger(ledger_path)
    run = RunLedger(ledger, run_id, arm, game_id=game_id)

    # Verified before the game starts, not after it. A run that turns out to
    # have been scored by an edited scorer has already cost its actions.
    scorer_fp = scoring.verify_frozen(scorer_id)

    # One reservation for the run, shared by both proxies, taken here for the
    # same reason the scorer is verified here: it is the one place that owns
    # both proxies' lifetimes, so it is the only place that can hand the claim
    # back when the run ends. Two proxies each taking their own would hold the
    # pool twice for one run's worth of spending.
    #
    # `campaign` names the run rather than the process. It is the field
    # `baseline-arms/ledger.jsonl` did not have, which is why one file ended up
    # holding two campaigns with no line able to say which was which.
    gate = spend_gate if spend_gate is not None else default_gate()
    campaign = campaign or default_campaign(arm, run_id)
    reservation = spend_reservation
    reservation_owned = reservation is None
    if reservation_owned:
        caps = gate.policy.default_run_caps
        reservation = gate.reserve(
            campaign,
            usd_cap if usd_cap is not None else caps["usd"],
            action_cap if action_cap is not None else caps["actions"],
            holder={"run_id": run_id, "arm": arm, "game_id": game_id,
                    "undeclared": usd_cap is None and action_cap is None})

    env_cfg = EnvProxyConfig(run_id=run_id, arm=arm, upstream=env_upstream,
                             api_key=env_key, require_key=require_keys,
                             ledger=ledger, run=run, guard=guard, variant=variant,
                             campaign=campaign, spend_gate=gate,
                             spend_reservation=reservation)
    model_cfg = ModelProxyConfig(run_id=run_id, arm=arm, upstream=model_upstream,
                                 api_key=model_key, require_key=require_keys,
                                 ledger=ledger, run=run, game_id=game_id,
                                 guard=env_cfg.guard,
                                 campaign=campaign, spend_gate=gate,
                                 spend_reservation=reservation)

    with EnvProxy(env_cfg) as env_proxy, ModelProxy(model_cfg) as model_proxy:
        run.run_start(
            game_id=game_id, budget=budget, model=model,
            env_base=env_proxy.base_url, model_base=model_proxy.base_url,
            env_upstream=env_upstream, model_upstream=model_upstream,
            guard=env_cfg.guard.fingerprint(),
            variant=variant.fingerprint() if variant else None,
            pricing=model_cfg.pricing.reference() if model_cfg.pricing else None,
            proxy_version=_proxy_version(),
            scorer=scorer_fp,
            # Which pool this run drew on, and under whose claim. A run that
            # drew on a widened ceiling is identifiable after the fact.
            spend_gate=dict(gate.fingerprint(), campaign=campaign,
                            reservation_id=reservation.reservation_id),
        )

        if arm_factory is None:
            from .mock.arm_mock import MockArm
            def arm_factory(env_base, model_base):        # noqa: E306
                return MockArm(env_base=env_base, model_base=model_base,
                               model=model, arm=arm, stream=stream,
                               check_sealed=False)

        instance = arm_factory(env_proxy.base_url, model_proxy.base_url)
        summary = instance.play(game_id, budget=budget)

        run.run_end(outcome=summary.get("outcome"),
                    steps=summary.get("steps"),
                    model_calls=summary.get("model_calls"),
                    score=summary.get("score"),
                    levels_completed=summary.get("levels_completed"),
                    scorecard=summary.get("scorecard"),
                    env_proxy=env_proxy.summary(),
                    model_proxy=model_proxy.summary())

        record = {"run_id": run_id, "arm": arm, "game_id": game_id,
                  "ledger": os.path.abspath(ledger_path),
                  "summary": summary,
                  "env_proxy": env_proxy.summary(),
                  "model_proxy": model_proxy.summary()}

    # The claim goes back the moment the run stops needing it, so a finished
    # run does not keep the next campaign out of the pool. What it spent stays
    # counted forever; only the unspent hold is returned.
    #
    # NOTE: this is the happy path only. `_release_on_exit` below wraps the
    # whole run so a crash in `play()` cannot strand the claim -- 43 crashed
    # runs would otherwise take the shared pool offline for an hour with
    # nothing spent, and the recovery is to wait.
    if reservation_owned:
        gate.release(reservation, reason="run %s finished" % run_id)
        reservation_owned = False
    record["spend"] = {"campaign": campaign,
                       "reservation_id": reservation.reservation_id,
                       "pool": gate.policy.pool,
                       "totals": gate.totals().as_dict()}

    # Scored the moment the game ends, not in a sweep afterwards: Phase 3
    # audits the order results arrive in, and a batch decided all at once is a
    # batch someone could have decided after seeing it.
    score_report = scoring.score_run(run_id, ledger_path=ledger_path,
                                     scorer_id=scorer_id)
    record["scorer"] = score_report["scorer"]
    record["score"] = score_report["score"]
    record["reconciliation"] = {"verdict": score_report["verdict"],
                                "failed_checks": score_report["failed_checks"],
                                "undetermined_checks":
                                    score_report["undetermined_checks"]}

    os.makedirs(runs_dir, exist_ok=True)
    with open(os.path.join(runs_dir, run_id + ".json"), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(record, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return record



def run_game(*args, **kwargs) -> Dict[str, Any]:
    """`_run_game`, with the pool's headroom guaranteed to come back.

    A `finally` rather than a tidy release at the end, because the release at
    the end only runs when the run finishes. An adversarial pass counted 43
    crashed runs stranding the whole shared pool for the full TTL with nothing
    actually spent -- fail-closed, but the recovery is to wait an hour, which
    is not a recovery anyone will accept twice.

    The reservation is re-derived here rather than threaded out, because
    `_run_game` releases its own on the happy path and flips `reservation_owned`
    when it does; this only has to catch the paths where it never got there.
    """
    from .spend_gate import default_gate
    gate = kwargs.get("spend_gate") or default_gate()
    declared = kwargs.get("spend_reservation")
    before = {r["reservation_id"] for r in gate.totals().live}
    try:
        return _run_game(*args, **kwargs)
    finally:
        if declared is None:
            # Anything this call opened and did not close. Comparing against a
            # snapshot rather than remembering a handle keeps this correct even
            # when `_run_game` dies before it has one.
            for entry in gate.totals().live:
                if entry["reservation_id"] in before:
                    continue
                if entry["holder"].get("run_id") != kwargs.get("run_id") \
                        and kwargs.get("run_id") is not None:
                    continue
                gate.release(
                    _Handle(entry["reservation_id"], entry["campaign"]),
                    reason="run ended without releasing its claim")


class _Handle:
    """The two fields `release` needs, rebuilt from the ledger."""

    def __init__(self, reservation_id: str, campaign: str):
        self.reservation_id = reservation_id
        self.campaign = campaign


def _proxy_version() -> Dict[str, Any]:
    """A hash over this package's sources. A run records which build produced
    it, so a later behaviour change is visible instead of silent."""
    here = os.path.dirname(os.path.abspath(__file__))
    digests = {}
    for name in sorted(os.listdir(here)):
        if name.endswith(".py"):
            with open(os.path.join(here, name), "rb") as fh:
                digests[name] = sha256(fh.read())
    return {"files": len(digests), "sha256": sha256(digests)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", default=None)
    ap.add_argument("--arm", default="mock_arm")
    ap.add_argument("--budget", type=int, default=40)
    ap.add_argument("--variant", default=None)
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--stream", action="store_true",
                    help="ask the provider to stream, exercising SSE usage capture")
    ap.add_argument("--mock", action="store_true",
                    help="run against the offline mocks; no key, no network, no cost")
    args = ap.parse_args(argv)

    variant = Variant.find(args.variant) if args.variant else None

    if args.mock:
        from .mock.arc_mock import DEFAULT_GAME, DEFAULT_KEY as ARC_KEY, MockArc
        from .mock.model_mock import DEFAULT_KEY as MODEL_KEY, MockProvider
        game_id = args.game or DEFAULT_GAME
        with MockArc(api_key=ARC_KEY, games=[game_id]) as arc, \
                MockProvider(api_key=MODEL_KEY) as provider:
            record = run_game(game_id, arm=args.arm, budget=args.budget,
                              env_upstream=arc.base_url,
                              model_upstream=provider.base_url,
                              env_key=ARC_KEY, model_key=MODEL_KEY,
                              require_keys=False, variant=variant,
                              ledger_path=args.ledger, stream=args.stream)
    else:
        if not args.game:
            print("--game is required unless --mock is given")
            return 2
        record = run_game(args.game, arm=args.arm, budget=args.budget,
                          variant=variant, ledger_path=args.ledger,
                          stream=args.stream)

    print(canonical({k: v for k, v in record.items() if k != "summary"}))
    print(json.dumps(record["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
