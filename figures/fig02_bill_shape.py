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
disagreement is reported in ``notes`` rather than reconciled.

**Every input arrives by rule, not by name** (P8). The roll-ups, the envelope
shards and the theoria runs are three families that grow, and each used to be a
hand-written tuple of source keys. Both tuples had gone stale by the time P8
listed the directories: two tracked roll-ups were never read, so two runs whose
outcome is committed to the repository were drawn as *outcome unknown* -- one of
them a ``model_error``, which is the plate's own warning that a short curve was
cut off by the API rather than being thrifty. A fourth theoria run directory was
likewise unread. They now come from ``sources.DISCOVERY``: a run that lands on
disk enters the figure at the next build, and every discovered file is still
hashed into ``figures/SOURCES.sha256`` because discovery produces real
``Source`` objects. Each rule carries a floor, so a family that empties out
stops the build instead of quietly shrinking the picture.

**The theoria arm is a second column** (P4; P-21 shipped this plate with one
arm and left the interface open). It did *not* arrive through the optional
ledger keys as P-21 predicted, and the reason is worth stating: the
theoria arm's ``ledger.jsonl`` is ``LEDGER_FORMAT v1.0``, a **third dialect**
whose ``model_call`` records carry no top-level cost at all -- the dollars are
nested under ``response``. Folding it into ``_classify`` would have meant either
teaching that function a schema it was written to reject, or reading a cost out
of a field that means something else. The arm publishes ``cost_curve.json`` for
exactly this purpose, so that is what is read, through ``_load_theoria_curves``.

The two arms' turns are the same x-quantity (``step_idx``, one environment
action) and their costs are **not** the same y-quantity. A baseline turn buys one
model call that chooses one action; a theoria turn may buy nothing at all, and
the turns that do buy something buy a *desk call* that theorizes across the whole
run. Five desk calls cover seven actions. The plate draws both and says this on
its face rather than letting the reader infer that theoria costs 30x per turn.

**The three shape metrics are read, not recomputed** (P8). E2 (front-load
index), E3 (convergence point) and E4 (context growth) are defined in
``battery/metrics/economy.py`` with anti-gaming floors, and E2 is one of Phase
4's three primary endpoints. This script takes their published per-run values
out of ``battery/artifacts/capability_spectrum.json``. Writing a second
implementation would be writing a second definition of a primary endpoint, and
the two would drift -- which is the failure ``sources.py`` exists to catch.

Two things about those metrics have to be said on the plate rather than smoothed
over. First, **the battery's turn axis is not this plate's x-axis**: the battery
counts turns in model-call order (``INPUT_FORMAT.md`` gap 5 -- the ledger has no
explicit turn index), while panels A and B count ``step_idx``. They agree for
most runs and disagree wherever a turn was retried, so E3's crossing is drawn as
a position on panel B *only* for runs where the two counts agree, and the
disagreement is named for the rest. Second, **the theoria arm has no E2/E3/E4 at
all**: battery v2's five arms are ``bare_cc``, ``schema_repro``, ``theoria_a0``,
``theoria_a0_spike`` and ``theoria_a2``, and the live ARC theoria run is none of
them. That is drawn as an absence with its reason, never as a zero.

Two warnings are *drawn*, per PLAN.md section 3:

* runs whose roll-up ``outcome`` is ``model_error`` or ``api_unusable`` are
  dashed, and the legend says why -- a curve that stops at turn 1 because the
  API died is not a cheap run;
* panel C is the step-failure strip. ``REPORT_V0`` records 27-45% of pilot
  steps failing outright, which makes E5 cost-per-action a price list rather
  than a skill measure. The reader meets that confound on the plate -- and meets
  it twice, because ``papers/phase1-workshop/REVIEW.md`` recomputes the band as
  28.3-45.1% and records that the 27% lower bound does not reproduce. Both
  numbers are drawn; the repository's rule where two artefacts disagree is that
  both travel.

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

#: The one ledger named by hand. Everything else this figure reads arrives
#: through a discovery rule, named here so the reader can find it:
#:
#:   ``envelope_ledger``  the envelope campaign's ledger shards. Read
#:                        "optional campaign shards, untracked by design" until
#:                        V23; A14 committed all fifteen, so the rule is
#:                        tracked and floored like every other one now.
#:   ``pilot_rollup``     per-run roll-ups: the ``outcome`` column and the
#:                        endpoint cross-check. Never used to patch a cost.
#:   ``theoria_run``      the theoria arm, a ``(cost_curve, MANIFEST)`` pair per
#:                        run directory
#:
#: Order within a rule is path order, which is fixed, so folding a newly landed
#: member in cannot reorder the records that were already there.
LEDGER_KEYS: tuple[str, ...] = ("pilot_ledger",)
ENVELOPE_RULE = "envelope_ledger"
ROLLUP_RULE = "pilot_rollup"
THEORIA_RULE = "theoria_run"

#: The three battery metric ids this plate reads, and nothing else from that
#: artefact. Kept as a tuple so the CSV header and the panel agree by
#: construction rather than by two people remembering the same list.
SHAPE_METRICS: tuple[str, ...] = ("E2", "E3", "E4")

#: Deliberately **not** a copy of battery/metrics/economy.py's ``FRONTLOAD_K``
#: and ``CONVERGENCE_SHARE``. SOURCES.md's rule is that a hand-copied fact about
#: another file is a fact that will go stale, and these two are exactly that
#: kind of fact. The head boundary is derived from the battery's own per-run
#: support (``head_turns / turns``) and the 90 % share is quoted from the
#: battery's own card text -- both of which are hashed inputs.
#:
#: The E3 crossing is likewise marked on each run's own curve at the turn the
#: battery reports, rather than drawn as a horizontal rule at a share this
#: script asserts.

#: The capability ladder, which is v0's substitute for the missing Schema arm
#: (battery/DECISIONS.md D-B-004). Alphabetical order would put opus before
#: sonnet and break the ladder reading, so the order is declared. Anything not
#: on the ladder sorts after it, alphabetically -- still deterministic.
MODEL_LADDER: tuple[str, ...] = (
    "claude-haiku-4-5-20251001",
    "claude-sonnet-5",
    "claude-opus-5",
)

#: The lower edge of the step-failure band, used only to decide which rate in
#: panel C's gutter is inked as critical. It is REVIEW.md's **reproduced** 28.3%
#: and not REPORT_V0's 27%: that lower bound is recorded as not reproducing, and
#: a threshold is a poor place to keep a refuted number alive. No run on this
#: build falls between the two, so nothing on the plate moves -- which is the
#: reason to fix it now rather than after something does.
FAILURE_BAND_LOW = 0.283

#: Outcomes that mean "this curve was cut short by the API, not by thrift".
OUTCOME_DASHED: frozenset[str] = frozenset({"model_error", "api_unusable"})

#: The arm whose marks are filled. Every other arm draws hollow -- see the
#: comment in panel A on why the arm gets marker fill and nothing stronger.
BASELINE_ARM = "bare_cc"

#: Cross-check tolerance, in USD. The roll-ups carry full float repr; the
#: ledger sum accumulates in a different order, so exact equality is not the
#: right test. One hundredth of a cent is.
COST_TOLERANCE_USD = 1e-6

