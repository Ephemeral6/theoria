#!/usr/bin/env python3
"""Cross-arm cost reconciliation, in `cost x actions`, over the sources fig02 reads.

**What this is for.** The bill-shape plate compares what a run cost against what
it accomplished, across arms whose ledgers were written by different code at
different times. Nothing checked that the four independent derivations of that
one pair agree. This does, per run, and refuses when they do not.

**The unit is `cost x actions` and nothing else.** Two other candidates were
considered and are excluded on the record, because an unexplained exclusion
reads as an oversight:

* **`turns` does not vote.** `battery/INPUT_FORMAT.md:72-76` (gap 5) records that
  no ledger carries a turn index distinct from `step_idx`, and the gap is still
  open upstream. `capability_spectrum.json` *does* publish a run-level `turns`,
  but it publishes two more that disagree with it by construction --
  `metrics.E2/E3.support.turns` counts decisions and `metrics.E4.support.turns`
  counts billed calls (20 vs 24 on one bare_cc run). Three numbers under one name
  cannot arbitrate anything. Carried here as `turns_*` columns, marked
  `does not vote`.
* **`score` does not vote, and this is not the same as "score is unverifiable".**
  `proxy/SCORING.md:40-43` records that all 32 real closed scorecards report
  `score == 0.0` and `levels_completed == 0`. A reconciliation anchored on score
  would therefore agree everywhere while checking nothing -- vacuously green,
  which is worse than absent. The per-run anchor that *does* carry information is
  `total_actions`: `proxy/SCORING.md:60-62` establishes it counts successful
  non-RESET commands, with 32-of-32 exact agreement over the corpus. So per-run
  actions are a real check and are used; per-step is not cross-verifiable between
  arms (one bare_cc model call maps to one action, one theoria desk call spans
  several) and is reported absent rather than approximated.

**The sources.** Every read goes through ``sources.py`` -- gate 7 of
``verify.sh`` enforces that, and it is the reason this file declares nothing of
its own. Four derivations, over three arms:

===========================  ==========================  ==============================
derivation                   arm(s)                      cost, actions
===========================  ==========================  ==============================
``pilot_rollup``             bare_cc                     ``cost_usd``, ``actions_ok``
``pilot_ledger`` (+shards)   bare_cc                     sum ``model_call.total_cost_usd``,
                                                         count non-failed ``env_step``
``theoria_run`` MANIFEST     theoria                     ``cost.cli_reported_usd``,
                                                         ``reconciliation.successful_actions``
``capability_spectrum``      bare_cc, schema_repro,      ``metrics.E5.support.total_usd``,
                             theoria_a0/a0_spike/a2      ``metrics.E5.support.actions``
===========================  ==========================  ==============================

**A single source is not a pass.** Runs covered by one derivation are reported
``UNCORROBORATED`` and counted separately from ``AGREE``. The live ``theoria``
arm is in that state for every run it has: ``capability_spectrum``'s
``provenance.arms`` lists ``theoria_a0``, ``theoria_a0_spike`` and ``theoria_a2``
-- the offline worlds -- and not the arm that played ARC. So the arm whose cost
the plate most wants to compare is the one arm whose cost nothing corroborates.
That is the finding, not a caveat on it.

**The ablation arm is absent and cannot be added by declaring it.** It writes
``arm: "theoria"`` (``ablation-arm/ablcore/ledger_abl.py:47``) because
``proxy.ledger.ARMS`` has no name for it (D-AB-004), so folding it in would
silently merge two arms under one label. It also spends nothing by construction
(``ledger_abl.py:9``), so its ``cost x actions`` is ``0 / n`` and would divide
into every ratio as zero. Reported as a named absence.

Usage::

    python reconcile_cost.py            # table + csv/reconcile_cost.csv
    python reconcile_cost.py --json     # machine form
    python reconcile_cost.py --selftest # the negative control, on doctored data

Exit status is 1 when any run DISAGREES; UNCORROBORATED alone does not fail the
gate, because it is the honest state of the tree and not a regression.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import sys
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sources  # noqa: E402

#: Relative tolerance on dollars. The derivations are different arithmetic over
#: the same records, not copies, so exact equality is the wrong demand: a
#: roll-up sums floats in write order and the ledger sum in read order.
#: fig02's own rollup-vs-ledger cross-check (`fig02_bill_shape.py:849-865`)
#: measures the worst real disagreement at 4.4e-16, so 1e-9 is four orders of
#: magnitude of slack over the observed noise and still ~six orders below any
#: difference that would mean something.
USD_RTOL = 1e-9
USD_ATOL = 1e-12

#: Actions are counted integers. Off by one is a defect, not noise.
ACTIONS_EXACT = True

#: Published decimal places, per source, where a source rounds before writing.
#: `battery/run_battery.py` writes `metrics.E5.support.total_usd` at six
#: decimals, so 1.0021635 is published as 1.002163. That is a precision dialect,
#: not a disagreement, and it is normalised -- but only for sources listed here,
#: and only to the declared width. A source that starts rounding without saying
#: so still fails.
PUBLISHED_DECIMALS = {"capability_spectrum": 6}

#: Systematic differences that are *real defects*, named so the gate can be
#: green on "nothing unexplained" while still saying this out loud. Each entry
#: is asserted to still be true: a declaration that has stopped being true is
#: removed, not left to hide a regression that came back the other way.
#:
#: RESET_IN_DENOMINATOR -- `capability_spectrum`'s `metrics.E5.support.actions`
#: counts the run's one successful RESET as an action. `proxy/SCORING.md:60-62`
#: establishes the opposite: the scorecard's `total_actions` counts successful
#: *non-RESET* commands, verified 32-of-32 against real cards. Every bare_cc run
#: has exactly one successful RESET, so E5's denominator is exactly one too
#: large on every run, and E5 -- cost per action, the metric the paper's §6.5
#: once cited -- systematically *understates* cost per action. On a run with one
#: successful action it understates it by half.
KNOWN_DEFECTS = {
    "RESET_IN_DENOMINATOR": {
        "source": "capability_spectrum",
        "field": "actions",
        "offset": +1,
        "against": ("pilot_rollup", "pilot_ledger"),
        "why": "counts the successful RESET as an action; proxy/SCORING.md:60-62 "
               "says total_actions counts successful non-RESET commands",
    },
}

CSV_NAME = "reconcile_cost.csv"

CSV_HEADER = (
    "run_id",
    "arm",
    "game_id",
    "verdict",
    "n_derivations",
    "usd_agreed",
    "usd_spread",
    "actions_agreed",
    "actions_spread",
    "usd_per_action",
    "derivations",
    "turns_run_level",       # does not vote -- gap 5
    "turns_decisions",       # does not vote -- E2/E3 support
    "turns_billed_calls",    # does not vote -- E4 support
    "scorecard_total_actions",
    "note",
)


# ---------------------------------------------------------------------------
# the four derivations
# ---------------------------------------------------------------------------
def _claim(source: str, arm: str, run_id: str, game_id: str,
           usd: float | None, actions: int | None, **extra: Any) -> dict:
    return {"source": source, "arm": arm, "run_id": run_id, "game_id": game_id,
            "usd": usd, "actions": actions, **extra}


def from_pilot_rollup(read_json=None) -> list[dict]:
    """`baseline-arms/out/pilot_*.json` -- per-run roll-up written by run_pilot.py."""
    read_json = read_json or sources.read_json
    out = []
    for src in sources.discovered("pilot_rollup"):
        for rec in read_json(src.key):
            out.append(_claim(
                "pilot_rollup", rec.get("arm", "?"), rec["run_id"],
                rec.get("game_id", "?"),
                rec.get("cost_usd"), rec.get("actions_ok"),
                model_calls=rec.get("model_calls"),
                actions_failed=rec.get("actions_failed"),
                outcome=rec.get("outcome"),
            ))
    return out


def from_pilot_ledger(read_jsonl=None) -> list[dict]:
    """The ledger the roll-up summarises, recomputed rather than trusted.

    Two dialects in one stream, discriminated exactly as `fig02._classify` does
    it -- by the presence of ``usage`` -- so a record this cannot place is a
    record fig02 could not place either.
    """
    read_jsonl = read_jsonl or sources.read_jsonl
    keys = ["pilot_ledger"] + [s.key for s in sources.discovered("envelope_ledger")
                               if s.exists()]
    acc: dict[str, dict] = {}
    for key in keys:
        for rec in read_jsonl(key):
            run_id = rec.get("run_id")
            if not run_id:
                continue
            slot = acc.setdefault(run_id, {
                "usd": 0.0, "actions": 0, "arm": None, "game_id": None,
                "model_calls": 0, "actions_failed": 0, "resets": 0,
                "saw_cost": False,
            })
            if "usage" in rec:
                cost = rec.get("total_cost_usd")
                if cost is not None:
                    slot["usd"] += float(cost)
                    slot["saw_cost"] = True
                slot["model_calls"] += 1
                slot["game_id"] = slot["game_id"] or rec.get("game_id")
            elif "action" in rec:
                # `failed` is absent on the majority of rows and absent means
                # "did not fail" -- the same reading fig02's `_truthy` takes.
                if rec.get("failed"):
                    slot["actions_failed"] += 1
                elif _is_reset(rec):
                    # Not an action. `proxy/SCORING.md:60-62` establishes that
                    # the scorecard's `total_actions` counts successful
                    # *non-RESET* commands, with 32-of-32 exact agreement over
                    # the real-card corpus. Counting the RESET here would put
                    # this derivation one ahead of the roll-up on every single
                    # run -- which is exactly the state `capability_spectrum`
                    # is in; see RESET_OFF_BY_ONE below.
                    slot["resets"] += 1
                else:
                    slot["actions"] += 1
                slot["arm"] = slot["arm"] or rec.get("arm")
                slot["game_id"] = slot["game_id"] or rec.get("game_id")
    out = []
    for run_id, slot in acc.items():
        if not slot["saw_cost"]:
            # A run with env_steps and no model_call rows cannot state a cost.
            # Emitting 0.0 here would manufacture a disagreement out of silence.
            continue
        out.append(_claim("pilot_ledger", slot["arm"] or "?", run_id,
                          slot["game_id"] or "?", slot["usd"], slot["actions"],
                          model_calls=slot["model_calls"],
                          actions_failed=slot["actions_failed"],
                          resets=slot["resets"]))
    return out


def _is_reset(rec: dict) -> bool:
    """A RESET row, whatever shape the writer used for `action`.

    In `baseline-arms/ledger.jsonl` the field is the bare string ``"RESET"`` on
    24 rows and ``None`` on the other 262 -- the gameplay rows do not name their
    action at all. Other writers use ``{"name": "RESET", ...}``. Both are read,
    because guessing wrong here is worth exactly one action per run and that is
    the size of the discrepancy this file exists to report.
    """
    action = rec.get("action")
    name = action if isinstance(action, str) else (
        action.get("name") if isinstance(action, dict) else None)
    return isinstance(name, str) and name.upper().startswith("RESET")


def from_theoria_manifest(read_json=None) -> list[dict]:
    """`theoria-arm/runs/*/MANIFEST.json` -- the live arm's own reconciliation."""
    read_json = read_json or sources.read_json
    out = []
    for src in sources.discovered("theoria_run"):
        if not src.key.endswith("MANIFEST.json"):
            continue
        man = read_json(src.key)
        cost = man.get("cost") or {}
        rec = man.get("reconciliation") or {}
        out.append(_claim(
            "theoria_manifest", man.get("arm", "?"),
            man.get("run_id") or man.get("slug", "?"),
            man.get("game_id", "?"),
            cost.get("cli_reported_usd"), rec.get("successful_actions"),
            model_calls=cost.get("model_calls"),
            env_steps=rec.get("env_steps"),
            scorecard_total_actions=rec.get("scorecard_total_actions"),
            slug=man.get("slug"),
            outcome=man.get("outcome"),
        ))
    return out


