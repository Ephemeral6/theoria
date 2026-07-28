"""Adapter for the A2 repair-loop bundle (`cold-start-a2/`, read-only).

A2 is the only bundle in the repository that contains a **打脸→修复 episode**:
a manual whose Lean theorem compiles green with an empty axiom list and is
nevertheless false of the world, followed by the six-beat loop that finds that
out and fixes it.  `battery/model.py`'s `Repair` and `Beat` exist for this
bundle, and until it is loaded the U4 family has nothing to eat.

A2 is a *self-built* world, like A0, so it shares A0's shape and this adapter
shares A0's readers — `parse_dsl`, `parse_playbook`, `_count_evidence`,
`_read_json`, `_read_jsonl`, `_first_frame_with_colour`, `_concepts` are all
imported rather than re-written.  Two adapters that parse the same DSL two
different ways would eventually disagree about a clause count and nobody would
know which was right.

Like A0 it has **no model calls**: the whole spike was engines plus hand
adjudication (`A2_REPORT.md` records the offline check that no shipped file
imports a network library or mentions `ARC_API_KEY`).  The economy family
therefore returns `not-applicable` on every A2 run, and that is the correct
answer, not a gap to paper over.

Four runs come out of one bundle, and they are **not four independent
samples**:

| run | trace | manual | what it is |
|---|---|---|---|
| `a2-sweep` | `raw_trace.jsonl` (248) | `theory.dsl` r1 | the control |
| `a2-play-record` | `history_trace.jsonl` (184) | `theory_holed.dsl` | the exhibit |
| `a2-probed` | `probed_trace.jsonl` (196) | `theory_repaired.dsl` r2 | the repair |
| `a2-refutation` | `solved_episode.jsonl` (19) | — | the 18-step solve |

`history_trace[0..182]` is byte-identical to `raw_trace[0..182]`, and
`probed_trace[0..182]` is byte-identical to both; the play record is the sweep
cut at the portal transition, and the probe record is the play record with
twelve probe frames appended.  Every run records that overlap in
`Run.notes["overlaps"]` so a de-redundancy pass cannot read four rows as four
observations.  What differs at index 183 is instructive rather than incidental:
`history_trace[183]` is the `action: null` truncation sentinel and
`probed_trace[183]` back-fills `"LEFT"`, so the two rows share a frame and
disagree about the action — which is why traces must never be deduplicated on
`(t, frame)`.

Three things this adapter reconstructs rather than reads:

* **A trace step's identity.**  Same off-by-one as A0: row `t` holds the state
  *before* its action and the last row has `action: null`, so `N` records are
  `N-1` steps and step `i` is identified by row `i+1`'s frame.
* **The control manual's concept accounts.**  `concept_accounts.json` carries
  `a2-holed` and `a2-repaired` but its `a2-base` entry is an **empty list** —
  the control's accounts survive only as `compress:` annotations in
  `theory.dsl`'s word table.  Emitting zero concepts there would say the
  control manual named nothing, which is false, so the annotations are parsed
  out of the DSL text and `Run.notes["concept_source"]` records that they came
  from prose rather than from the JSON.
* **Every beat's environment cost.**  No producer in A2 writes a per-beat
  action count.  `_beat_cost` derives each one from the beat's own evidence and
  writes the derivation into `Beat.note`, so a reader can check the arithmetic
  without trusting this file.

And one thing it deliberately refuses to reconstruct.  `exhibit_report.json`'s
`certify_cheap_vs_full_sweep` is the nearest thing A2 has to a held-out score —
the holed manual, replayed against the 248-frame sweep it never saw, is red
with 44 anomalies.  It is **not** convertible into `held_out_agree`: the
producer (`cold-start-a0/certify/replay.py`) caps its anomaly list at 40
entries, and one transition can raise several anomalies of different kinds, so
44 is neither a transition count nor a complete list.  `247 - 44` would be a
fabricated number wearing a denominator.  Both held-out fields stay `None`, the
anomaly count goes to `Run.notes`, and `Theory.held_out_frame` says in one line
what the frame actually was.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from battery.adapters.a0 import (_concepts, _count_evidence,
                                 _first_frame_with_colour, _read_json,
                                 _read_jsonl, parse_dsl, parse_playbook)
from battery.guard import Piles, load_piles
from battery.model import Beat, Repair, Run, Step, Theory, Truth, digest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
A2_ROOT = os.path.join(REPO, "cold-start-a2")

# Same three mechanisms as A0's base world and deliberately the same table
# shape, because the mechanism family compares the two.  `marker` is the board
# colour that makes the mechanism visible; `used_key` is the `trace_summary`
# field recording when it was first exploited; `available_from` names the
# mechanism whose first use unlocks this one — the Door is not a passage until
# the Button has opened it, so measuring its delay from frame 0 would charge
# the arm for time in which the mechanism did not exist.
#
# The Portal has no `available_from` even though the world's own rule table
# says the teleport is only reachable through the opened Door.  A0's `portal`
# does not have one either, and a mechanism whose delay is measured from a
# different origin on two arms is not a comparable mechanism.  The asymmetry is
# recorded here rather than silently fixed on one side.
MECHANISMS: Dict[str, Dict[str, Any]] = {
    "portal": {"marker": 3, "used_key": "portal_transitions"},
    "button": {"marker": 7, "used_key": "button_press_transitions"},
    "door_passage": {"marker": 5, "used_key": "door_entry_transitions",
                     "available_from": "button"},
}

# `run_id -> where its four inputs live`.  `summary_key` indexes
# `trace_summary.json`, which only carries the two traces the sweep step
# produced; `None` means the summary has no entry and the mechanism uses are
# derived from the frames instead (see `_mechanisms`).
INSTANCES: Dict[str, Dict[str, Any]] = {
    "a2-sweep": {
        "trace": "raw_trace.jsonl",
        "dsl": os.path.join("theory", "theory.dsl"),
        "concepts_key": "a2-base",
        "summary_key": "raw_trace",
        "replay": ("certify_generated.json", "cheap"),
        # The sweep is a coverage walk over all 55 reachable states: 247 steps
        # against an 18-step optimal plan is 13.7x, which measures the trace's
        # purpose and not the arm's planning.  `explore` is what stops the
        # planning family scoring it.
        "intent": "explore",
        "held_out_frame":
            "none: theory.dsl was mined from the full sweep and certified "
            "against that same sweep, so there is no unseen evidence behind "
            "this manual's replay score.",
        "role": "control -- the complete manual, revision 1",
    },
    "a2-play-record": {
        "trace": "history_trace.jsonl",
        "dsl": os.path.join("theory", "theory_holed.dsl"),
        "concepts_key": "a2-holed",
        "summary_key": "history_trace",
        "replay": ("exhibit_report.json", "certify_cheap"),
        "intent": "explore",
        "held_out_frame":
            "the 64 sweep frames past the portal cut that the play record "
            "never contained (raw_trace 248 vs history_trace 184). Count of "
            "anomalies only -- the replay certifier caps its anomaly list at "
            "40 and one transition can raise several -- so no agree/total "
            "ratio exists and held_out_pairs/agree stay None.",
        "role": "exhibit -- the holed manual, false of the world",
    },
    "a2-probed": {
        "trace": "probed_trace.jsonl",
        "dsl": os.path.join("theory", "theory_repaired.dsl"),
        "concepts_key": "a2-repaired",
        "summary_key": None,
        "replay": ("repair_report.json", "certify_cheap"),
        "intent": "explore",
        "held_out_frame":
            "none: theory_repaired.dsl was written from probes.jsonl and "
            "certified against probed_trace.jsonl, the same evidence.",
        "role": "repair -- the repaired manual, revision 2",
    },
    "a2-refutation": {
        "trace": "solved_episode.jsonl",
        "dsl": None,                 # the refutation is an episode, not a book
        "concepts_key": None,
        "summary_key": None,
        "replay": None,
        # The one A2 run that is a genuine attempt to win: 18 actions against
        # an 18-action optimum, ending on the goal with win=true.  It is the
        # first run in the whole battery that can legitimately be asked for
        # path efficiency, which needs `intent="solve"` and `optimal_steps`.
        "intent": "solve",
        "held_out_frame": None,
        "role": "refutation -- the 18-action episode that refutes the exhibit",
    },
}

# Narrative order, not alphabetical: the four runs are the loop's own sequence
# and reading them in that order is how the exhibit makes sense.  An explicit
# tuple rather than dict order so the output cannot drift if the table is
# re-arranged.
ORDER: Tuple[str, ...] = ("a2-sweep", "a2-play-record", "a2-probed",
                          "a2-refutation")

# `Theoria.md` Phase 1's A2 acceptance, in order.  The ledger tags the loop
# beats L1..L6 and prefixes the instrument and the exhibit as M0 and M5; only
# the six L beats are the loop, and `Repair.beats_required` is 6.
LOOP_TAGS: Tuple[str, ...] = ("L1", "L2", "L3", "L4", "L5", "L6")

# Word-table entries carrying a compression account, e.g.
#   Cart [segment: uniform_color ev: t0-t247 compress: 1891]
# Object names are capitalised and the surrounding `object Cart { ... }`
# declarations are not, so the leading `[A-Z]` is what separates them.
_ACCOUNT_RE = re.compile(r"^\s*([A-Z][A-Za-z0-9_]*)\s*\[[^\]]*?compress:\s*"
                         r"(-?\d+)")
_LAW_RE = re.compile(r"^\s*(invariant|theorem)\b")


# --------------------------------------------------------------- the manual

def parse_word_table_accounts(path: str,
                              objects: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Concept accounts read out of a manual's word table.

    The fallback for `concept_accounts.json["a2-base"] == []`.  The control
    manual's accounts were written into `theory.dsl` as `compress:`
    annotations and never emitted as JSON, and a battery that read the empty
    list literally would report that the control named no concepts — the one
    reading the evidence rules out.

    Returns dictionaries in `concept_accounts.json`'s own shape so
    `a0._concepts` can consume either source without a branch.  Two fields are
    not in the DSL and are recovered from the world's own declarations:

    * `colour` comes from `ground_truth.json`'s `objects[name]["colors"]`,
      which is what `first_seen_step` scans frames for;
    * `load_bearing` is true when a law names the concept.  The JSON accounts
      define it the same way (`reason`: "a law names it"), and on the two
      manuals that have both sources the two agree, which is what makes the
      fallback checkable rather than merely plausible.
    """
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    laws = [line for line in lines
            if not line.strip().startswith("#") and _LAW_RE.match(line)]

    out: List[Dict[str, Any]] = []
    for line in lines:
        if line.strip().startswith("#"):
            continue
        match = _ACCOUNT_RE.match(line)
        if not match:
            continue
        name = match.group(1)
        colours = ((objects.get(name) or {}).get("colors") or [])
        named = re.compile(r"\b%s\b" % re.escape(name))
        out.append({
            "name": name,
            "colour": colours[0] if colours else None,
            "script_delta_bits": int(match.group(2)),
            "load_bearing": any(named.search(law) for law in laws),
            # Not consumed by `_concepts`; carried so the caller can check the
            # manual's declared evidence span against the trace it was mined
            # from.  `ev: t0-t247` on a 248-frame sweep is the manual saying
            # which trace it is about.
            "evidence_span": _count_evidence(line),
        })
    return sorted(out, key=lambda e: e["name"])


