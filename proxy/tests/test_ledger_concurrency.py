"""Several real OS processes, one ledger file. The chain must not fork.

`LEDGER_FORMAT.md` §2 promises that `seq` is "monotonic within the file,
assigned by the writer under a lock. Gaps are impossible; duplicates are a
corrupt file." Until item A10 that promise was kept only within one process:
`Ledger` held a `threading.Lock` and seeded its counter **once, in the
constructor**, so a writer that opened the file while another was mid-run
resumed from an already-invalid `seq`. Both then emitted the same `seq` and the
same `prev`, and the hash chain forked -- which `verify_chain` reports as a
BREAK, and `--emit-head` then refuses to publish provenance for.

That is not hypothetical. `theoria-arm/runs/pytest-test_the_shell_turns_end_to_en0/
ledger.jsonl` carries exactly one such fork at 2026-07-28T23:39:49Z: 253 lines,
seq 137-143 each written twice, no gaps and no lost records -- two pytest
sessions overlapping. A10 points three real arms at one shared ledger, so the
same window would be open three ways.

**Every process test here launches real interpreters.** A thread-only test
passes against the broken writer -- its `threading.Lock` was never the missing
piece -- and would have proved nothing. This repo has been bitten repeatedly by
checks that pass because they have no failing path, so the two in-process tests
at the bottom exist as well: they open the seed-to-append window directly and
deterministically, without depending on process timing.

    cd proxy && python -m pytest tests/test_ledger_concurrency.py
"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from proxy.ledger import Ledger, LedgerLockUnavailable, read_ledger   # noqa: E402
from proxy.tools import verify_chain                                  # noqa: E402
from proxy.tools.validate_ledger import validate_records             # noqa: E402


#: Each worker is a separate interpreter, so it shares no lock object, no
#: counter and no memory with any other -- only the file and the sidecar.
WORKER = textwrap.dedent(r'''
    import json, random, sys, time
    sys.path.insert(0, %(repo)r)
    from proxy.ledger import Ledger

    path, run_id, seed, rounds, open_delay, pause = sys.argv[1:7]
    rng = random.Random(int(seed))
    out = {"run_id": run_id, "seqs": [], "error": None}
    try:
        # Opening late is the poisoned file's exact shape: this writer seeds its
        # counter while another is part-way through a run.
        time.sleep(float(open_delay))
        led = Ledger(path)
        for i in range(int(rounds)):
            time.sleep(rng.random() * float(pause))   # interleave the appends
            record = led.append("env_meta", run_id, "probe", http={"i": i})
            out["seqs"].append(record["seq"])
    except Exception as exc:
        out["error"] = "%%s: %%s" %% (type(exc).__name__, exc)
    print(json.dumps(out))
''')


def run_fleet(tmp_path, *, workers, rounds, stagger=0.0, pause=0.01):
    """Launch `workers` interpreters against one ledger; return their reports.

    `stagger` delays each worker's *open* by a further step, and `pause` sets
    how long each worker's run lasts. The two together are what puts a writer's
    seed inside another writer's run: with a stagger longer than a run the
    fleet is serial, every seed is fresh, and the pre-fix writer passes.
    """
    path = str(tmp_path / "ledger.jsonl")
    script = tmp_path / "ledger_worker.py"
    script.write_text(WORKER % {"repo": REPO}, encoding="utf-8")

    procs = []
    for i in range(workers):
        procs.append(subprocess.Popen(
            [sys.executable, str(script), path, "r-%d" % i, str(1000 + i),
             str(rounds), str(i * stagger), str(pause)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    reports = []
    for proc in procs:
        stdout, stderr = proc.communicate(timeout=300)
        assert proc.returncode == 0, stderr
        reports.append(json.loads(stdout.strip().splitlines()[-1]))
    return path, reports


def _assert_dense_unique_and_chained(path, reports, *, workers, rounds):
    assert not any(r["error"] for r in reports), [r["error"] for r in reports]

    records = read_ledger(path)
    expected = workers * rounds
    assert len(records) == expected, \
        "%d records on disk, %d were written" % (len(records), expected)

    seqs = [r["seq"] for r in records]
    duplicates = sorted({s for s in seqs if seqs.count(s) > 1})
    assert not duplicates, "duplicate seq %r -- two writers took the same " \
                           "number, so the chain forked" % (duplicates,)
    assert seqs == list(range(1, expected + 1)), \
        "seq is not dense and ascending: %r" % (seqs[:20],)

    # The reader-side judgement, from the same code that judged the poisoned
    # file: no duplicate_seq, no sparse_seq.
    problems = validate_records(records)
    assert not problems, problems

    report = verify_chain.verify(path)
    assert report["verdict"] == "PASS", report
    assert report["breaks"] == []
    assert report["chained"] == expected

    # Nothing lost: every seq a worker believes it wrote is on disk, once,
    # against that worker's run.
    for r in reports:
        mine = [rec["seq"] for rec in records if rec["run_id"] == r["run_id"]]
        assert mine == r["seqs"], (r["run_id"], mine, r["seqs"])


# -- the deliverable: real processes ----------------------------------------

def test_three_processes_appending_at_once_do_not_fork_the_chain(tmp_path):
    """Three arms, one shared ledger -- item A10's actual configuration.

    All three open the file at the same moment, so every one of them seeds from
    the same empty file. Against the pre-fix writer that alone forks the chain:
    three counters all start at 0 and all three write seq 1.
    """
    path, reports = run_fleet(tmp_path, workers=3, rounds=12)
    _assert_dense_unique_and_chained(path, reports, workers=3, rounds=12)


def test_a_process_that_opens_mid_run_resumes_from_the_real_tail(tmp_path):
    """The poisoned file's shape: staggered opens, so each later writer seeds
    while the earlier ones are still appending. Its seed is stale the moment it
    is taken, and only a re-read inside the lock can save it.

    Measured against the pre-fix writer these settings gave 48 records with no
    gaps and nothing lost, and every seq from 4 upwards written twice -- the
    poisoned file's signature exactly.
    """
    path, reports = run_fleet(tmp_path, workers=4, rounds=12, stagger=0.15,
                              pause=0.08)
    _assert_dense_unique_and_chained(path, reports, workers=4, rounds=12)


def test_every_worker_actually_got_through(tmp_path):
    """The negative control. Four processes that all wrote nothing would satisfy
    "no duplicates, no gaps" perfectly."""
    path, reports = run_fleet(tmp_path, workers=4, rounds=6)
    assert all(len(r["seqs"]) == 6 for r in reports), reports
    assert len({r["run_id"] for r in read_ledger(path)}) == 4


def test_no_line_is_torn_by_a_concurrent_append(tmp_path):
    """Every line is complete JSON. A half-written record makes the file
    unreadable from that point, and it is append-only, so it stays that way."""
    path, _ = run_fleet(tmp_path, workers=3, rounds=10)
    with open(path, "rb") as fh:
        raw = [l.rstrip(b"\r\n") for l in fh]
    assert raw, "nothing was written"
    for line in raw:
        assert line.strip(), "the writer never emits a blank line"
        record = json.loads(line.decode("utf-8"))
        assert record["event"] == "env_meta" and isinstance(record["seq"], int)


# -- the seed-to-append window, deterministically ---------------------------

def test_two_writers_opened_before_either_wrote_do_not_collide(tmp_path):
    """The window at its smallest, with no timing in it at all.

    Both objects seed from the same empty file, so both hold `seq == 0`. A
    writer that trusts its constructor's snapshot gives them both seq 1.
    """
    path = str(tmp_path / "ledger.jsonl")
    first, second = Ledger(path), Ledger(path)      # both seeded, neither wrote
    a = first.append("env_meta", "r1", "probe", http={"who": "first"})
    b = second.append("env_meta", "r2", "probe", http={"who": "second"})

    assert (a["seq"], b["seq"]) == (1, 2)
    assert b["prev"] is not None and a["prev"] is None
    assert verify_chain.verify(path)["verdict"] == "PASS"


def test_a_stale_seed_is_never_the_number_that_gets_written(tmp_path):
    """The incident's arithmetic, reproduced exactly.

    `second` seeds at seq 3 and then `first` writes four more records before
    `second` gets its turn. The pre-fix writer hands `second` seq 4 -- a number
    already on disk -- and every record after it repeats one.
    """
    path = str(tmp_path / "ledger.jsonl")
    first = Ledger(path)
    for i in range(3):
        first.append("env_meta", "r1", "probe", http={"i": i})

    second = Ledger(path)                    # seeds at seq 3: correct, briefly
    for i in range(4):
        first.append("env_meta", "r1", "probe", http={"i": 3 + i})   # now stale

    record = second.append("env_meta", "r2", "probe", http={"late": True})
    assert record["seq"] == 8, \
        "resumed from the constructor's snapshot, not from the file"
    assert [r["seq"] for r in read_ledger(path)] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert verify_chain.verify(path)["verdict"] == "PASS"


def test_a_reopened_writer_still_resumes_a_file_it_never_saw(tmp_path):
    """The sequential case that already worked keeps working -- it is the path
    the existing tests cover, and the fix must not trade one for the other."""
    path = str(tmp_path / "ledger.jsonl")
    for _ in range(3):
        Ledger(path).append("env_meta", "r1", "probe", http={})
    assert [r["seq"] for r in read_ledger(path)] == [1, 2, 3]
    assert verify_chain.verify(path)["verdict"] == "PASS"


# -- the lock itself ---------------------------------------------------------

def test_the_lock_is_a_file_other_processes_can_see(tmp_path):
    """An in-process lock leaves no trace on disk; this one has to.

    Pinned because the regression is invisible otherwise: swapping the sidecar
    back for a `threading.Lock` passes every single-process test in this suite.
    """
    path = str(tmp_path / "ledger.jsonl")
    Ledger(path).append("env_meta", "r1", "probe", http={})
    assert os.path.exists(path + ".lock"), \
        "no sidecar lock file: the critical section is not cross-process"


def test_the_writer_fails_closed_without_a_lock_primitive(tmp_path, monkeypatch):
    """No `fcntl`, no `msvcrt`, no write.

    Appending anyway would produce a record indistinguishable from a locked one
    -- and the file is append-only, so it could not be taken back.
    """
    from proxy import ledger as ledger_module
    monkeypatch.setattr(ledger_module, "fcntl", None)
    monkeypatch.setattr(ledger_module, "msvcrt", None)

    path = str(tmp_path / "ledger.jsonl")
    led = Ledger(path)
    with pytest.raises(LedgerLockUnavailable):
        led.append("env_meta", "r1", "probe", http={})
    assert not os.path.exists(path), "a refused append must write nothing"


def test_a_held_lock_makes_the_next_writer_wait_rather_than_race(tmp_path):
    """A writer that cannot take the lock in time refuses; it does not proceed
    unlocked. Held by a real second process, since that is the case that
    matters."""
    path = str(tmp_path / "ledger.jsonl")
    holder_src = tmp_path / "holder.py"
    holder_src.write_text(textwrap.dedent(r'''
        import sys, time
        sys.path.insert(0, %(repo)r)
        from proxy.ledger import _ChainLock
        with _ChainLock(sys.argv[1], timeout=30.0):
            print("held", flush=True)
            time.sleep(float(sys.argv[2]))
    ''') % {"repo": REPO}, encoding="utf-8")

    holder = subprocess.Popen(
        [sys.executable, str(holder_src), path + ".lock", "5"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == "held"
        led = Ledger(path, lock_timeout=0.5)
        with pytest.raises(LedgerLockUnavailable):
            led.append("env_meta", "r1", "probe", http={})
        assert not os.path.exists(path), "the refused append wrote nothing"
    finally:
        holder.kill()
        holder.communicate(timeout=60)

    # And once the holder is gone the ledger is writable again: the refusal
    # above is a wait that expired, not a permanently poisoned writer.
    assert Ledger(path).append("env_meta", "r1", "probe", http={})["seq"] == 1
