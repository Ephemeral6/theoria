"""The canonical field registry: what a v1.0 record may and may not contain.

`LEDGER_FORMAT.md` says the ledger has exactly two shapes. Until now that was
true of what the proxies happen to write; it was not enforced, and `**extra`
would have carried any field at all onto disk. F-16 ruled
`proxy/LEDGER_FORMAT.md` the canon and `baseline-arms/harness/ledger.py`'s
earlier spelling the dialect to be migrated. A canon that cannot refuse a
non-canonical field is a style guide, not a canon, so this module is the
refusal.

Three lines, in the order they fire:

  * **A banned spelling is named, with its canonical replacement.** `frame`,
    `timestamp`, `total_cost_usd` and the rest of the v0 vocabulary raise an
    error that says which field to use instead and points at the migrator.
    Getting `frame` silently written next to `frames` is exactly the drift the
    ruling exists to stop.
  * **`env_step` and `model_call` are closed.** Their field sets are the tables
    in `LEDGER_FORMAT.md` §3 and §4 and nothing else. Two shapes means two
    shapes: the Phase 2 battery reads them without branching, and an extra
    field is a branch someone will eventually have to write.
  * **Auxiliaries are open in the payload but closed in the envelope.** §6 says
    an auxiliary is "same envelope, different `event`", and the payload column
    is deliberately loose -- `run_start` carries whatever a run needs to
    describe itself. So required keys are checked, banned spellings are still
    banned, and anything else is allowed through.

Types are checked where a wrong type would silently corrupt a later
computation: `score` must be an int and not a bool, because `True` sums as 1;
`frames` must be a list, because a bare frame written where a list belongs is
the observation-losing bug §7 was written about.
"""

from typing import Any, Dict, Optional, Set

#: Envelope fields, on every record whatever its event (§2). The writer owns
#: all four plus `seq`/`ts`; a caller may not set them.
ENVELOPE = frozenset({"v", "event", "seq", "ts", "run_id", "arm"})

#: §3. The closed field set of an `env_step`, minus the envelope.
#:
#: `response` was added by P-9 and is the reason this list is a superset of
#: what the proxies used to write. The first closure property is *complete
#: record* -- every bit entering or leaving an arm is in the ledger -- and the
#: earlier field set quietly failed it: a live command response carries
#: `win_levels`, `available_actions`, `full_reset` and `action_input`, and
#: none of them had a home, so they were dropped on the floor. `win_levels` in
#: particular is the only place the environment says how many levels a game
#: has, without which no score fraction can be computed from the ledger alone.
#: The field holds the response body with `frame` removed, because the frames
#: are already stored whole and hashed; storing them twice would be two things
#: to keep in agreement.
ENV_STEP_FIELDS = frozenset({
    "game_id", "card_id", "guid", "step_idx", "action", "frames", "n_frames",
    "frame_hash", "state", "score", "levels_completed", "level",
    "level_boundary", "variant", "guard", "http", "response",
})

ENV_STEP_REQUIRED = frozenset({
    "game_id", "step_idx", "action", "frames", "n_frames", "frame_hash",
    "level", "level_boundary", "guard", "http",
})

#: §4. The closed field set of a `model_call`, minus the envelope.
#:
#: `game_id` is in the set because the Phase 2 battery asked for it: without it
#: a run that thought and never acted lands as `unknown`, and a guardrail can
#: only filter model traffic by rejoining it to `env_step` records. It is
#: optional in the format -- adding a *required* field is what §8 bumps `v`
#: for -- but this writer always supplies it when the run knows its game, so
#: every record the proxies produce carries one.
MODEL_CALL_FIELDS = frozenset({
    "call_idx", "provider", "model", "request", "response", "usage",
    "pricing_ref", "step_idx", "game_id", "http",
})

MODEL_CALL_REQUIRED = frozenset({
    "call_idx", "provider", "model", "request", "response", "usage", "http",
})

#: §6. Auxiliary payloads are open; these are the keys each one must carry.
AUXILIARY_REQUIRED: Dict[str, Set[str]] = {
    "run_start": {"game_id"},
    "run_end": {"outcome"},
    "env_meta": {"http"},
    "guard_block": {"rule", "path"},
    "incident": {"kind", "detail"},
}