def theorem_names(clauses) -> List[str]:
    """Sorted theorem names, for diffing one manual against another."""
    return sorted(c.name for c in clauses if c.kind == "theorem")


def rule_names(clauses) -> List[str]:
    """Sorted rule names, for diffing one manual against another."""
    return sorted(c.name for c in clauses if c.kind == "rule")


# ------------------------------------------------------------- the mechanisms

def _cart_cell(frame: List[List[int]], colour: int) -> Optional[Tuple[int, int]]:
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == colour:
                return (r, c)
    return None


def _derive_transitions(frames: List[Any], palette: Dict[str, Any],
                        door_cell: Optional[List[int]]) -> Dict[str, List[int]]:
    """`trace_summary.json`'s three transition lists, recomputed from frames.

    `trace_summary.json` only covers the two traces the sweep step wrote, so
    `probed_trace` and `solved_episode` have no recorded mechanism use at all.
    Reporting `first_used=None` for those would say the probe episode never
    touched the Portal, which the repaired manual's own witness (`ev: t194`)
    contradicts — a fabricated absence rather than a fabricated number, but a
    fabrication either way.

    So the three lists are derived from the frames, using the world's own
    definitions:

    * `button_press_transitions` — the Button's unpressed colour disappears;
    * `portal_transitions` — the Cart moves more than one cell, which is
      `trace_summary.json`'s own `cut_rule` ("the single non-adjacent Cart
      move, found from the frames' geometry");
    * `door_entry_transitions` — the Cart lands on the Door's cell.

    On the two traces that have both a record and a derivation the two agree
    exactly, which is what licenses using the derivation on the two that do
    not.  `test_adapter_a2.py` asserts that agreement rather than assuming it.
    """
    cart = palette.get("cart")
    unpressed = palette.get("button_unpressed")
    target = tuple(door_cell) if door_cell else None

    button: List[int] = []
    portal: List[int] = []
    door: List[int] = []
    for i in range(len(frames) - 1):
        before, after = frames[i], frames[i + 1]
        if unpressed is not None:
            was = any(unpressed in row for row in before)
            still = any(unpressed in row for row in after)
            if was and not still:
                button.append(i)
        if cart is not None:
            here = _cart_cell(before, cart)
            there = _cart_cell(after, cart)
            if here and there:
                if abs(here[0] - there[0]) + abs(here[1] - there[1]) > 1:
                    portal.append(i)
                if target is not None and there == target:
                    door.append(i)
    return {"button_press_transitions": button,
            "portal_transitions": portal,
            "door_entry_transitions": door}


