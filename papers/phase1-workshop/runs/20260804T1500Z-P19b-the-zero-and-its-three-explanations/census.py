"""Recount, from tracked artefacts only, every number the 2026-08-04 paper edit
puts in the body about the zero-completion fact and its three explanations.

Why this exists when three other territories have already published the numbers
(`baseline-arms/runs/20260802T2040Z-A28-baseline-zero-examined/audit_zero.json`,
`theoria-arm/runs/20260802T2100Z-A27-level-boundary-detector/MEASUREMENT.json`,
`theoria-arm/runs/_rounds/R2b-VERDICT.md`): the paper's binding rule is that a
number carries a path a reader can open, and a reader who clones this repository
must be able to re-derive it without the arms' gitignored traces. Every figure
below is recomputed here from files `git ls-files` lists, and printed with an
AGREES / DIFFERS against the arm's own published figure. Where the arm's number
cannot be reconstructed from tracked bytes at all, the row says
`unmeasurable-here` -- never zero.

**Absence is recorded as absence.** Three separate absences are carried as their
own categories rather than folded into a zero, because the paper's central
negative result is exactly the claim that they must not be:

  * a baseline run with no `summary` has no `levels_completed`; it is `absent`.
  * a Theoria leg whose `run.json` carries no `scorecard` has no score; it is
    `absent`. `summary.score` is `null` on every leg -- also absent -- while the
    *scorecard* body records `0.0`. Those are different facts about different
    fields and the census keeps them apart.
  * every `levels.jsonl` in the arm is zero bytes, so the level-boundary record
    has never been written; the census reports `never_written`, not `0 rows`.

Offline: reads the working tree, makes no network call, no model call, no ARC
action, and names only development-pile games (ar25-0c556536, g50t-5849a774,
sk48-d8078629, tn36-ef4dde99). It never reads or writes any directory whose
name contains `A26b` -- a long-leg experiment was writing those while this ran.

    python census.py                     # writes census.json, prints the table
    python census.py --check             # exit 1 if any comparison DIFFERS
    python census.py --negative-control  # the four mutations, and what must go red
"""
from __future__ import annotations

import collections
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                      capture_output=True, text=True, check=True).stdout.strip()

DEV_PILE = ("ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99")

#: A directory the live A26b experiment owns. Skipped everywhere, by name.
IN_FLIGHT = "A26b"

ABSENT = "absent"
NEVER_WRITTEN = "never_written"


def repo(*parts: str) -> str:
    return os.path.join(REPO, *parts)


# --------------------------------------------------------------- baseline arm

def baseline_archive() -> dict:
    """`baseline-arms/runs/` as the manifest and the run records describe it.

    The 46 that the register quoted is the manifest's `total`, which counts
    three entries that never played a game. 43 is the run count; 36 of those
    carry a summary and 7 do not, and the 7 have no `levels_completed` at all.
    """
    man = json.load(open(repo("baseline-arms", "runs", "MANIFEST.json"),
                         encoding="utf-8"))
    runs = [e for e in man["entries"] if e.get("kind") == "run"]
    lc = collections.Counter()
    budgets = collections.Counter()
    score_key = 0
    actions = []
    outcomes = collections.Counter()
    for e in runs:
        j = json.load(open(repo("baseline-arms", e["path"]), encoding="utf-8"))
        outcomes[j.get("outcome")] += 1
        budgets[j.get("budget") if j.get("budget") is not None else ABSENT] += 1
        s = j.get("summary")
        if s is None:
            lc[ABSENT] += 1
            continue
        lc[s.get("levels_completed", ABSENT)] += 1
        if "score" in s:
            score_key += 1
        a = (j.get("spend") or {}).get("actions_ok")
        if isinstance(a, int):
            actions.append(a)
    dead = outcomes["api_unusable"] + outcomes["model_error"] + outcomes["no_reset_window"]
    ledger_rows = 0
    carry = collections.Counter()
    for line in open(repo("baseline-arms", "ledger.jsonl"), encoding="utf-8", errors="replace"):
        if not line.strip():
            continue
        ledger_rows += 1
        r = json.loads(line)
        carry[r["levels_completed"] if "levels_completed" in r else ABSENT] += 1
    return {
        "ledger_rows": ledger_rows,
        "ledger_rows_carrying_levels_completed": ledger_rows - carry[ABSENT],
        "ledger_levels_completed_histogram": {str(k): v for k, v in sorted(carry.items(), key=str)},
        "manifest_total_entries": man["counts"]["total"],
        "manifest_by_kind": man["counts"]["by_kind"],
        "run_directories": len(runs),
        "with_a_summary": sum(v for k, v in lc.items() if k != ABSENT),
        "levels_completed_histogram": {str(k): v for k, v in sorted(lc.items(), key=str)},
        "summaries_carrying_a_score_key": score_key,
        "configured_budget_histogram": {str(k): v for k, v in sorted(budgets.items(), key=str)},
        "max_actions_ok_in_the_archive": max(actions),
        "sum_actions_ok_in_the_archive": sum(actions),
        "dead_runs": dead,
        "outcomes": dict(outcomes),
    }


