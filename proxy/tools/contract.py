"""The shared contract as a pinned artefact, and a diff that knows which way
a change points.

`proxy/CONTRACT_CHANGES.md` says a change that *narrows* what the proxies
accept is a breaking change and has to be announced before it lands, while a
change that *widens* is free. That rule needs a detector, because the reason it
exists is that a narrowing arrived on a commit an importing track never touched
and nobody -- including the person who wrote it -- noticed it was breaking
(INC-TA-006, $2.695).

So: `proxy/canon_contract.json` pins `canon.describe()`, this module diffs the
live registry against the pin, and `tests/test_contract_changes.py` fails the
suite when they disagree. The failure is the announcement prompt. It does not
and cannot verify that the announcement was made -- a test cannot read
PARTNER_SYNC and judge a paragraph -- but it does guarantee that nobody changes
the contract without being told, at the moment of the change, which kind of
change it was.

    python -m proxy.tools.contract                # verdict against the pin
    python -m proxy.tools.contract --fingerprint  # the one line an importer pins
    python -m proxy.tools.contract --update       # re-pin, and print what is owed

An importing track's obligation is one line in its run manifest: record the
fingerprint, and diff it against the previous run's. A pin that is written and
never diffed documents an incident afterwards rather than preventing one.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

from .. import canon
from ..ledger import ARMS, EVENTS, INCIDENT_KINDS, canonical, sha256

#: The registries `ledger.py` owns and `canon.describe()` does not publish.
#: They are part of the shared contract by the same test as everything else --
#: an arm whose name is not in `ARMS` cannot write a record at all -- so a
#: detector that could not see them would be silently narrower than the rule it
#: enforces. They live here rather than in `canon.describe()` because
#: `ledger.py` imports `canon.py` and not the other way round.
_REGISTRIES = (("events", EVENTS), ("arms", ARMS),
               ("incident_kinds", INCIDENT_KINDS))

SNAPSHOT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "canon_contract.json")

#: Which side of the line each kind of delta falls on.
TIGHTENING = "tightening"      # narrows what is accepted -- breaking
ADDITIVE = "additive"          # widens what is accepted -- free
NEUTRAL = "neutral"            # neither; wording, hints, ordering


def current() -> Dict[str, Any]:
    """The live contract, in the shape the snapshot stores.

    A superset of `canon.describe()`: the field registry plus the three
    registries `ledger.py` owns. `describe()` stays exactly what it was, so a
    reader that pins *it* is unaffected -- this is the wider thing the detector
    watches, not a change to the published one.
    """
    described = canon.describe()
    described.update({name: sorted(values) for name, values in _REGISTRIES})
    return described


def fingerprint(described: Dict[str, Any] = None) -> str:
    """One line an importer can pin and diff. Uses the ledger's own canonical
    JSON so the fingerprint is byte-determined by the contract's content."""
    return sha256(canonical(current() if described is None else described))


class NoSnapshot(FileNotFoundError):
    """There is nothing pinned to diff against. Distinguished from a diff that
    came out empty, because "no snapshot" is a missing safeguard and "no
    deltas" is the safeguard reporting all clear."""


