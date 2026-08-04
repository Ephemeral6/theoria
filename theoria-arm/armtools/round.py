"""One Phase-3 round: N legs in parallel, one framework version, one scoreboard.

    python -m armtools.round --round R7 --legs g50t:a sk48:b --budget 300 --ceiling 15

`Theoria.md:336` fixes the shape of an iteration: pick the most painful
failure class, change **one** thing, re-run a minimal verification unit
(2-3 legs on the same small set), keep or roll back against the scoreboard.
The forbidden moves are named too: changing several things at once (attribution
dies) and deciding on a single leg's difference (variance lies).

Parallelism has to respect that. So the unit of change is the **round**, never
the leg: every leg in a round runs the same tree, and legs differ only in the
game they play and which CLI account carries their desk. Two accounts means two
legs at a time without either waiting on the other's rate limit; the ARC side is
shared and is charged through the one shared pool either way, which is what
makes the pool -- not the account -- the thing that says stop.

What this does NOT do is decide anything. It runs the legs, waits, and writes
`round.json` with the seven surprise counts, the theorize rounds, the desk
spend and the level progress per leg. The keep-or-roll-back call reads that
file and is made by a person or by the session driving the loop, because
`Theoria.md:336`'s rule is about judgement and the numbers are its input.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from . import level_evidence

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
REPO = os.path.dirname(ARM)

#: The two CLI accounts. A leg's desk runs under exactly one of them, so a
#: session limit on one account stops one leg rather than the round.
ACCOUNTS = {
    "a": os.path.join(os.path.expanduser("~"), ".claude-accounts", "a"),
    "b": os.path.join(os.path.expanduser("~"), ".claude-accounts", "b"),
}

SURPRISE_KINDS = ("replay_mismatch", "render_mismatch", "proof_failure",
                  "probe_refutation", "execution_mismatch",
                  "search_timeout", "heuristic_miss")


def utc_slug() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def launch(game: str, account: str, slug: str, *, budget: int, ceiling: float,
           model: str, seed_books: Optional[str], prompt_id: str,
           round_id: str, knobs: Optional[List[str]] = None) -> subprocess.Popen:
    """Start one leg. Returns the process; the log is its own file.

    `knobs` are the switch flags this round turns on, forwarded verbatim to
    `harness.run`. R1 is why this parameter exists: the runner recorded a
    `--change` sentence saying `goal_protocol=propose` and had no way to pass
    it, so both legs ran the default and the round measured nothing while its
    own record said otherwise. A field that describes an intervention without
    causing it is worse than no field -- it is a green light with no bulb.
    """
    env = dict(os.environ)
    cfg = ACCOUNTS.get(account)
    if cfg:
        env["CLAUDE_CONFIG_DIR"] = cfg
    cmd = [sys.executable, "-m", "harness.run",
           "--game", game, "--slug", slug,
           "--budget", str(budget), "--cost-ceiling", str(ceiling),
           "--model", model, "--prompt-id", prompt_id,
           "--tags", "%s,round,%s" % (round_id, account)]
    if seed_books:
        cmd += ["--seed-books", seed_books, "--carry-source-game", game]
    cmd += list(knobs or ())
    log_dir = os.path.join(ARM, "runs", "_round_logs")
    os.makedirs(log_dir, exist_ok=True)
    log = open(os.path.join(log_dir, "%s.log" % slug), "w", encoding="utf-8")
    return subprocess.Popen(cmd, cwd=ARM, env=env, stdout=log,
                            stderr=subprocess.STDOUT, text=True)


def read_leg(slug: str) -> Dict[str, Any]:
    """One leg's scoreboard row, straight from its own record."""
    path = os.path.join(ARM, "runs", slug, "RUN_STATE.json")
    if not os.path.exists(path):
        return {"slug": slug, "state": "no RUN_STATE.json"}
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    budget = d.get("budget") or {}
    desk = d.get("desk") or {}
    surprises = d.get("surprises") or {}
    levels = d.get("levels") or {}
    by_kind = dict(surprises.get("by_kind") or {})
    # The counter as the leg's own summary reports it, and -- separately -- what
    # the leg's *artefacts* support. A34: the two are not the same claim. A leg
    # that crossed a boundary and lost `levels.jsonl` reports the same
    # `levels.levels_completed` as a leg that crossed nothing, and the round
    # total below used to add both to the same number.
    evidence = level_evidence.read_leg(os.path.join(ARM, "runs", slug))
    return {
        "slug": slug,
        "game_id": d.get("game_id"),
        "outcome": d.get("outcome"),
        "stopped_because": (d.get("stopped_because") or "")[:200] or None,
        "actions_ok": budget.get("actions_ok"),
        "levels_completed": levels.get("levels_completed"),
        "levels_evidence": {"verdict": evidence["verdict"],
                            "levels_completed": evidence["levels_completed"],
                            "detail": evidence["detail"]},
        "level": levels.get("level"),
        "desk_calls": desk.get("calls"),
        "usd": desk.get("cli_cost_usd"),
        # `theorize_rounds` is the scoreboard column Theoria.md:351 names, and
        # it is absent on runs that stopped before the first theorize -- absent
        # is recorded as absent, never as zero (battery/REPORT_V0.md's rule).
        "theorize_rounds": d.get("theorize_rounds"),
        "surprises_total": surprises.get("total"),
        "surprises": {k: by_kind.get(k) for k in SURPRISE_KINDS},
        "empirical": (surprises.get("by_family") or {}).get("empirical"),
        "computational": (surprises.get("by_family") or {}).get("computational"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--round", required=True,
                    help="round id, e.g. R7 -- goes into the tags and the record")
    ap.add_argument("--legs", nargs="+", required=True, metavar="GAME:ACCOUNT",
                    help="one per parallel leg, e.g. g50t-5849a774:a sk48-d8078629:b")
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--ceiling", type=float, default=15.0)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--prompt-id", default="A3-campaign-devpile")
    ap.add_argument("--seed-books", default=None,
                    help="a books/ dir to carry into EVERY leg, or omit for cold")
    ap.add_argument("--change", required=True,
                    help="the ONE thing this round changed, in a sentence. "
                         "Written into round.json; Theoria.md:336 forbids a "
                         "round that changed several things, and a record with "
                         "no answer here is that round with the evidence lost.")
    ap.add_argument("--knob", action="append", default=None, metavar="FLAG",
                    help="a switch flag forwarded verbatim to every leg, e.g. "
                         "--knob --goal-protocol=propose. Repeatable, but a "
                         "round that turns on two unrelated knobs is not one "
                         "round (Theoria.md:336) -- the runner does not stop "
                         "you, it records what you did.")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    stamp = utc_slug()
    out_dir = args.out_dir or os.path.join(ARM, "runs",
                                           "_rounds", "%s-%s" % (stamp, args.round))
    os.makedirs(out_dir, exist_ok=True)

    procs, slugs = [], []
    for spec in args.legs:
        game, _, account = spec.partition(":")
        account = account or "a"
        slug = "%s-%s-%s-%s" % (stamp, args.round, game.split("-")[0], account)
        procs.append((slug, launch(game, account, slug, budget=args.budget,
                                   ceiling=args.ceiling, model=args.model,
                                   seed_books=args.seed_books,
                                   prompt_id=args.prompt_id,
                                   round_id=args.round,
                                   knobs=args.knob)))
        slugs.append(slug)
        print("launched %s (%s, account %s)" % (slug, game, account), flush=True)

    codes = {}
    for slug, p in procs:
        codes[slug] = p.wait()
        print("finished %s rc=%d" % (slug, codes[slug]), flush=True)

    legs = [read_leg(s) for s in slugs]
    record = {
        "round": args.round,
        "utc": stamp,
        "change": args.change,
        # The prose and the argv, side by side. A reader comparing them is the
        # only thing that catches a `--change` describing an intervention the
        # legs never received; R1 shipped exactly that and nothing noticed.
        "knobs": list(args.knob or ()),
        "seed_books": args.seed_books,
        "budget_per_leg": args.budget,
        "ceiling_per_leg": args.ceiling,
        "model": args.model,
        "exit_codes": codes,
        "legs": legs,
        "totals": {
            "usd": round(sum((l.get("usd") or 0) for l in legs), 6),
            "actions_ok": sum((l.get("actions_ok") or 0) for l in legs),
            "desk_calls": sum((l.get("desk_calls") or 0) for l in legs),
            # A34's negative control lives on this line. It used to read
            # `sum((l.get("levels_completed") or 0) for l in legs)`, which
            # turns three different facts -- "completed none", "never looked",
            # "completed one and lost the record" -- into the same integer.
            # `level_evidence.total` sums only the legs whose artefacts support
            # a count and reports the rest as not counted, by name.
            "levels": level_evidence.total(
                [dict(l.get("levels_evidence") or
                      {"verdict": "no_run", "levels_completed": None},
                      slug=l.get("slug")) for l in legs]),
            "surprises": {k: sum((l["surprises"].get(k) or 0) for l in legs
                                 if isinstance(l.get("surprises"), dict))
                          for k in SURPRISE_KINDS},
        },
    }
    path = os.path.join(out_dir, "round.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(record, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(record["totals"], indent=1, sort_keys=True))
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
