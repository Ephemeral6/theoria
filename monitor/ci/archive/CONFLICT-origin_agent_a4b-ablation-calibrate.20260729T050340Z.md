# CONFLICT-origin_agent_a4b-ablation-calibrate.md
branch: origin/agent/a4b-ablation-calibrate
reason: verify gate red in ablation-arm (verify.sh)
tip: 37ab4d003f4818fd5f28799dd9705e7d67e81b55
first_seen: 2026-07-29T04:53:34Z
last_seen: 2026-07-29T04:53:34Z
attempts: 1

```
y.py:97: AttributeError
_______ test_the_recorded_half_names_the_instruments_that_do_not_exist ________

artefacts = ({'exhibits': {'available': True, 'fields': {'certificate_owed': {'E1_a0_no_button': False, 'E2_a2_holed': False, 'sam...s theorem tier is gone (C-5)", '[status: proven]': 'an invariant may still be observed, never guaranteed (C-5)'}, ...})

    def test_the_recorded_half_names_the_instruments_that_do_not_exist(artefacts):
        """P-2 and P-4 are not merely uncompared -- nothing in this arm measures
        them at all. A4b reading `RECORDED` and expecting numbers would lose a day
        finding that out."""
>       recorded = verify._recorded(*artefacts[:2])
                   ^^^^^^^^^^^^^^^^
E       AttributeError: module 'verify' has no attribute '_recorded'

ablation-arm\tests\test_verify.py:112: AttributeError
_______________ test_the_gate_reports_e3_without_failing_on_it ________________

artefacts = ({'exhibits': {'available': True, 'fields': {'certificate_owed': {'E1_a0_no_button': False, 'E2_a2_holed': False, 'sam...s theorem tier is gone (C-5)", '[status: proven]': 'an invariant may still be observed, never guaranteed (C-5)'}, ...})

    def test_the_gate_reports_e3_without_failing_on_it(artefacts):
        run_all, exhibits, cut = artefacts
>       recorded = verify._recorded(run_all, exhibits)
                   ^^^^^^^^^^^^^^^^
E       AttributeError: module 'verify' has no attribute '_recorded'

ablation-arm\tests\test_verify.py:120: AttributeError
=========================== short test summary info ===========================
FAILED ablation-arm\tests\test_verify.py::test_the_gate_is_green_on_what_the_arm_actually_produced
FAILED ablation-arm\tests\test_verify.py::test_every_claim_states_itself_and_shows_its_evidence
FAILED ablation-arm\tests\test_verify.py::test_the_gate_refuses_when_the_run_says_otherwise[path0-7-expected_red0]
FAILED ablation-arm\tests\test_verify.py::test_the_gate_refuses_when_the_run_says_otherwise[path1-value1-expected_red1]
FAILED ablation-arm\tests\test_verify.py::test_the_gate_refuses_when_the_run_says_otherwise[path2-False-expected_red2]
FAILED ablation-arm\tests\test_verify.py::test_the_gate_refuses_when_the_run_says_otherwise[path3-False-expected_red3]
FAILED ablation-arm\tests\test_verify.py::test_a_missing_field_is_not_read_as_the_value_the_gate_wants
FAILED ablation-arm\tests\test_verify.py::test_a_recorded_number_can_never_turn_the_gate_red
FAILED ablation-arm\tests\test_verify.py::test_the_recorded_half_names_the_instruments_that_do_not_exist
FAILED ablation-arm\tests\test_verify.py::test_the_gate_reports_e3_without_failing_on_it

==============================================================================
== the gate: what A4a asserts
==============================================================================
  P-3            ok
  P-5(correct)   ok
  P-6            ok
  P-7            ok
  shadow-1       ok
  shadow-2       ok
  shadow-3       ok
  shadow-4       ok
  read-only      ok
  P-1(counts)    ok

==============================================================================
== recorded for A4b -- NOT asserted, and cannot turn this red
==============================================================================
  P-1             RECORDED
      replay accuracy, byte-equal to the full arm
  P-2             RECORDED
      behavioural / held-out accuracy, equal to the full arm
  P-4             RECORDED
      this arm is cheaper, not dearer
  P-5(identical)  RECORDED
      the A0 verdict is *identical* to the full arm's
  E3              NOT CONSTRUCTIBLE
      the charitable exhibit

==============================================================================
== stages
  build_theory --check   ok
  run_arm                ok
  run_arm --twice        ok
  run_exhibits           ok
  pytest                 FAILED(1)

wrote C:\Users\user\AppData\Local\Temp\ci-merge-hulfrab7\ablation-arm\artifacts\verify.json

RED: stages ['pytest'], assertions ok

```
