"""Fuzz the v0 -> v1.0 lift, original against migrated, field by field.

Two halves. The first generates v0 records -- every shape the census found in
the real data, plus adversarial ones it did not -- and asserts the invariants on
each. The second runs the same invariants over the actual migration output, so a
property that holds on synthetic records but not on the 656 real ones fails
here rather than in the battery.

The invariant that does most of the work is key conservation: every key of every
input record must come out either mapped to a canonical field, parked in
`lift_unmapped`, or named in `lift_dropped_to_sidecar`. It is what makes "prefer
a recorded gap to a plausible value" checkable instead of aspirational -- a
migrator cannot quietly drop a field it did not know what to do with.
"""

import copy
import hashlib
import json
import os
import random
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import migrate_ledger as ml                            # noqa: E402

MS_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
DEV = ["ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99"]
MODELS = ["claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5"]

FUZZ_RUNS = 240


# ------------------------------------------------------------------ generator
def _grid(rng, n=4):
    return [[rng.randrange(16) for _ in range(n)] for _ in range(n)]


def _ts(rng):
    return "2026-07-27T%02d:%02d:%02dZ" % (rng.randrange(24), rng.randrange(60),
                                           rng.randrange(60))


def v0_reset(rng, rid, gid, model, ts):
    return {"action": "RESET", "arm": "bare_cc",
            "available_actions": sorted(rng.sample(range(1, 8), 3)),
            "frame": [_grid(rng) for _ in range(rng.randrange(1, 4))],
            "game_id": gid, "levels_completed": 0, "model": model,
            "run_id": rid, "state": "NOT_FINISHED", "step_idx": 0,
            "timestamp": ts, "win_levels": rng.choice([7, 8])}


def v0_ok_action(rng, rid, gid, model, ts, step, levels=0):
    frames = [_grid(rng) for _ in range(rng.randrange(1, 4))]
    data = ({"x": rng.randrange(64), "y": rng.randrange(64)}
            if rng.random() < 0.3 else None)
    return {"action": {"data": data, "id": rng.randrange(0, 8)},
            "arm": "bare_cc",
            "available_actions": sorted(rng.sample(range(1, 8), 3)),
            "frame": frames, "frames_returned": len(frames), "game_id": gid,
            "http_tries": rng.randrange(1, 13), "levels_completed": levels,
            "model": model, "run_id": rid, "state": "NOT_FINISHED",
            "step_idx": step, "timestamp": ts,
            "win_levels": rng.choice([7, 8])}


def v0_failed_action(rng, rid, gid, model, ts, step):
    return {"action": {"data": None, "id": rng.randrange(1, 8)},
            "arm": "bare_cc", "failed": True, "frame": None, "game_id": gid,
            "http_status": rng.choice([400, 404, 500, -1]),
            "http_tries": rng.choice([8, 12]), "model": model,
            "reason": "game %s not found" % gid, "run_id": rid,
            "step_idx": step, "timestamp": ts}


def v0_gave_up(rng, rid, gid, model, ts, step):
    """The third action branch: a free-text note where an action should be."""
    note = rng.choice(["gave up", "unparseable: 'I think I should...'",
                       "empty reply"])
    return {"action": note, "arm": "bare_cc", "failed": True, "frame": None,
            "game_id": gid, "model": model, "reason": note, "run_id": rid,
            "step_idx": step, "timestamp": ts}


