"""One place that decides whether a sealed game appears in something.

Before this file there were three, and they disagreed:

* `precheck.assert_playable` -- full id, plus a stem *collision* check between
  the dev and sealed piles. Guards the outbound direction, never the ledger.
* `contamination.sealed_api_contacts` -- full id or stem, but only when it is
  the entire value of `request_body["game_id"]` or `["game"]`, plus a full-id
  substring test on the URL.
* `cascade/verify.py` A7 -- a full-id substring of `json.dumps(request_body)`,
  no stem, no URL, and `request_body or {}` so a body of `None` passes
  vacuously.

Three implementations of one sentence is the arrangement `contamination.entries`
already has a docstring about: two implementations will drift, and these had.
The bill came due in a specific way. `cascade/probe.py:216` opens a scorecard
with `tags=["p20-cascade", game.split("-")[0]]`, so a **bare stem** goes into a
request body on every cascade run -- and neither ledger audit could see it. A7
compares full ids; `contamination` only looked inside two named keys, and the
stem was under `tags`. Both would have reported clean on a request that named a
sealed game, had the game been sealed.

**The criterion, in one place, in three parts.** A sealed game is present in a
payload when any of these holds:

1. its **full id** (`ls20-9607627b`) appears anywhere in the payload;
2. its **stem** (`ls20`) appears anywhere in the payload *as a whole token* --
   not as a fragment of a longer word, which is what keeps a hex digest from
   colliding with one;
3. either of the above appears in the **URL**, which is a payload like any
   other and is passed in as one.

Part 2 is the part the old implementations kept dropping, and INC-005 recorded
the live API accepting the short form, so it is not hypothetical. Part 3 is the
part `cascade/verify.py` never had.

**What this module deliberately does not decide.** Whether a hit is a *contact*
or a *listing*. `GET /api/games` returns all twenty-five ids by construction, so
a sealed id in a response is the catalogue the cut was made from, not a touch --
scoring it as contact would make the audit incapable of ever coming back clean.
That distinction belongs to the caller, which knows which half of a record it is
holding; this module only answers "is it in there".
"""

import json
import os
import re
from typing import Any, Dict, Iterable, List, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
PILES_PATH = os.path.join(HERE, "data", "piles.json")


def piles(path: str = None) -> Dict[str, Any]:
    with open(path or PILES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def sealed_pile(path: str = None) -> List[str]:
    return list(piles(path)["sealed_pile"])


def dev_pile(path: str = None) -> List[str]:
    return list(piles(path)["dev_pile"])


def stem(game_id: str) -> str:
    """The short form the live API also accepts (INC-005)."""
    return game_id.split("-")[0]


def as_text(payload: Any) -> str:
    """A payload as the string the criterion searches.

    `json.dumps` rather than `str` so that a dict, a list, a bare string and
    `None` all become searchable text by one rule, and so that nothing depends
    on Python's repr. `default=str` because a payload read from a ledger can
    carry anything a writer put there, and a `TypeError` here would abort an
    audit -- which is the failure mode this whole work order is about.
    """
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(payload)


def _stem_pattern(short: str) -> "re.Pattern":
    # Whole-token: not preceded or followed by another id character. `ar25`
    # matches in `["p20-cascade", "ar25"]` and in `ar25-0c556536`, and does not
    # match inside `war2500`.
    return re.compile(r"(?<![0-9A-Za-z])%s(?![0-9A-Za-z])" % re.escape(short))


def hits(payload: Any, sealed: Sequence[str] = None) -> Dict[str, str]:
    """Which sealed games appear in `payload`, and by which part of the rule.

    Returns `{game_id: "full id" | "stem"}`. Empty means the payload names no
    sealed game -- by the *whole* criterion, so an empty result here is a real
    check having been made and not a field having been missed.
    """
    text = as_text(payload)
    if not text:
        return {}
    found: Dict[str, str] = {}
    for game_id in (sealed if sealed is not None else sealed_pile()):
        if game_id in text:
            found[game_id] = "full id"
            continue
        if _stem_pattern(stem(game_id)).search(text):
            found[game_id] = "stem"
    return found


def hits_in_any(payloads: Iterable[Any],
                sealed: Sequence[str] = None) -> Dict[str, str]:
    """`hits` over several payloads, first reason per game wins."""
    sealed = list(sealed if sealed is not None else sealed_pile())
    found: Dict[str, str] = {}
    for payload in payloads:
        for game_id, why in hits(payload, sealed).items():
            found.setdefault(game_id, why)
    return found


CRITERION = ("a sealed game is present when its full id appears anywhere in the "
             "payload, or its short stem appears as a whole token; the URL is "
             "searched as a payload like any other. Whether a hit is a contact "
             "or a listing is the caller's call, not this module's.")
