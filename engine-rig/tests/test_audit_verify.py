"""The E7 verifier, checked the way the verifier checks the run.

`audit/verify.py` is the thing standing between `DEADLOCK_CLAIM.md` and the
possibility that its numbers quietly stopped describing
`runs/20260728T150713Z-E7-deadlock-claim-audit/`.  A verifier that passes
because it is not looking is worse than none, so this module asserts three
different things about it:

* it **passes** on the real run directory, offline and with a planner;
* it **fails**, with a legible reason, when an artefact the manifest hashes is
  edited -- tested on a temporary copy, because a test that corrupts the run it
  is verifying has destroyed the evidence;
* the numbers it pins are **the numbers in the document**, parsed out of
  `DEADLOCK_CLAIM.md`'s own tables rather than retyped a second time here.

Everything runs on a machine with no planner.  The one check that needs Fast
Downward skips, on the same convention as `test_bench.py` and
`test_audit_claim.py` and for the same reason: it is about a real planner by
definition.
"""

import json
import os
import re
import shutil

import pytest

from audit import verify
from engines.fd_adapter import backends

pytestmark = pytest.mark.filterwarnings("ignore")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(HERE, "runs", "20260728T150713Z-E7-deadlock-claim-audit")
CLAIM_MD = os.path.join(HERE, "DEADLOCK_CLAIM.md")

FD = backends.find_fast_downward()
needs_fd = pytest.mark.skipif(FD is None, reason="no Fast Downward reachable")


def _ignore(_directory, names):
    """Copy everything but the 1232 raw FD logs and the bytecode cache."""
    return [n for n in names if n.endswith(".log") or n == "__pycache__"]


@pytest.fixture
def copied_run(tmp_path):
    """A disposable copy of the run, at a depth where `../../` still resolves.

    The manifest lists `../../DEADLOCK_CLAIM.md`, so the copy has to sit two
    directories below a copy of the document or check 1 would report it missing
    for a reason that has nothing to do with what is being tested.
    """
    rig = tmp_path / "engine-rig"
    target = rig / "runs" / os.path.basename(RUN)
    shutil.copytree(RUN, str(target), ignore=_ignore)
    shutil.copy2(CLAIM_MD, str(rig / "DEADLOCK_CLAIM.md"))
    return str(target)


# ------------------------------------------------------------ it passes, really

def test_the_committed_run_directory_is_still_there():
    """Every assertion below is blind if this one fails."""
    assert os.path.isfile(os.path.join(RUN, "MANIFEST.json")), RUN
    assert os.path.isfile(os.path.join(RUN, "claim_audit.json")), RUN


def test_the_real_run_verifies():
    """The headline. Exit 0, with FD if there is one and without if there is not."""
    assert verify.main([RUN]) == 0


