"""Generate the machine-checked half of `freeze/BUDGET_TABLE.md` — item 12 of
`Theoria.md:368`.

## Why this is a program

`freeze/build_manifest.py`'s docstring records what happened to the two
hand-written drafts of the hash table: nineteen of thirty-three hashes were
already wrong one day later.  A budget table rots the same way and worse, because
its numbers are *sums over append-only files that keep growing*.  The moment a
run spends a dollar, every total in a hand-copied table is false — and false in
the direction of claiming more headroom than exists, which is the direction that
launches a campaign that cannot finish.

So the rule is the same one:

    every dollar figure in BUDGET_TABLE.md is generated from the ledgers, and
    `--verify` fails if the ledgers no longer produce it.

The judgements around it — what B should be, which scenario to run, whether a
placeholder counts as spent — stay hand-written in the Markdown, because a
judgement is exactly the thing that must not be regenerated.

## The three pools this file keeps apart

There is no single number for "what has been spent", and pretending otherwise is
the defect this file exists to prevent:

1. **The gate's pool** — `proxy/var/spend_gate.jsonl`, the only total any
   `SpendGate.check()` consults, and therefore the only one that can refuse a
   request.  It is **gitignored** (`proxy/.gitignore:3`), so it cannot enter a
   freeze manifest; see `--emit-pool-digest`.
2. **The tracked arm ledgers** — `baseline-arms/ledger.jsonl`,
   `baseline-arms/out/shards/ledger.*.jsonl`, `theoria-arm/runs/**/ledger.jsonl`.
   These carry the CLI's self-reported `total_cost_usd`, i.e. what was actually
   billed, and they are in git.  They are **larger** than the gate's pool,
   because most of the money was spent before the gate existed.
3. **A re-pricing of the same tracked usage** through
   `proxy/pricing/pricing_v1.json`, which is what the frozen price table would
   say the history cost.  It disagrees with (2), and by how much is a number the
   budget table has to publish rather than average away.

## Usage

    python freeze/build_budget_table.py                 # write JSON + refresh the block
    python freeze/build_budget_table.py --verify         # exit 1 on drift
    python freeze/build_budget_table.py --verify --allow-absent-pool
    python freeze/build_budget_table.py --emit-pool-digest

`--verify` is what belongs in a gate.  Drift in the tracked half means somebody
edited a ledger or the table; drift in the pool half means **the balance moved**,
which is not a nuisance — it is the one event that must invalidate a frozen
budget table.
"""

import argparse
import glob
import hashlib
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_JSON = os.path.join(HERE, "BUDGET_TABLE.json")
OUT_MD = os.path.join(HERE, "BUDGET_TABLE.md")
POOL_DIGEST = os.path.join(HERE, "POOL_DIGEST.json")

BEGIN = "<!-- BEGIN GENERATED: freeze/build_budget_table.py -->"
END = "<!-- END GENERATED -->"

#: `proxy/spend_policy.json` names the pool by a path relative to the **main
#: checkout**, not the importing worktree (`proxy/SPEND_GATE.md:219-226`: one
#: pool per worktree was a real defect worth $10,959.90 of authorised exposure).
#: This file resolves it the same way, by walking up out of `.worktrees/<id>/`.
def resolve_pool(rel):
    cand = os.path.join(REPO, rel.replace("/", os.sep))
    if os.path.exists(cand):
        return cand
    parts = REPO.replace("/", os.sep).split(os.sep)
    if ".worktrees" in parts:
        main = os.sep.join(parts[:parts.index(".worktrees")])
        cand = os.path.join(main, rel.replace("/", os.sep))
        if os.path.exists(cand):
            return cand
    return None


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args):
    try:
        out = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                             text=True, timeout=60)
    except Exception:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def usd(value):
    """Money is rounded once, here, to four places, and never re-rounded.

    Four is not cosmetic: the ledgers carry six, and a table that prints two
    would make `$0.0000` records (there are 1,617 of them) look like absences.
    """
    return round(float(value) + 0.0, 4)


# --------------------------------------------------------------------------
# 1 · the policy and the price table
# --------------------------------------------------------------------------

def read_policy():
    path = os.path.join(REPO, "proxy", "spend_policy.json")
    spec = json.load(open(path, encoding="utf-8"))
    return {
        "path": "proxy/spend_policy.json",
        "sha256": sha256_file(path),
        "usd_ceiling": spec["usd_ceiling"],
        "action_ceiling": spec["action_ceiling"],
        "default_run_usd": spec["default_run_caps"]["usd"],
        "default_run_actions": spec["default_run_caps"]["actions"],
        "ledger_rel": spec["ledger"],
    }


def read_pricing():
    path = os.path.join(REPO, "proxy", "pricing", "pricing_v1.json")
    spec = json.load(open(path, encoding="utf-8"))
    return {
        "path": "proxy/pricing/pricing_v1.json",
        "sha256": sha256_file(path),
        "effective": spec["effective"],
        "models": sorted(spec["models"]),
        "cache_multipliers": spec["cache_multipliers"],
        # The dated id every arm actually sends is absent from the table
        # (THEORIA_ARM_COST.md:184-190). Recorded, not worked around.
        "dated_haiku_key_present": "claude-haiku-4-5-20251001" in spec["models"],
    }


# --------------------------------------------------------------------------
# 2 · the gate's pool (untracked)
# --------------------------------------------------------------------------

