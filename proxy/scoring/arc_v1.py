"""`arc_v1` -- the frozen scorer.

Phase 1's standing discipline is that the three arms share one shell: the same outer
loop, the same ledger format, and **the same scorer**. A scorer that drifted
between arms would make the arms' numbers incomparable, which is the one thing
the whole design is trying to buy.

So this file is frozen: `proxy/scoring/frozen.json` records the sha256 of its
source, `proxy.scoring.verify_frozen()` recomputes it, and a mismatch refuses
to score rather than scoring under a changed rule. Changing the scoring rule
means a new `scorer_id` and a new freeze record; it never means editing this
file in place, because runs already scored would then be unreproducible.

## What it does, and what it deliberately does not

It reports the **scorecard's own numbers** and reconciles them against the
ledger. It does **not** reimplement the ARC-AGI-3 percentage.

That restraint is evidential, not lazy. Every scorecard in this repository --
32 of them, four development-pile games, two models, two campaigns -- has
`levels_completed == 0` and `score == 0.0`. The per-level partial-credit
formula (the cards carry `level_scores` as floats and `level_baseline_actions`
alongside them, which suggests efficiency weighting) is therefore **not
determined by any evidence we hold**. A scorer that shipped a guess at it would
produce a plausible number with nothing behind it, and Phase 1's whole claim is
that conclusions come from the ledger. When a run finally completes a level,
`score.basis` says `scorecard` and the number is the API's; the formula stays
unimplemented until there is a corpus that pins it down.

## The upstream scorer

`Theoria.md` Phase 1 §5 says "冻结打分器原样接入" and `baseline-arms`'s
`SCHEMA_LOCATE.md` §2.4 identified the upstream `score_trajectories.py` as pure
offline Python. It is **not** vendored here, and that is a decision with three
reasons (see `proxy/DECISIONS.md` D-016), not an oversight. The registry in
`proxy/scoring/__init__.py` takes a second scorer by design: if that file is
ever adopted it registers beside this one, and every `run.json` already records
*which* scorer produced its number.
"""

from typing import Any, Dict, List, Optional

SCORER_ID = "arc_v1"
VERSION = "1.0.0"

#: Measured calibration, not assumption. Each entry names the evidence, because
#: a constant whose provenance is lost is a constant nobody dares change.
CALIBRATION = {
    "failed_requests_are_not_billed": {
        "value": True,
        "evidence": "baseline-arms BUDGET_REPORT §4 reported this on 4 "
                    "samples; proxy/tests/fixtures/scorecard_corpus.json "
                    "extends it to 32 closed scorecards across "
                    "ar25/g50t/sk48/tn36 and two models, in every one of which "
                    "total_actions equals the count of successful non-RESET "
                    "commands. The failed commands behind them were 400/500 -- "
                    "requests the server refused before executing.",
        "limit": "This is evidence that a REFUSED request is not billed. It is "
                 "not evidence that a semantically wasted action is free: a "
                 "click on empty space returns 200 and is billed.",
    },
    "total_actions_counts_successful_non_reset_commands": {
        "value": True,
        "evidence": "32/32 exact agreement, checked by "
                    "tests/test_scoring.py against "
                    "proxy/tests/fixtures/scorecard_corpus.json.",
        "limit": "The card also carries `resets`, which was 0 in all 32 "
                 "despite one RESET per run. RESET is therefore counted "
                 "somewhere else, or counts only re-RESETs; this scorer does "
                 "not model it and does not need to.",
    },
}


