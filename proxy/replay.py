"""Replay a run from the ledger and compare frame hashes, step by step.

This is Phase 1's second closure property made executable: *any game can be
re-run from the ledger*. The environment side replays for real -- same actions,
same order, hashes compared one at a time. The model side cannot be replayed in
principle, which is why its inputs, outputs and usage are recorded in full
instead.

The replay opens its **own scorecard**, marked as a probe, so re-running a game
does not add actions or score to the original game's card. It also runs under
its own `run_id` with `arm: "replay"`, so its steps are evidence in the same
ledger rather than a second copy of the original run.

    python -m proxy.replay --run-id r-... --mock
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .env_proxy import EnvProxy, EnvProxyConfig
from .guard import SealedPileGuard
from .ledger import Ledger, RunLedger, read_ledger
from .paths import LEDGER_PATH, UPSTREAM_ARC
from .runner import new_run_id
from .variants import Variant


def _post(base: str, path: str, body: Dict[str, Any], timeout: float = 30.0):
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        base.rstrip("/") + path, data=payload, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": raw}


def commands_of(run_id: str, ledger_path: str = LEDGER_PATH) -> List[Dict[str, Any]]:
    """The run's env_step records in step order -- including refused ones, which
    must be replayed too: a refusal is part of what happened."""
    steps = [r for r in read_ledger(ledger_path)
             if r.get("run_id") == run_id and r.get("event") == "env_step"]
    return sorted(steps, key=lambda r: r.get("step_idx", 0))


def start_record(run_id: str, ledger_path: str = LEDGER_PATH) -> Optional[Dict[str, Any]]:
    for record in read_ledger(ledger_path):
        if record.get("run_id") == run_id and record.get("event") == "run_start":
            return record
    return None


def replay_run(run_id: str, *,
               ledger_path: str = LEDGER_PATH,
               env_upstream: str = UPSTREAM_ARC,
               env_key: Optional[str] = None,
               require_key: bool = True,
               variant: Optional[Variant] = None,
               guard: Optional[SealedPileGuard] = None,
               replay_run_id: Optional[str] = None) -> Dict[str, Any]:
    original = commands_of(run_id, ledger_path)
    if not original:
        raise KeyError("no env_step records for run %r in %s" % (run_id, ledger_path))

    started = start_record(run_id, ledger_path)
    if variant is None and started and started.get("variant"):
        variant = Variant.find(started["variant"]["variant_id"])

    game_id = original[0].get("game_id")
    replay_id = replay_run_id or (new_run_id() + "-replay")
    ledger = Ledger(ledger_path)
    run = RunLedger(ledger, replay_id, "replay")

    cfg = EnvProxyConfig(run_id=replay_id, arm="replay", upstream=env_upstream,
                         api_key=env_key, require_key=require_key,
                         ledger=ledger, run=run, guard=guard, variant=variant)

    comparisons: List[Dict[str, Any]] = []
    with EnvProxy(cfg) as proxy:
        run.run_start(game_id=game_id, replay_of=run_id, scorecard_kind="probe",
                      env_upstream=env_upstream,
                      variant=variant.fingerprint() if variant else None,
                      note="prefix replay; a separate probe scorecard keeps the "
                           "original game's action and score counts clean")

        _, card = _post(proxy.base_url, "/api/scorecard/open",
                        {"arm": "replay", "probe": True, "replay_of": run_id})
        card_id = card.get("card_id")
        guid = None

        for record in original:
            action = record.get("action") or {}
            name = action.get("name")
            body: Dict[str, Any] = {"game_id": record.get("game_id"),
                                    "card_id": card_id}
            if name != "RESET":
                body["guid"] = guid
            if action.get("data") is not None:
                body["data"] = action["data"]

            status, response = _post(proxy.base_url, "/api/cmd/" + str(name), body)
            if isinstance(response, dict) and response.get("guid"):
                guid = response["guid"]

            replayed = response.get("frame") if isinstance(response, dict) else None
            if replayed is not None and not isinstance(replayed, list):
                replayed = [replayed]
            from .ledger import frame_hash
            comparisons.append({
                "step_idx": record.get("step_idx"),
                "action": name,
                "expected": record.get("frame_hash"),
                "actual": frame_hash(replayed),
                "status": status,
            })

        _post(proxy.base_url, "/api/scorecard/close", {"card_id": card_id})

        mismatches = [c for c in comparisons if c["expected"] != c["actual"]]
        report = {
            "replay_of": run_id, "replay_run_id": replay_id, "game_id": game_id,
            "steps_compared": len(comparisons),
            "mismatches": mismatches,
            "first_divergence": mismatches[0]["step_idx"] if mismatches else None,
            "verdict": "PASS" if not mismatches else "FAIL",
            "variant": variant.fingerprint() if variant else None,
        }
        if mismatches:
            run.incident("replay_mismatch",
                         "%d of %d steps did not reproduce" % (len(mismatches),
                                                               len(comparisons)),
                         replay_of=run_id, mismatches=mismatches[:20])
        run.run_end(outcome=report["verdict"], steps=len(comparisons),
                    replay_of=run_id, mismatches=len(mismatches))
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--upstream", default=UPSTREAM_ARC)
    ap.add_argument("--mock", action="store_true",
                    help="replay against a fresh mock world; the point is that a "
                         "deterministic world reproduces the same frames")
    args = ap.parse_args(argv)

    if args.mock:
        from .mock.arc_mock import DEFAULT_KEY, MockArc
        game_id = (commands_of(args.run_id, args.ledger) or [{}])[0].get("game_id")
        with MockArc(api_key=DEFAULT_KEY, games=[game_id]) as arc:
            report = replay_run(args.run_id, ledger_path=args.ledger,
                                env_upstream=arc.base_url, env_key=DEFAULT_KEY,
                                require_key=False)
    else:
        report = replay_run(args.run_id, ledger_path=args.ledger,
                            env_upstream=args.upstream)

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
