"""Figure 2's raw material, cut at the level boundaries, written per leg.

    python -m armtools.curves --run-dir theoria-arm/runs/<slug>

## What this is for

A campaign is hours long and the thing it loses first is not the score, it is
the accounting. `armtools/archive.py` already reduces one leg's ledger to a
per-turn series -- theorize rounds, the seven surprise counts, cost -- and
`harness/campaign.py` already concatenates those series across legs. What
neither produces is the cut that claim C3 is actually about: **per level**.

C3 is transfer, and `inner/levels.py` fixes its mechanical meaning as *the
same `theory.dsl` against a different computed problem*. So the sentence the
figure has to support is "the second level cost less than the first", and that
sentence needs the three curves segmented at the boundary rather than averaged
across it. A run that clears a level and then spends nothing more looks, on an
un-segmented curve, exactly like a run that was cheap throughout.

## It reduces, it does not re-derive

Every number here comes out of `armtools.archive.turn_series()` -- the join
between `model_call` records, `turns.json` and `surprises.jsonl` -- and out of
`inner/levels.py`'s boundary events. Nothing in this file re-reads the raw
ledger to recompute a quantity that join already produces.

That is a rule, not a preference. `archive.turn_series` carries a written-down
account of why the join is sound (which index bridges to which, and how
confident the reconstruction is), and it lowers its own `join_confidence` when
a check fails. A second implementation would be a second, unlabelled answer to
the same question, and E2's own input would then have two definitions -- which
is the exact failure `figures/sources.py` exists to catch and the reason
`campaign.campaign_series` does not recompute the front-load index either.

The one thing this file reads the ledger for is the self-check below, and it
reads it to *count records*, not to derive a quantity.

## The self-check: no accounting gap goes unnoticed

Three strict equalities, against three numbers counted straight out of the
ledger: **commands**, **billed calls**, and **dollars**.

`turn_series` rows carry `http_commands`, the number of environment commands
the turn issued. Summed over every row in this file's curves, that must equal
the number of `env_step` records in the leg's ledger. Measured on the archive:
`20260728T025503Z-g50t-e08-fixed` 146 = 146 over 3 turns,
`20260729T004020Z-leg01` 104 = 104 over 52 turns.

**The command equality alone was not enough, and the gap it missed was
measured.** `20260731T1310Z-A3-level2-carried-r2` and
`...T1430Z-...-r3` both ended `spend_gate_tripped`. In each, the final desk
call was billed by the pool and landed in no turn row, because
`inner/loop.py` appends a turn's record only *after* the turn's last ARC
command and the gate killed the turn before it sent one. The vanished turn had
therefore issued no command at all -- so `http_commands` balanced perfectly,
99 = 99 and 234 = 234, while the curve understated r2 by $1.63 of $9.56 (17%)
and r3 by $1.68 of $13.44 (12.5%). A check that watches only commands cannot
see money go missing; the two are counted separately here because a hole can
open in either without moving the other.

Each is a strict equality and a mismatch **raises**. The failure they catch is a
segmentation that silently dropped turns -- a level whose boundary was
mis-placed, a leg whose rows were filtered by a predicate that was one off. A
gap like that is invisible in the plot (the curve simply looks shorter) and it
is discovered, if ever, long after the money is spent. Better to refuse to
write the file.

Note what the equality is **not**: it is not "one turn per environment step".
A turn issues many commands -- RESET, retries, failed actions -- and on this
arm the ratio has been as high as 146:3. The invariant is that the curves
*account for* every command, not that they are indexed by one.

And an equality alone is not enough, because `0 == 0` satisfies it. A leg that
never took a turn would otherwise write a syntactically perfect file whose
every series is empty and every total is zero -- and a zero in a cost curve
reads as "this leg was cheap", not as "this leg did not happen". So zero rows
is refused outright, with both numbers in the message, because the two causes
are not equally serious: nothing played, versus the join lost every row a
ledger full of commands should have produced. `theoria-arm/verify.py` opens by
naming this failure mode with the same example, `figures/verify.sh` printing
"ok" when both of its builds produced nothing at all.

## A call with no turn is recorded, not dropped

The corollary of the money equality: a billed call whose turn the run never
wrote down still has to appear. `archive._unrecorded_turn_rows` gives it a row
flagged `turn_record_missing`, carrying its calls and its dollars and owning no
ARC command, with `turn_source` and `turn_record_missing_why` saying in full
why no record exists. `turn_record_missing` is a declared column, False on
every ordinary row, so the flag is a measurement on every turn rather than a
key that materialises only when something has gone wrong.

The join's own confidence stays `degraded` for such a leg -- the row is the
archive's reconstruction, not the run's record, and that distinction must not
be laundered by the fact that the money now adds up. Absence is recorded as
absence. A cost that vanishes is worse than a cost with no turn number.

## Format

`curves.json` next to `turn_series.json` and `cost_curve.json`, plus one file
per level under `curves/`, so a per-level consumer has a per-level path. Both
are written the way this repository writes every deterministic artefact --
`indent=1, sort_keys=True`, LF, trailing newline -- so two runs over the same
ledger are byte-identical and a diff means something changed.

Levels are numbered, not named, and the numbering is `inner/levels.py`'s: level
1 is the run's first, and a boundary event's `to_level` opens the next. There
is no directory named after a level, and that is deliberate: a level is a thing
*inside* a leg, one level can be split across two legs when a leg dies
mid-level, and two games in one campaign both have a level 1. A path keyed by
level alone would collide across all three. The run directory is the arm's only
run identity, so the level files live under it.

## `columns`, and why a flat row list is emitted at all

`figures/` is a deterministic pipeline whose audit surface is a CSV: every
plotted number appears in `figures/csv/<name>.csv` so a reader can check the
figure without reading plotting code. `rows` here is that shape already --
flat records, one per turn, with `columns` naming the order -- so the figure
side can write its CSV straight out of this file instead of re-deriving the
column set from a nested document and guessing at the order.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                       # noqa: F401  (sys.path)

from armtools import archive

SCHEMA = "theoria-arm/curves v1"

#: The flat row's columns, in order. Named rather than inferred from a dict so
#: the CSV the figures track writes has a stable column order across runs --
#: `sort_keys` would give one too, but it would put `usd_cumulative` before
#: `theorize_rounds` and the audit table would read backwards.
COLUMNS = (["level", "turn", "campaign_turn_in_leg", "step_idx",
            "http_commands", "actions_taken", "theorize_rounds",
            "model_calls", "usd", "usd_cumulative_in_level",
            "usd_cumulative_in_leg", "surprise_total", "turn_record_missing"]
           + ["surprise_%s" % kind for kind in archive.KINDS])

#: How far apart two dollar figures may be before the difference is real.
#: `battery/audit/live_economy.py` uses the same number for the same
#: comparison, and it is three orders of magnitude coarser than the 9-decimal
#: rounding every producer here applies -- so anything above it is a missing
#: call, not a float artefact.
USD_TOLERANCE = 1e-06


class CurveGap(Exception):
    """The curves do not account for every environment step in the ledger.

    Raised rather than recorded. Everything else in this arm's archive path is
    written to fail soft -- `write_turn_series` is wrapped in a `try` by
    `harness/campaign.py` precisely so a reduction failure cannot lose a leg
    that played. This one is different: a curve with a hole in it is not a
    degraded artefact, it is a *wrong* one, and it is wrong in the direction
    that makes a campaign look cheaper than it was.
    """


def _levels(run_dir: str) -> Dict[str, Any]:
    """`inner/levels.py`'s own record, from whichever file carries it.

    `run.json` is written by `harness/run.py` and `RUN_STATE.json` by the loop;
    both may carry the `levels` block and a leg that died early may carry
    neither. An absent block means one level, which is the truth for every
    single-level run rather than a guess: `LevelLog` starts at level 1 and only
    an observed increase opens another.
    """
    for name in ("run.json", "RUN_STATE.json", "summary.json"):
        path = os.path.join(run_dir, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except ValueError:
            continue
        levels = doc.get("levels")
        if isinstance(levels, dict):
            return dict(levels, _source=name)
    return {"boundaries": 0, "events": [], "levels_completed": 0,
            "_source": "absent: no run.json/RUN_STATE.json carries a levels "
                       "block, so this leg played one level"}


def _boundary_turns(levels: Dict[str, Any]) -> List[int]:
    """The turn at which each new level opens, in order.

    A boundary event whose `turn` is null is recorded and skipped rather than
    guessed at: `LevelLog.observe` takes `turn` as an optional argument and a
    leg reconstructed without `turns.json` may not have one. Guessing would put
    the cut in the wrong place, which is the one thing this file exists to get
    right.
    """
    turns = []
    for event in (levels.get("events") or []):
        turn = event.get("turn")
        if isinstance(turn, int):
            turns.append(turn)
    return sorted(turns)


def _this_run(run_dir: str, records: List[Dict[str, Any]]
              ) -> List[Dict[str, Any]]:
    """`records` narrowed to this run, the way `archive.turn_series` narrows.

    A ledger may hold more than one run (`runs/a3-gate-mock` holds three), and
    a self-check that counts the file while the join counts the run would
    compare two different runs and call the difference a defect.
    """
    for name in ("run.json", "RUN_STATE.json"):
        doc = None
        path = os.path.join(run_dir, name)
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    doc = json.load(fh)
            except ValueError:
                doc = None
        if isinstance(doc, dict):
            summary = doc.get("summary") or {}
            run_id = summary.get("run_id") or doc.get("run_id")
            if run_id:
                return [r for r in records if r.get("run_id") == run_id]
    return list(records)


def _ledger_facts(run_dir: str,
                  records: Optional[List[Dict[str, Any]]] = None
                  ) -> Dict[str, Any]:
    """What the ledger *says*, counted. Three numbers, no join, no derivation.

    `env_steps` is what the original self-check compared against. `billed_calls`
    and `usd` are the two the original did not have, and their absence is what
    let a leg lose its last desk call in silence: the command count balanced
    perfectly, because the missing turn had issued no command -- it was killed
    before it could. A check that can only see commands is blind to money, and
    money is what the curve is for.
    """
    if records is None:
        records = archive.read_ledger(os.path.join(run_dir, "ledger.jsonl"))
    mine = _this_run(run_dir, records)
    calls = [r for r in mine if r.get("event") == "model_call"]
    usd = 0.0
    for record in calls:
        response = record.get("response") or {}
        if isinstance(response, dict):
            usd += float(response.get("total_cost_usd") or 0.0)
    return {
        "env_steps": sum(1 for r in mine if r.get("event") == "env_step"),
        "billed_calls": len(calls),
        "usd": usd,
    }


#: `_env_steps()` was the whole of this module's ledger reading and is now
#: `_ledger_facts()["env_steps"]`. It is gone rather than kept as a one-line
#: forwarder: it is private, nothing else in the repository called it, and a
#: second door onto the same count is how two callers end up reading the ledger
#: two different ways -- which is exactly the defect the money equality above
#: exists to catch, one layer down.


def curves(run_dir: str, *, doc: Optional[Dict[str, Any]] = None
           ) -> Dict[str, Any]:
    """The three curves, cut at the level boundaries. Writes nothing.

    `doc` is an already-computed `turn_series()` document; passing it is how
    `harness/campaign.py` avoids performing the join twice for one leg, since
    it has just written `turn_series.json` from the same records.
    """
    run_dir = os.path.abspath(run_dir)
    if doc is None:
        path = os.path.join(run_dir, "turn_series.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                doc = json.load(fh)
        else:
            doc = archive.turn_series(run_dir)

    rows = list(doc.get("rows") or [])
    levels = _levels(run_dir)
    boundaries = _boundary_turns(levels)

    # Which level each turn belongs to. `bisect` on the boundary turns: a turn
    # at or after the k-th boundary is in level k+1. The boundary event is
    # observed *at* the step whose envelope carries the new count, so the turn
    # carrying it is the new level's first -- `inner/levels.py:observe` says so
    # in as many words, and getting this off by one would attribute the first
    # turn of every level to the previous one, which is the single most
    # expensive turn on a front-loaded curve.
    import bisect                                       # noqa: PLC0415

    flat: List[Dict[str, Any]] = []
    per_level: Dict[int, List[Dict[str, Any]]] = {}
    in_leg = 0.0
    in_level: Dict[int, float] = {}

    for ordinal, row in enumerate(rows, start=1):
        turn = row.get("turn")
        level = (1 + bisect.bisect_right(boundaries, turn)
                 if isinstance(turn, int) else 1)
        usd = float(row.get("usd") or 0.0)
        in_leg += usd
        in_level[level] = in_level.get(level, 0.0) + usd
        counts = row.get("surprise_counts") or {}
        record = {
            "level": level,
            "turn": turn,
            "campaign_turn_in_leg": ordinal,
            "step_idx": row.get("step_idx"),
            "http_commands": int(row.get("http_commands") or 0),
            "actions_taken": row.get("actions_taken"),
            "theorize_rounds": row.get("theorize_rounds"),
            "model_calls": row.get("model_calls"),
            "usd": round(usd, 9),
            "usd_cumulative_in_level": round(in_level[level], 9),
            "usd_cumulative_in_leg": round(in_leg, 9),
            "surprise_total": row.get("surprise_total"),
            # A turn the loop opened, billed, and never wrote to `turns.json`.
            # False on every recorded turn, so the column is a measurement on
            # every row rather than a key that appears only when something went
            # wrong -- and a reader of the CSV can see at a glance which row
            # carries money the run itself never attributed.
            "turn_record_missing": bool(row.get("turn_record_missing")),
        }
        for kind in archive.KINDS:
            record["surprise_%s" % kind] = int(counts.get(kind) or 0)
        flat.append(record)
        per_level.setdefault(level, []).append(record)

    blocks = [_level_block(level, per_level[level])
              for level in sorted(per_level)]

    accounted = sum(r["http_commands"] for r in flat)
    ledger = _ledger_facts(run_dir)
    ledger_env_steps = ledger["env_steps"]
    billed = sum(int(r["model_calls"] or 0) for r in flat)
    curve_usd = sum(float(r["usd"] or 0.0) for r in flat)
    unrecorded = [r for r in flat if r["turn_record_missing"]]

    out = {
        "schema": SCHEMA,
        "run_id": doc.get("run_id"),
        "game_id": doc.get("game_id"),
        "slug": doc.get("slug") or os.path.basename(os.path.normpath(run_dir)),
        "levels_source": levels.get("_source"),
        "level_boundaries_at_turn": boundaries,
        "join_confidence": (doc.get("join") or {}).get("join_confidence"),
        "columns": list(COLUMNS),
        "levels": blocks,
        "rows": flat,
        "totals": {
            "turns": len(flat),
            "levels": len(blocks),
            "usd": round(in_leg, 9),
            "theorize_rounds": sum(int(r["theorize_rounds"] or 0) for r in flat),
            "surprises": sum(int(r["surprise_total"] or 0) for r in flat),
        },
        "self_check": {
            "turns": len(flat),
            "http_commands_over_the_curves": accounted,
            "env_step_records_in_the_ledger": ledger_env_steps,
            "accounts_for_every_env_step": accounted == ledger_env_steps,
            "billed_calls_over_the_curves": billed,
            "model_call_records_in_the_ledger": ledger["billed_calls"],
            "accounts_for_every_billed_call": billed == ledger["billed_calls"],
            "usd_over_the_curves": round(curve_usd, 9),
            "usd_in_the_ledger": round(ledger["usd"], 9),
            "usd_tolerance": USD_TOLERANCE,
            "accounts_for_every_dollar": (abs(curve_usd - ledger["usd"])
                                          <= USD_TOLERANCE),
            "turns_with_no_record_of_their_own": [
                {"turn": r["turn"], "step_idx": r["step_idx"],
                 "model_calls": r["model_calls"], "usd": r["usd"]}
                for r in unrecorded],
            "why": ("a curve is allowed to have fewer turns than the ledger "
                    "has commands -- a turn issues several -- but it is never "
                    "allowed to account for fewer commands than were issued. "
                    "That difference is a hole in the accounting, and it is "
                    "invisible in the plot: the curve just looks shorter."),
            "why_money_too": (
                "the command equality above is blind to money, and that "
                "blindness had a cost. Two live legs ended on a tripped spend "
                "gate; the final desk call of each was billed by the pool and "
                "landed in no turn row, because inner/loop.py appends a turn "
                "record only after the turn's last ARC command and the gate "
                "killed the turn before it sent one. The missing turn had "
                "issued no command, so `http_commands` balanced exactly -- and "
                "the curve understated the leg by 17% and 12.5%. Commands and "
                "dollars are counted separately because a hole can open in "
                "either without moving the other."),
            "floor": ("zero turns is refused outright. 0 == 0 satisfies the "
                      "equality above, so an empty leg would otherwise write a "
                      "file of zeros that reads exactly like a leg that was "
                      "cheap."),
            "unattributed": (
                "a turn the loop opened and never wrote down still gets a row "
                "-- flagged `turn_record_missing`, carrying its calls and its "
                "dollars, owning no ARC command. Absence is recorded as "
                "absence; a cost that vanishes is worse than a cost with no "
                "turn number."),
        },
        "reading": (
            "Three curves per level: `theorize_rounds` (expected to fall "
            "toward zero after the first level -- that is C3's carrying "
            "claim), the seven surprise counts (a record of what the world "
            "did, not of what was paid for), and cumulative cost. The "
            "front-load index over these is E2 in battery/metrics/economy.py "
            "and is deliberately not recomputed here: a second implementation "
            "of a Phase 4 primary endpoint is a second definition of it."),
    }
    if not flat:
        # An empty result is not a pass. The equality below is satisfied by
        # `0 == 0`, so without this floor a leg that never took a turn writes a
        # syntactically perfect `curves.json` full of zeros -- and zeros in a
        # cost curve read as "this leg was cheap", not as "this leg did not
        # happen". `theoria-arm/verify.py` opens with the same rule and the
        # same example (`figures/verify.sh` printed "ok" when both of its
        # builds produced nothing, because two empty trees are byte-identical).
        raise CurveGap(
            "no turns to reduce in %s: the series carries %d row(s) and the "
            "ledger records %d env_step(s). If both are zero the leg never "
            "played and has no curve to write; if the ledger has commands and "
            "the series has no rows, the join lost every one of them. Either "
            "way a file of zeros would be read as a cheap leg."
            % (run_dir, len(rows), ledger_env_steps))
    if accounted != ledger_env_steps:
        raise CurveGap(
            "the curves account for %d environment command(s) but the ledger "
            "records %d env_step(s) in %s. %d turn(s) over %d level(s) were "
            "reduced; a difference here means turns were dropped between the "
            "join and the cut, and the missing cost would never be noticed in "
            "the figure."
            % (accounted, ledger_env_steps, run_dir, len(flat), len(blocks)))
    # The two the command equality cannot see. Same class of failure, same
    # refusal: a curve that does not account for every billed call is a *wrong*
    # curve, and it is wrong in the direction that makes the campaign look
    # cheaper than it was.
    if billed != ledger["billed_calls"]:
        raise CurveGap(
            "the curves account for %d billed model call(s) but the ledger "
            "records %d model_call(s) in %s. %d turn(s) were reduced. A call "
            "with no turn is still a call that was paid for: it belongs in the "
            "curve as an unattributed row with its reason, never as a gap. "
            "(This is exactly what a leg killed by the spend gate looks like "
            "-- the last call is billed and its turn is never written down.)"
            % (billed, ledger["billed_calls"], run_dir, len(flat)))
    if abs(curve_usd - ledger["usd"]) > USD_TOLERANCE:
        raise CurveGap(
            "the curves total $%.6f over %d turn(s) but the ledger's "
            "model_call records total $%.6f in %s -- a difference of $%.6f, "
            "past the $%g the producers' own 9-dp rounding can explain. The "
            "curve is the raw material for figure 2 and for C2; a bill shape "
            "drawn from it would be the shape of a bill nobody was sent."
            % (curve_usd, len(flat), ledger["usd"], run_dir,
               ledger["usd"] - curve_usd, USD_TOLERANCE))
    return out


def _level_block(level: int, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One level's three curves, as series rather than as records.

    Series and not a row list, because that is what a plot consumes and
    because the three are *different lengths conceptually*: the surprise curve
    is seven parallel series over the same axis. Emitting them as seven named
    lists keeps the seven kinds in `archive.KINDS` order in the file, which a
    dict-of-dicts sorted by key would not.
    """
    return {
        "level": level,
        "turns": [r["turn"] for r in rows],
        "first_turn": rows[0]["turn"] if rows else None,
        "last_turn": rows[-1]["turn"] if rows else None,
        "theorize_rounds": [r["theorize_rounds"] for r in rows],
        "surprises": {kind: [r["surprise_%s" % kind] for r in rows]
                      for kind in archive.KINDS},
        "surprise_total": [r["surprise_total"] for r in rows],
        "usd": [r["usd"] for r in rows],
        "usd_cumulative": [r["usd_cumulative_in_level"] for r in rows],
        "totals": {
            "turns": len(rows),
            "usd": round(sum(r["usd"] for r in rows), 9),
            "theorize_rounds": sum(int(r["theorize_rounds"] or 0)
                                   for r in rows),
            "http_commands": sum(r["http_commands"] for r in rows),
            "surprises": {kind: sum(r["surprise_%s" % kind] for r in rows)
                          for kind in archive.KINDS},
        },
    }


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")


def write_curves(run_dir: str, *, doc: Optional[Dict[str, Any]] = None
                 ) -> Dict[str, Any]:
    """`curves()` on disk: one file for the leg, one per level beside it.

    Nothing is written unless `curves()` returned, so a run whose accounting
    has a hole leaves no `curves.json` at all rather than a plausible-looking
    one. A missing file is a question somebody asks; a short curve is not.
    """
    out = curves(run_dir, doc=doc)
    _write_json(os.path.join(run_dir, "curves.json"), out)

    per_level_dir = os.path.join(run_dir, "curves")
    os.makedirs(per_level_dir, exist_ok=True)
    for block in out["levels"]:
        _write_json(os.path.join(per_level_dir,
                                 "level-%02d.json" % block["level"]),
                    dict(block, schema=SCHEMA, slug=out["slug"],
                         run_id=out["run_id"], columns=list(COLUMNS)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--write", action="store_true",
                    help="write curves.json and curves/level-NN.json; without "
                         "it the document is printed and nothing is written")
    args = ap.parse_args(argv)

    if args.write:
        out = write_curves(args.run_dir)
    else:
        out = curves(args.run_dir)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