class CardView:
    """A scorecard, normalised, with the shape it arrived in recorded.

    Three shapes exist in this repository and a reader that guessed between
    them would be the bug: the live API's (`environments`), the mock's flat
    `score`, and the `cards` mapping an earlier reader anticipated. An
    unrecognised shape yields `shape == "unrecognised"` and no numbers -- a
    fabricated score here would defeat the entire reconciliation.
    """

    def __init__(self, raw: Any, game_id: Optional[str] = None):
        self.raw = raw
        self.game_id = game_id
        self.shape = "absent"
        #: True when the card covers more than one game or more than one run
        #: and the run being scored is only part of it. The card's *totals* are
        #: then not this run's numbers, and comparing them to one run's ledger
        #: would manufacture a mismatch on a perfectly good stream.
        self.scoped_to_run = False
        self.multi = False
        self.card_id: Optional[str] = None
        self.total_actions: Optional[int] = None
        self.score: Optional[float] = None
        self.levels_completed: Optional[int] = None
        self.level_count: Optional[int] = None
        self.game_ids: List[str] = []
        self.state: Optional[str] = None
        #: Places where the card's own totals do not add up. Pure arithmetic
        #: on the card itself -- it needs no knowledge of the scoring formula,
        #: and it is what catches a forger who edits one number.
        self.aggregate_errors: List[str] = []

        if not isinstance(raw, dict):
            return
        self.card_id = raw.get("card_id")

        environments = raw.get("environments")
        if isinstance(environments, list) and environments:
            self.shape = "arc_live"
            self.total_actions = _as_int(raw.get("total_actions"))
            self.score = _as_float(raw.get("score"))
            self.levels_completed = _as_int(raw.get("total_levels_completed"))
            self.level_count = _as_int(raw.get("total_levels"))
            envs = [e for e in environments if isinstance(e, dict)]
            for env in envs:
                if isinstance(env.get("id"), str):
                    self.game_ids.append(env["id"])

            # A card is per-scorecard, and one scorecard can cover several
            # games and several runs -- `environments[].runs` is a list in the
            # API's own shape. When the run being scored is identifiable inside
            # it, use *that* environment's numbers; the card totals are the
            # whole card's and are not this run's (battery D-4).
            mine = [e for e in envs if e.get("id") == game_id] if game_id else []
            self.multi = len(envs) > 1 or any(
                len(e.get("runs") or []) > 1 for e in envs)
            if mine:
                env = mine[0]
                self.scoped_to_run = True
                self.total_actions = _as_int(env.get("actions"))
                self.levels_completed = _as_int(env.get("levels_completed"))
                self.level_count = _as_int(env.get("level_count"))
                self.score = _as_float(env.get("score"))
                runs = env.get("runs")
                if isinstance(runs, list) and runs and isinstance(runs[0], dict):
                    self.state = runs[0].get("state")
            else:
                for env in envs:
                    if self.levels_completed is None:
                        self.levels_completed = _as_int(env.get("levels_completed"))
                    if self.level_count is None:
                        self.level_count = _as_int(env.get("level_count"))
                    runs = env.get("runs")
                    if isinstance(runs, list) and runs and isinstance(runs[0], dict):
                        self.state = runs[0].get("state")
            self._check_aggregates(raw, environments)
            return

        cards = raw.get("cards")
        if isinstance(cards, dict):
            self.shape = "cards_map"
            total = 0
            found = False
            for entry in cards.values():
                scores = (entry or {}).get("scores") or []
                numeric = [s for s in scores if isinstance(s, (int, float))
                           and not isinstance(s, bool)]
                if numeric:
                    total += max(numeric)
                    found = True
            self.score = float(total) if found else None
            self.total_actions = _as_int(raw.get("total_actions"))
            return

        if isinstance(raw.get("score"), (int, float)) and not isinstance(raw.get("score"), bool):
            self.shape = "flat"
            self.score = float(raw["score"])
            self.levels_completed = _as_int(raw.get("levels_completed"))
            self.total_actions = _as_int(raw.get("total_actions"))
            return

        self.shape = "unrecognised"

    def _check_aggregates(self, raw: Dict[str, Any], environments: List[Any]) -> None:
        envs = [e for e in environments if isinstance(e, dict)]

        def total(field: str) -> Optional[int]:
            values = [_as_int(e.get(field)) for e in envs]
            return None if any(v is None for v in values) else sum(values)

        for card_field, env_field in (("total_actions", "actions"),
                                      ("total_levels", "level_count"),
                                      ("total_levels_completed", "levels_completed")):
            declared = _as_int(raw.get(card_field))
            summed = total(env_field)
            if declared is not None and summed is not None and declared != summed:
                self.aggregate_errors.append(
                    "%s is %d but the environments sum to %d"
                    % (card_field, declared, summed))

        if len(envs) == 1:
            # With one environment the card's score IS that environment's
            # score. No knowledge of the aggregation rule is needed, and it is
            # what catches a forger who edits the headline number and leaves
            # the environment it summarises alone.
            top = _as_float(raw.get("score"))
            inner = _as_float(envs[0].get("score"))
            if top is not None and inner is not None and top != inner:
                self.aggregate_errors.append(
                    "score is %r but the single environment reports %r"
                    % (top, inner))

        declared = _as_int(raw.get("total_environments"))
        if declared is not None and declared != len(envs):
            self.aggregate_errors.append(
                "total_environments is %d but %d environments are listed"
                % (declared, len(envs)))

        completed = _as_int(raw.get("total_levels_completed"))
        available = _as_int(raw.get("total_levels"))
        if completed is not None and available is not None and completed > available:
            self.aggregate_errors.append(
                "total_levels_completed %d exceeds total_levels %d"
                % (completed, available))

        for env in envs:
            runs = env.get("runs")
            if not isinstance(runs, list):
                continue
            summed = sum(v for v in (_as_int(r.get("actions"))
                                     for r in runs if isinstance(r, dict))
                         if v is not None)
            declared = _as_int(env.get("actions"))
            if declared is not None and runs and declared != summed:
                self.aggregate_errors.append(
                    "environment %s reports %d actions but its runs sum to %d"
                    % (env.get("id"), declared, summed))

    def as_dict(self) -> Dict[str, Any]:
        return {"shape": self.shape, "card_id": self.card_id,
                "total_actions": self.total_actions, "score": self.score,
                "levels_completed": self.levels_completed,
                "level_count": self.level_count,
                "game_ids": self.game_ids, "state": self.state,
                "aggregate_errors": self.aggregate_errors or None}


