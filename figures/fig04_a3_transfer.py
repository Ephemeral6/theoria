"""fig04_a3_transfer -- 图4 A3 migration: carrying the book vs starting again.

Theoria.md 3.2's transfer figure, serving claim C3: *a domain written once is
worth carrying*. The measured object is a **bill** -- frames, actions, engine
stages, candidates, rounds, clauses -- and the comparison is deliberately
narrow: ``l2_from_scratch`` vs ``l2_transfer``, the **same level** with and
without the two books. ``l1_cold_start`` is a different level and is therefore
in the CSV and on panel C's level-labelled row, but nowhere in a ratio: the
source's own ``note`` warns that ratios against l1 compare across levels.

What this script does, in order:

1. reads the seven declared A3 artefacts through ``sources`` (never a raw path,
   so every input lands in ``figures/SOURCES.sha256``);
2. **cross-checks the bill four ways** before drawing anything -- the two
   per-arm event ledgers' ``counts`` against ``bill_table``'s like-for-like
   block, their ``cost_to_first_plan`` blocks against ``bill_table``'s, each
   ledger's per-line event amounts against its own counts, and the
   precomputed ``ratio``/``saved`` against the two values they claim to
   summarise. Disagreements are reported in ``notes``, never reconciled;
3. writes ``csv/fig04_a3_transfer.csv`` (the audit surface). Every number on
   the plate is a row there, carrying its ``source_key``, its ``value_state``
   and its own caveat in ``note``;
4. renders one figure per theme, two themes x svg+png = 4 images.

**The axis problem, and how it is solved.** The nine meter lines span 347 down
to 0, and three of them are 1:1 / 3:3 / 1:1. On one linear axis the flat rows
collapse onto the origin and disappear; on a log axis the genuine zeros cannot
be drawn at all. Panel A therefore uses a **symlog** x-axis with
``linthresh=1``: exactly zero and one are separated in the linear region near
the origin, and 11 vs 347 still reads as the ratio it is. The flatness of the
bottom three rows is the honest half of this result -- A3_REPORT.md says a
table showing savings there "would be measuring something other than transfer"
-- so they are drawn, banded, and labelled as saving nothing.

**Zero is not absence, and this plate distinguishes them.** The transfer arm
genuinely adjudicated zero candidates and wrote zero clauses: those are real
zeros, drawn at 0 on the axis and marked ``real-zero`` in the CSV. Two values
are structurally absent and are drawn with ``theme.ABSENCE`` encodings
instead: ``provenance.also_derivable.goal_cell``/``landmarks`` are
*not-applicable* (the goal is not rendered and a portal exit is plain floor --
they are not in the pixels, so "0 derived" would be a category error), and the
controls' ``first_mismatch: null`` is *insufficient-data* (a mismatch did
occur; its index was simply never recorded).

Six things are **drawn**, not captioned, because they must not travel
separately from the numbers: n = 1 per arm with no variance anywhere; the
three flat lines; the theorize rounds that were toolchain conformance rather
than world-facing work; the broken blind and the fact that the carrier wrote
the books; levels-not-games; and the bill being structural rather than
economic. ``theme.caveat`` puts them on the figure's face.

**Those caveats are guarded, not asserted.** Four of them come from prose that
no JSON carries, so ``A3_REPORT.md`` is a declared source and is read rather
than merely hashed -- a hash tells the next author the report moved, but would
not stop this module drawing a number the report no longer supports. See
``_report_claims``: the toolchain-tax round count is **parsed** out of the
report and drawn, with no fallback; three sentences that state numbers the
artefacts also hold are parsed and **compared** to them; and nine sentences are
**anchored** by presence, each failing the build by the name of the caveat it
licenses. Two claims stay module-local, for stated reasons: ``n = 1 per arm``
has no sentence to anchor to, so it is checked structurally instead (each arm
appears exactly once in ``bill_table.arms``); and panel E's two decision IDs
are checked against ``provenance_l2_transfer.json``'s own note fields, which
are already hashed, rather than by declaring ``DECISIONS.md`` as a source.

Not drawn, deliberately: any shortest-path length for ``l2-rewired``.
A3_REPORT.md says 15, DECISIONS.md D-A3-010 says 14, and neither number is in
any artefact this figure is allowed to read -- so it is reported in ``notes``
as unsourceable rather than picked.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from matplotlib.ticker import FixedLocator, NullLocator  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig04_a3_transfer"

#: The two arms of the like-for-like comparison, in drawing order. Series slot
#: 0 is the control, slot 1 is the treatment, everywhere on the plate.
CONTROL_ARM = "l2_from_scratch"
TRANSFER_ARM = "l2_transfer"
BASELINE_ARM = "l1_cold_start"  # a different level; in the CSV, not in a ratio

#: Meter lines in drawing order: the six that save something first, the three
#: that save nothing after. Declared rather than sorted-by-magnitude so the
#: order cannot drift when a number does; ``_check_lines`` asserts this tuple
#: is exactly the set the artefact carries.
SAVING_LINES: tuple[str, ...] = (
    "world_frames",
    "world_actions",
    "candidates_adjudicated",
    "dsl_clauses_written",
    "theorize_rounds",
    "engine_stages",
)
FLAT_LINES: tuple[str, ...] = ("compile_runs", "certify_runs", "plan_runs")
LINE_ORDER: tuple[str, ...] = SAVING_LINES + FLAT_LINES

#: The two lines A3_REPORT.md snapshots "the instant a plan first existed".
FIRST_PLAN_LINES: tuple[str, ...] = ("world_frames", "world_actions")

#: The accuracy rows, keyed by the one field that is unique across them. Order
#: is declared: level 1 first (a different level, banded off), then the two
#: level-2 manuals with the control before the carried one.
ACCURACY_ORDER: tuple[str, ...] = (
    "theory/generated_l1/theory.py",
    "theory/generated_l2_scratch/theory.py",
    "theory/generated_l2/theory.py",
)
ACCURACY_LABEL = {
    "theory/generated_l1/theory.py": "a3-l1  manual, on the level it was induced from",
    "theory/generated_l2_scratch/theory.py": "a3-l2  control manual, induced from level 2's own sweep",
    "theory/generated_l2/theory.py": "a3-l2  CARRIED manual, on a level it never explored",
}

#: The meter line the toolchain tax is charged to. How much of it was tax is
#: read out of the report, not asserted here -- see ``_report_claims``.
TOOLCHAIN_TAX_LINE = "theorize_rounds"

#: Tolerance for the ratio arithmetic cross-check. The artefact carries full
#: float repr; recomputing divides in a different order.
RATIO_TOLERANCE = 1e-12

CSV_HEADER = (
    "section",
    "line",
    "l1_cold_start",
    "l2_from_scratch",
    "l2_transfer",
    "ratio_transfer_over_from_scratch",
    "saved",
    "panel",
    "value_state",
    "source_key",
    "note",
)

#: Carried verbatim onto every row whose l1 column is populated.
CROSS_LEVEL_NOTE = (
    "l1_cold_start is a DIFFERENT LEVEL; bill_table.note: ratios against it "
    "compare across levels. No ratio here is taken against it."
)


# --------------------------------------------------------------------------
# the report: one claim parsed, the rest anchored
# --------------------------------------------------------------------------
#
# ``a3_report`` is declared so that A3_REPORT.md is hashed into
# ``figures/SOURCES.sha256``. A hash alone only tells the *next* author that the
# prose moved; it does not stop this module from drawing a number the prose no
# longer supports. So the report is read, and it guards three different things:
#
# 1. **Parsed.** The toolchain-tax round count is taken from the report's own
#    sentence and drawn. There is no fallback: if the sentence stops matching,
#    the build fails. A figure that quietly reverts to a hard-coded 2 is worse
#    than one that never opened the file.
# 2. **Parsed and cross-checked against the artefacts.** Three sentences state
#    numbers that also live in JSON. Those are parsed and compared, so the prose
#    and the meters cannot drift apart in silence.
# 3. **Anchored.** Every remaining caveat on the plate's face is tied to the
#    sentence that licenses it. The sentence's presence is required; its absence
#    raises, naming the caveat that just lost its source.
#
# Regexes run over whitespace-normalised text, because every one of these
# sentences is wrapped across two lines in the file. The two non-ASCII
# characters the report uses inside them (U+2014 em dash, U+2192 rightwards
# arrow) are written literally rather than as ``\uXXXX`` escapes: the pattern
# then matches the report's own bytes with nothing in between to mistype, and
# both this module and ``sources.read_text`` are UTF-8. Neither character is
# ever drawn -- figure text stays ASCII, per PLAN.md section 0.

_WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

#: The one report claim this figure *draws*. Captures the tax, the total it is
#: a fraction of, and the percentage the report itself computes.
_TOOLCHAIN_TAX_RE = (
    r"\*\*(?P<tax>\w+) of its (?P<total>\w+) theorize rounds — "
    r"(?P<pct>\d+) ?% of its adjudication budget — went to toolchain "
    r"conformance rather than to the world\.\*\*"
)

#: Sentences that state a number the artefacts also carry. Parsed, then
#: compared -- ``_report_claims`` owns the comparison.
_HEADLINE_RE = (
    r"The (?P<a>\d+) → (?P<b>\d+) ratio is the headline, and the "
    r"(?P<c>\d+) → (?P<d>\d+) is the one that matters\."
)
_PROVENANCE_SPLIT_RE = r"\*\*(?P<derived>\d+) derived from the frame, (?P<supplied>\d+) supplied\*\*"

#: The number this figure refuses to draw. The report's control table says
#: l2-rewired is solvable in n; DECISIONS.md D-A3-010 says one less, and no
#: artefact carries either. Parsing it does not put it on the plate -- it keeps
#: the refusal honest, so the note names the report's live value rather than one
#: read once by hand and left to rot.
_REWIRED_LENGTH_RE = r"\| the world \| \*\*unsolvable\*\* \| solvable in (?P<length>\d+) \|"

#: caveat clause -> the sentence in the report that licenses it. Presence is
#: required; the key is what gets named when it goes missing.
_CAVEAT_ANCHORS: tuple[tuple[str, str], ...] = (
    (
        "who-carried-the-books",
        r"the person who carried the books to level 2 is the person who wrote them "
        r"for level 1, and they already knew the answer",
    ),
    (
        "blind-partially-broken",
        r"The blind was partially broken, by us, and it is recorded as an incident",
    ),
    ("incident-A3-I1", r"\*\*Incident A3-I1\*\* has the full account"),
    (
        "no-naming-agreement",
        r"\*\*No agreement on names is claimed\*\*, and none is used as evidence",
    ),
    (
        "levels-not-games",
        r"A3 says nothing about carrying a domain between games with different mechanics",
    ),
    ("bill-structural-not-economic", r"\*\*The bill is structural, not economic\.\*\*"),
    (
        "model-calls-not-measured",
        r"does \*\*not\*\* measure what the theorize step cost in model calls, which is "
        r"the single largest term in a real C3 bill",
    ),
    (
        "zeros-real-not-dollars",
        r"are real and they are the right shape, but converting them to dollars is not "
        r"something this experiment did",
    ),
    (
        "flat-lines-would-mislead",
        r"a table that showed savings there would be measuring something other than transfer",
    ),
)


def _normalise(text: str) -> str:
    """Collapse every whitespace run to one space. Every anchored sentence in
    A3_REPORT.md is wrapped across lines, so matching the raw text would be
    matching this checkout's line breaks rather than the claim."""
    return " ".join(text.split())


