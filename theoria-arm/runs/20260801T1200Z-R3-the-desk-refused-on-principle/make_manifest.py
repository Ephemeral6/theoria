"""Derive this run's MANIFEST.json. Byte-stable; no wall clock enters it.

The narrative fields are this run's own claims. Everything mechanical -- the
file list, the sizes, the sha256s -- is derived here and rendered through
`armtools.backfill.render`, so this manifest has the same shape and the same
serialisation as every other in the archive rather than whatever `json.dump`
was called with by hand.

This directory has no `ledger.jsonl` (no API call, no model call), so
`armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it. Same footing as
`20260801T0900Z-R2-frontier-by-generation` and `20260801T0000Z-A-probe-
economics`.

    python make_manifest.py
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from armtools import backfill                          # noqa: E402

SLUG = os.path.basename(HERE)


def _files():
    out = []
    for name in sorted(os.listdir(HERE)):
        if name in ("MANIFEST.json",) or name.startswith("__"):
            continue
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            blob = fh.read()
        out.append({"path": name,
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "bytes": len(blob)})
    return out


PAYLOAD = {
    "prompt_id": "R3-r1b-goal-rider-understood",
    "branch": "z/r1b-goal-rider",
    "base_commit": "e8345affa0d500b8358e19fab65b8e25f615c7f9",
    "utc": "2026-08-01T12:00:00Z",
    "territory": "theoria-arm",
    "lane": "framework-change",
    "cell": "R3",
    "classification": {
        "kind": "framework-change-preparation",
        "archive_material": False,
        "why": "offline: no ARC action, no model call, no network, no ledger. "
               "Reads the archived records of R1b and every earlier leg and "
               "changes the arm's recording. Not run live.",
    },
    "what": (
        "R1b turned on goal_protocol=propose; the arm proposed, its mode moved "
        "off silence, and goal_declared_ever stayed False with plan reporting "
        "no_goal_declared 16 of 16. Read against the desk transcripts, the "
        "round's two legs are two different answers to the same question and "
        "the round reported one. On 20260801T001851Z-R1b-g50t-a the rider was "
        "DELIVERED three times and REFUSED three times, each time with the "
        "signed theorem the_goal_is_absent_because_no_instance_can_name_the_"
        "socket, whose body refutes all four goal forms this grammar admits "
        "against the frame -- the socket cells have never changed, so they are "
        "board, so arc-instances: all seats no instance on them, so no count "
        "ranges over them and no landmark names them. The mechanism connected; "
        "the desk took a position about expressive reach. On 20260801T001851Z-"
        "R1b-sk48-b the ask was BOOKED ON TURN 1 AND NEVER POSTED: the rider "
        "parks for the next theorize call a surprise pays for, turns 2-4 "
        "skipped theorize under the new-transitions gate, the following beat "
        "lost all five of its replies in transit, and the leg hit its spend "
        "reservation. Neither leg is a parser defect. Separately and not "
        "looked for: inner/theorize.py's single error string `no THEORY block "
        "in the reply` has been written 32 times and names three unrelated "
        "events -- 24 provider refusals, 1 empty reply, and 11 replies that "
        "were complete and arrived with their beginning missing, because "
        "harness/modelcall.py:561 keeps envelope['result'], the CLI's LAST "
        "assistant message. Those 11 were billed in full: $31.05 of a $108.54 "
        "lifetime desk bill, 28.6%, and $19.70 of R1b's own $35.14."),
    "measurement": {
        "desk_replies_classified": 89,
        "well_formed": 53,
        "provider_refusal": 24,
        "empty": 1,
        "lost_continuation": 11,
        "usd_lost_to_lost_continuation": 31.0513,
        "usd_total_desk_bill": 108.5410,
        "share_of_desk_spend_lost": 0.2861,
        "usd_lost_on_r1b_alone": 19.6959,
        "r1b_round_total_usd": 35.139827,
        "discriminator": "structural: all 53 accepted replies begin with the "
                         "literal marker `=== THEORY ===` and none of the 35 "
                         "rejected do. The arithmetic discriminator (chars per "
                         "output token) was tried and REJECTED: claude -p "
                         "bills thinking tokens that never reach `result`, so "
                         "the ratio is below 1.0 on 39 of 88 calls, most of "
                         "which parsed perfectly.",
        "legs_read": 19,
        "legs_with_a_goal_block": 2,
        "verdicts": {
            "20260801T001851Z-R1b-g50t-a": "declined_with_argument",
            "20260801T001851Z-R1b-sk48-b": "booked_never_delivered",
        },
        "g50t_proposals_booked": 3,
        "g50t_answers": ["declined_with_argument"] * 3,
        "sk48_proposals_booked": 1,
        "sk48_answers": [],
        "sk48_replies_lost_in_transit": 5,
        "sk48_replies_total": 6,
        "reads": "turns.json, RUN_STATE.json, theorize.json, desk_log.json, "
                 "desk/*.md, books/theory.dsl -- all tracked",
    },
    "the_four_hypotheses": {
        "a_never_saw_it": "TRUE of 20260801T001851Z-R1b-sk48-b. The ask was "
                          "booked and never posted; nothing on that leg is "
                          "evidence about the rider's wording.",
        "b_saw_it_and_ignored_it": "FALSE. The desk answered in detail three "
                                   "times, quoting the rider's own soundness "
                                   "criterion back and applying it.",
        "c_answered_and_it_never_reached_the_manual": "TRUE ONCE, and beyond "
                                                      "the rider: proposal 1's "
                                                      "first reply was lost in "
                                                      "transit at $2.696, and "
                                                      "the repair round it "
                                                      "forced carried the "
                                                      "answer. 11 replies "
                                                      "archive-wide.",
        "d_parser_rejected_the_goal_clause": "FALSE. answer_proposal read "
                                             "every delivered reply correctly "
                                             "and absence_signature found the "
                                             "signature the moment the manual "
                                             "carried one. There is no parser "
                                             "bug here.",
    },
    "does_the_rider_engage_the_desks_argument": {
        "engaged": "soundness -- 'it must be false in the states you have "
                   "already seen', which is the manuals' own argument in their "
                   "own terms, and the desk uses it to reject count(Glyph9, "
                   "color = 9) = 11.",
        "talked_past": "reach -- all three refusals demonstrate that the goal "
                       "section CANNOT SAY the target. Cart.pos = <landmark> "
                       "and count(<Type>, color = c) = n, `=` only, one "
                       "equation, no conjunction, against a target whose cells "
                       "are board and carry no instance.",
        "consequence": "offered only 'write one' or 'argue why not', the desk "
                       "put its real target in prose of its own naming "
                       "(the_socket_is_a_keyhole_and_names_the_winning_"
                       "position) where nothing in the arm reads it.",
        "same_wall_as": "20260801T0900Z-R2-frontier-by-generation GAP R2-2: 12 "
                        "of 47 off-frontier probes missed by exactly one "
                        "never-before-changed cell. One missing feature seen "
                        "twice.",
    },
    "changed": [
        "theoria-arm/armtools/replyloss.py",
        "theoria-arm/armtools/goal_forensics.py",
        "theoria-arm/inner/goal.py",
        "theoria-arm/inner/loop.py",
        "theoria-arm/tests/test_reply_loss.py",
        "theoria-arm/tests/test_goal_forensics.py",
        "theoria-arm/tests/test_goal_state.py",
        "theoria-arm/GAPS.md",
        "theoria-arm/DECISIONS.md",
    ],
    "not_changed": [
        "harness/modelcall.py -- the transport defect is DIAGNOSED, not "
        "repaired: both candidate fixes change what a live subprocess returns "
        "and neither can be validated offline",
        "CONTRACTS/",
        "theory-compiler/ and engine-rig/ (read only; the goal grammar finding "
        "belongs to theory-compiler and goes through monitor/inbox/)",
        "any existing runs/ directory",
    ],
    "prompt_change_and_how_it_is_judged": {
        "what": "inner/goal.prompt_rider gains a third acceptable answer: if "
                "you decline because the goal section cannot SAY what you "
                "believe wins, name the target under a theorem prefixed "
                "the_goal_i_cannot_write_is and say which forms you tried and "
                "what each lacked.",
        "cost": "zero model calls. Same rider, same already-paid-for theorize "
                "turn; the beat count does not move and constraint 8 is "
                "untouched.",
        "settled_offline": [
            "it cannot ask for a form the compiler refuses: it asks for a "
            "`theorem`, the DSL's own home for a belief that is not an "
            "equation",
            "its base rate is measured, not guessed: the desk produced exactly "
            "this artefact unprompted on 2 of 2 legs that reached that point",
            "the reading half pays off regardless: extract_target_theorems is "
            "fixture-tested and correctly returns [] on both R1b manuals, and "
            "the record now separates refused / not-asked / asked-and-lost, "
            "which it could not on 2026-08-01",
        ],
        "not_settled": "whether a desk given somewhere to put its target uses "
                       "it. That needs a live leg.",
        "what_a_live_leg_would_cost": "one carried g50t-5849a774 leg from the "
                                      "r3 seed books, --goal-protocol=propose, "
                                      "leg ceiling $25: $17-25, ~9 desk calls, "
                                      "~25 ARC actions, by the shape of R1b's "
                                      "two legs ($17.75 and $17.39, both "
                                      "stopped on the spend gate).",
        "what_it_would_settle": "only adoption of the third channel. NOT "
                                "whether a goal becomes writable -- that is "
                                "the grammar and belongs to theory-compiler.",
        "not_run": "this programme is over its spend ceiling and this session "
                   "had zero spend authority. No live ARC call, no live desk "
                   "call, no round, no leg.",
    },
    "tests": {
        "new_files": [
            "tests/test_reply_loss.py (17 tests)",
            "tests/test_goal_forensics.py (18 tests)",
        ],
        "extended": "tests/test_goal_state.py (+9)",
        "negative_controls": [
            "an empty reply and a provider refusal are each asserted NOT to be "
            "a lost continuation -- without this the headline 11 would absorb "
            "every call that failed for any reason",
            "a reply quoting the session-limit phrase inside a theorem is "
            "asserted well_formed, so the prefix match cannot swallow a real "
            "answer",
            "the same useless chars-per-token ratio is attached to a good "
            "reply and a bad one and asserted not to separate them, so the "
            "arithmetic threshold cannot be reintroduced",
            "every one of the eight goal verdicts is fired by a synthetic leg "
            "built on disk AND refused on the legs belonging to the others",
            "extract_target_theorems is asserted to return [] on both real R1b "
            "manuals -- a reader that found the third channel before it "
            "shipped would prove nothing about the third channel",
            "the target theorem prefix is asserted NOT to be an absence "
            "signature, so answering channel 3 cannot silently satisfy 2",
            "a due proposal is asserted to have an EMPTY refusal list, so the "
            "negation is not applied to passing checks",
            "sweeping an empty root is asserted to read as an absence, not as "
            "a clean result",
        ],
    },
    "inherited_red_gates": {
        "note": "verified on a detached pristine worktree of master "
                "e8345aff BEFORE this branch existed. Both were already "
                "failing; neither is introduced here.",
        "verify_provenance_check_8": "re-deriving every manifest reproduces it "
                                     "byte for byte -- drifted: "
                                     "20260731T231654Z-R1-g50t-a, "
                                     "20260731T231654Z-R1-sk48-b, "
                                     "20260801T001851Z-R1b-g50t-a, "
                                     "20260801T001851Z-R1b-sk48-b",
        "test_the_ceiling_table_still_covers_the_archive": "claude-opus-5: "
                                                           "ceiling $12.00 is "
                                                           "below $13.4480",
    },
    "residual_gaps": [
        "the transport is diagnosed, not repaired: 28.6% of every desk dollar "
        "this arm has spent bought an answer nobody read, and until it is "
        "fixed no A/B across R1/R1b legs means anything",
        "the goal grammar cannot name a cell the board explains, which is the "
        "same missing feature as R2's 12 expressivity misses, and it belongs "
        "to theory-compiler",
        "the third channel is unjudged: its reading half is tested, its "
        "adoption is not and cannot be offline",
        "nothing here says a level would have been completed. No leg was run.",
    ],
    "sealed_pile_contact": "none. Development-pile games only "
                           "(g50t-5849a774, sk48-d8078629), and both only as "
                           "already-archived records -- no game was played, "
                           "opened or inspected.",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": "none"},
    "reproduce": [
        "cd theoria-arm",
        "python -m pytest -q tests/test_reply_loss.py tests/test_goal_forensics.py",
        "python -m armtools.replyloss",
        "python -m armtools.goal_forensics",
        "cd runs/20260801T1200Z-R3-the-desk-refused-on-principle",
        "python measure.py",
        "python make_manifest.py",
    ],
}


def main():
    payload = dict(PAYLOAD)
    payload["files"] = _files()
    path = os.path.join(HERE, "MANIFEST.json")
    with open(path, "wb") as fh:
        fh.write(backfill.render(payload))
    print("wrote %s (%d files)" % (path, len(payload["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