class LedgerView:
    """What the run's own records say happened."""

    def __init__(self, records: List[Dict[str, Any]]):
        steps = sorted([r for r in records if r.get("event") == "env_step"],
                       key=lambda r: r.get("step_idx", 0))
        self.steps = steps
        self.game_ids = sorted({r.get("game_id") for r in steps
                                if isinstance(r.get("game_id"), str)})
        self.card_ids = sorted({r.get("card_id") for r in steps
                                if isinstance(r.get("card_id"), str)})

        #: Places the stream is not readable rather than not correct. Each one
        #: turns a check into UNDETERMINED instead of quietly deciding it: a
        #: record the scorer cannot classify must not be classified anyway.
        self.malformed: List[str] = []

        self.resets = 0
        self.actions_ok = 0
        self.actions_failed = 0
        self.actions_refused = 0
        self.status_missing = 0
        for record in steps:
            name = (record.get("action") or {}).get("name")
            decision = (record.get("guard") or {}).get("decision")
            if decision not in ("allow", "deny"):
                # Absent, or a word nobody defined. The earlier version read
                # anything that was not the literal "deny" as allowed, so a
                # typo silently promoted a refusal into a played action.
                self.malformed.append(
                    "step %s has guard.decision %r, which is neither allow nor "
                    "deny" % (record.get("step_idx"), decision))
                continue
            status = (record.get("http") or {}).get("status")
            if decision == "deny":
                self.actions_refused += 1
                continue
            if status is None:
                self.status_missing += 1
                continue
            ok = status == 200
            if name == "RESET":
                self.resets += 1 if ok else 0
            elif ok:
                self.actions_ok += 1
            else:
                self.actions_failed += 1

        # The last value, not the biggest one. `levels_completed` is what the
        # environment reported at that step, and a mid-run RESET reports zero
        # again -- `max()` would hold the high-water mark while the scorecard
        # reported the final figure, and call the difference a mismatch.
        self.levels_reported = 0
        self.levels_completed = 0
        previous: Optional[int] = None
        for record in steps:
            raw = record.get("levels_completed")
            if raw is None:
                continue
            value = _as_int(raw)
            if value is None:
                self.malformed.append(
                    "step %s has a non-integer levels_completed %r"
                    % (record.get("step_idx"), raw))
                continue
            self.levels_reported += 1
            if previous is not None and value < previous:
                self.malformed.append(
                    "levels_completed went backwards at step %s (%d -> %d); the "
                    "level derivation assumes it only rises"
                    % (record.get("step_idx"), previous, value))
            previous = value
            self.levels_completed = value

        # How many levels the game has. The live API answers this as
        # `win_levels` on every command response and nowhere else, so it lives
        # in `env_step.response`. Without it the ledger alone cannot express a
        # score as a fraction, and Phase 1 says conclusions come from the
        # ledger.
        self.level_count: Optional[int] = None
        for record in steps:
            response = record.get("response")
            if isinstance(response, dict):
                value = _as_int(response.get("win_levels"))
                if value:
                    self.level_count = value
                    break
        self.level_boundaries = sum(1 for r in steps if r.get("level_boundary"))
        scores = [r.get("score") for r in steps
                  if isinstance(r.get("score"), int) and not isinstance(r.get("score"), bool)]
        self.max_step_score = max(scores) if scores else None
        ends = [r for r in records if r.get("event") == "run_end"]
        self.run_end = ends[-1] if ends else None
        self.n_run_end = len(ends)
        starts = [r for r in records if r.get("event") == "run_start"]
        self.run_start = starts[0] if starts else None
        self.model_calls = sum(1 for r in records if r.get("event") == "model_call")
        #: One run is one arm playing one game once. More than one arm in a run
        #: means somebody appended records to somebody else's run, which is how
        #: a failing reconciliation was whitewashed (RED-38).
        self.arms = sorted({r.get("arm") for r in records
                            if isinstance(r.get("arm"), str)})

    def as_dict(self) -> Dict[str, Any]:
        return {"steps": len(self.steps), "resets": self.resets,
                "level_count": self.level_count,
                "actions_ok": self.actions_ok,
                "actions_failed": self.actions_failed,
                "actions_refused": self.actions_refused,
                "status_missing": self.status_missing,
                "levels_completed": self.levels_completed,
                "levels_reported": self.levels_reported,
                "level_boundaries": self.level_boundaries,
                "max_step_score": self.max_step_score,
                "model_calls": self.model_calls,
                "arms": self.arms,
                "malformed": self.malformed or None,
                "game_ids": self.game_ids, "card_ids": self.card_ids}


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and value != int(value):
        return None
    return int(value)


