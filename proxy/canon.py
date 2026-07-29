"""The canonical field registry: what a v1.0 record may and may not contain.

`LEDGER_FORMAT.md` says the ledger has exactly two shapes. Until now that was
true of what the proxies happen to write; it was not enforced, and `**extra`
would have carried any field at all onto disk. F-16 ruled
`proxy/LEDGER_FORMAT.md` the canon and `baseline-arms/harness/ledger.py`'s
earlier spelling the dialect to be migrated. A canon that cannot refuse a
non-canonical field is a style guide, not a canon, so this module is the
refusal.

Five lines, in the order they fire:

  * **The envelope is the writer's.** A caller that sets `seq` or `ts` is
    either confused or forging; either way the writer owns those (§2).
  * **A banned spelling is named, with its canonical replacement.** `frame`,
    `timestamp`, `total_cost_usd` and the rest of the v0 vocabulary raise an
    error that says which field to use instead and points at the migrator.
    Getting `frame` silently written next to `frames` is exactly the drift the
    ruling exists to stop.
  * **`env_step` and `model_call` have required fields, and they are
    required.** A record missing one is not a lossy record, it is an
    uninterpretable one.
  * **Everything else on the two shapes is additive-safe**: a field §3 and §4
    do not list is *warned about and kept*, never refused. See below.
  * **Auxiliaries are open in the payload.** §6 says an auxiliary is "same
    envelope, different `event`", and the payload column is deliberately loose
    -- `run_start` carries whatever a run needs to describe itself.

**Why the two shapes stopped being closed** (INC-TA-006, `proxy/CONTRACT_CHANGES.md`).
This module used to refuse an unlisted field on `env_step`/`model_call`, on the
reasoning that "the battery reads two shapes without branching, and an extra
field is a branch". That reasoning was about *readers*, and it was applied to
the *writer*, where its cost is paid in a different currency. P-8's arm had been
writing `beat`/`label`/`transport`/`proxied`/`proxy_gap` on its `model_call`
records since before the closure existed; the closure landed afterwards, on a
commit that arm never touched, and it imports `proxy/` as a library. The first
live desk call after that refused to serialise. The provider had already been
paid $2.695 and the reply was discarded — the fact the record existed to record
was *already true* when the writer said no.

That is the shape of the failure mode, not an unlucky instance of it. A ledger
is append-only and written after the fact; a refusal there cannot un-spend the
money, cannot un-send the request, and destroys the only evidence that either
happened. **Refusing to record is strictly worse than recording something a
reader may have to skip.** So the closure is now the warning, and what stays a
refusal is the set of things that are wrong rather than merely unknown: a v0
spelling (drift), a dollar figure (§5), an envelope field (forgery), a missing
required field (uninterpretable).

Readers are not thereby asked to branch. `LEDGER_FORMAT.md` §8's guarantee is
that a *defined* field never changes meaning under one `v`; a reader that
handles the fields it knows and ignores the rest was always correct, and is
still correct. What it now also gets is a stream that exists.

Types are checked where a wrong type would silently corrupt a later
computation: `score` must be an int and not a bool, because `True` sums as 1;
`frames` must be a list, because a bare frame written where a list belongs is
the observation-losing bug §7 was written about.
"""

import warnings
from typing import Any, Callable, Dict, List, Optional, Set

