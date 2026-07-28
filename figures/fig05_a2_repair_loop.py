"""fig05_a2_repair_loop -- 图5 the DC22 case: the A2 six-beat repair account.

Theoria.md 3.2 figure 5, PLAN.md section 5. This repository's DC22 exhibit is
``cold-start-a2``: a self-built world isomorphic to DC22's failure structure.
``loop_ledger.json``'s ``authority`` field records the INC-004 ruling that no
upstream DC22 artefact was read, so the pile seal is intact; that sentence is
carried onto the plate rather than left in a caption.

What the figure has to get right, and what most of this module is about:

1. **The ledger holds eight beats; the loop is six.** ``loop_ledger.json``'s
   ``summary`` is ``{"pass": 8, "fail": 0, "absent": 0, "total": 8}`` and covers
   M0 + M5 + L1-L6. M0 (the complete manual) and M5 (the exhibit) are *prelude*:
   they build and display the broken theorem, they are not repair beats. The
   flow therefore draws them in a visually subordinate band upstream of the
   loop, and no panel carries the 8-pass summary as if it were the loop's score.
   The loop's own score is 6 of 6, and that is what K12 measures.

2. **The exhibit's point must be legible without a caption.** At M5 three facts
   hold *at once*: the holed manual replays the play record at 100% (184 frames
   / 183 transitions / 14904 pixels, 0 unexplained), Lean signs ``unsolvable``
   with an empty axiom list, and the world contradicts it (an 18-action solved
   episode). Their co-occurrence *is* the phenomenon, so the M5 node draws them
   as three ANDed badges rather than three bullet points anyone could read
   separately.

3. **Nothing absent is drawn as zero.** Five distinct non-value states appear in
   this data and each gets its own encoding and its own ``value_kind`` in the
   CSV:

   | kind | what it means here |
   |---|---|
   | ``measured`` | a number the artefact reports |
   | ``real-zero`` | a genuine, checked zero (0 board diffs, 0 axioms, 0 mismatches) |
   | ``structurally-absent`` | the key does not exist because it cannot: an UNSAT plan has no ``length`` |
   | ``absent-by-construction`` | an empty list produced by how the evidence was cut, not by measurement |
   | ``not-applicable`` | the battery's own structural absence (an arm with no repair episode) |
   | ``undeclared-source`` | a number that exists, but only in a file this figure may not read |

   The last kind currently has no rows. P-21 shipped this figure with three of
   them; P4 declared all three files in ``sources.py``, so they are now hashed
   inputs and are drawn. ``UNDECLARED_WANTS`` is deliberately kept as an empty
   tuple rather than deleted: the machinery that names a gap on the plate, in
   the CSV and in ``notes`` is what stopped those three numbers from being
   quietly dropped, and the next gap should be reported the same way.

4. **One number in this figure comes from prose, and says so.** The full-sweep
   RED pixel figures (128 unexplained of 20088 checked) exist in no artefact --
   ``exhibit_report.certify_cheap_vs_full_sweep`` carries the anomaly count and
   no pixel keys at all. ``A2_REPORT.md`` is now a declared, hashed source, so
   they are drawn, labelled prose-sourced, and cross-checked two ways: the
   anomaly count in the same sentence must equal the artefact's, and the pixel
   total must equal frames x the pixels-per-frame the two JSON certify records
   agree on. **The `44 is a CAP, not a count` caveat is unchanged by any of
   this** -- the cheap layer still caps its anomaly list, so 44 is a ceiling.

**Figure text is English.** The beats are named bilingually in the ledger
(``打脸 · refutation``) and that bilingual string is the machine-readable form,
so it is preserved verbatim in the CSV. It is *not* drawn: matplotlib's bundled
DejaVu Sans has no CJK coverage, so CJK renders as tofu boxes and the embedded
SVG path data would depend on whatever system font got substituted -- which
breaks byte-determinism on any other machine. Only the English half of each
``name`` is rendered; the split is programmatic (on U+00B7), so the plate cannot
drift from the ledger.

Sources are read only through ``sources.py`` keys, so every input is hashed into
``figures/SOURCES.sha256``. Two numbers this figure would like and cannot have
are named on its face rather than silently omitted -- see ``notes``.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig05_a2_repair_loop"

# --------------------------------------------------------------------------
# vocabulary
# --------------------------------------------------------------------------

#: The two beats that build and display the broken theorem. They are in the
#: ledger and they are not repair beats; the figure keeps them upstream.
PRELUDE_BEATS: tuple[str, ...] = ("M0", "M5")

#: The repair loop proper. Six, not eight.
LOOP_BEATS: tuple[str, ...] = ("L1", "L2", "L3", "L4", "L5", "L6")

BEAT_ORDER: tuple[str, ...] = PRELUDE_BEATS + LOOP_BEATS

#: The runs the battery can even ask K12/K13 of: the theory-bearing arms. Every
#: other run in capability_spectrum.json (the ~100 bare_cc runs and the upstream
#: transcripts) carries the same `not-applicable` reason, so listing them would
#: be a hundred identical hatched rows. Declared explicitly rather than filtered
#: by prefix, so a new run cannot silently join or leave the panel.
THEORY_RUNS: tuple[str, ...] = (
    "a0-base",
    "a0-no-button",
    "a0-spike",
    "a2-play-record",
    "a2-probed",
    "a2-refutation",
    "a2-sweep",
)

MEASURED = "measured"
REAL_ZERO = "real-zero"
STRUCTURAL = "structurally-absent"
BY_CONSTRUCTION = "absent-by-construction"
NOT_APPLICABLE = "not-applicable"
UNDECLARED = "undeclared-source"

CSV_HEADER = (
    "order",
    "beat",
    "name_bilingual",
    "name_en",
    "phase",
    "status",
    "claim",
    "key_metric",
    "key_value",
    "value_kind",
    "evidence",
    "note",
)

#: Numbers that exist in the repository and are not reachable from this figure's
#: declared source list. Named here, printed in ``notes``, and drawn on the
#: plate at the beat that wants them -- never quietly dropped, never plotted.
#:
#: **Empty, and kept.** It held three entries when this figure was first built:
#: ``engines_diff.json`` (M0's rule counts), ``engines_diff_probed.json`` (L4's
#: re-proposal) and ``A2_REPORT.md`` (M5's pixel figures). All three are now
#: declared in ``sources.py``, hashed, and drawn. The machinery stays so that the
#: next number this figure wants and cannot have is reported the same way rather
#: than silently omitted.
UNDECLARED_WANTS: tuple[tuple[str, str, str], ...] = ()

#: The name of the one rule the whole exhibit turns on. Not used to *find*
#: anything -- the figure computes the sweep/history set difference and asserts
#: it is exactly this one rule, so a changed miner stops the build instead of
#: quietly redrawing "the hole" as something else.
THE_MISSING_RULE = "obj1_jump_DOWN"

#: The sentence in ``A2_REPORT.md`` that is the only home of the full-sweep pixel
#: figures. Anchored on three numbers at once so a reworded paragraph cannot
#: match half of it and hand back a plausible wrong number.
_PROSE_PIXELS = re.compile(
    r"(\d[\d ]*?) unexplained pixels across (\d[\d ]*?) checked, (\d+) anomalies recorded"
)


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def _english(name: str) -> str:
    """The English half of a bilingual ledger ``name``.

    The ledger writes ``<CJK> · <english>``. Splitting programmatically rather
    than hard-coding the six strings means the plate cannot drift from the file,
    and it is also the mechanism that keeps CJK off a DejaVu-only canvas.
    """
    parts = [p.strip() for p in name.split("·")]
    if len(parts) != 2 or not parts[1]:
        raise ValueError(
            f"ledger beat name {name!r} is not the expected '<CJK> · <english>' "
            "form; the figure renders the English half and cannot guess it"
        )
    return parts[1]


def _load() -> dict:
    """Every declared source this figure reads, in one place."""
    return {
        "ledger": sources.read_json("a2_loop_ledger"),
        "refutation": sources.read_json("a2_refutation"),
        "locate": sources.read_json("a2_locate_report"),
        "probe_report": sources.read_json("a2_probe_report"),
        "probes": sources.read_jsonl("a2_probes"),
        "exhibit": sources.read_json("a2_exhibit_report"),
        "repair": sources.read_json("a2_repair_report"),
        "plan_repaired": sources.read_json("a2_plan_repaired"),
        "traces": sources.read_json("a2_trace_summary"),
        "engines": sources.read_json("a2_engines_diff"),
        "engines_probed": sources.read_json("a2_engines_diff_probed"),
        "report": sources.read_text("a2_report"),
        "spectrum": sources.read_json("capability_spectrum"),
    }


def _prose_pixels(report: str) -> tuple[int, int, int]:
    """``(unexplained, checked, anomalies)`` from A2_REPORT.md's one sentence.

    The numbers are written with a thin-space thousands separator and wrapped
    across a line break, so the document is whitespace-normalised first. Three
    numbers are captured, not one: the anomaly count is redundant with
    ``exhibit_report`` and is used as a tripwire in ``extract``.
    """
    match = _PROSE_PIXELS.search(" ".join(report.split()))
    if match is None:
        raise ValueError(
            "A2_REPORT.md no longer contains the full-sweep pixel sentence this "
            "figure reads. The figures exist in no artefact, so a rewording must "
            "stop the build rather than silently drop them from the plate."
        )
    return tuple(int(g.replace(" ", "")) for g in match.groups())  # type: ignore[return-value]


def _engine_side(payload: dict, key: str) -> dict:
    """One miner run out of an ``engines_diff``-shaped artefact."""
    side = payload[key]
    jumps = side["rules_with_a_jump_effect"]
    return {
        "frames": side["frames"],
        "transitions": side["transitions"],
        "rules": sorted(side["rules_proposed"]),
        "n_rules": len(side["rules_proposed"]),
        "n_jumps": len(jumps),
        "jump_name": jumps[0]["name"] if jumps else None,
        "jump_guard": jumps[0]["guard"] if jumps else None,
        "jump_coverage": jumps[0]["coverage"] if jumps else None,
        "jump_transitions": jumps[0]["transitions"] if jumps else None,
    }


def _beats_by_id(ledger: dict) -> dict[str, dict]:
    """The ledger's beats keyed by id, with the eight/six discipline enforced."""
    beats = {b["beat"]: b for b in ledger["beats"]}
    seen = tuple(sorted(beats))
    if seen != tuple(sorted(BEAT_ORDER)):
        raise ValueError(
            f"loop_ledger.json holds beats {seen}; this figure is written against "
            f"{tuple(sorted(BEAT_ORDER))}. The prelude/loop split is a claim about "
            "the data, so a changed beat set must stop the build."
        )
    total = ledger["summary"]["total"]
    if total != len(BEAT_ORDER):
        raise ValueError(
            f"loop_ledger.summary.total is {total}, not {len(BEAT_ORDER)}; the "
            "eight-beat summary is exactly the trap this figure exists to avoid "
            "carrying onto a six-beat plate"
        )
    return beats


def _probe_rows(probes: list[dict]) -> list[dict]:
    """One row per probe, sorted by id, with absence preserved as ``None``.

    P-03 is ``tier: hypothetical`` / ``status: not_separable_in_this_world`` and
    carries **no outcome fields at all** -- no ``manual_agreed``, no ``refuted``,
    no ``surviving``. It is a designed experiment this world cannot run, not an
    experiment that returned nothing, so every outcome column stays ``None`` and
    the panel draws it hatched.
    """
    rows: list[dict] = []
    for p in sorted(probes, key=lambda q: q["id"]):
        has_outcome = "predictions" in p
        rows.append(
            {
                "id": p["id"],
                "tier": p["tier"],
                "status": p["status"],
                "question": p["question"],
                "n_predictions": len(p["predictions"]) if has_outcome else None,
                "n_refuted": len(p["refuted"]) if has_outcome else None,
                "n_surviving": len(p["surviving"]) if has_outcome else None,
                "surviving": sorted(p["surviving"]) if has_outcome else None,
                "manual_agreed": p.get("manual_agreed") if has_outcome else None,
                "observation": p.get("observation") if has_outcome else None,
                "action": p.get("action") if has_outcome else None,
            }
        )
    return rows


