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

    python -m armtools.archive --slug <run slug>
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from harness.modelcall import call_field

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

    # `proxy/cost.py`'s own `price_run` is the conversion, used as it is meant
    # to be. An earlier version of this function called `PriceTable.cost`
    # directly and coerced its return to a float -- it returns a *dict* -- so
    # every call landed in the exception path and the report announced that the
    # price table could not price `claude-opus-5`. It can. The lesson is worth
    # the comment: a cross-check that can only fail in one direction is not a
    # cross-check, and this one was reporting its own defect as a finding about
    # somebody else's file.
    table_cost: Dict[str, Any]
    table_ref = None
    unpriced_keys: List[str] = []
    try:
        from proxy.cost import DEFAULT_TABLE, PriceTable, price_run   # noqa: PLC0415
        table = PriceTable.load(DEFAULT_TABLE)
        table_ref = table.reference()
        table_cost = price_run(calls, table)
        for record in calls:
            line = table.cost(record.get("model", "?"), record.get("usage") or {})
            for key in (line.get("unpriced_usage_keys") or []):
                if key not in unpriced_keys:
                    unpriced_keys.append(key)
    except Exception as exc:                           # noqa: BLE001
        table_cost = {"error": "%s: %s" % (type(exc).__name__, exc)}

    out: Dict[str, Any] = {
        "model_calls": len(calls),
        "usage_total": usage_total,
        "cli_reported_usd": round(cli_total, 6),
        "price_table": table_ref,
        "from_price_table": table_cost,
        "usage_keys_the_table_cannot_price": sorted(unpriced_keys) or None,
    }
    out["cache_ttl_diagnosis"] = _cache_ttl_diagnosis(calls, table_ref)

    table_usd = table_cost.get("usd_total")
    if isinstance(table_usd, (int, float)) and cli_total:
        delta = table_usd - cli_total
        out["delta_usd"] = round(delta, 6)
        out["relative_delta"] = round(delta / cli_total, 4)
        agree = abs(delta) / cli_total < 0.02
        out["verdict"] = (
            "the price table and the provider's own arithmetic agree to within "
            "2%: pricing_v1.json is validated against a real bill for the first "
            "time" if agree else
            "the price table and the provider's own arithmetic DISAGREE by "
            "%.1f%% -- a finding about proxy/pricing/pricing_v1.json (or about "
            "which usage keys it knows how to price), not about the run"
            % (100 * delta / cli_total))
    elif isinstance(table_usd, (int, float)):
        out["verdict"] = ("nothing to compare: the CLI reported no cost "
                          "(an offline or cached run)")
    return out