def test_the_manifest_is_finished_and_lists_what_it_should():
    """A manifest still marked in-progress cannot be the record of a done run."""
    with open(os.path.join(RUN, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    for required in ("prompt_id", "branch", "base_commit", "utc"):
        assert manifest.get(required), required
    assert manifest["status"] == "done"
    assert {w["id"] for w in manifest["worker"]} == {"W-1411", "W-130"}
    listed = {entry["path"] for entry in manifest["files"]}
    assert "claim_audit.json" in listed
    assert "../../DEADLOCK_CLAIM.md" in listed
    assert manifest["soundness_problems"] == []
    # The logs are listed as directories with a stated reason, not hashed one by
    # one -- 1232 entries would make the manifest unreadable.
    assert manifest["directories"]
    assert manifest["why_the_directories_are_not_hashed_file_by_file"]


# ------------------------------------------------------------ it fails, really

def test_an_edited_artefact_is_caught_on_a_copy(copied_run, monkeypatch, capsys):
    """The check that gives every other check its point.

    The copy verifies first -- otherwise a failure after the edit would prove
    only that the copy was broken -- and then one byte is appended to
    `claim_audit.json`, which leaves it valid JSON and changes its hash.
    """
    monkeypatch.setattr(verify.backends, "find_fast_downward", lambda: None)

    assert verify.main([copied_run]) == 0, "the untouched copy must verify"
    capsys.readouterr()

    edited = os.path.join(copied_run, "claim_audit.json")
    with open(edited, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n")

    assert verify.main([copied_run]) == 1
    out = capsys.readouterr().out
    assert "claim_audit.json" in out
    assert "edited after the run" in out
    # And only that: an edit to one artefact must not smear across the report.
    assert "FAIL (1)" in out


def test_a_missing_artefact_is_reported_rather_than_skipped(copied_run):
    manifest_path = os.path.join(copied_run, "MANIFEST.json")
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    os.remove(os.path.join(copied_run, "attacks", "a7_hunt.json"))
    problems, _note = verify.check_manifest_hashes(copied_run, manifest)
    assert problems == ["missing: attacks/a7_hunt.json"]


def test_a_manifest_listing_nothing_is_a_failure_not_a_pass(tmp_path):
    """An empty files[] would otherwise make check 1 vacuously green."""
    problems, note = verify.check_manifest_hashes(str(tmp_path), {"files": []})
    assert problems and "nothing was checked" in problems[0]
    assert note == "0 files"


# ------------------------------------------------------ it skips, with a reason

def test_the_fd_check_skips_cleanly_with_no_planner(monkeypatch, capsys):
    """Offline is the state of every machine that has not built `.toolchain/`.

    The rest of the audit is pure Python over committed artefacts, so a missing
    planner must cost exactly one check and must say so.
    """
    monkeypatch.setattr(verify.backends, "find_fast_downward", lambda: None)
    assert verify.main([RUN]) == 0
    out = capsys.readouterr().out
    assert out.count("SKIP") == 1
    assert "reason: No Fast Downward reachable" in out
    assert "TOOLCHAIN_MANIFEST.md" in out
    assert "(FD checks skipped)" in out
    # Everything else still ran.
    assert out.count("PASS") == 7
    assert "FAIL" not in out


# ------------------------------------------------------------ the pinned numbers

def test_rnd0021_is_re_derived_from_the_generator_not_read(capsys):
    """Section 3a's counterexample, recomputed from `random_level(seed=20260728)`.

    Structural and planner-free: 92 reachable states, all truly dead, 59 the
    relaxation catches, 70 the theorems catch, and the 11 that are the whole
    point -- theorem-dead states Fast Downward's own pre-search relaxation calls
    alive. If any of those five move, section 3a is describing a different
    instance.
    """
    problems, note, derived = verify.check_rnd0021(RUN)
    assert problems == []
    assert derived["n_reachable"] == 92
    assert derived["n_truly_dead"] == 92
    assert derived["n_relaxation_dead"] == 59
    assert derived["n_theorem_dead"] == 70
    assert derived["n_theorem_dead_outside_relaxation"] == 11
    assert derived["n_theorem_dead_not_truly_dead"] == 0, "the carver must be sound"
    assert "11 outside the relaxation" in note


def test_the_carver_is_sound_on_far4_and_on_the_counterexample():
    _problems, _note, rnd = verify.check_rnd0021(RUN)
    problems, note = verify.check_soundness({"soundness_problems": []}, rnd)
    assert problems == []
    assert "far4 0/1624" in note


def test_a_recorded_soundness_problem_is_not_swallowed():
    """The manifest's own field has to reach the report, or it is decoration."""
    _problems, _note, rnd = verify.check_rnd0021(RUN)
    problems, _note2 = verify.check_soundness(
        {"soundness_problems": ["a theorem covered a live state"]}, rnd)
    assert any("a theorem covered a live state" in line for line in problems)


# --------------------------------------- the pins are the document's own numbers

def _table(header_starts_with):
    """The rows of the first markdown table whose header line matches."""
    with open(CLAIM_MD, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for index, line in enumerate(lines):
        if line.startswith(header_starts_with):
            rows = []
            for row in lines[index + 2:]:          # skip the |---|---| divider
                if not row.startswith("|"):
                    break
                rows.append([cell.strip() for cell in row.strip("|").split("|")])
            return rows
    raise AssertionError("no table under %r in DEADLOCK_CLAIM.md"
                         % header_starts_with)


def _plain(cell):
    return cell.replace("`", "").replace("*", "").strip()


def test_the_replication_pins_are_section_1s_own_table():
    """Retyping the table into `verify.py` is a second chance to mistype it."""
    rows = _table("| instance | configuration | before | after |")
    parsed = []
    for instance, config, before, after, dividend, _e2 in rows:
        percent = float(_plain(dividend).replace("−", "").rstrip("%"))
        parsed.append((_plain(instance), _plain(config), int(_plain(before)),
                       int(_plain(after)), percent))
    assert parsed == list(verify.REPLICATION)


def test_the_coverage_pins_are_section_3s_own_table():
    rows = _table("| instance | reachable | truly dead |")
    parsed = [(_plain(a), int(_plain(b)), int(_plain(c)), int(_plain(d)),
               int(_plain(e))) for a, b, c, d, e, _f in rows]
    assert parsed == list(verify.COVERAGE)
    # The last column -- the zero the document turns on -- is checked too.
    assert all(int(_plain(row[5])) == 0 for row in rows)


def test_the_crosscheck_total_is_the_one_section_3_prints():
    """116/116, not the 16/16 an earlier draft published."""
    with open(CLAIM_MD, encoding="utf-8") as fh:
        text = fh.read()
    assert "**116/116**" in text
    assert verify.CROSSCHECK_TOTAL == 116
    total = 0
    for relative in verify.CROSSCHECKS:
        with open(os.path.join(RUN, relative), encoding="utf-8") as fh:
            total += json.load(fh)["n_checked"]
    with open(os.path.join(RUN, "claim_audit.json"), encoding="utf-8") as fh:
        total += json.load(fh)["relaxation_vs_fd"]["n_checked"]
    assert total == 116


def test_the_rnd0021_pins_are_the_numbers_section_3a_prints():
    """The counterexample's five numbers, read out of the prose that states them."""
    with open(CLAIM_MD, encoding="utf-8") as fh:
        text = fh.read()
    block = text[text.index("### 3a"):]
    assert re.search(r"92 reachable, 0 goal states, 92 truly dead", block)
    assert re.search(r"relaxation dead 59 . theorem dead 70 . outside the "
                     r"relaxation 11", block)
    assert verify.RND0021["n_reachable"] == 92
    assert verify.RND0021["n_truly_dead"] == 92
    assert verify.RND0021["n_relaxation_dead"] == 59
    assert verify.RND0021["n_theorem_dead"] == 70
    assert verify.RND0021["n_theorem_dead_outside_relaxation"] == 11


# ---------------------------------------------------------- timings, never equal

def test_timings_are_checked_for_order_and_never_for_equality():
    with open(os.path.join(RUN, "claim_audit.json"), encoding="utf-8") as fh:
        report = json.load(fh)
    problems, note = verify.check_timings(report)
    assert problems == []
    assert "timings present and ordered" in note

    # A search that took longer than the run containing it is a parsing bug.
    report["seconds"] = 0.001
    problems, _note = verify.check_timings(report)
    assert problems and "misparsed" in problems[0]


def test_a_measurement_with_no_timing_and_no_error_is_a_problem():
    report = {"seconds": 1.0,
              "rows": [{"heuristic": "lmcut", "search_seconds": None,
                        "error": None}]}
    problems, _note = verify.check_timings(report)
    assert problems and "no search time recorded" in problems[0]


def test_an_fd_refusal_without_a_timing_is_not_counted_against_the_run():
    """The `full` guard exits 34 on axioms before it searches; there is no clock."""
    report = {"seconds": 1.0,
              "rows": [{"heuristic": "lmcut", "search_seconds": None,
                        "error": "no plan file and no proof (exit 34, ...)"}]}
    problems, _note = verify.check_timings(report)
    assert problems == []


# --------------------------------------------------------- needs a real planner

@needs_fd
def test_the_structural_facts_still_measure_the_same(tmp_path):
    """far4 blind 837 -> 610, and every dead start at 0 expansions with h=infinity.

    Exact equality, on the same tasks: node counts, plan lengths, task sizes and
    exit codes are a function of the instance and the configuration.
    """
    with open(os.path.join(RUN, "claim_audit.json"), encoding="utf-8") as fh:
        report = json.load(fh)
    problems, note = verify.check_structural_fd(
        report, FD, str(tmp_path / "instances"), str(tmp_path / "logs"))
    assert problems == [], problems
    assert "measurements re-derived" in note


@needs_fd
def test_the_planner_in_front_of_us_is_the_one_the_run_recorded():
    """Without this, check 7 could pass against a different build that agreed."""
    from bench import toolchain

    with open(os.path.join(RUN, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    live = toolchain.probe(FD, os.path.dirname(HERE))
    assert manifest["toolchain"]["binary_sha256"] == live["binary_sha256"]