#: Envelope fields, on every record whatever its event (§2). The writer owns
#: all four plus `seq`/`ts`; a caller may not set them.
#:
#: `prev` joined them for D-024/RED-40: it is the sha256 of the previous line's
#: bytes as they were written, so editing, deleting, inserting or reordering a
#: record breaks every `prev` after it.  It is *optional* by design -- a stream
#: without it is unchained, not invalid -- which is why the format stays at
#: v1.0: §8 bumps `v` for a changed meaning or a new **required** field, and an
#: optional one is neither.  It is listed here for the same reason as the rest:
#: the writer owns it, and a caller who could set it could forge the chain.
ENVELOPE = frozenset({"v", "event", "seq", "ts", "run_id", "arm", "prev"})

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
#:
#: The last five are P-8's, and they are here because they were always in use,
#: not because unknown fields are now tolerated. They describe *how the call was
#: made*, which nothing else on the record says:
#:
#:   * `beat` is the loop beat that spent the call, and it is the reason
#:     Theoria.md constraint 8 -- the large model appears at theorize and at
#:     probe design and nowhere else -- is checkable **from the ledger** rather
#:     than asserted in prose. Grouping `model_call` records by `beat` either
#:     shows two values or shows the constraint was broken.
#:   * `proxied` and `proxy_gap` are the completeness property stated at its
#:     real size. `false` means this record was written by an arm's own writer
#:     rather than observed at `model_proxy`, so "every bit entering or leaving
#:     an arm is in the ledger" rests on the arm rather than on construction;
#:     `proxy_gap` says why. A reader that cannot tell those two cases apart
#:     will read the weaker one as the stronger one.
#:   * `transport` distinguishes an HTTPS call to `/v1/messages` from a
#:     `claude-code-cli` subprocess. It is load-bearing for cost comparison:
#:     the CLI transport does no prompt caching, so its cache-read column is a
#:     structural zero rather than a small number (INC-TA-005).
#:   * `label` is a free short tag distinguishing calls within one beat.
MODEL_CALL_FIELDS = frozenset({
    "call_idx", "provider", "model", "request", "response", "usage",
    "pricing_ref", "step_idx", "game_id", "http",
    "beat", "label", "transport", "proxied", "proxy_gap",
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
    """A field that `LEDGER_FORMAT.md` forbids, or a required one that is
    missing. Raised before anything reaches disk.

    Note what this is *not* raised for any more: a field the format simply does
    not mention. That is `UnknownField`, and it is a warning.
    """


class UnknownField(UserWarning):
    """A field `LEDGER_FORMAT.md` §3/§4 does not list was written to one of the
    two shapes. The field is kept; this says so out loud.

    A warning rather than an error because the writer runs after the fact: by
    the time it sees the record, the request has been sent and the money has
    been spent, so refusing destroys evidence of something that happened
    anyway. See `proxy/CONTRACT_CHANGES.md` and the module docstring.
    """


def _unknown_message(event: str, names: List[str]) -> str:
    return (
        "%s carries %s, which LEDGER_FORMAT.md §%s does not list. The field%s "
        "kept -- a writer that runs after the request has been sent cannot "
        "refuse a record without destroying evidence (INC-TA-006). If this is "
        "deliberate, add it to §%s and to canon.%s so it stops warning; if it "
        "is a typo, it is now a typo on disk. Either way "
        "proxy/CONTRACT_CHANGES.md is the procedure."
        % (event, ", ".join(repr(n) for n in names),
           "3" if event == "env_step" else "4",
           " is" if len(names) == 1 else "s are",
           "3" if event == "env_step" else "4",
           "ENV_STEP_FIELDS" if event == "env_step" else "MODEL_CALL_FIELDS"))


def _banned_keys_within(value: Any, _depth: int = 0) -> List[str]:
    """Every banned spelling used as a *key* anywhere inside `value`.

    §5's "no dollar figure is ever written to the ledger" is a property of the
    file. Before S9 the two shapes were closed, so the only way a price could
    hide was inside a block the format requires verbatim -- which is why the
    original check looked one level into `usage` and stopped. Additive-safety
    opens a second way in: an unlisted field is now written, and
    `{"billing": {"cost_usd": 2.695}}` would have been refused outright the day
    before. Scanning to the bottom keeps the property exactly the size it was.

    Depth is bounded because a record is JSON the writer is about to serialise:
    if it were deep enough to matter here, `json.dumps` would already be the
    problem.
    """
    if _depth > 12:
        return []
    found: List[str] = []
    if isinstance(value, dict):
        for key, sub in value.items():
            if isinstance(key, str) and key in BANNED_SPELLINGS:
                found.append(key)
            found.extend(_banned_keys_within(sub, _depth + 1))
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_banned_keys_within(item, _depth + 1))
    return sorted(set(found))


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
        # Scanned to the bottom rather than one level down, because "one level"
        # was never the property -- it was as deep as the first attack went.
        # The five P-8 fields, checked by the same rule as everything else in
        # this function: a wrong type here produces a *plausible wrong answer*
        # rather than an obvious error. `proxied` is the sharp one --
        # `bool("false")` is `True`, so a record the arm wrote itself would read
        # as one the proxy observed, which is the exact confusion the field was
        # added to prevent. `beat` is next: constraint 8 is checked by grouping
        # on it, and a group key of the wrong type either crashes the check or
        # silently makes a third group.
        if not isinstance(fields.get("proxied"), (bool, type(None))):
            raise NonCanonicalField(
                "proxied must be a bool or null, got %r. It is read for "
                "truthiness, so the string 'false' would count as proxied and "
                "an arm-written record would be read as proxy-observed -- the "
                "completeness property one size larger than it is."
                % (fields.get("proxied"),))
        for name in ("beat", "label", "transport", "proxy_gap"):
            value = fields.get(name)
            if value is not None and not isinstance(value, str):
                raise NonCanonicalField(
                    "%s must be a string or null, got %r. `beat` in particular "
                    "is the group key Theoria.md constraint 8 is checked on, "
                    "and a group key of the wrong type checks a different claim."
                    % (name, type(value).__name__))

        nested = _banned_keys_within(usage)
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


def check(event: str, fields: Dict[str, Any], *,
          on_unknown: Optional[Callable[[str, List[str], str], None]] = None
          ) -> List[str]:
    """Refuse what `LEDGER_FORMAT.md` v1.0 forbids; warn about what it merely
    does not mention.

    Called by the writer before a record is serialised, and by
    `proxy/tools/validate_ledger.py` on a stream someone else produced.

    Returns the sorted names of fields on a closed shape that §3/§4 do not
    list. They are **not** removed from `fields`: the caller writes them.
    `on_unknown(event, names, message)` replaces the default
    `warnings.warn(..., UnknownField)` for a caller that has somewhere better
    to put the notice -- the validator collects them as non-fatal notices, the
    ledger tallies them per run.
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
        return []

    # Missing-required is still a refusal, and it is checked *before* the
    # unknown-field notice. A caller who mistyped a required field's name gets
    # told the field is missing, which is the actionable half; the notice about
    # the typo's new spelling follows it.
    missing = required - offered
    if missing:
        raise NonCanonicalField(
            "a %s record must carry %s" % (event, ", ".join(sorted(missing))))

    check_types(event, fields)

    unknown = sorted(offered - allowed)

    # §5 is a property of the *file*, and additive-safety opened a second route
    # into it: `{"billing": {"cost_usd": 2.695}}` on a `model_call` would have
    # been refused outright the day before this change, as an unlisted field.
    # The named spellings stay refused however deep they are nested, so the
    # property is exactly the size it was, not one size smaller.
    #
    # This *is* a refusal on the writer path, which D-030 argues against, and
    # the distinction is that INC-TA-006's field was correct and became refused
    # by a change elsewhere. A price in an append-only file is never correct and
    # no change elsewhere makes it so; the caller owns the field and the error
    # names the fix. Note also that refusing here is strictly more permissive
    # than the closure it replaces.
    for name in unknown:
        nested = _banned_keys_within(fields[name])
        if nested:
            raise NonCanonicalField(
                "%s.%s carries %s. A field this format does not define is kept "
                "-- but it may not be a back door for one the format bans. "
                "Write %s"
                % (event, name, ", ".join(repr(k) for k in nested),
                   BANNED_SPELLINGS[nested[0]]))

    if unknown:
        message = _unknown_message(event, unknown)
        if on_unknown is not None:
            on_unknown(event, unknown, message)
        else:
            warnings.warn(message, UnknownField, stacklevel=2)
    return unknown


def describe() -> Dict[str, Any]:
    """The registry as data, for the migrator interface document and for any
    reader that wants to check its own output without importing the writer.

    This is also the thing `proxy/canon_contract.json` pins and
    `proxy/tools/contract.py` diffs, so that a change which *narrows* what the
    proxies accept cannot arrive on an importing track unannounced. It did
    once; that is INC-TA-006 and $2.695.
    """
    shapes = {
        "env_step": {"fields": sorted(ENV_STEP_FIELDS),
                     "required": sorted(ENV_STEP_REQUIRED)},
        "model_call": {"fields": sorted(MODEL_CALL_FIELDS),
                       "required": sorted(MODEL_CALL_REQUIRED)},
    }
    return {
        "ledger_version": "1.0",
        "envelope": sorted(ENVELOPE),
        #: `fields` is now the *known* set, not the permitted set: an unlisted
        #: field on one of these shapes is warned about and written.
        "additive_safe": True,
        "shapes": shapes,
        # Deprecated spelling, kept because `describe()` is published for
        # readers this package cannot enumerate, and removing a key from a
        # published surface is exactly the kind of tightening
        # CONTRACT_CHANGES.md now requires an announcement for. C-003 there
        # holds the window; it may be dropped after it closes.
        "closed_shapes": shapes,
        "auxiliary_required": {k: sorted(v) for k, v in sorted(AUXILIARY_REQUIRED.items())},
        "banned_spellings": dict(sorted(BANNED_SPELLINGS.items())),
    }