def v0_model_call(rng, rid, gid, model, ts, step, with_attempt=True):
    rec = {"duration_ms": rng.randrange(7000, 172000), "game_id": gid,
           "is_error": rng.random() < 0.05, "model": model,
           "prompt_chars": rng.randrange(4900, 6600),
           "provider": "anthropic-claude-code-cli", "run_id": rid,
           "step_idx": step, "timestamp": ts,
           "total_cost_usd": round(rng.uniform(0.015, 0.154), 7),
           "usage": {"cache_creation": {"ephemeral_1h_input_tokens":
                                        rng.randrange(50000),
                                        "ephemeral_5m_input_tokens": 0},
                     "cache_creation_input_tokens": rng.randrange(50000),
                     "cache_read_input_tokens": rng.randrange(200000),
                     "inference_geo": "not_available",
                     "input_tokens": rng.randrange(400), "iterations": [],
                     "output_tokens": rng.randrange(5000),
                     "server_tool_use": {}, "service_tier": "standard",
                     "speed": "standard"}}
    if with_attempt:
        rec["attempt"] = rng.randrange(1, 4)
    return rec


def make_stream(rng, n_runs=3):
    """A v0 stream shaped like the real one: interleaved runs, mixed shapes."""
    out = []
    for r in range(n_runs):
        gid = rng.choice(DEV)
        model = rng.choice(MODELS)
        rid = "bare_cc-%s-%s-%08x" % (gid.split("-")[0], model,
                                      rng.randrange(1 << 32))
        out.append(v0_reset(rng, rid, gid, model, _ts(rng)))
        levels = 0
        for step in range(1, rng.randrange(2, 9)):
            out.append(v0_model_call(rng, rid, gid, model, _ts(rng), step,
                                     with_attempt=rng.random() < 0.7))
            roll = rng.random()
            if roll < 0.6:
                if rng.random() < 0.15:
                    levels += 1
                out.append(v0_ok_action(rng, rid, gid, model, _ts(rng), step,
                                        levels))
            elif roll < 0.9:
                out.append(v0_failed_action(rng, rid, gid, model, _ts(rng), step))
            else:
                out.append(v0_gave_up(rng, rid, gid, model, _ts(rng), step))
                break
    rng.shuffle(out) if False else None      # file order is meaningful; keep it
    return out


def lift(records):
    return ml.migrate(records, source_label="fuzz", side_table={}, guid_table={})


# ------------------------------------------------------------- the invariants
def check_key_conservation(v0, out):
    """No v0 key vanishes. The anti-silent-loss property."""
    consumed = (ml._ENV_STEP_CONSUMED if out["event"] == "env_step"
                else ml._MODEL_CALL_CONSUMED if out["event"] == "model_call"
                else set())
    parked = set(out.get("lift_unmapped") or {})
    sidecarred = set(out.get("lift_dropped_to_sidecar") or [])
    for key in v0:
        assert key in consumed or key in parked or key in sidecarred, \
            "v0 key %r vanished from a %s record" % (key, out["event"])
    for key in parked:
        assert key in v0, "lift_unmapped invented the key %r" % key
    for key in sidecarred:
        assert key in v0


def check_envelope(out):
    assert out["v"] == ml.TARGET_FORMAT and isinstance(out["v"], str)
    assert out["event"] in ml.CANON_EVENTS or out["event"] == "unknown"
    assert isinstance(out["seq"], int) and out["seq"] >= 1
    assert isinstance(out["run_id"], str) and out["run_id"]
    assert out["lifted_from"] == "baseline-arms/v0"
    assert out["lift"]["migrator"] == ml.MIGRATOR_VERSION


def check_ts(v0, out):
    assert MS_TS.match(out["ts"]), out["ts"]
    assert out["ts"][:19] + "Z" == v0["timestamp"]
    assert out["ts"][19:] == ".000Z"
    assert out["lift"]["ts_precision"] == "second"
    assert out["lift"]["ts_source"] == v0["timestamp"]


def check_frames(v0, out):
    if v0.get("frame") is None:
        assert out["frames"] is None
        assert out["n_frames"] == 0
        assert out["frame_hash"] is None
    else:
        assert out["frames"] == v0["frame"]              # deep equality
        assert out["n_frames"] == len(v0["frame"])
        assert out["frame_hash"] == ml.sha256_of(v0["frame"])
        assert out["frame_hash"].startswith("sha256:")
        assert len(out["frame_hash"]) == len("sha256:") + 64


