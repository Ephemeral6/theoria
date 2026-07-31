"""fig02_bill_shape -- 图2 账单形状 / bill shape: the per-turn cost curve.

Theoria.md 3.2 figure 2, serving claim C2: *understanding is bought early and
spent late*. The picture is the shape of the bill, not its total.

What this script does, in order:

1. reads every declared cost ledger through ``sources`` (never a raw path, so
   every input lands in ``figures/SOURCES.sha256``);
2. splits the ledger into its **two record dialects** -- ``model_call`` rows
   (``usage`` present, carry ``total_cost_usd``) and ``env_step`` rows
   (``usage`` absent, carry ``action``/``failed``). A record that is neither
   raises: guessing a dialect is how a cost column silently becomes wrong;
3. rolls model-call cost up per ``(run_id, turn)`` -- retried calls share a
   ``step_idx`` and both attempts are billed, so a turn's cost is the **sum**
   over its attempts, not the last one;
4. writes ``csv/fig02_bill_shape.csv`` (the audit surface);
5. renders one figure per theme, two themes x svg+png = 4 images.

**The arm axis is a column, not a hard-coded triple.** ``arm`` comes from the
record. Model-call rows carry no ``arm`` field, so the arm for a run is taken
from that run's ``env_step`` rows (which do carry it) and, only if a run has no
``env_step`` row at all, from the ``run_id`` prefix -- ``run_id`` is
``<arm>-<game>-<model>-<hash8>``. Both derivations are computed and a
disagreement is reported in ``notes`` rather than reconciled. When
``theoria-arm/runs/ledger.jsonl`` appears, adding it is one entry in
``sources.py`` and zero changes here: see ``OPTIONAL_LEDGER_KEYS``.

Two warnings are *drawn*, per PLAN.md section 3:

* runs whose roll-up ``outcome`` is ``model_error`` or ``api_unusable`` are
  dashed, and the legend says why -- a curve that stops at turn 1 because the
  API died is not a cheap run;
* panel C is the step-failure strip. ``REPORT_V0`` records 27-45% of pilot
  steps failing outright, which makes E5 cost-per-action a price list rather
  than a skill measure. The reader meets that confound on the plate.

Nothing absent is drawn as zero: a run with no roll-up has no outcome (dotted,
labelled), and a run that took no action has no failure rate (labelled absent).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig02_bill_shape"

#: Required ledger, then every optional one. Order is fixed, so folding an
#: optional ledger in cannot reorder the records that were already there.
LEDGER_KEYS: tuple[str, ...] = ("pilot_ledger",)
OPTIONAL_LEDGER_KEYS: tuple[str, ...] = (
    "envelope_ledger_ar25",
    "envelope_ledger_g50t",
    "envelope_ledger_sk48",
    "envelope_ledger_tn36",
    "theoria_arm_ledger",
)

#: Per-run roll-ups. Used for exactly two things: the ``outcome`` column and
#: the endpoint cross-check. Never to patch a cost.
ROLLUP_KEYS: tuple[str, ...] = ("pilot_ar25", "pilot_g50t", "pilot_sk48", "pilot_tn36")

#: The capability ladder, which is v0's substitute for the missing Schema arm
#: (battery/DECISIONS.md D-B-004). Alphabetical order would put opus before
#: sonnet and break the ladder reading, so the order is declared. Anything not
#: on the ladder sorts after it, alphabetically -- still deterministic.
MODEL_LADDER: tuple[str, ...] = (
    "claude-haiku-4-5-20251001",
    "claude-sonnet-5",
    "claude-opus-5",
)

#: Outcomes that mean "this curve was cut short by the API, not by thrift".
OUTCOME_DASHED: frozenset[str] = frozenset({"model_error", "api_unusable"})

#: Cross-check tolerance, in USD. The roll-ups carry full float repr; the
#: ledger sum accumulates in a different order, so exact equality is not the
#: right test. One hundredth of a cent is.
COST_TOLERANCE_USD = 1e-6

CSV_HEADER = (
    "arm",
    "game_id",
    "model",
    "run_id",
    "turn",
    "cost_usd",
    "cum_cost_usd",
    "frac_of_run",
    "frac_of_spend",
    "failed_step",
    "outcome",
)

_MODEL_CALL_REQUIRED = ("run_id", "game_id", "model", "step_idx", "total_cost_usd")
_ENV_STEP_REQUIRED = ("run_id", "game_id", "model", "step_idx", "action")


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def _model_rank(model: str) -> tuple[int, str]:
    if model in MODEL_LADDER:
        return (MODEL_LADDER.index(model), "")
    return (len(MODEL_LADDER), model)


def _truthy(value) -> bool:
    """``failed`` has been seen as a bool; accept the string form too.

    Anything else is a value this script does not understand, so it raises
    rather than quietly deciding a failed step succeeded.
    """
    if value is None or value is False:
        return False
    if value is True:
        return True
    if isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "1", "yes"):
            return True
        if low in ("false", "0", "no", ""):
            return False
    if isinstance(value, int):
        return value != 0
    raise ValueError(f"unrecognised 'failed' value {value!r} in an env_step record")


def _classify(record: dict, origin: str) -> str:
    """``'model_call'`` or ``'env_step'``. Raises on anything else.

    The ledger mixes two dialects in one file and the discriminator is whether
    ``usage`` is present. A third dialect appearing (a folded-in envelope or
    theoria-arm ledger with a different schema) must stop the build, because
    the alternative is a cost curve built from fields that mean something else.
    """
    if not isinstance(record, dict):
        raise TypeError(f"{origin}: ledger record is {type(record).__name__}, not an object")
    if "usage" in record:
        missing = [k for k in _MODEL_CALL_REQUIRED if k not in record]
        if missing:
            raise ValueError(
                f"{origin}: record has 'usage' (model_call dialect) but is missing {missing}"
            )
        return "model_call"
    missing = [k for k in _ENV_STEP_REQUIRED if k not in record]
    if missing:
        raise ValueError(
            f"{origin}: record has no 'usage' (env_step dialect) but is missing {missing}; "
            "it parses into neither declared dialect -- declare the new dialect rather "
            "than letting it through"
        )
    return "env_step"


def _load_ledgers() -> tuple[list[dict], list[dict], list[str]]:
    """Every declared ledger, split by dialect. Returns ``(calls, steps, notes)``."""
    notes: list[str] = []
    calls: list[dict] = []
    steps: list[dict] = []
    present: list[str] = []
    absent: list[str] = []

    for key in LEDGER_KEYS:
        present.append(key)
    for key in OPTIONAL_LEDGER_KEYS:
        (present if sources.maybe_path(key) is not None else absent).append(key)

    for key in present:
        for record in sources.read_jsonl(key):
            kind = _classify(record, key)
            (calls if kind == "model_call" else steps).append(record)

    notes.append(
        f"ledgers read: {', '.join(present)} -- {len(calls)} model_call rows, "
        f"{len(steps)} env_step rows."
    )
    if absent:
        notes.append(
            "optional sources absent (declared in sources.py, named not silently "
            f"skipped): {', '.join(absent)}. The arm axis reads the record, so "
            "dropping any of them in changes no code here."
        )
    else:
        notes.append("every optional source was present and folded in.")
    return calls, steps, notes


def _load_rollups() -> dict[str, dict]:
    rollups: dict[str, dict] = {}
    for key in ROLLUP_KEYS:
        payload = sources.read_json(key)
        if not isinstance(payload, list):
            raise TypeError(f"{key}: expected a JSON list of per-run dicts")
        for row in payload:
            rid = row["run_id"]
            if rid in rollups and rollups[rid] != row:
                raise ValueError(f"{key}: conflicting roll-ups for {rid}")
            rollups[rid] = row
    return rollups


def extract() -> tuple[list[dict], list[str]]:
    """Per-run curve records, plus notes. No plotting, no writing."""
    calls, steps, notes = _load_ledgers()
    rollups = _load_rollups()

    # --- arm, per run: env_step rows carry it, model_call rows do not -------
    arm_from_steps: dict[str, set[str]] = {}
    for record in steps:
        arm_from_steps.setdefault(record["run_id"], set()).add(str(record.get("arm")))

    def arm_for(run_id: str) -> tuple[str, str]:
        """``(arm, provenance)``. env_step is authoritative; run_id is fallback."""
        prefix = run_id.split("-", 1)[0]
        seen = sorted(arm_from_steps.get(run_id, ()))
        if len(seen) == 1 and seen[0] != "None":
            return seen[0], "env_step"
        if len(seen) > 1:
            raise ValueError(f"{run_id}: env_step rows disagree on arm: {seen}")
        return prefix, "run_id-prefix"

    # --- per-turn cost: sum over attempts sharing a step_idx ---------------
    per_turn: dict[str, dict[int, float]] = {}
    meta: dict[str, dict] = {}
    for record in calls:
        rid = record["run_id"]
        turn = int(record["step_idx"])
        cost = record["total_cost_usd"]
        if cost is None:
            raise ValueError(f"{rid} turn {turn}: model_call row has no total_cost_usd")
        bucket = per_turn.setdefault(rid, {})
        bucket[turn] = bucket.get(turn, 0.0) + float(cost)
        if rid not in meta:
            meta[rid] = {"game_id": record["game_id"], "model": record["model"]}

    # --- action outcome per turn: env_step step_idx 0 is RESET, so turn t's
    #     action is the env_step with step_idx == t ------------------------
    failed_at: dict[str, dict[int, bool]] = {}
    action_steps: dict[str, dict[int, bool]] = {}
    for record in steps:
        rid = record["run_id"]
        turn = int(record["step_idx"])
        if turn == 0:
            continue  # the RESET observation, not an action a turn paid for
        flag = _truthy(record.get("failed"))
        failed_at.setdefault(rid, {})[turn] = flag
        action_steps.setdefault(rid, {})[turn] = flag

    # --- runs that spent nothing we can see -------------------------------
    step_only = sorted(set(arm_from_steps) - set(per_turn))
    if step_only:
        notes.append(
            f"{len(step_only)} run(s) have env_step rows but no model_call rows "
            f"({', '.join(r.split('-')[-1] for r in step_only)}): no cost is known "
            "for them, so no curve is drawn and no zero is substituted."
        )

    arm_provenance: set[str] = set()
    arm_disagreements: list[str] = []
    curves: list[dict] = []
    for rid in sorted(per_turn, key=lambda r: (meta[r]["game_id"], meta[r]["model"], r)):
        arm, provenance = arm_for(rid)
        arm_provenance.add(provenance)
        if provenance == "env_step" and arm != rid.split("-", 1)[0]:
            arm_disagreements.append(f"{rid}: env_step says {arm!r}, run_id prefix says {rid.split('-', 1)[0]!r}")

        turns = sorted(per_turn[rid])
        total = sum(per_turn[rid][t] for t in turns)
        if total <= 0.0:
            raise ValueError(f"{rid}: total cost is {total!r}; cannot normalise a run that spent nothing")
        max_turn = turns[-1]
        rollup = rollups.get(rid)
        outcome = rollup["outcome"] if rollup is not None else None

        cum = 0.0
        points: list[dict] = []
        for turn in turns:
            cost = per_turn[rid][turn]
            cum += cost
            observed = failed_at.get(rid, {})
            points.append(
                {
                    "turn": turn,
                    "cost_usd": cost,
                    "cum_cost_usd": cum,
                    "frac_of_run": turn / max_turn,
                    "frac_of_spend": cum / total,
                    # absent, not False, when the turn has no env_step row
                    "failed_step": observed.get(turn),
                }
            )

        actions = action_steps.get(rid, {})
        n_actions = len(actions)
        n_failed = sum(1 for v in actions.values() if v)
        curves.append(
            {
                "run_id": rid,
                "arm": arm,
                "arm_provenance": provenance,
                "game_id": meta[rid]["game_id"],
                "model": meta[rid]["model"],
                "outcome": outcome,
                "has_rollup": rollup is not None,
                "rollup_cost": (rollup or {}).get("cost_usd"),
                "ledger_cost": total,
                "max_turn": max_turn,
                "points": points,
                "actions": actions,
                "n_actions": n_actions,
                "n_failed": n_failed,
                # a run that took no action has no failure rate. Absent, not 0.
                "fail_rate": (n_failed / n_actions) if n_actions else None,
            }
        )

    notes.append(
        "arm derived from " + " and ".join(sorted(arm_provenance))
        + " (model_call rows carry no arm field; env_step rows do)."
    )
    if arm_disagreements:
        notes.append(
            "arm disagreement, reported not reconciled: " + "; ".join(sorted(arm_disagreements))
        )

    # --- endpoint cross-check: ledger sum vs roll-up cost_usd -------------
    checked = [c for c in curves if c["has_rollup"]]
    mismatched = [
        c for c in checked if abs(float(c["rollup_cost"]) - c["ledger_cost"]) > COST_TOLERANCE_USD
    ]
    if checked:
        worst = max(abs(float(c["rollup_cost"]) - c["ledger_cost"]) for c in checked)
        notes.append(
            f"endpoint cross-check: {len(checked)} of {len(curves)} runs have a roll-up; "
            f"ledger-summed cost agrees with roll-up cost_usd on {len(checked) - len(mismatched)} "
            f"of them (tolerance {COST_TOLERANCE_USD:g} USD, worst |diff| {worst:.3e})."
        )
    for c in mismatched:
        notes.append(
            f"MISMATCH (not reconciled) {c['run_id']}: ledger sum "
            f"{c['ledger_cost']:.6f} USD vs roll-up {float(c['rollup_cost']):.6f} USD."
        )
    no_rollup = [c["run_id"] for c in curves if not c["has_rollup"]]
    if no_rollup:
        notes.append(
            f"{len(no_rollup)} run(s) have no roll-up record, so their outcome is absent, "
            "not 'fine': drawn dotted and labelled as such in the legend."
        )
    absent_rate = [c["run_id"] for c in curves if c["fail_rate"] is None]
    if absent_rate:
        notes.append(
            f"{len(absent_rate)} run(s) took zero actions, so they have no step-failure "
            "rate; panel C labels them absent rather than 0%."
        )
    return curves, notes


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def csv_rows(curves: list[dict]) -> list[list]:
    """Rows sorted by ``(game_id, model, run_id, turn)`` -- literal, explicit."""
    ordered = sorted(curves, key=lambda c: (c["game_id"], c["model"], c["run_id"]))
    rows: list[list] = []
    for c in ordered:
        for p in sorted(c["points"], key=lambda q: q["turn"]):
            rows.append(
                [
                    c["arm"],
                    c["game_id"],
                    c["model"],
                    c["run_id"],
                    p["turn"],
                    theme.fmt_num(p["cost_usd"], places=6),
                    theme.fmt_num(p["cum_cost_usd"], places=6),
                    theme.fmt_num(p["frac_of_run"], places=6),
                    theme.fmt_num(p["frac_of_spend"], places=6),
                    # None -> "" via write_csv: the turn had no env_step row
                    theme.fmt_num(p["failed_step"]) if p["failed_step"] is not None else None,
                    c["outcome"],
                ]
            )
    return rows


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------


def _short_model(model: str) -> str:
    stem = model[len("claude-") :] if model.startswith("claude-") else model
    return stem.split("-", 1)[0]


def _linestyle(curve: dict) -> str:
    outcome = curve["outcome"]
    if outcome is None:
        return ":"  # no roll-up: outcome unknown, and unknown is not "fine"
    if outcome in OUTCOME_DASHED:
        return "--"  # cut short by the API, not by thrift
    return "-"


def _render(curves: list[dict], theme_name: str, n_absent_optional: int) -> list[str]:
    p = theme.apply_theme(theme_name)

    models = sorted({c["model"] for c in curves}, key=_model_rank)
    games = sorted({c["game_id"] for c in curves})
    arms = sorted({c["arm"] for c in curves})

    try:
        colours = theme.series_colours(theme_name, len(models), all_pairs=True)
    except ValueError:
        # More than three models: the all-pairs floors cannot be cleared, so
        # fall back deliberately. Marker (game) and linestyle still carry
        # identity, so colour is never alone.
        colours = theme.series_colours(theme_name, len(models), all_pairs=False)
    colour_of = {m: colours[i] for i, m in enumerate(models)}
    marker_of = {g: theme.series_marker(i) for i, g in enumerate(games)}

    fig = plt.figure(figsize=(11.0, 9.4))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.00, 1.30, 0.20])
    ax_abs = fig.add_subplot(gs[0, 0])
    ax_norm = fig.add_subplot(gs[0, 1])
    ax_strip = fig.add_subplot(gs[1, :])
    ax_pad = fig.add_subplot(gs[2, :])  # reserves room for the caveat text
    ax_pad.axis("off")

    plot_order = sorted(curves, key=lambda c: (_model_rank(c["model"]), c["game_id"], c["run_id"]))

    # --- panel A: absolute -------------------------------------------------
    for c in plot_order:
        xs = [q["turn"] for q in c["points"]]
        ys = [q["cum_cost_usd"] for q in c["points"]]
        every = max(1, (len(xs) + 5) // 6)
        ax_abs.plot(
            xs,
            ys,
            color=colour_of[c["model"]],
            linestyle=_linestyle(c),
            linewidth=1.3,
            marker=marker_of[c["game_id"]],
            markersize=3.4,
            markevery=every,
            alpha=0.92,
            solid_capstyle="round",
        )
    max_turn = max(c["max_turn"] for c in curves)
    ax_abs.set_xlim(0.0, max_turn + 1.0)
    ax_abs.set_ylim(bottom=0.0)
    ax_abs.set_title("A. absolute: cumulative model cost", loc="left")
    ax_abs.set_xlabel("turn (model-call / env-step index)")
    ax_abs.set_ylabel("cumulative cost (USD)")

    model_handles = [
        Line2D([], [], color=colour_of[m], linewidth=1.6, label=m) for m in models
    ]
    outcome_handles = [
        Line2D([], [], color=p["ink_secondary"], linewidth=1.4, linestyle="-",
               label="ran to budget"),
        Line2D([], [], color=p["ink_secondary"], linewidth=1.4, linestyle="--",
               label="model_error / api_unusable: cut short by the API, not cheap"),
        Line2D([], [], color=p["ink_secondary"], linewidth=1.4, linestyle=":",
               label="no roll-up record: outcome unknown, not 'fine'"),
    ]
    leg_models = ax_abs.legend(
        handles=model_handles,
        loc="upper left",
        title="colour: model ladder (substitute for the missing Schema arm)",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 1.5,
        title_fontsize=theme.BASE_FONT_SIZE - 1.5,
    )
    leg_models.get_title().set_color(p["ink_secondary"])

    # --- panel B: normalised ----------------------------------------------
    # The reference diagonal must not reuse any of the three outcome line
    # styles, or "flat spend" would read as an outcome.
    _REFERENCE_STYLE = (0, (5, 2, 1, 2))
    ax_norm.plot(
        [0.0, 1.0],
        [0.0, 1.0],
        color=p["muted"],
        linewidth=0.9,
        linestyle=_REFERENCE_STYLE,
        zorder=0,
    )
    for c in plot_order:
        xs = [0.0] + [q["frac_of_run"] for q in c["points"]]
        ys = [0.0] + [q["frac_of_spend"] for q in c["points"]]
        every = max(1, (len(xs) + 5) // 6)
        ax_norm.plot(
            xs,
            ys,
            color=colour_of[c["model"]],
            linestyle=_linestyle(c),
            linewidth=1.3,
            marker=marker_of[c["game_id"]],
            markersize=3.4,
            markevery=every,
            alpha=0.92,
        )
    ax_norm.set_xlim(0.0, 1.02)
    ax_norm.set_ylim(0.0, 1.02)
    ax_norm.set_title("B. normalised: the shape E2's front-load index reads", loc="left")
    ax_norm.set_xlabel("fraction of run (turn / final turn)")
    ax_norm.set_ylabel("fraction of total spend")
    game_handles = [
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker=marker_of[g],
               markersize=4.5, linestyle="none", label=g)
        for g in games
    ] + [Line2D([], [], color=p["muted"], linewidth=0.9, linestyle=_REFERENCE_STYLE,
                label="flat spend (reference)")]
    leg_games = ax_norm.legend(
        handles=game_handles,
        loc="lower right",
        title="marker: game (colour is never the only channel)",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 1.5,
        title_fontsize=theme.BASE_FONT_SIZE - 1.5,
    )
    leg_games.get_title().set_color(p["ink_secondary"])
    ax_norm.add_artist(leg_games)
    # The outcome key lives here because panel B's upper-left is the one large
    # empty region on the plate; on panel A it would sit on top of the curves.
    leg_outcome = ax_norm.legend(
        handles=outcome_handles,
        loc="upper left",
        title="line style (both panels): how the run ended",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 2,
        title_fontsize=theme.BASE_FONT_SIZE - 2,
    )
    leg_outcome.get_title().set_color(p["ink_secondary"])

    # --- panel C: the confound, met before the curve is believed ----------
    strip_order = sorted(curves, key=lambda c: (c["game_id"], _model_rank(c["model"]), c["run_id"]))
    labels: list[str] = []
    rate_x = max_turn + 1.4
    for row, c in enumerate(strip_order):
        turns = sorted(c["actions"])
        ok = [t for t in turns if not c["actions"][t]]
        bad = [t for t in turns if c["actions"][t]]
        if turns:
            ax_strip.plot(
                [turns[0], turns[-1]],
                [row, row],
                color=p["grid"],
                linewidth=0.8,
                zorder=0,
            )
        if ok:
            ax_strip.plot(
                ok, [row] * len(ok), linestyle="none", marker="|", markersize=6.0,
                markeredgewidth=1.2, color=p["muted"], zorder=2,
            )
        if bad:
            ax_strip.plot(
                bad, [row] * len(bad), linestyle="none", marker="|", markersize=8.0,
                markeredgewidth=1.6, color=theme.STATUS["critical"], zorder=3,
            )
        if c["fail_rate"] is None:
            rate_text = "no action taken -- rate absent"
            rate_colour = p["muted"]
        else:
            rate_text = f"{c['n_failed']}/{c['n_actions']} = {c['fail_rate'] * 100:.0f}%"
            rate_colour = theme.STATUS["critical"] if c["fail_rate"] >= 0.27 else p["ink_secondary"]
        ax_strip.text(
            rate_x, row, rate_text, ha="left", va="center",
            fontsize=theme.BASE_FONT_SIZE - 3, color=rate_colour,
        )
        arm_tag = f"{c['arm']} " if len(arms) > 1 else ""
        labels.append(
            f"{arm_tag}{c['game_id'].split('-')[0]} {_short_model(c['model'])} "
            f"{c['run_id'].split('-')[-1]}"
        )

    for row in range(1, len(strip_order)):
        if strip_order[row]["game_id"] != strip_order[row - 1]["game_id"]:
            ax_strip.axhline(row - 0.5, color=p["axis"], linewidth=0.6, zorder=1)

    ax_strip.set_yticks(list(range(len(strip_order))))
    ax_strip.set_yticklabels(labels, fontsize=theme.BASE_FONT_SIZE - 3)
    # One blank lane at the bottom so the tick key sits off the data.
    ax_strip.set_ylim(len(strip_order) + 0.9, -0.7)
    ax_strip.set_xlim(0.0, max_turn + 9.5)
    # Ticks stop where the data stops: the right-hand gutter carries the rate
    # column, not turns, and a tick out there would claim otherwise.
    ax_strip.set_xticks(list(range(0, max_turn + 1, 5)))
    ax_strip.axvline(max_turn + 0.8, color=p["axis"], linewidth=0.6, zorder=1)
    ax_strip.grid(False)
    ax_strip.set_xlabel("turn (one tick per environment action)")
    ax_strip.set_title(
        "C. the confound first: environment actions per turn, failures in red "
        "(REPORT_V0: 27-45% of pilot steps failed outright)",
        loc="left",
    )
    strip_handles = [
        Line2D([], [], color=p["muted"], linestyle="none", marker="|", markersize=6.0,
               markeredgewidth=1.2, label="action accepted"),
        Line2D([], [], color=theme.STATUS["critical"], linestyle="none", marker="|",
               markersize=8.0, markeredgewidth=1.6, label="action failed outright"),
    ]
    ax_strip.legend(
        handles=strip_handles,
        loc="lower right",
        fontsize=theme.BASE_FONT_SIZE - 2,
        ncols=2,
    )

    fig.suptitle(
        "Figure 2 -- bill shape: the per-turn cost curve (C2: bought early, spent late)"
    )
    theme.caveat(
        fig,
        "Two of the three arms are absent, and absence is not zero: there is no Schema arm "
        "(baseline-arms/SCHEMA_LOCATE.md) and the theoria arm has no cost ledger yet, so the "
        "model ladder stands in for it (battery/DECISIONS.md D-B-004, weaker by REPORT_V0's own "
        "note). Cost is summed over retried calls sharing a turn. Panel C is the price-list "
        "confound: with 27-45% of steps failing, E5 cost-per-action tracks token pricing, not "
        f"skill. {n_absent_optional} optional ledger(s) declared and absent -- named in "
        "figures/sources.py, not silently dropped.",
        theme=theme_name,
    )
    return theme.save(fig, NAME, theme_name)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    curves, notes = extract()
    rows = csv_rows(curves)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    n_absent_optional = sum(1 for k in OPTIONAL_LEDGER_KEYS if sources.maybe_path(k) is None)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(curves, theme_name, n_absent_optional))

    notes.append(
        f"{len(curves)} curves drawn over {len({c['game_id'] for c in curves})} games, "
        f"{len({c['model'] for c in curves})} models, {len({c['arm'] for c in curves})} arm(s); "
        f"{len(rows)} CSV rows."
    )
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
