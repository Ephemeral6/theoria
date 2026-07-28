"""fig03_capability_spectrum -- 图3 电池能力谱 / the battery capability spectrum.

Theoria.md 3.2 figure 3, per PLAN.md section 4: the metric-family x arm matrix
that `battery/artifacts/capability_spectrum.json` holds. Rows are the 38 metric
cards grouped by ``family``; columns are the four arms; a cell is that arm's
**median** of that metric over its runs scored ``ok``.

What this script does, in order:

1. reads the three declared battery artefacts through ``sources`` (never a raw
   path, so every input lands in ``figures/SOURCES.sha256``);
2. enumerates metrics, families and arms **from the file** -- nothing about the
   metric set is hard-coded, and a family or arm this module has never seen
   raises rather than being silently dropped;
3. reduces each (metric, arm) pair to one cell: the median over the arm's runs
   whose status is ``ok``, plus the status breakdown of the runs that were not;
4. normalises **within the row** -- units are incompatible across metrics, so
   there is no cross-row comparison to be had -- and orients by the card's
   ``direction`` so that further along the colour ramp is always better;
5. writes ``csv/fig03_capability_spectrum.csv`` (the audit surface): one row per
   (metric, arm) pair, absent ones included, with their real status;
6. renders one figure per theme, two themes x svg+png = 4 images.

Four cell states, four distinct encodings -- this is why it is not a plain
heatmap. ``ok`` takes colour on the sequential ramp; ``not-applicable`` is
hatched with no fill; ``insufficient-data`` is outlined with no fill; and a
metric the gaming audit demoted to reference tier carries a marker on its row
label and a band in the tier column. **No absent cell is ever drawn as a zero**
-- that is exactly the error `battery/REPORT_V0.md` exists to complain about.

Two structural commitments the module enforces rather than documents:

* **The bound pair.** ``battery/REPORT_V0.md`` and ``battery/METRICS.md`` bind
  K4 (evidence coverage) to K2 (held-out accuracy): A0 scores K4 = 1.000
  *because* it refused the one generalisation it lacked evidence for, which is
  precisely why its K2 = 0.000. So K4 is placed immediately beside K2 in the
  same family group, the two rows are bracketed and boxed as one block, and
  ``_row_order`` **raises** if anything ever separates them. A future edit that
  breaks the pairing cannot render a figure.
* **Neutral is not a ranking.** A card with ``direction == "neutral"`` is not
  oriented and does not take the ranking ramp; it is drawn on a desaturated
  grey ramp and the legend says it is support, not a score.

Determinism: no clock, no randomness, no reliance on dict order. Every key list
is sorted explicitly (see ``FAMILY_ORDER``, ``_natural_key``, ``_arm_order``).
Even-length medians use ``statistics.median``, i.e. the arithmetic mean of the
two middle values.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import statistics  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig03_capability_spectrum"

#: Row-group order, top to bottom. PLAN.md section 4 names "economy /
#: epistemic / planning / exploration / metacognition"; the ``family`` field in
#: the artefact spells the fifth one ``mechanism``, so that is what is used
#: here. The order is otherwise PLAN.md's. ``_row_order`` raises if the file
#: ever carries a family that is not in this tuple -- a new family must be
#: placed deliberately, not appended by accident.
FAMILY_ORDER: tuple[str, ...] = (
    "economy",
    "epistemic",
    "planning",
    "exploration",
    "mechanism",
)

#: ``(anchor, follower)``: ``follower`` is lifted out of its natural slot and
#: placed immediately after ``anchor`` in the same family group. One entry, and
#: it is the binding rule from ``battery/REPORT_V0.md``: evidence coverage
#: rewards exactly the caution that held-out accuracy punishes, so K4 must
#: never be reported without K2 beside it.
BOUND_PAIRS: tuple[tuple[str, str], ...] = (("K2", "K4"),)

BOUND_PAIR_WHY = (
    "K4 (evidence coverage) must never be read without K2 (held-out accuracy) "
    "beside it: A0 scores K4 = 1.000 because it refused the one generalisation "
    "it lacked evidence for, which is exactly why its K2 = 0.000."
)

#: Cell status is a reduction over an arm's runs, and this is the reduction:
#: one ``ok`` run makes the cell a value; otherwise one ``insufficient-data``
#: run makes the absence contingent; only an arm whose every run was
#: ``not-applicable`` gets the structural encoding.
STATUS_PRECEDENCE: tuple[str, ...] = ("ok", "insufficient-data", "not-applicable")

#: Floor on the sequential ramp, so the step nearest the chart surface still
#: clears 2:1 against it. 0.25 lands on ``theme``'s documented ordinal floor in
#: both themes (step 250 on light, step 600 on dark).
RAMP_FLOOR = 0.25

#: Normalised value given to every ok cell in a row whose ok medians are all
#: equal. The row carries no ranking, and mid-ramp says so without claiming an
#: order that is not there.
FLAT_ROW_NORMALISED = 0.5

CSV_HEADER: tuple[str, ...] = (
    "family",
    "metric",
    "tier",
    "direction",
    "arm",
    "n_runs",
    "median",
    "normalised",
    "status",
    "note",
)

_DIRECTION_MARK = {"higher": "↑", "lower": "↓", "neutral": "≈"}

#: Appended to the row label of a metric the gaming audit demoted.
DEMOTED_MARK = "†"  # dagger

FIGSIZE = (8.8, 12.8)


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def _natural_key(metric_id: str) -> tuple[str, int]:
    """``K10`` sorts after ``K9``, not after ``K1``."""
    head = metric_id[:1]
    tail = metric_id[1:]
    if not head.isalpha() or not tail.isdigit():
        raise ValueError(
            f"metric id {metric_id!r} is not <letter><digits>; the row order "
            "rule cannot place it. Extend _natural_key deliberately."
        )
    return (head, int(tail))


def _row_order(cards: dict) -> list[str]:
    """Metric ids top to bottom: family group, then id, then the bound pairs."""
    families = sorted({card["family"] for card in cards.values()})
    unknown = [f for f in families if f not in FAMILY_ORDER]
    if unknown:
        raise ValueError(
            f"family {unknown!r} is in the artefact but not in FAMILY_ORDER; "
            "give it a deliberate position in the row grouping."
        )

    order: list[str] = []
    for family in FAMILY_ORDER:
        group = sorted(
            (mid for mid, card in cards.items() if card["family"] == family),
            key=_natural_key,
        )
        for anchor, follower in BOUND_PAIRS:
            if anchor in group and follower in group:
                group.remove(follower)
                group.insert(group.index(anchor) + 1, follower)
        order.extend(group)

    # The commitment, enforced. A figure that separated the bound pair would be
    # the one object this plate exists to make impossible.
    for anchor, follower in BOUND_PAIRS:
        if anchor not in order or follower not in order:
            raise ValueError(
                f"bound pair {anchor}/{follower}: {anchor if anchor not in order else follower} "
                "is absent from the metric set, so the pairing cannot be drawn. "
                f"{BOUND_PAIR_WHY}"
            )
        if abs(order.index(anchor) - order.index(follower)) != 1:
            raise ValueError(
                f"bound pair {anchor}/{follower} is not adjacent in the row "
                f"order (rows {order.index(anchor)} and {order.index(follower)}). "
                f"{BOUND_PAIR_WHY}"
            )
        if cards[anchor]["family"] != cards[follower]["family"]:
            raise ValueError(
                f"bound pair {anchor}/{follower} straddles two family groups "
                f"({cards[anchor]['family']} / {cards[follower]['family']}); a "
                "group band would split them. " + BOUND_PAIR_WHY
            )
    return order


def _arm_order(runs: dict, spectrum: dict, validation: dict) -> tuple[list[str], list[str]]:
    """Control arms first, then the rest. Returns ``(order, control_arms)``.

    The axis authority is the spectrum's own ``provenance.arms`` -- the arms of
    the artefact actually being drawn -- and the control/treatment split comes
    from ``validation_material.json``, which states it as a field rather than
    leaving it to be inferred from an arm's name.

    ``arm_contrast.json`` deliberately does *not* get a vote here. It is a v1-era
    artefact that predates the ``schema_repro`` arm, and letting a stale file
    veto the column axis meant this plate could not be drawn at all. It is still
    read, and its staleness is reported as a note rather than silently absorbed
    -- see ``extract``.
    """
    declared = list(spectrum["provenance"]["arms"])
    present = sorted({run["arm"] for run in runs.values()})
    if sorted(declared) != present:
        raise ValueError(
            f"arms scored in capability_spectrum.json {present!r} do not match "
            f"the arms its own provenance declares {sorted(declared)!r}; the "
            "artefact is internally inconsistent."
        )
    controls = [a for a in validation["control_arms"] if a in declared]
    unknown = [a for a in validation["control_arms"] if a not in declared]
    if unknown:
        raise ValueError(
            f"validation_material.json calls {unknown!r} a control arm, but no "
            "such arm is in the spectrum; the split would be a guess."
        )
    return controls + [a for a in declared if a not in controls], controls


def _cell_status(counts: dict[str, int]) -> str:
    for status in STATUS_PRECEDENCE:
        if counts.get(status):
            return status
    raise ValueError(f"no run status to reduce: {counts!r}")


def extract() -> tuple[dict, list[str]]:
    """Read the three artefacts and reduce them to the matrix and its labels."""
    spectrum = sources.read_json("capability_spectrum")
    contrast = sources.read_json("arm_contrast")
    validation = sources.read_json("validation_material")
    audit = sources.read_json("gaming_audit")

    cards = spectrum["cards"]
    coverage = spectrum["coverage"]
    runs = spectrum["runs"]
    notes: list[str] = []

    metrics = _row_order(cards)
    arms, control_arms = _arm_order(runs, spectrum, validation)
    runs_by_arm = {arm: sorted(r for r in runs if runs[r]["arm"] == arm) for arm in arms}

    # gaming_audit is the tier authority: its `rule` is what assigns a tier
    # ("accidental and not defended -> reference; else main"). coverage.*.tier
    # carries the same field, and a disagreement means one of the two artefacts
    # was regenerated without the other -- which is a fact about the inputs, not
    # something to average over.
    tier_conflicts = [
        mid
        for mid in metrics
        if audit["metrics"][mid]["tier"] != coverage[mid]["tier"]
    ]
    if tier_conflicts:
        raise ValueError(
            "gaming_audit.json and capability_spectrum.json disagree on the tier "
            f"of {tier_conflicts!r}; one artefact is stale."
        )

    cells: dict[tuple[str, str], dict] = {}
    for mid in metrics:
        for arm in arms:
            counts: dict[str, int] = {}
            reasons: dict[str, int] = {}
            values: list[float] = []
            for run_id in runs_by_arm[arm]:
                entry = runs[run_id]["metrics"][mid]
                status = entry["status"]
                counts[status] = counts.get(status, 0) + 1
                if status == "ok":
                    if entry["value"] is None:
                        raise ValueError(
                            f"{run_id}/{mid} is ok with a null value; a cell "
                            "cannot be both scored and empty."
                        )
                    values.append(float(entry["value"]))
                elif entry.get("reason"):
                    reasons[entry["reason"]] = reasons.get(entry["reason"], 0) + 1
            values.sort()  # median is order-free, but the list is an artefact too
            cells[(mid, arm)] = {
                "status": _cell_status(counts),
                "counts": counts,
                # statistics.median: for an even-length list this is the
                # arithmetic mean of the two middle values.
                "median": statistics.median(values) if values else None,
                "n": len(values),
                # deterministic modal reason: most frequent, then alphabetical
                "reason": (
                    sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                    if reasons
                    else ""
                ),
                "normalised": None,
                "flat_row": False,
            }

    # ---- normalise within the row, orient by direction --------------------
    for mid in metrics:
        direction = cards[mid]["direction"]
        if direction not in _DIRECTION_MARK:
            raise ValueError(
                f"{mid} has direction {direction!r}; only "
                f"{sorted(_DIRECTION_MARK)} have a defined orientation."
            )
        scored = [cells[(mid, arm)]["median"] for arm in arms if cells[(mid, arm)]["n"]]
        if not scored:
            continue
        lo, hi = min(scored), max(scored)
        flat = hi == lo
        for arm in arms:
            cell = cells[(mid, arm)]
            if not cell["n"]:
                continue
            if flat:
                cell["normalised"] = FLAT_ROW_NORMALISED
                cell["flat_row"] = True
                continue
            raw = (cell["median"] - lo) / (hi - lo)
            # "further along the ramp is better". Neutral is deliberately NOT
            # oriented: there is no better end to send it to.
            cell["normalised"] = 1.0 - raw if direction == "lower" else raw

    # Cross-arm overlap: a metric has it when at least one control arm and at
    # least one treatment arm both score it. Computed here from the cells rather
    # than read out of arm_contrast.json, because that artefact predates the
    # schema_repro arm and would understate the overlap for exactly the metrics
    # schema_repro was added to cover.
    treatments = [a for a in arms if a not in control_arms]
    overlap = {
        mid: any(cells[(mid, a)]["n"] for a in control_arms)
        and any(cells[(mid, a)]["n"] for a in treatments)
        for mid in metrics
    }
    n_overlap = sum(overlap.values())

    # The stale artefact still gets read, and its disagreement is reported
    # rather than absorbed. Silently preferring the recomputation would hide
    # that one of the battery's own outputs has drifted.
    contrast_arms = sorted([contrast["control_arm"], *contrast["theoria_arms"]])
    contrast_stale = contrast_arms != sorted(arms)
    contrast_overlap = {mid: bool(contrast["metrics"][mid]["overlap"]) for mid in metrics}
    gained = sorted(m for m in metrics if overlap[m] and not contrast_overlap[m])
    lost = sorted(m for m in metrics if contrast_overlap[m] and not overlap[m])
    if lost:
        raise ValueError(
            f"arm_contrast.json says {lost!r} have cross-arm overlap but the "
            "spectrum's own cells do not; that is a contradiction, not staleness."
        )

    state_totals = {s: 0 for s in STATUS_PRECEDENCE}
    for cell in cells.values():
        state_totals[cell["status"]] += 1

    data = {
        "battery_version": spectrum["battery_version"],
        "metrics": metrics,
        "arms": arms,
        "cards": cards,
        "tier": {mid: audit["metrics"][mid]["tier"] for mid in metrics},
        "audit_rule": audit["rule"],
        "overlap": overlap,
        "n_overlap": n_overlap,
        "n_no_contrast": len(metrics) - n_overlap,
        "n_runs_by_arm": {arm: len(runs_by_arm[arm]) for arm in arms},
        "control_arms": control_arms,
        "contrast_stale": contrast_stale,
        "contrast_arms": contrast_arms,
        "contrast_gained": gained,
        "cells": cells,
        "state_totals": state_totals,
        "n_runs": len(runs),
        "coverage_note": contrast["coverage_note"],
        "design": contrast["design"],
    }

    notes.append(
        f"battery {data['battery_version']}: {len(metrics)} metrics x {len(arms)} arms "
        f"= {len(metrics) * len(arms)} cells over {data['n_runs']} runs; "
        f"ok {state_totals['ok']}, not-applicable {state_totals['not-applicable']}, "
        f"insufficient-data {state_totals['insufficient-data']}."
    )
    notes.append(
        f"gaming_audit.json demoted {sum(1 for m in metrics if data['tier'][m] == 'reference')} "
        f"of {len(metrics)} metrics to reference tier by its own rule "
        f"({data['audit_rule']}); they carry {DEMOTED_MARK} on the row label and a tier band."
    )
    notes.append(
        f"{data['n_no_contrast']} of {len(metrics)} metrics have no cross-arm "
        "contrast at all (banded): no control arm and no Theoria arm both score "
        "them, so the column difference is unavailable rather than small. Design "
        f"of the Theoria-side contrast: {data['design']}."
    )
    notes.append(
        "bound pair enforced adjacent in the row order: " + BOUND_PAIR_WHY
    )
    if contrast_stale:
        notes.append(
            f"arm_contrast.json is stale: it knows arms {contrast_arms} while the "
            f"spectrum scores {sorted(arms)}. The column axis and the overlap band "
            "are therefore computed from capability_spectrum.json itself. The "
            f"{len(gained)} metric(s) the stale artefact misses"
            + (f" ({', '.join(gained)})" if gained else "")
            + " gain their contrast from the arm it does not know about."
        )
    return data, notes


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def _median_places(value: float) -> int:
    """Decimals for a raw median. Magnitude-keyed, so it never drifts."""
    magnitude = abs(value)
    if magnitude >= 100:
        return 1
    if magnitude >= 10:
        return 2
    return 6


def _note_for(data: dict, mid: str, arm: str) -> str:
    cell = data["cells"][(mid, arm)]
    card = data["cards"][mid]
    parts: list[str] = []
    parts.append(
        "runs: "
        + ", ".join(
            f"{status}={cell['counts'][status]}"
            for status in STATUS_PRECEDENCE
            if cell["counts"].get(status)
        )
    )
    if cell["status"] != "ok" and cell["reason"]:
        parts.append("reason: " + cell["reason"])
    if cell["flat_row"]:
        parts.append(
            f"row has no spread across arms; normalised fixed at {FLAT_ROW_NORMALISED}"
        )
    if card["direction"] == "neutral":
        parts.append("neutral: not oriented, support rather than a ranking")
    if not data["overlap"][mid]:
        parts.append("no cross-arm contrast")
    if data["tier"][mid] == "reference":
        parts.append("demoted to reference tier by the gaming audit")
    for anchor, follower in BOUND_PAIRS:
        if mid in (anchor, follower):
            parts.append(f"bound pair {anchor}/{follower}")
    if arm in data["control_arms"]:
        parts.append("control arm")
    return "; ".join(parts)


def csv_rows(data: dict) -> list[list]:
    """One row per (metric, arm), absent cells included. Sorted (family, metric, arm).

    The sort is on the literal column strings -- plain lexicographic, so a
    reviewer can reproduce it in a spreadsheet. The figure's row order is a
    different, documented thing (``FAMILY_ORDER`` then ``_natural_key`` then
    ``BOUND_PAIRS``); the CSV is the audit surface, not the layout.
    """
    rows: list[list] = []
    for mid in data["metrics"]:
        card = data["cards"][mid]
        for arm in data["arms"]:
            cell = data["cells"][(mid, arm)]
            median = cell["median"]
            rows.append(
                [
                    card["family"],
                    mid,
                    data["tier"][mid],
                    card["direction"],
                    arm,
                    cell["n"],
                    "" if median is None else theme.fmt_num(median, _median_places(median)),
                    theme.fmt_num(cell["normalised"], 4) if cell["normalised"] is not None else "",
                    cell["status"],
                    _note_for(data, mid, arm),
                ]
            )
    rows.sort(key=lambda r: (r[0], r[1], r[4]))
    return rows


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------


def _relative_luminance(colour) -> float:
    def channel(value: float) -> float:
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = to_rgb(colour)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _ink_on(colour) -> str:
    """Black or white on ``colour``, whichever has the better contrast ratio."""
    lum = _relative_luminance(colour)
    on_white = 1.05 / (lum + 0.05)
    on_black = (lum + 0.05) / 0.05
    return "#0b0b0b" if on_black >= on_white else "#ffffff"


def _neutral_cmap(theme_name: str):
    """Desaturated ramp for ``neutral`` metrics -- visibly not the score ramp."""
    p = theme.PALETTE[theme_name]
    stops = [p["grid"], p["axis"], p["muted"], p["ink_secondary"]]
    if theme_name == "dark":
        stops = [p["axis"], p["muted"], p["ink_secondary"]]
    return LinearSegmentedColormap.from_list(f"theoria_neutral_{theme_name}", stops, N=256)


def _row_label(data: dict, mid: str) -> str:
    card = data["cards"][mid]
    bits = [mid, _DIRECTION_MARK[card["direction"]]]
    if card["unit"]:
        bits.append(card["unit"])
    if data["tier"][mid] == "reference":
        bits.append(DEMOTED_MARK)
    return " ".join(bits)


def _family_spans(data: dict) -> list[tuple[str, int, int]]:
    spans: list[tuple[str, int, int]] = []
    for family in FAMILY_ORDER:
        rows = [i for i, mid in enumerate(data["metrics"]) if data["cards"][mid]["family"] == family]
        if rows:
            spans.append((family, min(rows), max(rows)))
    return spans


def _banner(data: dict) -> str:
    return "\n".join(
        [
            "CONFOUND (battery/REPORT_V1.md): every Theoria run is a self-built world, so "
            f"arm and world are perfectly confounded for the {len(data['arms']) - len(data['control_arms'])} "
            "Theoria column(s) on this plate -- no difference between a control column and a "
            f"Theoria column can be charged to the arm alone. The contrast is {data['design']}.",
            "The two control columns are the exception and the reason they are drawn first: "
            "battery v2 ingested the Schema arm (REPORT_V2.md -- 8 runs, 4 development-pile "
            "games x 2 upstream collections) and pairs it against bare_cc BY GAME, which does "
            "control for the world. That pairing is what v1's arm contrast could not do.",
            f"{data['n_no_contrast']} of {len(data['metrics'])} metrics still have data on one "
            f"side only and carry no cross-arm contrast at all ({data['n_overlap']} do). The "
            "matrix is not dense, and the band on the right is where a column difference is "
            "unavailable rather than small.",
            "BOUND PAIR: " + BOUND_PAIR_WHY,
            "Cells are arm medians over runs scored ok (statistics.median), min-max normalised "
            "WITHIN THE ROW because units are incompatible across metrics, and oriented by the "
            "card's direction. Absent cells are drawn absent, never as zero.",
        ]
    )


def _render(data: dict, theme_name: str) -> list[str]:
    p = theme.apply_theme(theme_name)
    cmap = theme.sequential_cmap(theme_name)
    ncmap = _neutral_cmap(theme_name)
    metrics = data["metrics"]
    arms = data["arms"]
    n_rows = len(metrics)
    n_cols = len(arms)
    pair_colour = p["slots"]["orange"]
    contrast_colour = p["slots"]["aqua"]
    tier_colour = p["status"]["warning"]

    fig = plt.figure(figsize=FIGSIZE)
    grid = fig.add_gridspec(
        3,
        4,
        width_ratios=[0.055, 0.032, 1.0, 0.10],
        # The last row is empty: it exists only to reserve floor space for the
        # banner, which theme.caveat anchors to the figure rather than to an
        # axis. Sized to the banner's actual line count -- at 0.075 the banner
        # ran up into the colour ramp and the two texts overlapped.
        height_ratios=[1.0, 0.15, 0.20],
        wspace=0.02,
        hspace=0.03,
    )
    ax_fam = fig.add_subplot(grid[0, 0])
    ax_bind = fig.add_subplot(grid[0, 1])
    ax_map = fig.add_subplot(grid[0, 2])
    ax_band = fig.add_subplot(grid[0, 3])
    ax_ramp = fig.add_subplot(grid[1, 0:2])
    ax_leg = fig.add_subplot(grid[1, 2:4])
    ax_pad = fig.add_subplot(grid[2, :])  # reserves the banner's room

    for axis in (ax_fam, ax_bind, ax_map, ax_band, ax_ramp, ax_leg, ax_pad):
        axis.grid(False)
        axis.set_xmargin(0)
        axis.set_ymargin(0)
    for axis in (ax_fam, ax_bind, ax_ramp, ax_leg, ax_pad):
        axis.set_axis_off()

    # ---- the matrix -------------------------------------------------------
    for row, mid in enumerate(metrics):
        direction = data["cards"][mid]["direction"]
        for col, arm in enumerate(arms):
            cell = data["cells"][(mid, arm)]
            x, y = col - 0.5, row - 0.5
            if cell["status"] == "ok":
                ramp = ncmap if direction == "neutral" else cmap
                face = ramp(RAMP_FLOOR + (1.0 - RAMP_FLOOR) * cell["normalised"])
                ax_map.add_patch(
                    Rectangle(
                        (x, y), 1.0, 1.0,
                        facecolor=face, edgecolor=p["surface"], linewidth=0.8, zorder=2,
                    )
                )
                places = _median_places(cell["median"])
                ax_map.text(
                    col, row,
                    f"{theme.fmt_num(cell['median'], min(places, 3))}   n={cell['n']}",
                    ha="center", va="center", zorder=4,
                    fontsize=theme.BASE_FONT_SIZE - 2, color=_ink_on(face),
                )
            else:
                style = theme.ABSENCE[cell["status"]]
                ax_map.add_patch(
                    Rectangle(
                        (x, y), 1.0, 1.0,
                        facecolor=style["facecolor"],
                        hatch=style["hatch"],
                        # Both absences wear ink_secondary, and the hatch alone
                        # tells them apart. `muted` on the insufficient-data
                        # outline was legible on the light surface and very
                        # nearly invisible on the dark one -- a 0.8pt dotted
                        # line at #898781 on #1a1a19 reads as an empty black
                        # hole, which is the one thing an absence must never
                        # look like.
                        edgecolor=p["ink_secondary"],
                        linestyle="-" if cell["status"] == "not-applicable" else ":",
                        linewidth=0.8 if cell["status"] == "not-applicable" else 1.1,
                        zorder=2,
                    )
                )

    # family separators, drawn over the cells
    for _family, first, last in _family_spans(data):
        if first:
            ax_map.axhline(first - 0.5, color=p["ink_secondary"], linewidth=0.9, zorder=5)
        del last

    # the bound pair, boxed as one block
    for anchor, follower in BOUND_PAIRS:
        top = min(metrics.index(anchor), metrics.index(follower))
        ax_map.add_patch(
            Rectangle(
                (-0.5, top - 0.5), n_cols, 2.0,
                facecolor="none", edgecolor=pair_colour, linewidth=2.0, zorder=6,
            )
        )

    ax_map.set_xlim(-0.5, n_cols - 0.5)
    ax_map.set_ylim(n_rows - 0.5, -0.5)  # row 0 at the top
    ax_map.set_xticks(range(n_cols))
    ax_map.set_xticklabels(
        [
            f"{arm}\n{data['n_runs_by_arm'][arm]} runs"
            + ("\n(control)" if arm in data["control_arms"] else "")
            for arm in arms
        ]
    )
    ax_map.xaxis.set_ticks_position("top")
    ax_map.set_yticks(range(n_rows))
    ax_map.set_yticklabels([_row_label(data, mid) for mid in metrics])
    ax_map.tick_params(length=0)
    for label, mid in zip(ax_map.get_yticklabels(), metrics):
        label.set_fontsize(theme.BASE_FONT_SIZE - 1.5)
        if data["tier"][mid] == "reference":
            label.set_color(p["muted"])
        if mid in {m for pair in BOUND_PAIRS for m in pair}:
            label.set_color(pair_colour)
    for spine in ax_map.spines.values():
        spine.set_visible(False)
    # Computed, not written down. The hard-coded "38 metric cards ... 4 arms"
    # this replaces was already wrong by one column when P4 found it: battery v2
    # scores five arms. A caption that states a count must derive it.
    ax_map.set_title(
        f"rows: {len(metrics)} metric cards by family    "
        f"columns: {len(arms)} arms    "
        "cell: arm median (raw, in the row's unit) and the number of runs scored ok",
        fontsize=theme.BASE_FONT_SIZE - 1,
        color=p["ink_secondary"],
        pad=26,
    )

    # ---- family gutter ----------------------------------------------------
    ax_fam.set_xlim(0, 1)
    ax_fam.set_ylim(n_rows - 0.5, -0.5)
    for family, first, last in _family_spans(data):
        ax_fam.plot(
            [0.86, 0.86], [first - 0.42, last + 0.42],
            color=p["ink_secondary"], linewidth=1.2, solid_capstyle="butt",
        )
        ax_fam.text(
            0.52, (first + last) / 2.0, family.upper(),
            rotation=90, ha="center", va="center",
            fontsize=theme.BASE_FONT_SIZE - 1, color=p["ink"],
        )

    # ---- bound-pair bracket ----------------------------------------------
    ax_bind.set_xlim(0, 1)
    ax_bind.set_ylim(n_rows - 0.5, -0.5)
    for anchor, follower in BOUND_PAIRS:
        top = min(metrics.index(anchor), metrics.index(follower))
        bottom = top + 1
        ax_bind.plot(
            [0.62, 0.62], [top - 0.44, bottom + 0.44],
            color=pair_colour, linewidth=1.8, solid_capstyle="butt",
        )
        for edge in (top - 0.44, bottom + 0.44):
            ax_bind.plot([0.62, 1.0], [edge, edge], color=pair_colour, linewidth=1.8)
        ax_bind.text(
            0.22, (top + bottom) / 2.0, "bound pair",
            rotation=90, ha="center", va="center",
            fontsize=theme.BASE_FONT_SIZE - 3, color=pair_colour,
        )

    # ---- tier and contrast bands -----------------------------------------
    ax_band.set_xlim(0, 2)
    ax_band.set_ylim(n_rows - 0.5, -0.5)
    for row, mid in enumerate(metrics):
        if data["tier"][mid] == "reference":
            ax_band.add_patch(
                Rectangle(
                    (0.08, row - 0.5), 0.84, 1.0,
                    facecolor=tier_colour, hatch="...", edgecolor=p["ink_secondary"],
                    linewidth=0.0,
                )
            )
        if data["overlap"][mid]:
            ax_band.add_patch(
                Rectangle(
                    (1.08, row - 0.5), 0.84, 1.0,
                    facecolor=contrast_colour, edgecolor="none", linewidth=0.0,
                )
            )
        else:
            ax_band.add_patch(
                Rectangle(
                    (1.08, row - 0.5), 0.84, 1.0,
                    facecolor="none", hatch="xxx", edgecolor=p["muted"], linewidth=0.0,
                )
            )
    ax_band.set_yticks([])
    ax_band.set_xticks([0.5, 1.5])
    ax_band.set_xticklabels(["tier", "cross-arm"], rotation=90, fontsize=theme.BASE_FONT_SIZE - 3)
    ax_band.xaxis.set_ticks_position("top")
    ax_band.tick_params(length=0)
    for spine in ax_band.spines.values():
        spine.set_visible(False)

    # ---- the two ramps ---------------------------------------------------
    ax_ramp.set_xlim(0, 1)
    ax_ramp.set_ylim(0, 1)
    steps = 12
    for index, (label, ramp, sub) in enumerate(
        (
            ("normalised within row, oriented:\nfurther right is better", cmap, "worse → better"),
            ("neutral metrics are not oriented:\nsupport, not a ranking", ncmap, "low → high"),
        )
    ):
        base = 0.60 - index * 0.44
        for step in range(steps):
            frac = step / (steps - 1)
            ax_ramp.add_patch(
                Rectangle(
                    (0.06 + step * (0.62 / steps), base), 0.62 / steps, 0.13,
                    facecolor=ramp(RAMP_FLOOR + (1.0 - RAMP_FLOOR) * frac),
                    edgecolor="none",
                )
            )
        ax_ramp.text(
            0.06, base + 0.17, label,
            ha="left", va="bottom", fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"],
        )
        ax_ramp.text(
            0.06, base - 0.03, sub,
            ha="left", va="top", fontsize=theme.BASE_FONT_SIZE - 3, color=p["muted"],
        )

    # ---- legend ----------------------------------------------------------
    handles = list(theme.absence_handles(theme_name))
    handles.append(
        Patch(facecolor="none", edgecolor=pair_colour, linewidth=2.0,
              label="bound pair: K4 never without K2")
    )
    handles.append(
        Patch(facecolor=tier_colour, hatch="...", edgecolor=p["ink_secondary"], linewidth=0.0,
              label=f"tier band: demoted to reference ({DEMOTED_MARK})")
    )
    handles.append(
        Patch(facecolor=contrast_colour, edgecolor="none",
              label=f"cross-arm band: contrast exists ({data['n_overlap']} of {len(metrics)})")
    )
    handles.append(
        Patch(facecolor="none", hatch="xxx", edgecolor=p["muted"], linewidth=0.0,
              label=f"cross-arm band: none ({data['n_no_contrast']} of {len(metrics)})")
    )
    handles.append(
        Line2D([], [], linestyle="none", marker="", label="in cell: median   n = runs scored ok")
    )
    handles.append(
        Line2D([], [], linestyle="none", marker="",
               label=f"{_DIRECTION_MARK['higher']} higher is better   "
                     f"{_DIRECTION_MARK['lower']} lower is better   "
                     f"{_DIRECTION_MARK['neutral']} neutral")
    )
    ax_leg.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(0.0, 1.06),
        ncols=2,
        handlelength=1.8,
        handleheight=1.1,
        labelspacing=0.7,
        columnspacing=1.4,
        fontsize=theme.BASE_FONT_SIZE - 2,
    )

    fig.suptitle(
        f"Figure 3 -- battery capability spectrum, metric family x arm "
        f"(battery {data['battery_version']}, {data['n_runs']} runs)"
    )
    theme.caveat(fig, _banner(data), theme=theme_name)
    return theme.save(fig, NAME, theme_name)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    data, notes = extract()
    rows = csv_rows(data)
    expected = len(data["metrics"]) * len(data["arms"])
    if len(rows) != expected:
        raise ValueError(f"{len(rows)} CSV rows for {expected} (metric, arm) pairs")
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(data, theme_name))

    notes.append(f"{len(rows)} CSV rows, {len(images)} images.")
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