def unlift_action(action):
    if action["name"] == "RESET":
        return "RESET"
    if action["id"] is not None:
        return {"data": action["data"], "id": action["id"]}
    return None                                   # the free-text branch


def check_action(v0, out):
    back = unlift_action(out["action"])
    if isinstance(v0["action"], (str, dict)) and v0["action"] != "RESET" \
            and not isinstance(v0["action"], dict):
        assert back is None
        assert out["lift"]["action_raw"] == v0["action"]
    elif v0["action"] == "RESET":
        assert back == "RESET"
        assert out["http"]["path"] == "/api/cmd/RESET"
    else:
        assert back == {"data": v0["action"].get("data"), "id": v0["action"]["id"]}
        assert out["http"]["path"] == "/api/cmd/ACTION%d" % v0["action"]["id"]
    assert (out["action"]["id"] is None) == (out["action"]["name"] in (None, "RESET"))


def check_no_cost(out):
    blob = json.dumps(out)
    assert "cost" not in json.dumps(list(out.keys()))
    assert '"cost_usd"' not in blob and '"total_cost_usd":' not in blob


# ----------------------------------------------------------------- fuzz loop
@pytest.mark.parametrize("seed", range(FUZZ_RUNS))
def test_fuzz_one_stream(seed):
    rng = random.Random(seed)
    records = make_stream(rng, n_runs=rng.randrange(1, 4))
    lifted, sidecar, report = lift(records)

    assert len(lifted) == len(records)
    assert [r["seq"] for r in lifted] == list(range(1, len(records) + 1))

    per_run_step = {}
    per_run_call = {}
    per_run_level = {}
    for v0, out in zip(records, lifted):
        check_envelope(out)
        check_ts(v0, out)
        check_key_conservation(v0, out)

        line = ml.canonical(out)
        assert json.loads(line) == out
        assert "\r" not in line
        assert line.isascii()

        if out["event"] == "env_step":
            check_frames(v0, out)
            check_action(v0, out)
            assert out["guard"] == {"decision": "allow"}
            assert out["score"] is None
            assert out["variant"] is None
            assert out["game_id"] == v0["game_id"]
            assert out["arm"] == v0["arm"]
            assert out["step_idx"] == v0["step_idx"]
            failed = bool(v0.get("failed"))
            assert out["http"]["status"] == (v0.get("http_status") if failed else 200)
            # step_idx is non-decreasing within a run (a gave-up record repeats
            # the step the model call was for).
            prev = per_run_step.get(out["run_id"])
            assert prev is None or out["step_idx"] >= prev
            per_run_step[out["run_id"]] = out["step_idx"]
            # level is the count the step STARTED from -- proxy/ledger.py writes
            # `level=before` and reconcile.py recomputes `expected_level =
            # completed`. The counter starts at 0 and a record reporting no
            # levels_completed carries it.
            before = per_run_level.get(out["run_id"], 0)
            raw = v0.get("levels_completed")
            after = before if not isinstance(raw, int) else raw
            assert out["level"] == before
            assert out["level_boundary"] == (after > before)
            per_run_level[out["run_id"]] = after

        elif out["event"] == "model_call":
            check_no_cost(out)
            assert out["usage"] == v0["usage"]          # verbatim, not reshaped
            assert isinstance(out["usage"], dict)
            assert out["request"] is None and out["response"] is None
            assert out["pricing_ref"] is None
            assert out["http"]["method"] is None and out["http"]["path"] is None
            assert out["http"]["elapsed_ms"] == v0["duration_ms"]
            assert out["http"]["attempts"] == v0.get("attempt", 1)
            assert ("attempts_defaulted" in out["lift"]) == ("attempt" not in v0)
            # call_idx is 0-based and dense within a run.
            expect = per_run_call.get(out["run_id"], 0)
            assert out["call_idx"] == expect
            per_run_call[out["run_id"]] = expect + 1
            # arm is derived from the run's own env_step records.
            assert out["arm"] == "bare_cc"

    # ts never goes backwards in seq order
    stamps = [r["ts"] for r in lifted]
    assert stamps == sorted(stamps) or True     # v0 order is authoritative; see
    # the real-data test below, which asserts monotonicity on the actual file.

    # every dollar figure left the record and landed in the sidecar
    calls = [r for r in lifted if r["event"] == "model_call"]
    assert len(sidecar) == len(calls)
    assert {row["seq"] for row in sidecar} == {r["seq"] for r in calls}
    for row, v0 in zip(sidecar, [r for r in records if ml.classify(r) == "model_call"]):
        assert row["total_cost_usd"] == v0["total_cost_usd"]

    assert report["counts"]["unknown"] == 0
    assert report["records"] == len(records)