def _require(text: str, key: str, pattern: str):
    import re

    match = re.search(pattern, text)
    if match is None:
        raise ValueError(
            f"A3_REPORT.md no longer contains the sentence anchoring {key!r}. The plate "
            "draws a caveat that this sentence is the source of, so the figure stops "
            "rather than keep asserting it. Re-read the report, then update the anchor "
            "and the caveat together."
        )
    return match


def _word_int(word: str, key: str) -> int:
    if word.isdigit():
        return int(word)
    try:
        return _WORD_NUMBERS[word.lower()]
    except KeyError:
        raise ValueError(
            f"A3_REPORT.md states {key} as {word!r}, which is not a number this module "
            "can read. No default is substituted."
        ) from None


def _report_claims(like: dict, first_plan: dict, prov_counts: tuple[int, int]) -> tuple[dict, list[str]]:
    """Read A3_REPORT.md and return the claims it licenses, plus notes."""
    text = _normalise(sources.read_text("a3_report"))
    notes: list[str] = []

    # --- 1. parsed and drawn -------------------------------------------------
    m = _require(text, "toolchain-tax", _TOOLCHAIN_TAX_RE)
    tax = _word_int(m.group("tax"), "the toolchain-tax round count")
    total = _word_int(m.group("total"), "the control arm's theorize-round total")
    pct = int(m.group("pct"))
    control_rounds = int(like[TOOLCHAIN_TAX_LINE][CONTROL_ARM])
    if total != control_rounds:
        raise ValueError(
            f"A3_REPORT.md says the control arm ran {total} theorize rounds; "
            f"bill_table says {control_rounds}. The prose and the meter disagree, so the "
            "mark on the theorize_rounds bar has no defensible size."
        )
    if not 0 <= tax <= total:
        raise ValueError(f"toolchain tax {tax} is not a part of {total} rounds")
    if pct != round(100 * tax / total):
        raise ValueError(
            f"A3_REPORT.md computes the tax as {pct}% of {total} rounds; {tax}/{total} is "
            f"{round(100 * tax / total)}%."
        )
    notes.append(
        f"A3_REPORT.md parsed: {tax} of the control arm's {total} theorize rounds ({pct}%) "
        "were toolchain conformance. Drawn on panel A; not hard-coded, and no fallback -- "
        "if that sentence stops matching, the build fails."
    )

    # --- 2. parsed and cross-checked against the artefacts -------------------
    m = _require(text, "headline-ratio", _HEADLINE_RE)
    a, b, c, d = (int(m.group(g)) for g in ("a", "b", "c", "d"))
    expected = (
        int(like["world_frames"][CONTROL_ARM]),
        int(like["world_actions"][TRANSFER_ARM]),
        int(first_plan[BASELINE_ARM]["world_actions"]),
        int(first_plan[TRANSFER_ARM]["world_actions"]),
    )
    if (a, b, c, d) != expected:
        raise ValueError(
            f"A3_REPORT.md's headline sentence states {(a, b, c, d)}; the artefacts give "
            f"{expected} for the four values it names."
        )
    notes.append(
        f"A3_REPORT.md's headline sentence anchored, and it is looser than the plate: "
        f"'{a} -> {b}' crosses two meter lines ({a} is world_frames from-scratch, {b} is "
        f"world_actions transfer), and '{c} -> {d}' is CROSS-LEVEL (cost-to-first-plan "
        "world_actions, l1_cold_start -> transfer). The figure draws neither pairing: panel A "
        f"draws {a} -> {int(like['world_frames'][TRANSFER_ARM])} and "
        f"{int(like['world_actions'][CONTROL_ARM])} -> {b} like-for-like, panel B draws "
        f"{int(first_plan[CONTROL_ARM]['world_actions'])} -> {d} within level 2."
    )

    m = _require(text, "provenance-split", _PROVENANCE_SPLIT_RE)
    split = (int(m.group("derived")), int(m.group("supplied")))
    if split != prov_counts:
        raise ValueError(
            f"A3_REPORT.md states a {split[0]} derived / {split[1]} supplied split; "
            f"provenance_l2_transfer.json's fields give {prov_counts[0]} / {prov_counts[1]}."
        )
    notes.append(
        f"A3_REPORT.md's '{split[0]} derived from the frame, {split[1]} supplied' agrees with "
        "provenance_l2_transfer.json field by field (panel E)."
    )

    m = _require(text, "rewired-plan-length", _REWIRED_LENGTH_RE)
    rewired_length = int(m.group("length"))

    # --- 3. anchored ---------------------------------------------------------
    for key, pattern in _CAVEAT_ANCHORS:
        _require(text, key, pattern)
    notes.append(
        f"{len(_CAVEAT_ANCHORS)} caveat anchors checked in A3_REPORT.md and all present: "
        + ", ".join(sorted(key for key, _ in _CAVEAT_ANCHORS))
        + ". Each is the sentence a clause of the drawn caveat comes from; a missing one "
        "fails the build by name rather than letting the clause go stale."
    )
    return {"rounds": tax, "total": total, "pct": pct, "rewired_length": rewired_length}, notes


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def _check_lines(observed: set[str], origin: str) -> None:
    """The declared row order must be exactly the artefact's line set.

    A line appearing or vanishing under the figure is a change in what is
    being measured, and it should stop the build rather than silently drop a
    row off the bottom of the plate.
    """
    declared = set(LINE_ORDER)
    if observed != declared:
        raise ValueError(
            f"{origin}: meter lines {sorted(observed)} do not match the declared "
            f"order {sorted(declared)}; missing={sorted(declared - observed)}, "
            f"unexpected={sorted(observed - declared)}"
        )