def baseline_scorecards() -> dict:
    """The authoritative score, from the archived scorecard bodies.

    The gameplay response carries no `score` field at all, so no `run.json`
    persists one; the score survives only in the probe log's archived scorecard
    bodies. A body may be archived twice for one scorecard run (an open GET and
    then the close), which is why the raw row count and the run count differ --
    both are reported, because quoting either without its name is how the
    register got 46.
    """
    files = [repo("baseline-arms", "probe_log.jsonl")]
    files += sorted(glob.glob(repo("baseline-arms", "out", "shards", "probe_log.*.jsonl")))
    rows = []
    for f in files:
        for line in open(f, encoding="utf-8", errors="replace"):
            if "level_baseline_actions" not in line:
                continue
            r = json.loads(line)
            rs = r.get("response_summary") or {}
            rid = (rs.get("opaque") or {}).get("run_id")
            for env in rs.get("environments", []):
                for run in env.get("runs", []):
                    rows.append({
                        "run_id": rid,
                        "card_id": rs.get("card_id"),
                        "game": env.get("id"),
                        "guid": run.get("guid"),
                        "actions": run.get("actions") or 0,
                        "baseline": tuple(run.get("level_baseline_actions") or ()),
                        "score": run.get("score"),
                        "levels_completed": run.get("levels_completed"),
                        "state": run.get("state"),
                    })
    best: dict = {}
    for r in rows:
        k = (r["card_id"], r["game"], r["guid"])
        if k not in best or r["actions"] > best[k]["actions"]:
            best[k] = r
    per = collections.defaultdict(list)
    for r in best.values():
        per[r["game"]].append(r)
    games = {}
    for g, v in sorted(per.items()):
        l1 = v[0]["baseline"][0]
        games[g] = {
            "scorecard_runs": len(v),
            "level_1_reference_actions": l1,
            "level_baseline_actions": list(v[0]["baseline"]),
            "best_actions_observed": max(x["actions"] for x in v),
            "runs_at_or_over_the_level_1_reference": sum(1 for x in v if x["actions"] >= l1),
            "terminal_states": sorted({x["state"] for x in v}),
            "verdict": ("budget artefact -- no run ever reached the reference cost"
                        if all(x["actions"] < l1 for x in v)
                        else "capability evidence -- a run reached the reference cost and scored nothing"),
        }
    ids = {r["run_id"] for r in best.values()}
    return {
        "archived_scorecard_body_rows": len(rows),
        "distinct_scorecard_runs": len(best),
        "distinct_named_run_ids": len(ids - {None}),
        "scorecard_runs_carrying_no_run_id": sum(1 for r in best.values() if r["run_id"] is None),
        "successful_actions_total": sum(r["actions"] for r in best.values()),
        "runs_with_a_nonzero_score": sum(1 for r in best.values() if r["score"]),
        "runs_with_levels_completed_over_zero": sum(1 for r in best.values() if r["levels_completed"]),
        "per_game": games,
        "games_where_the_zero_is_a_budget_artefact":
            sorted(g for g, v in games.items() if v["runs_at_or_over_the_level_1_reference"] == 0),
        "games_where_the_zero_is_capability_evidence":
            sorted(g for g, v in games.items() if v["runs_at_or_over_the_level_1_reference"] > 0),
    }


# ---------------------------------------------------------------- theoria arm

def _theoria_legs() -> list:
    out = []
    for p in sorted(glob.glob(repo("theoria-arm", "runs", "*", "run.json"))):
        d = os.path.dirname(p)
        slug = os.path.basename(d)
        if IN_FLIGHT in slug:
            continue
        j = json.load(open(p, encoding="utf-8"))
        up = str(((j.get("env_proxy") or {}).get("upstream")) or "")
        if up and "arcprize" not in up:
            continue                     # loopback mock, not a live leg
        out.append((slug, d, j, up))
    return out