def from_capability_spectrum(read_json=None) -> list[dict]:
    """`battery/artifacts/capability_spectrum.json` -- E5's own support pair."""
    read_json = read_json or sources.read_json
    spectrum = read_json("capability_spectrum")
    out = []
    for run_id, run in (spectrum.get("runs") or {}).items():
        e5 = (run.get("metrics") or {}).get("E5") or {}
        support = e5.get("support") or {}
        if e5.get("status") != "ok":
            continue
        out.append(_claim(
            "capability_spectrum", run.get("arm", "?"), run_id,
            run.get("game_id", "?"),
            support.get("total_usd"), support.get("actions"),
            model_calls=run.get("model_calls"),
            turns_run_level=run.get("turns"),
            turns_decisions=((run.get("metrics") or {}).get("E2") or {})
                .get("support", {}).get("turns"),
            turns_billed_calls=((run.get("metrics") or {}).get("E4") or {})
                .get("support", {}).get("turns"),
        ))
    return out


DERIVATIONS = (from_pilot_rollup, from_pilot_ledger,
               from_theoria_manifest, from_capability_spectrum)


# ---------------------------------------------------------------------------
# the vote
# ---------------------------------------------------------------------------
def _close(a: float, b: float, decimals: int | None = None) -> bool:
    if decimals is not None:
        # One source published fewer digits than the other holds. Compare at the
        # coarser width -- half a unit in the last published place.
        return abs(a - b) <= 0.5 * 10 ** (-decimals) + USD_ATOL
    return abs(a - b) <= max(USD_ATOL, USD_RTOL * max(abs(a), abs(b)))