#: Every dollar-shaped field gets the whole reason, not a cross-reference. A
#: refusal that says "see the other entry" is a refusal the next caller routes
#: around by renaming the field.
_COST_HINT = ("`usage` verbatim plus a `pricing_ref`, and nothing else: a "
              "dollar figure is usage x a versioned price table, computed on "
              "demand by proxy/cost.py. An append-only file that recorded a "
              "price would be wrong the day the price changed, and could not "
              "be corrected (LEDGER_FORMAT.md §4, §5; D-004)")

#: Spellings that must never reach a v1.0 record, and what to write instead.
#: The v0 half of this table is `baseline-arms/harness/ledger.py`'s vocabulary;
#: the rest are quantities §5 rules derived and therefore unrecordable.
BANNED_SPELLINGS: Dict[str, str] = {
    # -- baseline-arms v0 spellings (LEDGER_FORMAT.md §7) ------------------
    "frame": "frames (always a list -- one command can return several)",
    "timestamp": "ts (ISO-8601 UTC, millisecond precision)",
    "frames_returned": "n_frames",
    "win_levels": "levels_completed",
    "available_actions": "no canonical field; it belongs in the env_meta "
                         "response body, not on a step",
    "failed": "http.status and guard.decision -- 'failed' conflates a refusal "
              "with a server error",
    "http_status": "http.status",
    "http_tries": "http.attempts",
    "reason": "guard.reason on env_step; free on auxiliaries",
    "attempt": "http.attempts",
    "duration_ms": "http.elapsed_ms",
    "is_error": "http.status",
    "prompt_chars": "no canonical field; the whole request is recorded",
    # -- derived quantities, which §5 forbids recording --------------------
    "cost": _COST_HINT,
    "cost_usd": _COST_HINT,
    "total_cost_usd": _COST_HINT,
    "price_usd": _COST_HINT,
    "score_pct": "nothing: the score is produced by the frozen scorer from "
                 "this file, not written into it",
}

#: `reason` is banned as a *step* field but is the natural word on an
#: auxiliary, where the payload is open. Same for a couple of others.
BANNED_EXCEPT_ON_AUXILIARIES = frozenset({"reason", "failed", "attempt"})


class NonCanonicalField(ValueError):
    """A field that `LEDGER_FORMAT.md` does not define was offered to the
    writer. Raised before anything reaches disk."""


def _bool_is_not_int(name: str, value: Any) -> None:
    if isinstance(value, bool):
        raise NonCanonicalField(
            "%s is a bool; the canon says int. `True` sums as 1 and would "
            "quietly become a score." % name)


def check_types(event: str, fields: Dict[str, Any]) -> None:
    """The type checks that stop a silent corruption, and no others.

    This is not a schema validator. Each check here is one that, if it did not
    fire, would produce a *plausible wrong number* downstream rather than an
    obvious error.
    """
    if event == "env_step":
        frames = fields.get("frames")
        if frames is not None and not isinstance(frames, list):
            raise NonCanonicalField(
                "frames must be a list or null: one command can return several "
                "frames (the precheck observed seven), and a bare frame written "
                "here is an observation silently lost (LEDGER_FORMAT.md §3).")
        n_frames = fields.get("n_frames")
        if not isinstance(n_frames, int) or isinstance(n_frames, bool):
            raise NonCanonicalField("n_frames must be an int")
        if frames is not None and n_frames != len(frames):
            raise NonCanonicalField(
                "n_frames is %r but frames has %d entries; n_frames is recorded "
                "explicitly because >1 is what the cascade-semantics ruling "
                "turns on, so it may not disagree with the list."
                % (n_frames, len(frames)))
        if frames is None and n_frames != 0:
            raise NonCanonicalField("frames is null so n_frames must be 0")
        for name in ("score", "levels_completed", "step_idx", "level"):
            value = fields.get(name)
            if value is not None:
                _bool_is_not_int(name, value)
                if not isinstance(value, int):
                    raise NonCanonicalField("%s must be an int or null, got %r"
                                            % (name, type(value).__name__))
        action = fields.get("action")
        if not isinstance(action, dict) or set(action) != {"name", "id", "data"}:
            raise NonCanonicalField(
                "action must be exactly {name, id, data} (LEDGER_FORMAT.md §3); "
                "got %r" % (sorted(action) if isinstance(action, dict) else action,))
        guard = fields.get("guard")
        if not isinstance(guard, dict) or guard.get("decision") not in ("allow", "deny"):
            raise NonCanonicalField(
                "guard must carry decision 'allow' or 'deny': a refusal is a "
                "record, not an absence (LEDGER_FORMAT.md §3, D-003).")
        if not isinstance(fields.get("level_boundary"), bool):
            raise NonCanonicalField(
                "level_boundary must be a bool. It is read for truthiness "
                "downstream, so any non-empty string would count as a level.")
        http = fields.get("http")
        if not isinstance(http, dict) or "status" not in http:
            raise NonCanonicalField(
                "env_step.http must carry a `status` key -- null is allowed, "
                "absent is not. Whether a command succeeded is what the billed "
                "action count is derived from, and a reader that has to guess "
                "at it will guess consistently and wrongly.")

    if event == "model_call":
        usage = fields.get("usage")
        if not isinstance(usage, dict):
            raise NonCanonicalField(
                "usage must be an object, copied through from the provider "
                "verbatim (LEDGER_FORMAT.md §4, D-005).")
        # D-005 says usage is copied verbatim; §5 says no dollar figure is ever
        # written. Where the two meet, §5 wins: the ban is on the *file*
        # containing a price, and a nested key is still in the file (RED-42).
        nested = sorted(set(usage) & set(BANNED_SPELLINGS))
        if nested:
            raise NonCanonicalField(
                "usage carries %s. `usage` is copied through verbatim, but "
                "\"no dollar figure is ever written to the ledger\" is a "
                "property of the file, not of one field -- a price nested "
                "inside a verbatim block is still a price in an append-only "
                "file. Record it outside the ledger, as cost.py does."
                % ", ".join(repr(k) for k in nested))

    http = fields.get("http")
    if http is not None and not isinstance(http, dict):
        raise NonCanonicalField("http must be an object")