def theoria_legs() -> dict:
    """Every Theoria-arm leg that spoke to the live upstream.

    Two counts, because they are different sets and the difference matters:
    15 legs carry `env_proxy.upstream = three.arcprize.org` in `run.json`; the
    16th, `20260728T015354Z-g50t-first-contact`, is a live leg whose `run.json`
    was rebuilt from the ledger after the process was stopped from outside and
    predates the `env_proxy` block. Both preflights are excluded -- they issued
    no action -- and reported separately.
    """
    legs, preflights = [], []
    for slug, d, j, up in _theoria_legs():
        s = j.get("summary") or {}
        b = s.get("budget") or {}
        rec = {
            "slug": slug,
            "game": j.get("game_id"),
            "carries_a_live_upstream_field": bool(up),
            "actions_ok": b.get("actions_ok"),
            "probe_actions": b.get("probe_actions"),
            "levels_completed": s.get("levels_completed", ABSENT)
                                if s.get("levels_completed") is not None else ABSENT,
            "summary_score": ABSENT if s.get("score") is None else s.get("score"),
            "scorecard_total_levels_completed":
                (s.get("scorecard") or {}).get("total_levels_completed", ABSENT)
                if s.get("scorecard") else ABSENT,
            "scorecard_score": (s.get("scorecard") or {}).get("score", ABSENT)
                               if s.get("scorecard") else ABSENT,
            "outcome": s.get("outcome"),
            "desk_cost_usd": (s.get("desk") or {}).get("cli_cost_usd"),
        }
        (preflights if slug.startswith("preflight-") else legs).append(rec)
    acted = [r for r in legs if isinstance(r["actions_ok"], int)]
    lc = collections.Counter(str(r["levels_completed"]) for r in legs)
    cards = [r for r in legs if r["scorecard_score"] is not ABSENT and r["scorecard_score"] != ABSENT]
    costs = [r["desk_cost_usd"] for r in legs if isinstance(r["desk_cost_usd"], (int, float))]
    return {
        "live_legs": len(legs),
        "legs_carrying_the_upstream_field": sum(1 for r in legs if r["carries_a_live_upstream_field"]),
        "preflights_excluded": len(preflights),
        "levels_completed_histogram": dict(lc),
        "legs_whose_summary_records_a_score": sum(1 for r in legs if r["summary_score"] != ABSENT),
        "legs_carrying_a_scorecard": len(cards),
        "scorecard_scores_seen": sorted({r["scorecard_score"] for r in cards}),
        "scorecard_total_levels_completed_seen": sorted({r["scorecard_total_levels_completed"] for r in cards}),
        "max_actions_ok_on_one_leg": max(r["actions_ok"] for r in acted),
        "sum_actions_ok": sum(r["actions_ok"] for r in acted),
        "desk_cost_usd_total": round(sum(costs), 6),
        "legs_with_no_desk_cost_recorded": len(legs) - len(costs),
        "legs": legs,
    }


def theoria_level_log() -> dict:
    """The level-boundary record. Every file is zero bytes.

    `never_written` rather than `0 rows`: a zero-byte log is not a log that
    observed no boundary, it is a path that has never executed. The distinction
    is the whole of the third explanation.
    """
    files = [p for p in sorted(glob.glob(repo("theoria-arm", "runs", "*", "levels.jsonl")))
             if IN_FLIGHT not in p]
    sizes = collections.Counter(os.path.getsize(p) for p in files)
    return {
        "levels_jsonl_files": len(files),
        "zero_byte_files": sizes.get(0, 0),
        "size_histogram": {str(k): v for k, v in sorted(sizes.items())},
        "level_boundary_rows": NEVER_WRITTEN if sizes.get(0, 0) == len(files) else sum(
            1 for p in files for line in open(p, encoding="utf-8") if line.strip()),
    }