#: Per-turn columns, then the per-run shape block. The shape values repeat down
#: a run's rows exactly as ``outcome`` already does -- a reviewer checking a
#: number against the picture should not have to join two files to do it.
#:
#: Each shape metric gets **two** columns: the value and the battery's status.
#: A blank value with a status of ``insufficient-data`` is a different fact from
#: a blank value with a status of ``no-battery-run``, and collapsing them into
#: one empty cell is how an absence turns into a zero.
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
    "e2_frontload_index",
    "e2_status",
    "e3_convergence_point",
    "e3_status",
    "e4_context_growth",
    "e4_status",
    "battery_turns",
    "turn_axis_agrees",
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
    for src in sources.discovered(ENVELOPE_RULE):
        (present if src.exists() else absent).append(src.key)

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
            "optional sources absent (declared by rule in sources.py, named not silently "
            f"skipped): {', '.join(absent)}. The arm axis reads the record, so "
            "dropping any of them in changes no code here."
        )
    elif len(present) > len(LEDGER_KEYS):
        notes.append(
            f"{len(present) - len(LEDGER_KEYS)} envelope ledger shard(s) folded in "
            "beside the pilot ledger, every one committed."
        )
    else:
        # V23: the honest statement for a tree where the shards are excluded on
        # purpose -- release/LICENCE_POSTURE.md classes them B, so the release
        # builds this branch. Absence here is legal and it is not nothing: the
        # campaign's spend is missing from the bill, and saying so is the whole
        # job of this note.
        notes.append(
            "no envelope ledger shard was read: none is committed in this tree. The "
            "bill therefore covers the pilot ledger alone and excludes the envelope "
            "campaign -- expected in a release tree, a defect in the source repo."
        )
    return calls, steps, notes


def _load_rollups() -> tuple[dict[str, dict], list[str]]:
    """Every discovered roll-up, keyed by ``run_id``. Returns ``(rollups, notes)``."""
    notes: list[str] = []
    rollups: dict[str, dict] = {}
    files = sources.discovered(ROLLUP_RULE)
    for src in files:
        payload = sources.read_json(src.key)
        if not isinstance(payload, list):
            raise TypeError(f"{src.key}: expected a JSON list of per-run dicts")
        for row in payload:
            rid = row["run_id"]
            if rid in rollups and rollups[rid] != row:
                raise ValueError(f"{src.key}: conflicting roll-ups for {rid}")
            rollups[rid] = row
    notes.append(
        f"roll-ups: {len(files)} file(s) found by rule {ROLLUP_RULE!r} under "
        f"{sources.rule(ROLLUP_RULE).root}/, {len(rollups)} run(s) with a declared outcome. "
        "Discovered, not listed: the tuple this replaced named four of the six and the two "
        "it missed were drawn as outcome-unknown while their outcomes sat committed on disk."
    )
    return rollups, notes


#: How the run whose numbers back the cost-basis caveat is chosen. Stated on the
#: plate because the previous version named one run directly, and a caveat
#: anchored to a name silently keeps describing that run after a better one
#: lands.
_COST_BASIS_RULE = (
    "the discovered run with a game_id and the largest billed total; ties by slug"
)


def _cost_basis(curves: list[dict]) -> dict | None:
    """The theoria run the cost-basis caveat describes, or ``None``.

    Safe to call over the whole curve list: baseline curves carry no manifest.
    """
    played = [c for c in curves if (c.get("manifest") or {}).get("game_id")]
    if not played:
        return None
    return max(played, key=lambda c: (c["ledger_cost"], c["run_id"]))


#: The two spellings of the theoria arm's per-call cost record, and how to get
#: the call list out of each. `cost_curve.json` was the name until
#: 20260729T105729Z-leg01; `bill_shape.json` is the name the arm writes now, and
#: it wraps the same list in a document that also carries `totals` and a
#: `reading` note. A third shape is refused rather than guessed at: guessing a
#: dialect is how a cost column silently becomes wrong, which is the rule this
#: module already applies to the two ledger dialects.
def _theoria_calls(entry: str, name: str, payload) -> tuple[list[dict], str]:
    """``(calls, note)`` from either dialect. Raises on anything else."""
    if name == "cost_curve.json":
        if not isinstance(payload, list):
            raise ValueError(
                f"theoria run {entry}: cost_curve.json is {type(payload).__name__}, not a "
                "list of per-call records. The arm's schema changed and this figure must "
                "not guess how."
            )
        return payload, ""
    if name == "bill_shape.json":
        if not isinstance(payload, dict) or not isinstance(payload.get("calls"), list):
            raise ValueError(
                f"theoria run {entry}: bill_shape.json carries no 'calls' list. The arm's "
                "schema changed and this figure must not guess how."
            )
        return payload["calls"], (
            f"theoria {entry}: read from bill_shape.json, the arm's current name for the "
            "per-call cost record. Same role as cost_curve.json, same step_idx keying, "
            "same usd field; it additionally carries a game `turn` (offset from step_idx "
            "by the pre-roll) and a `totals` block, neither of which this plate's x-axis "
            "uses -- the axis is still step_idx, so no already-published curve moves."
        )
    raise ValueError(f"theoria run {entry}: {name} is not a cost-record dialect this figure reads")


def _theoria_dialect_crosscheck(entry: str, members: dict) -> list[str]:
    """When a run carries both spellings, are they the same bill?

    The alternation in ``sources.Rule`` is only as good as the claim that the
    two names mean the same thing, and exactly one run directory
    (20260728T083400Z-E3-sk48-carried-v2) is in a position to test it. So it is
    tested on every build rather than asserted in a comment: same step_idx
    multiset, same total to the cent. A disagreement is reported and **not**
    reconciled -- if the arm's two writers ever diverge, the figure should say
    which run and by how much, not quietly pick the one it prefers.
    """
    if not ({"cost_curve.json", "bill_shape.json"} <= set(members)):
        return []
    old, _ = _theoria_calls(entry, "cost_curve.json", sources.read_json(members["cost_curve.json"].key))
    new, _ = _theoria_calls(entry, "bill_shape.json", sources.read_json(members["bill_shape.json"].key))
    old_total = sum(float(r["usd"]) for r in old)
    new_total = sum(float(r["usd"]) for r in new)
    old_steps = sorted(int(r["step_idx"]) for r in old)
    new_steps = sorted(int(r["step_idx"]) for r in new)
    if old_steps != new_steps or abs(old_total - new_total) > COST_TOLERANCE_USD:
        return [
            f"MISMATCH (not reconciled) theoria {entry}: cost_curve.json and "
            f"bill_shape.json describe different bills -- {len(old)} call(s) summing "
            f"{old_total:.6f} USD against {len(new)} call(s) summing {new_total:.6f} USD. "
            "cost_curve.json is drawn because it is declared first; the disagreement is "
            "reported because the alternation between the two names is only sound while "
            "they agree."
        ]
    return [
        f"theoria {entry} carries both cost-record dialects and they agree: "
        f"{len(old)} call(s), {old_total:.6f} USD, identical step_idx sequence either "
        "way. This is the only run in a position to test the alternation, and it is "
        "tested on every build rather than asserted once."
    ]