def _mechanisms(frames: List[Any], summary: Optional[Dict[str, Any]],
                derived: Dict[str, List[int]]
                ) -> Dict[str, Dict[str, Optional[int]]]:
    """A0's `_mechanisms`, with a derived fallback for the unsummarised traces.

    `first_seen` is always recomputed by scanning frames for the marker
    colour, so the delay is measured against the trace rather than asserted.
    `first_used` prefers `trace_summary.json` where the trace has an entry —
    the world's own record outranks this file's arithmetic — and falls back to
    `_derive_transitions` where it does not.

    `history_trace`'s `portal_transitions` is `[]`, and that empty list is the
    whole exhibit: the play record never uses the Portal, which is why the
    manual mined from it can omit the teleport rule and still replay at 100%.
    It must survive as `first_used=None` and never collapse to 0.
    """
    out: Dict[str, Dict[str, Optional[int]]] = {}
    used: Dict[str, Optional[int]] = {}
    for name in sorted(MECHANISMS):
        key = MECHANISMS[name]["used_key"]
        hits = (summary or {}).get(key) if summary is not None else None
        if hits is None:
            hits = derived.get(key) or []
        used[name] = min(hits) if hits else None

    for name in sorted(MECHANISMS):
        entry = MECHANISMS[name]
        seen = _first_frame_with_colour(frames, entry["marker"])
        unlock = entry.get("available_from")
        if unlock is not None:
            # The mechanism does not exist before its unlock fires.
            unlocked_at = used.get(unlock)
            seen = unlocked_at if unlocked_at is not None else None
        out[name] = {"first_seen": seen, "first_used": used[name]}
    return out


