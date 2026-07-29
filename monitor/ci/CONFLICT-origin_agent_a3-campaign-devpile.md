# CONFLICT-origin_agent_a3-campaign-devpile.md
branch: origin/agent/a3-campaign-devpile
reason: verify gate red in monitor (verify.sh)
tip: cde83c28714933bdf0a6e4d335cf09061451b09e
first_seen: 2026-07-29T04:14:01Z
last_seen: 2026-07-29T04:14:01Z
attempts: 1

```
======================================================================
== tests              FAILED(1)
======================================================================
...............xx.                                            [100%]
================================== FAILURES ===================================
_____________ test_this_repository_is_where_the_survey_says_it_is _____________

    def test_this_repository_is_where_the_survey_says_it_is():
        """Pinned deliberately. When a territory gains or loses a gate this test
        fails, and the correct response is to update it *and* say so in the item
        that changed it -- which is the visibility S13 exists to create."""
        survey = gates.survey(ROOT)
        assert "monitor" in survey["gated"], (
            "the rig that enforces gates must have one; it did not until S13")
        # fleet-study 是 2026-07-29 新落地的领地，尚无闸门——按上面那条规矩，
        # 更新这个集合的同时要说明：它的闸门由 S17-fleet-evidence-capture 负责补，
        # 补上之后这条测试会再红一次，那是对的。
        #
        # S14 在此同样自报：十一个领地各得了一个三段式 verify.py，盘面从 6 个有闸门
        # 变成 17 个，`tests_only` 因此清零。
        assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops", "papers",
                                          "release", "fleet-study",
                                          "verify-lab"}, survey["ungated"]
        # S14 cleared `tests_only` completely; anything in it now is a territory
        # that arrived afterwards and still owes a gate.  Naming them one by one is
        # the point -- an unexpected name here means a gate was deleted, which the
        # blanket `not survey["tests_only"]` I first wrote could not distinguish
        # from an ordinary new arrival.
>       assert set(survey["tests_only"]) <= {"verify-lab"}, survey["tests_only"]
E       AssertionError: ['fleetkit', 'verify-lab']
E       assert {'fleetkit', 'verify-lab'} <= {'verify-lab'}
E         
E         Extra items in the left set:
E         'fleetkit'

tests\test_gates.py:126: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 19 gated, 2 tests-only, 3 UNGATED
  ungated: CONTRACTS, browser-ops, papers
board.py list: 91 line(s)
======================================================================
== artifact fields    ok
======================================================================
state.json carries all 10 required fields; the gate survey is consistent

territories that merge with nothing checking them: CONTRACTS, browser-ops, papers
(reported, not a failure -- making it visible is the fix; refusing to merge them would stop the repository dead)

RED: tests

```
