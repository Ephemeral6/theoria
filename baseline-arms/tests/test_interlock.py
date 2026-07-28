"""The serialisation interlock (INC-BA-003, BUDGET_REPORT.md 11.5).

The process lister is injected, so these run without spawning anything and
without depending on what happens to be running on the machine.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import interlock                                       # noqa: E402

NOW = 1_800_000_000.0            # fixed clock; nothing here reads the real one


def lister(rows, error=None):
    return lambda: (rows, error)


def checkpoint(tmp_path, name, **state):
    directory = tmp_path / "baseline-arms" / "out" / "campaign"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(state), encoding="utf-8")
    return str(tmp_path)


def iso(epoch):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


# ------------------------------------------------------------ process table
def test_a_live_campaign_process_blocks():
    state = interlock.check(
        lister=lister([(4242, "python -u -m harness.campaign --game g50t-5849a774")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]
    assert "pid 4242" in state["blockers"][0]


def test_a_live_run_campaign_process_blocks():
    state = interlock.check(
        lister=lister([(7, "python -m harness.run_campaign --game sk48-d8078629")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]


def test_our_own_process_does_not_block_us():
    state = interlock.check(
        lister=lister([(99, "python -m harness.run_campaign --game g50t")]),
        roots=[], now=NOW, own_pid=99)
    assert state["clear"], state["blockers"]


def test_campaign_status_is_not_a_campaign():
    """It prints a table and spends nothing; blocking on it would deadlock the
    obvious way of checking whether it is safe to start."""
    state = interlock.check(
        lister=lister([(5, "python -m harness.campaign_status")]),
        roots=[], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


def test_unrelated_python_does_not_block():
    state = interlock.check(
        lister=lister([(5, "python -m pytest tests/"),
                       (6, "python -m harness.summarise_campaign"),
                       (7, "python -m tools.validate_candidates x.jsonl")]),
        roots=[], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


# --------------------------------------------------------------- checkpoints
def test_a_fresh_running_checkpoint_blocks(tmp_path):
    root = checkpoint(tmp_path, "campaign_g50t.json", game_id="g50t-5849a774",
                      status="running", cost_usd=11.07, http_calls=2803,
                      live_episode={"at": iso(NOW - 120)})
    state = interlock.check(lister=lister([]), roots=[root], now=NOW, own_pid=1)
    assert not state["clear"]
    assert "campaign_g50t.json" in state["blockers"][0]


def test_a_stale_running_checkpoint_does_not_block_forever(tmp_path):
    """A killed process must not wedge the track. Reported, but not blocking."""
    root = checkpoint(tmp_path, "campaign_g50t.json", game_id="g50t-5849a774",
                      status="running", cost_usd=11.07,
                      live_episode={"at": iso(NOW - 6 * 3600)})
    state = interlock.check(lister=lister([]), roots=[root], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]
    assert state["checkpoints"][0]["stale_running"] is True


def test_a_finished_checkpoint_does_not_block(tmp_path):
    root = checkpoint(tmp_path, "campaign_tn36.json", game_id="tn36-ef4dde99",
                      status="episode_limit_hit", cost_usd=8.28,
                      ended=iso(NOW - 60))
    state = interlock.check(lister=lister([]), roots=[root], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


def test_the_newest_episode_end_counts_as_activity(tmp_path):
    """A campaign between episodes has no live_episode key -- the freshness has
    to come from the episode list, or a between-episode campaign reads as dead."""
    root = checkpoint(tmp_path, "campaign_sk48.json", game_id="sk48-d8078629",
                      status="running", started=iso(NOW - 20 * 3600),
                      episodes=[{"n": 1, "ended": iso(NOW - 19 * 3600)},
                                {"n": 2, "ended": iso(NOW - 300)}])
    state = interlock.check(lister=lister([]), roots=[root], now=NOW, own_pid=1)
    assert not state["clear"]


def test_an_unreadable_checkpoint_is_reported_not_crashed(tmp_path):
    directory = tmp_path / "baseline-arms" / "out" / "campaign"
    directory.mkdir(parents=True)
    (directory / "campaign_x.json").write_text("{ truncated", encoding="utf-8")
    state = interlock.check(lister=lister([]), roots=[str(tmp_path)], now=NOW,
                            own_pid=1)
    assert "unreadable" in state["checkpoints"][0]


# ------------------------------------------------------------- failing closed
def test_no_signal_at_all_blocks():
    """Neither a process table nor a checkpoint to fall back on. Not knowing is
    not the same as knowing there is nothing."""
    state = interlock.check(lister=lister([], error="ps: not found"),
                            roots=[], now=NOW, own_pid=1)
    assert not state["clear"]
    assert "cannot determine" in state["blockers"][0]


def test_a_finished_checkpoint_does_not_rescue_a_failed_process_scan(tmp_path):
    """The hole the P-12 review found. The fail-closed branch used to clear when
    any checkpoint file existed -- but only harness/campaign.py writes one, so
    for run_campaign / bare_cc / run_pilot the checkpoint signal can never say
    yes, and four terminal checkpoints were already on disk. The fallback
    silenced fail-closed in every real situation while looking like a second
    opinion."""
    root = checkpoint(tmp_path, "campaign_tn36.json", game_id="tn36-ef4dde99",
                      status="episode_limit_hit", ended=iso(NOW - 60))
    state = interlock.check(lister=lister([], error="ps: not found"),
                            roots=[root], now=NOW, own_pid=1)
    assert not state["clear"]
    assert any("process table is unavailable" in b for b in state["blockers"])
    assert state["process_scan_error"] == "ps: not found"


def test_an_unreadable_checkpoint_blocks(tmp_path):
    """An unknown state is not an answered one."""
    directory = tmp_path / "baseline-arms" / "out" / "campaign"
    directory.mkdir(parents=True)
    (directory / "campaign_x.json").write_text("{ truncated", encoding="utf-8")
    state = interlock.check(lister=lister([]), roots=[str(tmp_path)], now=NOW,
                            own_pid=1)
    assert not state["clear"]
    assert any("could not be read" in b for b in state["blockers"])


def test_a_clear_scan_with_both_signals_present(tmp_path):
    root = checkpoint(tmp_path, "campaign_ar25.json", game_id="ar25-0c556536",
                      status="episode_limit_hit", ended=iso(NOW - 3600))
    state = interlock.check(lister=lister([(1, "python -m pytest")]),
                            roots=[root], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


# -------------------------------------------------------- combined exposure
def test_combined_exposure_adds_both_campaigns():
    checkpoints = [{"cost_usd": 11.56, "http_calls": 3471},
                   {"cost_usd": 8.28, "http_calls": 2588}]
    ex = interlock.combined_exposure(checkpoints, envelope_usd=2.5275,
                                     envelope_http=425)
    assert ex["other_campaigns_usd"] == 19.84
    assert ex["combined_usd"] == 22.3675
    assert ex["combined_http"] == 6484
    assert ex["other_campaign_count"] == 2


def test_combined_exposure_tolerates_missing_fields():
    ex = interlock.combined_exposure([{}, {"cost_usd": None}], envelope_usd=1.0)
    assert ex["combined_usd"] == 1.0
    assert ex["combined_http"] == 0


# ------------------------------------------------------------------ plumbing
def test_the_real_process_lister_works_on_this_platform():
    """Not a mock. If this fails the interlock is running on one signal."""
    rows, error = interlock.list_processes()
    assert error is None, error
    assert rows, "the process table came back empty"
    assert any(isinstance(pid, int) for pid, _ in rows)


def test_worktree_roots_includes_this_checkout():
    roots = interlock.worktree_roots()
    assert any(os.path.realpath(r) == os.path.realpath(interlock.REPO)
               for r in roots)


# ---------------------------------------------- read-only invocations
def test_a_gate_only_reader_is_not_a_live_campaign():
    """Observed for real: three concurrent `--gate-only` readers showed up as
    three live campaigns. The obvious way to ask "is it safe to start" must not
    be the thing that says no."""
    state = interlock.check(
        lister=lister([(11, "python -m harness.run_campaign --gate-only")]),
        roots=[], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


def test_a_dry_run_fetch_is_not_a_live_campaign():
    state = interlock.check(
        lister=lister([(12, "python -m harness.fetch_schema_traces --dry-run")]),
        roots=[], now=NOW, own_pid=1)
    assert state["clear"], state["blockers"]


def test_a_real_campaign_still_blocks_when_a_reader_is_also_running():
    state = interlock.check(
        lister=lister([(11, "python -m harness.run_campaign --gate-only"),
                       (12, "python -u -m harness.campaign --game g50t-5849a774")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]
    assert len(state["processes"]) == 1
    assert state["processes"][0]["pid"] == 12


def test_a_nohup_wrapper_and_its_child_are_both_reported():
    """Both are real: the wrapper exits with the child, so neither wedges the
    check, and reporting both is more honest than guessing which is which."""
    state = interlock.check(
        lister=lister([(1000, 'nohup.exe python -u -m harness.campaign --game g50t'),
                       (1001, "python.exe -u -m harness.campaign --game g50t")]),
        roots=[], now=NOW, own_pid=1)
    assert len(state["processes"]) == 2



# ------------------------------------------- what the review found (P-12)
def test_a_read_only_flag_inside_an_argument_value_does_not_excuse_a_campaign():
    """The exclusion is a whole-argument match, not a substring of the command
    line. A prompt or a path containing the text must not silence it."""
    state = interlock.check(
        lister=lister([(13, "python -m harness.run_campaign --game g50t "
                            "--note 'see --gate-only for the read-only path'")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]


def test_gate_only_only_excuses_run_campaign():
    """It is run_campaign's flag. A `--gate-only` token on any other module is
    somebody's quoted text, not a read-only invocation."""
    state = interlock.check(
        lister=lister([(15, "python -m harness.campaign --gate-only")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]


def test_m_without_a_space_is_still_a_campaign():
    state = interlock.check(
        lister=lister([(14, "python -mharness.campaign --game g50t-5849a774")]),
        roots=[], now=NOW, own_pid=1)
    assert not state["clear"]


def test_combined_exposure_counts_the_episode_in_flight():
    """Leaving live_episode out understates the other campaign by exactly the
    episode running right now -- which is when anyone reads the number."""
    checkpoints = [{"cost_usd": 12.55, "http_calls": 2803, "live": True,
                    "live_episode": {"cost_usd": 0.32}}]
    ex = interlock.combined_exposure(checkpoints, envelope_usd=2.5275)
    assert ex["other_campaigns_usd"] == 12.87
    assert ex["other_campaigns_live"] == 1


def test_combined_exposure_separates_live_campaigns_from_finished_ones():
    checkpoints = [{"cost_usd": 8.28, "live": False},
                   {"cost_usd": 12.55, "live": True}]
    ex = interlock.combined_exposure(checkpoints)
    assert ex["other_campaign_count"] == 2
    assert ex["other_campaigns_live"] == 1


def test_every_spending_entry_point_consults_the_interlock():
    """D-017 claims the two campaigns are serialised. Serialisation that holds
    in one direction only just decides which campaign loses the race."""
    import inspect
    from harness import bare_cc, campaign, run_campaign, run_pilot
    for module in (campaign, run_campaign, run_pilot, bare_cc):
        source = inspect.getsource(module.main)
        assert "interlock.check()" in source, module.__name__