def _events_by_line(bill: dict, origin: str) -> dict[str, int]:
    """Sum each line's event amounts, and check the running totals agree.

    The ledger carries both a per-event ``amount`` and a per-line
    ``running_total``; they are two statements of the same thing, so a
    disagreement means the ledger is internally inconsistent.
    """
    running: dict[str, int] = {}
    summed: dict[str, int] = {}
    for event in sorted(bill["events"], key=lambda e: int(e["seq"])):
        line = event["line"]
        summed[line] = summed.get(line, 0) + int(event["amount"])
        running[line] = int(event["running_total"])
        if running[line] != summed[line]:
            raise ValueError(
                f"{origin}: at seq {event['seq']} line {line!r} the running_total "
                f"{running[line]} disagrees with the summed amounts {summed[line]}"
            )
    return summed


def extract() -> tuple[dict, list[str]]:
    """Everything the plate draws, plus notes. No plotting, no writing."""
    notes: list[str] = []

    bill_table = sources.read_json("a3_bill_table")
    score = sources.read_json("a3_score_vs_truth")
    bill_transfer = sources.read_json("a3_bill_l2_transfer")
    bill_scratch = sources.read_json("a3_bill_l2_scratch")
    provenance = sources.read_json("a3_provenance_transfer")
    controls = sources.read_json("a3_negative_controls")

    like = bill_table["like_for_like_level_2"]
    _check_lines(set(like), "bill_table.like_for_like_level_2")

    # --- l1's column, from the cross-level table. Read for the CSV only. ----
    baseline = {row["line"]: int(row[BASELINE_ARM]) for row in bill_table["table"]}
    _check_lines(set(baseline), "bill_table.table")

    # --- cross-check 1: the table block against the like-for-like block ----
    table_l2 = {
        row["line"]: (int(row[CONTROL_ARM]), int(row[TRANSFER_ARM]))
        for row in bill_table["table"]
    }
    disagree = [
        line
        for line in LINE_ORDER
        if table_l2[line] != (int(like[line][CONTROL_ARM]), int(like[line][TRANSFER_ARM]))
    ]
    notes.append(
        "cross-check 1/4 bill_table.table vs bill_table.like_for_like_level_2: "
        + ("agree on all 9 lines." if not disagree else f"DISAGREE on {sorted(disagree)} (not reconciled).")
    )

    # --- cross-check 2: each arm's own event ledger against the table ------
    ledger_of = {CONTROL_ARM: bill_scratch, TRANSFER_ARM: bill_transfer}
    counts_bad: list[str] = []
    for arm in (CONTROL_ARM, TRANSFER_ARM):
        ledger = ledger_of[arm]
        if ledger["arm"] != arm:
            raise ValueError(f"ledger for {arm} declares arm={ledger['arm']!r}")
        _check_lines(set(ledger["counts"]), f"{arm}.counts")
        for line in LINE_ORDER:
            if int(ledger["counts"][line]) != int(like[line][arm]):
                counts_bad.append(f"{arm}.{line}")
    notes.append(
        "cross-check 2/4 per-arm ledger counts vs the like-for-like block: "
        + ("agree on all 18 cells." if not counts_bad else f"DISAGREE on {sorted(counts_bad)}.")
    )

    # --- cross-check 3: event amounts against the same ledger's counts -----
    events_bad: list[str] = []
    event_counts = {}
    for arm in (CONTROL_ARM, TRANSFER_ARM):
        ledger = ledger_of[arm]
        summed = _events_by_line(ledger, arm)
        event_counts[arm] = len(ledger["events"])
        for line in LINE_ORDER:
            # A line with no event must be 0: the arm did none of it. That is a
            # real zero, and it is the only reading of an absent event here.
            if summed.get(line, 0) != int(ledger["counts"][line]):
                events_bad.append(f"{arm}.{line}")
    notes.append(
        f"cross-check 3/4 event amounts vs counts ({event_counts[CONTROL_ARM]} billed events "
        f"for the control, {event_counts[TRANSFER_ARM]} for the transfer arm): "
        + ("agree on all 18 cells." if not events_bad else f"DISAGREE on {sorted(events_bad)}.")
    )

    # --- cross-check 4: the precomputed ratio and saved ---------------------
    arith_bad: list[str] = []
    for line in LINE_ORDER:
        cell = like[line]
        scratch, transfer = int(cell[CONTROL_ARM]), int(cell[TRANSFER_ARM])
        if int(cell["saved"]) != scratch - transfer:
            arith_bad.append(f"{line}.saved")
        if scratch and abs(float(cell["ratio"]) - transfer / scratch) > RATIO_TOLERANCE:
            arith_bad.append(f"{line}.ratio")
    notes.append(
        "cross-check 4/4 precomputed ratio/saved against the two values they summarise: "
        + ("agree on all 9 lines." if not arith_bad else f"DISAGREE on {sorted(arith_bad)}.")
    )

    # --- the like-for-like rows -------------------------------------------
    meter_rows = []
    for line in LINE_ORDER:
        cell = like[line]
        scratch, transfer = int(cell[CONTROL_ARM]), int(cell[TRANSFER_ARM])
        meter_rows.append(
            {
                "line": line,
                "l1": baseline[line],
                "scratch": scratch,
                "transfer": transfer,
                "ratio": float(cell["ratio"]),
                "saved": int(cell["saved"]),
                "flat": line in FLAT_LINES,
                # A 0 here is the arm having done none of this, not a gap in the
                # record. The distinction is the CSV's value_state column.
                "value_state": "real-zero" if transfer == 0 else "value",
            }
        )

    # --- cost to first plan: the snapshot that A3 calls the one that matters
    first_plan_src = bill_table["cost_to_first_plan"]
    fp_bad: list[str] = []
    for arm in (CONTROL_ARM, TRANSFER_ARM):
        for line in LINE_ORDER:
            if int(ledger_of[arm]["cost_to_first_plan"][line]) != int(first_plan_src[arm][line]):
                fp_bad.append(f"{arm}.{line}")
    if fp_bad:
        notes.append(f"cost_to_first_plan DISAGREES between ledger and bill_table on {sorted(fp_bad)}.")
    else:
        notes.append(
            "cost_to_first_plan agrees between each arm's ledger and bill_table on all 18 cells."
        )

    first_plan_rows = []
    for line in LINE_ORDER:
        scratch = int(first_plan_src[CONTROL_ARM][line])
        transfer = int(first_plan_src[TRANSFER_ARM][line])
        first_plan_rows.append(
            {
                "line": line,
                "l1": int(first_plan_src[BASELINE_ARM][line]),
                "scratch": scratch,
                "transfer": transfer,
                # Derived here, not in the artefact: the source publishes this
                # block as three raw columns with no ratio.
                "ratio": (transfer / scratch) if scratch else None,
                "saved": scratch - transfer,
                "value_state": "real-zero" if transfer == 0 else "value",
            }
        )

    # --- accuracy ----------------------------------------------------------
    by_theory = {}
    for row in score["results"]:
        key = row["theory"]
        if key in by_theory:
            raise ValueError(f"score_vs_truth: two results for {key!r}")
        by_theory[key] = row
    if set(by_theory) != set(ACCURACY_ORDER):
        raise ValueError(
            f"score_vs_truth results {sorted(by_theory)} do not match the declared "
            f"order {sorted(ACCURACY_ORDER)}"
        )
    accuracy_rows = []
    for key in ACCURACY_ORDER:
        row = by_theory[key]
        accuracy_rows.append(
            {
                "theory": key,
                "label": ACCURACY_LABEL[key],
                "level": row["level"],
                "accuracy": float(row["accuracy"]),
                "pairs_checked": int(row["pairs_checked"]),
                "pairs_correct": int(row["pairs_correct"]),
                "n_mismatches": len(row["mismatches"]),
                "note": row["note"],
            }
        )

    # --- negative controls -------------------------------------------------
    control_rows = []
    for row in sorted(controls["controls"], key=lambda r: r["arm"]):
        control_rows.append(
            {
                "arm": row["arm"],
                "level": row["level"],
                "edit": row["edit"],
                "static_green": bool(row["static_certify_green"]),
                "replay_green": bool(row["replay_certify_green"]),
                "caught": bool(row["caught"]),
                "claimed_a_win": bool(row["claimed_a_win"]),
                "world_is_solvable": bool(row["world_is_solvable"]),
                # null. A mismatch did occur -- the index was never recorded.
                # Absent, never 0, and never "no mismatch".
                "first_mismatch": row["first_mismatch"],
                "anomaly_kinds": sorted(row["anomaly_kinds"]),
            }
        )
    if any(r["first_mismatch"] is not None for r in control_rows):
        raise ValueError("first_mismatch is populated; the absence encoding no longer applies")

    # --- provenance --------------------------------------------------------
    fields = provenance["fields"]
    derived = sorted(k for k in fields if fields[k] == "derived_from_frame")
    supplied = sorted(k for k in fields if fields[k] == "supplied")
    other = sorted(k for k in fields if fields[k] not in ("derived_from_frame", "supplied"))
    if other:
        raise ValueError(f"provenance.fields carries unknown provenance values for {other}")
    if len(derived) != int(provenance["derived_fields"]) or len(supplied) != int(
        provenance["supplied_fields"]
    ):
        notes.append(
            f"provenance DISAGREES with itself: fields{{}} gives {len(derived)} derived / "
            f"{len(supplied)} supplied, the counters say {provenance['derived_fields']} / "
            f"{provenance['supplied_fields']} (not reconciled)."
        )
    not_derivable = sorted(
        k for k in ("goal_cell", "landmarks") if not provenance["also_derivable"][k]
    )
    # Panel E names two decision IDs. DECISIONS.md is deliberately not a
    # declared source: the artefact echoes both IDs in its own note fields, and
    # those are hashed, so the label is anchored without a fifth A3 source.
    for field, decision in (("goal_cell", "D-A3-002"), ("landmarks", "D-A3-003")):
        note_text = provenance["also_derivable"].get(f"{field}_note", "")
        if decision not in note_text:
            raise ValueError(
                f"panel E labels {field} with {decision}, but "
                f"provenance_l2_transfer.json's {field}_note no longer cites it: {note_text!r}"
            )

    # n = 1 is drawn as a caveat, so it is checked rather than assumed: each arm
    # appears exactly once, and no artefact here carries a second run of one.
    arm_names = sorted(a["arm"] for a in bill_table["arms"])
    if len(arm_names) != len(set(arm_names)):
        raise ValueError(
            f"bill_table.arms lists an arm twice ({arm_names}); the plate's 'n = 1 run per "
            "arm, no variance' caveat would no longer be true."
        )

    toolchain_tax, report_notes = _report_claims(
        like, first_plan_src, (len(derived), len(supplied))
    )
    notes.extend(report_notes)

    notes.append(
        "n = 1 run per arm. There is no replication and no variance in any artefact this "
        "figure reads, so no error bar is drawn; the only genuine sample size on the plate "
        "is the accuracy row's n = "
        + "/".join(str(r["pairs_checked"]) for r in accuracy_rows)
        + " reachable (state, action) pairs."
    )
    notes.append(
        f"{len(FLAT_LINES)} of 9 meter lines save nothing at all "
        + ", ".join(
            f"{r['line']} {r['scratch']}:{r['transfer']}" for r in meter_rows if r["flat"]
        )
        + " -- drawn and banded, not dropped."
    )
    notes.append(
        "no shortest-path length is drawn for l2-rewired. A3_REPORT.md's control table says "
        f"solvable in {toolchain_tax['rewired_length']} (read here, not remembered); "
        "DECISIONS.md D-A3-010 says one less and is deliberately not a declared source, so "
        "this module can see only one side of that conflict. No artefact carries either "
        "number, so the figure states neither."
    )

    data = {
        "toolchain_tax": toolchain_tax,
        "meter_rows": meter_rows,
        "first_plan_rows": first_plan_rows,
        "accuracy_rows": accuracy_rows,
        "control_rows": control_rows,
        "provenance": {
            "derived": derived,
            "supplied": supplied,
            "not_derivable": not_derivable,
            "supplied_values": provenance["supplied_values"],
        },
        "controls_meta": {
            "all_caught": bool(controls["all_caught"]),
            "static_layer_caught_any": bool(controls["static_layer_caught_any"]),
            "none_claimed_a_win": bool(controls["none_claimed_a_win"]),
        },
        "bill_note": bill_table["note"],
        "score_reading": score["reading"],
        "event_counts": event_counts,
    }
    return data, notes


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def csv_rows(data: dict) -> list[list]:
    """Every number on the plate, in declared section then declared line order."""
    rows: list[list] = []

    for row in data["meter_rows"]:
        note = CROSS_LEVEL_NOTE
        if row["flat"]:
            note = (
                "NO SAVING AT ALL on this line; drawn because its flatness is part "
                "of the result. " + note
            )
        if row["line"] == TOOLCHAIN_TAX_LINE:
            tax = data["toolchain_tax"]
            note = (
                f"{tax['rounds']} of the control arm's {row['scratch']} rounds went to "
                f"toolchain conformance rather than to the world ({tax['pct']}% of its "
                f"adjudication budget, read from A3_REPORT.md), so 'saved' overstates "
                f"transfer by {tax['rounds']} rounds. " + note
            )
        rows.append(
            [
                "like_for_like_level_2",
                row["line"],
                row["l1"],
                row["scratch"],
                row["transfer"],
                theme.fmt_num(row["ratio"], places=6),
                row["saved"],
                "A",
                row["value_state"],
                "a3_bill_table",
                note,
            ]
        )

    for row in data["first_plan_rows"]:
        rows.append(
            [
                "cost_to_first_plan",
                row["line"],
                row["l1"],
                row["scratch"],
                row["transfer"],
                theme.fmt_num(row["ratio"], places=6),
                row["saved"],
                "B" if row["line"] in FIRST_PLAN_LINES else "",
                row["value_state"],
                "a3_bill_table",
                "snapshot at the instant a plan first existed. ratio and saved are DERIVED "
                "HERE (the source publishes this block as raw columns only). " + CROSS_LEVEL_NOTE,
            ]
        )

    for row in data["accuracy_rows"]:
        note = row["note"]
        if row["theory"].endswith("generated_l2/theory.py"):
            note += (
                "; the level was never explored, so this is the accuracy of TRANSFER "
                "rather than of induction"
            )
        # The three manuals do not line up with the three bill arms, so the arm
        # columns carry the value only for the arm each manual belongs to.
        cols = {"l1": None, "scratch": None, "transfer": None}
        which = (
            "l1"
            if row["theory"].endswith("generated_l1/theory.py")
            else "scratch"
            if row["theory"].endswith("generated_l2_scratch/theory.py")
            else "transfer"
        )
        for field, value in (
            ("accuracy", theme.fmt_num(row["accuracy"], places=4)),
            ("pairs_checked", row["pairs_checked"]),
            ("pairs_correct", row["pairs_correct"]),
            ("mismatches", row["n_mismatches"]),
        ):
            cols_out = dict(cols)
            cols_out[which] = value
            rows.append(
                [
                    "score_vs_truth",
                    f"{row['level']}:{field}",
                    cols_out["l1"],
                    cols_out["scratch"],
                    cols_out["transfer"],
                    None,
                    None,
                    "C",
                    "value",
                    "a3_score_vs_truth",
                    note,
                ]
            )

    for row in data["control_rows"]:
        for field, value, state in (
            ("static_certify_green", theme.fmt_num(row["static_green"]), "value"),
            ("replay_certify_green", theme.fmt_num(row["replay_green"]), "value"),
            ("caught", theme.fmt_num(row["caught"]), "value"),
            ("claimed_a_win", theme.fmt_num(row["claimed_a_win"]), "value"),
            ("world_is_solvable", theme.fmt_num(row["world_is_solvable"]), "value"),
            ("first_mismatch", None, "insufficient-data"),
        ):
            note = row["edit"]
            if field == "first_mismatch":
                note = (
                    "null: a mismatch did occur (outcome replay_mismatch, anomaly kinds "
                    + ", ".join(row["anomaly_kinds"])
                    + ") but no index was recorded. ABSENT, not 0 and not 'no mismatch'."
                )
            rows.append(
                [
                    "negative_controls",
                    f"{row['arm']}:{field}",
                    None,
                    None,
                    # The controls test the CARRIED manual, so they sit in the
                    # transfer column.
                    value,
                    None,
                    None,
                    "D",
                    state,
                    "a3_negative_controls",
                    note,
                ]
            )

    prov = data["provenance"]
    for line, value, state, note in (
        (
            "derived_fields",
            len(prov["derived"]),
            "value",
            "derived from frame 0: " + ", ".join(prov["derived"]),
        ),
        (
            "supplied_fields",
            len(prov["supplied"]),
            "value",
            "supplied to EVERY arm alike (cold start, control and transfer), so the "
            "comparison isolates the rules: " + ", ".join(prov["supplied"]),
        ),
    ):
        rows.append(
            ["provenance_l2_transfer", line, None, None, value, None, None, "E", state, "a3_provenance_transfer", note]
        )
    for line in prov["not_derivable"]:
        rows.append(
            [
                "provenance_l2_transfer",
                f"also_derivable.{line}",
                None,
                None,
                None,
                None,
                None,
                "E",
                "not-applicable",
                "a3_provenance_transfer",
                "structurally not derivable, NOT '0 derived': the goal cell is not "
                "rendered (D-A3-002) and a portal exit is plain floor (D-A3-003); one "
                "frame or a thousand, neither is in the pixels.",
            ]
        )

    bad = [i for i, row in enumerate(rows) if len(row) != len(CSV_HEADER)]
    if bad:
        raise ValueError(
            f"CSV rows {bad} have the wrong width; a short row silently shifts every "
            "column right of the gap, which is exactly the failure the audit layer exists "
            "to catch."
        )
    return rows


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

