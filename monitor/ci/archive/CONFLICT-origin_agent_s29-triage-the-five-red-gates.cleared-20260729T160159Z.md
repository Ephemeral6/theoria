# CONFLICT-origin_agent_s29-triage-the-five-red-gates.md
branch: origin/agent/s29-triage-the-five-red-gates
reason: verify gate red in monitor (verify.sh)
tip: 5d35ee56cb98afd12a2491616b4d5a3a2ff4aeae
first_seen: 2026-07-29T14:46:02Z
last_seen: 2026-07-29T15:53:31Z
attempts: 2

```
--- cause lines (lifted out of the transcript) ---
== tests              FAILED(1)
        assert "monitor" in survey["gated"], (
        assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops",
>       assert set(survey["tests_only"]) <= {"verify-lab",
E       AssertionError: ['papers', 'verify-lab']
E       assert {'papers', 'verify-lab'} <= {'fleetkit', 'verify-lab'}
E         
E         Extra items in the left set:
E         'papers'
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
--- tail of the transcript ---
 gains or loses a gate this test
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
        # 2026-07-29 收紧：`fleet-study`（S17 补上）与 `release` 都已自带闸门，
        # 所以它们从这个集合里**移除**——按上面那条规矩，收紧同样要说出来，
        # 否则下一个人会以为这两块地还敞着。
        assert set(survey["ungated"]) <= {"CONTRACTS", "browser-ops",
                                          "papers"}, survey["ungated"]
        # S14 cleared `tests_only` completely; anything in it now is a territory
        # that arrived afterwards and still owes a gate.  Naming them one by one is
        # the point -- an unexpected name here means a gate was deleted, which the
        # blanket `not survey["tests_only"]` I first wrote could not distinguish
        # from an ordinary new arrival.
        # `fleetkit` 是 S18 抽出来的新领地，有测试、还没有闸门——按 S13 它欠一个。
>       assert set(survey["tests_only"]) <= {"verify-lab",
                                             "fleetkit"}, survey["tests_only"]
E       AssertionError: ['papers', 'verify-lab']
E       assert {'papers', 'verify-lab'} <= {'fleetkit', 'verify-lab'}
E         
E         Extra items in the left set:
E         'papers'

tests\test_gates.py:129: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_gates.py::test_this_repository_is_where_the_survey_says_it_is
======================================================================
== real run           ok
======================================================================
scan.build wrote history.jsonl, index.html, state.json
gates: 21 gated, 2 tests-only, 2 UNGATED
  ungated: CONTRACTS, browser-ops
board.py list: 84 line(s)
======================================================================
== artifact fields    ok
======================================================================
state.json carries all 10 required fields; the gate survey is consistent

territories that merge with nothing checking them: CONTRACTS, browser-ops
(reported, not a failure -- making it visible is the fix; refusing to merge them would stop the repository dead)

RED: tests

```
