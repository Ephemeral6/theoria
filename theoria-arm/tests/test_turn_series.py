"""`armtools.archive.turn_series` -- the turn-indexed join, and its honesty.

Three writers record the three quantities figure 2 needs and none of them
shares an index with the others. These tests hold the join to the properties
that make it worth trusting rather than merely available:

* **all seven surprise kinds on every row.** `inner/surprise.py` takes the
  position that a zero is a measurement and not an absence, and a series that
  emitted only the kinds that happened to fire would let a reader mistake "no
  proof failure" for "proof failures not measured";
* **the money reconciles.** Per-turn cost must sum to what the desk was billed.
  A join that redistributes cost is worse than no join;
* **byte-determinism.** The artefact goes in a release manifest;
* **the empty cases do not divide by zero, and do not lie.** A run with no
  model call has a shape of `None`, not a shape of `0.0`;
* **a turn whose theorize the evidence gate skipped is still a turn.** It is
  the point of the gate, and an earlier draft of the windowing silently handed
  such a turn's action to its successor.

Kept in its own file rather than appended to `test_arm.py` on purpose: that
file is being edited concurrently.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                      # noqa: E402,F401

from armtools import archive                           # noqa: E402
from inner.surprise import COMPUTATIONAL, EMPIRICAL, KINDS   # noqa: E402
from proxy import LEDGER_VERSION                       # noqa: E402

#: The one live run. 7 successful actions, 40 HTTP commands, 5 model calls all
#: at `theorize`, $6.317658, 8 surprises (4 render + 4 replay).
G50T = _bootstrap.path("runs", "20260728T015354Z-g50t-first-contact")
G50T_USD = 6.317658
G50T_SURPRISES = {"render_mismatch": 4, "replay_mismatch": 4}

needs_g50t = pytest.mark.skipif(
    not os.path.exists(os.path.join(G50T, "ledger.jsonl")),
    reason="the live g50t run is not present in this checkout")


# -- synthetic runs ---------------------------------------------------------
#
# Hand-built rather than replayed, because the two edges worth testing -- a run
# that never called a model, and a turn the evidence gate skipped -- are edges
# the one live run does not contain.

RID = "r-synthetic00000000"
T0 = 1_800_000_000


def _stamp(offset, *, seconds_only=False):
    import datetime
    when = datetime.datetime.fromtimestamp(T0 + offset, datetime.timezone.utc)
    if seconds_only:                      # what `inner/surprise.py` writes
        return when.strftime("%Y-%m-%dT%H:%M:%SZ")
    return when.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (
        int(round((offset - int(offset)) * 1000)))


class _Builder:
    """A run directory with the four files `turn_series` reads."""

    def __init__(self, root):
        self.root = str(root)
        os.makedirs(self.root, exist_ok=True)
        self.rows = []
        self.surprises = []
        self.turns = None
        self.calls = 0
        self.usd = 0.0
        self.actions_ok = 0
        self.actions_failed = 0
        self.resets = 0
        self._seq = 0
        self.event("run_start", 0)

    def event(self, kind, at, **extra):
        self._seq += 1
        row = {"v": LEDGER_VERSION, "event": kind, "run_id": RID,
               "seq": self._seq, "ts": _stamp(at), "arm": "theoria"}
        row.update(extra)
        self.rows.append(row)
        return row

    def step(self, name, at, status=200):
        self.event("env_step", at, action={"name": name, "id": None},
                   http={"status": status})
        if status == 200:
            if name == "RESET":
                self.resets += 1
            else:
                self.actions_ok += 1
        return self

    def call(self, at, *, step_idx, usd, label="round1", elapsed_ms=1000,
             beat="theorize"):
        self.event("model_call", at, call_idx=self.calls, step_idx=step_idx,
                   beat=beat, label=label, model="claude-opus-5",
                   usage={"input_tokens": 1, "output_tokens": 1},
                   http={"elapsed_ms": elapsed_ms},
                   response={"total_cost_usd": usd})
        self.calls += 1
        self.usd += usd
        return self

    def surprise(self, kind, at):
        self.surprises.append(
            {"seq": len(self.surprises) + 1, "kind": kind,
             "family": "empirical" if kind in EMPIRICAL else "computational",
             "book": "theory.dsl", "detail": "synthetic", "step_idx": None,
             "ts": _stamp(at, seconds_only=True), "handled_by": None,
             "payload": {}})
        return self

    def write(self):
        with open(os.path.join(self.root, "ledger.jsonl"), "w",
                  encoding="utf-8", newline="\n") as fh:
            for row in self.rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        with open(os.path.join(self.root, "surprises.jsonl"), "w",
                  encoding="utf-8", newline="\n") as fh:
            for row in self.surprises:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        run = {"summary": {
            "run_id": RID, "game_id": "g50t-5849a774",
            "budget": {"actions_ok": self.actions_ok,
                       "actions_failed": self.actions_failed,
                       "resets": self.resets},
            "desk": {"calls": self.calls,
                     "cli_cost_usd": round(self.usd, 9)}}}
        with open(os.path.join(self.root, "run.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(run, fh, indent=1, sort_keys=True)
        if self.turns is not None:
            with open(os.path.join(self.root, "turns.json"), "w",
                      encoding="utf-8", newline="\n") as fh:
                json.dump(self.turns, fh, indent=1, sort_keys=True)
        return self.root


def _gated_run(root):
    """Four turns, and turn 2's theorize is skipped by the evidence gate.

    Sweep of five, then a turn that theorizes once, then a turn that spends no
    model call at all -- it still takes an action and still meets a surprise,
    because plan and probe fire surprises for free -- then a turn that
    theorizes twice.
    """
    b = _Builder(root)
    b.turns = [
        {"turn": 0, "beat": "observe", "detail": "opening sweep over [1,2,3,4,5]",
         "actions_spent": 5},
        {"turn": 1, "actions_before": 5, "elapsed_s": 10.0,
         "theorize_rounds": 1},
        {"turn": 2, "actions_before": 6, "elapsed_s": 20.0,
         "theorize": ("skipped: 2 surprise(s) pending but only 1 new "
                      "transition(s) since the last call (want 4). Going to "
                      "get more.")},
        {"turn": 3, "actions_before": 7, "elapsed_s": 30.0,
         "theorize_rounds": 2},
    ]
    b.step("RESET", 1)
    for k in range(5):
        b.step("ACTION%d" % (k + 1), 2 + k)
    b.call(20, step_idx=6, usd=1.0, elapsed_ms=5000)
    b.surprise("render_mismatch", 22)
    b.step("ACTION1", 25, status=400)          # the retry burst belongs to t1
    b.step("ACTION1", 26)
    b.surprise("search_timeout", 28)           # a free turn's own surprise
    b.step("ACTION2", 30)
    b.call(40, step_idx=8, usd=2.0)
    b.call(45, step_idx=8, usd=0.5)            # second invocation, same turn
    b.surprise("replay_mismatch", 42)
    b.surprise("proof_failure", 42)
    b.step("ACTION3", 50)
    return b.write()


def _silent_run(root):
    """A run that never called a model. The division-by-zero edge."""
    b = _Builder(root)
    b.step("RESET", 1)
    for k in range(3):
        b.step("ACTION%d" % (k + 1), 2 + k)
    return b.write()


# -- all seven kinds, always ------------------------------------------------

@needs_g50t
def test_every_row_carries_all_seven_surprise_kinds_on_the_live_run():
    doc = archive.turn_series(G50T)
    assert doc["rows"], "the live run must produce at least one turn"
    for row in doc["rows"]:
        assert set(row["surprise_counts"]) == set(KINDS)
        assert len(KINDS) == 7


def test_a_run_with_no_surprise_at_all_still_reports_seven_zeros(tmp_path):
    doc = archive.turn_series(_silent_run(tmp_path / "silent"))
    for row in doc["rows"]:
        assert row["surprise_counts"] == {kind: 0 for kind in KINDS}
        assert row["surprise_total"] == 0
        assert row["surprise_by_family"] == {"empirical": 0,
                                             "computational": 0}
    # And the reconciliation histogram too -- a zero there is a measurement
    # for exactly the same reason.
    assert set(doc["reconciliation"]["surprises"]["by_kind_over_turns"]) \
        == set(KINDS)


def test_the_family_split_is_five_two_and_the_rows_respect_it(tmp_path):
    doc = archive.turn_series(_gated_run(tmp_path / "gated"))
    assert len(EMPIRICAL) == 5 and len(COMPUTATIONAL) == 2
    for row in doc["rows"]:
        counts = row["surprise_counts"]
        assert row["surprise_by_family"]["empirical"] == \
            sum(counts[k] for k in EMPIRICAL)
        assert row["surprise_by_family"]["computational"] == \
            sum(counts[k] for k in COMPUTATIONAL)
        assert row["surprise_total"] == sum(counts.values())


# -- the money reconciles ---------------------------------------------------

@needs_g50t
def test_the_per_turn_usd_sums_to_the_manifest_total():
    doc = archive.turn_series(G50T)
    manifest = json.load(open(os.path.join(G50T, "MANIFEST.json"),
                              encoding="utf-8"))
    billed = manifest["cost"]["cli_reported_usd"]
    assert billed == G50T_USD, "the ground truth moved; re-read the run first"
    assert sum(row["usd"] for row in doc["rows"]) == pytest.approx(billed, abs=1e-9)
    assert doc["totals"]["usd"] == pytest.approx(billed, abs=1e-9)
    assert doc["reconciliation"]["usd"]["reconciles"] is True
    assert doc["rows"][-1]["usd_cumulative"] == pytest.approx(billed, abs=1e-9)


@needs_g50t
def test_the_live_run_reconciles_on_every_axis_it_records():
    doc = archive.turn_series(G50T)
    recon = doc["reconciliation"]
    assert recon["usd"]["reconciles"] is True
    assert recon["surprises"]["reconciles"] is True
    assert recon["model_calls"]["reconciles"] is True
    assert recon["actions"]["reconciles"] is True
    assert doc["totals"]["model_calls"] == 5
    assert doc["totals"]["actions"] == 7
    assert doc["totals"]["surprises"] == 8
    kinds = recon["surprises"]["by_kind_over_turns"]
    assert {k: v for k, v in kinds.items() if v} == G50T_SURPRISES
    # Nothing was reconciled by being quietly dropped.
    assert doc["join"]["billed_calls_outside_their_own_turn_window"] == []
    assert all(c.get("ok") is not False for c in doc["join"]["checks"])


@needs_g50t
def test_the_cost_curve_and_the_turn_series_price_the_same_run():
    """The join redistributes cost onto turns; it must not create or lose any."""
    doc = archive.turn_series(G50T)
    curve = json.load(open(os.path.join(G50T, "cost_curve.json"),
                           encoding="utf-8"))
    assert sum(r["usd"] for r in curve) == pytest.approx(
        sum(r["usd"] for r in doc["rows"]), abs=1e-9)
    assert sorted(i for r in doc["rows"] for i in r["call_idx"]) == \
        sorted(r["call_idx"] for r in curve)


def test_a_synthetic_run_reconciles_too(tmp_path):
    doc = archive.turn_series(_gated_run(tmp_path / "gated"))
    assert doc["totals"]["usd"] == pytest.approx(3.5, abs=1e-9)
    assert doc["reconciliation"]["usd"]["reconciles"] is True
    assert doc["reconciliation"]["surprises"]["reconciles"] is True
    assert doc["reconciliation"]["actions"]["reconciles"] is True


# -- determinism ------------------------------------------------------------

def test_the_join_is_byte_identical_across_two_runs(tmp_path):
    root = _gated_run(tmp_path / "gated")
    first = archive.write_turn_series(root)
    with open(os.path.join(root, "turn_series.json"), "rb") as fh:
        bytes_one = fh.read()
    second = archive.write_turn_series(root)
    with open(os.path.join(root, "turn_series.json"), "rb") as fh:
        bytes_two = fh.read()
    assert bytes_one == bytes_two
    assert json.dumps(first, sort_keys=True, default=str) == \
        json.dumps(second, sort_keys=True, default=str)
    assert b"\r\n" not in bytes_one, "LF is pinned; CRLF would break the hash"


@needs_g50t
def test_the_live_run_joins_identically_twice():
    a = archive.turn_series(G50T)
    b = archive.turn_series(G50T)
    assert json.dumps(a, sort_keys=True, default=str) == \
        json.dumps(b, sort_keys=True, default=str)


@needs_g50t
def test_the_provenance_block_hashes_the_sources_it_actually_read():
    import hashlib
    doc = archive.turn_series(G50T)
    sources = doc["provenance"]["sources"]
    assert sources["ledger.jsonl"]["present"] is True
    # `turns.json` is genuinely absent on this run -- it was killed before
    # `_save_all()` -- and the block says so rather than omitting the key.
    assert sources["turns.json"]["present"] is False
    assert sources["turns.json"]["sha256"] is None
    with open(os.path.join(G50T, "surprises.jsonl"), "rb") as fh:
        assert sources["surprises.jsonl"]["sha256"] == \
            hashlib.sha256(fh.read()).hexdigest()


# -- the empty series -------------------------------------------------------

def test_a_run_with_no_model_call_has_no_shape_rather_than_a_shape_of_zero(
        tmp_path):
    doc = archive.turn_series(_silent_run(tmp_path / "silent"))
    assert doc["totals"]["model_calls"] == 0
    assert doc["totals"]["usd"] == 0
    assert doc["totals"]["billed_turns"] == 0
    for row in doc["rows"]:
        assert row["usd"] == 0
        assert row["usd_share"] == 0.0          # not a NaN, not an exception
    shape = archive.frontload_input(doc)
    for axis in ("all_turns", "billed_turns_only"):
        assert shape[axis]["frontload_index_25"] is None
        assert shape[axis]["status"] == "insufficient-data"
        assert "zero" in shape[axis]["reason"]


def test_an_entirely_empty_run_directory_does_not_raise(tmp_path):
    empty = tmp_path / "nothing"
    empty.mkdir()
    doc = archive.turn_series(str(empty))
    assert doc["rows"] == [] or all(r["usd"] == 0 for r in doc["rows"])
    assert doc["totals"]["usd"] == 0
    assert archive.frontload_input(doc)["all_turns"]["frontload_index_25"] \
        is None


# -- the turn the evidence gate skipped -------------------------------------

def test_a_gated_turn_is_a_turn_and_keeps_its_own_action_and_surprise(tmp_path):
    doc = archive.turn_series(_gated_run(tmp_path / "gated"))
    rows = {row["turn"]: row for row in doc["rows"]}
    assert sorted(rows) == [0, 1, 2, 3]

    gated = rows[2]
    assert gated["theorize_rounds"] == 0
    assert gated["model_calls"] == 0
    assert gated["usd"] == 0
    # The point of the test: the gated turn keeps the action it spent and the
    # surprise it met.  Forward-filling its window from turn 1 gave it an empty
    # interval and handed both to turn 3.
    assert gated["actions_taken"] == 1
    assert gated["surprise_total"] == 1
    assert gated["surprise_counts"]["search_timeout"] == 1

    assert rows[0]["actions_taken"] == 5 and rows[0]["usd"] == 0
    assert rows[1]["theorize_rounds"] == 1 and rows[1]["usd"] == pytest.approx(1.0)
    assert rows[1]["http_commands"] == 2      # the 400 retry rode with its 200
    assert rows[1]["actions_taken"] == 1
    assert rows[3]["theorize_rounds"] == 2 and rows[3]["usd"] == pytest.approx(2.5)
    assert rows[3]["call_idx"] == [1, 2]
    assert rows[3]["surprise_total"] == 2


def test_a_turns_json_spine_is_reported_as_an_exact_join(tmp_path):
    doc = archive.turn_series(_gated_run(tmp_path / "gated"))
    assert doc["join"]["join_confidence"] == "exact"
    assert doc["join"]["spine"] == "turns.json"
    assert all(c.get("ok") is not False for c in doc["join"]["checks"])


@needs_g50t
def test_a_missing_turns_json_is_declared_not_papered_over():
    """The live run has no `turns.json`; the join says so in the artefact."""
    doc = archive.turn_series(G50T)
    assert not os.path.exists(os.path.join(G50T, "turns.json"))
    assert doc["join"]["join_confidence"] == "exact-reconstructed"
    assert "reconstructed" in doc["join"]["spine"]


def test_an_ambiguous_reconstruction_lowers_the_confidence(tmp_path):
    """A gap of more than one store step admits two readings; say so."""
    b = _Builder(tmp_path / "ambiguous")
    b.step("RESET", 1)
    for k in range(5):
        b.step("ACTION%d" % (k + 1), 2 + k)
    b.call(20, step_idx=6, usd=1.0)
    b.step("ACTION1", 25)
    b.step("ACTION2", 26)
    b.step("ACTION3", 27)          # three steps before the next billed turn
    b.call(40, step_idx=9, usd=1.0)
    b.step("ACTION4", 50)
    doc = archive.turn_series(b.write())
    assert doc["join"]["join_confidence"] == "ambiguous-reconstructed"
    gaps = [c for c in doc["join"]["checks"] if c.get("gaps")]
    assert gaps and gaps[0]["gaps"][0]["store_steps_between"] == 3
    assert "evidence gate" in gaps[0]["gaps"][0]["readings"]


# -- the metric input -------------------------------------------------------

@needs_g50t
def test_the_interpolation_matches_the_batterys_own():
    """`_cost_through` is duplicated from `battery/metrics/economy.py`.

    Duplicated so this arm can read its own bill without importing the
    battery; pinned here so the duplicate cannot drift.
    """
    economy = pytest.importorskip("battery.metrics.economy")
    for costs in ([1.0, 2.0, 3.0, 4.0], [0.0, 5.0], [6.317658], [],
                  [3.626608, 2.69105]):
        for mark in (0.0, 0.25, 0.5, 0.75, 1.0, len(costs) * 0.25,
                     len(costs) * 0.9):
            assert archive._cost_through(costs, mark) == \
                economy._cost_through(costs, mark)
    assert archive.FRONTLOAD_K == economy.FRONTLOAD_K
    assert archive.MIN_TURNS_FOR_SHAPE == economy.MIN_TURNS_FOR_SHAPE


@needs_g50t
def test_the_billed_axis_matches_what_the_battery_would_build_itself():
    """The join and `battery.model.Run.turn_costs()` must agree.

    The battery reaches the same axis by a different route -- it buckets billed
    calls onto the `step_idx` they were deciding (`INPUT_FORMAT.md` gap 5) --
    so agreement here is two independent derivations landing on one answer,
    which is the strongest evidence available that the join key is right.
    """
    model = pytest.importorskip("battery.model")
    doc = archive.turn_series(G50T)
    curve = json.load(open(os.path.join(G50T, "cost_curve.json"),
                           encoding="utf-8"))
    distinct = sorted({r["step_idx"] for r in curve
                       if r.get("step_idx") is not None})
    turn_of = {step: n for n, step in enumerate(distinct)}
    run = model.Run(
        run_id=doc["run_id"], arm="theoria", source="test", intent="solve",
        game_id=doc["game_id"], pile="dev",
        calls=[model.Call(idx=r["call_idx"], step_idx=r["step_idx"],
                          cost_usd=r["usd"], turn=turn_of.get(r["step_idx"]))
               for r in curve])
    assert run.turn_costs() == \
        archive.frontload_input(doc)["turn_costs_billed_only"]


@needs_g50t
def test_the_live_runs_frontload_index_is_refused_for_being_short():
    """Three turns is below `MIN_TURNS_FOR_SHAPE`, and that is the reading.

    The ratio is still emitted -- suppressing it would hide the run's shape --
    but its status is `insufficient-data` on both axes, which is what the
    battery reports and what any figure must carry.
    """
    doc = archive.turn_series(G50T)
    shape = archive.frontload_input(doc)
    assert shape["turn_costs"] == [0, pytest.approx(3.626608),
                                   pytest.approx(2.69105)]
    assert shape["all_turns"]["turns"] == 3
    assert shape["billed_turns_only"]["turns"] == 2
    assert shape["all_turns"]["status"] == "insufficient-data"
    assert shape["billed_turns_only"]["status"] == "insufficient-data"
    # The two axes disagree completely, which is the finding: the free opening
    # sweep is the whole head of the all-turns axis.
    assert shape["all_turns"]["frontload_index_25"] == 0.0
    assert shape["billed_turns_only"]["frontload_index_25"] == \
        pytest.approx(0.287021551, abs=1e-9)


def test_a_flat_run_scores_a_quarter_on_the_interpolated_head():
    """The property v2.1 of E2 exists to have, checked on this reduction."""
    for n in (8, 9, 12, 40):
        shape = archive._frontload([1.0] * n)
        assert shape["status"] == "ok"
        assert shape["frontload_index_25"] == pytest.approx(0.25, abs=1e-9)
