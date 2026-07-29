"""Actually run the page's JavaScript, instead of grepping for its source.

The rest of S30's suite asserts that strings from `FRESH_JS` appear in a page
built by concatenating `FRESH_JS` -- which proves the constant was not deleted
and nothing else. Two real defects lived entirely inside that blind spot:

  * the widget measured the age of the **DOM**, not of the file. `index.html`
    carries no meta-refresh unless `--watch` is passed, so any tab left open
    past the threshold displayed 「扫描可能已经挂了」 about a perfectly healthy
    scan -- a false red, the same disease pointed the other way;
  * the failure page's age span carried no `data-stale`, so `parseInt(null)`
    made the red branch unreachable and a month-old last-success rendered in
    the muted "nothing to see here" grey.

Neither is visible to a substring assertion. Both are visible the moment the
code is executed, so it is executed here, in node, against a DOM stub.

Skipped rather than failed where node is absent: this is a second opinion on
the page, not a reason to hold a merge on a machine without a JS runtime.
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scan                                                     # noqa: E402

NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(NODE is None, reason="node is not installed")

#: The harness stubs exactly what `FRESH_JS` touches: `Date.now`, `setInterval`,
#: `location.reload` and `document.querySelectorAll`. Scenarios are driven from
#: the outside so one node start covers all of them.
HARNESS = r"""
const SCENARIOS = __SCENARIOS__;
const out = [];

for (const sc of SCENARIOS) {
  let NOW = sc.now * 1000;
  let reloads = 0;
  let tick = null;

  const el = {
    _a: sc.attrs, className: "", textContent: "",
    getAttribute(k){ return k in this._a ? String(this._a[k]) : null; },
  };

  globalThis.Date = { now: () => NOW };
  globalThis.setInterval = (fn) => { tick = fn; };
  globalThis.location = { reload: () => { reloads++; } };
  globalThis.document = { querySelectorAll: () => [el] };

  __SCRIPT__

  // Optionally let the tab sit for a while and fire the interval again.
  if (sc.advance) { NOW += sc.advance * 1000; if (tick) tick(); }

  out.push({name: sc.name, cls: el.className, text: el.textContent,
            reloads: reloads});
}
console.log(JSON.stringify(out));
"""


def _script_body():
    """`FRESH_JS` with its <script> wrapper removed."""
    body = scan.FRESH_JS
    body = re.sub(r"^<script>", "", body.strip())
    body = re.sub(r"</script>$", "", body.strip())
    return body


def _run(scenarios, tmp_path):
    src = (HARNESS
           .replace("__SCENARIOS__", json.dumps(scenarios))
           .replace("__SCRIPT__", _script_body()))
    path = tmp_path / "harness.mjs"
    path.write_text(src, encoding="utf-8")
    proc = subprocess.run([NODE, str(path)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)
    assert proc.returncode == 0, proc.stderr
    return {r["name"]: r for r in json.loads(proc.stdout)}


NOW = 1785350000


def test_the_widget_reads_fresh_stale_and_unknown_correctly(tmp_path):
    res = _run([
        {"name": "fresh", "now": NOW,
         "attrs": {"data-since": NOW - 120, "data-stale": 1200}},
        {"name": "stale", "now": NOW,
         "attrs": {"data-since": NOW - 3000, "data-stale": 1200}},
        {"name": "no-stamp", "now": NOW, "attrs": {}},
        {"name": "zero-stamp", "now": NOW, "attrs": {"data-since": 0}},
        {"name": "future", "now": NOW,
         "attrs": {"data-since": NOW + 600, "data-stale": 1200}},
    ], tmp_path)

    assert res["fresh"]["cls"] == "ago fresh"
    assert "2 分钟前" in res["fresh"]["text"]

    assert res["stale"]["cls"] == "ago stale"
    assert "扫描可能已经挂了" in res["stale"]["text"]

    # Unknown is grey and says so -- not red, not "just now".
    for name in ("no-stamp", "zero-stamp"):
        assert res[name]["cls"] == "ago unknown", name
        assert "未知不写成 0" in res[name]["text"], name

    assert res["future"]["cls"] == "ago unknown"
    assert "年龄不可信" in res["future"]["text"]


def test_a_tab_left_open_rereads_the_file_before_crying_stale(tmp_path):
    """The false red. A healthy scan must not be accused by an old tab.

    On first paint the tab is young, so an old file is honestly reported as
    stale. But once the tab itself has been open longer than the window, the
    age it measures may be its own -- so it reloads to find out, exactly once
    per window rather than every 15 s.
    """
    res = _run([
        # Freshly opened onto a genuinely old file: report red, do not reload.
        {"name": "old-file-new-tab", "now": NOW,
         "attrs": {"data-since": NOW - 3000, "data-stale": 1200}},
        # Same page, but the tab has now been sitting for 21 minutes.
        {"name": "old-tab", "now": NOW,
         "attrs": {"data-since": NOW - 100, "data-stale": 1200},
         "advance": 1300},
    ], tmp_path)

    assert res["old-file-new-tab"]["reloads"] == 0, \
        "a page opened onto stale data must accuse the backend, not reload"
    assert res["old-file-new-tab"]["cls"] == "ago stale"

    assert res["old-tab"]["reloads"] == 1, \
        "an old tab must re-read the file before reporting the scan dead"


def test_the_failure_pages_age_span_can_reach_the_red_branch(tmp_path):
    """Defect: without `data-stale` the span was permanently `fresh` grey.

    Driven from the real page rather than from a hand-written attribute dict,
    so it fails if `render_failure` stops emitting the attribute.
    """
    state = scan.failure_state(RuntimeError("x"), "Traceback\n  boom\n")
    state["last_success_at"] = "2026-06-01 00:00:00"
    state["last_success_epoch"] = NOW - 30 * 86400
    page = scan.render_failure(state)

    span = re.search(r'<span class="ago"([^>]*)>', page)
    assert span, "the failure page must carry an age span"
    attrs = dict(re.findall(r'(data-[\w-]+)="([^"]*)"', span.group(1)))
    assert "data-since" in attrs and "data-stale" in attrs

    res = _run([{"name": "month-old", "now": NOW,
                 "attrs": {k: int(v) for k, v in attrs.items()}}], tmp_path)
    assert res["month-old"]["cls"] == "ago stale", \
        "a last success 30 days ago rendered in the muted 'all fine' grey"