def _usd_agree(group: list[dict]) -> bool:
    """Pairwise, at the coarser of the two sources' published precisions."""
    stated = [(c["source"], c["usd"]) for c in group if c["usd"] is not None]
    for i, (src_a, a) in enumerate(stated):
        for src_b, b in stated[i + 1:]:
            widths = [PUBLISHED_DECIMALS[s] for s in (src_a, src_b)
                      if s in PUBLISHED_DECIMALS]
            if not _close(a, b, min(widths) if widths else None):
                return False
    return True


def _actions_agree(group: list[dict]) -> tuple[bool, list[str]]:
    """Exact, except where a declared defect explains the difference exactly.

    Returns (agree_after_declared_defects, defect_ids_that_applied). A defect
    only excuses a difference it predicts *exactly*; an off-by-two where the
    declaration says off-by-one is still a disagreement.
    """
    stated = {c["source"]: c["actions"] for c in group if c["actions"] is not None}
    if len(set(stated.values())) <= 1:
        return True, []
    applied: list[str] = []
    adjusted = dict(stated)
    for defect_id, spec in KNOWN_DEFECTS.items():
        src = spec["source"]
        if spec["field"] != "actions" or src not in adjusted:
            continue
        if not any(other in adjusted for other in spec["against"]):
            continue
        candidate = dict(adjusted)
        candidate[src] = candidate[src] - spec["offset"]
        if len(set(candidate.values())) < len(set(adjusted.values())):
            adjusted = candidate
            applied.append(defect_id)
    return len(set(adjusted.values())) <= 1, applied