#: Where panel A's data ends and its ratio/saved gutter begins, in data units
#: on the symlog axis. The upper limit is far past it so the gutter is empty
#: chart, and the x ticks stop at the data -- a tick out there would claim the
#: gutter was an axis position.
_A_GUTTER_X = 1100.0
_A_XMAX = 30000.0
_A_XTICKS = (0.0, 1.0, 3.0, 10.0, 35.0, 100.0, 347.0)
_ROW_OFFSET = 0.17  # the two arms sit either side of their row's centre


def _panel_a(ax, data, t, p) -> None:
    """The nine meter lines, control vs transfer, on a symlog axis."""
    rows = data["meter_rows"]
    c_scratch, c_transfer = theme.series_colour(t, 0), theme.series_colour(t, 1)
    m_scratch, m_transfer = theme.series_marker(0), theme.series_marker(1)

    y_bottom = len(rows) - 0.25
    first_flat = min(i for i, r in enumerate(rows) if r["flat"])
    ax.axhspan(first_flat - 0.5, y_bottom, color=p["grid"], zorder=0)

    for i, row in enumerate(rows):
        y_s, y_t = i - _ROW_OFFSET, i + _ROW_OFFSET
        ax.plot(
            [row["scratch"], row["transfer"]],
            [y_s, y_t],
            color=p["ink_secondary"],
            linewidth=1.1,
            linestyle=":" if row["flat"] else "-",
            alpha=0.55,
            zorder=2,
        )
        ax.plot(
            [row["scratch"]], [y_s], marker=m_scratch, markersize=6.0, linestyle="none",
            color=c_scratch, zorder=4,
        )
        ax.plot(
            [row["transfer"]], [y_t], marker=m_transfer, markersize=6.0, linestyle="none",
            color=c_transfer, zorder=4,
        )
        ax.annotate(
            str(row["scratch"]), (row["scratch"], y_s), textcoords="offset points",
            xytext=(0, 6), ha="center", va="bottom", fontsize=theme.BASE_FONT_SIZE - 2,
            color=p["ink"], clip_on=False,
        )
        ax.annotate(
            str(row["transfer"]), (row["transfer"], y_t), textcoords="offset points",
            xytext=(0, -6), ha="center", va="top", fontsize=theme.BASE_FONT_SIZE - 2,
            color=p["ink"], clip_on=False,
        )

        # The toolchain tax: the part of the control arm's bar that was not
        # world-facing work, so the saving on this line is overstated by it.
        if row["line"] == TOOLCHAIN_TAX_LINE:
            tax = data["toolchain_tax"]["rounds"]
            world_facing = row["scratch"] - tax
            ax.plot(
                [world_facing, row["scratch"]], [y_s, y_s],
                color=theme.STATUS["warning"], linewidth=3.2, solid_capstyle="butt", zorder=3,
            )
            ax.annotate(
                f"* {tax} of these {row['scratch']} rounds were toolchain "
                f"conformance, not the world:\nonly {world_facing} of this saving is transfer",
                (row["scratch"], y_s), textcoords="offset points", xytext=(14, 1),
                ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3,
                # The mark wears the status colour; the sentence wears a text
                # token, because STATUS['warning'] on the light surface is well
                # under the contrast floor for body text.
                color=p["ink_secondary"],
            )

    trans = ax.get_yaxis_transform()
    for i, row in enumerate(rows):
        ax.text(
            0.800, i, theme.fmt_num(row["ratio"], places=4), transform=trans, ha="right",
            va="center", fontsize=theme.BASE_FONT_SIZE - 2,
            color=p["muted"] if row["flat"] else p["ink_secondary"],
        )
        ax.text(
            0.875, i, str(row["saved"]), transform=trans, ha="right", va="center",
            fontsize=theme.BASE_FONT_SIZE - 2,
            color=p["muted"] if row["flat"] else p["ink_secondary"],
        )
    ax.text(0.800, -0.95, "ratio", transform=trans, ha="right", va="center",
            fontsize=theme.BASE_FONT_SIZE - 2, color=p["muted"])
    ax.text(0.875, -0.95, "saved", transform=trans, ha="right", va="center",
            fontsize=theme.BASE_FONT_SIZE - 2, color=p["muted"])
    ax.text(
        0.44, (first_flat + len(rows) - 1) / 2.0,
        "no saving at all -- 1:1, 3:3, 1:1.\nDrawn because the flatness is half of the result:\n"
        "a table showing savings here would be measuring\nsomething other than transfer.",
        transform=trans, ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3,
        color=p["ink_secondary"],
    )

    ax.set_xscale("symlog", linthresh=1.0, linscale=0.9)
    ax.set_xlim(-0.45, _A_XMAX)
    ax.xaxis.set_major_locator(FixedLocator(list(_A_XTICKS)))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{v:g}" for v in _A_XTICKS])
    ax.axvline(_A_GUTTER_X, color=p["axis"], linewidth=0.6, zorder=1)
    ax.set_ylim(y_bottom, -1.35)
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels(
        [r["line"] + (" *" if r["line"] == TOOLCHAIN_TAX_LINE else "") for r in rows],
        fontsize=theme.BASE_FONT_SIZE - 1,
    )
    ax.grid(False)
    ax.grid(True, axis="x")
    ax.set_xlabel("meter units (symlog, linear below 1 so a genuine 0 is drawn at 0)")
    ax.set_title(
        "A. same level, books or no books: the like-for-like bill (n = 1 run per arm, "
        "no variance, no error bars)",
        loc="left",
    )


