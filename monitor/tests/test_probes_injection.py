"""Injection self-test for the two probes S16 added.

The ticket's second half: *"对每个探针做一次『注入式自检』——人为制造一个该报红的
情形，探针必须真的报红；不能自检的探针本身就是负资产。"*

That is not a style preference. Every one of the failures this ticket exists to
catch was a check that looked like it was working: the dashboard was green, the
probe ran, and the criterion had quietly stopped meaning anything. A probe with
no manufactured red has never been observed to do its job -- it has only been
observed not to complain.

So each case below builds the failing world on purpose and requires the red.
Each also has a companion green, because a probe hardwired to return `risk`
would satisfy the red half while being exactly as useless.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scan                                                     # noqa: E402


def _ops_status(tmp_path, monkeypatch, files):
    """Point scan at a throwaway tree holding exactly `files`."""
    root = tmp_path / "repo"
    d = root / "monitor" / "ops-status"
    d.mkdir(parents=True)
    for name, payload in files.items():
        p = d / ("%s.json" % name)
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(scan, "ROOT", str(root))
    return root


def _stamp(offset_seconds=0):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",
                         time.gmtime(time.time() + offset_seconds))


# ------------------------------------------------------------ clock_sanity

def test_a_heartbeat_from_the_future_is_red(tmp_path, monkeypatch):
    """The live case, reproduced: RES-1 claimed 20:55Z when it was 15:47Z.

    Nothing checked it, and the direction is the dangerous part -- a
    self-reported time that only runs forward makes a dropped session look
    fresher than it is.
    """
    _ops_status(tmp_path, monkeypatch, {
        "RES-9": {"id": "RES-9", "utc": _stamp(+5 * 3600), "cycle": 1,
                  "state": "working", "note": "hand-typed"},
    })
    r = scan.probe_clock_sanity()
    assert r["status"] == "risk", r
    assert "还没到" in r["detail"]
    assert "RES-9" in r["detail"]


def test_honest_heartbeats_are_green(tmp_path, monkeypatch):
    """The companion green.

    Without it a probe hardwired to `risk` would pass the test above while
    telling nobody anything.
    """
    _ops_status(tmp_path, monkeypatch, {
        "RES-9": {"id": "RES-9", "utc": _stamp(-120), "cycle": 3,
                  "state": "working", "note": "took the stamp from date -u"},
    })
    r = scan.probe_clock_sanity()
    assert r["status"] == "green", r


def test_a_stamp_that_cannot_be_parsed_is_red_not_ignored(tmp_path, monkeypatch):
    """"Unreadable" must not resolve to "fine".

    Skipping what it cannot parse is how a probe ends up reporting green over a
    field that stopped being written at all.
    """
    _ops_status(tmp_path, monkeypatch, {
        "RES-9": {"id": "RES-9", "utc": "yesterday afternoon", "state": "working"},
    })
    r = scan.probe_clock_sanity()
    assert r["status"] == "risk", r
    assert "读不出来" in r["detail"]


def test_a_missing_utc_field_is_red(tmp_path, monkeypatch):
    _ops_status(tmp_path, monkeypatch, {
        "RES-9": {"id": "RES-9", "cycle": 2, "state": "working"},
    })
    r = scan.probe_clock_sanity()
    assert r["status"] == "risk", r
    assert "没有 utc 字段" in r["detail"]


def test_a_stamp_far_from_the_files_mtime_is_partial(tmp_path, monkeypatch):
    """Backdating is the other direction, and it is a weaker signal.

    A stamp long before the file's own mtime means the agent wrote a time it
    remembered rather than one it measured. Not future-dated, so not the
    dangerous direction -- reported, not alarmed.
    """
    _ops_status(tmp_path, monkeypatch, {
        "RES-9": {"id": "RES-9", "utc": _stamp(-9 * 3600), "state": "working"},
    })
    r = scan.probe_clock_sanity()
    assert r["status"] == "partial", r
    assert "mtime" in r["detail"]


def test_no_heartbeats_at_all_does_not_read_as_green_by_accident(tmp_path,
                                                                 monkeypatch):
    """An empty directory satisfies every loop in the probe.

    This repo has been bitten repeatedly by exactly that shape, so the case is
    pinned even though the honest answer here is 'nothing to report': what must
    never happen is a *risk* being hidden, and with zero files there is none.
    The value of the test is that it documents the reasoning instead of leaving
    a future reader to wonder whether the green was earned.
    """
    _ops_status(tmp_path, monkeypatch, {})
    r = scan.probe_clock_sanity()
    assert r["status"] == "green"


# ----------------------------------------------------------- disk_headroom

def test_low_disk_is_red(tmp_path, monkeypatch):
    """At 9.1 GB free a merge failed with `No space left on device` and the log
    blamed a0-spike. The probe exists so the next one names the disk."""
    monkeypatch.setattr(scan.os.path, "exists", scan.os.path.exists)

    class Usage:
        total = 474 * 1024 ** 3
        used = total - 5 * 1024 ** 3
        free = 5 * 1024 ** 3

        def __iter__(self):
            return iter((self.total, self.used, self.free))

    import shutil
    monkeypatch.setattr(shutil, "disk_usage", lambda *_a: Usage())
    r = scan.probe_disk_headroom()
    assert r["status"] == "risk", r
    assert "磁盘仅剩" in r["detail"]


def test_ample_disk_is_green(monkeypatch):
    class Usage:
        total = 474 * 1024 ** 3
        used = 100 * 1024 ** 3
        free = 374 * 1024 ** 3

        def __iter__(self):
            return iter((self.total, self.used, self.free))

    import shutil
    monkeypatch.setattr(shutil, "disk_usage", lambda *_a: Usage())
    r = scan.probe_disk_headroom()
    assert r["status"] == "green", r


def test_an_unreadable_disk_is_red_not_assumed_fine(monkeypatch):
    import shutil

    def boom(*_a):
        raise OSError("device not ready")

    monkeypatch.setattr(shutil, "disk_usage", boom)
    r = scan.probe_disk_headroom()
    assert r["status"] == "risk", r
    assert "读不到" in r["detail"]


def test_both_new_probes_are_registered():
    """A probe that exists and is not wired in is the purest form of this bug."""
    assert scan.PROBES["clock_sanity"] is scan.probe_clock_sanity
    assert scan.PROBES["disk_headroom"] is scan.probe_disk_headroom


# ------------------------------- clock_sanity: the scope, widened (S30)

def _repo_with(tmp_path, monkeypatch, heartbeats=(), manifests=(), sync_lines=()):
    root = tmp_path / "repo"
    (root / "monitor" / "ops-status").mkdir(parents=True)
    for name, stamp in heartbeats:
        (root / "monitor" / "ops-status" / ("%s.json" % name)).write_text(
            json.dumps({"id": name, "utc": stamp}), encoding="utf-8")
    for territory, run, stamp in manifests:
        d = root / territory / "runs" / run
        d.mkdir(parents=True)
        (d / "MANIFEST.json").write_text(
            json.dumps({"prompt_id": run, "utc": stamp}), encoding="utf-8")
    if sync_lines:
        (root / "PARTNER_SYNC.md").write_text("\n".join(sync_lines),
                                              encoding="utf-8")
    monkeypatch.setattr(scan, "ROOT", str(root))
    return root


def test_a_manifest_stamped_in_the_future_is_caught(tmp_path, monkeypatch):
    """The instance the first version of this probe could not see.

    I wrote it to read heartbeats -- the one case I had noticed -- and then put
    the same error into a run manifest in the same session. A probe whose scope
    is pinned to its first sample misses the rest of its own class.
    """
    _repo_with(tmp_path, monkeypatch,
               manifests=[("monitor", "20260729T1430Z-x", _stamp(+4 * 3600))])
    r = scan.probe_clock_sanity()
    assert r["status"] == "risk", r
    assert "manifest" in r["detail"]


def test_a_partner_sync_paragraph_stamped_in_the_future_is_caught(tmp_path,
                                                                  monkeypatch):
    _repo_with(tmp_path, monkeypatch,
               sync_lines=["## [engine-rig] %s S99-thing" % _stamp(+6 * 3600),
                           "状态：x"])
    r = scan.probe_clock_sanity()
    assert r["status"] == "risk", r
    assert "PARTNER_SYNC" in r["detail"]


def test_all_three_sources_are_in_scope(tmp_path, monkeypatch):
    """The whole point of S30: one class, three places it is written."""
    _repo_with(tmp_path, monkeypatch,
               heartbeats=[("RES-9", _stamp(-60))],
               manifests=[("monitor", "20260729T1000Z-y", _stamp(-60))],
               sync_lines=["## [engine-rig] %s S98-thing" % _stamp(-60)])
    kinds = {l.split()[0] for l, _p, _s, _e in scan._stamps_to_check()}
    assert kinds == {"heartbeat", "manifest", "PARTNER_SYNC"}


def test_honest_stamps_across_all_three_are_green(tmp_path, monkeypatch):
    """The companion green: a probe hardwired to risk would pass the rest."""
    _repo_with(tmp_path, monkeypatch,
               heartbeats=[("RES-9", _stamp(-60))],
               manifests=[("monitor", "20260729T1000Z-y", _stamp(-60))],
               sync_lines=["## [engine-rig] %s S98-thing" % _stamp(-60)])
    assert scan.probe_clock_sanity()["status"] == "green"


def test_an_old_partner_sync_paragraph_is_not_flagged_as_drift(tmp_path,
                                                               monkeypatch):
    """PARTNER_SYNC is append-only, so old headers are legitimately far older
    than the file. Only the future check applies to them."""
    _repo_with(tmp_path, monkeypatch,
               sync_lines=["## [engine-rig] 2026-07-01T00:00:00Z S1-old",
                           "状态：ancient but honest"])
    assert scan.probe_clock_sanity()["status"] == "green"


def test_a_manifest_without_utc_is_left_to_the_provenance_probe(tmp_path,
                                                               monkeypatch):
    """Two probes shouting about one fact is how both get ignored."""
    root = _repo_with(tmp_path, monkeypatch)
    d = root / "monitor" / "runs" / "20260729T1000Z-z"
    d.mkdir(parents=True)
    (d / "MANIFEST.json").write_text(json.dumps({"prompt_id": "z"}),
                                     encoding="utf-8")
    assert scan.probe_clock_sanity()["status"] == "green"