def read_pool(rel):
    path = resolve_pool(rel)
    if path is None:
        return {"present": False, "path": rel,
                "why": "the pool is gitignored (proxy/.gitignore:3) and this "
                       "checkout does not have one; every balance figure below "
                       "is unverifiable here"}

    kinds = {}
    total_usd = 0.0
    total_actions = 0
    unpriced = []
    corrections = []
    by_campaign = {}
    by_model = {}
    lines = 0
    max_seq = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            lines += 1
            rec = json.loads(line)
            kind = rec.get("kind")
            kinds[kind] = kinds.get(kind, 0) + 1
            max_seq = max(max_seq, int(rec.get("seq") or 0))
            if kind not in ("spend", "price_correction"):
                continue
            amount = float(rec.get("usd") or 0)
            actions = int(rec.get("actions") or 0)
            total_usd += amount
            total_actions += actions
            camp = rec.get("campaign") or "?"
            slot = by_campaign.setdefault(camp, {"usd": 0.0, "actions": 0,
                                                 "lines": 0, "unpriced_usd": 0.0})
            slot["usd"] += amount
            slot["actions"] += actions
            slot["lines"] += 1
            detail = rec.get("detail") or {}
            model = detail.get("model")
            if model:
                mslot = by_model.setdefault(model, {"calls": 0, "usd": 0.0,
                                                    "min": None, "max": None,
                                                    "values": []})
                mslot["calls"] += 1
                mslot["usd"] += amount
                mslot["values"].append(amount)
            if kind == "price_correction":
                corrections.append({"seq": rec.get("seq"), "usd": usd(amount),
                                    "resolves": rec.get("resolves"),
                                    "reason": rec.get("reason")})
            elif rec.get("unpriced"):
                slot["unpriced_usd"] += amount
                unpriced.append({
                    "seq": rec.get("seq"), "usd": usd(amount),
                    "actions": actions, "campaign": camp,
                    "model": detail.get("model"), "beat": detail.get("beat"),
                    "outcome": detail.get("outcome"), "why": detail.get("why"),
                })

    for model, slot in by_model.items():
        # Per-call figures keep six places: rounding them to four would erase
        # the 0.5% agreement with BUDGET_REPORT 13.1 that is the only
        # independent check any unit price in this table has.
        values = sorted(slot.pop("values"))
        total = slot["usd"]
        slot["usd"] = usd(total)
        slot["min"] = round(values[0], 6)
        slot["max"] = round(values[-1], 6)
        slot["median"] = round(values[len(values) // 2], 6)
        slot["mean"] = round(total / slot["calls"], 6)

    # Traffic that consumed action headroom without buying an observation.
    # Append-only: this headroom is gone, so it belongs in the balance.
    def test_like(name):
        return any(tag in name for tag in ("pytest", "mock", "smoke", "canary"))

    return {
        "present": True,
        "path": rel,
        "abspath_is_main_checkout": os.path.normpath(path)
                                    != os.path.normpath(os.path.join(REPO, rel)),
        "sha256": sha256_file(path),
        "lines": lines,
        "max_seq": max_seq,
        "kinds": dict(sorted(kinds.items())),
        "usd": usd(total_usd),
        "actions": total_actions,
        "unpriced_calls": len(unpriced),
        "unpriced_usd": usd(sum(u["usd"] for u in unpriced)),
        "unpriced": unpriced,
        "price_corrections": corrections,
        "usd_measured": usd(total_usd - sum(u["usd"] for u in unpriced)),
        "actions_test_like": sum(s["actions"] for c, s in by_campaign.items()
                                 if test_like(c)),
        "by_model": dict(sorted(by_model.items())),
        "by_campaign_nonzero": {
            c: {"usd": usd(s["usd"]), "actions": s["actions"],
                "lines": s["lines"], "unpriced_usd": usd(s["unpriced_usd"])}
            for c, s in sorted(by_campaign.items(), key=lambda kv: -kv[1]["usd"])
            if usd(s["usd"]) > 0
        },
        "campaigns": len(by_campaign),
    }


# --------------------------------------------------------------------------
# 3 · the tracked arm ledgers
# --------------------------------------------------------------------------

BARE_CC_LEDGERS = ("baseline-arms/ledger.jsonl",
                   "baseline-arms/out/shards/ledger.*.jsonl")
THEORIA_LEDGERS = ("theoria-arm/runs/**/ledger.jsonl",)


def _self_reported(rec):
    value = rec.get("total_cost_usd")
    if value is None and isinstance(rec.get("response"), dict):
        value = rec["response"].get("total_cost_usd")
    return value


def _usage(rec):
    if isinstance(rec.get("usage"), dict):
        return rec["usage"]
    if isinstance(rec.get("response"), dict) \
            and isinstance(rec["response"].get("usage"), dict):
        return rec["response"]["usage"]
    return None


def read_tracked_ledgers(patterns, reprice):
    """Sum `total_cost_usd` over every tracked ledger matching `patterns`.

    Files are sorted and read once each; the run-id/step-id keys are checked for
    cross-file collisions, because a shard that duplicated another shard would
    inflate the bill silently and is exactly the kind of thing a budget table is
    asked to have ruled out.
    """
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(REPO, pattern.replace("/", os.sep)),
                               recursive=True))
    files = sorted(set(files))

    per_file = {}
    total = 0.0
    repriced_total = 0.0
    calls = 0
    unpriceable = 0
    runs = set()
    seen = {}
    collisions = 0
    for path in files:
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        if not git("ls-files", "--error-unmatch", rel):
            continue
        file_usd = 0.0
        file_calls = 0
        file_repriced = 0.0
        file_unpriceable = 0
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            usage = _usage(rec)
            amount = _self_reported(rec)
            if usage is None or amount is None:
                continue
            key = (rec.get("run_id"), rec.get("seq"), rec.get("step_idx"),
                   rec.get("call_idx"), rec.get("ts"))
            if key in seen and seen[key] != rel:
                collisions += 1
            seen[key] = rel
            file_usd += float(amount)
            file_calls += 1
            calls += 1
            runs.add(rec.get("run_id"))
            if reprice is not None:
                priced = reprice(rec.get("model"), usage)
                if priced is None:
                    unpriceable += 1
                    file_unpriceable += 1
                else:
                    file_repriced += priced
        total += file_usd
        repriced_total += file_repriced
        # `usd_pricing_v1` is **null**, never 0.0, when nothing in the file could
        # be priced. A frozen price table that cannot price a call must say so:
        # printing $0.0000 there would be a false zero, and a false zero in a
        # budget table reads as "this was free".
        per_file[rel] = {"usd_self_reported": usd(file_usd),
                         "usd_pricing_v1": (None if file_unpriceable
                                            and file_repriced == 0.0
                                            else usd(file_repriced)),
                         "calls": file_calls,
                         "unpriceable_calls": file_unpriceable}
    return {
        "files": dict(sorted(per_file.items())),
        "usd_self_reported": usd(total),
        "usd_pricing_v1": usd(repriced_total),
        "calls": calls,
        "runs": len(runs),
        "unpriceable_calls": unpriceable,
        "cross_file_duplicate_keys": collisions,
    }