def _panel_b(ax, data, t, p) -> None:
    """Cost to first plan: A3's "the one that matters"."""
    rows = [r for r in data["first_plan_rows"] if r["line"] in FIRST_PLAN_LINES]
    rows = sorted(rows, key=lambda r: FIRST_PLAN_LINES.index(r["line"]))
    c_scratch, c_transfer = theme.series_colour(t, 0), theme.series_colour(t, 1)
    m_scratch, m_transfer = theme.series_marker(0), theme.series_marker(1)

    for i, row in enumerate(rows):
        ax.plot([row["transfer"], row["scratch"]], [i, i], color=p["ink_secondary"],
                linewidth=1.1, alpha=0.55, zorder=2)
        ax.plot([row["scratch"]], [i], marker=m_scratch, markersize=6.0, linestyle="none",
                color=c_scratch, zorder=3)
        ax.plot([row["transfer"]], [i], marker=m_transfer, markersize=6.0, linestyle="none",
                color=c_transfer, zorder=3)
        ax.annotate(str(row["scratch"]), (row["scratch"], i), textcoords="offset points",
                    xytext=(7, 0), ha="left", va="center",
                    fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink"])
        tag = f"{row['transfer']}" + (
            "  (a real zero: the arm took no action before it had a plan)"
            if row["transfer"] == 0 else ""
        )
        ax.annotate(tag, (row["transfer"], i), textcoords="offset points", xytext=(7, -11),
                    ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink"])

    ax.set_xlim(-12.0, 470.0)
    ax.set_ylim(len(rows) - 0.4, -0.75)
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([r["line"] for r in rows], fontsize=theme.BASE_FONT_SIZE - 1)
    ax.grid(False)
    ax.grid(True, axis="x")
    ax.set_xlabel("meter units, spent before a plan first existed")
    ax.set_title("B. cost to first plan (same two arms; l1 is a different level)", loc="left")


def _panel_c(ax, data, t, p) -> None:
    """Accuracy against ground truth, each with the n it was measured over."""
    rows = data["accuracy_rows"]
    # The two level-2 manuals are the two arms of panels A and B, so they wear
    # the same two slots. l1 is a different level and wears a text token, not a
    # series colour -- it is not a third arm of this comparison.
    colour_of = {
        "theory/generated_l1/theory.py": p["muted"],
        "theory/generated_l2_scratch/theory.py": theme.series_colour(t, 0),
        "theory/generated_l2/theory.py": theme.series_colour(t, 1),
    }

    for i, row in enumerate(rows):
        ax.barh(i, row["accuracy"], height=0.46, color=colour_of[row["theory"]], zorder=2)
        ax.text(
            row["accuracy"] + 0.03, i,
            f"{theme.fmt_num(row['accuracy'], places=4)}   n = {row['pairs_checked']} pairs, "
            f"{row['n_mismatches']} mismatches",
            ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink"],
        )

    # l1 is a different level. Band it off; no ratio is taken across this line.
    boundary = max(i for i, r in enumerate(rows) if r["level"] == "a3-l1") + 0.5
    ax.axhline(boundary, color=p["axis"], linewidth=0.8, linestyle="--")
    ax.text(
        0.02, boundary - 0.05, "a3-l1: a different level, no ratio taken across this line",
        transform=ax.get_yaxis_transform(), ha="left", va="bottom",
        fontsize=theme.BASE_FONT_SIZE - 3, color=p["muted"],
    )
    ax.annotate(
        "the level was never explored: this is the accuracy of TRANSFER, not of induction",
        (0.02, len(rows) - 1 + 0.36), xycoords=ax.get_yaxis_transform(), ha="left", va="top",
        fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"],
    )

    ax.set_xlim(0.0, 1.62)
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_yticks(list(range(len(rows))))
    ax.set_yticklabels([r["label"] for r in rows], fontsize=theme.BASE_FONT_SIZE - 3)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.grid(False)
    ax.grid(True, axis="x")
    ax.set_xlabel("accuracy over every reachable (state, action) pair")
    ax.set_title("C. the one row with a real sample size", loc="left")


_CONTROL_COLUMNS: tuple[tuple[str, str], ...] = (
    ("static", "static\ncertify"),
    ("replay", "replay\ncertify"),
    ("win", "claimed\na win?"),
    ("first_mismatch", "first_\nmismatch"),
)

#: Short glosses for the two edits. The full ``edit`` string is in the CSV; on
#: the plate it would take more width than the whole panel has.
_CONTROL_GLOSS = {
    "l2_negctl_oneway": "portal B -> exit_b leg\ndeleted (unsolvable)",
    "l2_negctl_rewired": "portal B leg lands the\nCart elsewhere (solvable)",
}


def _panel_d(ax, data, t, p) -> None:
    """Which layer caught the rewired worlds.

    Colour tracks one thing only -- whether that layer caught the edit -- and it
    is carried on the cell's edge rather than its fill, so the text inside keeps
    an ink token and its contrast in both themes. Every cell is labelled.
    """
    rows = data["control_rows"]
    for i, row in enumerate(rows):
        for j, (kind, _) in enumerate(_CONTROL_COLUMNS):
            edge, style, text, width = p["axis"], "-", "", 2.0
            if kind == "static":
                # 'green' here means the check PASSED, i.e. it saw nothing wrong.
                edge = theme.STATUS["good"] if not row["static_green"] else theme.STATUS["critical"]
                text = "green:\ndid NOT\ncatch it"
            elif kind == "replay":
                edge = theme.STATUS["good"] if not row["replay_green"] else theme.STATUS["critical"]
                text = "not green:\nCAUGHT\nit"
            elif kind == "win":
                edge = theme.STATUS["good"] if not row["claimed_a_win"] else theme.STATUS["critical"]
                text = "no"
            else:
                # null: absent, and absence is drawn as absence -- never as 0,
                # and never as "there was no mismatch".
                edge, style, width = p["muted"], ":", 0.9
                text = "absent:\nnot\nrecorded"
            ax.add_patch(
                Rectangle((j + 0.08, i + 0.10), 0.84, 0.80, facecolor="none", edgecolor=edge,
                          linewidth=width, linestyle=style, zorder=2)
            )
            ax.text(
                j + 0.5, i + 0.5, text, ha="center", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3,
                color=p["muted"] if kind == "first_mismatch" else p["ink"], zorder=3,
            )

    ax.set_xlim(0.0, len(_CONTROL_COLUMNS))
    ax.set_ylim(len(rows), 0.0)
    ax.set_xticks([j + 0.5 for j in range(len(_CONTROL_COLUMNS))])
    ax.set_xticklabels([label for _, label in _CONTROL_COLUMNS], fontsize=theme.BASE_FONT_SIZE - 2)
    ax.set_yticks([i + 0.5 for i in range(len(rows))])
    ax.set_yticklabels(
        [f"{r['arm']}\n{_CONTROL_GLOSS[r['arm']]}" for r in rows],
        fontsize=theme.BASE_FONT_SIZE - 3,
    )
    ax.grid(False)
    ax.tick_params(length=0.0)
    meta = data["controls_meta"]
    ax.set_xlabel(
        f"all_caught: {theme.fmt_num(meta['all_caught'])}   ·   none_claimed_a_win: "
        f"{theme.fmt_num(meta['none_claimed_a_win'])}\nstatic_layer_caught_any: "
        f"{theme.fmt_num(meta['static_layer_caught_any'])}",
        fontsize=theme.BASE_FONT_SIZE - 2,
    )
    ax.set_title("D. the safety valve: static caught neither, replay caught both", loc="left")


def _panel_e(ax, data, t, p) -> None:
    """6 derived / 3 supplied, and the two fields that are not derivable at all."""
    prov = data["provenance"]
    n_derived, n_supplied = len(prov["derived"]), len(prov["supplied"])
    # Ordinal, not categorical: "how much of the manual's frame reading the arm
    # did itself". The two categorical slots stay reserved for the two arms.
    dark, light = theme.sequential_steps(t, 2, ordinal=True)[::-1]
    # Slot 1's hatch is ABSENCE['not-applicable']'s "///", which must not appear
    # on a value bar in the same panel as the absence cells below.
    supplied_hatch = theme.series_hatch(2)

    ax.barh(0.30, n_derived, height=0.42, color=dark, zorder=2)
    ax.barh(0.30, n_supplied, height=0.42, left=n_derived, color=light,
            hatch=supplied_hatch, edgecolor=p["ink_secondary"], linewidth=0.8, zorder=2)
    # Both segments are ramp steps, so which ink reads on them is fixed by the
    # ramp and not by the theme: the dark step wears the dark theme's ink token,
    # the light step wears the light theme's. Using p["ink"] for both would put
    # white on #cde2fb in the dark theme.
    ax.text(n_derived / 2.0, 0.30, f"{n_derived} derived", ha="center", va="center",
            fontsize=theme.BASE_FONT_SIZE - 2, color=theme.PALETTE["dark"]["ink"], zorder=3)
    ax.text(n_derived + n_supplied / 2.0, 0.30, f"{n_supplied} supplied", ha="center",
            va="center", fontsize=theme.BASE_FONT_SIZE - 2,
            color=theme.PALETTE["light"]["ink"], zorder=3)
    ax.text(
        -0.1, -0.28,
        f"derived from frame 0 ({n_derived}): " + ", ".join(prov["derived"]),
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"],
    )
    ax.text(
        -0.1, -0.62,
        f"supplied ({n_supplied}): " + ", ".join(prov["supplied"]),
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"],
    )
    ax.text(
        -0.1, -0.92,
        "-- handed to EVERY arm alike, so the comparison isolates the rules",
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=p["muted"],
    )

    for k, field in enumerate(prov["not_derivable"]):
        ax.add_patch(
            Rectangle((k * 1.95, 0.98), 1.75, 0.40, facecolor="none",
                      edgecolor=p["ink_secondary"],
                      hatch=theme.ABSENCE["not-applicable"]["hatch"], linewidth=0.8, zorder=2)
        )
        ax.text(k * 1.95 + 0.875, 1.18, field, ha="center", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink"], zorder=3)
    ax.text(
        len(prov["not_derivable"]) * 1.95 + 0.25, 1.18,
        "also_derivable: structurally NOT derivable -- not '0 derived'.\n"
        "The goal is not rendered (D-A3-002); a portal exit is plain floor (D-A3-003).",
        ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"],
    )

    ax.set_xlim(-0.2, 9.7)
    ax.set_ylim(-1.25, 1.55)
    ax.set_yticks([])
    ax.set_xticks([0, 3, 6, 9])
    ax.grid(False)
    ax.set_xlabel("fields of the transfer arm's problem instance (frame route, 1 frame read)")
    ax.set_title("E. what the transfer arm was handed vs read off the frame", loc="left")


def _render(data: dict, t: str) -> list[str]:
    p = theme.apply_theme(t)

    fig = plt.figure(figsize=(12.6, 12.8))
    gs = fig.add_gridspec(4, 2, height_ratios=[1.80, 0.60, 0.82, 0.62])
    _panel_a(fig.add_subplot(gs[0, :]), data, t, p)
    _panel_b(fig.add_subplot(gs[1, 0]), data, t, p)
    _panel_c(fig.add_subplot(gs[1, 1]), data, t, p)
    _panel_d(fig.add_subplot(gs[2, 0]), data, t, p)
    _panel_e(fig.add_subplot(gs[2, 1]), data, t, p)

    # One key for the plate. The two arms are the same two arms in panels A, B
    # and C, so the key belongs to the figure rather than to any one panel --
    # and on panel A every region large enough to hold it sits on data.
    pad = fig.add_subplot(gs[3, :])
    pad.axis("off")
    arm_key = pad.legend(
        handles=[
            Line2D([], [], color=theme.series_colour(t, 0), marker=theme.series_marker(0),
                   linestyle="none", markersize=6.0,
                   label=f"{CONTROL_ARM} -- the control: level 2 from nothing, carrying nothing"),
            Line2D([], [], color=theme.series_colour(t, 1), marker=theme.series_marker(1),
                   linestyle="none", markersize=6.0,
                   label=f"{TRANSFER_ARM} -- carries domain.dsl + playbook.dsl from level 1, unchanged"),
            Line2D([], [], color=theme.STATUS["warning"], linewidth=3.2,
                   label="* toolchain conformance, not world-facing work (panel A)"),
            Line2D([], [], color=p["muted"], linewidth=6.0,
                   label=f"{BASELINE_ARM} -- a DIFFERENT LEVEL; drawn only on panel C, never in a ratio"),
        ],
        loc="upper left",
        title="panels A, B, C -- the arms",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 2,
        title_fontsize=theme.BASE_FONT_SIZE - 2,
    )
    arm_key.get_title().set_color(p["ink_secondary"])
    pad.add_artist(arm_key)
    absence_key = pad.legend(
        handles=theme.absence_handles(t),
        loc="upper right",
        bbox_to_anchor=(1.0, 1.0),
        title="panels D, E -- absence encodings; an absent value is never drawn as a zero",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 2,
        title_fontsize=theme.BASE_FONT_SIZE - 2,
    )
    absence_key.get_title().set_color(p["ink_secondary"])

    fig.suptitle(
        "Figure 4 -- A3 migration: carrying the book vs starting again "
        "(C3: a domain written once is worth carrying)"
    )
    accuracy_ns = "/".join(str(r["pairs_checked"]) for r in data["accuracy_rows"])
    tax = data["toolchain_tax"]
    theme.caveat(
        fig,
        "n = 1 RUN PER ARM. Nothing here is replicated and no artefact carries a variance, so no "
        "error bar is drawn and none could be; the only genuine sample size on the plate is panel "
        f"C's n = {accuracy_ns} reachable (state, action) pairs, printed beside each 1.0000.   "
        f"* THE TOOLCHAIN TAX: {tax['rounds']} of the control arm's {tax['total']} theorize rounds "
        "went to toolchain conformance (grounding lifted rules, then object names) rather than to "
        f"the world -- {tax['pct']}% of its adjudication budget -- so the theorize_rounds saving "
        f"overstates transfer by {tax['rounds']} rounds.   "
        "THE BOTTOM THREE LINES SAVE NOTHING (1:1, 3:3, 1:1) and are drawn for that "
        "reason: a table showing savings there would be measuring something other than transfer.   "
        "WHO CARRIED THE BOOKS: the person who carried them to level 2 is the person who wrote "
        "them for level 1, and they already knew the answer. The control arm's blind was PARTIALLY "
        "BROKEN and recorded as incident A3-I1 -- object names and the law's name are contaminated "
        "-- so no cross-arm agreement on naming is claimed anywhere on this figure.   LEVELS, NOT "
        "GAMES: the two levels share a mechanism set by construction; A3 says nothing about "
        "carrying a domain between games with different mechanics.   THE BILL IS STRUCTURAL, NOT "
        "ECONOMIC: it counts frames, actions, engine stages, candidates, rounds and clauses, and "
        "does NOT count model calls -- the largest term in a real bill. The zeros are real and the "
        "right shape; converting them to dollars is not something this experiment did.   "
        f"l1_cold_start appears only in panel C, labelled by level, and in the CSV. {data['bill_note']}"
        "   A 0 on panel A or B means the arm genuinely did none of that (a real zero); the "
        "hatched and dotted cells in panels D and E are values that are absent, and absence is "
        "never drawn as a zero.",
        theme=t,
    )
    return theme.save(fig, NAME, t)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    data, notes = extract()
    rows = csv_rows(data)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    images: list[str] = []
    for t in theme.THEMES:
        images.extend(_render(data, t))

    headline = {r["line"]: r for r in data["meter_rows"]}
    notes.append(
        "headline like-for-like: world_frames "
        f"{headline['world_frames']['scratch']} -> {headline['world_frames']['transfer']} "
        f"(ratio {theme.fmt_num(headline['world_frames']['ratio'], places=4)}); the line A3 calls "
        "the one that matters is cost-to-first-plan world_actions "
        f"{data['first_plan_rows'][1]['scratch']} -> {data['first_plan_rows'][1]['transfer']}."
    )
    notes.append(f"{len(rows)} CSV rows over 5 sections; 5 panels drawn per theme.")
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
