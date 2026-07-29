"""The development-pile campaign: many legs, one budget, books that travel.

`harness/run.py` plays one game until something stops it -- an action budget, a
cost ceiling, a wall clock. That is a *leg*, not a game: ARC games have seven or
eight levels and a leg that ends at level 2 has not finished anything. This
module is the loop above that one. It runs legs, carries the two books from each
leg into the next, and keeps the accounts that decide when to stop.

## What it is for

The claim being measured is C3, transfer: the same `theory.dsl` against a
different computed problem. That claim needs a level boundary that actually
happened, with the books that crossed it hashed on both sides. `inner/levels.py`
handles the boundary inside a run; this module handles it across runs, which is
the case that matters when a leg dies with levels left to play.

The second thing it is for is figure 2. The per-turn series -- theorize rounds,
the seven surprise counts, cost -- is written per leg by `armtools/archive.py`;
what the figure needs is those series *concatenated in play order with the level
boundaries marked*, which is a thing only a campaign knows.

## The budget, and why it is written here rather than passed in

The fleet shares one pool with a real ceiling, and RES-1 is the only member
permitted to draw on it (`monitor/CHARTER.md`). The package authorised for this
campaign is written down here so that a run and its authorisation cannot drift
apart:

* **$200** for the whole campaign;
* **$60** for any one game;
* **$25** for any one reservation -- draw in batches, never lock the shared
  pool up in one claim;
* **40 successful actions** per level.

`spend.plan_caps` converts the action figure into the pool's own unit (outbound
HTTP requests, not successful actions) and refuses if the *global* free headroom
cannot cover it. Raising any of these is a human act, not a code change:
`proxy/spend_policy.json` says so and this module does not touch it.

## Stopping

Four conditions, any one of which ends the campaign, all of them recorded with
the state that triggered them:

* the spend gate trips or becomes unavailable;
* a game exceeds its $60;
* the campaign exceeds its $200;
* three consecutive legs make **zero progress** -- no level completed and no
  new surprise kind seen. Three, because one dead leg is noise and two is bad
  luck; a campaign that has learned nothing in three is spending money to
  confirm it cannot.

A stop is not a failure. The order this campaign is run under says it plainly:
一局打不完就交阶段结果，绝不为了跑完而降低记录标准 -- deliver the partial
result, never lower the recording standard to finish.

## Checkpoints

Every leg is written to disk the moment it ends, atomically (write a temp file
in the same directory, then replace). `baseline-arms/harness/campaign.py` does
the same and for the same reason: a campaign is hours long, the session running
it will be interrupted, and a campaign that only records its result at the end
records nothing. Only what is on disk exists.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import _bootstrap                                      # noqa: F401  (sys.path)

from harness import spend as spend_mod
from harness.run import play
from inner.loop import TheoriaArm

#: The arm's directory. Deliberately not `harness.run.ARM`, which is the arm's
#: *name* (`"theoria"`, the string that goes in every ledger record) -- two
#: different things that read the same at a glance.
HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
REPO = os.path.dirname(ARM)

#: The authorised package. See the module docstring; changing these is a
#: decision about money, so they are named constants rather than defaults
#: buried in a signature.
CAMPAIGN_USD = 200.0
GAME_USD = 60.0
LEG_USD_CAP = 25.0
ACTIONS_PER_LEVEL = 40

#: `plan_caps` computes `usd_cap = cost_ceiling_usd + MODEL_CALL_CEILING_USD`,
#: so the per-leg cost ceiling has to leave room for that last call to land on
#: top of a full ceiling. 20 + 4 = 24, under the $25 per-reservation limit.
LEG_COST_CEILING_USD = LEG_USD_CAP - spend_mod.MODEL_CALL_CEILING_USD - 1.0

#: Legs in a row that may make no progress before the campaign gives up.
ZERO_PROGRESS_LIMIT = 3

#: The development pile, and nothing else, ever. `arc-recon/data/piles.json` is
#: the authority; this list is checked against it at startup rather than
#: trusted, because a typo here would be a sealed-pile contact and that is an
#: incident, not a bug.
DEV_PILE = ("g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99", "ar25-0c556536")


class CampaignStopped(Exception):
    """Raised to end the campaign, carrying the reason and the accounts."""

    def __init__(self, reason: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


class GameStopped(CampaignStopped):
    """Raised to end one game and move to the next.

    Separate from `CampaignStopped` because the two ceilings mean different
    things. A game that has spent its $60 has finished being measured; the
    campaign has three more games and $140 and should get on with them. Folding
    the two together -- which this module did until a test caught it -- makes
    the *first* game to exhaust its budget silently end the whole campaign, and
    the report would say "stopped: g50t has spent its $60" as though that were
    the campaign's verdict rather than one game's.
    """


def assert_dev_pile(game_ids) -> None:
    """Refuse to play anything the cut did not put in the development pile.

    Checked against `piles.json` itself, not against `DEV_PILE`: a constant in
    this file could be edited by the same hand that edited the caller, and the
    sealed pile's guarantee is worth more than one round trip to disk.
    """
    path = os.path.join(REPO, "arc-recon", "data", "piles.json")
    with open(path, encoding="utf-8") as fh:
        piles = json.load(fh)
    allowed = set(piles["dev_pile"])
    sealed = set(piles["sealed_pile"])
    for game_id in game_ids:
        if game_id in sealed:
            raise CampaignStopped(
                "sealed pile contact refused: %s is sealed. This is an "
                "incident if it ever reaches the network." % game_id,
                {"game_id": game_id})
        if game_id not in allowed:
            raise CampaignStopped(
                "%s is in neither pile; the cut does not know this game"
                % game_id, {"game_id": game_id})


def _leg_cost(summary: Dict[str, Any]) -> tuple:
    """What one leg cost, and both of the numbers that answer it.

    `D-P8-015` keeps two cost figures on purpose -- the CLI's own report and the
    price table's -- because that disagreement is the only reason INC-TA-003
    (1-hour cache writes under-billed by 6.8%) was ever findable. This function
    keeps that discipline and adds the one that actually governs.

    Three numbers are in play:

    * `desk.cli_cost_usd` -- what `claude -p` said it charged.
    * `desk.spend_gate.usd_charged` -- what the shared pool actually booked.
      This one charges `MODEL_CALL_CEILING_USD` for a call it cannot price
      (`price_of`, never $0), so it **cannot under-count**.
    * the larger of the two, which is what the ceilings are checked against.

    The ceiling takes the max rather than picking a favourite. A budget ceiling
    that trusts the smaller of two disagreeing figures is a ceiling that can be
    walked past by whichever accounting happens to be broken -- and one of them
    is known to be, by 6.8%, in the direction that under-reports.

    This replaces a read of `desk["cost_usd"]`, a key `ModelDesk.summary()` has
    never emitted. It returned `None` every time, so `usd` was always 0.0, the
    per-game and per-campaign totals never moved, and the $60/$200 ceilings
    could not trip. No test caught it because every test in `test_campaign.py`
    replaces `run_leg` wholesale.
    """
    desk = summary.get("desk") or {}
    cli = desk.get("cli_cost_usd")
    gate = ((desk.get("spend_gate") or {}) or {}).get("usd_charged")

    cli_usd = float(cli) if cli is not None else None
    gate_usd = float(gate) if gate is not None else None

    known = [v for v in (cli_usd, gate_usd) if v is not None]
    governing = max(known) if known else 0.0

    return governing, {
        "cli_cost_usd": cli_usd,
        "gate_usd_charged": gate_usd,
        "governing_usd": governing,
        "governing_source": (
            "no-cost-reported" if not known
            else "gate" if gate_usd is not None and governing == gate_usd
            else "cli"),
        # An absent gate figure on a leg that spent anything means the desk ran
        # without a claim on the pool, which `ModelDesk.binding()` is supposed
        # to make impossible. Recorded rather than asserted: this is the
        # accounting, not the enforcement.
        "gate_absent": gate_usd is None,
    }


class Campaign:
    """Legs, in order, with the books carried between them."""

    def __init__(self, *, prompt_id: str, out_dir: str,
                 games=DEV_PILE,
                 campaign_usd: float = CAMPAIGN_USD,
                 game_usd: float = GAME_USD,
                 actions_per_level: int = ACTIONS_PER_LEVEL,
                 model: str = "claude-opus-5",
                 offline: bool = False,
                 env_upstream: Optional[str] = None,
                 env_key: Optional[str] = None,
                 require_key: bool = True,
                 spend_gate=None,
                 expect_pool: Optional[Dict[str, Any]] = None):
        # `spend_gate`/`expect_pool` exist so a whole multi-leg campaign can be
        # rehearsed against a scratch pool in a temp directory. Without them
        # `Campaign` could only ever draw on `proxy/var/spend_gate.jsonl`, so
        # the only way to exercise `run_leg` was to write fictional reservations
        # into the pool the fleet actually shares -- which is precisely what
        # `harness/run.py --pool` was added to prevent. A campaign is the one
        # caller that most needs a dry run and was the one that could not have
        # one.
        assert_dev_pile(games)
        self.prompt_id = prompt_id
        self.games = list(games)
        self.campaign_usd = campaign_usd
        self.game_usd = game_usd
        self.actions_per_level = actions_per_level
        self.model = model
        self.offline = offline
        self.env_upstream = env_upstream
        self.env_key = env_key
        self.require_key = require_key
        self.spend_gate = spend_gate
        self.expect_pool = expect_pool

        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)
        self.state_path = os.path.join(self.out_dir, "campaign.json")

        self.legs: List[Dict[str, Any]] = []
        self.spent_usd = 0.0
        self.by_game: Dict[str, float] = {g: 0.0 for g in self.games}
        self.zero_progress = 0
        self.stopped: Optional[Dict[str, Any]] = None
        self.started = time.time()

    # -- accounts ----------------------------------------------------------
    def _game_headroom(self, game_id: str) -> float:
        return min(self.game_usd - self.by_game.get(game_id, 0.0),
                   self.campaign_usd - self.spent_usd)

    def _check_campaign_budget(self) -> None:
        """The ceiling that ends everything. Checked before a leg *and* after
        one: a campaign whose last leg overran, and which then ran out of games
        to play, would otherwise finish with `stopped: null` and a report that
        never mentions it went over."""
        if self.spent_usd >= self.campaign_usd:
            raise CampaignStopped(
                "campaign budget spent: $%.2f of $%.2f"
                % (self.spent_usd, self.campaign_usd),
                {"spent_usd": self.spent_usd})

    def _check_budget(self, game_id: str) -> None:
        self._check_campaign_budget()
        if self.by_game.get(game_id, 0.0) >= self.game_usd:
            raise GameStopped(
                "%s has spent its $%.2f" % (game_id, self.game_usd),
                {"game_id": game_id, "spent_usd": self.by_game[game_id]})

    def _progress(self, summary: Dict[str, Any], seen_kinds: set) -> bool:
        """Did this leg learn anything?

        Two ways to count, because either alone is a bad measure. A level
        completed is progress by anyone's definition. A surprise *kind* not
        seen before is progress too: it is a fact about the world the arm did
        not have, and on a game nobody has ever cleared a level of, insisting
        on level completions would end the campaign before it measured
        anything -- which is exactly the outcome the bill-shape figure needs
        the campaign NOT to have.
        """
        levels = (summary.get("levels") or {}).get("boundaries", 0)
        kinds = {k for k, n in
                 ((summary.get("surprises") or {}).get("by_kind") or {}).items()
                 if n}
        fresh = kinds - seen_kinds
        seen_kinds |= kinds
        return bool(levels) or bool(fresh)

    # -- one leg -----------------------------------------------------------
    def _leg_slug(self, game_id: str, index: int) -> str:
        """A slug with no game in it.

        This used to be `<utc>-<stem>-leg<nn>`, e.g. `...-g50t-leg01`, which put
        the game stem into the run directory path -- and therefore into every
        absolute path under it: `candidates.jsonl`, `books/generated/*.lean`,
        the transcript directory. That matters because several of those paths
        reach the model:

        * `world/adapt.py` records `{"error", "traceback"}` for an engine that
          raises and `evidence_brief` dumps the report into the prompt; an
          `OSError` message carries the path it failed on. Forcing a
          candidate-write failure put six occurrences of `g50t` into a
          20,975-char prompt.
        * `books.compile_all` stringifies write errors into `compile_errors`,
          which is also concatenated into the prompt.
        * Lean prefixes every diagnostic with the absolute source path, and a
          `proof_failure` payload carries `stderr` verbatim into the next
          prompt.

        `Theoria.md:353` is a hard rule -- 游戏 ID 永不进模型上下文 -- so the
        cheapest place to keep it is to never put the id in a path. The game is
        still recorded, in `run.json`, the ledger and `campaign.json`, none of
        which the desk can read. `ModelDesk.forbid_in_prompt` is the backstop
        for the channels this does not anticipate.

        The leg index is per game, so `<utc>-leg01` can repeat across games in
        one campaign; the timestamp is what separates them, and `campaign.json`
        maps every slug to its game.
        """
        return "%s-leg%02d" % (
            time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), index)

    def run_leg(self, game_id: str, index: int,
                seed_books: Optional[str]) -> Dict[str, Any]:
        """One `play()`, sized so its reservation cannot exceed the leg cap."""
        self._check_budget(game_id)
        slug = self._leg_slug(game_id, index)
        headroom = self._game_headroom(game_id)
        ceiling = min(LEG_COST_CEILING_USD, max(0.0, headroom - 1.0))
        if ceiling <= 0:
            raise GameStopped(
                "no headroom left for %s: $%.2f" % (game_id, headroom),
                {"game_id": game_id, "headroom_usd": headroom})

        caps = spend_mod.plan_caps(
            actions=self.actions_per_level,
            commands=2000,
            cost_ceiling_usd=ceiling,
            gate=self.spend_gate)
        campaign_name = spend_mod.campaign_name(
            prompt_id=self.prompt_id, game_id=game_id, slug=slug)

        def factory(env_base, run):
            return TheoriaArm(env_base=env_base, run=run, game_id=game_id,
                              budget_actions=self.actions_per_level,
                              offline=self.offline, model=self.model,
                              cost_ceiling_usd=ceiling,
                              seed_books=seed_books)

        kwargs: Dict[str, Any] = {"caps": caps, "campaign": campaign_name}
        if self.env_upstream:
            kwargs["env_upstream"] = self.env_upstream
        if self.env_key is not None:
            kwargs["env_key"] = self.env_key
        kwargs["require_key"] = self.require_key
        if self.spend_gate is not None:
            kwargs["spend_gate"] = self.spend_gate
        if self.expect_pool is not None:
            kwargs["expect_pool"] = self.expect_pool

        summary = play(game_id, slug, factory, **kwargs)

        # The per-turn series, written while the leg's ledger is still the only
        # thing that knows what happened. `armtools.archive.write_turn_series`
        # is the one implementation of this reduction and it is not repeated
        # here -- a second implementation of the input to a Phase 4 primary
        # endpoint would be a second definition of the endpoint.
        #
        # Not fatal if it raises: a leg that played is worth recording even if
        # the reduction over it fails, and the failure is a fact about the
        # archive step rather than about the leg.
        series_error = None
        try:
            from armtools.archive import write_turn_series    # noqa: PLC0415
            write_turn_series(os.path.join(ARM, "runs", slug))
        except Exception as exc:                       # noqa: BLE001
            series_error = "%s: %s" % (type(exc).__name__, exc)

        usd, accounting = _leg_cost(summary)
        leg = {
            "index": index,
            "game_id": game_id,
            "slug": slug,
            "campaign": campaign_name,
            "seed_books": seed_books,
            "carried": summary.get("carried_books"),
            "usd": usd,
            "cost_accounting": accounting,
            "turn_series_error": series_error,
            "levels": summary.get("levels"),
            "surprises": summary.get("surprises"),
            "theorize_rounds": summary.get("theorize_rounds"),
            "outcome": summary.get("outcome"),
            "stopped_because": summary.get("stopped_because"),
            "actions_ok": (summary.get("budget") or {}).get("actions_ok"),
            "run_dir": os.path.join(ARM, "runs", slug),
            "books_dir": os.path.join(ARM, "runs", slug, "books"),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.spent_usd += usd
        self.by_game[game_id] = self.by_game.get(game_id, 0.0) + usd
        return leg

    # -- the campaign ------------------------------------------------------
    def run(self, max_legs_per_game: int = 3) -> Dict[str, Any]:
        seen_kinds: set = set()
        try:
            for game_id in self.games:
                try:
                    self._run_game(game_id, max_legs_per_game, seen_kinds)
                except GameStopped as stop:
                    # One game finished being measured; the campaign has more.
                    self.legs.append({"game_id": game_id, "event": "game_end",
                                      "reason": stop.reason,
                                      "detail": stop.detail})
                    self.save()
                    continue
        except CampaignStopped as stop:
            self.stopped = {"reason": stop.reason, "detail": stop.detail}
        except spend_mod.SpendGateError as stop:
            # The gate is the one authority that outranks the plan. Red means
            # stop, not retry and not re-reserve smaller.
            self.stopped = {"reason": "spend gate: %s: %s"
                                      % (type(stop).__name__, stop),
                            "detail": {"gate": True}}
        self.save()
        return self.report()

    def _run_game(self, game_id: str, max_legs_per_game: int,
                  seen_kinds: set) -> None:
        """One game's legs. Raises `GameStopped` to move on, `CampaignStopped`
        to end everything."""
        # The books travel *within* a game. They are deliberately not carried
        # across games: two ARC games are two different worlds, and a manual
        # for one is not evidence about the other. C3's claim is
        # level-to-level (`Theoria.md` C3, `D-A3-002`).
        seed: Optional[str] = None
        for index in range(1, max_legs_per_game + 1):
            try:
                leg = self.run_leg(game_id, index, seed)
            except (CampaignStopped, spend_mod.SpendGateError):
                # The two that mean something. Re-raised to `run`, which knows
                # the difference between ending a game and ending everything.
                raise
            except BaseException as exc:                # noqa: BLE001
                # Everything else -- an ArcError, a transport failure, a bug in
                # a beat. Previously these escaped `run`'s handler and killed
                # the campaign without a final `save()`, losing the record of
                # every leg that had already been paid for.
                #
                # A campaign is hours long and legs cost real money; one leg
                # dying is a fact to record and move past, not a reason to
                # discard the ones that worked. Recorded as a leg-shaped entry
                # so `report()` and the figure pipeline see it, and counted as
                # zero progress so a game that only ever raises still trips the
                # zero-progress limit rather than retrying forever.
                self.legs.append({
                    "index": index, "game_id": game_id, "event": "leg_failed",
                    "error": "%s: %s" % (type(exc).__name__, exc),
                    "usd": 0.0,
                    "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                self.save()
                self.zero_progress += 1
                if self.zero_progress >= ZERO_PROGRESS_LIMIT:
                    raise CampaignStopped(
                        "%d legs in a row made no progress; the last %d ended "
                        "in an exception" % (ZERO_PROGRESS_LIMIT,
                                             self.zero_progress),
                        {"game_id": game_id, "last_error": str(exc)})
                continue
            self.legs.append(leg)
            self.save()

            # After the leg, not only before it: a campaign whose last leg
            # overran and which then ran out of games to play would otherwise
            # finish with `stopped: null` and never mention it went over.
            self._check_campaign_budget()

            if not self._progress({"levels": leg["levels"],
                                   "surprises": leg["surprises"]}, seen_kinds):
                self.zero_progress += 1
                if self.zero_progress >= ZERO_PROGRESS_LIMIT:
                    raise CampaignStopped(
                        "%d legs in a row completed no level and met no new "
                        "kind of surprise" % ZERO_PROGRESS_LIMIT,
                        {"game_id": game_id})
            else:
                self.zero_progress = 0

            # Only carry books that a *finished* leg wrote. A leg that died
            # mid-theorize can leave a half-written manual, and seeding the
            # next leg from it would launder a broken book into a transfer
            # claim.
            if leg["outcome"] not in ("reset_failed", "level_advance_failed"):
                seed = leg["books_dir"]

            if leg["outcome"] in ("WIN", "GAME_OVER"):
                return

    # -- the record --------------------------------------------------------
    def report(self) -> Dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "elapsed_s": round(time.time() - self.started, 1),
            "games": self.games,
            "budget": {"campaign_usd": self.campaign_usd,
                       "game_usd": self.game_usd,
                       "leg_usd_cap": LEG_USD_CAP,
                       "actions_per_level": self.actions_per_level},
            "spent_usd": round(self.spent_usd, 6),
            "by_game": {k: round(v, 6) for k, v in self.by_game.items()},
            "legs": self.legs,
            "levels_completed": sum(
                (leg.get("levels") or {}).get("boundaries", 0)
                for leg in self.legs),
            "stopped": self.stopped,
            "zero_progress_streak": self.zero_progress,
        }

    # -- figure 2's raw material -------------------------------------------
    def campaign_series(self) -> Dict[str, Any]:
        """Every leg's turn series, concatenated in play order.

        `armtools.archive.write_turn_series` writes one row per turn per leg:
        cost, theorize rounds, and all seven surprise counts. Those are the
        three columns the A3 order calls figure 2's entire raw material. What a
        single leg cannot supply is the thing that makes them a *campaign*
        curve: play order across legs, and where the level boundaries fell.

        Two ordinals, kept apart on purpose:

        * `turn` -- the leg's own turn number, which restarts at each leg.
        * `campaign_turn` -- a dense ordinal across the whole campaign, which
          is the x-axis the bill-shape claim is about. C2 predicts 前重后轻,
          front-heavy then light, and that shape only means anything against a
          clock that does not restart every time a leg dies.

        The front-load index is deliberately NOT computed here. It is E2 in
        `battery/metrics/economy.py`, one of Phase 4's three primary endpoints,
        and the figures track's rule is right: a second implementation of a
        primary endpoint is a second definition of it. This assembles the input
        and stops.

        Legs that failed appear as rows-less entries rather than being dropped.
        A campaign that spent money on a leg which then produced no series is
        not the same thing as a campaign with fewer legs, and the difference is
        exactly the kind that a concatenation quietly destroys.
        """
        rows: List[Dict[str, Any]] = []
        legs: List[Dict[str, Any]] = []
        campaign_turn = 0

        for leg in self.legs:
            slug = leg.get("slug")
            if not slug:
                # A `game_end` or `leg_failed` marker, not a leg that played.
                legs.append({"event": leg.get("event"),
                             "game_id": leg.get("game_id"),
                             "error": leg.get("error"), "rows": 0})
                continue

            path = os.path.join(ARM, "runs", slug, "turn_series.json")
            doc = None
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as fh:
                        doc = json.load(fh)
                except Exception as exc:               # noqa: BLE001
                    legs.append({"slug": slug, "game_id": leg.get("game_id"),
                                 "rows": 0,
                                 "error": "unreadable turn_series.json: %s"
                                          % exc})
                    continue
            if doc is None:
                legs.append({"slug": slug, "game_id": leg.get("game_id"),
                             "rows": 0,
                             "error": leg.get("turn_series_error")
                                      or "no turn_series.json"})
                continue

            leg_rows = doc.get("rows") or []
            boundaries = {b.get("turn") for b
                          in ((leg.get("levels") or {}).get("events") or [])
                          if b.get("turn") is not None}
            for row in leg_rows:
                campaign_turn += 1
                rows.append(dict(
                    row,
                    campaign_turn=campaign_turn,
                    leg_index=leg.get("index"),
                    leg_slug=slug,
                    game_id=leg.get("game_id"),
                    # True only where a level actually changed. `levels` is
                    # `inner/levels.py`'s record, not an inference from score.
                    level_boundary=row.get("turn") in boundaries,
                    # Whether this leg started from the previous leg's books.
                    # C3's transfer claim is about rows on the far side of a
                    # True here, and a series that does not mark it cannot be
                    # read for transfer at all.
                    seeded_from_previous_leg=bool(leg.get("seed_books")),
                ))
            legs.append({"slug": slug, "game_id": leg.get("game_id"),
                         "rows": len(leg_rows),
                         "seeded": bool(leg.get("seed_books")),
                         "carried": leg.get("carried"),
                         "usd": leg.get("usd"),
                         "outcome": leg.get("outcome")})

        return {
            "schema": "theoria-campaign-series/v1",
            "prompt_id": self.prompt_id,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "games": self.games,
            "legs": legs,
            "rows": rows,
            "totals": {
                "turns": len(rows),
                "legs_with_rows": sum(1 for entry in legs if entry["rows"]),
                "legs_recorded": len(legs),
                "usd": round(sum(float(r.get("usd") or 0.0) for r in rows), 6),
                "level_boundaries": sum(1 for r in rows
                                        if r.get("level_boundary")),
            },
            "reading": (
                "campaign_turn is the axis for C2's 前重后轻 claim. The "
                "front-load index over it is E2 in battery/metrics/economy.py "
                "and is deliberately not recomputed here. A leg with rows 0 "
                "and an error spent money and produced no series; it is not "
                "the same as a campaign with fewer legs."),
        }

    def save(self) -> str:
        """Atomically, after every leg. A campaign is hours long and the
        session running it will be interrupted."""
        self._write_json(self.state_path, self.report())
        self._write_json(os.path.join(self.out_dir, "MANIFEST.json"),
                         self.manifest())
        self._write_json(os.path.join(self.out_dir, "campaign_series.json"),
                         self.campaign_series())
        return self.state_path

    @staticmethod
    def _write_json(path: str, payload: Dict[str, Any]) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)

    def manifest(self) -> Dict[str, Any]:
        """The four required provenance fields, written beside `campaign.json`.

        CLAUDE.md: every experiment writes `runs/<id>/MANIFEST.json` with
        `prompt_id`, `branch`, `base_commit` and `utc`. This module wrote only
        `campaign.json`, which is the campaign's *result* and not its
        provenance -- a distinction the convention makes on purpose, since
        narrative and result both evaporate without the commit they came from.

        Note this is the campaign-level manifest. Each leg's own run directory
        gets its own from `armtools.archive`, and that is the one the figure-2
        discovery rule looks for.
        """
        return {
            "prompt_id": self.prompt_id,
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "base_commit": _git("rev-parse", "HEAD"),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                 time.gmtime(self.started)),
            "games": self.games,
            "budget": {"campaign_usd": self.campaign_usd,
                       "game_usd": self.game_usd,
                       "leg_usd_cap": LEG_USD_CAP,
                       "actions_per_level": self.actions_per_level},
            "model": self.model,
            "offline": self.offline,
            "legs": [{"slug": leg.get("slug"), "game_id": leg.get("game_id"),
                      "usd": leg.get("usd"), "outcome": leg.get("outcome")}
                     for leg in self.legs],
            "spent_usd": round(self.spent_usd, 6),
            "stopped": self.stopped,
        }


def _git(*args: str) -> Optional[str]:
    try:
        import subprocess                              # noqa: PLC0415
        out = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                             text=True, timeout=15)
        return out.stdout.strip() or None
    except Exception:                                  # noqa: BLE001
        # A manifest missing its commit is worth more than a campaign that
        # refused to start because git was slow.
        return None


# -- the entry point --------------------------------------------------------
#
# There was none. `campaign.py` had no `main`, no argparse and no `__main__`,
# and nothing in the repo imported it except its own test -- so the module that
# holds the authorised budget could not be started from a shell. That is also
# why `run_leg` was the one method with no test: every test in
# `tests/test_campaign.py` subclasses `Campaign` and replaces it.

def main(argv=None) -> int:
    import argparse                                    # noqa: PLC0415
    import sys                                         # noqa: PLC0415

    from harness.run import _scratch_policy            # noqa: PLC0415

    ap = argparse.ArgumentParser(
        description="The development-pile campaign: many legs, one budget.")
    ap.add_argument("--prompt-id", default="A3-campaign-devpile")
    ap.add_argument("--out-dir", required=True,
                    help="the campaign's own run directory; campaign.json and "
                         "MANIFEST.json are written here after every leg")
    ap.add_argument("--games", nargs="+", default=list(DEV_PILE),
                    help="checked against piles.json, not against DEV_PILE")
    ap.add_argument("--max-legs", type=int, default=3)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--campaign-usd", type=float, default=CAMPAIGN_USD)
    ap.add_argument("--game-usd", type=float, default=GAME_USD)
    ap.add_argument("--actions-per-level", type=int, default=ACTIONS_PER_LEVEL)
    ap.add_argument("--mock", action="store_true",
                    help="play the whole campaign against proxy/mock. No key, "
                         "no network, no ARC quota.")
    ap.add_argument("--desk", action="store_true",
                    help="with --mock, still call the real desk. This SPENDS "
                         "model money against a mock world.")
    ap.add_argument("--pool", default=None,
                    help="a scratch spend-gate ledger. Required with --mock: "
                         "a rehearsal's fictional reservations must not land "
                         "in proxy/var/spend_gate.jsonl, which the whole fleet "
                         "shares.")
    ap.add_argument("--i-have-authorisation", action="store_true",
                    help="start a LIVE campaign on the shared pool. Requires "
                         "that the Phase 1 gate is green or that an exception "
                         "is registered in monitor/spec.py p3-gate-exception, "
                         "and that the campaign lane's spend authority applies "
                         "to you (monitor/CHARTER.md). Neither is checked here "
                         "-- this flag exists so that spending is a thing "
                         "someone typed, not a default.")
    args = ap.parse_args(argv)

    # A live campaign is the single most expensive thing in this repo and the
    # default must not be one. `harness/run.py` gets this wrong in the other
    # direction -- bare `python -m harness.run` is a live money-spending run --
    # and that is not a default worth copying.
    if not args.mock and args.pool is None and not args.i_have_authorisation:
        print("refusing to start a LIVE campaign without an explicit "
              "acknowledgement.\n"
              "\n"
              "Theoria.md:305 makes the Phase 1 acceptance list the gate on "
              "spending game money (全绿才准烧游戏钱), and monitor/state.json "
              "currently reports p1_green 9 of 16. monitor/CHARTER.md grants "
              "the campaign lane's spend to RES-1 alone.\n"
              "\n"
              "Rehearse instead:\n"
              "  python -m harness.campaign --mock --pool <tmp>/pool.jsonl "
              "--out-dir <dir>\n"
              "\n"
              "If a live run has been authorised, pass --i-have-authorisation "
              "and record the exception in monitor/spec.py p3-gate-exception "
              "first.", file=sys.stderr)
        return 2

    gate = (spend_mod.SpendGate() if args.pool is None
            else spend_mod.SpendGate(_scratch_policy(args.pool)))
    expect_pool = ({"pool": gate.policy.pool,
                    "ledger_abspath": os.path.abspath(gate.ledger_path)}
                   if args.pool else None)

    kwargs: Dict[str, Any] = {
        "prompt_id": args.prompt_id, "out_dir": args.out_dir,
        "games": args.games, "model": args.model,
        "campaign_usd": args.campaign_usd, "game_usd": args.game_usd,
        "actions_per_level": args.actions_per_level,
        "offline": args.mock and not args.desk,
        "spend_gate": gate, "expect_pool": expect_pool,
    }

    if args.mock:
        from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415
        with MockArc(api_key=DEFAULT_KEY, games=list(args.games)) as arc:
            camp = Campaign(env_upstream=arc.base_url, env_key=DEFAULT_KEY,
                            require_key=False, **kwargs)
            report = camp.run(max_legs_per_game=args.max_legs)
    else:
        camp = Campaign(**kwargs)
        report = camp.run(max_legs_per_game=args.max_legs)

    print(json.dumps(report, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
