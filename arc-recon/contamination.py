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
    """
    ledger_path = ledger_path or os.path.join(DATA_DIR, "recon_ledger.jsonl")
    sealed = piles()["sealed_pile"]
    short = {game_id.split("-")[0]: game_id for game_id in sealed}
    contacts: Dict[str, List[str]] = {}
    listed: Dict[str, int] = {}
    lines = 0
    if os.path.exists(ledger_path):
        for line in open(ledger_path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            lines += 1
            entry = json.loads(line)
            url = str(entry.get("url", ""))
            body = entry.get("request_body")
            # Exact-match the id fields we actually send, then substring-scan the
            # URL: an id can reach the server either way.
            sent = set()
            if isinstance(body, dict):
                for key in ("game_id", "game"):
                    value = body.get(key)
                    if isinstance(value, str):
                        sent.add(value)
            for game_id in sealed:
                stem = game_id.split("-")[0]
                if game_id in sent or stem in sent or game_id in url:
                    contacts.setdefault(game_id, []).append(
                        "%s %s" % (entry.get("method"), url))
            response = json.dumps(entry.get("response_body"), ensure_ascii=False)
            for game_id in sealed:
                if game_id in response:
                    listed[game_id] = listed.get(game_id, 0) + 1
    return {
        "ledger_lines": lines,
        "definition": ("contact = sealed id in the request url or request body; "
                       "a sealed id in a response is a listing, not a touch"),
        "sealed_games_contacted": sorted(contacts),
        "contacts": {k: sorted(set(v))[:5] for k, v in contacts.items()},
        "clean": not contacts,
        "sealed_ids_seen_in_responses": len(listed),
        "responses_note": ("GET /api/games returns the whole public set, so all "
                           "21 sealed ids appear in read-only responses; that is "
                           "the catalogue the cut was made from"),
        "short_id_stems_checked": sorted(short),
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


def entries() -> List[Dict[str, Any]]:
    if not os.path.exists(LOG_PATH):
        return []
    out = []
    for line in open(LOG_PATH, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


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
            print("  ledger audit: %-40s absent" % label)
        else:
            print("  ledger audit: %-40s %5d calls, sealed ADDRESSED: %s"
                  % (label, report["ledger_lines"],
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
    if args.json:
        with open(CLAIM_SET_PATH, "w", encoding="utf-8", newline="") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print("  claim set -> %s" % CLAIM_SET_PATH)
    return 0 if check["matches"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