def _spectrum_rows(spectrum: dict) -> list[dict]:
    """K12/K13 for the theory-bearing arms, status preserved."""
    runs = spectrum["runs"]
    out: list[dict] = []
    for run in THEORY_RUNS:
        if run not in runs:
            raise KeyError(
                f"capability_spectrum.json has no run {run!r}; THEORY_RUNS is "
                "declared explicitly so this is a real change, not a filter miss"
            )
        metrics = runs[run].get("metrics", {})
        row: dict = {"run": run}
        for card in ("K12", "K13"):
            entry = metrics.get(card)
            if entry is None:
                raise KeyError(f"{run}: capability_spectrum has no {card} entry")
            row[card] = {
                "status": entry.get("status"),
                "value": entry.get("value"),
                "support": entry.get("support"),
                "reason": entry.get("reason"),
            }
        out.append(row)
    return out


def extract() -> tuple[dict, list[dict], list[str]]:
    """``(values, metrics, notes)``. No plotting, no writing.

    ``values`` is the flat number bag the renderer draws from; ``metrics`` is the
    CSV's row model. Both come from the same reads, so a number on the plate is
    the number in the CSV by construction rather than by care.
    """
    notes: list[str] = []
    raw = _load()
    ledger = raw["ledger"]
    beats = _beats_by_id(ledger)
    refutation = raw["refutation"]
    locate = raw["locate"]
    probe_report = raw["probe_report"]
    exhibit = raw["exhibit"]
    repair = raw["repair"]
    plan_rep = raw["plan_repaired"]
    traces = raw["traces"]

    probe_rows = _probe_rows(raw["probes"])
    spectrum_rows = _spectrum_rows(raw["spectrum"])

    # --- cross-checks: the roll-up counts against the rows themselves -------
    designed = len(probe_rows)
    executable = sum(1 for r in probe_rows if r["tier"] == "executable")
    refuted = sum(1 for r in probe_rows if r["status"] == "refuted")
    not_separable = sum(1 for r in probe_rows if r["status"] == "not_separable_in_this_world")
    with_surviving = sum(1 for r in probe_rows if r["n_surviving"])
    declared = (
        probe_report["probes_designed"],
        probe_report["executable"],
        probe_report["refuted"],
        probe_report["not_separable"],
    )
    if (designed, executable, refuted, not_separable) != declared:
        raise ValueError(
            f"probes.jsonl counts {(designed, executable, refuted, not_separable)} "
            f"disagree with probe_report's {declared}; not reconciled here"
        )
    notes.append(
        f"L3 cross-check: probes.jsonl and probe_report.json agree -- {designed} designed, "
        f"{executable} executable, {refuted} refuted, {not_separable} not separable."
    )
    notes.append(
        f"L3 'confirmed: {probe_report['confirmed']}' is a coding artefact, not a finding: "
        f"a probe is coded 'refuted' when it refutes at least one hypothesis, and all "
        f"{executable} executable probes did. {with_surviving} of {executable} also left a "
        "hypothesis standing (P-02.1/2/3 confirm `ring_is_solid`), so the figure reports "
        "'executed / left a hypothesis standing / not separable' and never draws a 0 bar "
        "for `confirmed` beside a 4 bar for `refuted`."
    )

    # --- the miner, on three evidence sets ---------------------------------
    # M0's hole and L4's re-derivation are the same rule seen twice, so both
    # sides are read through one shaper and checked against the ledger's own
    # booleans rather than trusted.
    eng_sweep = _engine_side(raw["engines"], "candidates.jsonl")
    eng_history = _engine_side(raw["engines"], "candidates_history.jsonl")
    eng_probed = _engine_side(raw["engines_probed"], "candidates_probed.jsonl")
    only_in_sweep = sorted(set(eng_sweep["rules"]) - set(eng_history["rules"]))
    only_in_history = sorted(set(eng_history["rules"]) - set(eng_sweep["rules"]))
    if only_in_sweep != [THE_MISSING_RULE] or only_in_history:
        raise ValueError(
            f"the sweep/history rule sets differ by {only_in_sweep} (and "
            f"{only_in_history} the other way); this figure draws 'the two evidence sets "
            f"are exactly one rule apart, and that rule is {THE_MISSING_RULE}', which "
            "would no longer be true"
        )
    verdict = raw["engines"]["verdict"]
    ledger_m0 = beats["M0"]["detail"]
    if (verdict["sweep_proposes_a_jump"] != ledger_m0["sweep_proposes_a_jump"]
            or verdict["history_proposes_a_jump"] != ledger_m0["history_proposes_a_jump"]):
        raise ValueError("engines_diff.verdict disagrees with loop_ledger's M0 detail")
    if (eng_sweep["n_jumps"] != 1 or eng_history["n_jumps"] != 0
            or eng_probed["n_jumps"] != 1):
        raise ValueError(
            "the jump-effect counts changed (sweep/history/probed = "
            f"{eng_sweep['n_jumps']}/{eng_history['n_jumps']}/{eng_probed['n_jumps']}, "
            "expected 1/0/1)"
        )
    if eng_probed["jump_name"] != THE_MISSING_RULE:
        raise ValueError(
            f"the grown evidence re-proposes {eng_probed['jump_name']!r}, not "
            f"{THE_MISSING_RULE!r}; L4's corroboration claim is that it is the SAME rule"
        )

    history = traces["history_trace"]
    sweep = traces["raw_trace"]
    ex_cheap = exhibit["certify_cheap"]
    ex_full = exhibit["certify_cheap_vs_full_sweep"]
    rp_cheap = repair["certify_cheap"]
    stale = repair["stale_certificate"]
    region = repair["region"]
    scored = repair["scored_against_the_world"]

    # The exhibit's plan is UNSAT and therefore has NO length and NO backend.
    # Both are drawn as structural absences, so both are asserted rather than
    # assumed: if the artefact ever grows a length, the absence claim is wrong.
    if "length" in exhibit["plan"]:
        raise ValueError(
            "exhibit_report.plan grew a 'length' key; 'an UNSAT arm has no plan length' "
            "is a claim this figure draws, so it must stop the build rather than lie"
        )
    if exhibit["plan"]["status"] != "UNSAT" or exhibit["plan"]["backend"] is not None:
        raise ValueError("exhibit_report.plan is no longer the UNSAT / backend-null arm")

    # --- the one prose-sourced pair, checked twice before it is drawn -------
    prose_unexplained, prose_checked, prose_anomalies = _prose_pixels(raw["report"])
    if prose_anomalies != ex_full["anomalies"]:
        raise ValueError(
            f"A2_REPORT.md says {prose_anomalies} anomalies, exhibit_report says "
            f"{ex_full['anomalies']}; the prose has drifted from the artefact and its "
            "pixel figures cannot be trusted either"
        )
    # 14904/184 and 15876/196 both give 81 cells per frame; the sweep's own
    # pixel total is not in any artefact, so it is checked against that rate.
    rates = {
        ex_cheap["pixels_checked"] / ex_cheap["frames"],
        rp_cheap["pixels_checked"] / rp_cheap["frames"],
    }
    if len(rates) != 1:
        raise ValueError(f"the two certify records disagree on pixels per frame: {sorted(rates)}")
    pixels_per_frame = rates.pop()
    expected = int(round(ex_full["frames"] * pixels_per_frame))
    if expected != prose_checked:
        raise ValueError(
            f"A2_REPORT.md's {prose_checked} checked pixels does not equal "
            f"{ex_full['frames']} frames x {pixels_per_frame:g} pixels/frame = {expected}"
        )

    v: dict = {
        # ---- M0: the complete manual -----------------------------------
        "m0_sweep_frames": sweep["frames"],
        "m0_sweep_transitions": sweep["transitions"],
        "m0_history_frames": history["frames"],
        "m0_history_transitions": history["transitions"],
        "m0_sweep_jump": beats["M0"]["detail"]["sweep_proposes_a_jump"],
        "m0_history_jump": beats["M0"]["detail"]["history_proposes_a_jump"],
        "m0_plan_status": beats["M0"]["detail"]["plan"],
        "m0_plan_length": beats["M0"]["detail"]["plan_length"],
        "m0_history_portal_transitions": len(history["portal_transitions"]),
        "m0_history_win_frames": len(history["win_frames"]),
        "m0_sweep_portal_transition": traces["portal_transition"],
        "m0_history_coverage": history["coverage"],
        "m0_sweep_coverage": sweep["coverage"],
        "m0_omitted_pair": traces["history_omitted_pairs"][0],
        # the hole, as a number: two evidence sets, one rule apart
        "m0_sweep_rules": eng_sweep["n_rules"],
        "m0_sweep_jumps": eng_sweep["n_jumps"],
        "m0_history_rules": eng_history["n_rules"],
        "m0_history_jumps": eng_history["n_jumps"],
        "m0_missing_rule": THE_MISSING_RULE,
        "m0_jump_guard": ", ".join(eng_sweep["jump_guard"]),
        "m0_jump_coverage": eng_sweep["jump_coverage"],
        "m0_jump_transition": eng_sweep["jump_transitions"][0],
        "m0_shared_rules": eng_history["n_rules"],
        # ---- M5: the exhibit -------------------------------------------
        "m5_replay_frames": ex_cheap["frames"],
        "m5_replay_transitions": ex_cheap["transitions"],
        "m5_replay_pixels": ex_cheap["pixels_checked"],
        "m5_replay_unexplained": ex_cheap["pixels_unexplained"],
        "m5_replay_anomaly_kinds": len(ex_cheap["anomaly_kinds"]),
        "m5_replay_green": ex_cheap["green"],
        "m5_lean_green": exhibit["certify_lean"]["green"],
        "m5_lean_returncode": exhibit["certify_lean"]["returncode"],
        "m5_lean_errors": len(exhibit["certify_lean"]["errors"]),
        "m5_lean_theorem": exhibit["certify_lean"]["axiom_reports"][0]["name"],
        "m5_lean_axioms": len(exhibit["certify_lean"]["axiom_reports"][0]["axioms"]),
        "m5_plan_status": exhibit["plan"]["status"],
        "m5_false_of_the_world": exhibit["exhibit_is_false_of_the_world"],
        "m5_sweep_frames": ex_full["frames"],
        "m5_sweep_anomalies": ex_full["anomalies"],
        "m5_sweep_anomaly_kinds": len(ex_full["anomaly_kinds"]),
        "m5_sweep_green": ex_full["green"],
        "m5_sweep_first_t": ex_full["first_anomaly"]["t"],
        "m5_sweep_first_cell": tuple(ex_full["first_anomaly"]["cell"]),
        "m5_sweep_first_kind": ex_full["first_anomaly"]["kind"],
        "m5_theorem": exhibit["theorem"]["name"],
        "m5_region_size": exhibit["zero_space"]["region_size"],
        # prose-sourced, cross-checked, and labelled as prose everywhere it is drawn
        "m5_sweep_pixels": prose_checked,
        "m5_sweep_unexplained": prose_unexplained,
        "m5_pixels_per_frame": int(pixels_per_frame),
        # ---- L1: refutation ---------------------------------------------
        "l1_theorems_in": 1,
        "l1_episodes_out": 1,
        "l1_episode_length": refutation["episode"]["length"],
        "l1_episode_frames": refutation["episode"]["frames"],
        "l1_final_win": refutation["episode"]["final_win"],
        "l1_refuted": refutation["refuted"],
        "l1_search_space": len(refutation["search_space_per_1_4"]),
        "l1_win_frame": refutation["episode"]["win_frames"][0],
        "l1_theorem": refutation["claim"]["theorem"],
        # ---- L2: localisation --------------------------------------------
        "l2_path_length": locate["path_length"],
        "l2_checks_run": len(locate["checks"]),
        "l2_board_diffs": len(locate["board_diffs"]),
        "l2_goal_diffs": len(locate["goal_diffs"]),
        "l2_misread_board": locate["checks"]["misread_board"],
        "l2_wrong_goal_test": locate["checks"]["wrong_goal_test"],
        "l2_mispredicted_step": locate["checks"]["mispredicted_step"],
        "l2_n_step_diffs": locate["n_step_diffs"],
        "l2_t": locate["located"]["t"],
        "l2_mover_at": tuple(locate["located"]["mover_at"]),
        "l2_action": locate["located"]["action"],
        "l2_manual_predicts": tuple(locate["located"]["manual_predicts"]),
        "l2_world_shows": tuple(locate["located"]["world_shows"]),
        "l2_rules_fired": len(locate["located"]["rules_that_fired"]),
        "l2_diagnosis": beats["L2"]["detail"]["diagnosis"],
        # ---- L3: probe ----------------------------------------------------
        "l3_designed": designed,
        "l3_executable": executable,
        "l3_refuted": refuted,
        "l3_not_separable": not_separable,
        "l3_with_surviving": with_surviving,
        "l3_confirmed_field": probe_report["confirmed"],
        "l3_frames_before": probe_report["trace_frames_before"],
        "l3_frames_after": probe_report["trace_frames_after"],
        "l3_frames_delta": probe_report["trace_frames_after"] - probe_report["trace_frames_before"],
        "l3_transitions_before": ex_cheap["transitions"],
        "l3_transitions_after": rp_cheap["transitions"],
        # ---- L4: revision --------------------------------------------------
        "l4_re_derivable": beats["L4"]["detail"]["re_derivable_from_grown_evidence"],
        "l4_teleport_steps": sum(
            1 for a in plan_rep["actions"] if a.startswith("(teleport-down ")
        ),
        "l4_pddl_cells_added": len(repair["compiled"]["pddl_cells_added"]),
        # corroboration from a DIFFERENT artefact, not a stand-in for the boolean
        "l4_probed_frames": eng_probed["frames"],
        "l4_probed_transitions": eng_probed["transitions"],
        "l4_probed_rules": eng_probed["n_rules"],
        "l4_probed_jumps": eng_probed["n_jumps"],
        "l4_probed_jump_name": eng_probed["jump_name"],
        "l4_probed_jump_transition": eng_probed["jump_transitions"][0],
        "l4_probed_jump_coverage": eng_probed["jump_coverage"],
        # ---- L5: re-proof ---------------------------------------------------
        "l5_stale_died": stale["died"],
        "l5_stale_returncode": stale["lean"]["returncode"],
        "l5_stale_errors": len(stale["lean"]["errors"]),
        "l5_stale_axioms": ", ".join(sorted(stale["lean"]["axiom_reports"][0]["axioms"])),
        "l5_stale_n_axioms": len(stale["lean"]["axiom_reports"][0]["axioms"]),
        "l5_stale_region": stale["region_size"],
        "l5_new_green": repair["certify_lean"]["green"],
        "l5_new_axioms": len(repair["certify_lean"]["axiom_reports"][0]["axioms"]),
        "l5_new_theorem": beats["L5"]["detail"]["new_theorem"],
        "l5_latch_green": repair["certify_lean_latch"]["green"],
        "l5_latch_axioms": len(repair["certify_lean_latch"]["axiom_reports"][0]["axioms"]),
        "l5_latch_theorem": repair["certify_lean_latch"]["axiom_reports"][0]["name"],
        "l5_cheap_frames": rp_cheap["frames"],
        "l5_cheap_transitions": rp_cheap["transitions"],
        "l5_cheap_pixels": rp_cheap["pixels_checked"],
        "l5_cheap_anomaly_kinds": len(rp_cheap["anomaly_kinds"]),
        "l5_cheap_green": rp_cheap["green"],
        "l5_region_proposed": region["zero_space_size"],
        "l5_region_adopted": region["adopted_size"],
        "l5_pocket_in_closure": region["pocket_in_closure"],
        "l5_pocket_states": scored["world_states_with_cart_in_pocket"],
        "l5_reachable_states": sweep["reachable_states"],
        "l5_true_of_the_world": scored["true_of_the_world"],
        # ---- L6: solved -------------------------------------------------------
        "l6_status": plan_rep["status"],
        "l6_length": plan_rep["length"],
        "l6_manual_reaches_goal": plan_rep["manual_reaches_goal"],
        "l6_world_reaches_goal": plan_rep["world_reaches_goal"],
        "l6_mismatches": len(plan_rep["execution_mismatches"]),
        "l6_backend": plan_rep["backend"],
        "l6_green": plan_rep["green"],
        # ---- the ledger's own accounting --------------------------------------
        "ledger_total": ledger["summary"]["total"],
        "ledger_pass": ledger["summary"]["pass"],
        "ledger_fail": ledger["summary"]["fail"],
        "ledger_absent": ledger["summary"]["absent"],
        "loop_beats": len(LOOP_BEATS),
        "authority": ledger["authority"],
        "world": ledger["world"],
    }

    # The one number the exhibit's cheap layer does NOT emit for the repaired
    # run: repair_report.certify_cheap has no `pixels_unexplained` key at all,
    # while exhibit_report.certify_cheap does. Recorded, not invented as 0.
    v["l5_cheap_unexplained_key_present"] = "pixels_unexplained" in rp_cheap

    metrics = _metric_rows(beats, v, probe_rows, spectrum_rows)

    notes.append(
        f"beat accounting: loop_ledger holds {v['ledger_total']} beats "
        f"({'+'.join(PRELUDE_BEATS)} prelude + {len(LOOP_BEATS)} loop) and its summary reads "
        f"{v['ledger_pass']} pass / {v['ledger_fail']} fail / {v['ledger_absent']} absent. The "
        f"figure draws the loop's own score, {len(LOOP_BEATS)}/{len(LOOP_BEATS)}, and never the "
        "8-pass summary."
    )
    notes.append(
        f"summary.absent = {v['ledger_absent']} is a real zero and is legended as one: ledger.py "
        "has a genuine third status ('absent', for a missing artefact), the channel was "
        "exercisable, and no beat hit it."
    )
    notes.append(
        "P-03 is drawn hatched, not as a zero: tier 'hypothetical', status "
        "'not_separable_in_this_world', and no outcome fields exist on the record at all "
        "(the world has exactly one Portal, so neither separating configuration is reachable)."
    )
    notes.append(
        f"M5's plan is UNSAT with backend null and no 'length' key: an UNSAT arm has no plan "
        f"length, so the figure marks it structurally absent rather than 0 (M0's SAT plan is "
        f"length {v['m0_plan_length']}, L6's repaired plan is length {v['l6_length']})."
    )
    notes.append(
        f"M0's hole is now a number: the sweep ({v['m0_sweep_frames']} frames) makes the miner "
        f"propose {v['m0_sweep_rules']} rules, {v['m0_sweep_jumps']} with a jump effect; the "
        f"history ({v['m0_history_frames']} frames) makes it propose {v['m0_history_rules']}, "
        f"{v['m0_history_jumps']} with a jump effect. The set difference is asserted to be "
        f"exactly {{{v['m0_missing_rule']}}} in both directions, so a changed miner stops the "
        "build instead of redrawing the hole as something else. The 0 is a MEASURED zero -- the "
        "miner ran and proposed no jump rule -- and is drawn as a shorter bar with its count "
        "printed, never as an absence."
    )
    notes.append(
        f"the full-sweep RED is drawn as {v['m5_sweep_anomalies']} anomalies over "
        f"{v['m5_sweep_frames']} frames, still labelled a CAP: the cheap layer caps its anomaly "
        "list, so 44 remains a ceiling, not a count. That caveat is unchanged by the pixel "
        "figures, which count a different quantity."
    )
    notes.append(
        f"PROSE-SOURCED, and labelled as such everywhere it is drawn: the full sweep's "
        f"{v['m5_sweep_unexplained']} unexplained pixels of {v['m5_sweep_pixels']} checked exist "
        "only in A2_REPORT.md's prose -- exhibit_report.certify_cheap_vs_full_sweep carries no "
        f"pixel key at all. Two tripwires guard it: the same sentence's anomaly count must equal "
        f"the artefact's ({v['m5_sweep_anomalies']}), and the pixel total must equal "
        f"{v['m5_sweep_frames']} frames x {v['m5_pixels_per_frame']} pixels/frame, the rate the "
        "two JSON certify records independently agree on."
    )
    notes.append(
        f"L4 keeps its honest point AND gains its corroboration, drawn as two separate things: "
        f"the beat's own ledger metric is still a boolean (re_derivable_from_grown_evidence = "
        f"{str(v['l4_re_derivable']).lower()}) with no count-shaped metric in loop_ledger, and "
        f"engines_diff_probed.json -- a different artefact -- shows what that boolean asserts: "
        f"the grown {v['l4_probed_frames']}-frame evidence re-proposes {v['l4_probed_rules']} "
        f"rules, {v['l4_probed_jumps']} with a jump effect, and it is asserted to be "
        f"{v['l4_probed_jump_name']} again, now at transition {v['l4_probed_jump_transition']} "
        f"rather than {v['m0_jump_transition']}. The node labels which is which."
    )
    notes.append(
        "history_trace.portal_transitions [] and win_frames [] are empty by construction, not by "
        "measurement: the history is cut at the portal transition (t="
        f"{v['m0_sweep_portal_transition']}), which is what omits the single pair "
        f"'{v['m0_omitted_pair']}' and puts the hole in the manual."
    )
    notes.append(
        f"L4's own ledger accounting is still a boolean and no 0/N is synthesised from it; the "
        f"node also draws the {v['l4_teleport_steps']} teleport-down step and "
        f"{v['l4_pddl_cells_added']} PDDL cell the repair actually added."
    )
    for beat, path, what in UNDECLARED_WANTS:
        notes.append(
            f"NOT SOURCED ({beat}): {what}. It lives in {path}, which is not a declared key "
            "in figures/sources.py, so it is named on the plate and in the CSV as "
            f"'{UNDECLARED}' and never plotted."
        )
    if not UNDECLARED_WANTS:
        notes.append(
            "no declared-source gaps remain for this figure: the three files P-21 shipped as "
            "'undeclared-source' (engines_diff.json, engines_diff_probed.json, A2_REPORT.md) are "
            "declared, hashed and drawn. UNDECLARED_WANTS is kept empty rather than deleted so "
            "the next gap is reported the same way instead of quietly dropped."
        )
    ok_k12 = [r["run"] for r in spectrum_rows if r["K12"]["status"] == "ok"]
    na = [r["run"] for r in spectrum_rows if r["K12"]["status"] == "not-applicable"]
    notes.append(
        f"K12/K13: {len(ok_k12)} of {len(spectrum_rows)} theory-bearing runs carry a value "
        f"({', '.join(sorted(ok_k12))}); {len(na)} are status 'not-applicable' "
        f"({', '.join(sorted(na))}) and are drawn hatched, never as 0. a0-spike's K12 = 0.000 "
        "IS a measured zero (0 of 24 required beats over 4 rebuild episodes) and is drawn as a "
        "zero-length bar with its numerator printed, so it cannot be mistaken for an absence."
    )
    return v, metrics, notes


