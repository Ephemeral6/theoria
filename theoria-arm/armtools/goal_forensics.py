"""goal_forensics -- what became of the goal ask, per leg, from the archive.

**The question this answers.** R1b ran `goal_protocol=propose`. The arm booked
proposals, its mode moved from silence to `exploring_no_goal`, and
`goal_declared_ever` stayed `False` with `plan` reporting `no_goal_declared`
16 times out of 16. "The mechanism fired and did not connect" is true and is
not a diagnosis: it is consistent with four completely different events, which
need four completely different fixes.

* the desk **never saw** the ask,
* it saw it and **ignored** it,
* it answered and the answer **never reached the manual**,
* it answered and the **parser rejected** the goal clause.

Only the records can say which, and on R1b they say *two different things on
the two legs*, which is exactly why a single sentence about the round was
never going to be right.

**What the records say.** On `20260801T001851Z-R1b-g50t-a` the rider was
delivered three times and answered three times, each time
`declined_with_argument`, each time with the theorem
`the_goal_is_absent_because_no_instance_can_name_the_socket` whose body
enumerates the four goal forms this grammar admits and refutes each one
against the frame in front of it. That is not a mechanism failing to connect.
That is a desk taking a position, and the position is about **expressive
reach**: the socket cells have never changed, so they are board, so no
instance is seated on them, so no `count(...)` ranges over them and no
`Cart.pos = <landmark>` names them. `20260801T0900Z-R2-frontier-by-generation`
measured the same wall from the other side -- 12 of 47 off-frontier probes
missed by exactly one never-before-changed cell -- without either finding
knowing about the other.

On `20260801T001851Z-R1b-sk48-b` the rider was **booked and never delivered**.
It parks for the next theorize call a surprise pays for; the next three turns
skipped theorize under the new-transitions gate, the beat after that lost every
one of its five replies in transit (`armtools/replyloss.py`), and the leg then
hit its spend reservation. The ask sat in memory for the whole leg and the
record says so honestly -- `"answered": null` -- but nothing in the summary
distinguishes an ask that was refused from an ask that was never posted, and
`_reading` calls both "proposal(s) were made".

**Why this is a tool and not a paragraph.** The paragraph above is a reading of
two legs by one session. This module re-derives it from tracked files on every
run, over every leg in the archive, and will contradict the paragraph the
moment the archive stops supporting it. A finding that cannot be re-run is a
memory.

    python -m armtools.goal_forensics --runs-root theoria-arm/runs
"""

import argparse
import io
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from armtools import replyloss
from inner import goal as goal_beat

#: The closed set of leg verdicts, ordered from "the question does not arise"
#: to "the question was answered". Each names the fix it implies, because a
#: verdict that does not change what anybody does is a label.
VERDICTS = {
    "not_measured": "the leg carries no per-turn goal block: it ran before "
                    "inner/goal.py existed, or on the `off` rung. Nothing "
                    "here is evidence about the rider either way.",
    "recorded_only": "the leg ran on the `record` rung, which observes and "
                     "writes and never asks. No proposal can have been made "
                     "and none was.",
    "never_booked": "the leg ran on `propose` and the criterion refused every "
                    "turn. The fix, if one is wanted, is the criterion in "
                    "goal.proposal_due -- not the rider, which was never "
                    "written.",
    "booked_never_delivered": "the criterion fired and the ask never reached "
                              "the desk: it parks for the next theorize call "
                              "a surprise pays for, and no such call completed "
                              "before the leg ended. The fix is in DELIVERY, "
                              "not in the wording -- the desk has said "
                              "nothing about a question it was never asked.",
    "delivered_answer_lost": "the ask was delivered and the reply did not "
                             "survive the transport. The fix is "
                             "harness/modelcall.py, and the desk's opinion on "
                             "the goal is unknown, not negative.",
    "declined_with_argument": "the desk answered, refused, and signed the "
                              "refusal with a named theorem. This is a "
                              "position, not a miss. The fix -- if the "
                              "position is wrong -- is the argument, which "
                              "means the rider's wording or the goal grammar, "
                              "and NOT the plumbing.",
    "signed": "the desk answered with a goal clause and the manual now "
              "declares a winning condition.",
    "silent": "the ask was delivered, a reply came back, and the manual "
              "carries neither a goal nor an argument about its absence. This "
              "is the only outcome that is a defect in the ANSWER.",
}

#: How `inner/loop.py` writes the rider's fate into a turn record.
_DELIVERED = "delivered"
_ANSWERED_PREFIX = "answered: "


def _load(path: str) -> Optional[Any]:
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except ValueError:
            return None