def make_repricer():
    """`proxy/cost.py` is the authoritative converter and is imported, not
    re-implemented.  Re-implementing it is the defect `build_manifest.py`'s
    docstring names: a record of what another file says, with nothing that
    rereads it.  If the import fails, the re-pricing column is reported absent
    rather than guessed."""
    try:
        sys.path.insert(0, REPO)
        from proxy.cost import PriceTable
        table = PriceTable.load()
    except Exception as exc:                                # pragma: no cover
        print("note: proxy.cost unavailable (%s); pricing_v1 column omitted"
              % exc, file=sys.stderr)
        return None, None

    def reprice(model, usage):
        try:
            out = table.cost(model, usage)
        except Exception:
            return None
        return out.get("usd")

    return reprice, table.sha256


# --------------------------------------------------------------------------
# 4 · the factors of the sealed main table
# --------------------------------------------------------------------------

def read_factors():
    claim = json.load(open(os.path.join(REPO, "arc-recon", "data",
                                        "claim_set.json"), encoding="utf-8"))
    piles = json.load(open(os.path.join(REPO, "arc-recon", "data",
                                        "piles.json"), encoding="utf-8"))
    # Sealed game ids are counted, never read: `len()` on the roster is the
    # whole of this file's contact with the sealed pile.
    return {
        "claim_set_size": claim["claim_set_size"],
        "claim_set_len": len(claim["claim_set"]),
        "clean_len": len(claim["clean"]),
        "quarantined": sorted(claim["quarantined"]),
        "piles_sha256": piles["sha256"],
        "n_public": piles["n_public"],
        "dev_pile": len(piles["dev_pile"]),
        "sealed_pile": len(piles["sealed_pile"]),
        "arms": 3,
        "n_reps": 2,
        # Denominators quoted in the tree, not recomputed here: the per-game
        # baseline-action counts for the sealed pile are sealed-game metadata
        # and this file does not open them.
        "public_baseline_actions": 17135,      # BUDGET_REPORT.md:121
        "dev_baseline_actions": 3014,          # BUDGET_REPORT.md:119
        "envelope_action_budget": 30,          # BUDGET_REPORT.md:450 (D-011)
    }


# --------------------------------------------------------------------------
# 5 · unit costs and projections
# --------------------------------------------------------------------------

#: Measured unit prices, each with the cell count it rests on.  Every value is
#: quoted from a path:line, never averaged into a new number here — the point of
#: the table is that a reader can go and check each one.
UNIT_PRICES = [
    {"tier": "claude-haiku-4-5-20251001", "usd_per_success_action": 0.0435,
     "usd_per_model_call": 0.0392, "http_per_action": 1.97,
     "success_rate": 0.906, "cells": 9,
     "cite": "baseline-arms/BUDGET_REPORT.md:688"},
    {"tier": "claude-opus-5", "usd_per_success_action": 0.1460,
     "usd_per_model_call": 0.1168, "http_per_action": 3.11,
     "success_rate": 0.800, "cells": 3,
     "cite": "baseline-arms/BUDGET_REPORT.md:689"},
    {"tier": "claude-sonnet-5", "usd_per_success_action": 0.1793,
     "usd_per_model_call": 0.1143, "http_per_action": 4.46,
     "success_rate": 0.722, "cells": 3,
     "cite": "baseline-arms/BUDGET_REPORT.md:690"},
]

#: `BUDGET_REPORT.md:836` — "按 §3.5 +15–20% 留余量", because the newest measured
#: cell is 16% above the ten-cell mean the unit prices use and §14.3 rules the
#: rise a version-level change in the `claude -p` wrapper that will not fall
#: back.  18% is the midpoint of the interval the report states; it is a stated
#: margin, not a measurement, and is labelled as such everywhere it is used.
MARGIN = 1.18

#: `STATS_RULES.md` §5.2 finding three, as recomputed by RES-1 for §5.7.  This
#: is a *contention-condition* figure: all 48 episodes were measured during
#: INC-BA-003, so it is plausibly an upper bound on q, and no line below may
#: present it as a property of the world.
DEATH_RATE_NUM = 47
DEATH_RATE_DEN = 48
FLOOR_NUM = 14         # STATS_RULES.md §1.2 pre-registered U3 floor, claim tier
FLOOR_DEN = 19