# --------------------------------------------------------------------------
# the CSV row model -- the audit surface
# --------------------------------------------------------------------------


def _metric_rows(
    beats: dict[str, dict], v: dict, probe_rows: list[dict], spectrum_rows: list[dict]
) -> list[dict]:
    """One row per (beat, key_metric). Order is literal, not discovered."""
    rows: list[dict] = []

    def add(beat: str, metric: str, value, kind: str, evidence: str, note: str = "") -> None:
        b = beats.get(beat)
        rows.append(
            {
                "beat": beat,
                "name_bilingual": b["name"] if b else "",
                "name_en": _english(b["name"]) if b else "",
                "phase": "prelude" if beat in PRELUDE_BEATS else "loop",
                "status": b["status"] if b else "",
                "claim": b["claim"] if b else "",
                "key_metric": metric,
                "key_value": value,
                "value_kind": kind,
                "evidence": evidence,
                "note": note,
            }
        )

    TS = "a2_trace_summary"
    LL = "a2_loop_ledger"
    EX = "a2_exhibit_report"
    RF = "a2_refutation"
    LO = "a2_locate_report"
    PR = "a2_probe_report"
    PJ = "a2_probes"
    RP = "a2_repair_report"
    PL = "a2_plan_repaired"
    ED = "a2_engines_diff"
    EDP = "a2_engines_diff_probed"
    MD = "a2_report"

    # ---- M0 -----------------------------------------------------------------
    add("M0", "sweep_frames", v["m0_sweep_frames"], MEASURED, f"{TS}:raw_trace.frames")
    add("M0", "sweep_transitions", v["m0_sweep_transitions"], MEASURED, f"{TS}:raw_trace.transitions")
    add("M0", "sweep_coverage", v["m0_sweep_coverage"], MEASURED, f"{TS}:raw_trace.coverage")
    add("M0", "sweep_proposes_a_jump", v["m0_sweep_jump"], MEASURED,
        f"{LL}:beats[M0].detail.sweep_proposes_a_jump")
    add("M0", "history_frames", v["m0_history_frames"], MEASURED, f"{TS}:history_trace.frames")
    add("M0", "history_transitions", v["m0_history_transitions"], MEASURED,
        f"{TS}:history_trace.transitions")
    add("M0", "history_coverage", v["m0_history_coverage"], MEASURED, f"{TS}:history_trace.coverage")
    add("M0", "history_proposes_a_jump", v["m0_history_jump"], MEASURED,
        f"{LL}:beats[M0].detail.history_proposes_a_jump",
        "false is measured, not absent: the miner ran on the history and returned no jump rule")
    # Written as the literal empty list, not as its length: a reviewer scanning
    # this column must not meet a `0` in a row whose whole point is that no
    # measurement produced it.
    add("M0", "history_portal_transitions", "[]", BY_CONSTRUCTION,
        f"{TS}:history_trace.portal_transitions",
        f"empty because the history is cut at transition {v['m0_sweep_portal_transition']}, "
        "before the teleport -- absence by construction, not a measured 0")
    add("M0", "history_win_frames", "[]", BY_CONSTRUCTION,
        f"{TS}:history_trace.win_frames", "same cut; the history never reaches a win")
    add("M0", "history_omitted_pairs", v["m0_omitted_pair"], MEASURED,
        f"{TS}:history_omitted_pairs[0]", "the single pair whose absence is the hole")
    add("M0", "plan_status", v["m0_plan_status"], MEASURED, f"{LL}:beats[M0].detail.plan")
    add("M0", "plan_length", v["m0_plan_length"], MEASURED, f"{LL}:beats[M0].detail.plan_length")
    add("M0", "rules_proposed_from_sweep", v["m0_sweep_rules"], MEASURED,
        f"{ED}:candidates.jsonl.rules_proposed")
    add("M0", "rules_with_a_jump_effect_from_sweep", v["m0_sweep_jumps"], MEASURED,
        f"{ED}:candidates.jsonl.rules_with_a_jump_effect")
    add("M0", "rules_proposed_from_history", v["m0_history_rules"], MEASURED,
        f"{ED}:candidates_history.jsonl.rules_proposed")
    add("M0", "rules_with_a_jump_effect_from_history", v["m0_history_jumps"], REAL_ZERO,
        f"{ED}:candidates_history.jsonl.rules_with_a_jump_effect",
        "a measured zero: the miner ran on the history and proposed no jump rule. This is "
        "the hole -- the manual is false of the world because its evidence never showed the "
        "teleport, not because a rule was removed to order")
    add("M0", "rules_only_in_the_sweep", v["m0_missing_rule"], MEASURED,
        f"{ED}: set(candidates.jsonl.rules_proposed) - set(candidates_history.jsonl.rules_proposed)",
        f"the two rule sets are exactly one rule apart, both ways; asserted in extract(), so a "
        f"changed miner stops the build rather than redrawing 'the hole' as something else")
    add("M0", "shared_rules", v["m0_shared_rules"], MEASURED,
        f"{ED}: set intersection of the two rules_proposed lists")
    add("M0", "missing_rule_guard", v["m0_jump_guard"], MEASURED,
        f"{ED}:candidates.jsonl.rules_with_a_jump_effect[0].guard")
    add("M0", "missing_rule_coverage", v["m0_jump_coverage"], MEASURED,
        f"{ED}:candidates.jsonl.rules_with_a_jump_effect[0].coverage",
        "one witness, and the history is cut before it")
    add("M0", "missing_rule_transition", v["m0_jump_transition"], MEASURED,
        f"{ED}:candidates.jsonl.rules_with_a_jump_effect[0].transitions[0]",
        "the same transition the history is cut at -- see history_portal_transitions")

    # ---- M5 -----------------------------------------------------------------
    add("M5", "replay_frames", v["m5_replay_frames"], MEASURED, f"{EX}:certify_cheap.frames")
    add("M5", "replay_transitions", v["m5_replay_transitions"], MEASURED,
        f"{EX}:certify_cheap.transitions")
    add("M5", "replay_pixels_checked", v["m5_replay_pixels"], MEASURED,
        f"{EX}:certify_cheap.pixels_checked")
    add("M5", "replay_pixels_unexplained", v["m5_replay_unexplained"], REAL_ZERO,
        f"{EX}:certify_cheap.pixels_unexplained", "a checked zero over 14904 pixels")
    add("M5", "replay_anomaly_kinds", v["m5_replay_anomaly_kinds"], REAL_ZERO,
        f"{EX}:certify_cheap.anomaly_kinds")
    add("M5", "replay_green", v["m5_replay_green"], MEASURED, f"{EX}:certify_cheap.green")
    add("M5", "lean_green", v["m5_lean_green"], MEASURED, f"{EX}:certify_lean.green")
    add("M5", "lean_returncode", v["m5_lean_returncode"], REAL_ZERO, f"{EX}:certify_lean.returncode")
    add("M5", "lean_errors", v["m5_lean_errors"], REAL_ZERO, f"{EX}:certify_lean.errors")
    add("M5", f"axioms_of_{v['m5_lean_theorem']}", v["m5_lean_axioms"], REAL_ZERO,
        f"{EX}:certify_lean.axiom_reports[0].axioms",
        "`#print axioms unsolvable` = [] -- the theorem leans on nothing and is still false "
        "of the world")
    add("M5", "theorem", v["m5_theorem"], MEASURED, f"{EX}:theorem.name")
    add("M5", "plan_status", v["m5_plan_status"], MEASURED, f"{EX}:plan.status")
    add("M5", "plan_length", "", STRUCTURAL, f"{EX}:plan (no 'length' key)",
        "an UNSAT arm has no plan length; the key does not exist and is not a 0")
    add("M5", "plan_backend", "", STRUCTURAL, f"{EX}:plan.backend = null",
        "no backend ran, because there was nothing to run")
    add("M5", "false_of_the_world", v["m5_false_of_the_world"], MEASURED,
        f"{EX}:exhibit_is_false_of_the_world")
    add("M5", "zero_space_region_size", v["m5_region_size"], MEASURED, f"{EX}:zero_space.region_size")
    add("M5", "full_sweep_frames", v["m5_sweep_frames"], MEASURED,
        f"{EX}:certify_cheap_vs_full_sweep.frames")
    add("M5", "full_sweep_anomalies", v["m5_sweep_anomalies"], MEASURED,
        f"{EX}:certify_cheap_vs_full_sweep.anomalies",
        "the cheap layer CAPS its anomaly list, so 44 is a cap, not a count")
    add("M5", "full_sweep_anomaly_kinds", v["m5_sweep_anomaly_kinds"], MEASURED,
        f"{EX}:certify_cheap_vs_full_sweep.anomaly_kinds")
    add("M5", "full_sweep_first_anomaly", f"t={v['m5_sweep_first_t']} cell "
        f"({v['m5_sweep_first_cell'][0]},{v['m5_sweep_first_cell'][1]}) {v['m5_sweep_first_kind']}",
        MEASURED, f"{EX}:certify_cheap_vs_full_sweep.first_anomaly")
    add("M5", "full_sweep_green", v["m5_sweep_green"], MEASURED,
        f"{EX}:certify_cheap_vs_full_sweep.green")
    add("M5", "full_sweep_pixels_checked", v["m5_sweep_pixels"], MEASURED,
        f"{MD}:section 2 prose (`... across 20 088 checked ...`)",
        f"PROSE-SOURCED. No artefact carries a pixel key for the sweep. Cross-checked: "
        f"{v['m5_sweep_frames']} frames x {v['m5_pixels_per_frame']} pixels/frame = "
        f"{v['m5_sweep_pixels']}, and the two JSON certify records agree on the rate")
    add("M5", "full_sweep_pixels_unexplained", v["m5_sweep_unexplained"], MEASURED,
        f"{MD}:section 2 prose (`128 unexplained pixels`)",
        "PROSE-SOURCED, and it does NOT soften the anomaly caveat: 44 remains a cap on the "
        "anomaly LIST, which is a different quantity from the pixel count")
    add("M5", "full_sweep_prose_anomalies", v["m5_sweep_anomalies"], MEASURED,
        f"{MD}:section 2 prose, cross-checked against "
        f"{EX}:certify_cheap_vs_full_sweep.anomalies",
        "the same sentence restates the anomaly count; extract() asserts the two agree, so a "
        "prose that drifted from the artefact stops the build")

    # ---- L1 -----------------------------------------------------------------
    add("L1", "machine_checked_theorems_in", v["l1_theorems_in"], MEASURED,
        f"{RF}:claim (one theorem: {v['l1_theorem']})")
    add("L1", "solved_episodes_out", v["l1_episodes_out"], MEASURED, f"{RF}:episode")
    add("L1", "episode_length_actions", v["l1_episode_length"], MEASURED, f"{RF}:episode.length")
    add("L1", "episode_frames", v["l1_episode_frames"], MEASURED, f"{RF}:episode.frames")
    add("L1", "final_win", v["l1_final_win"], MEASURED, f"{RF}:episode.final_win")
    add("L1", "win_frame", v["l1_win_frame"], MEASURED, f"{RF}:episode.win_frames[0]")
    add("L1", "refuted", v["l1_refuted"], MEASURED, f"{RF}:refuted")
    add("L1", "search_space_per_1_4", v["l1_search_space"], MEASURED,
        f"{RF}:search_space_per_1_4",
        "Theoria 1.4 bounds the error to three candidate sites on this path")

    # ---- L2 -----------------------------------------------------------------
    add("L2", "witness_path_transitions", v["l2_path_length"], MEASURED, f"{LO}:path_length")
    add("L2", "checks_run", v["l2_checks_run"], MEASURED, f"{LO}:checks",
        "all three of 1.4's checks were run, not just the one that fired")
    add("L2", "misread_board", v["l2_misread_board"], MEASURED, f"{LO}:checks.misread_board")
    add("L2", "board_diffs", v["l2_board_diffs"], REAL_ZERO, f"{LO}:board_diffs",
        "a measured zero: the board was compared frame by frame and matched everywhere")
    add("L2", "wrong_goal_test", v["l2_wrong_goal_test"], MEASURED, f"{LO}:checks.wrong_goal_test")
    add("L2", "goal_diffs", v["l2_goal_diffs"], REAL_ZERO, f"{LO}:goal_diffs",
        "a measured zero: the goal test agreed with the episode's win flag at every frame")
    add("L2", "mispredicted_step", v["l2_mispredicted_step"], MEASURED,
        f"{LO}:checks.mispredicted_step")
    add("L2", "n_step_diffs", v["l2_n_step_diffs"], MEASURED, f"{LO}:n_step_diffs")
    add("L2", "located_at_t", v["l2_t"], MEASURED, f"{LO}:located.t")
    add("L2", "mover_at", f"({v['l2_mover_at'][0]},{v['l2_mover_at'][1]})", MEASURED,
        f"{LO}:located.mover_at")
    add("L2", "action", v["l2_action"], MEASURED, f"{LO}:located.action")
    add("L2", "manual_predicts", f"({v['l2_manual_predicts'][0]},{v['l2_manual_predicts'][1]})",
        MEASURED, f"{LO}:located.manual_predicts")
    add("L2", "world_shows", f"({v['l2_world_shows'][0]},{v['l2_world_shows'][1]})", MEASURED,
        f"{LO}:located.world_shows")
    add("L2", "rules_that_fired", v["l2_rules_fired"], REAL_ZERO, f"{LO}:located.rules_that_fired",
        "a measured zero, and the whole diagnosis: nothing fired, so nothing can be corrected")
    add("L2", "diagnosis", v["l2_diagnosis"], MEASURED, f"{LL}:beats[L2].detail.diagnosis")

    # ---- L3 -----------------------------------------------------------------
    add("L3", "probes_designed", v["l3_designed"], MEASURED, f"{PJ} (rows), {PR}:probes_designed")
    add("L3", "probes_executable", v["l3_executable"], MEASURED, f"{PR}:executable")
    add("L3", "probes_refuted", v["l3_refuted"], MEASURED, f"{PR}:refuted",
        "'refuted' means the probe refuted at least one hypothesis -- not that nothing survived")
    add("L3", "probes_leaving_a_surviving_hypothesis", v["l3_with_surviving"], MEASURED,
        f"{PJ}:surviving (per row)",
        "the honest counterpart to `confirmed`: every executable probe left one standing")
    add("L3", "probe_report_confirmed_field", v["l3_confirmed_field"], MEASURED, f"{PR}:confirmed",
        "a coding artefact, NOT a finding: the status vocabulary makes 'refuted' win over "
        "'confirmed' whenever a probe refutes anything, and all four did. P-02.1/2/3 confirm "
        "`ring_is_solid`. Never draw this 0 beside the 4.")
    add("L3", "probes_not_separable", v["l3_not_separable"], MEASURED, f"{PR}:not_separable")
    add("L3", "trace_frames_before", v["l3_frames_before"], MEASURED, f"{PR}:trace_frames_before")
    add("L3", "trace_frames_after", v["l3_frames_after"], MEASURED, f"{PR}:trace_frames_after")
    add("L3", "trace_frames_delta", v["l3_frames_delta"], MEASURED,
        f"{PR}:trace_frames_after - trace_frames_before")
    add("L3", "trace_transitions_before", v["l3_transitions_before"], MEASURED,
        f"{EX}:certify_cheap.transitions")
    add("L3", "trace_transitions_after", v["l3_transitions_after"], MEASURED,
        f"{RP}:certify_cheap.transitions")
    for row in probe_rows:
        pid = row["id"]
        src = f"{PJ}:{pid}"
        add("L3", f"{pid}.tier", row["tier"], MEASURED, f"{src}.tier")
        add("L3", f"{pid}.status", row["status"], MEASURED, f"{src}.status")
        if row["n_predictions"] is None:
            reason = (
                "designed and unrunnable: this world has exactly one Portal, so neither "
                "separating configuration is reachable. probes.jsonl carries NO outcome fields "
                "for this row -- no manual_agreed, no refuted, no surviving. Hatched, not zero."
            )
            for field in ("hypotheses_on_the_record", "hypotheses_refuted",
                          "hypotheses_surviving", "manual_agreed"):
                add("L3", f"{pid}.{field}", "", STRUCTURAL, f"{src} (key absent)", reason)
        else:
            add("L3", f"{pid}.hypotheses_on_the_record", row["n_predictions"], MEASURED,
                f"{src}.predictions", "written before the action, not after")
            add("L3", f"{pid}.hypotheses_refuted", row["n_refuted"], MEASURED, f"{src}.refuted")
            add("L3", f"{pid}.hypotheses_surviving", row["n_surviving"], MEASURED,
                f"{src}.surviving", "; ".join(row["surviving"]))
            add("L3", f"{pid}.manual_agreed", row["manual_agreed"], MEASURED,
                f"{src}.manual_agreed", f"observation: {row['observation']}")

    # ---- L4 -----------------------------------------------------------------
    add("L4", "re_derivable_from_grown_evidence", v["l4_re_derivable"], MEASURED,
        f"{LL}:beats[L4].detail.re_derivable_from_grown_evidence",
        "THE BEAT'S OWN METRIC, and it is a boolean: loop_ledger's L4 detail has exactly one key")
    add("L4", "count_shaped_metric_in_the_ledger", "", STRUCTURAL,
        f"{LL}:beats[L4].detail (one key, a boolean)",
        "the ledger holds no count for L4, and none is invented from one. The engines_diff_probed "
        "rows below are corroboration from a DIFFERENT artefact -- they show what the boolean is "
        "asserting; they are not this beat's score")
    add("L4", "teleport_down_steps_in_repaired_plan", v["l4_teleport_steps"], MEASURED,
        f"{PL}:actions", "the one rule the repair restored, as it appears in the plan")
    add("L4", "pddl_cells_added", v["l4_pddl_cells_added"], MEASURED,
        f"{RP}:compiled.pddl_cells_added", "cell (7,4), the teleport's intermediate")
    add("L4", "grown_evidence_frames", v["l4_probed_frames"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.frames", "corroboration, not the beat's metric")
    add("L4", "grown_evidence_transitions", v["l4_probed_transitions"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.transitions", "corroboration, not the beat's metric")
    add("L4", "rules_re_proposed_from_grown_evidence", v["l4_probed_rules"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.rules_proposed",
        "corroboration, not the beat's metric: the same 23-rule set the SWEEP proposed, now "
        "derived from evidence the loop grew for itself")
    add("L4", "re_proposed_rules_with_a_jump_effect", v["l4_probed_jumps"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.rules_with_a_jump_effect",
        "the history proposed 0 of these; the grown evidence proposes 1 again")
    add("L4", "re_proposed_jump_rule", v["l4_probed_jump_name"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.rules_with_a_jump_effect[0].name",
        f"asserted in extract() to be {THE_MISSING_RULE} -- the claim is that it is the SAME "
        "rule, not merely some jump rule")
    add("L4", "re_proposed_jump_transition", v["l4_probed_jump_transition"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.rules_with_a_jump_effect[0].transitions[0]",
        f"transition {v['l4_probed_jump_transition']} in the probed trace, where the sweep saw "
        f"it at {v['m0_jump_transition']}: a witness the loop produced, not one it was given")
    add("L4", "re_proposed_jump_coverage", v["l4_probed_jump_coverage"], MEASURED,
        f"{EDP}:candidates_probed.jsonl.rules_with_a_jump_effect[0].coverage")

    # ---- L5 -----------------------------------------------------------------
    add("L5", "stale_certificate_died", v["l5_stale_died"], MEASURED, f"{RP}:stale_certificate.died")
    add("L5", "stale_lean_returncode", v["l5_stale_returncode"], MEASURED,
        f"{RP}:stale_certificate.lean.returncode")
    add("L5", "stale_lean_errors", v["l5_stale_errors"], MEASURED,
        f"{RP}:stale_certificate.lean.errors")
    add("L5", "stale_axioms_of_unsolvable", v["l5_stale_axioms"], MEASURED,
        f"{RP}:stale_certificate.lean.axiom_reports[0].axioms",
        "the old certificate now leans on sorryAx -- it did not merely weaken, it died")
    add("L5", "stale_region_size", v["l5_stale_region"], MEASURED,
        f"{RP}:stale_certificate.region_size")
    add("L5", "new_theorem", v["l5_new_theorem"], MEASURED, f"{LL}:beats[L5].detail.new_theorem")
    add("L5", "new_lean_green", v["l5_new_green"], MEASURED, f"{RP}:certify_lean.green")
    add("L5", "new_lean_axioms", v["l5_new_axioms"], REAL_ZERO,
        f"{RP}:certify_lean.axiom_reports[0].axioms", "axiom-free again -- and this time true")
    add("L5", "latch_theorem", v["l5_latch_theorem"], MEASURED,
        f"{RP}:certify_lean_latch.axiom_reports[0].name")
    add("L5", "latch_lean_green", v["l5_latch_green"], MEASURED, f"{RP}:certify_lean_latch.green")
    add("L5", "latch_lean_axioms", v["l5_latch_axioms"], REAL_ZERO,
        f"{RP}:certify_lean_latch.axiom_reports[0].axioms")
    add("L5", "cheap_frames", v["l5_cheap_frames"], MEASURED, f"{RP}:certify_cheap.frames")
    add("L5", "cheap_transitions", v["l5_cheap_transitions"], MEASURED,
        f"{RP}:certify_cheap.transitions")
    add("L5", "cheap_pixels_checked", v["l5_cheap_pixels"], MEASURED,
        f"{RP}:certify_cheap.pixels_checked")
    add("L5", "cheap_anomaly_kinds", v["l5_cheap_anomaly_kinds"], REAL_ZERO,
        f"{RP}:certify_cheap.anomaly_kinds")
    if not v["l5_cheap_unexplained_key_present"]:
        add("L5", "cheap_pixels_unexplained", "", STRUCTURAL,
            f"{RP}:certify_cheap (no 'pixels_unexplained' key)",
            "exhibit_report emits this key and repair_report does not; the empty anomaly list "
            "is what is on the record, so no 0 is borrowed from the other artefact")
    add("L5", "cheap_green", v["l5_cheap_green"], MEASURED, f"{RP}:certify_cheap.green")
    add("L5", "region_zero_space_proposed", v["l5_region_proposed"], MEASURED,
        f"{RP}:region.zero_space_size")
    add("L5", "region_adopted", v["l5_region_adopted"], MEASURED, f"{RP}:region.adopted_size",
        "widened to the manual's own reachability closure, computed by running theory.py")
    add("L5", "pocket_in_closure", v["l5_pocket_in_closure"], MEASURED, f"{RP}:region.pocket_in_closure")
    add("L5", "world_states_with_cart_in_pocket", v["l5_pocket_states"], REAL_ZERO,
        f"{RP}:scored_against_the_world.world_states_with_cart_in_pocket",
        f"0 of {v['l5_reachable_states']} reachable states -- enumerated, not assumed")
    add("L5", "reachable_states", v["l5_reachable_states"], MEASURED, f"{TS}:raw_trace.reachable_states")
    add("L5", "true_of_the_world", v["l5_true_of_the_world"], MEASURED,
        f"{RP}:scored_against_the_world.true_of_the_world")

    # ---- L6 -----------------------------------------------------------------
    add("L6", "plan_status", v["l6_status"], MEASURED, f"{PL}:status")
    add("L6", "plan_length", v["l6_length"], MEASURED, f"{PL}:length")
    add("L6", "manual_reaches_goal", v["l6_manual_reaches_goal"], MEASURED, f"{PL}:manual_reaches_goal")
    add("L6", "world_reaches_goal", v["l6_world_reaches_goal"], MEASURED, f"{PL}:world_reaches_goal")
    add("L6", "execution_mismatches", v["l6_mismatches"], REAL_ZERO, f"{PL}:execution_mismatches",
        "a measured zero: all 18 planned steps were executed against the world and none diverged")
    add("L6", "backend", v["l6_backend"], MEASURED, f"{PL}:backend",
        "the BFS stub, not a Fast Downward rung -- see engine-rig STATUS.md P-13")
    add("L6", "green", v["l6_green"], MEASURED, f"{PL}:green")

    # ---- the ledger's own accounting, and the battery ------------------------
    ledger_rows = [
        ("ledger_beats_total", v["ledger_total"], MEASURED,
         "a2_loop_ledger:summary.total",
         "M0 + M5 + L1-L6. The repair loop proper is the six L-beats; the other two are prelude"),
        ("ledger_beats_pass", v["ledger_pass"], MEASURED, "a2_loop_ledger:summary.pass", ""),
        ("ledger_beats_fail", v["ledger_fail"], REAL_ZERO, "a2_loop_ledger:summary.fail", ""),
        ("ledger_beats_absent", v["ledger_absent"], REAL_ZERO, "a2_loop_ledger:summary.absent",
         "a real and meaningful zero: ledger.py has a third status 'absent' for a missing "
         "artefact; the channel was exercisable and no beat hit it"),
        ("loop_beats_drawn", v["loop_beats"], MEASURED, "figures/fig05_a2_repair_loop.py:LOOP_BEATS",
         "the figure's own count: L1-L6"),
        ("authority", v["authority"], MEASURED, "a2_loop_ledger:authority",
         "INC-004: a self-built world isomorphic to DC22's failure structure; no upstream DC22 "
         "artefact was read and the pile seal is intact"),
        ("world", v["world"], MEASURED, "a2_loop_ledger:world", ""),
    ]
    for metric, value, kind, evidence, note in ledger_rows:
        rows.append(
            {
                "beat": "LEDGER",
                "name_bilingual": "",
                "name_en": "",
                "phase": "accounting",
                "status": "",
                "claim": "",
                "key_metric": metric,
                "key_value": value,
                "value_kind": kind,
                "evidence": evidence,
                "note": note,
            }
        )

    for row in spectrum_rows:
        for card in ("K12", "K13"):
            entry = row[card]
            status = entry["status"]
            support = entry["support"] or {}
            if status == "ok":
                value = theme.fmt_num(entry["value"])
                kind = REAL_ZERO if entry["value"] == 0 else MEASURED
                if card == "K12":
                    note = (
                        f"{support.get('closed')} of {support.get('required')} beats closed over "
                        f"{support.get('episodes')} episode(s)"
                    )
                else:
                    note = (
                        f"strategy: {support.get('strategy')}, over "
                        f"{support.get('episodes')} episode(s); lower is better"
                    )
            else:
                value = ""
                kind = NOT_APPLICABLE
                note = entry["reason"] or ""
            rows.append(
                {
                    "beat": card,
                    "name_bilingual": "",
                    "name_en": (
                        "share of the six repair beats that closed"
                        if card == "K12"
                        else "environment actions spent repairing / actions the theory cost"
                    ),
                    "phase": "battery",
                    "status": status,
                    "claim": row["run"],
                    "key_metric": f"{card}[{row['run']}]",
                    "key_value": value,
                    "value_kind": kind,
                    "evidence": f"capability_spectrum:runs.{row['run']}.metrics.{card}",
                    "note": note,
                }
            )

    return rows


def csv_rows(metrics: list[dict]) -> list[list]:
    """``metrics`` in emission order, numbered. Order is declared, not sorted."""
    out: list[list] = []
    for i, m in enumerate(metrics):
        value = m["key_value"]
        if isinstance(value, bool):
            value = theme.fmt_num(value)
        out.append(
            [
                i,
                m["beat"],
                m["name_bilingual"],
                m["name_en"],
                m["phase"],
                m["status"],
                m["claim"],
                m["key_metric"],
                value,
                m["value_kind"],
                m["evidence"],
                m["note"],
            ]
        )
    return out


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------


def _yn(flag: bool) -> str:
    return "yes" if flag else "no"


def _node_lines(v: dict) -> dict[str, list[str]]:
    """The decisive numbers for each loop node, read from the extracted bag.

    Written here rather than inline in the drawing code so that every string on
    the plate is visibly a function of a number the CSV also carries.
    """
    return {
        "L1": [
            f"{v['l1_theorems_in']} machine-checked theorem in",
            f"({v['l1_theorem']}, axioms = [])",
            f"{v['l1_episodes_out']} solved episode out:",
            f"{v['l1_episode_length']} actions, {v['l1_episode_frames']} frames,",
            f"win at frame {v['l1_win_frame']}, refuted = {_yn(v['l1_refuted'])}",
            "",
            f"1.4 bounds the search to",
            f"{v['l1_search_space']} candidate error sites",
        ],
        "L2": [
            f"{v['l2_path_length']} transitions x {v['l2_checks_run']} checks,",
            "all three run",
            "",
            f"misread board: {_yn(v['l2_misread_board'])} ({v['l2_board_diffs']} diffs)",
            f"wrong goal test: {_yn(v['l2_wrong_goal_test'])} ({v['l2_goal_diffs']} diffs)",
            f"mispredicted step: {_yn(v['l2_mispredicted_step'])} ({v['l2_n_step_diffs']} diff)",
            "",
            f"at t={v['l2_t']}, ({v['l2_mover_at'][0]},{v['l2_mover_at'][1]}) {v['l2_action']}:",
            f"manual ({v['l2_manual_predicts'][0]},{v['l2_manual_predicts'][1]}), "
            f"world ({v['l2_world_shows'][0]},{v['l2_world_shows'][1]})",
            f"{v['l2_rules_fired']} rules fired ->",
            f"\"{v['l2_diagnosis']}\"",
        ],
        "L3": [
            f"designed {v['l3_designed']} -> executable {v['l3_executable']}",
            "",
            f"{v['l3_executable']} executed, {v['l3_refuted']} refuted at",
            f"least one hypothesis, {v['l3_with_surviving']} left",
            "one standing",
            f"{v['l3_not_separable']} not separable in this",
            "world (hatched below)",
            "",
            f"evidence {v['l3_frames_before']} -> {v['l3_frames_after']} frames",
            f"(+{v['l3_frames_delta']}); {v['l3_transitions_before']} -> "
            f"{v['l3_transitions_after']} transitions",
        ],
        # The beat's own score and its corroboration are two different things
        # from two different artefacts, and the node has to say which is which.
        "L4": [
            "THE BEAT'S METRIC is a boolean:",
            "loop_ledger's L4 detail has one",
            "key, and no count-shaped metric.",
            f"re_derivable_from_grown_evidence",
            f"  = {_yn(v['l4_re_derivable'])}   (no 0/N is invented)",
            "",
            "CORROBORATION, from a different",
            "artefact (engines_diff_probed):",
            f"the grown {v['l4_probed_frames']}-frame evidence",
            f"re-proposes {v['l4_probed_rules']} rules, "
            f"{v['l4_probed_jumps']} with a",
            f"jump effect -- {v['l4_probed_jump_name']}",
            f"again, at transition {v['l4_probed_jump_transition']}",
            f"(the sweep saw it at {v['m0_jump_transition']})",
            "",
            f"{v['l4_teleport_steps']} teleport-down step, "
            f"{v['l4_pddl_cells_added']} PDDL cell",
        ],
        "L5": [
            f"stale cert died: {_yn(v['l5_stale_died'])}",
            f"rc {v['l5_stale_returncode']}, {v['l5_stale_errors']} errors, axiom",
            f"{v['l5_stale_axioms']}; region {v['l5_stale_region']}",
            "",
            f"new `{v['l5_new_theorem']}`",
            f"and latch `{v['l5_latch_theorem']}`:",
            f"green, {v['l5_new_axioms']} axioms each",
            "",
            f"{v['l5_cheap_frames']} fr / {v['l5_cheap_transitions']} tr / "
            f"{v['l5_cheap_pixels']} px,",
            f"{v['l5_cheap_anomaly_kinds']} anomalies -> GREEN",
            f"region {v['l5_region_proposed']} -> {v['l5_region_adopted']} cells",
            f"{v['l5_pocket_states']} of {v['l5_reachable_states']} states in pocket",
        ],
        "L6": [
            f"plan {v['l6_status']}, length {v['l6_length']}",
            f"backend {v['l6_backend']}",
            "",
            f"manual reaches goal: {_yn(v['l6_manual_reaches_goal'])}",
            f"world reaches goal: {_yn(v['l6_world_reaches_goal'])}",
            "",
            f"{v['l6_mismatches']} execution mismatches",
            "over all 18 steps",
            f"(a checked zero)",
        ],
    }


def _flow(ax, v: dict, names: dict[str, str], p: dict, theme_name: str) -> None:
    """Panel A: the prelude band, the six-beat loop, and M5's three ANDed facts."""
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.grid(False)

    ramp = theme.sequential_steps(theme_name, len(LOOP_BEATS), ordinal=True)
    ink, ink2, muted = p["ink"], p["ink_secondary"], p["muted"]
    good, bad = theme.STATUS["good"], theme.STATUS["critical"]

    # ---- prelude band ---------------------------------------------------
    ax.add_patch(
        Rectangle(
            (1.0, 60.0), 98.0, 39.0,
            facecolor=p["page"], edgecolor=p["axis"], linestyle=(0, (4, 3)),
            linewidth=0.7, zorder=0,
        )
    )
    ax.text(
        2.2, 97.6,
        "PRELUDE  -  the two beats that build and display the broken theorem. "
        "In the ledger, not in the loop.",
        ha="left", va="top", fontsize=theme.BASE_FONT_SIZE - 2, color=ink2,
    )
    ax.text(
        2.2, 94.4,
        f"loop_ledger.summary counts {v['ledger_pass']} pass / {v['ledger_total']} total "
        f"(M0 + M5 + L1-L6). This plate draws the loop's own score, "
        f"{len(LOOP_BEATS)}/{len(LOOP_BEATS)}, and never the {v['ledger_total']}-beat summary.",
        ha="left", va="top", fontsize=theme.BASE_FONT_SIZE - 3, color=muted,
    )

    def header(x, y, w, beat, name, edge, size=7.2):
        ax.text(x + 1.0, y, beat, ha="left", va="center", fontsize=size,
                color=ink, fontweight="bold")
        ax.text(x + 1.0 + 3.4 * size / 7.2, y, name, ha="left", va="center",
                fontsize=size - 1.2, color=ink2)
        ax.text(x + w - 1.0, y, "pass", ha="right", va="center",
                fontsize=size - 1.6, color=good)

    # ---- M0: the hole, drawn as the one rule the two evidence sets differ by
    ax.add_patch(
        Rectangle((3.0, 64.0), 35.0, 27.0, facecolor=p["surface"], edgecolor=muted,
                  linestyle=(0, (4, 3)), linewidth=1.0, zorder=1)
    )
    header(3.0, 88.6, 35.0, "M0", names["M0"], muted)
    ax.text(4.2, 86.0,
            "the miner, on two evidence sets -- one rule apart, and that rule is the hole",
            ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3.6, color=ink)

    c_shared = theme.series_colour(theme_name, 0)
    c_jump = theme.series_colour(theme_name, 1)
    h_jump = theme.series_hatch(1)
    span, per_rule = 20.0, 20.0 / v["m0_sweep_rules"]
    for label, y_text, y_bar, n_rules, n_jumps in (
        (
            f"sweep  {v['m0_sweep_frames']} fr / {v['m0_sweep_transitions']} tr:  "
            f"{v['m0_sweep_rules']} rules proposed, {v['m0_sweep_jumps']} with a jump effect",
            83.6, 81.5, v["m0_sweep_rules"], v["m0_sweep_jumps"],
        ),
        (
            f"history  {v['m0_history_frames']} fr / {v['m0_history_transitions']} tr:  "
            f"{v['m0_history_rules']} rules proposed, {v['m0_history_jumps']} with a jump "
            "effect (a MEASURED zero)",
            79.0, 76.9, v["m0_history_rules"], v["m0_history_jumps"],
        ),
    ):
        ax.text(4.2, y_text, label, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.8, color=ink)
        shared = n_rules - n_jumps
        ax.add_patch(
            Rectangle((4.2, y_bar - 0.75), shared * per_rule, 1.5, facecolor=c_shared,
                      edgecolor="none", zorder=2)
        )
        if n_jumps:
            # Taller than the rest, so the single extra rule is visible at this
            # scale; 22-vs-23 is the honest proportion and stays the proportion.
            ax.add_patch(
                Rectangle((4.2 + shared * per_rule, y_bar - 1.15), n_jumps * per_rule, 2.3,
                          facecolor=c_jump, edgecolor=ink2, hatch=h_jump, linewidth=0.6,
                          zorder=3)
            )
            ax.text(4.2 + span + 0.5, y_bar, v["m0_missing_rule"], ha="left", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 4.0, color=ink)
        else:
            ax.text(4.2 + shared * per_rule + 0.5, y_bar, "-- no jump rule proposed",
                    ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 4.0, color=muted)

    m0_lines = [
        (f"sweep - history = exactly {{ {v['m0_missing_rule']} }}, and history - sweep = {{ }}",
         ink),
        (f"guard [{v['m0_jump_guard']}], coverage {v['m0_jump_coverage']}, fires once, at "
         f"transition {v['m0_jump_transition']}", ink),
        (f"plan {v['m0_plan_status']}, length {v['m0_plan_length']}; the world agrees", ink),
        (f"the history is cut at transition {v['m0_sweep_portal_transition']} and omits exactly "
         f"one pair, {v['m0_omitted_pair']} -- the", muted),
        ("one that fires that rule. portal_transitions [] and win_frames [] are empty by",
         muted),
        ("construction, not measured zeros.", muted),
    ]
    for i, (line, colour) in enumerate(m0_lines):
        ax.text(4.2, 74.2 - i * 1.75, line, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.9, color=colour)

    # ---- M5: the crux ---------------------------------------------------
    ax.add_patch(
        Rectangle((41.0, 64.0), 56.0, 27.0, facecolor=p["surface"], edgecolor=ink2,
                  linewidth=1.3, zorder=1)
    )
    header(41.0, 88.6, 56.0, "M5", names["M5"], ink2)
    ax.text(
        69.0, 86.0,
        "three facts hold AT ONCE -- their co-occurrence is the whole phenomenon",
        ha="center", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=ink2,
    )

    badges = [
        (
            "1. it replays the play record",
            [
                f"{v['m5_replay_frames']} frames / {v['m5_replay_transitions']} transitions",
                f"{v['m5_replay_pixels']} pixels checked",
                f"{v['m5_replay_unexplained']} unexplained, "
                f"{v['m5_replay_anomaly_kinds']} anomaly kinds",
                "-> 100%, GREEN",
            ],
            good,
        ),
        (
            "2. Lean signs it",
            [
                f"returncode {v['m5_lean_returncode']}, {v['m5_lean_errors']} errors, 0 sorries",
                f"#print axioms {v['m5_lean_theorem']}",
                f"  = []  ({v['m5_lean_axioms']} axioms)",
                "-> machine-checked, GREEN",
            ],
            good,
        ),
        (
            "3. the world contradicts it",
            [
                f"solved episode: {v['l1_episode_length']} actions,",
                f"{v['l1_episode_frames']} frames, win = {_yn(v['l1_final_win'])}",
                f"exhibit_is_false_of_the_world",
                f"  = {_yn(v['m5_false_of_the_world'])}   -> RED",
            ],
            bad,
        ),
    ]
    bx, bgap = 42.5, 2.4
    bw = (53.0 - bgap * (len(badges) - 1)) / len(badges)
    for i, (title, lines, chip) in enumerate(badges):
        x = bx + i * (bw + bgap)
        ax.add_patch(
            Rectangle((x, 71.4), bw, 12.6, facecolor="none", edgecolor=chip,
                      linewidth=1.0, zorder=2)
        )
        ax.text(x + 0.8, 82.7, title, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3, color=ink, fontweight="bold")
        for j, line in enumerate(lines):
            ax.text(x + 0.8, 80.0 - j * 2.2, line, ha="left", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 3.6, color=ink)
        if i < len(badges) - 1:
            ax.text(x + bw + bgap / 2.0, 77.7, "AND", ha="center", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 3, color=ink2, fontweight="bold")

    footers = (
        f"plan {v['m5_plan_status']}: the planner returns no plan, so there is NO plan length "
        "and NO backend -- structurally absent keys, not zeros.",
        f"the same manual against the full {v['m5_sweep_frames']}-frame sweep is RED: "
        f"{v['m5_sweep_anomalies']} anomalies in {v['m5_sweep_anomaly_kinds']} kinds -- a CAP, "
        "not a count, because the cheap layer caps its anomaly list --",
        f"first at t={v['m5_sweep_first_t']} cell "
        f"({v['m5_sweep_first_cell'][0]},{v['m5_sweep_first_cell'][1]}); "
        f"{v['m5_sweep_unexplained']} unexplained pixels of {v['m5_sweep_pixels']} checked, "
        "from A2_REPORT.md prose -- no artefact carries a pixel key for the sweep.",
    )
    for i, line in enumerate(footers):
        ax.text(42.5, 69.6 - i * 2.15, line, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.5, color=ink2)

    ax.annotate(
        "", xy=(40.6, 77.5), xytext=(38.4, 77.5),
        arrowprops={"arrowstyle": "-|>", "color": muted, "linewidth": 1.0,
                    "shrinkA": 0, "shrinkB": 0},
    )

    # ---- the loop --------------------------------------------------------
    y0, h = 14.0, 36.0
    gap = 2.2
    w = (96.0 - gap * (len(LOOP_BEATS) - 1)) / len(LOOP_BEATS)
    xs = [2.0 + i * (w + gap) for i in range(len(LOOP_BEATS))]
    lines_of = _node_lines(v)

    ax.annotate(
        "", xy=(xs[0] + w * 0.5, y0 + h + 0.6), xytext=(43.0, 63.4),
        arrowprops={"arrowstyle": "-|>", "color": ink2, "linewidth": 1.1,
                    "connectionstyle": "arc3,rad=0.16", "shrinkA": 0, "shrinkB": 0},
    )
    ax.text(
        44.0, 57.0,
        "the loop is handed a manual that is green on its own evidence, signed, and false",
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=ink2,
    )

    for i, beat in enumerate(LOOP_BEATS):
        x = xs[i]
        ax.add_patch(
            Rectangle((x, y0), w, h, facecolor=p["surface"], edgecolor=ramp[i],
                      linewidth=1.5, zorder=1)
        )
        ax.add_patch(
            Rectangle((x + 0.7, y0 + h - 3.0), 2.0, 2.0, facecolor=ramp[i],
                      edgecolor="none", zorder=2)
        )
        ax.text(x + 3.4, y0 + h - 2.0, beat, ha="left", va="center",
                fontsize=8.0, color=ink, fontweight="bold")
        ax.text(x + w - 0.7, y0 + h - 2.0, "pass", ha="right", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.2, color=good)
        ax.text(x + 0.7, y0 + h - 5.6, names[beat], ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 2, color=ink2)
        # Line pitch is per node: L4 carries the most lines, and the pitch is
        # derived rather than tuned so a longer node cannot silently overflow.
        body = lines_of[beat]
        pitch = min(2.3, (h - 10.4) / max(1, len(body) - 1))
        for j, line in enumerate(body):
            ax.text(x + 0.7, y0 + h - 8.9 - j * pitch, line, ha="left", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 3.8, color=ink)
        if i < len(LOOP_BEATS) - 1:
            ax.annotate(
                "", xy=(x + w + gap, y0 + h * 0.5), xytext=(x + w, y0 + h * 0.5),
                arrowprops={"arrowstyle": "-|>", "color": ramp[i], "linewidth": 1.2,
                            "shrinkA": 0, "shrinkB": 0},
            )

    # ---- the loop closes -------------------------------------------------
    lc, rc = xs[0] + w * 0.5, xs[-1] + w * 0.5
    ax.plot([rc, rc, lc], [y0, 8.0, 8.0], color=ramp[-1], linewidth=1.0,
            linestyle=(0, (5, 3)), zorder=1)
    ax.annotate(
        "", xy=(lc, y0 - 0.2), xytext=(lc, 8.0),
        arrowprops={"arrowstyle": "-|>", "color": ramp[-1], "linewidth": 1.0,
                    "shrinkA": 0, "shrinkB": 0},
    )
    ax.text(
        50.0, 5.6,
        f"the loop closes: {len(LOOP_BEATS)} of {len(LOOP_BEATS)} beats pass  (K12 = 1.000 on "
        f"a2-probed).  The ledger's third status, `absent`, was available throughout and no beat "
        f"hit it: summary.absent = {v['ledger_absent']} is a real zero.",
        ha="center", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=ink2,
    )
    ax.text(
        50.0, 2.2,
        f"authority: INC-004 ruling 2026-07-28, option (b) -- a self-built world ({v['world']}) "
        "isomorphic to DC22's failure structure. No upstream DC22 artefact was read; the pile "
        "seal is intact.",
        ha="center", va="center", fontsize=theme.BASE_FONT_SIZE - 3.4, color=muted,
    )


def _probes_panel(ax, v: dict, probe_rows: list[dict], p: dict, theme_name: str) -> None:
    """Panel B: L3's five probes. P-03 is hatched, never a zero bar."""
    ink2, muted = p["ink_secondary"], p["muted"]
    c_ref = theme.series_colour(theme_name, 0)
    c_sur = theme.series_colour(theme_name, 2)
    h_ref = theme.series_hatch(0)
    h_sur = theme.series_hatch(2)

    xmax = 3.0
    ax.set_xlim(0.0, 3.05)
    # One blank lane above (for the `confirmed` note) and one below (legend), so
    # neither ever lands on a bar.
    ax.set_ylim(len(probe_rows) + 0.35, -1.05)
    ax.set_xticks([0, 1, 2, 3])
    ax.grid(False)
    ax.set_xlabel("hypotheses written down BEFORE the action was taken")

    for row_i, row in enumerate(probe_rows):
        if row["n_predictions"] is None:
            ax.add_patch(
                Rectangle(
                    (0.0, row_i - 0.30), xmax, 0.46,
                    facecolor=theme.ABSENCE["not-applicable"]["facecolor"],
                    edgecolor=ink2, hatch=theme.ABSENCE["not-applicable"]["hatch"],
                    linewidth=0.8, zorder=2,
                )
            )
            detail = (
                "designed and unrunnable: tier `hypothetical`, status "
                "`not_separable_in_this_world` -- probes.jsonl carries NO outcome fields for "
                "this row at all"
            )
        else:
            ax.barh(row_i - 0.07, row["n_refuted"], height=0.46, color=c_ref, hatch=h_ref,
                    edgecolor=p["surface"], linewidth=0.6, zorder=2)
            ax.barh(row_i - 0.07, row["n_surviving"], left=row["n_refuted"], height=0.46,
                    color=c_sur, hatch=h_sur, edgecolor=p["surface"], linewidth=0.6, zorder=2)
            agreed = "manual agreed" if row["manual_agreed"] else "manual DISAGREED"
            detail = (
                f"{agreed}; observed \"{row['observation']}\"; surviving: "
                f"{', '.join(row['surviving'])}"
            )
        ax.text(0.03, row_i + 0.34, detail, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.4, color=ink2)

    ax.set_yticks(list(range(len(probe_rows))))
    ax.set_yticklabels([r["id"] for r in probe_rows], fontsize=theme.BASE_FONT_SIZE - 2)
    ax.set_title(
        f"B. L3: {v['l3_designed']} probes designed, {v['l3_executable']} executable, "
        f"{v['l3_with_surviving']} left a hypothesis standing, {v['l3_not_separable']} not "
        "separable",
        loc="left",
    )
    handles = [
        Patch(facecolor=c_ref, hatch=h_ref, edgecolor=p["surface"], label="refuted by the probe"),
        Patch(facecolor=c_sur, hatch=h_sur, edgecolor=p["surface"],
              label="survived the probe -- what `confirmed: 0` hides"),
    ] + theme.absence_handles(theme_name)[:1]
    ax.legend(handles=handles, loc="lower left", fontsize=theme.BASE_FONT_SIZE - 3, ncols=3)
    ax.text(
        0.03, -0.78,
        f"probe_report's `confirmed: {v['l3_confirmed_field']}` is a coding artefact, not a "
        "finding: a probe is coded `refuted` if it refutes anything, and all four did. "
        "P-02.1/2/3 confirm `ring_is_solid`.",
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3.4, color=muted,
    )


def _certify_panel(ax, v: dict, p: dict, theme_name: str) -> None:
    """Panel C: the same cheap certifier, three evidence sets, two verdicts."""
    ink2, muted = p["ink_secondary"], p["muted"]
    good, bad = theme.STATUS["good"], theme.STATUS["critical"]

    rows = [
        (
            "M5 holed manual\nvs the play record",
            v["m5_replay_frames"], True,
            [
                f"{v['m5_replay_transitions']} transitions | {v['m5_replay_pixels']} pixels "
                f"checked, {v['m5_replay_unexplained']} unexplained | "
                f"{v['m5_replay_anomaly_kinds']} anomaly kinds",
            ],
        ),
        (
            "M5 holed manual\nvs the full sweep",
            v["m5_sweep_frames"], False,
            [
                f"{v['m5_sweep_anomalies']} anomalies in {v['m5_sweep_anomaly_kinds']} kinds -- "
                "a CAP, not a count: the cheap layer caps its anomaly list",
                f"{v['m5_sweep_pixels']} pixels checked, {v['m5_sweep_unexplained']} unexplained "
                "-- from A2_REPORT.md PROSE; this artefact carries no pixel key",
                f"first at t={v['m5_sweep_first_t']}, cell "
                f"({v['m5_sweep_first_cell'][0]},{v['m5_sweep_first_cell'][1]}), "
                f"{v['m5_sweep_first_kind']}",
            ],
        ),
        (
            "L5 repaired manual\nvs the probed trace",
            v["l5_cheap_frames"], True,
            [
                f"{v['l5_cheap_transitions']} transitions | {v['l5_cheap_pixels']} pixels checked "
                "(no `pixels_unexplained` key emitted) | "
                f"{v['l5_cheap_anomaly_kinds']} anomaly kinds",
            ],
        ),
    ]
    for i, (label, frames, green, detail) in enumerate(rows):
        ax.barh(i - 0.16, frames, height=0.40, color=good if green else bad,
                edgecolor=p["surface"], linewidth=0.6, zorder=2)
        ax.text(frames + 4.0, i - 0.16, "GREEN" if green else "RED", ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 2, color=good if green else bad)
        for j, line in enumerate(detail):
            ax.text(3.0, i + 0.22 + j * 0.18, line, ha="left", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 3.4, color=ink2)

    ax.set_ylim(len(rows) - 0.30, -0.66)
    ax.set_xlim(0.0, 300.0)
    ax.set_xticks([0, 50, 100, 150, 200, 250])
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([r[0] for r in rows], fontsize=theme.BASE_FONT_SIZE - 2)
    ax.grid(False)
    ax.set_xlabel("frames checked")
    ax.set_title("C. one certifier, three evidence sets", loc="left")
    ax.text(
        3.0, -0.53,
        "the middle row is the whole exhibit: same manual, wider evidence, opposite verdict.",
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3.4, color=muted,
    )


def _battery_panel(ax, card: str, spectrum_rows: list[dict], p: dict, theme_name: str,
                   title: str, xlabel: str, xmax: float, reference: float | None) -> None:
    """Panels D/E: K12 and K13 over the theory-bearing arms, absence kept absent."""
    ink2, muted = p["ink_secondary"], p["muted"]
    colour = theme.series_colour(theme_name, 0 if card == "K12" else 1)
    marker_of = {"patch": theme.series_marker(0), "rebuild": theme.series_marker(1)}

    # Blank lane at the top for the reference annotation, one at the bottom for
    # the legend: neither may sit on a row.
    ax.set_ylim(len(spectrum_rows) + 0.55, -1.0)
    ax.set_xlim(0.0, xmax)
    ax.grid(False)
    ax.set_yticks(list(range(len(spectrum_rows))))
    ax.set_yticklabels([r["run"] for r in spectrum_rows], fontsize=theme.BASE_FONT_SIZE - 2)
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)

    if reference is not None:
        ax.axvline(reference, color=muted, linewidth=0.9, linestyle=(0, (5, 2, 1, 2)), zorder=1)
        ax.text(reference - 0.02, -0.72,
                "1.000 = the repair cost what the theory itself cost",
                ha="right", va="center", fontsize=theme.BASE_FONT_SIZE - 3.4, color=muted)

    for i, row in enumerate(spectrum_rows):
        entry = row[card]
        if entry["status"] != "ok":
            ax.add_patch(
                Rectangle(
                    (0.0, i - 0.3), xmax, 0.6,
                    facecolor=theme.ABSENCE["not-applicable"]["facecolor"],
                    edgecolor=ink2, hatch=theme.ABSENCE["not-applicable"]["hatch"],
                    linewidth=0.8, zorder=2,
                )
            )
            # The label sits on its own hatch, so it carries a surface-coloured
            # plate; the hatch still reads on either side of it.
            ax.text(0.02, i, "not applicable (structural): no repair episode in this arm",
                    ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3.4, color=ink2,
                    zorder=3,
                    bbox={"facecolor": p["surface"], "edgecolor": "none", "pad": 1.2})
            continue
        value = float(entry["value"])
        support = entry["support"] or {}
        strategy = support.get("strategy")
        ax.barh(i, value, height=0.6, color=colour, edgecolor=p["surface"],
                linewidth=0.6, zorder=2)
        if value == 0.0:
            # A measured zero is not an absence: mark it so the empty bar reads.
            ax.plot([0.0], [i], marker="|", markersize=9.0, markeredgewidth=1.8,
                    color=colour, zorder=3)
        if strategy in marker_of:
            ax.plot([value], [i], marker=marker_of[strategy], markersize=5.0,
                    color=colour, zorder=3, linestyle="none")
        if card == "K12":
            detail = (
                f"{theme.fmt_num(value)}  =  {support.get('closed')}/{support.get('required')} "
                f"beats over {support.get('episodes')} episode(s)"
                + ("  -- a MEASURED zero, not an absence" if value == 0.0 else "")
            )
        else:
            detail = (
                f"{theme.fmt_num(value)}  ({strategy}, {support.get('episodes')} episode(s))"
            )
        ax.text(value + xmax * 0.014, i, detail, ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3.4, color=ink2)


def _render(v: dict, probe_rows: list[dict], spectrum_rows: list[dict], names: dict[str, str],
            theme_name: str) -> list[str]:
    p = theme.apply_theme(theme_name)

    fig = plt.figure(figsize=(13.0, 13.0))
    # The last row draws nothing: it reserves the strip the caveat is written
    # into, so the caveat can never land on panel D/E's axis labels.
    gs = fig.add_gridspec(4, 2, height_ratios=[1.62, 0.92, 0.86, 0.32],
                          width_ratios=[1.0, 1.0])
    ax_flow = fig.add_subplot(gs[0, :])
    ax_probes = fig.add_subplot(gs[1, 0])
    ax_certify = fig.add_subplot(gs[1, 1])
    ax_k12 = fig.add_subplot(gs[2, 0])
    ax_k13 = fig.add_subplot(gs[2, 1])
    ax_pad = fig.add_subplot(gs[3, :])
    ax_pad.axis("off")
    ax_pad.grid(False)

    _flow(ax_flow, v, names, p, theme_name)
    ax_flow.set_title(
        "A. the six-beat repair loop L1-L6, and the two prelude beats that hand it a "
        "theorem that is proved, green, and false",
        loc="left",
    )
    _probes_panel(ax_probes, v, probe_rows, p, theme_name)
    _certify_panel(ax_certify, v, p, theme_name)
    _battery_panel(
        ax_k12, "K12", spectrum_rows, p, theme_name,
        "D. K12 -- repair beats closed (higher is better)",
        "share of the six beats", 1.62, None,
    )
    _battery_panel(
        ax_k13, "K13", spectrum_rows, p, theme_name,
        "E. K13 -- repair cost (LOWER is better)",
        "repair actions / actions the theory cost", 1.78, 1.0,
    )
    ax_k13.legend(
        handles=[
            Line2D([], [], color=p["ink_secondary"], marker=theme.series_marker(0),
                   linestyle="none", markersize=5.0, label="strategy: patch"),
            Line2D([], [], color=p["ink_secondary"], marker=theme.series_marker(1),
                   linestyle="none", markersize=5.0, label="strategy: rebuild"),
        ] + theme.absence_handles(theme_name)[:1],
        loc="lower right", fontsize=theme.BASE_FONT_SIZE - 3, ncols=3,
    )

    fig.suptitle(
        "Figure 5 -- the DC22 case in cold-start-a2: a machine-checked theorem that is false of "
        "the world, and the six beats that repaired it"
    )
    theme.caveat(
        fig,
        "Read the beat count carefully: loop_ledger.json records EIGHT beats and summarises "
        f"{v['ledger_pass']}/{v['ledger_total']} pass; the repair loop is the SIX L-beats, and "
        "M0/M5 are prelude, drawn subordinate above. Panel B: `probe_report.confirmed` is 0 only "
        "because a probe that refutes anything is coded `refuted` -- all four executable probes "
        "left a hypothesis standing, so `4 refuted / 0 confirmed` would misread the file; P-03 is "
        "hatched because probes.jsonl carries no outcome fields for it at all, not because it "
        f"scored nothing. Panel C: the full-sweep row's {v['m5_sweep_anomalies']} is a CAP -- the "
        "cheap layer caps its anomaly LIST -- and that is unchanged by the pixel figures beside "
        f"it, which count something else and come from A2_REPORT.md PROSE ({v['m5_sweep_pixels']} "
        f"= {v['m5_sweep_frames']} frames x {v['m5_pixels_per_frame']} px, cross-checked; no "
        "artefact carries a pixel key for the sweep). M5's plan is UNSAT and therefore has no "
        "length and no backend -- structurally absent, never 0. L4's own ledger metric is a "
        "boolean with no count-shaped metric behind it, and none is invented: the rule counts on "
        "that node are corroboration from a different artefact, labelled as such. Panels D/E: "
        "five of the seven "
        "theory-bearing arms are `not-applicable` by the battery's own reason (no repair "
        "episode) and are hatched; a0-spike's K12 = 0.000 is a MEASURED zero (0 of 24 beats over "
        "4 rebuild episodes) and is labelled as one. Arm and world are perfectly confounded here: "
        "a2 and a0-spike are different self-built worlds, so K13's 0.262-vs-1.095 contrast is a "
        "strategy contrast inside that confound, not a controlled one.",
        theme=theme_name,
    )
    return theme.save(fig, NAME, theme_name)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    v, metrics, notes = extract()

    raw = _load()
    beats = _beats_by_id(raw["ledger"])
    names = {b: _english(beats[b]["name"]) for b in BEAT_ORDER}
    probe_rows = _probe_rows(raw["probes"])
    spectrum_rows = _spectrum_rows(raw["spectrum"])

    rows = csv_rows(metrics)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(v, probe_rows, spectrum_rows, names, theme_name))

    kinds: dict[str, int] = {}
    for m in metrics:
        kinds[m["value_kind"]] = kinds.get(m["value_kind"], 0) + 1
    notes.append(
        f"{len(rows)} CSV rows over {len(BEAT_ORDER)} ledger beats + 2 battery cards; "
        "value_kind census: "
        + ", ".join(f"{k} {kinds[k]}" for k in sorted(kinds))
        + ". Every number on the plate has a row here with its source and JSON path."
    )
    notes.append(
        "figure text is English only: the bilingual ledger names are preserved verbatim in the "
        "CSV's name_bilingual column, and the English half is split off programmatically (on "
        "U+00B7) for the plate, because DejaVu Sans has no CJK coverage and a substituted system "
        "font would make the SVG path data machine-dependent."
    )
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
