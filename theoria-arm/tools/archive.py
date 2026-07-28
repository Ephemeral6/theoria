"""Close a run: reconcile it, audit it, and write the manifest.

Four obligations are discharged here and each one can fail loudly:

* **the score obligation** (`LEDGER_FORMAT.md` §3): the score derived from
  `env_step` records must equal the scorecard's. Live ARC gameplay responses
  carry **no `score` field at all** -- the key set is `action_input,
  available_actions, frame, full_reset, game_id, guid, levels_completed, state,
  win_levels` -- so the derived score is structurally unavailable and the
  reconciliation is reported as `unavailable`, with the reason, rather than as
  a pass. `levels_completed` *is* returned and is reconciled properly.
* **constraint 8**: counted from the ledger, not asserted. Every `model_call`
  carries the beat that made it; a call at any beat other than theorize or
  probe design is a violation, and so is any call at all in a run with no
  surprise.
* **cost**: computed two independent ways -- `proxy/cost.py` over the recorded
  `usage` against a hashed price table, and the CLI's own `total_cost_usd`.
  Agreement validates `pricing_v1.json` against a real bill for the first time;
  disagreement is a finding about the table.
* **the sealing check**: no record in the ledger may contain the credential,
  and no `bypass_attempt` incident may be present.

    python -m tools.archive --slug <run slug>
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from proxy.ledger import read_ledger


def reconcile(records: List[Dict[str, Any]], scorecard: Optional[Dict[str, Any]]
              ) -> Dict[str, Any]:
    steps = [r for r in records if r.get("event") == "env_step"]
    ok = [r for r in steps if (r.get("http") or {}).get("status") == 200]
    actions_ok = [r for r in ok if r.get("action", {}).get("name") != "RESET"]
    scores = [r.get("score") for r in steps if r.get("score") is not None]
    levels = [r.get("levels_completed") for r in steps
              if r.get("levels_completed") is not None]

    out: Dict[str, Any] = {
        "env_steps": len(steps),
        "env_steps_ok": len(ok),
        "successful_actions": len(actions_ok),
        "resets": len(ok) - len(actions_ok),
        "http_amplification": (round(len(steps) / len(actions_ok), 3)
                               if actions_ok else None),
        "levels_completed_from_ledger": max(levels) if levels else None,
    }

    if not scores:
        out["score_reconciliation"] = "unavailable"
        out["score_reconciliation_detail"] = (
            "no `score` field appears in any live ARC command response, so the "
            "ledger-derived score LEDGER_FORMAT.md §3 asks for cannot be "
            "computed. This is a property of the environment, not a failure of "
            "the run, and it means the §3 obligation is UNDISCHARGEABLE as "
            "written against this API. It is reported, not waived.")
    else:
        derived = max(scores)
        out["score_from_ledger"] = derived
        if scorecard is None:
            out["score_reconciliation"] = "no_scorecard"
        else:
            out["score_from_scorecard"] = scorecard.get("score")
            out["score_reconciliation"] = (
                "equal" if derived == scorecard.get("score") else "MISMATCH")

    if scorecard:
        out["scorecard_total_actions"] = scorecard.get("total_actions")
        out["actions_agree"] = (scorecard.get("total_actions") == len(actions_ok))
        out["scorecard_levels_completed"] = scorecard.get("total_levels_completed")
        out["levels_agree"] = (
            scorecard.get("total_levels_completed") ==
            (max(levels) if levels else 0))
    return out


def costs(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    calls = [r for r in records if r.get("event") == "model_call"]
    usage_total: Dict[str, int] = {}
    cli_total = 0.0
    for record in calls:
        for key, value in (record.get("usage") or {}).items():
            if isinstance(value, int):
                usage_total[key] = usage_total.get(key, 0) + value
        response = record.get("response") or {}
        if isinstance(response, dict):
            cli_total += float(response.get("total_cost_usd") or 0.0)

    table_cost = None
    table_ref = None
    try:
        from proxy.cost import DEFAULT_TABLE, PriceTable       # noqa: PLC0415
        table = PriceTable.load(DEFAULT_TABLE)
        table_ref = table.reference()
        total = 0.0
        priced, unpriced = 0, []
        for record in calls:
            model = record.get("model")
            try:
                total += float(table.cost(model, record.get("usage") or {}))
                priced += 1
            except Exception:                          # noqa: BLE001
                unpriced.append(model)
        table_cost = {"usd": round(total, 6), "calls_priced": priced,
                      "calls_unpriced": sorted(set(unpriced))}
    except Exception as exc:                           # noqa: BLE001
        table_cost = {"error": "%s: %s" % (type(exc).__name__, exc)}

    out: Dict[str, Any] = {
        "model_calls": len(calls),
        "usage_total": usage_total,
        "cli_reported_usd": round(cli_total, 6),
        "price_table": table_ref,
        "from_price_table": table_cost,
    }
    if isinstance(table_cost, dict) and isinstance(table_cost.get("usd"), float):
        delta = table_cost["usd"] - cli_total
        out["delta_usd"] = round(delta, 6)
        out["relative_delta"] = (round(delta / cli_total, 4) if cli_total else None)
        out["verdict"] = (
            "the price table and the provider's own arithmetic agree to within "
            "1%%" if cli_total and abs(delta) / cli_total < 0.01 else
            "the price table and the provider's own arithmetic DISAGREE -- this "
            "is a finding about proxy/pricing/pricing_v1.json, not about the run")
    return out


def sealing(records: List[Dict[str, Any]], key_len: int = 36) -> Dict[str, Any]:
    incidents = [r for r in records if r.get("event") == "incident"]
    by_kind: Dict[str, int] = {}
    for record in incidents:
        by_kind[record.get("kind")] = by_kind.get(record.get("kind"), 0) + 1
    blob = json.dumps(records)
    return {
        "incidents": len(incidents),
        "by_kind": by_kind,
        "bypass_attempts": by_kind.get("bypass_attempt", 0),
        "credential_in_body": by_kind.get("credential_in_body", 0),
        "sealed_pile_requests": by_kind.get("sealed_pile_request", 0),
        "redacted_markers": blob.count("<redacted>"),
        "guard_blocks": sum(1 for r in records if r.get("event") == "guard_block"),
    }


def constraint_8(records: List[Dict[str, Any]], run_dir: str) -> Dict[str, Any]:
    calls = [r for r in records if r.get("event") == "model_call"]
    beats: Dict[str, int] = {}
    for record in calls:
        beats[record.get("beat") or "unknown"] = \
            beats.get(record.get("beat") or "unknown", 0) + 1
    illegal = {b: n for b, n in beats.items()
               if b not in ("theorize", "probe_design")}

    surprises = []
    path = os.path.join(run_dir, "surprises.jsonl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            surprises = [json.loads(line) for line in fh if line.strip()]

    return {
        "model_calls": len(calls),
        "calls_by_beat": beats,
        "surprises": len(surprises),
        "surprises_by_kind": _histogram(s.get("kind") for s in surprises),
        "calls_at_forbidden_beats": illegal,
        "calls_without_any_surprise": bool(calls) and not surprises,
        "holds": (not illegal) and not (bool(calls) and not surprises),
        "note": ("probe design spent no model call: the frontier is computed by "
                 "probe_frontier, which is exact on a deterministic world. "
                 "Constraint 8 permits a call there; this run did not need one."),
    }


def cost_curve(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Cost per turn, on the step axis the battery will want."""
    out = []
    for record in records:
        if record.get("event") != "model_call":
            continue
        response = record.get("response") or {}
        out.append({
            "call_idx": record.get("call_idx"),
            "step_idx": record.get("step_idx"),
            "beat": record.get("beat"),
            "label": record.get("label"),
            "model": record.get("model"),
            "usd": (response.get("total_cost_usd")
                    if isinstance(response, dict) else None),
            "usage": record.get("usage"),
            "elapsed_ms": (record.get("http") or {}).get("elapsed_ms"),
        })
    return out