def reconcile(claims: list[dict]) -> dict:
    """Group by run_id, compare every pair of derivations, return the verdict set."""
    by_run: dict[str, list[dict]] = {}
    for c in claims:
        by_run.setdefault(c["run_id"], []).append(c)

    rows, disagreements = [], []
    for run_id in sorted(by_run):
        group = by_run[run_id]
        usd = [c["usd"] for c in group if c["usd"] is not None]
        acts = [c["actions"] for c in group if c["actions"] is not None]

        usd_ok = _usd_agree(group) if usd else False
        acts_ok, defects = _actions_agree(group) if acts else (False, [])

        why = []
        if not usd:
            verdict, why = "NO-COST", ["no derivation states a cost"]
        elif not acts:
            verdict, why = "NO-ACTIONS", ["no derivation states an action count"]
        elif not usd_ok or not acts_ok:
            verdict = "DISAGREE"
            if not usd_ok:
                why.append("usd: " + ", ".join(
                    f"{c['source']}={c['usd']!r}" for c in group if c["usd"] is not None))
            if not acts_ok:
                why.append("actions: " + ", ".join(
                    f"{c['source']}={c['actions']!r}" for c in group
                    if c["actions"] is not None))
        elif len(group) == 1:
            verdict = "UNCORROBORATED"
            why = [f"only {group[0]['source']} covers this run"]
        elif defects:
            verdict = "AGREE(known-defect)"
            why = [f"{d}: {KNOWN_DEFECTS[d]['why']}" for d in defects]
        else:
            verdict = "AGREE"

        merged: dict[str, Any] = {}
        for c in group:
            for k, v in c.items():
                if k.startswith("turns_") or k == "scorecard_total_actions":
                    merged.setdefault(k, v) if v is not None else None
                    if v is not None:
                        merged[k] = v

        usd_val = usd[0] if usd else None
        act_val = acts[0] if acts else None
        row = {
            "run_id": run_id,
            "arm": group[0]["arm"],
            "game_id": group[0]["game_id"],
            "verdict": verdict,
            "n_derivations": len(group),
            "usd_agreed": usd_val,
            "usd_spread": (max(usd) - min(usd)) if len(usd) > 1 else 0.0,
            "actions_agreed": act_val,
            "actions_spread": (max(acts) - min(acts)) if len(acts) > 1 else 0,
            "usd_per_action": (usd_val / act_val)
            if (usd_val is not None and act_val) else None,
            "derivations": "|".join(sorted(c["source"] for c in group)),
            "turns_run_level": merged.get("turns_run_level"),
            "turns_decisions": merged.get("turns_decisions"),
            "turns_billed_calls": merged.get("turns_billed_calls"),
            "scorecard_total_actions": merged.get("scorecard_total_actions"),
            "note": "; ".join(why),
        }
        rows.append(row)
        if verdict == "DISAGREE":
            disagreements.append(row)

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1

    arms_seen = sorted({r["arm"] for r in rows})
    corroborated_arms = sorted({r["arm"] for r in rows
                                if r["verdict"].startswith("AGREE")})
    defect_hits: dict[str, int] = {}
    for r in rows:
        for defect_id in KNOWN_DEFECTS:
            if defect_id in r["note"]:
                defect_hits[defect_id] = defect_hits.get(defect_id, 0) + 1
    stale = [d for d in KNOWN_DEFECTS if not defect_hits.get(d)]
    return {
        "rows": rows,
        "tally": tally,
        "disagreements": disagreements,
        "arms": arms_seen,
        "arms_with_a_corroborated_run": corroborated_arms,
        "arms_absent": ["ablation-arm (writes arm=\"theoria\"; D-AB-004)",
                        "schema_repro live (no ledger; battery/DECISIONS.md D-B-004)"],
        "unit": "cost x actions",
        "excluded_from_the_vote": {
            "turns": "battery/INPUT_FORMAT.md:72-76 gap 5, still open upstream; "
                     "capability_spectrum publishes three different `turns`",
            "score": "proxy/SCORING.md:40-43 -- score == 0.0 on all 32 real cards, "
                     "so a score anchor is vacuously green",
            "per_step": "one bare_cc model call is one action; one theoria desk "
                        "call spans several. Not comparable, reported absent",
        },
        "known_defects": {d: {"runs_affected": defect_hits.get(d, 0),
                              **KNOWN_DEFECTS[d]} for d in KNOWN_DEFECTS},
        "stale_defect_declarations": stale,
        "green": not disagreements and not stale,
    }