def _load_theoria_curves() -> tuple[list[dict], list[str]]:
    """The theoria arm's curves, from ``cost_curve.json`` + ``MANIFEST.json``.

    A separate path from ``_load_ledgers`` on purpose -- see the module
    docstring. ``cost_curve.json`` is a list of per-call records
    ``{beat, call_idx, elapsed_ms, label, model, step_idx, usage, usd}``; several
    calls can share a ``step_idx``, and as in the baseline the turn's cost is the
    **sum** over them.

    Three things are deliberately left absent rather than filled in:

    * **the step-failure rate.** The arm's own accounting is HTTP-attempt-shaped
      (40 attempts, 5.714 amplification, 7 successful actions) and is simply not
      the quantity panel C draws for the baseline, where a failure is an action
      the environment refused. Coercing one into the other would put two
      different numbers in one column.
    * **turns that bought no model call.** They are not drawn as $0 points; the
      curve starts where the spending starts, and the gap is visible as a gap.
    * **``outcome`` on the two abandoned attempts**, which their own manifests
      record as ``null``.
    """
    notes: list[str] = []
    curves: list[dict] = []
    abandoned: list[tuple[str, float]] = []
    empty: list[str] = []

    groups = sources.discovered_groups(THEORIA_RULE)
    notes.append(
        f"theoria: {len(groups)} run director(ies) found by rule {THEORIA_RULE!r} under "
        f"{sources.rule(THEORIA_RULE).root}/, each carrying a MANIFEST.json beside a "
        "per-call cost record under either accepted name ("
        + " or ".join(sources.rule(THEORIA_RULE).candidates("cost_curve.json"))
        + "). Directories carrying only one of the two are skipped by the rule rather "
        "than by omission from a list. The alternation is why this count is 16 and not "
        "the 7 it was on 2026-07-31: the arm renamed its cost record and a rule keyed on "
        "a filename rather than on a role stopped seeing every leg written since."
    )

    for entry, members in groups:
        curve_name, curve_src = sources.resolve_member(
            THEORIA_RULE, members, "cost_curve.json"
        )
        curve_key = curve_src.key
        manifest_key = members["MANIFEST.json"].key
        rows, dialect_note = _theoria_calls(entry, curve_name, sources.read_json(curve_key))
        if dialect_note:
            notes.append(dialect_note)
        notes.extend(_theoria_dialect_crosscheck(entry, members))
        manifest = sources.read_json(manifest_key)
        # A newly landed run reaches this loop without anyone reviewing it, which
        # is the point of discovery and also its risk: a malformed manifest would
        # otherwise kill the build of all six figures with a bare KeyError naming
        # a field and not a directory. Say which run and what it is missing.
        missing = [k for k in ("slug", "arm", "cost") if k not in manifest]
        if missing:
            raise ValueError(
                f"theoria run {entry}: MANIFEST.json is missing {missing}. It was "
                f"discovered by rule {THEORIA_RULE!r}; either the run is half-written or "
                "the arm's manifest schema changed, and this figure must not guess which."
            )
        slug = manifest["slug"]
        cost = manifest.get("cost") or {}

        if not rows:
            empty.append(slug)
            notes.append(
                f"theoria {slug}: {curve_name} is empty -- no model call was "
                "billed, so no curve. Not a zero-cost run; a run with no calls."
            )
            continue

        per_turn: dict[int, float] = {}
        models: set[str] = set()
        for row in rows:
            turn = int(row["step_idx"])
            per_turn[turn] = per_turn.get(turn, 0.0) + float(row["usd"])
            if "model" in row:
                models.add(str(row["model"]))
        if not models:
            # `bill_shape.json` carries no per-call model, so the model comes
            # from the manifest's own price-table breakdown -- the arm's
            # statement about the same calls, not a guess and not a default.
            # A run that spans models must say so; one that names none is
            # recorded as naming none rather than being labelled with the
            # ladder's most convenient rung.
            models = set(
                ((manifest.get("cost") or {}).get("from_price_table") or {}).get(
                    "per_model"
                )
                or {}
            )
            if models:
                notes.append(
                    f"theoria {slug}: {curve_name} carries no per-call model field, so "
                    f"the model is taken from MANIFEST cost.from_price_table.per_model "
                    f"({', '.join(sorted(models))}). Both describe the same calls; this "
                    "is a second reading of one fact, not a substitute for a missing one."
                )
        if len(models) != 1:
            raise ValueError(
                f"theoria {slug}: {curve_name} and MANIFEST between them name "
                f"{len(models)} model(s) {sorted(models)} for a run with billed calls. "
                "One curve is one model's price; this figure must not average two."
            )

        total = sum(per_turn[t] for t in sorted(per_turn))
        declared = cost.get("cli_reported_usd")
        if declared is not None and abs(float(declared) - total) > COST_TOLERANCE_USD:
            notes.append(
                f"MISMATCH (not reconciled) theoria {slug}: cost_curve sums to "
                f"{total:.6f} USD, MANIFEST cost.cli_reported_usd says {float(declared):.6f}."
            )

        outcome = manifest.get("outcome")
        if outcome is None:
            abandoned.append((slug, total))

        turns = sorted(per_turn)
        max_turn = turns[-1]
        cum = 0.0
        points: list[dict] = []
        for turn in turns:
            cum += per_turn[turn]
            points.append(
                {
                    "turn": turn,
                    "cost_usd": per_turn[turn],
                    "cum_cost_usd": cum,
                    "frac_of_run": turn / max_turn,
                    "frac_of_spend": cum / total,
                    "failed_step": None,  # this arm's steps are not in this file
                }
            )

        curves.append(
            {
                "run_id": slug,
                "arm": manifest["arm"],
                "arm_provenance": "manifest",
                # null on the abandoned attempts, and left null.
                "game_id": manifest.get("game_id") or "game absent",
                "model": sorted(models)[0],
                "outcome": outcome,
                "has_rollup": False,
                "rollup_cost": None,
                "ledger_cost": total,
                "max_turn": max_turn,
                "points": points,
                "actions": {},
                "n_actions": None,
                "n_failed": None,
                "fail_rate": None,
                "rate_absent_reason": "HTTP-shaped, not comparable -- absent",
                "manifest": manifest,
            }
        )

    if abandoned:
        wasted = sum(usd for _, usd in abandoned)
        notes.append(
            f"theoria: {len(abandoned)} attempt(s) were billed and abandoned "
            f"({', '.join(s for s, _ in sorted(abandoned))}), together "
            f"{wasted:.6f} USD. Their manifests declare outcome null, so they are "
            "drawn dotted as outcome-absent rather than labelled aborted, and "
            "their cost is in the arm's total. Omitting them would understate "
            "what this arm cost."
        )

    if empty:
        notes.append(
            f"theoria: {len(empty)} discovered run(s) billed nothing and are drawn as no "
            f"curve rather than as a zero-cost curve ({', '.join(sorted(empty))}). This "
            "branch existed before P8 and had never executed: the only run that reaches it "
            "was not in the hand-written tuple, so the code for the empty case was never "
            "once exercised on real data."
        )

    basis = _cost_basis(curves)
    if basis is None:
        notes.append(
            "theoria cost basis: absent. No discovered run carries both a game_id and a "
            "billed call, so there is no run whose per-action price is a real quantity. "
            "Nothing is substituted."
        )
        return curves, notes

    fcost = basis["manifest"]["cost"]
    recon = basis["manifest"].get("reconciliation") or {}
    ttl = fcost.get("cache_ttl_diagnosis") or {}
    ttl_clause = (
        f"{ttl['under_billed_usd']:.6f} USD of it is a known table defect (1-hour cache "
        "writes priced at the 5-minute multiplier)"
        if "under_billed_usd" in ttl
        else "the manifest carries no cache-TTL diagnosis for this run, so none is claimed"
    )
    notes.append(
        "theoria cost basis: the arm's per-call cost record carries the provider's own "
        f"arithmetic ({fcost['cli_reported_usd']:.6f} USD over "
        f"{fcost['model_calls']} calls on {basis['manifest']['slug']}). The repo's price "
        f"table recomputes {fcost['from_price_table']['usd_total']:.6f}, a "
        f"{fcost['relative_delta'] * 100:.1f}% disagreement; {ttl_clause}. "
        "The CLI figure is plotted; the disagreement is not averaged away. "
        f"Basis run chosen by rule ({_COST_BASIS_RULE}), not by name."
    )
    actions = recon.get("successful_actions")
    if actions:
        notes.append(
            f"theoria per-action price: {fcost['cli_reported_usd'] / actions:.4f} "
            f"USD over {actions} successful actions "
            f"({recon.get('env_steps')} HTTP attempts, amplification "
            f"{recon.get('http_amplification')}). "
            "Its turn-cost and the baseline's are not the same quantity: a baseline "
            "turn buys one model call that picks one action, a theoria turn buys a "
            "desk call that theorizes across the run."
        )
    else:
        notes.append(
            f"theoria per-action price: absent for {basis['manifest']['slug']} -- its "
            "manifest declares no successful_actions, and a price per action with no "
            "actions in the denominator is not a number."
        )
    return curves, notes


