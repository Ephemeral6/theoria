"""browser-ops' completion gate — the territory whose whole output is a record.

    cd browser-ops && python verify.py

This directory holds no code. Its product is `terms_canary.json`: a fingerprint
of the pages whose wording binds us -- ARC's terms and rate limits -- so that a
change upstream is noticed rather than discovered later by being in breach.

A territory whose product is a record has exactly one way to fail quietly: the
record stops being maintained and still looks like a record. Nothing errors. The
file is present, parses, and is simply older every day, while the page it
watches drifts. That is this repository's default suspect, and it is the only
thing worth gating here.

## What it checks, and what it deliberately cannot

  1. the canary parses and every check carries the fields a fingerprint needs
     -- a URL, a hash, the lengths, and *why it matters*, which is the field
     that stops the file becoming a list of hashes nobody can act on;
  2. the fingerprints are non-degenerate: a zero length or an empty hash is a
     check that would match anything, which is worse than no check;
  3. the history is present, ordered, and every verdict resolves to one of the
     known ones -- an unrecognised verdict is not a pass. A verdict may add a
     short parenthetical qualifier (`DRIFT (cosmetic scope)`); the base token
     is what must be recognised.

**It cannot tell you the canary is current.** Fetching the page needs a real
browser, a human-approved session, and network -- none of which belong in a
merge gate. So this reports the age of the newest history entry and says
plainly that freshness is asserted by whoever last ran the canary, not by this
file. Stating that is the point: a gate that implied it had checked the live
page would be worse than no gate.
"""

import argparse
import calendar
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CANARY = os.path.join(HERE, "terms_canary.json")

#: Fields a fingerprint needs to be actionable rather than merely present.
#:
#: `raw_len` is NOT here, and the omission is deliberate rather than a
#: concession. The first version of this list required it, met the real file,
#: and reported two checks incomplete -- but `raw_len` is present on two of the
#: four pages and absent on the other two by design, because those are rendered
#: pages with no stable raw length to record. The check that fired was mine,
#: not the record's.
#:
#: Saying that is worth a comment, because "the gate went red so I widened it"
#: is how a gate becomes decorative. The test is whether the dropped field is
#: absent *by design* or absent *because someone forgot*: `raw_len` is the
#: first, so it goes; every field below is present on all four and is load
#: bearing -- `anchors` is what makes a detected change locatable rather than
#: merely announced, and `why_it_matters` is what stops the file becoming a
#: list of hashes nobody can act on.
CHECK_FIELDS = ("id", "url", "fnv1a64", "norm_len", "anchors",
                "why_it_matters")

#: Verdicts the record is allowed to contain. An unknown one is refused rather
#: than assumed benign -- "I do not recognise this" must not read as "fine".
#: Compared case-insensitively; the record writes them upper-case. `NO-DRIFT`
#: was in use and not in my first list -- again the gate's error, not the
#: record's. The set stays closed rather than becoming "anything the file
#: contains", which would make the check circular and unable to fail.
VERDICTS = {"unchanged", "changed", "baseline", "unreachable", "drift",
            "no-drift"}

#: A verdict may carry a trailing parenthetical qualifier -- `DRIFT (cosmetic
#: scope)` -- and the *base token* is what must be in the closed set above.
#:
#: This is the third time this gate has met the record and been the one in the
#: wrong, and it is worth writing down why this is a correction rather than the
#: usual retreat. The record never declared a verdict vocabulary; `_procedure`
#: describes what to compare, not what to call the result. The closed set is
#: something this gate inferred from the two verdicts that existed when it was
#: written. When OPS-B's cycle 12 found the first real drift, it recorded
#: `DRIFT (cosmetic scope)` -- the alarming token, plus how far the alarm
#: reaches. The gate refused it.
#:
#: What decides it is that (A) is unreachable. To satisfy exact matching, entry
#: 2's `verdict` would have to be rewritten -- and that record is explicitly
#: append-only ("旧条目按追加式纪律不改，订正记在这里"), which is also how it
#: absorbed this very drift: the baseline `fnv1a64` was kept and a dated
#: `fnv1a64_2026-07-29T11:11Z` added beside it. A gate that can only go green by
#: rewriting published history is a gate at war with the invariant it is meant
#: to protect.
#:
#: What is given up, stated plainly: `NO-DRIFT (except two pages changed)` would
#: now pass, and under exact matching it would not have. That is a real loss and
#: not one I can close by parsing prose. It is bounded rather than open, though:
#: the base token still comes from the closed set, so `REVIEWED`, `OK-ish`, `""`
#: and `drift-ish (scope)` all still fail hard, which is the thing the check
#: exists for -- an unrecognised verdict must not read as a pass. And the
#: qualifier is capped at a label's length, so a verdict cannot become a
#: paragraph with the classification buried in it.
QUALIFIER_MAX = 40

#: Floors. Two pages is the minimum that makes this a watch rather than a note,
#: and one history entry means it has never actually been run twice.
MIN_CHECKS = 2
MIN_HISTORY = 1