def projections(factors):
    """Cost of the sealed main table, per scenario.

    Two axes the tree has not fixed, so both are enumerated rather than picked:
    the per-episode action budget (⛔ undecided) and the model tier (⛔ undecided,
    `PENDING_FIVE.md:93-95`).
    """
    sealed = factors["public_baseline_actions"] - factors["dev_baseline_actions"]
    mean_actions = sealed / factors["sealed_pile"]
    cells = factors["claim_set_size"] * factors["arms"]
    episodes = cells * factors["n_reps"]

    q = DEATH_RATE_NUM / DEATH_RATE_DEN
    floor = FLOOR_NUM / FLOOR_DEN
    n_for_floor = math.ceil(math.log(1 - floor) / math.log(q))

    rows = []
    for price in UNIT_PRICES:
        for label, budget in (("envelope-30", float(factors["envelope_action_budget"])),
                              ("S1-baseline-actions", mean_actions)):
            per_episode = price["usd_per_success_action"] * budget
            for n, tag in ((factors["n_reps"], "nominal"),
                           (n_for_floor, "n-to-reach-floor")):
                count = cells * n
                rows.append({
                    "tier": price["tier"], "scenario": label,
                    "n": n, "basis": tag,
                    "actions_per_episode": round(budget, 2),
                    "episodes": count,
                    "usd_per_episode": usd(per_episode),
                    "usd_total": usd(count * per_episode),
                    "usd_total_with_margin": usd(count * per_episode * MARGIN),
                    "arc_requests": int(round(count * budget
                                              * price["http_per_action"])),
                })
    return {
        "sealed_baseline_actions_21": sealed,
        "mean_baseline_actions_per_game": round(mean_actions, 4),
        "cells": cells,
        "episodes_nominal": episodes,
        "death_rate_q": round(q, 6),
        "cell_survival_at_n": {str(n): round(1 - q ** n, 6) for n in (1, 2, 3)},
        "live_cells_of_19_at_n": {str(n): round(factors["claim_set_size"]
                                                * (1 - q ** n), 4)
                                  for n in (1, 2, 3)},
        "n_to_reach_floor": n_for_floor,
        "q_ceiling_for_floor_at_n": {str(n): round((1 - floor) ** (1.0 / n), 4)
                                     for n in (2, 3)},
        "margin_applied": MARGIN,
        "rows": rows,
    }


# --------------------------------------------------------------------------
# 6 · citation liveness
# --------------------------------------------------------------------------

#: A budget table is a table of citations, so the citations are themselves
#: checked.  A `path:line` that has drifted, or a section number that does not
#: exist, is a silent failure of exactly the kind the table is supposed to stop.
CITED_LINES = [
    ("proxy/spend_policy.json", 4, '"usd_ceiling": 214.9'),
    ("proxy/spend_policy.json", 5, '"action_ceiling": 24000'),
    ("proxy/spend_policy.json", 6, '"ledger": "proxy/var/spend_gate.jsonl"'),
    ("proxy/.gitignore", 3, "var/"),
    ("baseline-arms/BUDGET_REPORT.md", 119, "3014"),
    ("baseline-arms/BUDGET_REPORT.md", 121, "17135"),
    ("baseline-arms/BUDGET_REPORT.md", 420, "$50.00"),
    ("baseline-arms/BUDGET_REPORT.md", 688, "0.0435"),
    ("baseline-arms/BUDGET_REPORT.md", 689, "0.1460"),
    ("baseline-arms/BUDGET_REPORT.md", 690, "0.1793"),
    ("baseline-arms/BUDGET_REPORT.md", 836, "15–20%"),
    ("baseline-arms/runs/20260728T103135Z-a7/THEORIA_ARM_COST.md", 52, "1.0935"),
    ("monitor/board/claimed/A3-campaign-devpile.RES-1.md", 54, "B = $60"),
    ("freeze/STATS_RULES.md", 26, "bare_cc"),
    # Re-anchored 2026-07-29 (RES-1, E-WORDING).  Two of these three were never
    # valid: `git show d4fb6d72:freeze/STATS_RULES.md | sed -n 777p` (the commit
    # that ADDED them) is not the 0.78 line, and 791 is not the 0.513 line --
    # they were computed against a draft whose §5.7 rewrite shifted before it was
    # committed.  So --verify has been red since the moment these landed, and
    # nobody saw it, because this generator is not called from verify.sh.  It is
    # now, as stage [15b].
    # These three move whenever STATS_RULES.md is edited, and it is edited
    # often.  That is the gate working as designed -- a quoted number must still
    # be where the quote says -- but it means the anchors have to be recomputed
    # with the edit, not later.  Reproducible one-liner, run from the repo root:
    #
    #   python -c "ls=open('freeze/STATS_RULES.md',encoding='utf-8').read().split(chr(10));    #   [print(repr(n),[i+1 for i,l in enumerate(ls) if n in l][:3]) for n in ('⟨n⟩ = 2','0.78','0.513')]"
    #
    # Take the FIRST hit in each case: each is the §5.5 ruling / §5.7 arithmetic
    # statement, and the later hits are the block quotes that restate it.
    ("freeze/STATS_RULES.md", 953, "⟨n⟩ = 2"),
    ("freeze/STATS_RULES.md", 956, "0.78"),
    ("freeze/STATS_RULES.md", 1046, "0.513"),
]

#: Files and sections the Markdown cites that are being written by other hands.
#: Absent ones are reported, so the citation cannot dangle unnoticed.
CITED_SECTIONS = [
    ("freeze/STATS_RULES.md", "§5.7"),
    ("freeze/n_feasibility.py", None),
]


def check_citations():
    line_results = []
    for rel, lineno, needle in CITED_LINES:
        path = os.path.join(REPO, rel.replace("/", os.sep))
        state = "missing-file"
        if os.path.exists(path):
            lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
            state = "ok" if (lineno <= len(lines) and needle in lines[lineno - 1]) \
                else "drifted"
        line_results.append({"cite": "%s:%d" % (rel, lineno),
                             "expect": needle, "state": state})
    section_results = []
    for rel, section in CITED_SECTIONS:
        path = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(path):
            state = "missing-file"
        elif section is None:
            state = "ok"
        else:
            body = open(path, encoding="utf-8", errors="replace").read()
            state = "ok" if section in body else "missing-section"
        section_results.append({"cite": rel + (" " + section if section else ""),
                                "state": state})
    return {"lines": line_results, "sections": section_results,
            "drifted": [r["cite"] for r in line_results if r["state"] != "ok"],
            "absent": [r["cite"] for r in section_results if r["state"] != "ok"]}


# --------------------------------------------------------------------------
# 7 · assembly
# --------------------------------------------------------------------------