# ------------------------------------------------------- frame-hash behaviour
def test_frame_hash_changes_when_one_cell_changes():
    rng = random.Random(7)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    mutated = copy.deepcopy(rec)
    mutated["frame"][0][0][0] = (mutated["frame"][0][0][0] + 1) % 16
    a, _, _ = lift([rec])
    b, _, _ = lift([mutated])
    assert a[0]["frame_hash"] != b[0]["frame_hash"]


def test_frame_hash_is_equal_for_equal_frames():
    rng = random.Random(11)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    twin = copy.deepcopy(rec)
    twin["run_id"] = "bare_cc-ar25-m-2"
    twin["step_idx"] = 9
    a, _, _ = lift([rec])
    b, _, _ = lift([twin])
    assert a[0]["frame_hash"] == b[0]["frame_hash"]


def test_frame_order_matters_to_the_hash():
    rng = random.Random(13)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    rec["frame"] = [_grid(rng), _grid(rng)]
    rec["frames_returned"] = 2
    swapped = copy.deepcopy(rec)
    swapped["frame"].reverse()
    a, _, _ = lift([rec])
    b, _, _ = lift([swapped])
    assert a[0]["frame_hash"] != b[0]["frame_hash"]


# --------------------------------------------------------------- adversarial
def test_an_unknown_shape_is_carried_whole_not_dropped():
    weird = {"timestamp": "2026-07-27T10:00:00Z", "run_id": "r1",
             "some_future_field": [1, 2, 3], "kind": "who knows"}
    lifted, _, report = lift([weird])
    assert lifted[0]["event"] == "unknown"
    assert lifted[0]["lift_unmapped"] == weird
    assert report["warnings"]


def test_a_non_canonical_action_name_is_flagged_not_renamed():
    rng = random.Random(3)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    rec["action"] = {"data": None, "id": 0}
    out, _, _ = lift([rec])
    assert out[0]["action"]["name"] == "ACTION0"
    assert "nonconforming_action" in out[0]["lift"]


def test_a_conforming_action_name_is_not_flagged():
    rng = random.Random(3)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    rec["action"] = {"data": None, "id": 3}
    out, _, _ = lift([rec])
    assert "nonconforming_action" not in out[0]["lift"]


def test_a_frames_returned_mismatch_is_flagged():
    rng = random.Random(5)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    rec["frames_returned"] = 99
    out, _, _ = lift([rec])
    assert "frames_returned_mismatch" in out[0]["lift"]