def _goal_blocks(turns: Any) -> List[Dict[str, Any]]:
    if not isinstance(turns, list):
        return []
    return [t["goal"] for t in turns
            if isinstance(t, dict) and isinstance(t.get("goal"), dict)]


def rider_deliveries(turns: Any) -> List[Dict[str, Any]]:
    """Every turn whose record carries a `goal_rider` field, with its fate.

    `inner/loop.py` writes `"delivered"` when the rider is taken off the peg
    and overwrites it with `"answered: <outcome>"` once the reply is read. A
    row still saying `"delivered"` is a call that went out and whose answer the
    beat never got to read -- which on this archive means the call raised.
    """
    out = []
    if not isinstance(turns, list):
        return out
    for row in turns:
        if not isinstance(row, dict):
            continue
        rider = row.get("goal_rider")
        if not rider:
            continue
        answered = None
        if isinstance(rider, str) and rider.startswith(_ANSWERED_PREFIX):
            answered = rider[len(_ANSWERED_PREFIX):]
            if answered == "None":
                answered = None
        out.append({"turn": row.get("turn"), "raw": rider,
                    "answered": answered})
    return out


def extract_refusal_theorems(theory_text: Optional[str]) -> List[Dict[str, str]]:
    """The theorems that argue the goal's absence, name and body.

    `inner/goal.absence_signature` returns only the first NAME, which is what
    the loop needs and not what a reader needs. The argument is in the body,
    and the whole point of the `declined_with_argument` verdict is that there
    IS one -- so the record has to be able to show it.

    The DSL's theorem form is ``theorem <name> "<prose>"``; the body is taken
    up to the closing quote, which the grammar does not let a body contain.
    """
    text = theory_text or ""
    out = []
    for match in re.finditer(r'^\s*theorem\s+(\w+)\s+"([^"]*)"', text, re.M):
        name, body = match.group(1), match.group(2)
        low = name.lower()
        if "goal" in low and any(w in low for w in goal_beat._ABSENCE_WORDS):
            out.append({"theorem": name, "argument": body})
    return out


def extract_target_theorems(theory_text: Optional[str]) -> List[Dict[str, str]]:
    """The winning position the desk believes in but could not compile.

    `inner/goal.prompt_rider`'s third channel asks for this under a fixed name
    prefix so it can be found without guessing. It is deliberately NOT part of
    `absence_signature`: a manual can decline a goal and still name its target,
    and collapsing the two would let a named target read as an argument for
    having none.

    Returns `[]` on every manual written before the third channel existed --
    including the two R1b legs, whose targets are in theorems named for their
    own subject matter (`the_socket_is_a_keyhole_...`) and which this function
    correctly does not claim to have found.
    """
    out = []
    for match in re.finditer(r'^\s*theorem\s+(\w+)\s+"([^"]*)"',
                             theory_text or "", re.M):
        if match.group(1).startswith(goal_beat.TARGET_THEOREM_PREFIX):
            out.append({"theorem": match.group(1), "target": match.group(2)})
    return out


def leg(leg_dir: str) -> Dict[str, Any]:
    """One leg's rider story, from its own tracked files."""
    name = os.path.basename(leg_dir.rstrip(os.sep))
    turns = _load(os.path.join(leg_dir, "turns.json"))
    state = _load(os.path.join(leg_dir, "RUN_STATE.json")) or {}
    summary = state.get("goal") if isinstance(state, dict) else None
    blocks = _goal_blocks(turns)
    deliveries = rider_deliveries(turns)

    theory_path = os.path.join(leg_dir, "books", "theory.dsl")
    theory = None
    if os.path.isfile(theory_path):
        with io.open(theory_path, encoding="utf-8") as fh:
            theory = fh.read()

    out: Dict[str, Any] = {
        "leg": name,
        "protocol": (summary or {}).get("protocol"),
        "turns_with_a_goal_block": len(blocks),
        "proposals_booked": len((summary or {}).get("proposals") or []),
        "rider_deliveries": deliveries,
        "answers": [d["answered"] for d in deliveries],
        "goal_declared_ever": (summary or {}).get("goal_declared_ever"),
        "absence_signature": (summary or {}).get("absence_signature"),
        "plan_status_counts": (summary or {}).get("plan_status_counts"),
        "refusal_theorems": extract_refusal_theorems(theory),
        "target_theorems": extract_target_theorems(theory),
    }
    out["proposals_delivered"] = (summary or {}).get("proposals_delivered")

    answers = [a for a in out["answers"] if a]
    if not blocks:
        verdict = "not_measured"
    elif out["protocol"] == "record":
        verdict = "recorded_only"
    elif not out["proposals_booked"]:
        verdict = "never_booked"
    elif not deliveries:
        verdict = "booked_never_delivered"
    elif "signed" in answers:
        verdict = "signed"
    elif "declined_with_argument" in answers:
        verdict = "declined_with_argument"
    elif "silent" in answers:
        verdict = "silent"
    else:
        verdict = "delivered_answer_lost"

    out["verdict"] = verdict
    out["what_it_means"] = VERDICTS[verdict]

    # The transport, joined in. A leg that declined with an argument AND lost
    # replies has two separate things wrong with it and the verdict names only
    # the first; saying so beats picking one.
    loss = replyloss.sweep_leg(leg_dir)
    out["transport"] = {
        "has_transcripts": loss["has_transcripts"],
        "counts": loss.get("counts"),
        "usd_lost": loss.get("usd_lost"),
        "usd_total": loss.get("usd_total"),
    }
    # The one cross-check worth making automatically: an ask that was booked
    # and never delivered, on a leg that also lost replies, is not evidence
    # about the desk's willingness at all.
    out["confounded_by_transport"] = bool(
        verdict in ("booked_never_delivered", "never_booked", "silent")
        and (loss.get("counts") or {}).get("lost_continuation"))
    return out