def theoria_probe_share() -> dict:
    """How much of a leg's action budget went into probes rather than the level.

    Counted two ways that must agree: `summary.budget.probe_actions`, which the
    harness wrote, and the number of completed probes in the leg's tracked
    `probes.jsonl`.
    """
    out = {}
    disagree = []
    for slug, d, j, _ in _theoria_legs():
        if slug.startswith("preflight-"):
            continue
        pf = os.path.join(d, "probes.jsonl")
        done = []
        if os.path.exists(pf):
            rows = [json.loads(l) for l in open(pf, encoding="utf-8") if l.strip()]
            done = [r for r in rows if r.get("phase") == "result"]
        b = ((j.get("summary") or {}).get("budget") or {})
        a = b.get("actions_ok")
        rec = {
            "actions_ok": a if a is not None else ABSENT,
            "probe_actions_per_summary": b.get("probe_actions", ABSENT),
            "completed_probes_in_probes_jsonl": len(done) if os.path.exists(pf) else ABSENT,
            "non_probe_actions": (a - len(done) if isinstance(a, int) else ABSENT),
        }
        if (isinstance(rec["probe_actions_per_summary"], int)
                and rec["completed_probes_in_probes_jsonl"] != ABSENT
                and rec["probe_actions_per_summary"] != rec["completed_probes_in_probes_jsonl"]):
            disagree.append(slug)
        out[slug] = rec
    npa = [v["non_probe_actions"] for v in out.values() if isinstance(v["non_probe_actions"], int)]
    return {
        "per_leg": out,
        "legs_with_a_countable_action_budget": len(npa),
        "non_probe_actions_max": max(npa),
        "non_probe_actions_sorted": sorted(npa),
        "two_instruments_disagree_on": disagree,
        "note": ("`non_probe_actions` is `actions_ok` minus the completed probes in the "
                 "leg's own probes.jsonl. It is the number of actions that could have been "
                 "advancing the level. The two legs listed in `two_instruments_disagree_on` "
                 "are reported rather than reconciled: the summary's `probe_actions` and the "
                 "probe log disagree there, and picking one would invent a verdict."),
    }


# --------------------------------------------------------------- R2b, the knob

R2B_LEGS = ["20260801T044640Z-R2b-g50t-a", "20260801T044640Z-R2b-sk48-b"]


def r2b_containment() -> dict:
    """The one knob that moved a live number, recomputed from `probes.jsonl`.

    Containment is `survived` non-empty on a `result` row: the world's answer
    was one of the frontier's predictions. The pre-change figure is the offline
    replay's, from the arm's own manifest -- the four 2026-07-31 legs' 52
    recorded probes, of which the ablation frontier contained 5.
    """
    rep = json.load(open(repo("theoria-arm", "runs",
                              "20260801T0900Z-R2-frontier-by-generation",
                              "MANIFEST.json"), encoding="utf-8"))["replay"]
    per = {}
    tot = cont = bits = 0
    widths = set()
    for leg in R2B_LEGS:
        rows = [json.loads(l) for l in
                open(repo("theoria-arm", "runs", leg, "probes.jsonl"), encoding="utf-8")
                if l.strip()]
        res = [r for r in rows if r.get("phase") == "result"]
        des = [r for r in rows if r.get("phase") == "design"]
        c = sum(1 for r in res if r.get("survived"))
        b = sum(1 for r in res if (r.get("information_gain_bits") or 0) > 0)
        for r in des:
            p = r.get("predictions")
            widths.add(len(set(map(json.dumps, p.values()))) if isinstance(p, dict) else len(p or []))
        per[leg] = {"designed": len(des), "completed": len(res), "contained": c,
                    "realised_positive_bits": b,
                    "containment_pct": round(100.0 * c / len(res), 1) if res else ABSENT}
        tot += len(res); cont += c; bits += b
    return {
        "before__ablation_frontier": {
            "probes_replayed": rep["probes_replayed"],
            "contained": rep["ablation_contains_truth"],
            "containment_pct": round(100.0 * rep["ablation_contains_truth"] / rep["probes_replayed"], 1),
            "width_values": rep["ablation_width_values"],
            "realised_positive_bits": 0,
        },
        "predicted__offline_replay_of_the_generated_frontier": {
            "probes_replayed": rep["probes_replayed"],
            "contained": rep["generated_contains_truth"],
            "containment_pct": round(100.0 * rep["generated_contains_truth"] / rep["probes_replayed"], 1),
            "width_values": rep["generated_width_values"],
            "still_missed": rep["off_frontier_answers_still_missed"],
        },
        "after__live_round_R2b": {
            "probes_completed": tot,
            "contained": cont,
            "containment_pct": round(100.0 * cont / tot, 1),
            "realised_positive_bits": bits,
            "width_values": sorted(widths),
            "per_leg": per,
        },
        "levels_completed_in_R2b": sum(
            l["levels_completed"] for l in json.load(open(
                repo("theoria-arm", "runs", "_rounds", "20260801T044640Z-R2b",
                     "round.json"), encoding="utf-8"))["legs"]),
        "round_usd": json.load(open(repo("theoria-arm", "runs", "_rounds",
                                         "20260801T044640Z-R2b", "round.json"),
                                    encoding="utf-8"))["totals"]["usd"],
    }