#: Beyond this the record is stale enough to say so out loud. Not a failure --
#: this file cannot refresh it -- but not silent either.
STALE_DAYS = 14


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def split_verdict(text):
    """`"DRIFT (cosmetic scope)"` -> `("drift", "cosmetic scope")`.

    Returns `(base, qualifier, problem)`. `problem` is None when the shape is
    acceptable. A bare verdict yields an empty qualifier. Anything that is not
    either `BASE` or `BASE (label)` -- trailing junk after the paren, an empty
    base, nested parens -- is refused, so this stays a two-part shape rather
    than becoming "any string containing a known word".
    """
    raw = (text or "").strip()
    base, qualifier = raw, ""
    if raw.endswith(")") and "(" in raw:
        head, _, tail = raw.partition("(")
        base, qualifier = head.strip(), tail[:-1].strip()
        if "(" in qualifier or ")" in qualifier:
            return base.lower(), qualifier, "its qualifier has nested parentheses"
        if not qualifier:
            return base.lower(), qualifier, "its parenthetical qualifier is empty"
        if len(qualifier) > QUALIFIER_MAX:
            return (base.lower(), qualifier,
                    "its qualifier is %d characters, over the %d-character cap "
                    "-- a qualifier is a label, not a paragraph with the "
                    "classification buried in it"
                    % (len(qualifier), QUALIFIER_MAX))
    elif "(" in raw or ")" in raw:
        return raw.lower(), "", "its parentheses are unbalanced or misplaced"
    return base.lower(), qualifier, None


def parse_utc(text):
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ", "%Y-%m-%d"):
        try:
            return calendar.timegm(time.strptime(text, fmt))
        except (ValueError, TypeError):
            continue
    return None


def main():
    argparse.ArgumentParser().parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    problems = []

    print("[1/3] the canary parses and its checks are complete")
    if not os.path.exists(CANARY):
        fail(problems, "terms_canary.json is absent -- this territory's only "
                       "product is the record, so an absent record is the "
                       "whole territory missing")
        print("\nbrowser-ops: RED (1 problem)")
        return 1
    try:
        data = json.load(open(CANARY, encoding="utf-8"))
    except Exception as exc:
        fail(problems, "terms_canary.json does not parse: %s" % exc)
        print("\nbrowser-ops: RED (1 problem)")
        return 1

    checks = data.get("checks")
    if not isinstance(checks, list) or len(checks) < MIN_CHECKS:
        fail(problems, "%d check(s), floor is %d -- fewer than two watched "
                       "pages is a note, not a watch"
             % (len(checks or []), MIN_CHECKS))
    else:
        for i, c in enumerate(checks):
            missing = [f for f in CHECK_FIELDS if f not in c]
            if missing:
                fail(problems, "check %d (%s) is missing %s"
                     % (i, c.get("id", "?"), ", ".join(missing)))
                break
        else:
            print("   ok    %d check(s), each with all %d fields"
                  % (len(checks), len(CHECK_FIELDS)))

    print("[2/3] the fingerprints could actually fail to match")
    if isinstance(checks, list):
        degenerate = [c.get("id", "?") for c in checks
                      if not c.get("fnv1a64")
                      or not isinstance(c.get("norm_len"), int)
                      or c.get("norm_len", 0) <= 0]
        if degenerate:
            # A hash of nothing matches nothing and never fires; a zero length
            # is a fingerprint of an empty page. Either is a check that cannot
            # go red, which is this lane's definition of a negative asset.
            fail(problems, "%d degenerate fingerprint(s) (%s): an empty hash or "
                           "a zero length is a check that can never fire"
                 % (len(degenerate), ", ".join(degenerate[:4])))
        else:
            print("   ok    every fingerprint has a hash and a non-zero length")

    print("[3/3] the history is readable, ordered, and freshness is stated")
    history = data.get("history")
    if not isinstance(history, list) or len(history) < MIN_HISTORY:
        fail(problems, "history holds %d entry(ies), floor is %d -- a canary "
                       "that has never been run twice has not been run"
             % (len(history or []), MIN_HISTORY))
    else:
        stamps = []
        for i, h in enumerate(history):
            base, _qual, shape = split_verdict(h.get("verdict"))
            if shape is not None:
                fail(problems, "history entry %d has verdict %r and %s"
                     % (i, h.get("verdict"), shape))
                break
            if base not in VERDICTS:
                fail(problems, "history entry %d has verdict %r, whose base "
                               "token %r is not one of %s -- an unrecognised "
                               "verdict is not a pass"
                     % (i, h.get("verdict"), base, sorted(VERDICTS)))
                break
            t = parse_utc(h.get("utc"))
            if t is None:
                fail(problems, "history entry %d has an unreadable utc %r"
                     % (i, h.get("utc")))
                break
            stamps.append(t)
        else:
            if stamps != sorted(stamps):
                fail(problems, "the history is not in chronological order; a "
                               "record whose order cannot be trusted cannot "
                               "answer 'what changed when'")
            else:
                age_d = (time.time() - stamps[-1]) / 86400.0
                print("   ok    %d entry(ies), in order; newest is %.1f day(s) "
                      "old" % (len(history), age_d))
                if age_d > STALE_DAYS:
                    print("   note  older than %d days. This gate CANNOT "
                          "refresh it -- fetching the page needs a real "
                          "browser, an approved session and network, none of "
                          "which belong in a merge gate. Freshness is asserted "
                          "by whoever last ran the canary, not by this file."
                          % STALE_DAYS)

    print()
    if problems:
        print("browser-ops: RED (%d problem(s))" % len(problems))
        return 1
    print("browser-ops: green -- the record is complete, its fingerprints can "
          "fail, and its age is stated rather than implied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