def load_snapshot(path: str = SNAPSHOT_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise NoSnapshot(
            "%s does not exist, so nothing is pinned and a tightening would "
            "pass unnoticed. `python -m proxy.tools.contract --update` writes "
            "it; proxy/CONTRACT_CHANGES.md says what it is for." % path)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["canon"]


def _delta(kind: str, detail: str) -> Dict[str, str]:
    return {"kind": kind, "detail": detail}


def classify(old: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, str]]:
    """Every difference between two contracts, each labelled by direction.

    The direction is the whole point, so each rule below states which way it
    reads rather than leaving it to the caller's intuition -- `required`
    growing and `fields` growing look alike in a diff and are opposites here.
    """
    out: List[Dict[str, str]] = []

    if old.get("ledger_version") != new.get("ledger_version"):
        # §8: a reader must reject a version it does not know. Bumping `v` makes
        # every existing reader reject every new record, which is as breaking as
        # it gets, whatever the change underneath was.
        out.append(_delta(TIGHTENING, "ledger_version %r -> %r: every existing "
                          "reader rejects the new records (§8)"
                          % (old.get("ledger_version"), new.get("ledger_version"))))

    if old.get("additive_safe") and not new.get("additive_safe"):
        out.append(_delta(TIGHTENING, "additive_safe true -> false: an unlisted "
                          "field goes back to being refused, which is INC-TA-006"))
    elif new.get("additive_safe") and not old.get("additive_safe"):
        out.append(_delta(ADDITIVE, "additive_safe false -> true"))

    # -- the envelope: growing it takes fields away from callers -------------
    old_env, new_env = set(old.get("envelope", ())), set(new.get("envelope", ()))
    for name in sorted(new_env - old_env):
        out.append(_delta(TIGHTENING, "envelope gained %r: a caller that sets "
                          "it is now refused" % name))
    for name in sorted(old_env - new_env):
        out.append(_delta(ADDITIVE, "envelope lost %r" % name))

    old_shapes = old.get("shapes") or old.get("closed_shapes") or {}
    new_shapes = new.get("shapes") or new.get("closed_shapes") or {}
    # Diff the shapes once, under whichever spelling carries them -- but the
    # *spellings themselves* are published keys and are diffed below like any
    # other. C-003 schedules removing the deprecated `closed_shapes` alias, and
    # a detector that cannot see the one change already on the calendar is
    # decoration.
    for shape in sorted(set(old_shapes) | set(new_shapes)):
        if shape not in new_shapes:
            out.append(_delta(TIGHTENING, "shape %r removed" % shape))
            continue
        if shape not in old_shapes:
            out.append(_delta(ADDITIVE, "shape %r added" % shape))
            continue
        before, after = old_shapes[shape], new_shapes[shape]
        for name in sorted(set(after.get("fields", ())) - set(before.get("fields", ()))):
            out.append(_delta(ADDITIVE, "%s.%s defined" % (shape, name)))
        for name in sorted(set(before.get("fields", ())) - set(after.get("fields", ()))):
            # Undefining a field does not delete it from the disk; it demotes
            # every record that carries it to "unknown field", which under
            # additive-safe is a warning and under the old rule was a refusal.
            out.append(_delta(TIGHTENING, "%s.%s undefined: records carrying it "
                              "stop being canonical" % (shape, name)))
        for name in sorted(set(after.get("required", ())) - set(before.get("required", ()))):
            out.append(_delta(TIGHTENING, "%s.%s became required: every writer "
                              "that omits it is refused, and §8 says this bumps "
                              "`v`" % (shape, name)))
        for name in sorted(set(before.get("required", ())) - set(after.get("required", ()))):
            out.append(_delta(ADDITIVE, "%s.%s no longer required" % (shape, name)))

    old_aux = old.get("auxiliary_required", {})
    new_aux = new.get("auxiliary_required", {})
    for event in sorted(set(old_aux) | set(new_aux)):
        before = set(old_aux.get(event, ()))
        after = set(new_aux.get(event, ()))
        if event not in old_aux:
            # A brand-new auxiliary event nobody writes yet cannot break a
            # writer; its required keys arrive with it.
            out.append(_delta(ADDITIVE, "auxiliary %r added" % event))
            continue
        for name in sorted(after - before):
            out.append(_delta(TIGHTENING, "auxiliary %s now requires %r"
                              % (event, name)))
        for name in sorted(before - after):
            out.append(_delta(ADDITIVE, "auxiliary %s no longer requires %r"
                              % (event, name)))

    for name, _ in _REGISTRIES:
        before, after = set(old.get(name, ())), set(new.get(name, ()))
        for value in sorted(before - after):
            # `ledger.append` refuses an unregistered arm or event outright, so
            # dropping one stops a writer that was working yesterday.
            out.append(_delta(TIGHTENING, "%s lost %r: a writer using it is "
                              "refused" % (name, value)))
        for value in sorted(after - before):
            out.append(_delta(ADDITIVE, "%s gained %r" % (name, value)))

    old_ban = old.get("banned_spellings", {})
    new_ban = new.get("banned_spellings", {})
    for name in sorted(set(new_ban) - set(old_ban)):
        out.append(_delta(TIGHTENING, "%r is now a banned spelling: a writer "
                          "using it is refused" % name))
    for name in sorted(set(old_ban) - set(new_ban)):
        out.append(_delta(ADDITIVE, "%r is no longer banned" % name))
    for name in sorted(set(old_ban) & set(new_ban)):
        if old_ban[name] != new_ban[name]:
            out.append(_delta(NEUTRAL, "the hint for %r was reworded" % name))

    for key in sorted(set(old) - set(new)):
        out.append(_delta(TIGHTENING, "the published key %r was removed" % key))
    for key in sorted(set(new) - set(old)):
        out.append(_delta(ADDITIVE, "the published key %r was added" % key))

    return out


#: The parts of a contract `classify()` actually models. Everything else is the
#: residual, and a residual that moved is a change nobody reviewed.
_MODELLED_TOP = (("ledger_version", "additive_safe", "envelope",
                  "auxiliary_required", "banned_spellings")
                 + tuple(name for name, _ in _REGISTRIES))
_MODELLED_IN_SHAPE = ("fields", "required")