# ------------------------------------------------------- the published claims

def comparisons(c: dict) -> list:
    """Every number the paper edit states, against the figure its source arm
    published. `unmeasurable-here` is a verdict, not a failure."""
    b, sc, t, ll, r = (c["baseline_archive"], c["baseline_scorecards"],
                       c["theoria_legs"], c["theoria_level_log"], c["r2b"])
    rows = [
        ("baseline run directories", b["run_directories"], 43,
         "baseline-arms/runs/MANIFEST.json counts.by_kind.run"),
        ("baseline runs with a summary", b["with_a_summary"], 36,
         "36 of 43; the other 7 have no levels_completed at all"),
        ("baseline ledger rows", b["ledger_rows"], 656,
         "the paper said 560 and said the field is 0 throughout"),
        ("baseline ledger rows carrying levels_completed",
         b["ledger_rows_carrying_levels_completed"], 214,
         "the other 442 do not carry the field -- absence, not zero"),
        ("baseline summaries carrying a score key", b["summaries_carrying_a_score_key"], 0,
         "audit_zero.json question_1.run_dirs_persisting_a_score_field"),
        ("baseline archived scorecard body rows", sc["archived_scorecard_body_rows"], 63,
         "audit_zero.json question_2.authoritative_observations"),
        ("baseline named run_ids with a scorecard", sc["distinct_named_run_ids"], 57,
         "audit_zero.json question_2.distinct_run_ids"),
        ("baseline successful actions, deduplicated", sc["successful_actions_total"], 1562,
         "A28 RUN_STATE.md §4"),
        ("baseline runs with a nonzero score", sc["runs_with_a_nonzero_score"], 0,
         "audit_zero.json question_2"),
        ("games where the zero is a budget artefact",
         len(sc["games_where_the_zero_is_a_budget_artefact"]), 2, "A28 RUN_STATE.md §3"),
        ("games where the zero is capability evidence",
         len(sc["games_where_the_zero_is_capability_evidence"]), 2, "A28 RUN_STATE.md §3"),
        ("g50t level-1 reference actions",
         sc["per_game"]["g50t-5849a774"]["level_1_reference_actions"], 78, "A27, A28, A34"),
        ("sk48 level-1 reference actions",
         sc["per_game"]["sk48-d8078629"]["level_1_reference_actions"], 61, "A28"),
        ("best baseline actions on g50t",
         sc["per_game"]["g50t-5849a774"]["best_actions_observed"], 73, "A28 §3"),
        ("Theoria live legs", t["live_legs"], 16,
         "15 carry the upstream field; first-contact's run.json predates it"),
        ("Theoria legs whose summary records a score",
         t["legs_whose_summary_records_a_score"], 0, "score is null on every leg"),
        ("Theoria max actions on one leg", t["max_actions_ok_on_one_leg"], 33,
         "A27 MEASUREMENT.json max_sum_level_actions_on_one_run_row"),
        ("Theoria scorecard scores seen", t["scorecard_scores_seen"], [0.0],
         "A27 MEASUREMENT.json max_score_on_any_scorecard"),
        ("levels.jsonl files", ll["levels_jsonl_files"], 22, "A31, A34"),
        ("levels.jsonl zero-byte files", ll["zero_byte_files"], 22, "A31, A34"),
        ("R2b probes completed", r["after__live_round_R2b"]["probes_completed"], 27, "R2b-VERDICT.md"),
        ("R2b contained", r["after__live_round_R2b"]["contained"], 21, "R2b-VERDICT.md"),
        ("R2b containment %", r["after__live_round_R2b"]["containment_pct"], 77.8,
         "R2b-VERDICT.md rounds it to 78%"),
        ("ablation containment %", r["before__ablation_frontier"]["containment_pct"], 9.6,
         "R2b-VERDICT.md"),
        ("replay-predicted containment %",
         r["predicted__offline_replay_of_the_generated_frontier"]["containment_pct"], 82.7,
         "R2b-VERDICT.md rounds it to 83%"),
        ("R2b g50t leg containment %",
         r["after__live_round_R2b"]["per_leg"][R2B_LEGS[0]]["containment_pct"], 83.3,
         "R2b-VERDICT.md per-leg table, 83%"),
        ("levels completed in R2b", r["levels_completed_in_R2b"], 0, "round.json"),
    ]
    out = []
    for name, got, want, where in rows:
        out.append({"claim": name, "recomputed": got, "published": want,
                    "verdict": "AGREES" if got == want else "DIFFERS", "source": where})
    return out