# ---------------------------------------------------------------------------
def collect(read_json=None, read_jsonl=None) -> list[dict]:
    return (from_pilot_rollup(read_json)
            + from_pilot_ledger(read_jsonl)
            + from_theoria_manifest(read_json)
            + from_capability_spectrum(read_json))


def write_csv(rows: list[dict], target: str | None = None) -> str:
    # Not `csv/`. That directory is the figure build's own output and gate 6
    # diffs it against a fresh `build_all.py` run, so a file there that
    # `build_all.py` does not produce reads as a stale committed figure. This is
    # an audit surface for a gate, not a plate's data, and it lives accordingly.
    target = target or os.path.join(HERE, "audit", CSV_NAME)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_HEADER),
                                lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["arm"], r["run_id"])):
            writer.writerow({k: ("" if row.get(k) is None else row.get(k))
                             for k in CSV_HEADER})
    return target


# ---------------------------------------------------------------------------
# the negative control
# ---------------------------------------------------------------------------
def selftest() -> tuple[bool, list[str]]:
    """Doctor one record in one source and require the verdict to flip.

    A reconciliation that has never been seen to refuse is a reconciliation
    nobody has tested. Two plants, because the two quantities fail differently:
    a cost that drifts and an action count that is off by one.
    """
    notes: list[str] = []
    base = reconcile(collect())
    if not base["green"]:
        return False, ["the tree is already red; the control cannot be read "
                       "against it. Fix the real disagreement first."]

    corroborated = [r for r in base["rows"] if r["verdict"].startswith("AGREE")]
    if not corroborated:
        return False, ["no run is covered by two derivations, so nothing here "
                       "could ever disagree. The control is the finding: this "
                       "reconciliation is not currently checking anything."]

    # The plants below doctor `pilot_rollup` records, so the target has to be a
    # run `pilot_rollup` actually covers. Picking any corroborated run is not
    # good enough: the first one is corroborated by pilot_ledger and
    # capability_spectrum, and doctoring a source that does not mention it
    # changes nothing -- which is how this control failed the first time it was
    # run, and the reason it is worth having.
    reachable = [r for r in corroborated if "pilot_rollup" in r["derivations"]]
    if not reachable:
        return False, ["no corroborated run is covered by pilot_rollup, so the "
                       "plants below cannot reach one. Re-target the control "
                       "rather than deleting it."]
    target = reachable[0]["run_id"]
    real = sources.read_json

    def doctored_cost(key):
        data = copy.deepcopy(real(key))
        if isinstance(data, list):
            for rec in data:
                if rec.get("run_id") == target and "cost_usd" in rec:
                    rec["cost_usd"] = float(rec["cost_usd"]) * 1.05 + 1e-6
        return data

    def doctored_actions(key):
        data = copy.deepcopy(real(key))
        if isinstance(data, list):
            for rec in data:
                if rec.get("run_id") == target and "actions_ok" in rec:
                    rec["actions_ok"] = int(rec["actions_ok"]) + 1
        return data

    for label, patch in (("cost", doctored_cost), ("actions", doctored_actions)):
        got = reconcile(collect(read_json=patch))
        row = next((r for r in got["rows"] if r["run_id"] == target), None)
        if got["green"] or row is None or row["verdict"] != "DISAGREE":
            return False, [f"planted a {label} mismatch on {target} and the "
                           f"reconciliation stayed green (verdict="
                           f"{row['verdict'] if row else 'missing'})"]
        notes.append(f"{label} mismatch on {target}: refused, as required")
    return True, notes


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--selftest", action="store_true",
                        help="plant a mismatch and require a refusal")
    parser.add_argument("--csv", default=None)
    args = parser.parse_args(argv)

    if args.selftest:
        ok, notes = selftest()
        for note in notes:
            print(("ok   " if ok else "FAIL ") + note)
        return 0 if ok else 1

    result = reconcile(collect())
    target = write_csv(result["rows"], args.csv)

    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                         indent=2, sort_keys=True, ensure_ascii=False))
        return 0 if result["green"] else 1

    print(f"cross-arm reconciliation, unit = {result['unit']}")
    print(f"  {len(result['rows'])} runs over arms: {', '.join(result['arms'])}")
    for verdict in ("AGREE", "AGREE(known-defect)", "UNCORROBORATED",
                    "DISAGREE", "NO-COST", "NO-ACTIONS"):
        if verdict in result["tally"]:
            print(f"    {verdict:<16} {result['tally'][verdict]}")
    print(f"  arms with at least one corroborated run: "
          f"{', '.join(result['arms_with_a_corroborated_run']) or 'none'}")
    for defect_id, info in result["known_defects"].items():
        print(f"  KNOWN DEFECT {defect_id}: {info['runs_affected']} run(s) -- "
              f"{info['source']}.{info['field']} {info['offset']:+d}; {info['why']}")
    for defect_id in result["stale_defect_declarations"]:
        print(f"  STALE DECLARATION {defect_id}: declared but never observed. "
              f"Remove it -- it is currently excusing nothing and would excuse "
              f"a real regression if one appeared.")
    for row in result["disagreements"]:
        print(f"  DISAGREE {row['run_id']}: {row['note']}")
    print(f"  wrote {os.path.relpath(target, os.path.dirname(HERE))}")
    return 0 if result["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