def check(event: str, fields: Dict[str, Any]) -> None:
    """Refuse anything `LEDGER_FORMAT.md` v1.0 does not define.

    Called by the writer before a record is serialised, and by
    `proxy/tools/validate_ledger.py` on a stream someone else produced.
    """
    offered = set(fields)

    for name in sorted(offered):
        if name in ENVELOPE:
            raise NonCanonicalField(
                "%s is an envelope field owned by the writer (LEDGER_FORMAT.md "
                "§2); a caller may not set it." % name)
        replacement = BANNED_SPELLINGS.get(name)
        if replacement is None:
            continue
        if (name in BANNED_EXCEPT_ON_AUXILIARIES
                and event not in ("env_step", "model_call")):
            continue
        raise NonCanonicalField(
            "%r is not canonical in a %s record. Write %s. If this came from a "
            "v0 stream, lift it with `python -m proxy.tools.upgrade_ledger` "
            "(LEDGER_FORMAT.md §7) rather than by hand."
            % (name, event, replacement))

    if event == "env_step":
        allowed, required = ENV_STEP_FIELDS, ENV_STEP_REQUIRED
    elif event == "model_call":
        allowed, required = MODEL_CALL_FIELDS, MODEL_CALL_REQUIRED
    else:
        missing = AUXILIARY_REQUIRED.get(event, set()) - offered
        if missing:
            raise NonCanonicalField(
                "a %s record must carry %s (LEDGER_FORMAT.md §6)"
                % (event, ", ".join(sorted(missing))))
        check_types(event, fields)
        return

    extra = offered - allowed
    if extra:
        raise NonCanonicalField(
            "%s is one of the two shapes and its field set is closed "
            "(LEDGER_FORMAT.md §%s): %s %s not defined. The battery reads two "
            "shapes without branching; an extra field is a branch. Put it on an "
            "auxiliary record instead (§6)."
            % (event, "3" if event == "env_step" else "4",
               ", ".join(repr(x) for x in sorted(extra)),
               "is" if len(extra) == 1 else "are"))

    missing = required - offered
    if missing:
        raise NonCanonicalField(
            "a %s record must carry %s" % (event, ", ".join(sorted(missing))))

    check_types(event, fields)


def describe() -> Dict[str, Any]:
    """The registry as data, for the migrator interface document and for any
    reader that wants to check its own output without importing the writer."""
    return {
        "ledger_version": "1.0",
        "envelope": sorted(ENVELOPE),
        "closed_shapes": {
            "env_step": {"fields": sorted(ENV_STEP_FIELDS),
                         "required": sorted(ENV_STEP_REQUIRED)},
            "model_call": {"fields": sorted(MODEL_CALL_FIELDS),
                           "required": sorted(MODEL_CALL_REQUIRED)},
        },
        "auxiliary_required": {k: sorted(v) for k, v in sorted(AUXILIARY_REQUIRED.items())},
        "banned_spellings": dict(sorted(BANNED_SPELLINGS.items())),
    }