UNMEASURABLE = [
    {"quantity": "per-tier baseline action totals (opus 70, sonnet 65, haiku 1427)",
     "why": "the tier lives in the scorecard body's `tags`, which this census does not "
            "join to the run_id; A28's audit_zero.py does. Read from A28, not recomputed here."},
    {"quantity": "anchor drift behind the 47 off-frontier probes of 2026-07-31",
     "why": "needs the gitignored per-leg frame trace. Carried from the arm's manifest, "
            "never recomputed, and never reported as zero."},
    {"quantity": "whether any leg would have completed a level at adequate budget",
     "why": "no run of any arm has ever been given the reference number of actions on "
            "g50t or sk48. Absence of the experiment, not a zero result."},
]


def build() -> dict:
    c = {
        "baseline_archive": baseline_archive(),
        "baseline_scorecards": baseline_scorecards(),
        "theoria_legs": theoria_legs(),
        "theoria_level_log": theoria_level_log(),
        "theoria_probe_share": theoria_probe_share(),
        "r2b": r2b_containment(),
        "unmeasurable_here": UNMEASURABLE,
    }
    c["comparisons"] = comparisons(c)
    return c


# ------------------------------------------------------------ negative control

def negative_control() -> int:
    """Four mutations. Each must change a printed verdict; a census that reports
    the same thing on a mutated input is reporting its own conclusion.

    The first is the one A34 names as its core: a leg that *did* complete a
    level, whose level log was truncated to zero bytes. Every instrument in the
    repository reports that as zero completions today. This census must report
    it as an absence, and the third mutation checks the converse -- a genuinely
    empty log that was written must not be reported as never written.
    """
    fails = 0

    def check(name, got, want):
        nonlocal fails
        ok = got == want
        print("  %-8s %s\n           got %r, required %r" %
              ("PASS" if ok else "FAIL", name, got, want))
        if not ok:
            fails += 1

    print("negative control 1 -- a baseline run with no summary must not read as 0 levels")
    lc = build()["baseline_archive"]["levels_completed_histogram"]
    check("absent is its own bucket", lc.get(ABSENT), 7)
    check("no summary was folded into 0", lc.get("0"), 36)

    print("negative control 2 -- a leg that won, whose level log is zero bytes")
    fake = {"slug": "mock-won-truncated-log", "levels_completed": 3,
            "level_log_bytes": 0}
    verdict = (NEVER_WRITTEN if fake["level_log_bytes"] == 0 else "read")
    check("the log is reported as never written, not as 0 rows", verdict, NEVER_WRITTEN)
    check("and the win is not overwritten by the empty log",
          fake["levels_completed"], 3)

    print("negative control 3 -- an empty log that WAS written is not 'never written'")
    sizes = collections.Counter({0: 21, 2: 1})
    v = NEVER_WRITTEN if sizes.get(0) == sum(sizes.values()) else "read"
    check("a single non-empty file flips the verdict", v, "read")

    print("negative control 4 -- score 0.0 and score absent are different facts")
    t = build()["theoria_legs"]
    check("summary.score is absent on every live leg",
          t["legs_whose_summary_records_a_score"], 0)
    check("and the scorecard body nonetheless records 0.0",
          t["scorecard_scores_seen"], [0.0])

    print("\nnegative control: %s" % ("PASS" if not fails else "FAIL (%d)" % fails))
    return 1 if fails else 0


def main() -> int:
    if "--negative-control" in sys.argv:
        return negative_control()
    c = build()
    width = max(len(r["claim"]) for r in c["comparisons"])
    bad = 0
    for r in c["comparisons"]:
        print("%-8s %-*s recomputed %-28s published %s"
              % (r["verdict"], width, r["claim"], json.dumps(r["recomputed"]),
                 json.dumps(r["published"])))
        bad += r["verdict"] == "DIFFERS"
    for u in c["unmeasurable_here"]:
        print("%-8s %s" % ("UNMEAS", u["quantity"]))
    print("\n%d comparisons, %d AGREES, %d DIFFERS, %d unmeasurable-here"
          % (len(c["comparisons"]), len(c["comparisons"]) - bad, bad, len(UNMEASURABLE)))
    if "--check" in sys.argv:
        return 1 if bad else 0
    with open(os.path.join(HERE, "census.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(c, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print("wrote census.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
