# CONFLICT-origin_agent_v13-audit-the-published-surface.md
branch: origin/agent/v13-audit-the-published-surface
reason: verify gate red in monitor (verify.sh)

```
======================================================================
== tests              FAILED(1)
======================================================================
..................F................................xx.                   [100%]
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
>       assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops", "papers",
                                          "release", "fleet-study"}, survey["ungated"]
E       AssertionError: ['CONTRACTS', 'browser-ops', 'fleet-study', 'papers', 'release', 'verify-lab']
E       assert {'CONTRACTS',... 'verify-lab'} <= {'CONTRACTS',...s', 'release'}
E         
E         Extra items in the left set:
E         'verify-lab'

tests\test_gates.py:115: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 8 gated, 9 tests-only, 6 UNGATED
  ungated: CONTRACTS, browser-ops, fleet-study, papers, release, verify-lab
board.py list: 88 line(s)
======================================================================
== artifact fields    ok
======================================================================
state.json carries all 10 required fields; the gate survey is consistent

territories that merge with nothing checking them: CONTRACTS, browser-ops, fleet-study, papers, release, verify-lab
(reported, not a failure -- making it visible is the fix; refusing to merge them would stop the repository dead)

RED: tests

```
