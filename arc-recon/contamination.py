"""Fold the append-only contamination log into the current register and the
sealed **claim set** -- the games a held-out claim may still be made about.

`data/piles.json` is hash-locked: changing it after play has begun is itself an
incident (its own rule 3). Its `contamination_register` therefore froze at
`never_audited` for all 25 games and has been wrong ever since the first RESET.
`data/contamination_log.jsonl` is the living record; this module is the reader
that makes "the log supersedes the register" executable rather than a sentence
in a README. Last entry per game wins, and every superseded entry stays.

The claim set is the point of the whole exercise. Theoria.md: "Phase 3 是'迭代到
出结果为止',只有在没见过的题上重打才不是自欺". A sealed game that somebody has
read the mechanics of is no longer a held-out problem, whether or not anyone
played it. Counting those games in a Phase 4 claim would overstate the result,
so they are subtracted here, by machine, from a file that records why.

    python contamination.py            # the table
    python contamination.py --json     # also write data/claim_set.json

## The exit code carries the whole verdict, not one third of it

`main()` used to end `return 0 if check["matches"] else 1` -- only the
`piles.json` hash. Sealed games ADDRESSED in a ledger, and games in NEEDS
ADJUDICATION, were **printed and dropped**. `verify.sh:53` looks at nothing but
the exit code, so the human reading the table was told the truth and the machine
holding the gate was told "clean" -- and only the machine's answer gates
anything.

Everything that can turn this red now goes through `gate()`, one function, so
the printed table and the exit code cannot disagree. Three of the four
conditions are about *not having looked*:

* an unparseable line in the contamination log -- a game whose registration
  nothing could read is not a game with no registration;
* a declared ledger that is absent or unreadable -- deleting a dirty ledger must
  not be a way through this gate;
* an empty scan set -- `all([])` is `True`, so the old `all_clean` would have
  reported a clean verdict having read nothing at all.

**A known gap, stated rather than hidden.** `OTHER_LEDGERS` is a hand-written
list of three files, and the repository holds far more ledger-shaped files than
that (see `monitor/inbox/20260728T171500Z-RES-3-...`). This module now reports
`scan_surface_self_discovered: False` so that the incompleteness is a boolean a
later check can gate on, instead of the prose caveat that no consumer reads.
Making the surface self-discovering is a separate work order; this one only
stops the gate from lying about what it *did* read.
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
LOG_PATH = os.path.join(DATA_DIR, "contamination_log.jsonl")
PILES_PATH = os.path.join(DATA_DIR, "piles.json")
CLAIM_SET_PATH = os.path.join(DATA_DIR, "claim_set.json")

# Ordered weakest to strongest. piles.json's own vocabulary is only
# never_audited / scores_only / trajectories_reviewed (indices 0, 2, 6); the
# other four were added by the log for exposures those three cannot express --
# knowledge contamination that never involved playing the game.
LEVELS = [
    "never_audited",            # nothing observed
    "filename_only",            # an id appeared in a file listing; no content
    "scores_only",              # aggregate numbers, no mechanics
    "blurb_glimpsed",           # promotional/evidence-card prose skimmed
    "design_document_disclosed",  # Theoria.md itself prints the mechanics
    "mechanics_disclosed",      # concrete rules read from an upstream page
    "trajectories_reviewed",    # frames/trajectories seen
]

CLAIM_STATES = ("in_claim_set", "retained_with_sensitivity_analysis",
                "quarantined_from_claims")

# At or above this level, a game must be quarantined or explicitly adjudicated.
# The level and the claim state are two hand-written fields; without a
# cross-check, a game can be registered as materially leaked and still sit in
# the held-out set because somebody typed the wrong second field.
MATERIAL_LEVEL = "mechanics_disclosed"

# Call records kept by other tracks. Read-only, and scanned only to make the
# "zero sealed contact" claim cover the places campaigns actually run -- this
# directory's own ledger does not.
import sealed as sealed_mod

CALL_FIELDS = ("url", "request_body", "request_headers", "method", "final_url")
EPISODE_FIELDS = ("game_id", "game", "games")
SUMMARY_FIELDS = ("kind",)

CALL = "call"
EPISODE = "episode"
SUMMARY = "summary"
UNRECOGNISED = "unrecognised"


def record_shape(entry: Dict[str, Any]) -> str:
    """Which kind of record is this, and therefore how should it be read?

    Three shapes exist in the files this module scans, and before A13 the reader
    knew only the first:

    * `call` -- an HTTP record: `url`, `request_body`, `request_headers`.
      `arc-recon/data/recon_ledger.jsonl` and most of
      `baseline-arms/probe_log.jsonl`.
    * `episode` -- a gameplay record carrying a top-level `game_id`. All 560
      lines of `baseline-arms/ledger.jsonl`. **Addressing a game is what playing
      one means**, so the id here is a contact, not a mention; reading these as
      "no request body, nothing to see" is exactly how 560 records audited
      themselves clean.
    * `summary` -- a probe's own aggregate output, keyed by `kind` with no call
      fields. Fifteen lines of `probe_log.jsonl`. These are derived *from*
      responses, so an id in one is a listing, on the same reasoning that keeps
      `GET /api/games` from scoring 21 contacts.

    Anything else is `unrecognised`, and the caller must treat that as *not
    audited*. Adding a shape here is how you make a new kind of record
    auditable; the one thing that must never happen again is a record shape
    passing through unread and being counted towards a clean verdict.
    """
    keys = set(entry)
    if keys & set(CALL_FIELDS):
        return CALL
    if keys & set(EPISODE_FIELDS):
        return EPISODE
    if keys & set(SUMMARY_FIELDS):
        return SUMMARY
    return UNRECOGNISED


def request_and_response(entry: Dict[str, Any], shape: str):
    """The two halves of a record: what we sent, and what came back.

    The split is the module's oldest and most load-bearing distinction --
    contact versus listing -- and it now has to be made for three shapes rather
    than one. For an `episode` record the id itself is the request half: you
    cannot take a step in a game without naming it.
    """
    if shape == CALL:
        # `game_id` at the top level of an HTTP record is still something we
        # addressed, and `record_shape` resolves CALL before EPISODE, so it has
        # to be picked up here or a record carrying both would lose it.
        return ([entry.get("url"), entry.get("final_url"),
                 entry.get("request_body"), entry.get("request_headers")]
                + [entry.get(key) for key in EPISODE_FIELDS],
                [entry.get("response_body"), entry.get("response_summary")])
    if shape == EPISODE:
        return ([entry.get(key) for key in EPISODE_FIELDS],
                [entry.get(key) for key in
                 ("frame", "state", "available_actions", "response_body")])
    # A summary is wholly derived from responses; nothing in it was sent.
    return ([], [entry])


OTHER_LEDGERS = [
    os.path.join(HERE, os.pardir, "baseline-arms", "ledger.jsonl"),
    os.path.join(HERE, os.pardir, "baseline-arms", "probe_log.jsonl"),
]


def piles() -> Dict[str, Any]:
    with open(PILES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def verify_piles_hash() -> Dict[str, Any]:
    """The cut file must be byte-identical to the hash it published.

    `sha256` lives inside the file it names, so it is computed over the file
    with that field blanked -- the same way cut_piles.py produced it.
    """
    raw = json.loads(open(PILES_PATH, encoding="utf-8").read())
    declared = raw.get("sha256")
    body = {k: v for k, v in raw.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    actual = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"declared": declared, "recomputed": actual,
            "matches": declared == actual}


def sealed_api_contacts(ledger_path: str = None) -> Dict[str, Any]:
    """Scan the call ledger for any sealed game we *addressed*. Zero is the claim.

    "No sealed game has been touched via the API" is the load-bearing sentence of
    the whole held-out design, and until now it was a sentence. The ledger records
    every call this directory has ever made, so it is checkable.

    Contact is defined as what we *sent*: the sealed id appears in the request
    URL or the request body. A sealed id in a *response* is not contact -- the
    read-only catalogue `GET /api/games` returns all 25 games by construction,
    which is how the cut was made in the first place. Scoring those as touches
    would report 21 contacts on a directory that has made none, and a check that
    cannot come back clean is as useless as one that cannot fail (INC-003).

    The response side is still counted, separately and labelled, because
    "we never even saw the id" and "we saw it listed and did not call it" are
    different facts and should not be made to look alike.

    **A13: this function read three fields and called every other shape clean.**
    It extracted `url`, `request_body` and `response_body`, and
    `baseline-arms/ledger.jsonl` has none of them -- its 560 records carry a
    top-level `game_id` and nothing else this reader knew. So `sent` was empty
    on every line, `contacts` was empty, and the guard below (`present and not
    unreadable`) saw a file that existed and parsed and returned `clean: True`.
    "560 calls, sealed ADDRESSED: NONE" was printed, and `claim_set.json`
    recorded it. The green light was constructed, not found.

    Two changes. Every record is now **classified into a shape** before it is
    read, and a record matching none of them is `unreadable` -- not checked is
    not clean, which is the whole rule this module exists to enforce. And the
    request side is scanned by `sealed.hits`, the one criterion, which searches
    the *whole* payload for the full id or a whole-token stem rather than
    looking inside two named keys; that is what makes the bare stem
    `cascade/probe.py` writes into `tags` visible to an audit for the first time.
    """
    ledger_path = ledger_path or os.path.join(DATA_DIR, "recon_ledger.jsonl")
    sealed = piles()["sealed_pile"]
    short = {game_id.split("-")[0]: game_id for game_id in sealed}
    contacts: Dict[str, List[str]] = {}
    listed: Dict[str, int] = {}
    unreadable: List[str] = []
    shapes: Dict[str, int] = {}
    lines = 0
    present = os.path.exists(ledger_path)
    if present:
        try:
            raw = open(ledger_path, encoding="utf-8").read().splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            raw = []
            unreadable.append("whole file: %s: %s" % (type(exc).__name__, exc))
        for i, line in enumerate(raw, 1):
            line = line.strip()
            if not line:
                continue
            lines += 1
            try:
                entry = json.loads(line)
            except ValueError as exc:
                # A call record nothing can parse is a call nobody has checked.
                # It used to raise, which at least stopped the run; the danger
                # was never this branch but the one below it, where a *missing*
                # ledger produced "0 calls, sealed ADDRESSED: NONE".
                unreadable.append("line %d: %s" % (i, exc))
                continue
            if not isinstance(entry, dict):
                unreadable.append("line %d: not a JSON object" % i)
                continue
            shape = record_shape(entry)
            shapes[shape] = shapes.get(shape, 0) + 1
            if shape == UNRECOGNISED:
                # The one branch this whole work order is about. A record whose
                # every field is unknown to this reader has not been audited,
                # and an audit that cannot read a record must not vote on it.
                unreadable.append(
                    "line %d: no field this audit knows how to read (keys: %s)"
                    % (i, ", ".join(sorted(entry)[:8]) or "none"))
                continue
            url = str(entry.get("url", ""))
            request, response = request_and_response(entry, shape)
            sent = sealed_mod.hits_in_any(request, sealed)
            back = sealed_mod.hits_in_any(response, sealed)
            for game_id, why in sent.items():
                contacts.setdefault(game_id, []).append(
                    "%s %s [%s, %s record]"
                    % (entry.get("method") or shape, url or "-", why, shape))
            for game_id in back:
                listed[game_id] = listed.get(game_id, 0) + 1

            # Recognising a record's SHAPE is not the same as reading all of it,
            # and the difference is the bug this work order is about, one level
            # down. `request_and_response` names the fields each shape keeps its
            # ids in; a sealed id sitting in some *other* field of an otherwise
            # familiar record -- an operator note, a new key a writer added last
            # week -- was extracted by neither half and voted clean.
            #
            # So the whole record is scanned too, and anything found that
            # neither half accounts for is counted as a CONTACT. Fail closed:
            # the response-side carve-out exists because `GET /api/games`
            # provably lists all 25, and no such argument is available for a
            # field nobody has classified. Teaching `request_and_response` about
            # the field is how you make it a listing again.
            for game_id, why in sealed_mod.hits(entry, sealed).items():
                if game_id in sent or game_id in back:
                    continue
                where = sorted(
                    key for key in entry
                    if sealed_mod.hits({key: entry[key]}, [game_id])
                )
                contacts.setdefault(game_id, []).append(
                    "%s %s [%s, in unclassified field(s) %s of a %s record]"
                    % (entry.get("method") or shape, url or "-", why,
                       ", ".join(where) or "?", shape))
    return {
        "ledger_lines": lines,
        "definition": ("contact = sealed id in the request url or request body; "
                       "a sealed id in a response is a listing, not a touch"),
        "sealed_games_contacted": sorted(contacts),
        "contacts": {k: sorted(set(v))[:5] for k, v in contacts.items()},
        "present": present,
        "unreadable": unreadable,
        # `None`, not `True`, when the ledger is absent or partly unreadable.
        # "no sealed game has been touched" is the load-bearing sentence of the
        # held-out design, and it used to be returned as `True` from a file that
        # was never opened -- `clean: not contacts` over an empty dict, printed
        # as "0 calls, sealed ADDRESSED: NONE". Deleting a ledger was a way
        # through this gate; `all_ledger_audit` already knew that about the
        # *other* tracks' ledgers and gave this one the benefit of the doubt.
        "clean": (not contacts) if (present and not unreadable) else None,
        "sealed_ids_seen_in_responses": len(listed),
        "responses_note": ("GET /api/games returns the whole public set, so all "
                           "21 sealed ids appear in read-only responses; that is "
                           "the catalogue the cut was made from"),
        "short_id_stems_checked": sorted(short),
        "record_shapes": dict(sorted(shapes.items())),
        "criterion": sealed_mod.CRITERION,
    }


def all_ledger_audit() -> Dict[str, Any]:
    """Run the sealed-id audit over every track's call records, not just ours.

    The claim "no sealed game has been touched" is project-wide, but
    `recon_ledger.jsonl` only covers this directory. The campaigns run in
    baseline-arms, so a check that never opens its ledger is evidence about the
    wrong place. Those files are read, never written.
    """
    reports = {"arc-recon/data/recon_ledger.jsonl": sealed_api_contacts()}
    for path in OTHER_LEDGERS:
        label = os.path.relpath(path, os.path.join(HERE, os.pardir)
                                ).replace(os.sep, "/")
        if not os.path.exists(path):
            reports[label] = {"present": False, "clean": None,
                              "note": "not present in this checkout"}
            continue
        reports[label] = sealed_api_contacts(path)
    scanned = [r for r in reports.values() if r.get("clean") is not None]
    return {
        "ledgers": reports,
        "all_clean": all(r["clean"] for r in scanned),
        "ledgers_scanned": len(scanned),
        "caveat": ("Other tracks may keep records this list does not name "
                   "(shards, per-campaign files). A clean result here is "
                   "evidence over the files scanned, not a proof over all "
                   "traffic ever sent."),
    }


def register_coverage() -> Dict[str, Any]:
    """Could the contamination log be read at all, and did every line parse?

    `entries()` answered both "the log is missing" and "the log is empty" with
    `[]`, and `current_register` turns `[]` into 21 sealed games at
    `never_audited` / `in_claim_set` -- a full, clean, maximally reassuring claim
    set derived from a file that is not there. Deleting the log was a way through
    the gate.

    A line that will not parse is worse still, because it is a registration
    somebody wrote: the game it names silently keeps its `never_audited` default
    and reads as unexamined rather than as unreadable.
    """
    present = os.path.exists(LOG_PATH)
    problems: List[str] = []
    if not present:
        problems.append(
            "%s does not exist, so every sealed game falls back to its "
            "never_audited default and the register describes no evidence at all"
            % os.path.relpath(LOG_PATH, os.path.join(HERE, os.pardir)).replace(os.sep, "/"))
        return {"present": False, "lines": 0, "problems": problems}
    lines = 0
    try:
        raw = open(LOG_PATH, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as exc:
        problems.append("contamination log could not be read: %s: %s"
                        % (type(exc).__name__, exc))
        return {"present": True, "lines": 0, "problems": problems, "entries": []}
    good: List[Dict[str, Any]] = []
    for i, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        lines += 1
        try:
            entry = json.loads(line)
        except ValueError as exc:
            problems.append("contamination log line %d does not parse (%s); the game it "
                            "registers keeps its never_audited default" % (i, exc))
            continue
        if not isinstance(entry, dict) or "game_id" not in entry or "level" not in entry:
            problems.append("contamination log line %d is missing game_id or level, so it "
                            "registers nothing" % i)
            continue
        # A level outside the vocabulary fails OPEN everywhere downstream:
        # `order.get(level, 0)` in the sort and `LEVELS.index` comparisons treat
        # an unknown value as `never_audited`, the weakest rung. So one typo'd
        # character in `trajectories_reviewed` puts a sealed game whose
        # trajectories were reviewed into the claim set with a green gate. This
        # is the same defect the module already fixed once for the `claims`
        # field (INC-006a), surviving untouched in the field beside it.
        if entry["level"] not in LEVELS:
            problems.append(
                "contamination log line %d registers %s at level %r, which is not one of "
                "%s. An unrecognised level sorts as never_audited -- the weakest rung -- "
                "so it cannot be left to the register to notice."
                % (i, entry.get("game_id"), entry["level"], "/".join(LEVELS)))
        if "claims" in entry and entry["claims"] not in CLAIM_STATES:
            # Already caught by `claim_set()` as an unrecognised claim state for
            # games in the sealed pile. Repeated here because the register covers
            # the dev pile too, where nothing else looks at this field.
            problems.append(
                "contamination log line %d registers %s with claims %r, which is not one "
                "of %s" % (i, entry.get("game_id"), entry["claims"],
                           "/".join(CLAIM_STATES)))
        good.append(entry)

    # A13: an entry whose game_id is not in the cut used to vanish silently.
    # `current_register` skipped it with a bare `continue` -- no counter, no
    # complaint -- so writing `ls20` where `ls20-9607627b` belonged deleted that
    # game's quarantine registration, the register fell back to its
    # `in_claim_set` / `never_audited` default, and the claim set went 19 -> 20
    # with the gate fully green and `problems` empty. The check lives here
    # rather than in `current_register` because this is the only function whose
    # complaints reach `gate()`, and a problem nothing gates on is a comment.
    known = set(piles()["dev_pile"]) | set(piles()["sealed_pile"])
    for entry in good:
        game_id = entry["game_id"]
        if game_id in known:
            continue
        problems.append(
            "contamination log registers %r, which is in neither pile. The cut "
            "names games by their full id, so this registration applies to "
            "nothing and the game it was meant for keeps its never_audited "
            "default -- a dropped quarantine reads as an unexamined game, not "
            "as a missing one. Nearest ids in the cut: %s"
            % (game_id, ", ".join(sorted(
                other for other in known
                if other.split("-")[0] == str(game_id).split("-")[0]) or ["none"])))

    return {"present": True, "lines": lines, "problems": problems, "entries": good}


def entries() -> List[Dict[str, Any]]:
    """Parseable registrations only, read through `register_coverage()`.

    This function and `register_coverage()` were briefly two loops over the same
    file inside the same module -- one collecting rows, one collecting
    complaints, each with its own `open`, its own exception tuple and its own
    idea of what makes a line usable. That is precisely the arrangement this
    whole work order is about ("两份实现一定会漂移"), reintroduced by the fix for
    it: the moment one of them learned to reject an unrecognised `level`, the
    other would have kept feeding that row to the register.

    One read, one set of rules, two views of the result. Unparseable lines are
    skipped here and reported there, so a broken log stays inspectable -- as the
    module docstring promises -- without that tolerance becoming a clean verdict.
    """
    return register_coverage().get("entries", [])


def current_register() -> Dict[str, Dict[str, Any]]:
    """Last entry per game wins; games with no entry keep never_audited."""
    cut = piles()
    register = {game_id: {"level": "never_audited", "pile": pile,
                          "claims": "in_claim_set" if pile == "sealed" else "n/a",
                          "note": "no entry in the contamination log"}
                for pile, ids in (("dev", cut["dev_pile"]),
                                  ("sealed", cut["sealed_pile"]))
                for game_id in ids}
    for entry in entries():
        game_id = entry["game_id"]
        if game_id not in register:
            # Still skipped -- an id outside the cut has no row to update -- but
            # no longer silently: `register_coverage` raises it as a problem and
            # `gate()` turns it red. See the note there.
            continue
        register[game_id] = {
            "level": entry["level"],
            "pile": entry.get("pile", register[game_id]["pile"]),
            "claims": entry.get("claims", register[game_id]["claims"]),
            "note": entry.get("note", ""),
            "t": entry.get("t"),
        }
    return register


def claim_set() -> Dict[str, Any]:
    """Derive the held-out claim set. Fails CLOSED on anything unrecognised.

    The first version of this matched two exact strings and let everything else
    fall through into `clean` -- the fully-uncontaminated set. So a log entry
    with `"claims": "quarantined"` (a typo) or with the field missing entirely
    put a contaminated game into the strongest bucket, silently, and the
    headline 21 -> 19 never moved. That is the same shape as INC-003: a check
    whose failure mode is to report the reassuring answer.

    Two guards now. An unrecognised claim state lands in `needs_adjudication`
    and is excluded from `clean`; and because the level and the claim state are
    two independently hand-written fields, a game registered at or above
    `mechanics_disclosed` that is not quarantined is flagged the same way.
    Nothing here throws -- a broken register must still be readable, and the
    caller needs to see the whole picture to fix it -- but nothing broken can
    quietly count as clean either.
    """
    register = current_register()
    sealed = piles()["sealed_pile"]
    order = {level: i for i, level in enumerate(LEVELS)}
    material = order[MATERIAL_LEVEL]

    quarantined, sensitivity, unrecognised, understated = [], [], [], []
    for game_id in sealed:
        state = register[game_id]["claims"]
        level = register[game_id]["level"]
        if state not in CLAIM_STATES:
            unrecognised.append({"game_id": game_id, "claims": state,
                                 "level": level})
            continue
        if state == "quarantined_from_claims":
            quarantined.append(game_id)
            continue
        if order.get(level, 0) >= material:
            understated.append({"game_id": game_id, "claims": state,
                                "level": level})
            continue
        if state == "retained_with_sensitivity_analysis":
            sensitivity.append(game_id)

    needs_adjudication = sorted(
        [row["game_id"] for row in unrecognised]
        + [row["game_id"] for row in understated])
    quarantined, sensitivity = sorted(quarantined), sorted(sensitivity)
    retained = sorted(g for g in sealed if g not in quarantined)
    return {
        "sealed_pile_size": len(sealed),
        "claim_set_size": len(retained),
        "claim_set": retained,
        "quarantined": quarantined,
        "retained_with_sensitivity_analysis": sensitivity,
        "clean": sorted(g for g in retained
                        if g not in sensitivity and g not in needs_adjudication),
        "needs_adjudication": needs_adjudication,
        "unrecognised_claim_state": unrecognised,
        "retained_above_material_level": understated,
        "rule": ("A held-out claim may name only games in `claim_set`. Games in "
                 "`retained_with_sensitivity_analysis` are in the claim set but "
                 "their exposure is disclosed, so any statistic over the claim "
                 "set must be reported a second time with them excluded; if the "
                 "two disagree, the weaker one governs. Games in "
                 "`needs_adjudication` are in neither `clean` nor any settled "
                 "bucket and must be ruled on before they carry any claim."),
        "piles_hash": verify_piles_hash(),
        "sealed_api_audit": sealed_api_contacts(),
        "cross_track_api_audit": all_ledger_audit(),
        "source": "derived from data/contamination_log.jsonl by contamination.py",
    }


#: `OTHER_LEDGERS` is a hand-written list. The repository holds more
#: ledger-shaped files than it names (per-campaign shards, for one), so a clean
#: audit is evidence over the files scanned and not a proof over all traffic.
#: Reported as a boolean rather than left in prose because a caveat no consumer
#: reads is not a disclosure. It does NOT turn the gate red -- a permanently red
#: gate is a gate nobody looks at -- but it is now a fact a later check can read.
SCAN_SURFACE_IS_SELF_DISCOVERED = False


def gate() -> Dict[str, Any]:
    """Every condition that must turn this check red, in exactly one place.

    `main()` used to end `return 0 if check["matches"] else 1`: the piles.json
    hash and nothing else. Sealed games ADDRESSED in a ledger and games in NEEDS
    ADJUDICATION were computed, printed, and dropped. `verify.sh` grades this
    step by its exit code alone, so the human reading the table was told the
    truth and the machine holding the gate was told "clean" -- and only the
    machine's answer gates anything.

    Both halves now come from here, so the printed table and the exit code
    cannot disagree without someone editing this function.

    Three of the five conditions are about *not having looked*, which is the
    whole point of the work order this implements: a check that could not run
    must not report the answer it would have liked to give.
    """
    reasons: List[str] = []

    piles_hash = verify_piles_hash()
    if not piles_hash["matches"]:
        reasons.append("piles.json no longer hashes to its declared value: the cut has "
                       "been edited, which CLAUDE.md defines as an incident")

    coverage = register_coverage()
    for problem in coverage["problems"]:
        reasons.append("register coverage: %s" % problem)

    summary = claim_set()
    if summary["needs_adjudication"]:
        reasons.append(
            "%d game(s) NEED ADJUDICATION and are in no settled bucket: %s. They were "
            "printed before this change and excluded from the exit code, so the only "
            "reader that gates anything was told the reassuring answer."
            % (len(summary["needs_adjudication"]), ", ".join(summary["needs_adjudication"])))

    cross = summary["cross_track_api_audit"]
    for label, report in sorted(cross["ledgers"].items()):
        if report.get("clean") is False:
            reasons.append(
                "SEALED GAME ADDRESSED in %s: %s. This is the strongest failure this "
                "module can find and it exited 0 on it."
                % (label, ", ".join(report.get("sealed_games_contacted", []))))
        elif report.get("clean") is None:
            reasons.append(
                "%s could not be audited (%s): a ledger that is absent or unreadable is "
                "not a ledger with no sealed contact in it."
                % (label, "absent" if not report.get("present")
                   else "; ".join(report.get("unreadable", []))[:200]))

    # `all([])` is True. Without this, a checkout where every declared ledger had
    # been renamed would compute all_clean=True over an empty scan set and report
    # a clean audit having read nothing at all.
    if cross["ledgers_scanned"] == 0:
        reasons.append("no ledger was scanned at all; the API audit covered nothing")

    return {
        "red": bool(reasons),
        "reasons": reasons,
        "piles_hash_matches": piles_hash["matches"],
        "register_coverage": coverage,
        "needs_adjudication": summary["needs_adjudication"],
        "ledgers_scanned": cross["ledgers_scanned"],
        "all_ledgers_clean": cross["all_clean"],
        "scan_surface_self_discovered": SCAN_SURFACE_IS_SELF_DISCOVERED,
    }


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="contamination.py",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true",
                        help="write data/claim_set.json as well")
    args = parser.parse_args(argv)

    register = current_register()
    check = verify_piles_hash()
    print("  piles.json sha256 %s" % ("MATCHES (cut unmodified)" if check["matches"]
                                      else "MISMATCH -- THE CUT HAS BEEN EDITED"))
    order = {level: i for i, level in enumerate(LEVELS)}
    for game_id, row in sorted(register.items(),
                               key=lambda kv: (-order.get(kv[1]["level"], 0),
                                               kv[0])):
        if row["level"] == "never_audited":
            continue
        print("  %-18s %-8s %-26s %s"
              % (game_id, row["pile"], row["level"], row["claims"]))
    untouched = [g for g, r in register.items() if r["level"] == "never_audited"]
    print("  %d games still never_audited" % len(untouched))

    cross = all_ledger_audit()
    for label, report in sorted(cross["ledgers"].items()):
        if report.get("clean") is None:
            print("  ledger audit: %-40s NOT AUDITED (%s)"
                  % (label, "absent" if not report.get("present") else "unreadable"))
        else:
            # A13: say what was actually read, not "calls". Every one of the 560
            # lines in baseline-arms/ledger.jsonl printed as a "call" while the
            # reader was extracting HTTP fields none of them has; a reader of
            # this table could not tell an audited record from a skipped one.
            shapes = ", ".join("%d %s" % (n, kind) for kind, n
                               in sorted(report.get("record_shapes", {}).items()))
            print("  ledger audit: %-40s %5d records (%s), sealed ADDRESSED: %s"
                  % (label, report["ledger_lines"], shapes or "no records",
                     "NONE" if report["clean"]
                     else ", ".join(report["sealed_games_contacted"])))

    summary = claim_set()
    print("  sealed pile %d -> claim set %d  (quarantined: %s)"
          % (summary["sealed_pile_size"], summary["claim_set_size"],
             ", ".join(summary["quarantined"]) or "none"))
    print("  of which %d carry a sensitivity caveat: %s"
          % (len(summary["retained_with_sensitivity_analysis"]),
             ", ".join(summary["retained_with_sensitivity_analysis"]) or "none"))
    if summary["needs_adjudication"]:
        print("  NEEDS ADJUDICATION (excluded from `clean`): %s"
              % ", ".join(summary["needs_adjudication"]))
        for row in summary["unrecognised_claim_state"]:
            print("    %-18s unrecognised claim state %r"
                  % (row["game_id"], row["claims"]))
        for row in summary["retained_above_material_level"]:
            print("    %-18s level %s but not quarantined"
                  % (row["game_id"], row["level"]))
    verdict = gate()

    # The gate is computed BEFORE the artefact is written, and its verdict is
    # written into it. `verify.sh` runs exactly `contamination.py --json`, and
    # with the contamination log missing this used to overwrite the tracked
    # `claim_set.json` with the maximally reassuring fabrication -- 21 games in
    # the claim set, nothing quarantined, derived from a file that is not there
    # -- and only then return 1. The exit code carried the verdict and the file
    # on disk contradicted it, and the file is what CLAUDE.md points readers at.
    if args.json:
        summary = dict(summary, gate=verdict)
        with open(CLAIM_SET_PATH, "w", encoding="utf-8", newline="") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print("  claim set -> %s%s"
              % (CLAIM_SET_PATH, "  (RECORDED AS RED)" if verdict["red"] else ""))

    if verdict["red"]:
        print("\n  GATE: RED -- %d condition(s) below must be ruled on:"
              % len(verdict["reasons"]))
        for reason in verdict["reasons"]:
            print("    * %s" % reason)
        return 1
    print("\n  GATE: green over %d ledger(s), %d register line(s)."
          % (verdict["ledgers_scanned"], verdict["register_coverage"]["lines"]))
    if not verdict["scan_surface_self_discovered"]:
        print("    caveat, not a failure: the ledger list is hand-written, so this is "
              "evidence over the files scanned, not a proof over all traffic ever sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