def sweep(runs_root: str) -> Dict[str, Any]:
    legs = []
    for name in sorted(os.listdir(runs_root)):
        path = os.path.join(runs_root, name)
        if not os.path.isdir(path):
            continue
        if not os.path.isfile(os.path.join(path, "turns.json")):
            continue
        legs.append(leg(path))

    counts: Dict[str, int] = {v: 0 for v in VERDICTS}
    for row in legs:
        counts[row["verdict"]] += 1
    measured = [r for r in legs if r["verdict"] != "not_measured"]
    return {
        "legs": legs,
        "legs_read": len(legs),
        "legs_measured": len(measured),
        "verdicts": counts,
        "reading": _reading(legs, counts),
    }


def _reading(legs: List[Dict[str, Any]], counts: Dict[str, int]) -> str:
    if not legs:
        return ("no leg under this root carries turns.json, so nothing was "
                "classified. That is an absence, not a clean result.")
    measured = sum(v for k, v in counts.items() if k != "not_measured")
    if not measured:
        return ("%d legs were read and none of them carries a goal block: "
                "every one predates inner/goal.py or ran on the `off` rung. "
                "This archive holds no evidence about the rider."
                % len(legs))
    parts = ["%d legs read, %d measured." % (len(legs), measured)]
    if counts["declined_with_argument"]:
        names = [r["leg"] for r in legs
                 if r["verdict"] == "declined_with_argument"]
        parts.append(
            "%d leg(s) -- %s -- were answered and REFUSED, with a named "
            "theorem carrying the argument. On those legs the mechanism "
            "connected; what did not move is the desk's mind, and the record "
            "now carries its reasons verbatim instead of a False."
            % (counts["declined_with_argument"], ", ".join(names)))
    if counts["booked_never_delivered"]:
        names = [r["leg"] for r in legs
                 if r["verdict"] == "booked_never_delivered"]
        parts.append(
            "%d leg(s) -- %s -- booked an ask that was never posted. Nothing "
            "on those legs is evidence about the rider's wording."
            % (counts["booked_never_delivered"], ", ".join(names)))
    if counts["signed"]:
        parts.append("%d leg(s) came back with a goal clause."
                     % counts["signed"])
    if counts["silent"]:
        parts.append("%d leg(s) were answered with silence, which is the only "
                     "outcome that is a defect in the answer."
                     % counts["silent"])
    confounded = [r["leg"] for r in legs if r["confounded_by_transport"]]
    if confounded:
        parts.append(
            "%d of them (%s) also lost desk replies in transit, so their "
            "negative reading is confounded and must not be quoted as the "
            "desk declining." % (len(confounded), ", ".join(confounded)))
    return " ".join(parts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs-root", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    report = sweep(args.runs_root)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if not args.quiet:
        for row in report["legs"]:
            if row["verdict"] == "not_measured":
                continue
            print("%-42s %-24s booked %d, answers %s"
                  % (row["leg"], row["verdict"], row["proposals_booked"],
                     row["answers"] or "[]"))
            for th in row["refusal_theorems"]:
                print("    theorem %s" % th["theorem"])
        print()
        print(json.dumps({k: v for k, v in report["verdicts"].items() if v},
                         sort_keys=True))
        print(report["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