def _cache_ttl_diagnosis(calls: List[Dict[str, Any]],
                         table_ref: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Why the two cost figures differ, computed rather than guessed.

    `pricing_v1.json` carries two cache-write multipliers -- 1.25x for the
    5-minute TTL and 2.0x for the 1-hour one -- but `proxy/cost.py` can only
    ever apply the first, because the provider's flat
    `cache_creation_input_tokens` key does not say which TTL was bought. The
    TTL *is* reported, in a nested `usage.cache_creation` object with
    `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens`, which
    `cost.py` does not read. When a run's cache writes are all 1-hour, the
    table under-bills every one of them by the difference between the two
    multipliers, and this function says by exactly how much.
    """
    total_1h = total_5m = 0
    for record in calls:
        nested = (record.get("usage") or {}).get("cache_creation") or {}
        total_1h += int(nested.get("ephemeral_1h_input_tokens") or 0)
        total_5m += int(nested.get("ephemeral_5m_input_tokens") or 0)

    out: Dict[str, Any] = {
        "cache_creation_1h_tokens": total_1h,
        "cache_creation_5m_tokens": total_5m,
        "table": table_ref,
    }
    if not total_1h:
        out["verdict"] = ("no 1-hour cache writes in this run, so the flat "
                          "1.25x multiplier is the right one and this is not a "
                          "source of disagreement")
        return out

    try:
        from proxy.cost import DEFAULT_TABLE, PriceTable       # noqa: PLC0415
        table = PriceTable.load(DEFAULT_TABLE)
        models = {r.get("model") for r in calls if r.get("model")}
        under = 0.0
        for model in models:
            prices = table.models.get(model)
            if not prices:
                continue
            per_token_in = prices["input"] / 1_000_000.0
            gap = (table.cache.get("cache_creation_input_tokens_1h", 2.0)
                   - table.cache.get("cache_creation_input_tokens", 1.25))
            tokens = sum(
                int(((r.get("usage") or {}).get("cache_creation") or {})
                    .get("ephemeral_1h_input_tokens") or 0)
                for r in calls if r.get("model") == model)
            under += tokens * per_token_in * gap
        out["under_billed_usd"] = round(under, 6)
        out["verdict"] = (
            "%d of this run's cache-creation tokens were 1-hour writes. "
            "`proxy/cost.py` priced them at the 5-minute multiplier because it "
            "reads the flat usage key and not the nested `cache_creation` "
            "object, so the table under-states this run by about $%.4f. The "
            "multiplier it needs is already in pricing_v1.json "
            "(`cache_creation_input_tokens_1h`); what is missing is the read."
            % (total_1h, under))
    except Exception as exc:                           # noqa: BLE001
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    return out


def sealing(records: List[Dict[str, Any]], key_len: int = 36) -> Dict[str, Any]:
    incidents = [r for r in records if r.get("event") == "incident"]
    by_kind: Dict[str, int] = {}
    for record in incidents:
        by_kind[record.get("kind")] = by_kind.get(record.get("kind"), 0) + 1
    blob = json.dumps(records)

    # The sealed pile, checked against the cut itself rather than against the
    # guard's own opinion of what it blocked. The guard fails closed and is
    # tested, but "the guard did not fire" is a statement about the guard; this
    # is a statement about the bytes. Every game id mentioned anywhere in this
    # run's records is compared with `arc-recon/data/piles.json`.
    sealed_seen: List[str] = []
    games_seen: List[str] = []
    try:
        from proxy.guard import load_piles              # noqa: PLC0415
        piles = load_piles(verify=True)
        sealed = set(piles.get("sealed_pile") or [])
        if not sealed:
            raise ValueError("piles.json carries no sealed_pile; refusing to "
                             "report 'sealed pile untouched' from an empty set")
        pattern = re.compile(r"\b([A-Za-z0-9]{2,6}-[0-9a-f]{8})\b")
        for match in pattern.finditer(blob):
            game = match.group(1)
            if game not in games_seen:
                games_seen.append(game)
            if game in sealed and game not in sealed_seen:
                sealed_seen.append(game)
        cut_ok: Any = True
    except Exception as exc:                            # noqa: BLE001
        cut_ok = "%s: %s" % (type(exc).__name__, exc)

    return {
        "incidents": len(incidents),
        "by_kind": by_kind,
        "bypass_attempts": by_kind.get("bypass_attempt", 0),
        "credential_in_body": by_kind.get("credential_in_body", 0),
        "sealed_pile_requests": by_kind.get("sealed_pile_request", 0),
        "redacted_markers": blob.count("<redacted>"),
        "guard_blocks": sum(1 for r in records if r.get("event") == "guard_block"),
        "game_ids_anywhere_in_the_records": sorted(games_seen),
        "sealed_game_ids_found": sorted(sealed_seen),
        "sealed_pile_untouched": (not sealed_seen) if cut_ok is True else cut_ok,
        "cut_integrity": cut_ok,
    }


def constraint_8(records: List[Dict[str, Any]], run_dir: str) -> Dict[str, Any]:
    calls = [r for r in records if r.get("event") == "model_call"]
    beats: Dict[str, int] = {}
    for record in calls:
        beat = call_field(record, "beat") or "unknown"
        beats[beat] = beats.get(beat, 0) + 1
    illegal = {b: n for b, n in beats.items()
               if b not in ("theorize", "probe_design")}

    surprises = []
    path = os.path.join(run_dir, "surprises.jsonl")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            surprises = [json.loads(line) for line in fh if line.strip()]

    # The bootstrap exception, named rather than smuggled. Constraint 8 says a
    # model is called only when a surprise fired. The FIRST theorize of a run
    # has no surprise to answer: there is no manual yet, so there is nothing
    # for the world to have contradicted. One call is therefore permitted
    # before the first surprise and every later one must be preceded by a
    # surprise. Stating it this way makes the check strictly stronger than
    # "calls > 0 and surprises == 0", which a long run would pass trivially.
    bootstrap = 1 if calls else 0

    # A retired surprise did not cause a model call, so it must not licence
    # one. `handled_by` records who closed a surprise; anything closed with
    # `"retired: ..."` was closed *without* theorizing -- today only by a level
    # boundary. Counting those in the denominator raises the ceiling on
    # unexplained calls by one apiece, which is a false negative in exactly the
    # direction that hides a violation of the arm's central claim: three
    # boundaries retiring two surprises each would buy six free unexplained
    # model calls with `holds` still True.
    #
    # This was found by an adversarial review while the boundary still retired
    # surprises. It no longer does (`DECISIONS.md` D-A3-003), so nothing on the
    # live path reaches this today -- but `Register.retire_pending` still
    # exists, and an audit that miscounts in the lenient direction is worth
    # fixing whether or not today's code path trips it. The retired ones are
    # reported rather than dropped: "how many surprises died at a boundary" is
    # itself a datum.
    def _retired(item):
        return str(item.get("handled_by") or "").startswith("retired:")

    retired = [s for s in surprises if _retired(s)]
    licensing = [s for s in surprises if not _retired(s)]
    unexplained = max(0, len(calls) - bootstrap - len(licensing))

    return {
        "model_calls": len(calls),
        "calls_by_beat": beats,
        "surprises": len(surprises),
        "surprises_licensing_a_call": len(licensing),
        "surprises_retired": len(retired),
        "surprises_by_kind": _histogram(s.get("kind") for s in surprises),
        "retired_by_kind": _histogram(s.get("kind") for s in retired),
        "calls_at_forbidden_beats": illegal,
        "bootstrap_calls_allowed": bootstrap,
        "calls_beyond_bootstrap": max(0, len(calls) - bootstrap),
        "calls_not_covered_by_a_surprise": unexplained,
        "holds": (not illegal) and unexplained == 0,
        "bootstrap_note": (
            "the first theorize of a run answers no surprise because no manual "
            "exists yet for the world to contradict; it is counted as the one "
            "permitted bootstrap call and every later call must be covered by "
            "a surprise."),
        "retired_note": (
            "a surprise closed with handled_by='retired: ...' was closed "
            "without theorizing, so it licences no model call and is excluded "
            "from the denominator. It is still counted in `surprises` and in "
            "`surprises_by_kind`, because the seven counts are a record of "
            "what the world did, not of what was paid for."),
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
            "beat": call_field(record, "beat"),
            "label": call_field(record, "label"),
            "model": record.get("model"),
            "usd": (response.get("total_cost_usd")
                    if isinstance(response, dict) else None),
            "usage": record.get("usage"),
            "elapsed_ms": (record.get("http") or {}).get("elapsed_ms"),
        })
    return out


# ---------------------------------------------------------------------------
# The turn series: the join nobody was performing.
#
# Three writers record the three quantities figure 2 ("bill shape") needs, and
# none of them shares an index with the others:
#
#   * `harness/modelcall.py` writes one `model_call` per billed invocation,
#     keyed by `call_idx` and stamped with `step_idx`;
#   * `inner/loop.py` appends one record per turn to `turns.json`, keyed by
#     `turn` and carrying `actions_before` (= `budget.actions_ok`);
#   * `inner/surprise.py` writes one line per surprise to `surprises.jsonl`,
#     stamped with a *frame* index (often `None`) and a wall-clock `ts`.
#
# `turn_series()` is the join. What follows is the reasoning it rests on,
# written down because a join that is only in someone's head is a join that
# will be silently wrong later.
#
# **The bridge between the two integer indexes is arithmetic and exact.**
# `loop.py` passes `step_idx=len(self.store.steps)` into every theorize call,
# and `FrameStore` gains exactly one step per `arc.act()` -- successful or not,
# RESET included, because `_record` runs whatever the status was.
# `harness/budget.py` counts those same commands into three disjoint
# counters. Therefore, at any instant:
#
#     len(store.steps) == resets + actions_ok + actions_failed
#
# and since `record["actions_before"]` is `budget.actions_ok` sampled at the
# top of the turn, a turn's theorize calls carry
#
#     step_idx == actions_before + resets_so_far + actions_failed_so_far
#
# `resets_so_far` is constant through the main loop (RESET happens once, in
# `play()`, before it). `actions_failed_so_far` is *not* recorded per turn, so
# the identity is only closed-form when a run failed no action at all. That is
# why the arithmetic bridge is used as a **check** and not as the allocator.
#
# **The allocator is structural.** `inner/theorize.py` labels its calls
# `"round%d" % (attempt + 1)`, and that counter restarts inside every
# `theorize.run()`. So a call labelled `round1` is the first billed attempt of
# a fresh theorize *invocation*, and one invocation is exactly one increment of
# `record["theorize_rounds"]`. Segmenting the call list at each `round1`
# recovers the invocations; handing them to turns in order, `theorize_rounds`
# at a time, recovers the turns -- using two fields written by two different
# modules that agree only if the join is right.
#
# **Within a turn `step_idx` cannot move.** `_theorize_and_certify` sends no
# ARC command between rounds; certify only replays. And **between turns it
# must move**, because every main-loop turn ends in `_commit` or
# `_probe_or_explore` and both send at least one command, which `_record`
# counts even when it fails. Constant-within / increasing-between is therefore
# a property the join must exhibit, and it is asserted rather than assumed.
#
# **Surprises join by time, not by index.** A surprise's own `step_idx` is a
# frame ordinal (`None` for render mismatches), so it cannot address a turn.
# But every surprise is stamped when it fires, and turns are contiguous
# intervals of wall clock, so containment decides it. The one weakness is
# resolution: `Surprise.ts` is truncated to the second while ledger stamps
# carry milliseconds, so a surprise landing inside a second that straddles a
# turn boundary is genuinely ambiguous. Those are counted and reported rather
# than assigned quietly.
# ---------------------------------------------------------------------------

#: The seven kinds, imported rather than re-listed. `inner/surprise.py` holds
#: the position that a zero is a measurement and not an absence, and every row
#: this module emits carries all seven keys for the same reason.
try:
    from inner.surprise import COMPUTATIONAL, EMPIRICAL, KINDS
except Exception:                                      # noqa: BLE001
    EMPIRICAL = ("replay_mismatch", "render_mismatch", "proof_failure",
                 "probe_refutation", "execution_mismatch")
    COMPUTATIONAL = ("search_timeout", "heuristic_miss")
    KINDS = EMPIRICAL + COMPUTATIONAL

#: `inner/loop.py`'s ceiling on theorize invocations per turn. Imported when it
#: can be (a stale copy here would silently weaken the structural check) and
#: defaulted otherwise; which of the two happened is recorded in the join block.
_MAX_THEORIZE_SOURCE = "inner.loop.MAX_THEORIZE_PER_TURN"
try:
    from inner.loop import MAX_THEORIZE_PER_TURN
except Exception:                                      # noqa: BLE001
    MAX_THEORIZE_PER_TURN = 2
    _MAX_THEORIZE_SOURCE = "fallback (inner.loop not importable)"

#: `battery/metrics/economy.py`'s constants, mirrored so this module can emit
#: the metric's input and its own reading of it without importing the battery.
FRONTLOAD_K = 0.25
MIN_TURNS_FOR_SHAPE = 8


def _zero_counts() -> Dict[str, int]:
    """All seven kinds at zero. Never a partial dict, never an empty one."""
    return {kind: 0 for kind in KINDS}


def _sha256_file(path: str):
    import hashlib                                     # noqa: PLC0415
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return None


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except (OSError, ValueError):
        return []


def _epoch(stamp: Optional[str]) -> Optional[float]:
    """ISO8601 `...Z` -> epoch seconds. Both resolutions the arm writes."""
    if not stamp or not isinstance(stamp, str):
        return None
    from datetime import datetime                      # noqa: PLC0415
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _call_usd(record: Dict[str, Any]) -> float:
    response = record.get("response") or {}
    if isinstance(response, dict):
        return float(response.get("total_cost_usd") or 0.0)
    return 0.0


def _invocations(calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Segment billed calls into desk *invocations*.

    A new invocation starts at every `round1` label -- `inner/theorize.py`
    restarts its attempt counter inside each `theorize.run()` -- and also
    whenever the beat or the step index moves, which no retry of one
    invocation can do.
    """
    out: List[Dict[str, Any]] = []
    for record in calls:
        label = call_field(record, "label") or ""
        fresh = (
            not out
            or label in ("", "round1")
            or record.get("step_idx") != out[-1]["step_idx"]
            or call_field(record, "beat") != out[-1]["beat"])
        if fresh:
            out.append({"beat": call_field(record, "beat"),
                        "step_idx": record.get("step_idx"),
                        "calls": [record]})
        else:
            out[-1]["calls"].append(record)
    for inv in out:
        inv["usd"] = sum(_call_usd(c) for c in inv["calls"])
        inv["call_idx"] = [c.get("call_idx") for c in inv["calls"]]
        first = inv["calls"][0]
        end = _epoch(first.get("ts"))
        elapsed = (first.get("http") or {}).get("elapsed_ms")
        inv["started_at"] = (end - (float(elapsed) / 1000.0)
                             if end is not None and elapsed else end)
        inv["ended_at"] = _epoch(inv["calls"][-1].get("ts"))
    return out


def _histogram(values) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for value in values:
        out[str(value)] = out.get(str(value), 0) + 1
    return out


def _base_commit_check(arm_version: Dict[str, Any],
                       head: Optional[str]) -> Dict[str, Any]:
    """Does `base_commit` actually describe the tree this run ran against?

    Never raises and never blocks a manifest: an archive that fails to be
    written because a provenance check errored is worse than one with an
    unchecked field. A failure here is reported inside the manifest.
    """
    recorded = arm_version.get("sha256")
    if not recorded:
        return {"verdict": "no_arm_version_recorded",
                "detail": "the ledger's run_start carries no arm_version to check"}
    try:
        from armtools import armversion                # noqa: PLC0415
        located = armversion.locate(recorded)
        derived = located["commits"][0] if located["verdict"] == "matched" else None
        if derived and head:
            return {
                "verdict": "agree" if derived == head else "DISAGREE",
                "base_commit_recorded": head,
                "base_commit_the_arm_version_reconstructs": derived,
                "detail": ("HEAD is the tree this run ran against"
                           if derived == head else
                           "`base_commit` is where HEAD is now; the run ran at "
                           "the derived commit. The derived one is the "
                           "reproducible one and should be preferred."),
            }
        return {
            "verdict": located["verdict"],
            "base_commit_recorded": head,
            "base_commit_the_arm_version_reconstructs": derived,
            "detail": located["detail"],
        }
    except Exception as exc:                           # noqa: BLE001
        return {"verdict": "check_failed",
                "detail": "%s: %s" % (type(exc).__name__, exc)}


def _turn_spine(turns_json, invocations, budget) -> Dict[str, Any]:
    """Decide what the turns were, and say how confident that is.

    Two modes, and the difference between them is not cosmetic.

    * `turns.json` present: `inner/loop.py` itself recorded the turns, so the
      spine is read rather than inferred and the invocations are dealt out
      `theorize_rounds` at a time.
    * `turns.json` absent -- which is what a run killed before `_save_all()`
      looks like, including the only live run this arm has -- the spine is
      reconstructed from the step index. That is exact **only** where the step
      index advances by one between consecutive billed turns: a gap of *k*
      could equally be one turn that committed a *k*-step plan or *k-1* turns
      whose theorize the evidence gate skipped. Those two readings are not
      distinguishable from the ledger and the ambiguity is reported, not
      resolved by preference.
    """
    checks: List[Dict[str, Any]] = []
    theorize = [i for i in invocations if i["beat"] == "theorize"]

    # -- the structural invariants, checked before anything is allocated ----
    by_step: Dict[Any, int] = {}
    for inv in theorize:
        by_step[inv["step_idx"]] = by_step.get(inv["step_idx"], 0) + 1
    over = {s: n for s, n in by_step.items() if n > MAX_THEORIZE_PER_TURN}
    checks.append({
        "check": "theorize invocations per step index <= MAX_THEORIZE_PER_TURN",
        "max_theorize_per_turn": MAX_THEORIZE_PER_TURN,
        "constant_source": _MAX_THEORIZE_SOURCE,
        "violations": {str(k): v for k, v in sorted(over.items(), key=str)},
        "ok": not over})
    seen = [i["step_idx"] for i in theorize if i["step_idx"] is not None]
    monotone = all(a <= b for a, b in zip(seen, seen[1:]))
    checks.append({"check": "step_idx never decreases across billed calls",
                   "ok": bool(monotone)})

    if turns_json:
        rows: List[Dict[str, Any]] = []
        queue = list(theorize)
        for record in turns_json:
            want = int(record.get("theorize_rounds") or 0)
            taken, queue = queue[:want], queue[want:]
            steps = {i["step_idx"] for i in taken}
            if len(steps) > 1:
                checks.append({
                    "check": "step_idx constant within turn %s"
                             % record.get("turn"),
                    "ok": False, "saw": sorted(steps, key=str)})
            rows.append({"turn": record.get("turn"),
                         "actions_before": record.get("actions_before"),
                         "elapsed_s": record.get("elapsed_s"),
                         "theorize_rounds": want,
                         "step_idx": (sorted(steps, key=str)[0] if steps
                                      else None),
                         "invocations": taken,
                         "from": "turns.json"})
        checks.append({
            "check": "every billed theorize invocation was claimed by a turn",
            "ok": not queue, "unclaimed": [i["call_idx"] for i in queue]})

        # The arithmetic bridge, usable only when nothing failed: without a
        # per-turn `actions_failed` the offset between the two indexes is not
        # closed-form. Reported either way so a reader can see which.
        failed = int((budget or {}).get("actions_failed") or 0)
        resets = int((budget or {}).get("resets") or 0)
        if failed == 0:
            bad = [r for r in rows
                   if r["step_idx"] is not None
                   and r["actions_before"] is not None
                   and r["step_idx"] != r["actions_before"] + resets]
            checks.append({
                "check": "step_idx == actions_before + resets (run failed no "
                         "action, so the identity is closed-form)",
                "resets": resets, "ok": not bad,
                "offenders": [r["turn"] for r in bad]})
        else:
            checks.append({
                "check": "step_idx == actions_before + resets + "
                         "actions_failed_so_far",
                "ok": None,
                "reason": "the run failed %d action(s) and no turn record "
                          "carries a running failed-action count, so the "
                          "offset is not closed-form per turn. The structural "
                          "allocation stands on its own; this cross-check "
                          "cannot be run." % failed})
        confidence = ("exact" if all(c.get("ok") is not False for c in checks)
                      else "degraded")
        return {"rows": rows, "checks": checks, "join_confidence": confidence,
                "spine": "turns.json"}

    # -- reconstruction ----------------------------------------------------
    groups: List[Dict[str, Any]] = []
    for inv in invocations:
        if groups and inv["step_idx"] == groups[-1]["step_idx"]:
            groups[-1]["invocations"].append(inv)
        else:
            groups.append({"step_idx": inv["step_idx"], "invocations": [inv]})

    resets = int((budget or {}).get("resets") or 0)
    gaps: List[Dict[str, Any]] = []
    for before, after in zip(groups, groups[1:]):
        if before["step_idx"] is None or after["step_idx"] is None:
            continue
        gap = after["step_idx"] - before["step_idx"]
        if gap != 1:
            gaps.append({"between_step_idx": [before["step_idx"],
                                              after["step_idx"]],
                         "store_steps_between": gap,
                         "readings": "one turn committing %d actions, or up to "
                                     "%d turn(s) whose theorize the evidence "
                                     "gate skipped" % (gap, max(gap - 1, 0))})

    # The tail: store steps recorded after the last billed turn's theorize.
    total_steps = (resets
                   + int((budget or {}).get("actions_ok") or 0)
                   + int((budget or {}).get("actions_failed") or 0))
    tail = None
    if groups and groups[-1]["step_idx"] is not None:
        tail = total_steps - groups[-1]["step_idx"]
    checks.append({
        "check": "len(store.steps) == resets + actions_ok + actions_failed",
        "store_steps_at_end": total_steps, "budget": budget,
        "last_billed_step_idx": (groups[-1]["step_idx"] if groups else None),
        "store_steps_after_the_last_billed_turn": tail,
        "ok": True if tail is None else tail >= 0})

    rows = []
    # Turn 0 is the opening sweep: `loop.py` appends it to `self.turns` with
    # `turn: 0` and it spends no model call by construction.
    rows.append({"turn": 0, "actions_before": 0, "elapsed_s": None,
                 "theorize_rounds": 0, "step_idx": None, "invocations": [],
                 "from": "reconstructed (opening sweep)"})
    for n, group in enumerate(groups, start=1):
        rows.append({
            "turn": n,
            "actions_before": (group["step_idx"] - resets
                               if group["step_idx"] is not None else None),
            "elapsed_s": None,
            "theorize_rounds": sum(1 for i in group["invocations"]
                                   if i["beat"] == "theorize"),
            "step_idx": group["step_idx"],
            "invocations": group["invocations"],
            "from": "reconstructed (step_idx grouping)"})

    # With no turn record to read `actions_before` from, the reconstruction
    # infers it as `step_idx - resets`. That is only the successful-action
    # count if nothing failed; a failed action also advances the store index
    # and would shift every inferred `actions_before` by one.
    failed = int((budget or {}).get("actions_failed") or 0)
    checks.append({
        "check": "actions_before can be inferred as step_idx - resets "
                 "(requires actions_failed == 0)",
        "actions_failed": failed, "ok": failed == 0,
        "reason": None if failed == 0 else
                  "%d failed action(s) also advanced the store index, so the "
                  "inferred actions_before is a lower bound, not the value "
                  "the turn would have recorded" % failed})

    trailing = (tail is not None and tail > 1)
    ambiguous = bool(gaps) or trailing or failed > 0
    if trailing:
        gaps.append({"after_the_last_billed_turn": True,
                     "store_steps_after": tail,
                     "readings": "the run may have taken up to %d further "
                                 "turn(s) that spent no model call and are "
                                 "therefore invisible in the cost curve"
                                 % max(tail - 1, 0)})
    checks.append({
        "check": "the step-index progression admits exactly one turn "
                 "decomposition",
        "ok": not ambiguous, "gaps": gaps})
    confidence = ("ambiguous-reconstructed" if ambiguous
                  else "exact-reconstructed")
    if any(c.get("ok") is False for c in checks[:2]):
        confidence = "degraded"
    return {"rows": rows, "checks": checks, "join_confidence": confidence,
            "spine": "reconstructed from ledger step_idx (turns.json absent)"}


def turn_series(run_dir: str, *, records: Optional[List[Dict[str, Any]]] = None
                ) -> Dict[str, Any]:
    """One row per turn: cost, theorize rounds and all seven surprise counts.

    The raw material for figure 2 and the input `battery/metrics/economy.py`'s
    `frontload_index` needs. Writes nothing; `write_turn_series()` does that.
    """
    run_json = _read_json(os.path.join(run_dir, "run.json")) or {}
    summary = run_json.get("summary") or {}
    run_id = summary.get("run_id") or run_json.get("run_id")

    ledger_path = os.path.join(run_dir, "ledger.jsonl")
    if records is None:
        records = read_ledger(ledger_path) if os.path.exists(ledger_path) else []
    mine = ([r for r in records if r.get("run_id") == run_id]
            if run_id else list(records))

    calls = sorted((r for r in mine if r.get("event") == "model_call"),
                   key=lambda r: (r.get("call_idx") if r.get("call_idx")
                                  is not None else 0, r.get("seq") or 0))
    invocations = _invocations(calls)

    run_state = _read_json(os.path.join(run_dir, "RUN_STATE.json")) or {}
    budget = summary.get("budget") or run_state.get("budget") or {}
    turns_json = _read_json(os.path.join(run_dir, "turns.json"))
    if not isinstance(turns_json, list):
        turns_json = None

    spine = _turn_spine(turns_json, invocations, budget)

    # -- allocate the ARC commands by index, not by clock -------------------
    #
    # `actions_before` is `budget.actions_ok` sampled at the top of the turn,
    # so turn *i* owns the successful actions numbered `[ab[i], ab[i+1])`, and
    # the failed retries that preceded each of them belong to the same turn
    # because the retry loop runs inside one `arc.act()`. Walking the ledger in
    # order and cutting on that counter is exact and needs no timestamps --
    # which matters, because a turn whose theorize the evidence gate skipped
    # spends no model call and therefore has no clock of its own to be placed
    # by. An earlier draft of this function forward-filled such a turn's start
    # from its predecessor, which gave it an empty window and quietly handed
    # its actions to the following turn.
    ab: List[int] = []
    for i, row in enumerate(spine["rows"]):
        value = row.get("actions_before")
        if value is None:
            value = 0 if i == 0 else ab[-1]
        ab.append(int(value))

    steps = [r for r in mine if r.get("event") == "env_step"]
    owner: Dict[int, int] = {}
    done = 0
    for pos, step in enumerate(steps):
        turn_of = 0
        for i in range(len(ab)):
            if done >= ab[i]:
                turn_of = i
        owner[pos] = turn_of
        http = (step.get("http") or {}).get("status")
        if http == 200 and (step.get("action") or {}).get("name") != "RESET":
            done += 1

    # -- the surprise window, bounded by owned commands ---------------------
    #
    # A surprise is stamped when it fires and carries no turn of its own (its
    # `step_idx` is a frame ordinal, `None` for a render mismatch). Turns are
    # contiguous in wall clock and each one ends with its last ARC command, so
    # turn *i* owns `(last command of turn i-1, last command of turn i]`, with
    # the final turn open-ended so a run killed mid-turn keeps its surprises.
    t0 = next((_epoch(r.get("ts")) for r in mine
               if r.get("event") == "run_start"), None)
    last_cmd: Dict[int, Optional[float]] = {}
    for pos, step in enumerate(steps):
        when = _epoch(step.get("ts"))
        if when is not None:
            last_cmd[owner[pos]] = when
    edges: List[Optional[float]] = []
    running_edge = t0
    for i in range(len(spine["rows"])):
        running_edge = last_cmd.get(i, running_edge)
        edges.append(running_edge)

    def window(i):
        lo = edges[i - 1] if i > 0 else None
        hi = edges[i] if i < len(edges) - 1 else None
        return lo, hi

    surprises = _read_jsonl(os.path.join(run_dir, "surprises.jsonl"))

    ambiguous_surprises = 0
    stray_calls: List[Any] = []
    rows: List[Dict[str, Any]] = []
    running_usd = 0.0
    running_actions = 0
    for i, row in enumerate(spine["rows"]):
        lo, hi = window(i)

        def inside(stamp, lo=lo, hi=hi):
            when = _epoch(stamp)
            if when is None:
                return False
            return ((lo is None or when > lo)
                    and (hi is None or when <= hi))

        mine_steps = [s for pos, s in enumerate(steps) if owner[pos] == i]
        ok_steps = [s for s in mine_steps
                    if (s.get("http") or {}).get("status") == 200]
        actions = [s for s in ok_steps
                   if (s.get("action") or {}).get("name") != "RESET"]

        counts = _zero_counts()
        seqs: List[Any] = []
        for surprise in surprises:
            if not inside(surprise.get("ts")):
                continue
            kind = surprise.get("kind")
            if kind in counts:
                counts[kind] += 1
            seqs.append(surprise.get("seq"))
            when = _epoch(surprise.get("ts"))
            # `Surprise.ts` is second-resolution; a boundary inside that second
            # cannot be adjudicated from the record.
            for edge in (lo, hi):
                if edge is not None and when is not None and abs(when - edge) < 1.0:
                    ambiguous_surprises += 1
                    break

        usd = sum(inv["usd"] for inv in row["invocations"])
        running_usd += usd
        calls_here = [c for inv in row["invocations"] for c in inv["calls"]]

        # Consistency: a turn's own billed calls must fall inside the window
        # its commands define. Cheap to check and it is the one place the
        # index join and the clock join can be caught disagreeing.
        strays = [c.get("call_idx") for c in calls_here
                  if not inside(c.get("ts"))]
        if strays:
            stray_calls.extend(strays)

        began = (row["invocations"][0]["started_at"]
                 if row["invocations"] else lo)
        rows.append({
            "turn": row["turn"],
            "step_idx": row["step_idx"],
            "actions_before": running_actions,
            "actions_before_recorded": row.get("actions_before"),
            "actions_taken": len(actions),
            "http_commands": len(mine_steps),
            "elapsed_s": row.get("elapsed_s"),
            "wall_clock_s": (round(began - t0, 3)
                             if began is not None and t0 is not None else None),
            "theorize_rounds": row["theorize_rounds"],
            "model_calls": len(calls_here),
            "call_idx": [c.get("call_idx") for c in calls_here],
            "beats": sorted({inv["beat"] for inv in row["invocations"]
                             if inv["beat"]}),
            "usd": round(usd, 9),
            "usd_cumulative": round(running_usd, 9),
            "surprise_counts": counts,
            "surprise_total": sum(counts.values()),
            "surprise_by_family": {
                "empirical": sum(counts[k] for k in EMPIRICAL),
                "computational": sum(counts[k] for k in COMPUTATIONAL)},
            "surprise_seqs": seqs,
            "turn_source": row["from"],
        })
        running_actions += len(actions)

    total_usd = sum(r["usd"] for r in rows)
    for row in rows:
        row["usd_share"] = (round(row["usd"] / total_usd, 9)
                            if total_usd > 0 else 0.0)

    # -- reconciliation ----------------------------------------------------
    desk = summary.get("desk") or run_state.get("desk") or {}
    reported = desk.get("cli_cost_usd")
    ledger_total = sum(_call_usd(c) for c in calls)
    every = _zero_counts()
    for surprise in surprises:
        if surprise.get("kind") in every:
            every[surprise["kind"]] += 1
    joined = _zero_counts()
    for row in rows:
        for kind, n in row["surprise_counts"].items():
            joined[kind] += n

    recon = {
        "usd": {
            "sum_over_turns": round(total_usd, 9),
            "sum_over_model_call_records": round(ledger_total, 9),
            "reported_by_the_desk": reported,
            "delta_vs_desk": (round(total_usd - reported, 9)
                              if isinstance(reported, (int, float)) else None),
            "reconciles": (isinstance(reported, (int, float))
                           and abs(total_usd - reported) < 1e-9),
        },
        "surprises": {
            "sum_over_turns": sum(joined.values()),
            "in_surprises_jsonl": len(surprises),
            "by_kind_over_turns": joined,
            "by_kind_in_surprises_jsonl": every,
            "reconciles": joined == every,
        },
        "model_calls": {
            "sum_over_turns": sum(r["model_calls"] for r in rows),
            "in_ledger": len(calls),
            "reconciles": sum(r["model_calls"] for r in rows) == len(calls),
        },
        "actions": {
            "sum_over_turns": sum(r["actions_taken"] for r in rows),
            "budget_actions_ok": budget.get("actions_ok"),
            "reconciles": (sum(r["actions_taken"] for r in rows)
                           == budget.get("actions_ok")),
        },
    }

    # The two checks that can only be run once the rows exist, and the final
    # confidence. A join that failed a check reports `degraded` even if the
    # spine itself was authoritative -- the point of the checks is that they
    # can lower the claim, not decorate it.
    after = [
        {"check": "every billed call falls inside the window its turn's ARC "
                  "commands define -- the index join and the clock join agree",
         "ok": not stray_calls, "offenders": stray_calls},
        {"check": "actions_before recomputed from the ledger matches the "
                  "value the turn recorded",
         "ok": all(r["actions_before_recorded"] is None
                   or r["actions_before_recorded"] == r["actions_before"]
                   for r in rows),
         "offenders": [r["turn"] for r in rows
                       if r["actions_before_recorded"] is not None
                       and r["actions_before_recorded"] != r["actions_before"]]},
    ]
    checks = spine["checks"] + after
    # Only these two can lower the verdict. The spine's own checks have already
    # been folded into its label -- an ambiguous reconstruction is *reported*
    # as `ambiguous-reconstructed`, and collapsing that into `degraded` would
    # throw away the distinction between "the decomposition is not unique" and
    # "the join contradicted itself".
    confidence = spine["join_confidence"]
    if any(c.get("ok") is False for c in after):
        confidence = "degraded"

    sources = {}
    for name in ("ledger.jsonl", "turns.json", "surprises.jsonl",
                 "cost_curve.json", "run.json", "RUN_STATE.json",
                 "desk_log.json", "theorize.json"):
        path = os.path.join(run_dir, name)
        present = os.path.exists(path)
        sources[name] = {"present": present,
                         "sha256": _sha256_file(path) if present else None}

    return {
        "schema": "theoria-arm/turn_series v1",
        "run_id": run_id,
        "game_id": summary.get("game_id"),
        "slug": os.path.basename(os.path.normpath(run_dir)),
        "join": {
            "key": "theorize-invocation segmentation (label 'round1' restarts "
                   "inside every theorize.run()) allocated to turns in order; "
                   "cross-checked by step_idx == actions_before + resets + "
                   "actions_failed_so_far",
            "spine": spine["spine"],
            "join_confidence": confidence,
            "surprise_join": "wall-clock containment in the turn's window; "
                             "a surprise's own step_idx is a frame ordinal and "
                             "cannot address a turn",
            "surprises_within_1s_of_a_turn_boundary": ambiguous_surprises,
            "billed_calls_outside_their_own_turn_window": stray_calls,
            "checks": checks,
        },
        "totals": {
            "turns": len(rows),
            "billed_turns": sum(1 for r in rows if r["model_calls"]),
            "model_calls": len(calls),
            "usd": round(total_usd, 9),
            "surprises": sum(joined.values()),
            "actions": sum(r["actions_taken"] for r in rows),
        },
        "reconciliation": recon,
        "provenance": {"run_dir": os.path.basename(os.path.normpath(run_dir)),
                       "sources": sources},
        "rows": rows,
    }


def frontload_input(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce a turn series to the axis `frontload_index` reads.

    Two series, deliberately, because they are not the same claim.

    `turn_costs` is every turn, zero-cost ones included: a turn whose theorize
    the evidence gate skipped is a real decision that cost nothing, and it is
    the *point* of the gate. `turn_costs_billed_only` drops them, which is what
    `battery.model.Run.turn_costs()` does by construction -- it buckets billed
    calls by `turn`, so a turn with no call cannot appear in it.

    That difference is a finding about the metric's input, not a preference:
    E2 is registered on a `Run`, and a `Run` assembled from the ledger cannot
    see the free turns. Both numbers are emitted so the gap is visible.
    """
    rows = doc["rows"]
    every = [r["usd"] for r in rows]
    billed = [r["usd"] for r in rows if r["model_calls"]]
    return {
        "run_id": doc.get("run_id"),
        "slug": doc.get("slug"),
        "frontload_k": FRONTLOAD_K,
        "min_turns_for_shape": MIN_TURNS_FOR_SHAPE,
        "turn_costs": [round(v, 9) for v in every],
        "turn_costs_billed_only": [round(v, 9) for v in billed],
        "usd_total": round(sum(every), 9),
        "billed_calls": doc["totals"]["model_calls"],
        "all_turns": _frontload(every),
        "billed_turns_only": _frontload(billed),
    }


def _cost_through(costs: List[float], mark: float) -> float:
    """`battery/metrics/economy.py:_cost_through`, mirrored.

    Whole turns up to `floor(mark)` plus the matching fraction of the turn the
    mark lands inside. Duplicated rather than imported so this arm can emit and
    check its own figure without depending on the battery being importable;
    `tests/test_turn_series.py` pins the two against each other.
    """
    whole = int(mark)
    head = sum(costs[:whole])
    remainder = mark - whole
    if remainder > 0 and whole < len(costs):
        head += costs[whole] * remainder
    return head


def _frontload(costs: List[float]) -> Dict[str, Any]:
    total = sum(costs)
    out: Dict[str, Any] = {"turns": len(costs), "usd_total": round(total, 9)}
    if total <= 0:
        out["status"] = "insufficient-data"
        out["reason"] = "total cost is zero"
        out["frontload_index_25"] = None
        return out
    head = _cost_through(costs, len(costs) * FRONTLOAD_K)
    out["head_turns"] = round(len(costs) * FRONTLOAD_K, 9)
    out["head_usd"] = round(head, 9)
    out["frontload_index_25"] = round(head / total, 9)
    if len(costs) < MIN_TURNS_FOR_SHAPE:
        out["status"] = "insufficient-data"
        out["reason"] = ("fewer than %d turns; a short run is trivially "
                         "front-loaded. The ratio is reported anyway because "
                         "suppressing it hides the run's shape, but "
                         "battery/metrics/economy.py will refuse it and that "
                         "refusal is the operative reading."
                         % MIN_TURNS_FOR_SHAPE)
    else:
        out["status"] = "ok"
    return out


def write_turn_series(run_dir: str, *,
                      records: Optional[List[Dict[str, Any]]] = None
                      ) -> Dict[str, Any]:
    """`turn_series()` plus its metric input, on disk, byte-stably."""
    doc = turn_series(run_dir, records=records)
    doc["frontload_input"] = frontload_input(doc)
    with open(os.path.join(run_dir, "turn_series.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    return doc


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

    # `utc` is one of CLAUDE.md's four required manifest fields and no earlier
    # version of this file wrote it. It is the run's own start time off the
    # ledger, not the moment this manifest is generated -- those differ by
    # however long the run took, and it is the run that is being dated.
    start = next((r for r in mine if r.get("event") == "run_start"), {})

    # `git rev-parse HEAD` answers "where is HEAD *now*", which is where it was
    # when this manifest was written, not necessarily where it was when the run
    # ran. For a run archived immediately those coincide; for one archived
    # after a fix was committed they do not, and four of this arm's manifests
    # carry a commit their own run never ran against (S8). The recorded
    # `arm_version` settles it independently, so it is checked here rather than
    # left for an audit to find.
    head = git("rev-parse", "HEAD")
    checked = _base_commit_check(start.get("arm_version") or {}, head)

    manifest = {
        "prompt_id": prompt_id,
        "slug": slug,
        "run_id": run_id,
        "game_id": summary.get("game_id"),
        "arm": "theoria",
        "utc": start.get("ts"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": head,
        "base_commit_check": checked,
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
    # The turn-indexed join. `cost_curve.json` is indexed by call, `turns.json`
    # by turn and `surprises.jsonl` by ARC command; figure 2 needs all three on
    # one axis and this is where they meet.
    series = write_turn_series(run_dir, records=mine)
    manifest["turn_series"] = {
        "join_confidence": series["join"]["join_confidence"],
        "totals": series["totals"],
        "reconciliation": series["reconciliation"],
        "frontload_input": series["frontload_input"],
    }
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
