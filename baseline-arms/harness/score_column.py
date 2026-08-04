"""A33 -- the baseline arm's missing `score` column, built rather than excused.

Registration #14 said the baseline arm's "max score" was 0. No `run.json` in
this arm has ever carried a `score` key, so as read that sentence was reporting
a field that does not exist. A33's second obligation was: **give the arm a
score column, or write down that it cannot have one. Silent absence is not an
option.**

It turns out a column is buildable, for part of the arm, entirely offline.

Where the score actually lives
------------------------------
The ARC gameplay response (`RESET`, `ACTIONn`) carries no `score` field at all
-- only `state`, `levels_completed` and `win_levels` (A28,
`harness.audit_zero`; the same conclusion is reached independently at
`theoria-arm/inner/loop.py`, which sets `"score": None` with that comment).
The authoritative score is on the **scorecard body**, returned by
`GET /api/scorecard/<id>` and by a successful `POST /api/scorecard/close`, at

    response_summary.environments[].runs[].score

joined back to a run through `response_summary.opaque.run_id`. This territory
archived those bodies into `probe_log.jsonl` and `out/shards/probe_log*.jsonl`
as they arrived, so the join can be made now, on a clean checkout, with no
network call.

Five states, and the last three are why this module exists
----------------------------------------------------------
Every run gets exactly one of:

  * ``recorded``      -- archived scorecard bodies carry its score, and they
    agree on one value.
  * ``conflicting``   -- bodies carry more than one distinct score for the same
    run. No number is published: two archived answers is not an answer, and
    picking one would be the same substitution this module exists to refuse.
  * ``unobtainable``  -- the run has a `card_id` and at least one archived
    attempt on that card came back ``404 scorecard <id> not found``. See the
    honesty note below for exactly how much that measured.
  * ``never_probed``  -- the run has a `card_id` and **no archived attempt on
    it at all**. Not the same as unobtainable: nothing was measured, so
    nothing may be concluded. (Empty on today's record -- every one of the 15
    unobtainable cards has a recorded failure -- but the code checks rather
    than assumes, because ``unobtainable`` asserts a measurement.)
  * ``absent``        -- no `card_id` was ever recorded (including the seven
    runs reconstructed from the ledger, which have no summary at all).

Only ``recorded`` carries a number. The other four are **not zero**, and this
module never emits one for them. That is the entire point: the sentence being
corrected turned a missing read into a measurement, and a column that defaulted
the gaps to 0.0 -- or that quietly dropped a disagreeing value out of its own
maximum -- would do the same thing one layer down.

How much "unobtainable" actually measured, stated exactly
----------------------------------------------------------
`DECISIONS.md` D-015 describes eight retries of both `GET /api/scorecard/<id>`
and a repeat close, all 404. That is a real measurement, and it is **not** what
was done to most of these cards. On the archived record:

  * 13 of the 15 have exactly **one** failed attempt -- a single
    `POST /api/scorecard/close` that returned 404.
  * 2 of them got D-015's eight retries.
  * `GET /api/scorecard/<id>` was **never attempted for any of the 15**. The
    only cards a GET was ever issued for are four that are in `recorded`.

So `unobtainable` here is: *one archived refusal, generalised by D-015's
finding on two other cards*. It is an inference resting on a measurement, not
the measurement itself, and each row says which it had. Writing "no amount of
money will buy it back" over thirteen single-404s would be dressing an
inference as a measurement -- in the module whose thesis is that you must not.

    python -m harness.score_column            # the column
    python -m harness.score_column --json     # machine-readable

Read-only. No network call, no credential read, nothing outside this
territory's own archived probe logs and `runs/`.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, List, Optional

from harness import audit_zero

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(HERE, "runs")

# What a permanently-lost card looks like in the probe log. D-015 measured it.
NOT_FOUND = "not found"


def card_probe_outcomes() -> Dict[str, List[int]]:
    """card_id -> the HTTP statuses its archived scorecard probes returned.

    Attribution reads the id from the places the writers actually put it,
    in order of how much they can be relied on:

      1. `request_body.card_id` -- present on every close call this territory
         ever made, and the only source that does not depend on what the
         server said back.
      2. top-level `card_id` -- how the `scorecard_close_failed` records carry
         it. Those records hold `last_status` and `tries`, i.e. the literal
         D-015 evidence, and an earlier draft of this function dropped all 17
         of them on the floor because it only looked at `status`/`http_status`.
      3. `response_summary.card_id` -- present on successful bodies.
      4. last resort: the first uuid-shaped token in the URL or the response
         text. This worked only because the API's 404 message happens to echo
         the id ("scorecard <uuid> not found"); if that wording ever changes,
         every card silently drops to zero recorded probes. That is survivable
         *now* only because `build()` distinguishes `never_probed` from
         `unobtainable` instead of labelling a card unobtainable on the
         strength of an attribution that quietly failed.
    """
    out: Dict[str, List[int]] = {}
    for pat in audit_zero.PROBE_GLOBS:
        for fp in sorted(glob.glob(os.path.join(HERE, pat))):
            with open(fp, encoding="utf-8") as fh:
                for line in fh:
                    if "scorecard" not in line:
                        continue
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    body = rec.get("response_summary")
                    req = rec.get("request_body")
                    card = None
                    for candidate in (
                            req.get("card_id") if isinstance(req, dict) else None,
                            rec.get("card_id"),
                            body.get("card_id") if isinstance(body, dict) else None):
                        if isinstance(candidate, str) and candidate:
                            card = candidate
                            break
                    if card is None:
                        url = str(rec.get("url") or rec.get("path") or "")
                        blob = url
                        if body is not None:
                            blob += " " + json.dumps(body, ensure_ascii=False)
                        for tok in blob.replace("/", " ").replace('"', " ").split():
                            if len(tok) == 36 and tok.count("-") == 4:
                                card = tok
                                break
                    if card is None:
                        continue

                    status = rec.get("status") or rec.get("http_status") \
                        or rec.get("last_status")
                    if isinstance(status, int):
                        # `tries` records how many times that status was seen;
                        # a close that retried 8 times is stronger evidence
                        # than one that failed once, and the difference is
                        # exactly what the docstring above refuses to blur.
                        tries = rec.get("tries")
                        out.setdefault(card, []).extend(
                            [status] * (tries if isinstance(tries, int) and tries > 0
                                        else 1))
                    elif isinstance(body, dict) and "score" in body:
                        out.setdefault(card, []).append(200)
    return out


def build(obs: Optional[List[Dict[str, Any]]] = None,
          runs_dir: str = RUNS) -> Dict[str, Any]:
    """The column: one row per archived run, plus the totals."""
    if obs is None:
        obs = audit_zero.scorecard_observations()

    by_run: Dict[str, List[Dict[str, Any]]] = {}
    for o in obs:
        if o.get("run_id"):
            by_run.setdefault(o["run_id"], []).append(o)
    probes = card_probe_outcomes()

    rows: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(runs_dir, "*", "run.json"))):
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        if doc.get("kind") != "run":
            continue
        rid = doc.get("id")
        summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
        card = doc.get("card_id") or summary.get("card_id")

        seen = by_run.get(rid, [])
        if seen:
            scores = sorted({o["run_score"] for o in seen
                             if o.get("run_score") is not None})
            if len(scores) == 1:
                state, score, why = "recorded", scores[0], \
                    "archived scorecard body (%d observation(s))" % len(seen)
            elif len(scores) > 1:
                # Two archived answers is not an answer.  Publishing the
                # smaller, or hiding the row from the maximum, is how a 5.0
                # would sit inside a column that reports "max 0.0".
                state, score, why = "conflicting", None, \
                    ("%d observation(s) disagree: %s -- no value is published, "
                     "this needs an adjudication" % (len(seen), scores))
            else:
                state, score, why = "conflicting", None, \
                    ("%d observation(s) archived, none carrying a run score --"
                     " a body was kept but the number in it was not"
                     % len(seen))
            rows.append({
                "run_id": rid, "game_id": doc.get("game_id"),
                "model": doc.get("model"), "card_id": card,
                "state": state, "score": score, "source": why,
            })
            continue

        if card:
            statuses = probes.get(card, [])
            failures = [s for s in statuses if isinstance(s, int) and s >= 400]
            if not failures:
                # The label `unobtainable` asserts that the API was asked and
                # refused.  With nothing archived, it was not asked.
                rows.append({
                    "run_id": rid, "game_id": doc.get("game_id"),
                    "model": doc.get("model"), "card_id": card,
                    "state": "never_probed", "score": None,
                    "source": "card %s recorded, but no archived probe of it "
                              "failed (%d attempt(s) on record) -- nothing was "
                              "measured, so nothing is concluded"
                              % (card, len(statuses)),
                })
                continue
            rows.append({
                "run_id": rid, "game_id": doc.get("game_id"),
                "model": doc.get("model"), "card_id": card,
                "state": "unobtainable",
                "score": None,
                "source": "card probed %d time(s), statuses %s, %d refusal(s)"
                          " -- D-015 measured 8 retries of both GET and close "
                          "on two other cards and got 404 every time; for this "
                          "card that finding is applied, not repeated"
                          % (len(statuses), sorted(set(statuses)) or "unrecorded",
                             len(failures)),
            })
            continue

        rows.append({
            "run_id": rid, "game_id": doc.get("game_id"),
            "model": doc.get("model"), "card_id": None,
            "state": "absent",
            "score": None,
            "source": "no card_id was ever recorded for this run"
                      + ("; the run has no summary at all"
                         if not summary else ""),
        })

    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    # `state == "recorded"` is the only gate.  An earlier draft also required
    # `isinstance(r["score"], float)`, which meant a row whose archived bodies
    # disagreed -- and which therefore held a *list* -- was counted in
    # `recorded` and dropped from the maximum.  A 5.0 could sit in the record
    # while this column published "max 0.0".  Disagreement is now its own
    # state and never reaches here; if a non-number still does, it must break
    # the max rather than be filtered out of it.
    values = sorted({r["score"] for r in rows if r["state"] == "recorded"})

    return {
        "rows": rows,
        "counts": dict(sorted(counts.items())),
        "runs": len(rows),
        "distinct_recorded_scores": values,
        "max_recorded_score": max(values) if values else None,
        "note": "`unobtainable` and `absent` carry no number. They are not "
                "zero and must never be summarised as one -- that substitution "
                "is the error this column was built to end.",
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="A33 -- the baseline arm's score column")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    col = build()
    if args.json:
        print(json.dumps(col, indent=2, sort_keys=True))
        return 0

    print("A33 -- baseline arm score column, from archived scorecard bodies\n")
    print("   %-52s %-14s %s" % ("run_id", "state", "score"))
    for r in col["rows"]:
        print("   %-52s %-14s %s"
              % (r["run_id"][:52], r["state"],
                 r["score"] if r["state"] == "recorded" else "--"))
    print()
    print("   %s" % ", ".join("%s=%d" % kv for kv in col["counts"].items()))
    print("   distinct recorded scores ................... %s"
          % (col["distinct_recorded_scores"] or "none"))
    print("   max recorded score ......................... %s"
          % (col["max_recorded_score"]
             if col["max_recorded_score"] is not None else "no score was recorded"))
    print("\n   %s" % col["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