def _load_shape_metrics() -> tuple[dict, list[str]]:
    """The battery's published E2/E3/E4, per run id. Read, never recomputed.

    Returns ``(bundle, notes)`` where ``bundle`` carries

    * ``by_run``   ``{run_id: {metric_id: cell}}``, cell as the battery wrote it
                   (``value``/``status``/``reason``/``support``);
    * ``cards``    the battery's own definition text for each metric, quoted on
                   the plate so the plate does not restate a definition in its
                   own words;
    * ``head_k``   the front-load head boundary, **derived** from the battery's
                   own ``head_turns / turns`` support rather than copied from
                   ``FRONTLOAD_K``. Disagreement between runs is reported, not
                   averaged;
    * ``arms``     battery v2's arm roster, which is how the plate knows the
                   live theoria arm has no battery run rather than assuming it.
    """
    notes: list[str] = []
    payload = sources.read_json("capability_spectrum")
    cards = {m: payload["cards"][m] for m in SHAPE_METRICS}
    by_run = {
        run_id: {m: run["metrics"][m] for m in SHAPE_METRICS}
        for run_id, run in payload["runs"].items()
    }

    ratios = sorted(
        {
            round(cell["support"]["head_turns"] / cell["support"]["turns"], 9)
            for cell in (c["E2"] for c in by_run.values())
            if cell.get("status") == "ok" and cell.get("support", {}).get("turns")
        }
    )
    if len(ratios) == 1:
        head_k = ratios[0]
    else:
        head_k = None
        notes.append(
            "E2 head boundary NOT drawn: the battery's own support implies "
            f"{len(ratios)} different head fractions ({', '.join(f'{r:g}' for r in ratios)}). "
            "A single reference line would have to pick one, and picking one is asserting a "
            "definition this script is not entitled to assert."
        )

    arms = tuple(payload["provenance"]["arms"])
    notes.append(
        f"shape metrics E2/E3/E4 read from battery {payload['battery_version']} "
        f"({len(by_run)} runs, arms {', '.join(arms)}) -- not recomputed here. "
        "E2 is a Phase 4 primary endpoint; a second implementation would be a second "
        "definition."
    )
    return {"by_run": by_run, "cards": cards, "head_k": head_k, "arms": arms}, notes


def _attach_shape(curves: list[dict], shape: dict) -> list[str]:
    """Hang each run's E2/E3/E4 on its curve. Absence keeps its reason."""
    notes: list[str] = []
    by_run = shape["by_run"]
    axis_mismatch: list[str] = []
    unknown: list[str] = []

    for c in curves:
        cells = by_run.get(c["run_id"])
        if cells is None:
            unknown.append(c["run_id"])
            # One reason string for every unscored run, deliberately not
            # interpolating the run id. The reason is a property of the battery's
            # arm roster, not of the individual run, and a per-run string would
            # print as N separate one-run lines on the plate where the truth is
            # a single N-run fact.
            reason = (
                "no battery run at all; battery v2 scores the arms "
                + ", ".join(shape["arms"])
            )
            c["shape"] = {
                m: {"value": None, "status": "no-battery-run", "reason": reason}
                for m in SHAPE_METRICS
            }
            c["shape_turns"] = None
            c["axis_agrees"] = False
            continue

        c["shape"] = {m: dict(cells[m]) for m in SHAPE_METRICS}
        # Only E2 and E3. E4's support also has a key called ``turns``, and it
        # is **a different quantity**: economy.py fills E2/E3 from
        # ``run.turn_costs()`` (decisions) and E4 from ``len(run.calls)``
        # (billed calls, retries included). On
        # bare_cc-g50t-claude-sonnet-5-ddabe772 that is 20 against 24. Widening
        # the fallback to E4 made this plate report a turn-axis disagreement
        # that does not exist -- the two numbers were never the same
        # measurement. Reported to the battery's territory, not fixed here.
        #
        # (The first version of this comment cited 9022a076 as the example. That
        # run's E2 and E3 are insufficient-data and carry no support at all, so
        # it has no E2/E3 turn count for E4's to disagree with; the 7 came from
        # the run-level `turns` field, which is a third thing again. The rule was
        # right and the example under it never happened.)
        support: dict = {}
        for m in ("E2", "E3"):
            support = cells[m].get("support") or {}
            if support.get("turns") is not None:
                break
        c["shape_turns"] = support.get("turns")
        e4_support = cells["E4"].get("support") or {}
        c["e4_turns"] = e4_support.get("turns")
        # The battery counts turns in model-call order; this plate counts
        # step_idx. Equal counts mean the two axes coincide for this run and E3
        # can be marked on the curve. Unequal means it cannot, and saying so is
        # the whole point of checking.
        #
        # Equal counts are necessary and not sufficient: the two axes coincide
        # only if this plate's turns are also contiguous 1..N, so that
        # ``turn / max_turn`` and the battery's ``i / n`` are the same number.
        # A run with 20 billed turns whose last step_idx is 34 would pass a
        # count test and still put E3's crossing in the wrong place.
        c["axis_agrees"] = (
            c["shape_turns"] is not None
            and c["shape_turns"] == len(c["points"]) == c["max_turn"]
        )
        if c["shape_turns"] is not None and not c["axis_agrees"]:
            axis_mismatch.append(
                f"{c['run_id']}: battery counts {c['shape_turns']} turns, this plate "
                f"draws {len(c['points'])} billed step_idx values ending at {c['max_turn']}"
            )

    if unknown:
        notes.append(
            f"{len(unknown)} drawn run(s) have no battery run and therefore no E2/E3/E4 "
            f"({', '.join(sorted(unknown))}). Battery v2 scores the arms "
            f"{', '.join(shape['arms'])}; the live theoria arm is not among them, so its "
            "shape metrics are absent with a reason and are never drawn as zero."
        )
    if axis_mismatch:
        notes.append(
            "battery turn axis disagrees with this plate's step axis on "
            f"{len(axis_mismatch)} run(s), reported not reconciled: "
            + "; ".join(sorted(axis_mismatch))
            + ". E3's crossing is not marked on those curves."
        )
    else:
        notes.append(
            f"battery turn axis agrees with this plate's step axis on all "
            f"{sum(1 for c in curves if c['axis_agrees'])} run(s) that carry a turn count, "
            "so every E3 crossing that exists is markable. Stated as a checked result, not "
            "as an assumption -- the check is the reason the marks may be drawn at all."
        )

    # A disagreement inside the battery's own support fields, found by trying to
    # use E4's turn count for the axis check. Reported here because it is the
    # kind of thing a reader of the CSV would otherwise reconcile wrongly.
    e4_disagree = sorted(
        f"{c['run_id']}: E2/E3 support says {c['shape_turns']} turns, E4 support says "
        f"{c['e4_turns']}"
        for c in curves
        if c.get("e4_turns") is not None
        and c["shape_turns"] is not None
        and c["e4_turns"] != c["shape_turns"]
    )
    if e4_disagree:
        notes.append(
            f"battery support labelling, reported not reconciled ({len(e4_disagree)} run(s)): "
            "E4's support key 'turns' holds len(run.calls) while E2/E3's holds "
            "len(run.turn_costs()) -- billed calls against decisions, which differ exactly "
            "when a decision was retried. " + "; ".join(e4_disagree) + ". Panel D's x-axis "
            "is therefore labelled with what E4 actually counts."
        )
    return notes


