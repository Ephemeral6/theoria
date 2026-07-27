"""The download whitelist is the one piece of this track whose failure is irreversible.

A sealed game's upstream trajectory directory contains that game's finished
`world_model_v*.py` and the author's `notes.md`. Fetching one does not cost
money and does not fail loudly -- it silently destroys that game's value as a
Phase 4 exam, and no later action undoes it. So the filter gets tests, and the
tests are written against *synthetic* paths built from `piles.json` ids, which
means running them needs no network and reveals nothing.

    cd baseline-arms && python -m pytest tests/ -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness.fetch_schema_traces import (  # noqa: E402
    WhitelistError, classify, dev_ids, match_dev, partition, sealed_ids,
)


@pytest.fixture(scope="module")
def piles():
    return dev_ids(), sealed_ids()


def verdict(path, piles):
    return classify(path, *piles)[0]


# -- the shape upstream actually uses: 4-character prefix, never the full id --
@pytest.mark.parametrize("path", [
    "claude_fable_opus/claude_fable_opus_max_ar25_100.0/run.json",
    "claude_fable_opus/claude_fable_opus_max_g50t_100.0/world_model_v3.py",
    "gpt_5_6_sol/gpt_5_6_sol_max_sk48/events.jsonl",
    "gpt_5_6_sol/gpt_5_6_sol_xhigh_tn36/sessions/a.jsonl",
    "claude_fable_opus/claude_fable_opus_max_tn36_94.74/snapshots/cleared_level_1.py",
])
def test_development_pile_is_allowed(path, piles):
    assert verdict(path, piles) == "allow"


def test_full_pile_id_still_matches(piles):
    dev, _ = piles
    assert verdict("traces/%s/run.json" % dev[0], piles) == "allow"


# -- the failures that matter ------------------------------------------------
@pytest.mark.parametrize("template", [
    "claude_fable_opus/claude_fable_opus_max_%s_99.0/notes.md",
    "gpt_5_6_sol/gpt_5_6_sol_max_%s/world_model_v1.py",
    "traces/%s/events.jsonl",
])
def test_every_sealed_game_is_denied(template, piles):
    _, sealed = piles
    for gid in sealed:
        assert verdict(template % gid.split("-")[0], piles) == "deny_sealed", gid
        assert verdict(template % gid, piles) == "deny_sealed", gid


def test_sealed_wins_when_a_path_names_both(piles):
    dev, sealed = piles
    both = "summary_%s_%s.json" % (dev[0].split("-")[0], sealed[0].split("-")[0])
    assert verdict(both, piles) == "deny_sealed"


def test_prefix_inside_a_hash_does_not_allow(piles):
    """`ar25` occurring inside a blob hash must not open the gate."""
    dev, _ = piles
    prefix = dev[0].split("-")[0]
    assert verdict("blobs/9%sf0e/chunk.json" % prefix, piles) == "deny_unknown"
    assert match_dev("blobs/9%sf0e/chunk.json" % prefix, dev) is None


@pytest.mark.parametrize("path", [
    "README.md",                                    # describes all 25 games
    ".gitattributes",
    "score_trajectories.py",
    "gpt_5_6_sol/evaluation_results.csv",           # per-game rows for all 25
    "gpt_5_6_sol/baseline_actions.csv",
    "claude_fable_opus/task_vs_human_baseline_5x5.png",
])
def test_gameless_paths_are_denied_by_default(path, piles):
    """Default deny. The aggregates are `scores_only` contamination for 21 games,
    and the rest are denied simply because nothing positively allowed them."""
    assert verdict(path, piles) == "deny_unknown"


def test_partition_refuses_to_return_a_sealed_path(piles, monkeypatch):
    """If `classify` were ever wrong, `partition`'s second, stricter check must
    still raise rather than hand a sealed path to the fetcher."""
    _, sealed = piles
    poisoned = "traces/%s/world_model.py" % sealed[0]
    monkeypatch.setattr("harness.fetch_schema_traces.classify",
                        lambda path, dev, seal: ("allow", "spoofed"))
    with pytest.raises(WhitelistError):
        partition([poisoned])


def test_the_two_piles_do_not_share_a_prefix(piles):
    """Prefix matching is only safe while prefixes are unique across the cut."""
    dev, sealed = piles
    dev_prefixes = {g.split("-")[0] for g in dev}
    sealed_prefixes = {g.split("-")[0] for g in sealed}
    assert dev_prefixes.isdisjoint(sealed_prefixes)
    assert len(dev_prefixes) == len(dev)
    assert len(sealed_prefixes) == len(sealed)