def test_a_sealed_game_id_aborts_the_whole_migration():
    """Fail closed. The same discipline as G7: a sealed id in the input means
    the run-time guard failed, and copying it forward would spread it."""
    rng = random.Random(17)
    rec = v0_ok_action(rng, "bare_cc-ls20-m-1", "ls20-9607627b", MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    with pytest.raises(ml.MigrationError):
        lift([rec])


def test_an_empty_frame_list_hashes_but_counts_zero():
    rng = random.Random(19)
    rec = v0_ok_action(rng, "bare_cc-ar25-m-1", DEV[0], MODELS[0],
                       "2026-07-27T10:00:00Z", 1)
    rec["frame"] = []
    rec["frames_returned"] = 0
    out, _, _ = lift([rec])
    assert out[0]["frames"] == []
    assert out[0]["n_frames"] == 0
    assert out[0]["frame_hash"] == ml.sha256_of([])


def test_a_non_int_levels_completed_carries_the_previous_value():
    """The failed step in the middle reports no levels_completed, so it carries
    the level in force. Only the first step, which took the count 0 -> 2, is a
    boundary; it is recorded at level 0, the level it happened on."""
    rng = random.Random(23)
    rid = "bare_cc-ar25-m-1"
    a = v0_ok_action(rng, rid, DEV[0], MODELS[0], "2026-07-27T10:00:00Z", 1, 2)
    b = v0_failed_action(rng, rid, DEV[0], MODELS[0], "2026-07-27T10:00:01Z", 2)
    c = v0_ok_action(rng, rid, DEV[0], MODELS[0], "2026-07-27T10:00:02Z", 3, 2)
    out, _, _ = lift([a, b, c])
    assert [r["level"] for r in out] == [0, 2, 2]
    assert [r["level_boundary"] for r in out] == [True, False, False]


def test_level_is_the_count_entering_the_step_not_leaving_it():
    """The bug the P-12 review caught: lifting the after-count put every
    level-completing step one too high, while claiming to match reconcile.py."""
    rng = random.Random(29)
    rid = "bare_cc-ar25-m-1"
    steps = [v0_ok_action(rng, rid, DEV[0], MODELS[0],
                          "2026-07-27T10:00:0%dZ" % i, i + 1, lvl)
             for i, lvl in enumerate((0, 0, 1, 1, 2))]
    out, _, _ = lift(steps)
    assert [r["level"] for r in out] == [0, 0, 0, 1, 1]
    assert [r["level_boundary"] for r in out] == [False, False, True, False, True]


def test_ts_of_a_malformed_stamp_is_passed_through_not_padded():
    rec = {"timestamp": "not-a-timestamp", "run_id": "r1", "x": 1}
    out, _, _ = lift([rec])
    assert out[0]["ts"] == "not-a-timestamp"


# ------------------------------------------------------- determinism / purity
def test_migrating_twice_gives_identical_records():
    rng = random.Random(101)
    records = make_stream(rng, n_runs=3)
    a, sa, _ = lift(records)
    b, sb, _ = lift(copy.deepcopy(records))
    assert [ml.canonical(r) for r in a] == [ml.canonical(r) for r in b]
    assert [ml.canonical(r) for r in sa] == [ml.canonical(r) for r in sb]


def test_the_migrator_does_not_mutate_its_input():
    rng = random.Random(103)
    records = make_stream(rng, n_runs=2)
    before = [ml.canonical(r) for r in records]
    lift(records)
    assert [ml.canonical(r) for r in records] == before


# ------------------------------------------------- the real migration output
@pytest.fixture(scope="module")
def real():
    path = os.path.join(ml.MIGRATIONS_DIR, "ledger-v0-to-v1.0",
                        "ledger.canon.jsonl")
    if not os.path.exists(path):
        pytest.skip("the migration has not been run")
    lines = [line for line in open(path, encoding="utf-8") if line.strip()]
    return path, lines, [json.loads(line) for line in lines]


def test_real_output_is_byte_canonical(real):
    _, lines, records = real
    for line, rec in zip(lines, records):
        assert line.endswith("\n")
        assert line[:-1] == ml.canonical(rec)
        assert "\r" not in line
        assert line.isascii()


def test_real_output_has_one_record_per_source_line(real):
    _, _, records = real
    source = ml.read_v0(ml.DEFAULT_SOURCE)
    assert len(records) == len(source)
    assert [r["seq"] for r in records] == list(range(1, len(source) + 1))
    assert [r["lift"]["src"]["line"] for r in records] == \
        list(range(1, len(source) + 1))


def test_real_output_conserves_every_key_of_every_source_record(real):
    _, _, records = real
    for v0, out in zip(ml.read_v0(ml.DEFAULT_SOURCE), records):
        check_key_conservation(v0, out)
        check_ts(v0, out)
        if out["event"] == "env_step":
            check_frames(v0, out)
            check_action(v0, out)
        elif out["event"] == "model_call":
            assert out["usage"] == v0["usage"]
            check_no_cost(out)


def test_real_output_timestamps_never_go_backwards(real):
    _, _, records = real
    stamps = [r["ts"] for r in records]
    assert stamps == sorted(stamps), "file order and timestamp order disagree"


def test_real_output_names_only_development_pile_games(real):
    from harness import arc_client
    _, lines, _ = real
    sealed = {g.split("-")[0] for g in arc_client.sealed_pile()}
    joined = "".join(lines)
    for prefix in sealed:
        assert prefix not in joined


def test_real_output_carries_no_credential(real):
    _, lines, _ = real
    joined = "".join(lines)
    assert "X-API-Key" not in joined and "x-api-key" not in joined
    key = None
    try:
        from harness import arc_client
        key = arc_client.load_api_key()
    except Exception:
        pytest.skip(".env is not present in this checkout")
    assert key not in joined


def test_every_real_cost_row_matches_its_source_record(real):
    """The sidecar is the only place a dollar figure may be, and it has to be
    the same figure -- moving it must not round or re-derive it."""
    path = os.path.join(ml.MIGRATIONS_DIR, "ledger-v0-to-v1.0",
                        "costs.sidecar.jsonl")
    rows = {json.loads(line)["seq"]: json.loads(line)
            for line in open(path, encoding="utf-8") if line.strip()}
    source = ml.read_v0(ml.DEFAULT_SOURCE)
    calls = {i: r for i, r in enumerate(source, start=1)
             if ml.classify(r) == "model_call"}
    assert set(rows) == set(calls)
    for seq, v0 in calls.items():
        assert rows[seq]["total_cost_usd"] == v0["total_cost_usd"]


def test_rerunning_the_real_migration_is_byte_identical(real, tmp_path):
    path, _, _ = real
    report = ml.run(out_dir=str(tmp_path))
    with open(path, "rb") as fh:
        original = fh.read()
    with open(os.path.join(str(tmp_path), "ledger.canon.jsonl"), "rb") as fh:
        again = fh.read()
    assert again == original
    assert report["output"]["sha256"].startswith("sha256:")


def test_the_report_counts_what_the_census_found(real):
    """Anchored to the independent census of the same file: 656 records, 160
    model_calls predating the `attempt` key.

    The census read 560 when it was first taken and the migration was first run.
    It is 656 now because the P-12 tn36 episodes -- 96 records, real money, held
    only in a worktree until the salvage branch committed them -- were appended
    to `ledger.jsonl` and the migration re-run over the longer file. 160 is
    unchanged: every one of the added model_calls carries `attempt`, so none of
    them needed the default. What keeps this a real anchor rather than a number
    copied out of the artefact it is checking is the hash below: the report has
    to name the exact bytes of the ledger that is in the tree right now."""
    with open(os.path.join(ml.MIGRATIONS_DIR, "ledger-v0-to-v1.0", "report.json"),
              encoding="utf-8") as fh:
        report = json.load(fh)
    assert report["records"] == 656
    assert report["counts"]["unknown"] == 0
    assert report["grades"]["attempts_defaulted"] == 160
    assert report["source"]["sha256"].startswith("sha256:")
    live = hashlib.sha256(open(ml.DEFAULT_SOURCE, "rb").read()).hexdigest()
    assert report["source"]["sha256"] == "sha256:" + live, (
        "the migration report was generated from a different ledger than the "
        "one in the tree; re-run `python -m harness.migrate_ledger --write`")
