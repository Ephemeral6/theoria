"""A33 -- recount the sentence registration #14 makes about this arm.

`monitor/spec.py` registration #14 says, of this territory:

    46 条基线臂 run（裸 CC 三档模型）最高分 0、通关 0
    ("46 baseline-arm runs (bare CC, three model tiers), max score 0,
     zero levels completed")

Three of those clauses do not survive contact with `runs/`, and all three err
in the same direction -- they make the evidence sound stronger than it is:

  * **46 is not a count of runs.** `runs/MANIFEST.json` counts 46 *entries*, of
    which 43 are `kind == "run"`. The other three are one excluded record, one
    fetch and one ledger migration. None of them played a game.
  * **"max score 0" read a field that does not exist -- but the claim is
    rescuable, on a smaller denominator.** No `run.json` in this arm carries a
    `score` key, and the ARC gameplay response (`RESET`, `ACTIONn`) has no
    `score` field at all -- only `state`, `levels_completed` and `win_levels`
    (A28, `harness.audit_zero`). So as written, registration #14 was reading
    `levels_completed` and calling it a score. The authoritative score lives on
    the **scorecard body**, and this territory archived enough of those to
    rebuild a column: `harness.score_column` recovers a real score for **20 of
    the 43** archived runs, offline, and every one of them is `0.0`. The other
    23 have none and never will (15 whose card now 404s permanently -- D-015 --
    and 8 with no card recorded at all). "Max score 0" is therefore true of 20
    runs and undefined for 23; it was never true of 46.
  * **"zero levels completed" is 36 runs' worth, not 43's.** Seven runs have no
    `summary` at all and therefore no completion count; and of the 36 that do,
    14 are the manifest's own `dead_runs` -- `api_unusable`, `model_error`,
    `no_reset_window`. A dead run is not "played and lost". Counting a network
    failure as evidence about capability is counting the network.

And a fourth thing, which registration #14 does not say and which changes what
the arm's zero is evidence *of*: **no bare_cc run was given a budget that
reached its game's own level-1 baseline.** 36 of 36 budgeted runs are below it;
for g50t-5849a774 the API's `level_baseline_actions[0]` is 78 and the largest
budget ever configured in this arm is 30. A control that cannot succeed is
barely a control -- see
`monitor/audit/DRIFT-20260730T0428Z-two-published-certifications-that-cannot-fail.md`.

Three things that clause must NOT be inflated into
--------------------------------------------------
Each of these is a way the correction could repeat the original error in the
opposite direction, so each is printed rather than assumed away.

1. **`level_baseline_actions` is not a lower bound.** It is what a reference
   solver took, and `theoria-arm/inner/scoreboard.py` says so in terms: "It is
   NOT a lower bound and beating it is the entire point of the exercise, so
   nothing here says a level is unreachable." So "a 30-action budget *could
   not* clear level 1" is an inference, not a theorem. What the record
   supports is the weaker, exact sentence: no run was budgeted to the point
   where clearing level 1 would have been a reasonable expectation. This
   module labels the bucket `budget_below_level_1_baseline`, never
   "impossible".

2. **43 is the number of *archived* runs, not the number of runs.** 57 distinct
   `run_id`s appear in archived scorecard bodies; 43 have a `runs/*/run.json`.
   The m4-pilot-era runs of 2026-07-27 survive only in the ledger and probe
   log. So "43 runs" is exact only with the word *archived* in it -- the same
   defect as "46", one denominator down.

3. **Some runs did pass their level-1 baseline -- they just left no
   `run.json`.** On ar25-0c556536 a card reached 67 actions against a baseline
   of 32, and on tn36-ef4dde99 one reached exactly 32; on g50t the best is 73
   against 78, close and still short. The reason is *not* that cards accumulate
   across resets -- every one of those observations records `resets: 0`. It is
   that 16 m4-pilot-era runs (2026-07-27) spent more than 30 actions and none
   of them was ever archived, so they are invisible at the budget layer and
   visible at the card layer. "No run was ever allowed to reach the level-1
   baseline" is true of the 43 *archived* budgets and false of the arm. This
   module prints both layers so the corrected wording cannot fudge which it
   means.

What is checked, and what would make it red
-------------------------------------------
`recount()` is pure: it derives every number from `runs/` and returns them,
asserting nothing. `adjudicate()` compares that recount against the numbers the
**published wording** commits to (the `WORDING_*` constants below) and against
two structural invariants:

  * a run registered `outcome == "no_summary"` must still have no `summary` and
    no completion count anywhere in it. A `levels_completed: 0` appearing on
    one of those seven is an absent value backfilled as zero, which is the
    exact error this module exists to prevent -- so it is named, not counted.
  * the budget partition is *computed*, never assumed. A run whose budget meets
    its game's level-1 baseline is reported in its own bucket. If such a run
    ever exists, the "structurally impossible" section must shrink by one; a
    checker that swept it into the same bucket would only be reciting the
    conclusion it was built to test.

    python -m harness.audit_claim_14           # the four sections
    python -m harness.audit_claim_14 --json    # machine-readable
    python -m harness.audit_claim_14 --runs-dir <path>   # recount another tree

No network call, no credential read, nothing outside `baseline-arms/` is
opened except through `harness.audit_zero`, which reads this territory's own
probe logs.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Optional

from harness import audit_zero, score_column

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(HERE, "runs")
MANIFEST = os.path.join(RUNS, "MANIFEST.json")

# --------------------------------------------------------------------------
# What the *published wording* commits to.  These are not floors and not
# guesses: each is a number that appears in the corrected sentence, so if the
# record moves away from one of them the sentence has gone stale and must be
# rewritten.  That is the whole contract -- the wording is recomputable, or it
# is not published.
# --------------------------------------------------------------------------

WORDING_MANIFEST_ENTRIES = 46      # every entry in runs/MANIFEST.json
WORDING_RUNS = 43                  # of which kind == "run"
WORDING_NON_RUN_KINDS = {"excluded": 1, "fetch": 1, "migration": 1}
WORDING_WITH_SUMMARY = 36
WORDING_NO_SUMMARY = 7
WORDING_DEAD_RUNS = 14
WORDING_RUNS_PERSISTING_SCORE = 0  # not "about zero" -- exactly none, ever
WORDING_MAX_ACTIONS_OK = 30
WORDING_TOTAL_ACTIONS_OK = 573
WORDING_BUDGETS = {"20": 14, "30": 22, "absent": 7}

# The score column `harness.score_column` rebuilds from archived scorecard
# bodies.  `recorded` is the only bucket that carries a number; the rest are
# the size of the hole and are published as such.  Absent keys mean zero -- a
# `conflicting` or `never_probed` row appearing is a real change and the
# equality below will say so.
WORDING_SCORE_COLUMN = {"absent": 8, "recorded": 20, "unobtainable": 15}
WORDING_MAX_RECORDED_SCORE = 0.0

# The outcome histogram, pinned in full rather than by its total.  Pinning only
# `dead_runs == 14` let one `model_error` be relabelled `api_unusable` with the
# total unmoved and the gate green, while the published sentence -- which names
# all three counts -- had gone false.  A total is not a distribution.
WORDING_BY_OUTCOME = {"api_unusable": 8, "budget_exhausted": 20, "gave_up": 2,
                      "model_error": 5, "no_reset_window": 1, "no_summary": 7}

# The 22 that actually played and lost.  Pinned for the same reason: relabelling
# one `budget_exhausted` to any value outside both lists left every other count
# intact and silently dropped this one to 21.
WORDING_PLAYED_AND_LOST = 22

# The API's own level-1 baselines, and the count of runs budgeted below them.
# `audit_zero.baselines()` is last-observation-wins over an append-only log, so
# one appended line can move a baseline; without these pinned it would move in
# silence and take the published "36/36" with it.
WORDING_LEVEL_1_BASELINES = {"ar25-0c556536": 32, "g50t-5849a774": 78,
                             "sk48-d8078629": 61, "tn36-ef4dde99": 32}
WORDING_BUDGET_BELOW_BASELINE = 36

# 57 distinct run_ids appear in archived scorecard bodies against 43 archived
# run dirs.  Carried so that "43 runs" can never be published without the word
# *archived* -- that omission is exactly how "46" got into the register.
WORDING_DISTINCT_SCORECARD_RUN_IDS = 57

# The 14 dead runs are these outcomes.  Named rather than derived from
# `dead_runs` so that a manifest quietly reclassifying an outcome is visible
# here instead of being absorbed into the same total.
DEAD_OUTCOMES = ("api_unusable", "model_error", "no_reset_window")

# A run that played and lost -- the only 22 that are evidence about capability
# at all.  Derived below; listed here so the complement is explicit.
PLAYED_OUTCOMES = ("budget_exhausted", "gave_up")

# The seven runs reconstructed from the ledger, which have no summary and
# therefore no completion count.  Frozen as a roster because the invariant this
# module defends is about *these* records: their completion count is absent,
# and absent is not zero.  A run rerun later gets a fresh uuid suffix, so the
# roster does not go stale on legitimate work.
NO_SUMMARY_ROSTER = (
    "bare_cc-ar25-claude-haiku-4-5-20251001-55ea5593",
    "bare_cc-g50t-claude-haiku-4-5-20251001-069d86f8",
    "bare_cc-sk48-claude-haiku-4-5-20251001-36c386d1",
    "bare_cc-sk48-claude-haiku-4-5-20251001-4f5d7ddb",
    "bare_cc-sk48-claude-haiku-4-5-20251001-b1ae92a0",
    "bare_cc-sk48-claude-haiku-4-5-20251001-b3e5c758",
    "bare_cc-tn36-claude-haiku-4-5-20251001-1b9b5309",
)


# --------------------------------------------------------------------------
# The recount.  Pure: derives, asserts nothing.
# --------------------------------------------------------------------------

def _load(path: str) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_runs(runs_dir: str = RUNS) -> List[Dict[str, Any]]:
    """Every `runs/*/run.json`, as recorded.  Not filtered to `kind == "run"`
    -- section one is precisely about the entries that are not runs."""
    out: List[Dict[str, Any]] = []
    for p in sorted(glob.glob(os.path.join(runs_dir, "*", "run.json"))):
        doc = _load(p)
        doc["_path"] = os.path.relpath(p, os.path.dirname(runs_dir)).replace(os.sep, "/")
        out.append(doc)
    return out


def _completion_count(doc: Dict[str, Any]) -> Any:
    """Whatever this run says about levels completed, from either place it can
    be written, or the sentinel `"absent"`.

    `"absent"` is a distinct value on purpose.  `dict.get(k, 0)` here would
    turn every one of the seven ledger-reconstructed runs into a zero and make
    the sentence this module is correcting true by construction.
    """
    for holder in (doc.get("summary"), doc.get("spend")):
        if isinstance(holder, dict) and "levels_completed" in holder:
            return holder["levels_completed"]
    return "absent"


def _unit_price(doc: Dict[str, Any]) -> Optional[float]:
    s = doc.get("summary") or {}
    spend = doc.get("spend") or {}
    cost = s.get("cost_usd", spend.get("cost_usd"))
    ok = s.get("actions_ok", spend.get("actions_ok"))
    if not isinstance(cost, (int, float)) or not isinstance(ok, int) or ok <= 0:
        return None
    return cost / ok


_OBS_CACHE: List[Dict[str, Any]] = []


def observations() -> List[Dict[str, Any]]:
    """`audit_zero.scorecard_observations()`, read once per process.

    It parses `probe_log.jsonl` and the `out/shards/` copies -- ~7 MB of JSON
    lines -- and the recount needs it twice (once for the level-1 baselines,
    once for card-level reach).  Reading it twice per call made the suite and
    `verify.py` pay for the same scan repeatedly.  The logs are append-only and
    nothing here writes to them, so caching for the life of the process cannot
    make the answer stale within a run.
    """
    if not _OBS_CACHE:
        _OBS_CACHE.extend(audit_zero.scorecard_observations())
    return _OBS_CACHE


def recount(runs_dir: str = RUNS,
            manifest_path: Optional[str] = None,
            level_1_baselines: Optional[Dict[str, int]] = None,
            obs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """The four sections, derived from the record.  No expectations applied.

    `level_1_baselines` and `obs` are injectable so that a test can put a
    known baseline in front of a synthetic runs tree -- the partition in
    section four is the thing under test, and it must be exercised against a
    budget that *does* clear a baseline, which no real run does.
    """
    manifest_path = manifest_path or os.path.join(runs_dir, "MANIFEST.json")
    docs = load_runs(runs_dir)

    manifest: Dict[str, Any] = {}
    if os.path.exists(manifest_path):
        manifest = _load(manifest_path)

    if obs is None:
        obs = observations()
    if level_1_baselines is None:
        level_1_baselines = {g: lb[0] for g, lb in audit_zero.baselines(obs).items() if lb}

    # ---- section 1: 46 is entries, 43 is runs ---------------------------
    by_kind: Dict[str, int] = {}
    for d in docs:
        by_kind[d.get("kind") or "absent"] = by_kind.get(d.get("kind") or "absent", 0) + 1
    runs = [d for d in docs if d.get("kind") == "run"]
    non_runs = [{"id": d.get("id"), "kind": d.get("kind"), "path": d["_path"]}
                for d in docs if d.get("kind") != "run"]

    section_1 = {
        "run_json_files_on_disk": len(docs),
        "by_kind": dict(sorted(by_kind.items())),
        "runs": len(runs),
        "not_runs": sorted(non_runs, key=lambda r: str(r["id"])),
        "manifest_total": (manifest.get("counts") or {}).get("total"),
        "manifest_by_kind": (manifest.get("counts") or {}).get("by_kind"),
        "manifest_agrees_with_disk":
            (manifest.get("counts") or {}).get("by_kind") == dict(sorted(by_kind.items()))
            if manifest else None,
    }

    # ---- section 2: score is absent, not zero ---------------------------
    with_summary = [d for d in runs if isinstance(d.get("summary"), dict)]
    persisting_score = [d["id"] for d in with_summary if "score" in d["summary"]]
    completions: Dict[str, int] = {}
    for d in runs:
        completions[str(_completion_count(d))] = completions.get(str(_completion_count(d)), 0) + 1

    column = score_column.build(obs=obs, runs_dir=runs_dir)
    section_2 = {
        "runs_with_a_summary": len(with_summary),
        "runs_persisting_a_score_field": len(persisting_score),
        "runs_persisting_a_score_field_ids": sorted(persisting_score),
        "completion_counts": dict(sorted(completions.items())),
        "score_field_exists_on_gameplay_response": False,
        "score_column": column["counts"],
        "max_recorded_score": column["max_recorded_score"],
        "distinct_recorded_scores": column["distinct_recorded_scores"],
        "score_absence_reason":
            "A28/harness.audit_zero: the ARC gameplay response (RESET, ACTIONn) "
            "carries state, levels_completed and win_levels and no score field, "
            "so no run.json in this arm records one. The authoritative score is "
            "on the scorecard body; harness.score_column rebuilds it offline "
            "for the runs whose body was archived. For the rest the score is "
            "unobtainable (D-015: a closed card 404s forever) or absent -- and "
            "neither is zero.",
    }

    # ---- section 3: seven have no completion count; 14 never played -----
    no_summary = sorted(d["id"] for d in runs if not isinstance(d.get("summary"), dict))
    by_outcome: Dict[str, int] = {}
    for d in runs:
        by_outcome[d.get("outcome") or "absent"] = by_outcome.get(d.get("outcome") or "absent", 0) + 1
    dead = sorted(d["id"] for d in runs if d.get("outcome") in DEAD_OUTCOMES)
    played = sorted(d["id"] for d in runs if d.get("outcome") in PLAYED_OUTCOMES)

    section_3 = {
        "runs_without_a_summary": len(no_summary),
        "runs_without_a_summary_ids": no_summary,
        "by_outcome": dict(sorted(by_outcome.items())),
        "dead_runs": len(dead),
        "dead_run_outcomes": list(DEAD_OUTCOMES),
        "dead_run_ids": dead,
        "manifest_dead_runs": (manifest.get("counts") or {}).get("dead_runs"),
        "runs_that_played_and_lost": len(played),
        "runs_that_played_and_lost_ids": played,
    }

    # ---- section 4: the budget, at both layers --------------------------
    budgets: Dict[str, int] = {}
    below: List[Dict[str, Any]] = []
    at_or_above: List[Dict[str, Any]] = []
    unattributable: List[Dict[str, Any]] = []
    actions_ok: List[int] = []

    for d in runs:
        b = d.get("budget")
        budgets[str(b) if b is not None else "absent"] = \
            budgets.get(str(b) if b is not None else "absent", 0) + 1
        s = d.get("summary") or {}
        if isinstance(s.get("actions_ok"), int):
            actions_ok.append(s["actions_ok"])

        base = level_1_baselines.get(d.get("game_id"))
        row = {"id": d.get("id"), "game_id": d.get("game_id"), "budget": b,
               "level_1_baseline": base}
        if not isinstance(b, int) or base is None:
            # No budget, or a game with no baseline observation. Neither
            # bucket may claim it: "we do not know" is its own answer.
            unattributable.append(row)
        elif b < base:
            below.append(row)
        else:
            at_or_above.append(row)

    # Per-tier unit price, for the priced gap in section four.  Computed, so
    # the quoted dollar figure cannot drift away from the record it cites.
    per_tier: Dict[str, Dict[str, Any]] = {}
    for d in runs:
        price = _unit_price(d)
        if price is None:
            continue
        tier = d.get("model") or "absent"
        per_tier.setdefault(tier, {"prices": [], "runs": 0})
        per_tier[tier]["prices"].append(price)
        per_tier[tier]["runs"] += 1
    # Priced per tier, and reported as a *range*.  A single run's $/action is
    # not the cost of the next run: the opus figure registration #14's
    # follow-up quotes ($0.1147) is the median of five runs whose spread is
    # 1.74x, and two further opus runs bought zero successful actions at all,
    # which a per-run median cannot see.  So the aggregate -- total dollars
    # over total successful actions, across every run including the ones that
    # got nothing -- is carried beside it. That is the number a budget needs.
    tier_cost: Dict[str, float] = {}
    tier_actions: Dict[str, int] = {}
    for d in runs:
        s = d.get("summary") or {}
        spend = d.get("spend") or {}
        cost = s.get("cost_usd", spend.get("cost_usd"))
        ok = s.get("actions_ok", spend.get("actions_ok"))
        if isinstance(cost, (int, float)) and isinstance(ok, int):
            tier = d.get("model") or "absent"
            tier_cost[tier] = tier_cost.get(tier, 0.0) + cost
            tier_actions[tier] = tier_actions.get(tier, 0) + ok
    for tier, t in per_tier.items():
        p = sorted(t.pop("prices"))
        t["usd_per_action_min"] = round(p[0], 6)
        t["usd_per_action_median"] = round(p[len(p) // 2], 6)
        t["usd_per_action_max"] = round(p[-1], 6)
        acts = tier_actions.get(tier, 0)
        t["runs_priced_including_zero_action_runs"] = sum(
            1 for d in runs if (d.get("model") or "absent") == tier
            and isinstance((d.get("summary") or {}).get("cost_usd",
                           (d.get("spend") or {}).get("cost_usd")), (int, float)))
        t["usd_per_action_aggregate"] = round(tier_cost[tier] / acts, 6) if acts else None

    # Layer two: actions a *card* actually accumulated, which crosses resets.
    card_reach: Dict[str, Dict[str, Any]] = {}
    for game, base in sorted(level_1_baselines.items()):
        reach = [o.get("actions") or 0 for o in obs if o.get("game_id") == game]
        card_reach[game] = {
            "level_1_baseline": base,
            "observations": len(reach),
            "best_card_actions": max(reach) if reach else 0,
            "cards_reaching_the_baseline": sum(1 for r in reach if r >= base),
        }

    # The denominator behind the denominator: `runs/` holds the runs somebody
    # archived, not the runs that happened.  Printing both stops "43" becoming
    # the next "46".
    archived_ids = {d.get("id") for d in runs}
    scorecard_ids = {o["run_id"] for o in obs if o.get("run_id")}

    # What one adequately-budgeted run would cost, per (game, tier) CELL.
    # Pooling by tier gave every game in a tier the same price and happily
    # quoted a number for tn36 x opus, where opus bought zero successful
    # actions across two runs costing $1.88.  A cell with no successful actions
    # has no price, and says so.
    cell_cost: Dict[str, Dict[str, Any]] = {}
    for game, base in sorted(level_1_baselines.items()):
        for tier in sorted({d.get("model") or "absent" for d in runs}):
            cells = [d for d in runs if d.get("game_id") == game
                     and (d.get("model") or "absent") == tier]
            cost = 0.0
            acts = 0
            priced = 0
            for d in cells:
                s = d.get("summary") or {}
                spend = d.get("spend") or {}
                c = s.get("cost_usd", spend.get("cost_usd"))
                a = s.get("actions_ok", spend.get("actions_ok"))
                if isinstance(c, (int, float)) and isinstance(a, int):
                    cost += c
                    acts += a
                    priced += 1
            if not priced:
                why = "no priced run of this game at this tier"
                cell_cost["%s x %s" % (game, tier)] = {"level_1_baseline": base, "usd": None,
                                           "runs": 0, "actions_ok": 0,
                                           "usd_per_action": None, "why": why}
            elif acts == 0:
                why = ("%d run(s) costing $%.4f bought 0 successful actions -- "
                       "there is no $/action here, and quoting one would price "
                       "an experiment off a tier that never worked on this game"
                       % (priced, cost))
                cell_cost["%s x %s" % (game, tier)] = {"level_1_baseline": base, "usd": None,
                                           "runs": priced, "actions_ok": 0,
                                           "usd_per_action": None, "why": why}
            else:
                cell_cost["%s x %s" % (game, tier)] = {
                    "level_1_baseline": base, "usd": round(base * cost / acts, 4),
                    "runs": priced, "actions_ok": acts,
                    "usd_per_action": round(cost / acts, 6), "why": None}

    section_4 = {
        "cell_cost_to_reach_baseline": cell_cost,
        "budgets": dict(sorted(budgets.items())),
        "max_actions_ok": max(actions_ok) if actions_ok else 0,
        "total_actions_ok": sum(actions_ok),
        "archived_run_dirs": len(archived_ids),
        "distinct_run_ids_in_scorecard_bodies": len(scorecard_ids),
        "run_ids_with_a_scorecard_but_no_archived_run_json":
            len(scorecard_ids - archived_ids),
        # The union is the arm's real size, and it lands on 80 -- which is the
        # denominator papers/phase1-workshop already uses for bare_cc
        # ("the 67 of 80 bare_cc runs that return a value").  Two counts made
        # from different sources agreeing is worth more than either alone.
        "distinct_run_ids_known": len(archived_ids | scorecard_ids),
        "level_1_baselines": dict(sorted(level_1_baselines.items())),
        "budget_below_level_1_baseline": len(below),
        "budget_below_level_1_baseline_rows": below,
        "budget_at_or_above_level_1_baseline": len(at_or_above),
        "budget_at_or_above_level_1_baseline_rows": at_or_above,
        "budget_unattributable": len(unattributable),
        "budget_unattributable_rows": unattributable,
        "card_level_reach": card_reach,
        "usd_per_action_by_model": dict(sorted(per_tier.items())),
    }

    return {"section_1_46_is_entries_not_runs": section_1,
            "section_2_score_is_absent_not_zero": section_2,
            "section_3_seven_have_no_count_and_fourteen_never_played": section_3,
            "section_4_no_budget_reached_the_level_1_baseline": section_4}


# --------------------------------------------------------------------------
# The adjudication.  Compares the recount to what the wording committed to.
# --------------------------------------------------------------------------

def adjudicate(rc: Dict[str, Any], runs_dir: str = RUNS) -> List[str]:
    problems: List[str] = []
    s1 = rc["section_1_46_is_entries_not_runs"]
    s2 = rc["section_2_score_is_absent_not_zero"]
    s3 = rc["section_3_seven_have_no_count_and_fourteen_never_played"]
    s4 = rc["section_4_no_budget_reached_the_level_1_baseline"]

    def eq(got: Any, want: Any, what: str) -> None:
        if got != want:
            problems.append("%s: recount says %r, the published wording says %r"
                            % (what, got, want))

    eq(s1["run_json_files_on_disk"], WORDING_MANIFEST_ENTRIES, "manifest entries")
    eq(s1["manifest_total"], WORDING_MANIFEST_ENTRIES, "MANIFEST.json counts.total")
    eq(s1["runs"], WORDING_RUNS, "entries with kind == 'run'")
    for kind, n in sorted(WORDING_NON_RUN_KINDS.items()):
        eq(s1["by_kind"].get(kind), n, "entries with kind == %r" % kind)
    if s1["manifest_agrees_with_disk"] is not True:
        problems.append("MANIFEST.json counts.by_kind %r disagrees with the "
                        "%r actually on disk -- the manifest is the thing "
                        "registration #14 was read off, so a disagreement "
                        "here is the bug, not a rounding note"
                        % (s1["manifest_by_kind"], s1["by_kind"]))

    eq(s2["runs_with_a_summary"], WORDING_WITH_SUMMARY, "runs with a summary")
    if s2["runs_persisting_a_score_field"] != WORDING_RUNS_PERSISTING_SCORE:
        problems.append(
            "%d run(s) now persist a `score` field in run.json (%s). That is "
            "not a regression -- it means the arm started recording what it "
            "used not to, and the corrected wording ('no run.json in this arm "
            "carries a score key') is now stale and must be rewritten rather "
            "than left standing"
            % (s2["runs_persisting_a_score_field"],
               ", ".join(s2["runs_persisting_a_score_field_ids"])))
    eq(s2["score_column"], WORDING_SCORE_COLUMN, "the rebuilt score column")
    eq(s2["max_recorded_score"], WORDING_MAX_RECORDED_SCORE,
       "the largest score ever recovered")
    if s2["distinct_recorded_scores"] not in ([], [WORDING_MAX_RECORDED_SCORE]):
        problems.append(
            "the recovered scores are %s -- the wording says every recovered "
            "score is %r, and a second distinct value means the arm did "
            "something the sentence does not describe"
            % (s2["distinct_recorded_scores"], WORDING_MAX_RECORDED_SCORE))
    eq(s2["completion_counts"].get("0"), WORDING_WITH_SUMMARY,
       "runs recording levels_completed == 0")
    eq(s2["completion_counts"].get("absent"), WORDING_NO_SUMMARY,
       "runs whose completion count is absent")

    eq(s3["runs_without_a_summary"], WORDING_NO_SUMMARY, "runs without a summary")
    eq(s3["dead_runs"], WORDING_DEAD_RUNS, "dead runs")
    eq(s3["manifest_dead_runs"], WORDING_DEAD_RUNS, "MANIFEST.json counts.dead_runs")
    eq(s3["by_outcome"], WORDING_BY_OUTCOME, "the outcome histogram")
    eq(s3["runs_that_played_and_lost"], WORDING_PLAYED_AND_LOST,
       "runs that played and lost")
    # 43 = 22 played + 14 dead + 7 with no summary.  Checked as a partition so
    # that a run relabelled into a fourth category is a red gate rather than a
    # count that quietly drops by one.
    covered = (s3["runs_that_played_and_lost"] + s3["dead_runs"]
               + s3["runs_without_a_summary"])
    if covered != s1["runs"]:
        problems.append(
            "the outcome partition covers %d of %d runs -- some run carries an "
            "outcome that is neither played-and-lost, nor dead, nor "
            "no-summary, so the published '22 played / 14 dead / 7 absent' no "
            "longer adds up" % (covered, s1["runs"]))

    eq(s4["budgets"], WORDING_BUDGETS, "budget distribution")
    eq(s4["max_actions_ok"], WORDING_MAX_ACTIONS_OK, "largest actions_ok")
    eq(s4["total_actions_ok"], WORDING_TOTAL_ACTIONS_OK, "total actions_ok")
    eq(s4["distinct_run_ids_in_scorecard_bodies"],
       WORDING_DISTINCT_SCORECARD_RUN_IDS,
       "distinct run_ids in archived scorecard bodies")
    eq(s4["level_1_baselines"], WORDING_LEVEL_1_BASELINES,
       "the API's level-1 baselines")
    eq(s4["budget_below_level_1_baseline"], WORDING_BUDGET_BELOW_BASELINE,
       "runs budgeted below their game's level-1 baseline")

    # ---- the invariant this module exists for ---------------------------
    roster = set(NO_SUMMARY_ROSTER)
    got = set(s3["runs_without_a_summary_ids"])
    for run_id in sorted(roster - got):
        # Named individually: this is the failure the negative sample models.
        doc_path = os.path.join(runs_dir, run_id, "run.json")
        count = "<the run.json is gone>"
        if os.path.exists(doc_path):
            count = _completion_count(_load(doc_path))
        problems.append(
            "run %s is on the no-summary roster -- its completion count is "
            "ABSENT, never written down -- but the record now reports %r for "
            "it. An absent value has been backfilled. This is the one thing "
            "this checker exists to refuse: a run that never produced a "
            "completion count may not be counted as a run that completed zero "
            "levels." % (run_id, count))
    for run_id in sorted(got - roster):
        problems.append(
            "run %s has no summary but is not on the no-summary roster -- a "
            "run lost its summary, or the roster is stale; either way the "
            "published counts no longer describe this tree" % run_id)

    # ---- the partition must stay a partition ----------------------------
    total_partitioned = (s4["budget_below_level_1_baseline"]
                         + s4["budget_at_or_above_level_1_baseline"]
                         + s4["budget_unattributable"])
    if total_partitioned != s1["runs"]:
        problems.append("the budget partition covers %d of %d runs -- a run "
                        "fell out of every bucket"
                        % (total_partitioned, s1["runs"]))
    return problems


# --------------------------------------------------------------------------

def _print(rc: Dict[str, Any]) -> None:
    s1 = rc["section_1_46_is_entries_not_runs"]
    s2 = rc["section_2_score_is_absent_not_zero"]
    s3 = rc["section_3_seven_have_no_count_and_fourteen_never_played"]
    s4 = rc["section_4_no_budget_reached_the_level_1_baseline"]

    print("A33 -- registration #14's sentence, recounted against runs/\n")

    print("1. 46 IS ENTRIES, 43 IS RUNS")
    print("   run.json files on disk ..................... %d" % s1["run_json_files_on_disk"])
    print("   MANIFEST.json counts.total ................. %s" % s1["manifest_total"])
    print("   by kind .................................... %s"
          % ", ".join("%s=%d" % kv for kv in s1["by_kind"].items()))
    print("   entries that never played a game ........... %d"
          % len(s1["not_runs"]))
    for r in s1["not_runs"]:
        print("       %-12s %s" % (r["kind"], r["id"]))

    print("\n2. THE SCORE WAS NEVER IN run.json -- BUT 20 OF 43 ARE RECOVERABLE")
    print("   runs with a summary ........................ %d of %d"
          % (s2["runs_with_a_summary"], s1["runs"]))
    print("   runs persisting a `score` field ............ %d"
          % s2["runs_persisting_a_score_field"])
    print("   gameplay response has a score field ........ %s"
          % s2["score_field_exists_on_gameplay_response"])
    print("   levels_completed across all %d runs ........ %s"
          % (s1["runs"], ", ".join("%s x%d" % kv for kv in s2["completion_counts"].items())))
    print("   score column (harness.score_column) ........ %s"
          % ", ".join("%s=%d" % kv for kv in s2["score_column"].items()))
    print("   distinct recorded scores ................... %s"
          % (s2["distinct_recorded_scores"] or "none"))
    print("   max RECORDED score ......................... %s   (undefined for "
          "the %d runs with no recovered score -- not zero)"
          % (s2["max_recorded_score"],
             s1["runs"] - s2["score_column"].get("recorded", 0)))
    print("   why the rest are missing ................... %s" % s2["score_absence_reason"])

    print("\n3. SEVEN HAVE NO COUNT; FOURTEEN NEVER PLAYED")
    print("   runs without a summary ..................... %d" % s3["runs_without_a_summary"])
    for rid in s3["runs_without_a_summary_ids"]:
        print("       %s" % rid)
    print("   by outcome ................................. %s"
          % ", ".join("%s=%d" % kv for kv in s3["by_outcome"].items()))
    print("   dead runs (%s)" % ", ".join(s3["dead_run_outcomes"]))
    print("                                              . %d (manifest says %s)"
          % (s3["dead_runs"], s3["manifest_dead_runs"]))
    print("   runs that actually played and lost ......... %d" % s3["runs_that_played_and_lost"])

    print("\n4. NO BUDGET REACHED ITS GAME'S LEVEL-1 BASELINE")
    print("   budgets configured ......................... %s"
          % ", ".join("%s x%d" % kv for kv in s4["budgets"].items()))
    print("   largest actions_ok / total ................. %d / %d"
          % (s4["max_actions_ok"], s4["total_actions_ok"]))
    print("   archived run dirs .......................... %d" % s4["archived_run_dirs"])
    print("   distinct run_ids in scorecard bodies ....... %d  (of which %d have "
          "NO archived run.json)"
          % (s4["distinct_run_ids_in_scorecard_bodies"],
             s4["run_ids_with_a_scorecard_but_no_archived_run_json"]))
    print("   distinct run_ids known, either source ...... %d  -- so '43 runs' "
          "means *archived* runs; the arm ran at least this many"
          % s4["distinct_run_ids_known"])
    print("   layer one -- per-run budget vs level-1 baseline")
    print("       (the baseline is a reference solver's action count, NOT a")
    print("        lower bound -- theoria-arm/inner/scoreboard.py says so)")
    print("       below the level-1 baseline ............. %d" % s4["budget_below_level_1_baseline"])
    print("       at or above it (a real test) ........... %d" % s4["budget_at_or_above_level_1_baseline"])
    for r in s4["budget_at_or_above_level_1_baseline_rows"]:
        print("           %s  budget=%s >= baseline=%s" % (r["id"], r["budget"], r["level_1_baseline"]))
    print("       unattributable (no budget or no game) .. %d" % s4["budget_unattributable"])
    print("   layer two -- actions a card accumulated (crosses resets)")
    print("       %-16s %9s %6s %9s %s" % ("game", "base_L1", "obs", "best", "cards>=base"))
    for game, d in s4["card_level_reach"].items():
        print("       %-16s %9d %6d %9d %s"
              % (game, d["level_1_baseline"], d["observations"],
                 d["best_card_actions"], d["cards_reaching_the_baseline"]))
    print("   unit price, $/successful action, by model tier")
    print("       %-32s %5s %9s %9s %9s %11s" % ("model", "runs", "min",
                                                 "median", "max", "aggregate"))
    for tier, t in s4["usd_per_action_by_model"].items():
        print("       %-32s %5d %9.6f %9.6f %9.6f %11s"
              % (tier, t["runs"], t["usd_per_action_min"],
                 t["usd_per_action_median"], t["usd_per_action_max"],
                 "%.6f" % t["usd_per_action_aggregate"]
                 if t["usd_per_action_aggregate"] is not None else "--"))
    print("       'runs' counts runs with a successful action; 'aggregate' is")
    print("       total $ / total successful actions over all priced runs,")
    print("       including the ones that bought nothing. Price a campaign off")
    print("       the aggregate, never off one run's ratio.")
    print("   cost of one run budgeted to its game's level-1 baseline")
    print("       priced per (game, tier) CELL, not per tier: an earlier draft")
    print("       labelled rows 'game x tier' while pricing by tier alone, so")
    print("       every game in a tier got the same number and a cell where")
    print("       that tier bought zero successful actions was priced anyway.")
    for cell, c in sorted(s4["cell_cost_to_reach_baseline"].items()):
        game, tier = cell.split(" x ", 1)
        if c["usd"] is None:
            print("       %-16s x %-28s %3d actions -> UNDEFINED (%s)"
                  % (game, tier, c["level_1_baseline"], c["why"]))
        else:
            print("       %-16s x %-28s %3d actions -> $%6.2f  (%d run(s), "
                  "%d successful action(s), $%.4f/action)"
                  % (game, tier, c["level_1_baseline"], c["usd"], c["runs"],
                     c["actions_ok"], c["usd_per_action"]))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="A33 -- recount registration #14")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--runs-dir", default=RUNS)
    args = ap.parse_args(argv)

    rc = recount(args.runs_dir)
    problems = adjudicate(rc, args.runs_dir)

    if args.json:
        print(json.dumps({"recount": rc, "problems": problems},
                         indent=2, sort_keys=True))
        return 1 if problems else 0

    _print(rc)
    print()
    if problems:
        print("A33: RED (%d problem(s))" % len(problems))
        for p in problems:
            print("   FAIL  %s" % p)
        return 1
    print("A33: green -- every number in the corrected wording recomputes off "
          "runs/, and no absent value is being reported as a zero")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