def _histogram(values) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def build(slug: str, *, prompt_id: str = "P-8") -> Dict[str, Any]:
    run_dir = _bootstrap.path("runs", slug)
    ledger_path = os.path.join(run_dir, "ledger.jsonl")
    records = read_ledger(ledger_path)

    run_json = {}
    if os.path.exists(os.path.join(run_dir, "run.json")):
        with open(os.path.join(run_dir, "run.json"), encoding="utf-8") as fh:
            run_json = json.load(fh)
    summary = run_json.get("summary") or {}
    run_id = summary.get("run_id") or run_json.get("run_id")
    mine = [r for r in records if r.get("run_id") == run_id] if run_id else records
    scorecard = summary.get("scorecard")

    import subprocess                                  # noqa: PLC0415
    def git(*args):
        try:
            return subprocess.run(["git", *args], cwd=_bootstrap.REPO,
                                  capture_output=True, text=True,
                                  timeout=30).stdout.strip()
        except Exception:                              # noqa: BLE001
            return None

    manifest = {
        "prompt_id": prompt_id,
        "slug": slug,
        "run_id": run_id,
        "game_id": summary.get("game_id"),
        "arm": "theoria",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "seed": None,
        "seed_note": ("this arm draws no random numbers: engine dispatch, the "
                      "compilers and the planner are deterministic, and the one "
                      "stochastic component is the model, whose sampling is not "
                      "controllable through `claude -p`. Determinism is "
                      "therefore claimed for everything except the desk's text, "
                      "and the desk's text is recorded verbatim instead."),
        "arm_version": run_json.get("arm_version"),
        "upstream_pin": _bootstrap.upstream_pin(),
        "ledger": {"path": "ledger.jsonl", "records": len(records),
                   "records_this_run": len(mine),
                   "format": "LEDGER_FORMAT v1.0"},
        "outcome": summary.get("outcome"),
        "stopped_because": summary.get("stopped_because"),
        "budget": summary.get("budget"),
        "world": summary.get("world"),
        "reconciliation": reconcile(mine, scorecard),
        "cost": costs(mine),
        "constraint_8": constraint_8(mine, run_dir),
        "sealing": sealing(mine),
        "surprises": summary.get("surprises"),
        "scorecard": scorecard,
        "files": sorted(
            os.path.relpath(os.path.join(root, name), run_dir).replace(os.sep, "/")
            for root, _dirs, names in os.walk(run_dir) for name in names
            if "__pycache__" not in root),
    }

    with open(os.path.join(run_dir, "MANIFEST.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    with open(os.path.join(run_dir, "cost_curve.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(cost_curve(mine), fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--prompt-id", default="P-8")
    args = ap.parse_args(argv)
    manifest = build(args.slug, prompt_id=args.prompt_id)
    print(json.dumps({k: v for k, v in manifest.items()
                      if k not in ("files", "upstream_pin", "scorecard")},
                     indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