def build():
    policy = read_policy()
    pricing = read_pricing()
    pool = read_pool(policy["ledger_rel"])
    reprice, pricing_sha = make_repricer()
    bare = read_tracked_ledgers(BARE_CC_LEDGERS, reprice)
    theoria = read_tracked_ledgers(THEORIA_LEDGERS, reprice)
    factors = read_factors()

    # Each dollar counted once. The gate's pool overlaps the tracked ledgers
    # (the a7 shards are the same money), so the union is taken as
    # tracked-ledger totals plus the pool campaigns that have no tracked ledger.
    pool_only = 0.0
    pool_only_placeholder = 0.0
    if pool["present"]:
        for camp, slot in pool["by_campaign_nonzero"].items():
            if camp.startswith("phase3-variance-envelope") and camp.endswith("envelope"):
                continue                              # == a7-*.jsonl shards
            if camp in ("phase3-unit-price-remeasure", "phase3-unit-price-recheck"):
                continue                              # == a7up-*/a7recheck shards
            pool_only += slot["usd"] - slot["unpriced_usd"]
            pool_only_placeholder += slot["unpriced_usd"]

    measured = bare["usd_self_reported"] + theoria["usd_self_reported"] + pool_only
    nominal = measured + pool_only_placeholder
    ceiling = policy["usd_ceiling"]

    balance = {
        "ceiling_usd": ceiling,
        "gate_visible_usd": pool["usd"] if pool["present"] else None,
        "gate_visible_headroom_usd": usd(ceiling - pool["usd"]) if pool["present"] else None,
        "tracked_bare_cc_usd": bare["usd_self_reported"],
        "tracked_theoria_usd": theoria["usd_self_reported"],
        "pool_only_measured_usd": usd(pool_only),
        "pool_only_placeholder_usd": usd(pool_only_placeholder),
        "programme_measured_usd": usd(measured),
        "programme_nominal_usd": usd(nominal),
        "remaining_measured_usd": usd(ceiling - measured),
        "remaining_nominal_usd": usd(ceiling - nominal),
        "gate_blind_spot_usd": usd(measured - pool["usd"]) if pool["present"] else None,
        "action_ceiling": policy["action_ceiling"],
        "actions_used": pool["actions"] if pool["present"] else None,
        "actions_remaining": (policy["action_ceiling"] - pool["actions"])
                             if pool["present"] else None,
        "actions_spent_on_test_traffic": pool.get("actions_test_like"),
        "pricing_v1_vs_self_reported_theoria_pct": (
            round(100 * (theoria["usd_pricing_v1"] / theoria["usd_self_reported"] - 1), 2)
            if theoria["usd_self_reported"] else None),
    }

    proj = projections(factors)
    remaining = balance["remaining_measured_usd"]
    for row in proj["rows"]:
        row["fits_remaining_measured"] = row["usd_total_with_margin"] <= remaining
        row["fits_action_ceiling"] = (
            balance["actions_remaining"] is not None
            and row["arc_requests"] <= balance["actions_remaining"])
    fitting = [r for r in proj["rows"] if r["fits_remaining_measured"]
               and r["fits_action_ceiling"]]

    return {
        "format": "theoria/freeze-budget-table/1",
        "source": "Theoria.md:368 冻结清单第 12 项「预算表」; Theoria.md:377 "
                  "⟨$/局硬顶、总局数、止损⟩",
        "generated_from": {
            "commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        },
        "policy": policy,
        "pricing": dict(pricing, table_sha256_as_loaded=pricing_sha),
        "pool": pool,
        "tracked_bare_cc": bare,
        "tracked_theoria": theoria,
        "factors": factors,
        "unit_prices": UNIT_PRICES,
        "balance": balance,
        "projection": proj,
        "citations": check_citations(),
        "verdict": {
            "fitting_scenarios": [
                "%s / %s / n=%d" % (r["tier"], r["scenario"], r["n"])
                for r in fitting],
            "sealed_table_fits": bool(fitting),
            "statement": (
                "Of %d enumerated scenarios for the sealed main table "
                "(%d claim games x %d arms), %d fit both the remaining "
                "measured balance ($%.2f) and the remaining action headroom "
                "(%s requests). At the only measured episode death rate "
                "(q=%d/%d) a nominal n=%d table yields %.2f live cells of %d, "
                "so a projection over nominal cells is not a projection over "
                "observations."
                % (len(proj["rows"]), factors["claim_set_size"], factors["arms"],
                   len(fitting), remaining,
                   balance["actions_remaining"], DEATH_RATE_NUM, DEATH_RATE_DEN,
                   factors["n_reps"],
                   proj["live_cells_of_19_at_n"][str(factors["n_reps"])],
                   factors["claim_set_size"])),
        },
    }


# --------------------------------------------------------------------------
# 8 · the generated Markdown block
# --------------------------------------------------------------------------

def render(data):
    bal = data["balance"]
    pool = data["pool"]
    proj = data["projection"]
    out = [BEGIN, ""]
    out.append("*Every figure in this block is recomputed by "
               "`python freeze/build_budget_table.py --verify`. Do not edit it "
               "by hand: the next `--verify` will call the edit drift, which is "
               "the point.*")
    out.append("")

    out.append("### G1 · 池与余额（口径三分，不合并）")
    out.append("")
    out.append("| 量 | 值 | 出处 |")
    out.append("|---|---|---|")
    out.append("| 池上限 | $%.2f | `proxy/spend_policy.json:4` |" % bal["ceiling_usd"])
    out.append("| 动作上限 | %s | `proxy/spend_policy.json:5` |"
               % format(bal["action_ceiling"], ","))
    if pool["present"]:
        out.append("| 闸门可见已花 | **$%.4f** | `%s` seq 1–%d（%d 行，sha256 `%s…`）|"
                   % (pool["usd"], pool["path"], pool["max_seq"], pool["lines"],
                      pool["sha256"][:12]))
        out.append("| 闸门可见余额 | $%.4f | 上两行相减 |"
                   % bal["gate_visible_headroom_usd"])
        out.append("| 其中未计价占位 | $%.4f（%d 笔）| 见 C1 |"
                   % (pool["unpriced_usd"], pool["unpriced_calls"]))
        out.append("| 动作已用 | %s / %s | 同上 |"
                   % (format(pool["actions"], ","),
                      format(bal["action_ceiling"], ",")))
        out.append("| 其中测试/离线流量 | %s（%.1f%%）| 见 C6 |"
                   % (format(bal["actions_spent_on_test_traffic"], ","),
                      100.0 * bal["actions_spent_on_test_traffic"] / pool["actions"]))
    else:
        out.append("| 闸门可见已花 | ⛔ 本 checkout 无池 | %s |" % pool["why"])
    out.append("| 已追踪账本 · `bare_cc` 轨道 | **$%.4f**（%d 次调用 / %d run / %d 文件）| `baseline-arms/ledger.jsonl` + `out/shards/ledger.*.jsonl` |"
               % (bal["tracked_bare_cc_usd"], data["tracked_bare_cc"]["calls"],
                  data["tracked_bare_cc"]["runs"],
                  len(data["tracked_bare_cc"]["files"])))
    out.append("| 已追踪账本 · Theoria 臂 | **$%.4f**（%d 次调用 / %d run）| `theoria-arm/runs/**/ledger.jsonl` |"
               % (bal["tracked_theoria_usd"], data["tracked_theoria"]["calls"],
                  data["tracked_theoria"]["runs"]))
    out.append("| 仅在池里、无追踪账本 | $%.4f + $%.4f 占位 | 见 C1 / C3 |"
               % (bal["pool_only_measured_usd"], bal["pool_only_placeholder_usd"]))
    out.append("| **全项目已花（实测）** | **$%.4f** | 上四行之并，每一元只计一次 |"
               % bal["programme_measured_usd"])
    out.append("| **全项目已花（含占位）** | $%.4f | 同上 + 占位 |"
               % bal["programme_nominal_usd"])
    out.append("| **真实余额（实测口径）** | **$%.4f** | 上限 − 实测 |"
               % bal["remaining_measured_usd"])
    if bal["gate_blind_spot_usd"] is not None:
        out.append("| **闸门盲区** | **$%.4f** | 实测已花 − 闸门可见已花 |"
                   % bal["gate_blind_spot_usd"])
    out.append("| `pricing_v1` 对 Theoria 臂重算 vs 实际账单 | **%+.2f%%** | 见 C4 |"
               % bal["pricing_v1_vs_self_reported_theoria_pct"])
    out.append("")

    out.append("### G2 · 已追踪账本逐文件（自报 `total_cost_usd`）")
    out.append("")
    out.append("`pricing_v1` 一列写 **⛔** 而不是 $0.0000 的地方，意思是"
               "**该文件的调用冻结价目表算不出来**（见 C5），不是「免费」。")
    out.append("")
    out.append("| 文件 | 自报 $ | `pricing_v1` 重算 $ | 调用 | 其中无法计价 |")
    out.append("|---|---|---|---|---|")
    for group in ("tracked_bare_cc", "tracked_theoria"):
        for rel, slot in data[group]["files"].items():
            priced = slot["usd_pricing_v1"]
            out.append("| `%s` | %.4f | %s | %d | %s |"
                       % (rel, slot["usd_self_reported"],
                          "⛔ 全部无法计价" if priced is None else "%.4f" % priced,
                          slot["calls"],
                          "%d" % slot["unpriceable_calls"]
                          if slot["unpriceable_calls"] else "—"))
    unpriceable = (data["tracked_bare_cc"]["unpriceable_calls"]
                   + data["tracked_theoria"]["unpriceable_calls"])
    calls = data["tracked_bare_cc"]["calls"] + data["tracked_theoria"]["calls"]
    out.append("| **合计** | **%.4f** | %.4f（仅可计价的 %d 笔）| **%d** | **%d（%.1f%%）** |"
               % (bal["tracked_bare_cc_usd"] + bal["tracked_theoria_usd"],
                  data["tracked_bare_cc"]["usd_pricing_v1"]
                  + data["tracked_theoria"]["usd_pricing_v1"],
                  calls - unpriceable, calls, unpriceable,
                  100.0 * unpriceable / calls))
    out.append("")
    out.append("跨文件重复记录键：**%d**（0 = 无双计）。"
               % (data["tracked_bare_cc"]["cross_file_duplicate_keys"]
                  + data["tracked_theoria"]["cross_file_duplicate_keys"]))
    out.append("**两列不可相减当差额**：自报一列是全部 %d 笔，`pricing_v1` 一列只是"
               "可计价的 %d 笔。唯一可比的一对是 Theoria 臂那 7 笔（G1 末行、C4）。"
               % (calls, calls - unpriceable))
    out.append("")

    if pool["present"]:
        out.append("### G3 · 池内有钱的战役（$0 的 %d 个战役省略）"
                   % (pool["campaigns"] - len(pool["by_campaign_nonzero"])))
        out.append("")
        out.append("| 战役 | $ | 其中占位 $ | 动作 |")
        out.append("|---|---|---|---|")
        for camp, slot in pool["by_campaign_nonzero"].items():
            out.append("| `%s` | %.4f | %.4f | %d |"
                       % (camp, slot["usd"], slot["unpriced_usd"], slot["actions"]))
        out.append("")

        out.append("### G4 · 池内逐模型每次调用的散布（点估计之外）")
        out.append("")
        out.append("| model | n 次调用 | 合计 $ | 均值 | 中位 | min | max |")
        out.append("|---|---|---|---|---|---|---|")
        for model, slot in pool["by_model"].items():
            out.append("| `%s` | %d | %.4f | %.6f | %.6f | %.6f | %.6f |"
                       % (model, slot["calls"], slot["usd"], slot["mean"],
                          slot["median"], slot["min"], slot["max"]))
        out.append("")

    out.append("### G5 · 封存主表的三个因子（逐个对树核过）")
    out.append("")
    fac = data["factors"]
    out.append("| 因子 | 值 | 出处 |")
    out.append("|---|---|---|")
    out.append("| claim 层局数 | **%d** | `arc-recon/data/claim_set.json` `claim_set_size`，`len(claim_set)` = %d，二者一致 |"
               % (fac["claim_set_size"], fac["claim_set_len"]))
    out.append("| clean 层局数 | %d | 同文件 `clean` |" % fac["clean_len"])
    out.append("| 隔离出去的 | %s | 同文件 `quarantined`（F-11）|"
               % "、".join("`%s`" % g for g in fac["quarantined"]))
    out.append("| 臂数 | **%d** | `freeze/STATS_RULES.md:26` |" % fac["arms"])
    out.append("| ⟨n⟩ | **%d** | `freeze/STATS_RULES.md:712`（§5.5 裁定）+ `:765` §5.7 |"
               % fac["n_reps"])
    out.append("| 公开集 / 开发堆 / 封存堆 | %d / %d / %d | `arc-recon/data/piles.json`（sha256 `%s…`）|"
               % (fac["n_public"], fac["dev_pile"], fac["sealed_pile"],
                  fac["piles_sha256"][:8]))
    out.append("| 格数 = 局 × 臂 | **%d** | %d × %d |"
               % (proj["cells"], fac["claim_set_size"], fac["arms"]))
    out.append("| episode 数 = 格 × n | **%d** | %d × %d |"
               % (proj["episodes_nominal"], proj["cells"], fac["n_reps"]))
    out.append("| 封存堆 21 局官方基线动作 | %s | %d − %d = %d（`BUDGET_REPORT.md:121` − `:119`）|"
               % (format(proj["sealed_baseline_actions_21"], ","),
                  fac["public_baseline_actions"], fac["dev_baseline_actions"],
                  proj["sealed_baseline_actions_21"]))
    out.append("| 均值动作/局 | %.2f | 上行 ÷ %d。**这是 21 局的均值，不是 19 局的实数** |"
               % (proj["mean_baseline_actions_per_game"], fac["sealed_pile"]))
    out.append("")

    out.append("### G6 · 逐格投影（%d 情景，全部枚举，不挑）"
               % len(proj["rows"]))
    out.append("")
    out.append("余量系数 **×%.2f** 按 `BUDGET_REPORT.md:836`（「+15–20%% 留余量」的中点）。"
               % proj["margin_applied"])
    out.append("`n-to-reach-floor` 一列的 n = %d，见 G7。" % proj["n_to_reach_floor"])
    out.append("")
    out.append("| 档位 | 情景 | 动作/ep | n | ep 数 | $/ep | 合计 $ | 含余量 $ | ARC 请求 | 装得下钱？ | 装得下动作？ |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for row in proj["rows"]:
        out.append("| `%s` | %s | %.1f | %d | %d | %.4f | %s | **%s** | %s | %s | %s |"
                   % (row["tier"], row["scenario"], row["actions_per_episode"],
                      row["n"], row["episodes"], row["usd_per_episode"],
                      format(round(row["usd_total"], 2), ","),
                      format(round(row["usd_total_with_margin"], 2), ","),
                      format(row["arc_requests"], ","),
                      "✅" if row["fits_remaining_measured"] else "❌",
                      "✅" if row["fits_action_ceiling"] else "❌"))
    out.append("")

    out.append("### G7 · 格的存活率：投影的分母不是格数，是**出数的格数**")
    out.append("")
    out.append("q = %d/%d = %.6f，**争用条件下的实测值**（`STATS_RULES.md` §5.2 "
               "发现三；48 集全部测于 INC-BA-003 自伤争用期，故 q 很可能是上界，"
               "**不是关于世界的性质**）。推导与复算：`STATS_RULES.md` §5.7 + "
               "`freeze/n_feasibility.py`（RES-1）。"
               % (DEATH_RATE_NUM, DEATH_RATE_DEN, proj["death_rate_q"]))
    out.append("")
    out.append("| n | 格存活率 1−qⁿ | claim 层出数格数（/%d）|" % fac["claim_set_size"])
    out.append("|---|---|---|")
    for n in ("1", "2", "3"):
        out.append("| %s | %.6f | **%.2f** |"
                   % (n, proj["cell_survival_at_n"][n],
                      proj["live_cells_of_19_at_n"][n]))
    out.append("")
    out.append("| 反解 | 值 |")
    out.append("|---|---|")
    out.append("| 在 q=%.6f 下达到预注册地板 %d/%d 所需的 n | **%d** |"
               % (proj["death_rate_q"], FLOOR_NUM, FLOOR_DEN,
                  proj["n_to_reach_floor"]))
    for n in ("2", "3"):
        out.append("| n=%s 能达到 %d/%d 所需的 q ≤ | **%.4f** |"
                   % (n, FLOOR_NUM, FLOOR_DEN, proj["q_ceiling_for_floor_at_n"][n]))
    out.append("")

    cits = data["citations"]
    out.append("### G8 · 引用存活检查")
    out.append("")
    out.append("逐行引用 %d 条：**%d 条对上**，漂移 %s。"
               % (len(cits["lines"]),
                  sum(1 for r in cits["lines"] if r["state"] == "ok"),
                  "无" if not cits["drifted"] else "、".join(
                      "`%s`" % c for c in cits["drifted"])))
    out.append("")
    out.append("待落盘引用：%s"
               % ("全部就位" if not cits["absent"] else "、".join(
                   "⛔ `%s`" % c for c in cits["absent"])))
    out.append("")
    out.append("### G9 · 裁决")
    out.append("")
    out.append("> %s" % data["verdict"]["statement"])
    out.append("")
    out.append("装得下的情景：%s"
               % ("**一个都没有**" if not data["verdict"]["fitting_scenarios"]
                  else "、".join("`%s`" % s for s
                                in data["verdict"]["fitting_scenarios"])))
    out.append("")
    out.append(END)
    return "\n".join(out) + "\n"


def splice(block):
    """Put the generated block back between its markers, leaving the prose."""
    if not os.path.exists(OUT_MD):
        return None
    body = open(OUT_MD, encoding="utf-8").read()
    match = re.search(re.escape(BEGIN) + r".*?" + re.escape(END), body, re.S)
    if not match:
        return None
    return body[:match.start()] + block.rstrip("\n") + body[match.end():]


# --------------------------------------------------------------------------
# 9 · the pool digest — the least-bad remedy for an unhashable ledger
# --------------------------------------------------------------------------

def pool_digest(data):
    """A tracked, redacted summary of an untracked pool.

    The pool cannot go into the freeze manifest: it is gitignored by design
    (`proxy/.gitignore:3`) and it contains host names, pids and reservation ids.
    But a budget table that must be frozen and reproducible cannot rest on a
    file nobody else can hash.  This is the compromise: the aggregates the table
    actually quotes, plus the pool's own sha256 and its last seq, so a later
    reader can say whether they are looking at the same pool — and, if the pool
    is gone, still has the numbers the freeze was decided on.

    Redaction is by allow-list, not by removal: only the fields named here are
    copied.  `holder`, `reservation_id`, `policy_sha256` and every `detail`
    payload are never read into it.
    """
    pool = data["pool"]
    if not pool["present"]:
        return None
    return {
        "format": "theoria/freeze-pool-digest/1",
        "why": "proxy/var/spend_gate.jsonl is gitignored (proxy/.gitignore:3) "
               "and cannot be hashed into freeze/MANIFEST.json. This digest is "
               "the tracked, redacted stand-in the budget table cites.",
        "pool_path": pool["path"],
        "pool_sha256": pool["sha256"],
        "pool_lines": pool["lines"],
        "pool_max_seq": pool["max_seq"],
        "kinds": pool["kinds"],
        "usd": pool["usd"],
        "usd_measured": pool["usd_measured"],
        "actions": pool["actions"],
        "actions_test_like": pool["actions_test_like"],
        "unpriced": pool["unpriced"],
        "price_corrections": pool["price_corrections"],
        "by_campaign_nonzero": pool["by_campaign_nonzero"],
        "by_model": pool["by_model"],
        "redaction": "allow-list; holder/pid/host, reservation_id, "
                     "policy_sha256 and all detail payloads are not copied",
    }


def main():
    # The block is CJK and carries U+2212; a GBK console would raise on it and
    # turn a reporting step into a crash.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # pragma: no cover
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true",
                        help="exit non-zero if the ledgers no longer produce "
                             "freeze/BUDGET_TABLE.{json,md}")
    parser.add_argument("--allow-absent-pool", action="store_true",
                        help="with --verify: a checkout without "
                             "proxy/var/spend_gate.jsonl is a warning, not a "
                             "failure. Use only where the balance is not the "
                             "thing under test.")
    parser.add_argument("--emit-pool-digest", action="store_true",
                        help="write freeze/POOL_DIGEST.json, the tracked "
                             "redacted stand-in for the untracked pool")
    args = parser.parse_args()

    data = build()
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    block = render(data)

    if args.verify:
        rc = 0
        if not os.path.exists(OUT_JSON):
            print("freeze/BUDGET_TABLE.json does not exist; run without --verify")
            return 1
        strip = lambda blob: {k: v for k, v in json.loads(blob).items()
                              if k != "generated_from"}
        on_disk = open(OUT_JSON, encoding="utf-8").read()
        if strip(on_disk) != strip(text):
            old, new = strip(on_disk), strip(text)
            moved = sorted(k for k in set(old) | set(new)
                           if old.get(k) != new.get(k))
            print("DRIFT: freeze/BUDGET_TABLE.json no longer describes this tree.")
            print("       sections that moved: %s" % ", ".join(moved))
            if "pool" in moved or "balance" in moved:
                print("       `pool`/`balance` moved => THE BALANCE MOVED. A frozen")
                print("       budget table with a stale balance is the failure this")
                print("       gate exists to catch. Regenerate and re-read it.")
            rc = 1
        spliced = splice(block)
        if spliced is None:
            print("DRIFT: freeze/BUDGET_TABLE.md is missing or has lost its "
                  "generated-block markers.")
            rc = 1
        elif spliced != open(OUT_MD, encoding="utf-8").read():
            print("DRIFT: the generated block in freeze/BUDGET_TABLE.md is "
                  "stale or was hand-edited.")
            rc = 1
        if not data["pool"]["present"]:
            print("POOL ABSENT: %s" % data["pool"]["why"])
            if not args.allow_absent_pool:
                rc = 1
        if data["citations"]["drifted"]:
            print("CITATION DRIFT: %s"
                  % ", ".join(data["citations"]["drifted"]))
            rc = 1
        if data["citations"]["absent"]:
            print("CITATION NOT YET ON DISK (⛔, not a failure): %s"
                  % ", ".join(data["citations"]["absent"]))
        if rc == 0:
            print("freeze/BUDGET_TABLE.{json,md} still describes this tree")
            print("  %s" % data["verdict"]["statement"])
        return rc

    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote freeze/BUDGET_TABLE.json")
    spliced = splice(block)
    if spliced is None:
        print("freeze/BUDGET_TABLE.md has no generated-block markers; "
              "writing the block to stdout instead")
        print(block)
    else:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(spliced)
        print("refreshed the generated block in freeze/BUDGET_TABLE.md")
    if args.emit_pool_digest:
        digest = pool_digest(data)
        if digest is None:
            print("no pool in this checkout; POOL_DIGEST.json not written")
        else:
            with open(POOL_DIGEST, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(digest, indent=2, sort_keys=True,
                                        ensure_ascii=False) + "\n")
            print("wrote freeze/POOL_DIGEST.json (tracked stand-in; "
                  "committing it is RES-1's call, not this script's)")
    print("  %s" % data["verdict"]["statement"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