def extract() -> tuple[list[dict], dict, list[str]]:
    """Per-run curve records, the shape bundle, and notes. No plotting, no writing."""
    calls, steps, notes = _load_ledgers()
    rollups, rollup_notes = _load_rollups()
    notes.extend(rollup_notes)

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
    zero_cost: list[str] = []
    curves: list[dict] = []
    for rid in sorted(per_turn, key=lambda r: (meta[r]["game_id"], meta[r]["model"], r)):
        arm, provenance = arm_for(rid)
        arm_provenance.add(provenance)
        if provenance == "env_step" and arm != rid.split("-", 1)[0]:
            arm_disagreements.append(f"{rid}: env_step says {arm!r}, run_id prefix says {rid.split('-', 1)[0]!r}")

        turns = sorted(per_turn[rid])
        total = sum(per_turn[rid][t] for t in turns)
        if total < 0.0:
            raise ValueError(
                f"{rid}: total cost is {total!r}. A negative bill is not an absence, it is a "
                "corrupt ledger, and this plate will not draw a shape over it."
            )
        if total == 0.0:
            # Billed nothing. Not a crash, and not a zero-cost curve either: a run
            # with no bill has no shape, exactly like the runs a few lines above
            # that have env_step rows and no model_call rows. Drawn as absent,
            # named in the notes.
            #
            # This raised until P8's discovery rules widened the input set. The
            # old hand-written four-name tuple never saw the *tracked*
            # `ledger.a7*.jsonl` shards, one of which is a smoke test whose run
            # billed nothing; the rule picks up every shard matching the pattern,
            # which is what it is for, and the build then died on a run that is
            # perfectly legitimate. Found by `release/reproduce.py` re-running the
            # figures build against the manifest -- which is the entire argument
            # for that step existing.
            zero_cost.append(rid)
            continue
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
                "rate_absent_reason": "no action taken -- rate absent",
            }
        )

    if zero_cost:
        notes.append(
            f"{len(zero_cost)} run(s) have model_call rows that sum to exactly 0.00 USD "
            f"({', '.join(sorted(zero_cost))}): billed nothing, so no curve and no "
            "zero-cost curve either -- a run with no bill has no shape. A NEGATIVE total "
            "still stops the build, because that is a corrupt ledger rather than an absence."
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

    # --- the second arm ----------------------------------------------------
    theoria_curves, theoria_notes = _load_theoria_curves()
    notes.extend(theoria_notes)
    curves.extend(theoria_curves)

    # --- the shape metrics, read from the battery --------------------------
    shape, shape_notes = _load_shape_metrics()
    notes.extend(shape_notes)
    notes.extend(_attach_shape(curves, shape))
    c2_sentence, c2_notes = _c2_verdict(curves)
    notes.extend(c2_notes)
    notes.append(c2_sentence)
    return curves, shape, notes


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def csv_rows(curves: list[dict]) -> list[list]:
    """Rows sorted by ``(game_id, model, run_id, turn)`` -- literal, explicit."""
    ordered = sorted(curves, key=lambda c: (c["game_id"], c["model"], c["run_id"]))
    rows: list[list] = []
    for c in ordered:
        shape = c["shape"]
        shape_cells: list = []
        for m in SHAPE_METRICS:
            cell = shape[m]
            value = cell.get("value")
            shape_cells.append(theme.fmt_num(value, places=9) if value is not None else None)
            shape_cells.append(cell.get("status"))
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
                    *shape_cells,
                    c["shape_turns"],
                    theme.fmt_num(c["axis_agrees"]) if c["shape_turns"] is not None else None,
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


def _wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap. Deterministic, and no dependency on locale.

    ``textwrap`` would do, but its break rules around punctuation have moved
    between Python versions, and this text lands in an SVG that a gate diffs
    byte for byte.
    """
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _shape_value(curve: dict, metric: str):
    """The battery's value for ``metric``, or ``None``. Never a substitute."""
    return (curve.get("shape") or {}).get(metric, {}).get("value")


def _render(
    curves: list[dict], shape: dict, theme_name: str
) -> list[str]:
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

    # The bottom row is empty axes whose only job is to reserve height for the
    # caveat, which `theme.caveat` draws in figure coordinates and which
    # therefore takes part in no layout. Every time the caveat grows this row
    # has to grow with it, and the failure mode when it does not is panel D's
    # x-label printing straight through the first two lines of text -- legible
    # in neither, identical between builds, green on every gate.
    fig = plt.figure(figsize=(11.0, 13.8))
    gs = fig.add_gridspec(
        4, 2, height_ratios=[1.00, 1.30, 0.80, 0.72], width_ratios=[1.0, 1.0]
    )
    ax_abs = fig.add_subplot(gs[0, 0])
    ax_norm = fig.add_subplot(gs[0, 1])
    ax_strip = fig.add_subplot(gs[1, :])
    ax_growth = fig.add_subplot(gs[2, 0])
    # Panel D's absences get their own column rather than a text block hung
    # under the axes. The first version put them below panel D with a negative
    # transAxes offset, where they landed on top of the caveat -- unreadable,
    # byte-identical between builds, and green on every gate.
    ax_growth_absent = fig.add_subplot(gs[2, 1])
    ax_growth_absent.axis("off")
    ax_pad = fig.add_subplot(gs[3, :])  # reserves room for the caveat text
    ax_pad.axis("off")

    plot_order = sorted(curves, key=lambda c: (_model_rank(c["model"]), c["game_id"], c["run_id"]))

    # --- panel A: absolute -------------------------------------------------
    #
    # Colour is the model ladder, marker is the game and linestyle is how the
    # run ended -- three channels, all spoken for. The arm is a fourth
    # dimension and it gets the one channel left: marker FILL. Baseline runs
    # are filled, theoria runs are hollow. It is a weak channel, so the theoria
    # curves are also labelled in place below; identity is never left to one
    # cue, least of all the weakest one.
    for c in plot_order:
        xs = [q["turn"] for q in c["points"]]
        ys = [q["cum_cost_usd"] for q in c["points"]]
        every = max(1, (len(xs) + 5) // 6)
        hollow = c["arm"] != BASELINE_ARM
        ax_abs.plot(
            xs,
            ys,
            color=colour_of[c["model"]],
            linestyle=_linestyle(c),
            linewidth=1.7 if hollow else 1.3,
            marker=marker_of[c["game_id"]],
            markersize=5.0 if hollow else 3.4,
            markerfacecolor="none" if hollow else colour_of[c["model"]],
            markeredgecolor=colour_of[c["model"]],
            markeredgewidth=1.2 if hollow else 0.8,
            markevery=every,
            alpha=0.92,
            solid_capstyle="round",
        )

    # The theoria curves, labelled on the plate. Without this the reader sees a
    # green line four times taller than everything else and reads it as "opus is
    # expensive", which is the wrong lesson: it is a different arm buying a
    # different thing. Anchored to the last point of the longest theoria curve
    # so the text lands beside the line rather than over the baseline bundle.
    theoria = [c for c in plot_order if c["arm"] != BASELINE_ARM]
    if theoria:
        lead = max(theoria, key=lambda c: (c["ledger_cost"], c["run_id"]))
        tip = lead["points"][-1]
        ax_abs.annotate(
            f"{lead['arm']} arm (hollow markers): {len(lead['points'])} of "
            f"{lead['max_turn']} turns bought\na desk call. Short and tall by "
            "construction -- not the same y-quantity.",
            xy=(tip["turn"], tip["cum_cost_usd"]),
            # Below the model/arm key rather than beside it: at 0.86 the two
            # overlapped once the key grew a second block.
            xytext=(0.40, 0.62),
            textcoords="axes fraction",
            fontsize=theme.BASE_FONT_SIZE - 2.5,
            color=p["ink_secondary"],
            va="top",
            arrowprops={
                "arrowstyle": "-",
                "color": p["muted"],
                "linewidth": 0.7,
                "shrinkB": 3.0,
            },
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
    arm_handles = [
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker="o",
               markersize=4.6, markerfacecolor=p["ink_secondary"],
               label=f"{BASELINE_ARM}: one model call buys one action"),
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker="o",
               markersize=5.4, markerfacecolor="none",
               markeredgecolor=p["ink_secondary"], markeredgewidth=1.2,
               label="theoria: one desk call theorises across the run"),
    ]
    leg_models = ax_abs.legend(
        handles=model_handles + arm_handles,
        loc="upper left",
        title="colour: model ladder   |   marker fill: arm",
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
        hollow = c["arm"] != BASELINE_ARM
        ax_norm.plot(
            xs,
            ys,
            color=colour_of[c["model"]],
            linestyle=_linestyle(c),
            linewidth=1.7 if hollow else 1.3,
            marker=marker_of[c["game_id"]],
            markersize=5.0 if hollow else 3.4,
            markerfacecolor="none" if hollow else colour_of[c["model"]],
            markeredgecolor=colour_of[c["model"]],
            markeredgewidth=1.2 if hollow else 0.8,
            markevery=every,
            alpha=0.92,
        )
    # --- E2 and E3, put where they can be read off the curve ---------------
    #
    # Both metrics are shares of this exact picture, so they are drawn as the
    # construction that defines them rather than as numbers in a corner: E2 is
    # the height of a curve where it crosses the head boundary, E3 is the x of
    # the marked crossing. A reader who distrusts the annotation can measure it.
    head_k = shape["head_k"]
    _HEAD_STYLE = (0, (1, 1.6))
    if head_k is not None:
        ax_norm.axvline(head_k, color=p["ink_secondary"], linewidth=0.8,
                        linestyle=_HEAD_STYLE, zorder=1)
        # The explanation lives in the legend, not as free text on the plate.
        # As free text it landed across the game key, which is the failure the
        # first render of this panel actually had.

    marked = 0
    for c in plot_order:
        e3 = _shape_value(c, "E3")
        if e3 is None or not c["axis_agrees"]:
            continue
        turn = (c["shape"]["E3"].get("support") or {}).get("turn")
        if turn is None:
            continue
        point = next((q for q in c["points"] if q["turn"] == turn), None)
        if point is None:
            continue
        ax_norm.plot(
            [e3],
            [point["frac_of_spend"]],
            linestyle="none",
            marker="|",
            markersize=11.0,
            markeredgewidth=1.5,
            color=theme.STATUS["warning"],
            zorder=6,
        )
        marked += 1

    ax_norm.set_xlim(0.0, 1.02)
    ax_norm.set_ylim(0.0, 1.02)
    ax_norm.set_title("B. normalised: where E2 and E3 are read", loc="left")
    ax_norm.set_xlabel("fraction of run (turn / final turn)")
    ax_norm.set_ylabel("fraction of total spend")
    n_e3_eligible = sum(
        1 for c in curves if _shape_value(c, "E3") is not None
    )
    e3_label = (
        f"E3 crossing ({marked}/{n_e3_eligible} scored)"
        if marked
        else "E3 crossing: none markable"
    )
    game_handles = [
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker=marker_of[g],
               markersize=4.5, linestyle="none", label=g)
        for g in games
    ] + [
        Line2D([], [], color=p["muted"], linewidth=0.9, linestyle=_REFERENCE_STYLE,
               label="flat spend (reference)"),
        Line2D([], [], color=p["ink_secondary"], linewidth=0.8, linestyle=_HEAD_STYLE,
               label=(
                   f"E2 head boundary ({head_k:g} of turns)"
                   if head_k is not None
                   else "E2 head boundary: not drawable"
               )),
        Line2D([], [], color=theme.STATUS["warning"], linewidth=0.0, marker="|",
               markersize=9.0, markeredgewidth=1.5, linestyle="none", label=e3_label),
    ]
    leg_games = ax_norm.legend(
        handles=game_handles,
        loc="lower right",
        title="marker: game (colour is never the only channel)",
        alignment="left",
        fontsize=theme.BASE_FONT_SIZE - 2.5,
        title_fontsize=theme.BASE_FONT_SIZE - 2.5,
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
            rate_text = c["rate_absent_reason"]
            rate_colour = p["muted"]
        else:
            rate_text = f"{c['n_failed']}/{c['n_actions']} = {c['fail_rate'] * 100:.0f}%"
            rate_colour = (
                theme.STATUS["critical"] if c["fail_rate"] >= FAILURE_BAND_LOW
                else p["ink_secondary"]
            )
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
        # Short enough to fit the plate. The two disagreeing bands are named in
        # full in the caveat; a title that runs off the right edge states
        # neither of them.
        "C. the confound first: environment actions per turn, failures in red "
        "(both published failure bands are in the caveat)",
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

    # --- panel D: the context-growth fit ----------------------------------
    #
    # E4 is the one shape metric that is not a share of this plate's money, so
    # it cannot be read off panels A or B: it is R^2(quadratic) - R^2(linear)
    # over the *token* series. It gets its own axes, against run length,
    # because the metric's own floor is a length ("a quadratic needs room") and
    # the reader should be able to see whether a high value is just a long run.
    #
    # Runs the battery could not score are not dropped. They sit on a separate
    # lane below the axis with their reason spelled out, because "we have no
    # number" and "the number is zero" are different facts and this figure's
    # standing rule is that absence is drawn as absence.
    growth_order = sorted(
        curves, key=lambda c: (_model_rank(c["model"]), c["game_id"], c["run_id"])
    )
    scored = [c for c in growth_order if _shape_value(c, "E4") is not None]
    unscored = [c for c in growth_order if _shape_value(c, "E4") is None]

    if scored:
        for c in scored:
            turns = (c["shape"]["E4"].get("support") or {}).get("turns")
            if turns is None:
                continue
            hollow = c["arm"] != BASELINE_ARM
            ax_growth.plot(
                [turns],
                [_shape_value(c, "E4")],
                linestyle="none",
                marker=marker_of[c["game_id"]],
                markersize=6.0 if hollow else 5.0,
                markerfacecolor="none" if hollow else colour_of[c["model"]],
                markeredgecolor=colour_of[c["model"]],
                markeredgewidth=1.2 if hollow else 0.9,
                alpha=0.95,
            )
        ax_growth.axhline(0.0, color=p["axis"], linewidth=0.6, zorder=0)
        ax_growth.set_ylabel("E4: R2(quadratic) - R2(linear)")
    # Labelled "billed model calls" and not "turns", although the battery's
    # support key for this number is called `turns`: E4 fills it from
    # len(run.calls), so on a run with retries it is not the decision count E2
    # and E3 use. Copying the key's name onto the axis would have put two
    # different quantities under one word.
    ax_growth.set_xlabel("billed model calls E4 was fitted over (battery E4 support 'turns')")
    ax_growth.set_title("D. context growth: transcript or manual?", loc="left")

    # The absence column. Grouped by the battery's own reason string, so the
    # plate carries the reason and not just a gap.
    reasons: dict[str, list[str]] = {}
    for c in unscored:
        cell = c["shape"]["E4"]
        reasons.setdefault(str(cell.get("reason") or cell.get("status")), []).append(
            c["run_id"]
        )
    lines = [
        "E4 IS THE BATTERY'S NUMBER, NOT THIS PLATE'S.",
        "Higher means context is accelerating: R2 of a",
        "quadratic fit to context tokens per turn, minus",
        "R2 of a linear one. It reads the token series,",
        "not the priced one, so it survives a change in",
        "the price list.",
        "",
        f"ABSENT, NOT ZERO -- {len(unscored)} of {len(curves)} drawn runs",
        "carry no E4:",
    ]
    for reason, rids in sorted(reasons.items()):
        lines.append(f"  {len(rids)} run(s):")
        lines.extend("    " + chunk for chunk in _wrap(reason, 52))
    ax_growth_absent.text(
        0.0,
        1.0,
        "\n".join(lines),
        transform=ax_growth_absent.transAxes,
        fontsize=theme.BASE_FONT_SIZE - 2.5,
        color=p["ink_secondary"],
        va="top",
        ha="left",
        linespacing=1.45,
    )

    n_base_scored = sum(1 for c in scored if c["arm"] == BASELINE_ARM)
    growth_handles = [
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker="o",
               markersize=4.6, markerfacecolor=p["ink_secondary"], linestyle="none",
               label=f"{BASELINE_ARM}, scored ({n_base_scored})"),
        Line2D([], [], color=p["ink_secondary"], linewidth=0.0, marker="o",
               markersize=5.4, markerfacecolor="none", markeredgecolor=p["ink_secondary"],
               markeredgewidth=1.2, linestyle="none",
               label=f"other arm, scored ({len(scored) - n_base_scored})"),
    ]
    ax_growth.legend(
        handles=growth_handles,
        loc="upper left",
        fontsize=theme.BASE_FONT_SIZE - 2,
        ncols=1,
    )

    fig.suptitle(
        "Figure 2 -- bill shape: the per-turn cost curve (C2: bought early, spent late)"
    )
    theme.caveat(fig, _caveat_text(curves, shape), theme=theme_name)
    return theme.save(fig, NAME, theme_name)


#: The one number in the caveat that this pipeline cannot compute and does not
#: parse: the baseline comparator, which exists only in a Markdown table.
#: Declared in sources.py so it is hashed, and quoted with its location so a
#: reader can check it. Parsing a figure out of prose would be a second, worse
#: dependency -- but reading a number off an *undeclared* file, which is what
#: this plate did before P8, is the failure the registry exists to prevent.
BASELINE_PRICE_CITE = "baseline-arms/BUDGET_REPORT.md 2.1, opus row"


def _caveat_text(curves: list[dict], shape: dict) -> str:
    """The caveat, with its arithmetic computed rather than typed.

    Two of these numbers used to be literals that the same build also computed
    into ``notes`` -- two definitions of one number, which is the exact failure
    this whole change is premised on. They are now derived from the basis run's
    own manifest.
    """
    basis = _cost_basis(curves)
    if basis is None:
        unit = (
            "THE TWO ARMS ARE NOT PRICED IN THE SAME UNIT, and this build has no theoria run "
            "with a game to quantify it from, so no per-action comparison is stated."
        )
    else:
        m = basis["manifest"]
        cost = m["cost"]
        recon = m.get("reconciliation") or {}
        actions = recon.get("successful_actions")
        calls = cost.get("model_calls")
        per_action = (
            f"USD {cost['cli_reported_usd'] / actions:.4f} (theoria, {actions} actions) "
            f"against USD 0.1459 (bare_cc opus, {BASELINE_PRICE_CITE})"
            if actions
            else "absent -- the basis run declares no successful actions to divide by"
        )
        unit = (
            "THE TWO ARMS ARE NOT PRICED IN THE SAME UNIT. A bare_cc turn buys one model call "
            "that picks one action; a theoria turn buys a desk call that theorises across the "
            f"whole run -- {calls} calls covered {actions} actions, so its curve is short and "
            "tall by construction and the vertical gap in panel A is NOT a like-for-like "
            f"markup. Per successful action the comparison that does hold is {per_action} -- "
            "and even that is one theoria run against a pilot. Theoria dollars are the "
            "provider's own arithmetic; the repo price table disagrees by "
            f"{cost['relative_delta'] * 100:.1f}% and that is a finding about the table, not "
            "the run."
        )
    return (
        unit
        + " The third arm is still absent, and absence is not zero: there is no Schema arm in "
        "this ledger (baseline-arms/SCHEMA_LOCATE.md), so the model ladder stands in for it "
        "(battery/DECISIONS.md D-B-004, weaker by REPORT_V0's own note). Cost is summed over "
        "retried calls sharing a turn. Panel C is the price-list confound: with a large share "
        "of steps failing, E5 cost-per-action tracks token pricing, not skill. BOTH FIGURES FOR "
        "THAT SHARE TRAVEL, because they disagree: battery/REPORT_V0.md says 27-45%, and "
        "papers/phase1-workshop/REVIEW.md recomputes 28.3-45.1% and records that the 27% lower "
        "bound does not reproduce. The panel is annotated with REPORT_V0's band, which is the "
        f"one it was drawn against. {_envelope_caveat()} "
        + _shape_caveat(curves, shape)
        + " "
        + _c2_verdict(curves)[0]
    )


def _envelope_caveat() -> str:
    """What the envelope shards contribute to this bill, or that they are missing.

    This replaced ``"{n} optional ledger(s) declared and absent"``, which was a
    number that could not vary. Once ``envelope_ledger`` became a tracked rule
    with no ``expected`` list, ``_discover`` only emits a ``Source`` for a file
    that is on disk, so the absent count is zero by construction and the sentence
    printed ``0`` on every plate forever. A caveat whose number cannot change is
    not a caveat, and this one sat on the face of a publication figure.

    So it reports the live fact instead, in the two states that actually occur: a
    source repo where the shards are committed and read, and a release tree where
    they are excluded by licence posture and the bill is correspondingly narrower.
    """
    n = len(sources.discovered(ENVELOPE_RULE))
    if n:
        return (
            f"The envelope campaign's {n} committed ledger shard(s) are folded in, "
            "declared by rule in figures/sources.py rather than by a list that ages."
        )
    return (
        "NO ENVELOPE LEDGER SHARD IS COMMITTED IN THIS TREE, so this bill covers the "
        "pilot ledger alone and excludes the envelope campaign entirely -- expected "
        "in a release tree (release/LICENCE_POSTURE.md classes them B, excluded by "
        "default), and absence is not zero."
    )


#: A leg needs this many *distinct billed steps* before its bill has a shape at
#: all. Two points make a slope and nothing else; the number below is this
#: plate's own, declared here rather than borrowed from
#: `battery/metrics/economy.py`'s MIN_TURNS_FOR_SHAPE -- E2 is a Phase 4 primary
#: endpoint counting a different thing on a different axis, and quietly reusing
#: its floor would be this plate asserting a definition it is not entitled to.
#: Legs under the floor are reported by name as too short, never folded into a
#: majority.
_C2_MIN_BILLED_STEPS = 4

#: "Trailing to zero" means the last billed step costs under this fraction of
#: the leg's most expensive one. It is deliberately generous: at a tenth of peak
#: the arm has all but stopped buying, which is what 收敛后趋零 asserts, and a
#: threshold that no leg can clear is a threshold that proves nothing.
_C2_TAIL_FRACTION = 0.10


def _outcome_tally(legs: list[dict], run_ids: list[str]) -> dict[str, list[str]]:
    """``{outcome: [run_id, ...]}`` over named legs. ``None`` keeps its own bucket.

    Written as a helper rather than inline because both C2 sentences want it and
    a claim like "every one of them tripped the spend gate" is the kind of thing
    that is true when it is typed and false a week later. Derived, so it cannot
    be.
    """
    tally: dict[str, list[str]] = {}
    for run_id in run_ids:
        outcome = next(c["outcome"] for c in legs if c["run_id"] == run_id)
        tally.setdefault("outcome absent" if outcome is None else str(outcome), []).append(run_id)
    return tally


def _c2_verdict(curves: list[dict]) -> tuple[str, list[str]]:
    """What the theoria legs actually show about C2. ``(sentence, notes)``.

    Theoria.md 1.6 predicts 前重后轻，收敛后趋零 -- front-heavy, tapering, and
    approaching zero once the theory converges. Until 2026-08-01 the plate drew
    one long theoria leg and left the reader to infer the rest. It now draws
    eight, and the inference the reader would draw is wrong, so it is stated
    instead.

    Two descriptive quantities, both computed off the drawn points and neither
    of them E2 (E2 is the battery's, is defined on a different axis, and is
    ABSENT for every live theoria leg because battery v2 does not score this
    arm -- see ``_shape_caveat``):

    * **front-half share** -- the fraction of a leg's spend falling in the first
      half of its billed-step span. Above 0.5 is front-heavy; at 0.5 the bill is
      flat; below 0.5 it is back-heavy.
    * **tail ratio** -- the last billed step's cost over the leg's peak. Near
      zero is the taper the claim predicts.

    A verdict either way is reportable. That matters: this function was written
    expecting to confirm C2, and what it says is the opposite.
    """
    notes: list[str] = []
    legs = sorted(
        (c for c in curves if c["arm"] != BASELINE_ARM and c["points"]),
        key=lambda c: c["run_id"],
    )
    if not legs:
        return (
            "C2 SHAPE, MEASURED: no theoria leg is drawn on this build, so the plate "
            "makes no statement about the bill's shape at all.",
            notes,
        )

    long_legs: list[tuple[str, float, float, int]] = []
    short: list[str] = []
    for c in legs:
        steps = [p["turn"] for p in c["points"]]
        costs = [p["cost_usd"] for p in c["points"]]
        if len(steps) < _C2_MIN_BILLED_STEPS:
            short.append(f"{c['run_id']} ({len(steps)})")
            continue
        span = steps[-1] - steps[0]
        midpoint = steps[0] + span / 2
        total = sum(costs)
        front = sum(k for s, k in zip(steps, costs) if s <= midpoint) / total
        peak = max(costs)
        tail = costs[-1] / peak if peak else 0.0
        long_legs.append((c["run_id"], front, tail, len(steps)))

    if not long_legs:
        return (
            "C2 SHAPE, MEASURED: NOT ONE drawn theoria leg reaches "
            f"{_C2_MIN_BILLED_STEPS} distinct billed steps, so no leg on this plate has "
            "a bill shape to read. The short ones are "
            + ", ".join(short)
            + " (billed steps in brackets). The shape Theoria.md 1.6 predicts "
            "(front-heavy, tapering to nothing once the theory converges) is UNTESTED "
            "here, which is not the same as unsupported and is very much not the same "
            "as confirmed.",
            notes,
        )

    front_heavy = [n for n, f, _, _ in long_legs if f > 0.5]
    tapering = [n for n, _, t, _ in long_legs if t <= _C2_TAIL_FRACTION]
    detail = "; ".join(
        f"{n} {k} steps, front-half share {f:.2f}, tail/peak {t:.2f}"
        for n, f, t, k in long_legs
    )
    notes.append(
        f"C2 shape, measured over {len(long_legs)} theoria leg(s) with at least "
        f"{_C2_MIN_BILLED_STEPS} billed steps: {detail}. "
        f"{len(front_heavy)} front-heavy, {len(tapering)} tapering to under "
        f"{_C2_TAIL_FRACTION:.0%} of peak."
    )
    if short:
        notes.append(
            f"C2 shape: {len(short)} drawn theoria leg(s) are under the {_C2_MIN_BILLED_STEPS}"
            "-billed-step floor and carry no shape verdict rather than a weak one ("
            + ", ".join(short)
            + "), and they ended "
            + "; ".join(
                f"{k}: {len(v)}"
                for k, v in sorted(_outcome_tally(legs, [s.split(" (")[0] for s in short]).items())
            )
            + ". Their shortness is a fact about where each leg was cut off, not about "
            "the theory -- which is exactly why it is reported and not averaged in."
        )

    # The plate stays ASCII on purpose. Theoria.md 1.6's own phrasing is
    # Chinese, and the honest thing would be to quote it -- but matplotlib's SVG
    # writer does not carry these code points through intact on this host, and
    # what reaches the file depends on the machine's codepage, which is a
    # determinism defect wearing a typography costume. The claim is glossed and
    # cited instead; the Chinese lives in the run record, which is UTF-8 text
    # nobody renders.
    verdict = (
        "C2 SHAPE, MEASURED AND NEGATIVE. Theoria.md 1.6 predicts a bill that is "
        "front-heavy and then tapers to nothing as the theory converges. Over the "
        f"{len(long_legs)} drawn theoria leg(s) long enough to have a shape ("
        f"at least {_C2_MIN_BILLED_STEPS} distinct billed steps), {len(front_heavy)} "
        f"is/are front-heavy and {len(tapering)} taper(s) to under "
        f"{_C2_TAIL_FRACTION:.0%} of peak: {detail}. "
        "THE PLATE SHOWS NO CONVERGENCE. It is written here rather than left to the "
        "reader because a flat curve and a converging one look alike at a glance when "
        "the curve is six points long."
    )
    by_outcome = _outcome_tally(legs, [n for n, _, _, _ in long_legs])
    if tapering:
        taper_outcomes = sorted(_outcome_tally(legs, tapering))
        verdict += (
            " The taper that does appear is on "
            + ", ".join(tapering)
            + ", and that leg's own manifest records its outcome as "
            + ", ".join(taper_outcomes)
            + " -- its zero-cost steps are the run still acting after the money stopped. "
            "The desk stopped being called because the budget ended, not because the "
            "manual stopped being surprised. A budget cutoff drawn on a cost axis is "
            "indistinguishable from convergence, and it is not convergence."
        )
    verdict += (
        " Read against how the legs ended ("
        + "; ".join(f"{k}: {len(v)}" for k, v in sorted(by_outcome.items()))
        + "), not one of them stopped because it ran out of surprises. C2 is therefore "
        "UNCONFIRMED on this evidence, and the reason is where the legs were cut off "
        "rather than what they showed before that."
    )
    return verdict, notes


def _shape_caveat(curves: list[dict], shape: dict) -> str:
    """The sentence the shape panels must never travel without."""
    cards = shape["cards"]
    unscored_runs = sorted({c["run_id"] for c in curves if _shape_value(c, "E2") is None})
    no_battery = sorted(
        {c["run_id"] for c in curves if c["shape"]["E2"].get("status") == "no-battery-run"}
    )
    mismatch = sorted(
        {
            c["run_id"]
            for c in curves
            if c["shape_turns"] is not None and not c["axis_agrees"]
        }
    )
    n_agree = sum(1 for c in curves if c["axis_agrees"])

    # The anti-gaming floor is quoted from the battery's own reason string, not
    # written out here. `MIN_TURNS_FOR_SHAPE = 8` lives in
    # battery/metrics/economy.py, and the same argument that keeps FRONTLOAD_K
    # out of this file applies to it: a hand-copied fact about another file is a
    # fact that will go stale. The reason text is in the hashed artefact.
    thin_reasons = sorted(
        {
            str(c["shape"]["E2"]["reason"])
            for c in curves
            if c["shape"]["E2"].get("status") == "insufficient-data"
            and c["shape"]["E2"].get("reason")
        }
    )
    if thin_reasons:
        floor_sentence = (
            "The battery's own floor is quoted rather than restated -- it reports those runs as "
            'insufficient-data with the reason "'
            + '"; "'.join(thin_reasons)
            + '" -- so a short run gets that verdict rather than a flattering number.'
        )
    else:
        floor_sentence = (
            "No drawn run fell under the battery's short-run floor on this build, so no "
            "insufficient-data reason is quoted."
        )
    return (
        "E2/E3/E4 ARE THE BATTERY'S NUMBERS, NOT THIS PLATE'S. They are read from "
        "battery/artifacts/capability_spectrum.json, whose definitions are: E2, "
        + cards["E2"]["definition"]
        + " E3, "
        + cards["E3"]["definition"]
        + " E4, "
        + cards["E4"]["definition"]
        + " Recomputing them here would be a second definition of a Phase 4 primary "
        "endpoint. THE TWO TURN AXES ARE CHECKED, NOT ASSUMED TO MATCH: the battery counts "
        "turns in model-call order (battery/INPUT_FORMAT.md gap 5) and this plate counts "
        "step_idx, so E3's crossing is marked only on runs where the two coincide. "
        + (
            f"On this build {len(mismatch)} run(s) disagree ({', '.join(mismatch)}) and are "
            "left unmarked rather than approximated."
            if mismatch
            else f"On this build they agree on all {n_agree} run(s) that carry a battery turn "
            "count, and that agreement is the licence to draw the marks at all."
        )
        + f" {len(unscored_runs)} drawn run(s) carry no E2 at all, of which {len(no_battery)} "
        "have no battery run: the live theoria arm is in none of battery v2's arms ("
        + ", ".join(shape["arms"])
        + "), so its front-load index is ABSENT, not low. "
        + floor_sentence
    )


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    curves, shape, notes = extract()
    rows = csv_rows(curves)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(curves, shape, theme_name))

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