# ------------------------------------------------------------- the replay

def _replay(report: Optional[Dict[str, Any]],
            key: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """`(pairs, agree)` from a certifier block, or `(None, None)`.

    A green certification agrees on every transition it checked, so `agree`
    is the transition count.  A red one does not license a count: the anomaly
    list is capped and a transition can raise several anomalies, so `agree`
    stays `None` rather than becoming `transitions - anomalies`.
    """
    if not report or not key:
        return None, None
    block = report.get(key) or {}
    pairs = block.get("transitions")
    if pairs is None:
        return None, None
    return pairs, (pairs if block.get("green") else None)


# ------------------------------------------------------------- the repair loop

def _beat_cost(tag: str, refutation: Dict[str, Any],
               probe: Dict[str, Any],
               repair: Dict[str, Any]) -> Tuple[int, str]:
    """`(environment actions, the derivation)` for one loop beat.

    Nothing in A2 records a per-beat cost, so every number here is computed
    from the beat's own evidence and the computation travels with it in
    `Beat.note`.  A zero means "cost nothing in the environment" — localisation
    and re-proof are offline work over frames already paid for — and never
    "did not happen"; `Beat.closed` carries that.
    """
    if tag == "L1":
        length = (refutation.get("episode") or {}).get("length")
        return int(length or 0), (
            "refutation.json episode.length = %s: the solved episode is played "
            "in the world, so the whole loop's evidence starts by paying for "
            "it." % length)
    if tag == "L2":
        path = refutation.get("_locate_path_length")
        return 0, (
            "offline. locate_report.json replays the %s-action episode L1 "
            "already recorded, through the manual rather than the world, and "
            "takes no new action." % path)
    if tag == "L3":
        after = probe.get("trace_frames_after")
        before = probe.get("trace_frames_before")
        grew = int((after or 0) - (before or 0))
        return grew, (
            "probe_report.json trace_frames_after - trace_frames_before = "
            "%s - %s = %s new frames, i.e. %s new actions; independently, the "
            "four executable probes sum to %s navigation steps plus 4 probe "
            "actions." % (after, before, grew, grew,
                          probe.get("_navigation_steps")))
    if tag == "L4":
        return 0, ("offline. theory_repaired.dsl is written from probes.jsonl "
                   "and engines_diff_probed.json; rewriting a manual takes no "
                   "action in the world.")
    if tag == "L5":
        return 0, ("offline. Lean re-checks the stale and the new certificate "
                   "over the manual's own state space; the prover never "
                   "touches the world.")
    if tag == "L6":
        # **Billed, and the choice is deliberate.**  `plan.py` steps a fresh
        # world through all 18 plan actions to fill `plan_repaired.json`'s
        # `world_reaches_goal`, so the actions are really executed.  It is
        # arguable either way -- one can call it a verification replay of a
        # plan L1 already paid for -- and the argument decides K13, which is a
        # metric this project registered a directional prediction about.
        #
        # Not billing it gives 30/183 = 0.164; billing it gives 48/183 = 0.262.
        # Both clear the registered prediction of "< 0.3", and the lower one is
        # the one that flatters it.  Choosing the number that makes your own
        # pre-registration look better is the exact failure this battery exists
        # to catch, so the conservative reading is taken and the alternative is
        # kept in `Repair.notes`.  `DECISIONS.md` D-B-015.
        #
        # 解出 is also a beat of the loop by `Theoria.md`'s own definition, and
        # K13 sums beat costs; excluding the only beat that touches the world
        # after 戳探 would make the sum something other than what it claims.
        length = (repair.get("plan") or {}).get("length")
        if not length:
            return 0, ("plan_repaired.json records no plan length; L6's world "
                       "execution cannot be costed and is reported as zero")
        return int(length), (
            "plan.py re-executes the %s-action repaired plan against a freshly "
            "initialised world to fill world_reaches_goal. Billed: the actions "
            "are executed, and 解出 is a beat of the loop. The unbilled "
            "reading is in Repair.notes." % length)
    return 0, "no derivation is defined for this beat"


def _build_repair(artifacts: str, holed_clauses, repaired_clauses
                  ) -> Optional[Repair]:
    """The one 打脸→修复 episode A2 contains, or `None` if its ledger is absent.

    Attached to `a2-probed` and to no other run: the repair is what produced
    `theory_repaired.dsl`, and hanging a copy on the sweep or the play record
    would let three rows be counted as three repairs.
    """
    ledger = _read_json(os.path.join(artifacts, "loop_ledger.json"))
    if not ledger:
        return None

    refutation = _read_json(os.path.join(artifacts, "refutation.json")) or {}
    locate = _read_json(os.path.join(artifacts, "locate_report.json")) or {}
    probe = _read_json(os.path.join(artifacts, "probe_report.json")) or {}
    exhibit = _read_json(os.path.join(artifacts, "exhibit_report.json")) or {}
    repair = _read_json(os.path.join(artifacts, "repair_report.json")) or {}

    # Two fields the cost derivations quote, threaded through rather than
    # re-read inside `_beat_cost`.
    refutation = dict(refutation)
    refutation["_locate_path_length"] = locate.get("path_length")
    probe = dict(probe)
    probe["_navigation_steps"] = sum(
        int(p.get("navigation_steps") or 0)
        for p in (probe.get("probes") or [])
        if p.get("tier") == "executable")

    by_tag = {b.get("beat"): b for b in (ledger.get("beats") or [])}
    beats: List[Beat] = []
    for tag in LOOP_TAGS:
        row = by_tag.get(tag)
        if row is None:
            # A missing beat is an open beat, not an absent one: the loop was
            # required to have six and this is how a short loop reads.
            beats.append(Beat(tag=tag, name=tag, closed=False,
                              note="loop_ledger.json carries no %s beat" % tag))
            continue
        actions, note = _beat_cost(tag, refutation, probe, repair)
        beats.append(Beat(
            tag=tag,
            name=str(row.get("name") or tag),
            closed=row.get("status") == "pass",
            env_actions=actions,
            note=note,
        ))

    # What the repair cost the downstream proofs.  The holed manual's
    # `right_room_locked` has no counterpart in the repaired manual: the
    # theorem did not survive the rule that refuted it.
    before = theorem_names(holed_clauses)
    after = theorem_names(repaired_clauses)
    invalidated = [name for name in before if name not in after]
    added_rules = [name for name in rule_names(repaired_clauses)
                   if name not in rule_names(holed_clauses)]

    # Would the repair have left a false theorem standing without dependency
    # tracking?  Read from evidence, not asserted: the exhibit's theorem is
    # Lean-green with an *empty* axiom list and false of the world, and the
    # stale certificate only died because the repair was tracked back to it.
    axiom_free = any(not (r.get("axioms") or [])
                     for r in ((exhibit.get("certify_lean") or {})
                               .get("axiom_reports") or []))
    silently_wrong = bool(
        (exhibit.get("certify_lean") or {}).get("green")
        and axiom_free
        and exhibit.get("exhibit_is_false_of_the_world")
        and (repair.get("stale_certificate") or {}).get("died"))

    sweep = exhibit.get("certify_cheap_vs_full_sweep") or {}
    prologue = sorted(
        (b.get("beat"), str(b.get("name") or ""), str(b.get("status") or ""))
        for b in (ledger.get("beats") or [])
        if b.get("beat") not in LOOP_TAGS)

    repair_actions = sum(b.env_actions for b in beats)
    return Repair(
        episode_id="a2-teleport-repair",
        trigger=("an 18-action episode reaches the goal cell with win=true, "
                 "refuting the axiom-free Lean theorem %r"
                 % (((refutation.get("claim") or {}).get("theorem")) or "?")),
        strategy="patch",
        changed_clause=added_rules[0] if added_rules else None,
        detected=bool(refutation.get("refuted")),
        # The first action on the witness path at which the world contradicted
        # the manual: locate_report.json's `located.t`.  Not the ledger's
        # `located_at`, which is a copy of the same number.
        detection_actions=(locate.get("located") or {}).get("t"),
        actions_examined=locate.get("path_length"),
        beats=beats,
        beats_required=len(LOOP_TAGS),
        repair_actions=repair_actions,
        # What the theory being repaired cost to build in the first place: the
        # 183 transitions of the play record the holed manual was mined from.
        baseline_actions=(exhibit.get("certify_cheap") or {}).get("transitions"),
        invalidated_theorems=len(invalidated),
        theorems_before=len(before),
        silently_wrong_without_tracking=silently_wrong,
        notes={
            # M0 and M5 are the instrument and the exhibit — the prologue that
            # sets the loop up, not beats of the loop.  Counting them would
            # make an eight-beat ledger look like a loop that overshot its six.
            "prologue_beats": [
                {"beat": tag, "name": name, "status": status}
                for tag, name, status in prologue],
            "ledger_summary": {k: (ledger.get("summary") or {}).get(k)
                               for k in ("pass", "fail", "absent", "total")},
            "ledger_green": ledger.get("green"),
            "invalidated": invalidated,
            "added_rules": added_rules,
            "theorems_after": after,
            "stale_certificate_died":
                (repair.get("stale_certificate") or {}).get("died"),
            "exhibit_lean_axioms_empty": axiom_free,
            "exhibit_anomalies_on_full_sweep": sweep.get("anomalies"),
            # The convention K13's ratio depends on, and the reading it
            # rejects, so a reader who disagrees does not have to re-derive it.
            "repair_actions_if_l6_verification_unbilled":
                repair_actions - int(
                    ((repair.get("plan") or {}).get("length")) or 0),
            "verification_convention":
                "L6 re-executes the repaired plan against a freshly "
                "initialised world to fill plan_repaired.json's "
                "world_reaches_goal. This adapter BILLS that replay: the "
                "actions are executed, 解出 is a beat of the loop by "
                "Theoria.md's definition, and the unbilled reading is the one "
                "that flatters this project's own registered prediction for "
                "K13. See DECISIONS.md D-B-015.",
        },
    )


# ------------------------------------------------------------------ the runs

def load_a2_runs(root: str = A2_ROOT, *,
                 piles: Optional[Piles] = None) -> List[Run]:
    """The four A2 runs, in the loop's own order.

    Pure reads: no network, no model, no write anywhere under `root`.
    """
    piles = piles or load_piles()
    artifacts = os.path.join(root, "artifacts")

    summaries = _read_json(os.path.join(artifacts, "trace_summary.json")) or {}
    accounts = _read_json(os.path.join(artifacts, "concept_accounts.json")) or {}
    truth_doc = _read_json(os.path.join(artifacts, "ground_truth.json")) or {}
    probes = _read_jsonl(os.path.join(artifacts, "probes.jsonl"))
    pin = _read_json(os.path.join(artifacts, "upstream_pin.json")) or {}

    palette = truth_doc.get("palette") or {}
    objects = truth_doc.get("objects") or {}
    door_cell = (truth_doc.get("spec") or {}).get("door_cell")

    # A2 ships no playbook: the spike is about the manual and its certificate,
    # and `Theoria.md`'s playbook half is A3's.  The path is read rather than
    # assumed so the zero is a measurement — `parse_playbook` returns (0, 0)
    # for a file that is not there.
    playbook_entries, deadlocks = parse_playbook(
        os.path.join(root, "theory", "playbook.dsl"))

    # `probes.jsonl` is ragged by design.  P-03 is `tier: "hypothetical"` with
    # `status: "not_separable_in_this_world"` and carries none of the
    # execution keys the other four have, because no experiment in this world
    # can separate the two guards it asks about.  Reading it with `.get` keeps
    # it counted as designed and not counted as executable, which is the
    # honest pair of facts.
    probes_designed = len(probes)
    probes_executable = sum(1 for p in probes
                            if p.get("tier") == "executable"
                            or p.get("executable") is True)

    # The repair needs both manuals' clause lists to diff them, so they are
    # parsed once here rather than reconstructed inside `_build_repair`.
    holed_clauses, _ = parse_dsl(
        os.path.join(root, "theory", "theory_holed.dsl"))
    repaired_clauses, _ = parse_dsl(
        os.path.join(root, "theory", "theory_repaired.dsl"))
    repair = _build_repair(artifacts, holed_clauses, repaired_clauses)

    provenance = {
        "repo_head_when_pinned": pin.get("repo_head_when_pinned"),
        "upstream_files_pinned": len(pin.get("sha256") or {}),
        "upstream_files_missing": len(pin.get("missing") or []),
        "note": "A2 imports these files from cold-start-a0 and its results are "
                "only valid against this pin; a changed hash means they must "
                "be regenerated before they are quoted.",
    }

    runs: List[Run] = []
    for run_id in ORDER:
        spec = INSTANCES[run_id]
        rows = _read_jsonl(os.path.join(artifacts, spec["trace"]))
        if not rows:
            continue
        rows.sort(key=lambda r: r.get("t", 0))
        frames = [r["frame"] for r in rows]

        # Row t holds the state *before* its action; the step that action makes
        # is identified by the state it lands in, which is row t+1's frame.
        # The last row is the `action: null` sentinel, so N rows are N-1 steps.
        #
        # A2's world cannot error -- it is a local simulator with a total step
        # function -- so no step is failed and `n_frames` is 1 by the manual's
        # own `cascade single_frame`.  There is no level field: one board, one
        # level, `level=0` throughout.
        steps: List[Step] = []
        for i, row in enumerate(rows[:-1]):
            steps.append(Step(
                idx=i,
                action=str(row.get("action")),
                state_key=digest(frames[i + 1]),
                failed=False,
                n_frames=1,
                level=0,
                won=bool(rows[i + 1].get("win")),
            ))

        summary_key = spec["summary_key"]
        summary = summaries.get(summary_key) if summary_key else None
        derived = _derive_transitions(frames, palette, door_cell)

        notes: Dict[str, Any] = {
            "role": spec["role"],
            "trace": spec["trace"],
            "frames": len(rows),
            "transitions": len(steps),
            # Four runs, one bundle, three of them sharing a prefix.  Recorded
            # on every run so a correlation pass cannot read four rows as four
            # independent samples of anything.
            "overlaps": _OVERLAPS[run_id],
            "mechanism_source": ("trace_summary.json[%s]" % summary_key
                                 if summary is not None
                                 else "derived from frames -- "
                                      "trace_summary.json has no entry for "
                                      "this trace"),
            "model_calls": "none: A2 ran no LLM in the loop, so the economy "
                           "family is structurally not-applicable",
            "upstream_pin": provenance,
        }

        theory: Optional[Theory] = None
        if spec["dsl"]:
            clauses, revision = parse_dsl(os.path.join(root, spec["dsl"]))
            entries = accounts.get(spec["concepts_key"]) or []
            if entries:
                notes["concept_source"] = ("artifacts/concept_accounts.json[%s]"
                                           % spec["concepts_key"])
            else:
                # The control's accounts exist only as prose.  Say so on the
                # run rather than emitting an empty concept list.
                entries = parse_word_table_accounts(
                    os.path.join(root, spec["dsl"]), objects)
                notes["concept_source"] = (
                    "theory.dsl word_table `compress:` annotations -- "
                    "concept_accounts.json[%s] is an empty list, so the "
                    "control manual's accounts were parsed out of the DSL "
                    "text; colours come from ground_truth.json objects and "
                    "load_bearing from whether a law names the concept"
                    % spec["concepts_key"])
                notes["concept_evidence_spans"] = {
                    e["name"]: e.get("evidence_span") for e in entries}

            pairs, agree = _replay(
                _read_json(os.path.join(artifacts, spec["replay"][0])),
                spec["replay"][1])

            theory = Theory(
                concepts=_concepts(entries, frames, revision),
                clauses=clauses,
                # A2 has no playbook and no deadlock theorem.  Both are read,
                # not assumed: `parse_playbook` on an absent file, and the
                # `unsolvable`-named-theorem count A0 uses, which is zero here
                # because the exhibit's theorem is named `right_room_locked`
                # and targets `unsolvable` from a separate `lean_target` field
                # the DSL reader does not see.
                playbook_entries=playbook_entries,
                deadlock_theorems=deadlocks + sum(
                    1 for c in clauses
                    if c.kind == "theorem" and "unsolvable" in c.name),
                revisions=revision,
                # One probe record for three manuals.  `probes.jsonl` is the
                # loop's L3 product; attributing it to each manual is A0's
                # convention (one `engines_report.probes` shared by both
                # instances) and must not be read as three probe programmes.
                probes_designed=probes_designed,
                probes_executable=probes_executable,
                replay_pairs=pairs,
                replay_agree=agree,
                # Never derived.  See this module's docstring.
                held_out_pairs=None,
                held_out_agree=None,
                held_out_frame=spec["held_out_frame"],
            )
            notes["probes_source"] = (
                "artifacts/probes.jsonl -- designed and executed in loop beat "
                "L3; the same record is attributed to all three A2 manuals")

        if run_id == "a2-play-record":
            exhibit = _read_json(
                os.path.join(artifacts, "exhibit_report.json")) or {}
            sweep = exhibit.get("certify_cheap_vs_full_sweep") or {}
            notes["held_out"] = {
                "frames": sweep.get("frames"),
                "anomalies": sweep.get("anomalies"),
                "anomaly_kinds": sorted(sweep.get("anomaly_kinds") or []),
                "green": sweep.get("green"),
                "why_no_ratio":
                    "the replay certifier caps its anomaly list at 40 entries "
                    "and one transition can raise several anomalies of "
                    "different kinds, so 44 is neither a transition count nor "
                    "a complete list; 247-44 would be a fabricated ratio.",
            }
            notes["exhibit"] = {
                "lean_green": (exhibit.get("certify_lean") or {}).get("green"),
                "false_of_the_world":
                    exhibit.get("exhibit_is_false_of_the_world"),
                "theorem": (exhibit.get("theorem") or {}).get("name"),
            }

        runs.append(Run(
            run_id=run_id,
            arm="theoria_a2",
            source="cold-start-a2",
            intent=spec["intent"],
            model=None,
            game_id=None,            # a self-built world belongs to no pile
            pile=piles.assert_playable(None),
            campaign=None,
            steps=steps,
            calls=[],                # A2 ran no model in the loop
            theory=theory,
            truth=Truth(
                optimal_steps=truth_doc.get("shortest_solution_length"),
                mechanisms=_mechanisms(frames, summary, derived),
                levels=1,
            ),
            repairs=[repair] if (repair and run_id == "a2-probed") else [],
            notes=notes,
        ))
    return runs


# Written out rather than computed so the statement survives a trace being
# regenerated: if the prefixes ever stop matching, `test_adapter_a2.py` fails
# instead of this note quietly becoming false.
_OVERLAPS: Dict[str, List[str]] = {
    "a2-sweep": [
        "records 0..182 are byte-identical to a2-play-record's",
        "records 0..182 are byte-identical to a2-probed's",
    ],
    "a2-play-record": [
        "records 0..182 are byte-identical to a2-sweep's -- this trace is the "
        "sweep cut at the portal transition (t183)",
        "records 0..182 are byte-identical to a2-probed's; record 183 shares "
        "its frame but is the action:null truncation sentinel, which a2-probed "
        "back-fills with LEFT -- never dedupe these traces on (t, frame)",
    ],
    "a2-probed": [
        "records 0..182 are byte-identical to a2-sweep's",
        "records 0..182 are byte-identical to a2-play-record's; records "
        "184..195 are the twelve probe frames appended in loop beat L3",
    ],
    "a2-refutation": [
        "shares no records with the other three: an independent 18-action "
        "episode played from the initial state",
    ],
}

__all__ = ["load_a2_runs", "parse_word_table_accounts", "theorem_names",
           "rule_names", "A2_ROOT", "MECHANISMS", "INSTANCES", "ORDER",
           "LOOP_TAGS"]