def residual(described: Dict[str, Any]) -> Dict[str, Any]:
    """What is left of a contract after removing everything `classify()` looks
    at. Two contracts with equal residuals differ only in ways the classifier
    was written to explain; unequal residuals mean it was not.

    This exists because "the classifier found no tightening" and "the
    classifier understood the change" are different statements, and only the
    second one is a clearance.
    """
    out = {k: v for k, v in described.items() if k not in _MODELLED_TOP}
    for spelling in ("shapes", "closed_shapes"):
        shapes = out.get(spelling)
        if isinstance(shapes, dict):
            out[spelling] = {
                name: {k: v for k, v in (shape or {}).items()
                       if k not in _MODELLED_IN_SHAPE}
                for name, shape in shapes.items()}
    return out


def verdict(deltas: List[Dict[str, str]]) -> str:
    if any(d["kind"] == TIGHTENING for d in deltas):
        return "TIGHTENING"
    if any(d["kind"] == ADDITIVE for d in deltas):
        return "ADDITIVE"
    if deltas:
        return "NEUTRAL"
    return "UNCHANGED"


def report(path: str = SNAPSHOT_PATH) -> Dict[str, Any]:
    """Compare the live registry to the pin.

    **The fingerprint is the authority; `classify()` is only the explanation.**
    Getting that the other way round is the failure mode this tool is supposed
    to prevent, one level up: a classifier only sees the deltas it was written
    to model, so any change nobody anticipated would come back `UNCHANGED` --
    not mislabelled, which is visible, but *cleared*, which is not. So when the
    hashes disagree and the classifier has nothing to say, the difference is
    reported as a tightening. Unexplained is the one case that must not be
    quiet, and an over-strict verdict costs a re-read while an over-permissive
    one costs what INC-TA-006 cost.
    """
    live = current()
    pinned = load_snapshot(path)
    deltas = classify(pinned, live)
    pinned_fp, live_fp = fingerprint(pinned), fingerprint(live)
    if pinned_fp != live_fp and residual(pinned) != residual(live):
        # Not `and not deltas`: a change can be half-explained. If the
        # classifier reported one additive delta and something it does not
        # model *also* moved, the additive verdict would clear the part nobody
        # looked at.
        deltas = deltas + [_delta(
            TIGHTENING,
            "the contract's fingerprint moved (%s -> %s) in a way the "
            "classifier does not model. Treated as a tightening until someone "
            "says otherwise: an unmodelled delta is unreviewed, not harmless. "
            "Diff %s against `python -m proxy.tools.contract --json`."
            % (pinned_fp, live_fp, path))]
    return {"snapshot": path,
            "pinned_fingerprint": pinned_fp,
            "live_fingerprint": live_fp,
            "deltas": deltas,
            "verdict": verdict(deltas)}


def write_snapshot(path: str = SNAPSHOT_PATH) -> str:
    live = current()
    blob = {
        "note": ("The shared ledger contract, pinned. Regenerate with "
                 "`python -m proxy.tools.contract --update`, and read "
                 "proxy/CONTRACT_CHANGES.md before you do -- a diff here that "
                 "narrows what the proxies accept is a breaking change for "
                 "every track that imports proxy/ as a library."),
        "fingerprint": fingerprint(live),
        "canon": live,
    }
    text = json.dumps(blob, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return blob["fingerprint"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--snapshot", default=SNAPSHOT_PATH)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fingerprint", action="store_true",
                    help="print the live contract fingerprint and nothing else")
    ap.add_argument("--update", action="store_true",
                    help="re-pin the snapshot to the live registry")
    args = ap.parse_args(argv)

    if args.fingerprint:
        print(fingerprint())
        return 0

    if args.update:
        try:
            owed = [d for d in report(args.snapshot)["deltas"]
                    if d["kind"] == TIGHTENING]
        except NoSnapshot:
            owed = []                    # first pin: there is nothing to break
        new_fp = write_snapshot(args.snapshot)
        print("re-pinned %s at %s" % (args.snapshot, new_fp))
        if owed:
            # Writing the snapshot is not the procedure; it is the last step of
            # it. Saying so here is the only place a person who took the
            # shortcut will be standing.
            print("\n%d tightening(s) in this change. CONTRACT_CHANGES.md §3 "
                  "owes each one a PARTNER_SYNC announcement, one cycle of "
                  "notice, and a compatibility window:" % len(owed))
            for delta in owed:
                print("  - %s" % delta["detail"])
            return 1
        return 0

    rep = report(args.snapshot)
    if args.json:
        print(json.dumps(rep, indent=2, sort_keys=True))
    else:
        print("%s: %s" % (rep["snapshot"], rep["verdict"]))
        print("  pinned %s" % rep["pinned_fingerprint"])
        print("  live   %s" % rep["live_fingerprint"])
        for delta in rep["deltas"]:
            print("  %-10s %s" % (delta["kind"], delta["detail"]))
    return 0 if rep["verdict"] == "UNCHANGED" else 1


if __name__ == "__main__":
    sys.exit(main())