def _as_float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _check(cid: str, claim: str, verdict: str, **detail: Any) -> Dict[str, Any]:
    record = {"id": cid, "claim": claim, "verdict": verdict}
    record.update(detail)
    return record


def score(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Score one run and reconcile it. Pure: records in, report out.

    The verdict is one of three, and the third one matters:

      PASS           every check that could be evaluated agreed
      FAIL           a check disagreed -- the ledger is not a faithful record
      UNDETERMINED   the obligation could not be discharged at all, usually
                     because the scorecard was never captured

    UNDETERMINED is not PASS. baseline-arms lost 22 of 23 scorecards to a
    transient 404 and the loss was silent, so Phase 1's reconciliation
    obligation was quietly not being performed. A scorer that returned PASS for
    "nothing to compare" would reproduce exactly that.
    """
    led = LedgerView(records)
    game_id = led.game_ids[0] if len(led.game_ids) == 1 else None
    card = CardView((led.run_end or {}).get("scorecard"), game_id=game_id)

    checks: List[Dict[str, Any]] = []

    # -- is this stream even readable? -------------------------------------
    #
    # These run first and their failure is not a judgement about the game, it
    # is a judgement about the file. A stream that does not survive the canon
    # cannot be reconciled, and reconciling it anyway is how a fabricated run
    # gets a verdict (RED-39, RED-41).
    from ..tools.validate_ledger import validate_records
    structural = validate_records(records, subset=True)
    checks.append(_check(
        "S-12", "the records are canonical and internally consistent",
        "PASS" if not structural else "FAIL",
        problems=[{"line": p["line"], "kind": p["kind"]} for p in structural[:10]] or None,
        n_problems=len(structural)))

    checks.append(_check(
        "S-11", "the run belongs to exactly one arm",
        "PASS" if len(led.arms) == 1 else "FAIL",
        arms=led.arms,
        note="one run is one arm playing one game once; records from a second "
             "arm under the same run_id are somebody appending to somebody "
             "else's run"))

    if led.malformed:
        checks.append(_check(
            "S-13", "every step can be classified", "UNDETERMINED",
            detail=led.malformed[:10], n=len(led.malformed)))
    else:
        checks.append(_check("S-13", "every step can be classified", "PASS"))

    if card.shape in ("absent", "unrecognised"):
        checks.append(_check(
            "S-0", "a scorecard was captured for this run", "UNDETERMINED",
            detail="scorecard shape is %r; the score cannot be reconciled "
                   "against the API. A closed card cannot be re-fetched, so "
                   "this is not recoverable after the fact." % card.shape))
    else:
        checks.append(_check("S-0", "a scorecard was captured for this run",
                             "PASS", shape=card.shape))

        if card.total_actions is None:
            checks.append(_check(
                "S-1", "scorecard total_actions == successful non-RESET commands",
                "UNDETERMINED", detail="the card carries no total_actions"))
        elif led.status_missing:
            checks.append(_check(
                "S-1", "scorecard total_actions == successful non-RESET commands",
                "UNDETERMINED",
                detail="%d step(s) carry no http.status, so whether they "
                       "succeeded is not recorded. Counting them either way "
                       "would be inventing the answer." % led.status_missing))
        elif card.multi and not card.scoped_to_run:
            checks.append(_check(
                "S-1", "scorecard total_actions == successful non-RESET commands",
                "UNDETERMINED",
                detail="the card covers more than one game or run and this "
                       "run is not identifiable inside it, so its totals are "
                       "not this run's numbers"))
        else:
            agree = card.total_actions == led.actions_ok
            checks.append(_check(
                "S-1", "scorecard total_actions == successful non-RESET commands",
                "PASS" if agree else "FAIL",
                scorecard=card.total_actions, ledger=led.actions_ok,
                note="calibrated: refused 400/500 requests are not billed and "
                     "RESET is counted separately (CALIBRATION)"))

        if card.levels_completed is None:
            checks.append(_check("S-2", "scorecard levels_completed == ledger's",
                                 "UNDETERMINED",
                                 detail="the card carries no levels_completed"))
        else:
            agree = card.levels_completed == led.levels_completed
            checks.append(_check(
                "S-2", "scorecard levels_completed == ledger's",
                "PASS" if agree else "FAIL",
                scorecard=card.levels_completed, ledger=led.levels_completed))

        if card.score is None or card.levels_completed is None:
            checks.append(_check(
                "S-3", "a positive score iff a level was completed",
                "UNDETERMINED", detail="score or levels_completed missing"))
        else:
            consistent = (card.score > 0) == (card.levels_completed > 0)
            checks.append(_check(
                "S-3", "a positive score iff a level was completed",
                "PASS" if consistent else "FAIL",
                score=card.score, levels_completed=card.levels_completed,
                note="the only relation between score and levels this corpus "
                     "pins down; the partial-credit formula is not "
                     "reimplemented here"))

        if card.score is not None and card.levels_completed is not None:
            # A bound that holds under either reading of `score`, so it needs
            # no knowledge of the partial-credit formula: as a fraction it
            # cannot exceed 1, and as a count it cannot exceed the levels
            # actually completed. A forger who edits the score and leaves the
            # rest of the card alone lands outside both.
            bound = max(1.0, float(card.levels_completed))
            checks.append(_check(
                "S-9", "the card's score is within any reading of it",
                "PASS" if 0.0 <= card.score <= bound else "FAIL",
                score=card.score, bound=bound,
                levels_completed=card.levels_completed))

        if card.aggregate_errors:
            checks.append(_check(
                "S-10", "the card's totals agree with its own environments",
                "FAIL", errors=card.aggregate_errors))
        elif card.shape == "arc_live":
            checks.append(_check(
                "S-10", "the card's totals agree with its own environments",
                "PASS"))

        if card.level_count is not None and led.level_count is not None:
            agree = card.level_count == led.level_count
            checks.append(_check(
                "S-8", "the card and the step responses agree on the level count",
                "PASS" if agree else "FAIL",
                scorecard=card.level_count, ledger=led.level_count,
                note="the ledger's copy is the API's `win_levels`, recorded on "
                     "every command response"))

        if card.game_ids and led.game_ids:
            # The ledger's games must be *among* the card's, not equal to them:
            # one scorecard legitimately covers several games, and demanding
            # equality turned that into a forgery signature on a clean stream.
            covered = set(led.game_ids) <= set(card.game_ids)
            checks.append(_check(
                "S-4", "the scorecard covers the game the ledger played",
                "PASS" if covered else "FAIL",
                scorecard=card.game_ids, ledger=led.game_ids))

        if card.card_id and led.card_ids:
            same = card.card_id in led.card_ids
            checks.append(_check(
                "S-5", "the steps counted against this very card",
                "PASS" if same else "FAIL",
                scorecard=card.card_id, ledger=led.card_ids))

    if not led.levels_reported:
        # Both sides are zero and the check has verified nothing. Saying PASS
        # here is how a check earns a reputation it has not paid for.
        checks.append(_check(
            "S-6", "level boundaries recompute from the step sequence",
            "UNDETERMINED",
            detail="no step reported a levels_completed, so there is nothing "
                   "to recompute"))
    else:
        boundaries_agree = led.level_boundaries == led.levels_completed
        checks.append(_check(
            "S-6", "level boundaries recompute from the step sequence",
            "PASS" if boundaries_agree else "FAIL",
            boundaries=led.level_boundaries,
            levels_completed=led.levels_completed))

    if led.n_run_end > 1:
        checks.append(_check(
            "S-7", "the run has exactly one run_end", "FAIL",
            run_end_records=led.n_run_end,
            note="a second run_end would let a later record decide the score; "
                 "the ledger is append-only, so this is a forgery signature."))
    elif led.n_run_end == 1:
        checks.append(_check("S-7", "the run has exactly one run_end", "PASS"))
    else:
        checks.append(_check("S-7", "the run has exactly one run_end",
                             "UNDETERMINED", detail="the run never closed"))

    failed = [c for c in checks if c["verdict"] == "FAIL"]
    undetermined = [c for c in checks if c["verdict"] == "UNDETERMINED"]
    verdict = "FAIL" if failed else ("UNDETERMINED" if undetermined else "PASS")

    return {
        "scorer": {"id": SCORER_ID, "version": VERSION},
        "game_ids": led.game_ids,
        "score": {
            "value": card.score,
            "basis": "scorecard" if card.score is not None else "unavailable",
            "levels_completed": (card.levels_completed
                                 if card.levels_completed is not None
                                 else led.levels_completed),
            "level_count": (card.level_count if card.level_count is not None
                            else led.level_count),
            "partial_credit_formula": "not reimplemented; see the module "
                                      "docstring -- no scorecard in this "
                                      "corpus has a completed level",
        },
        "scorecard": card.as_dict(),
        "ledger": led.as_dict(),
        "checks": checks,
        "verdict": verdict,
        "failed_checks": [c["id"] for c in failed] or None,
        "undetermined_checks": [c["id"] for c in undetermined] or None,
    }
