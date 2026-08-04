# CONFLICT-origin_agent_v28-exam-four-tests-must-flip.md
branch: origin/agent/v28-exam-four-tests-must-flip
reason: verify gate red in exam (verify.py)
tip: 7fa4eea1b1c9df05668aaaff9a1517c905e7c6b0
base: 9e478dd81b880a8b9053d65185e80e3e590f0077
first_seen: 2026-08-02T11:40:29Z
last_seen: 2026-08-02T11:40:29Z
attempts: 1

```
--- cause lines (lifted out of the transcript) ---
>       assert proc.returncode == 0, proc.stdout + proc.stderr
E       AssertionError: Traceback (most recent call last):
E           File "D:\Miniforge3\Lib\site-packages\scipy\__init__.py", line 95, in <module>
E             from scipy._lib._ccallback import LowLevelCallable
E           File "D:\Miniforge3\Lib\site-packages\scipy\_lib\_ccallback.py", line 1, in <module>
E             from . import _ccallback_c
E         ImportError: DLL load failed while importing _ccallback_c: 页面文件太小，无法完成操作。
E         
E         The above exception was the direct cause of the following exception:
E         
E         Traceback (most recent call last):
E           File "<frozen runpy>", line 198, in _run_module_as_main
E           File "<frozen runpy>", line 88, in _run_code
E           File "C:\Users\user\AppData\Local\Temp\ci-merge-xn1fs99s\exam\tools\build_papers.py", line 157, in <module>
E             raise SystemExit(main())
E                              ~~~~^^
E           File "C:\Users\user\AppData\Local\Temp\ci-merge-xn1fs99s\exam\tools\build_papers.py", line 137, in main
E             payload = build_all(argv or None)
E           File "C:\Users\user\AppData\Local\Temp\ci-merge-xn1fs99s\exam\tools\build_papers.py", line 115, in build_all
E             results = [build_one(qt, write=write) for qt in types]
E                        ~~~~~~~~~^^^^^^^^^^^^^^^^^
E           File "C:\Users\user\AppData\Local\Temp\ci-merge-xn1fs99s\exam\tools\build_papers.py", line 66, in build_one
E             module = module_for(question_type)
E           File "C:\Users\user\AppData\Local\Temp\ci-merge-xn1fs99s\exam\papers\__init__.py", line 60, in module_for
... and 36 more cause line(s)
--- tail of the transcript ---
answers.json
wrote exam/artifacts/endpoint_controls/null.answers.json
wrote exam/artifacts/prereg/verdict_prereg.json
wrote exam/artifacts/prereg/verdict_class_inventory.md
wrote exam/artifacts/prereg/verdict_negative_controls.md
pre-registration matches the built paper and every control was judged as pre-registered

==============================================================================
== withdrawn_claims
==============================================================================
withdrawn-claim scan: 125 tracked exam files, 4 pattern(s), 0 hit(s)
clean

==============================================================================
== artefact_locations
==============================================================================
artefact locations: 51 tracked files under exam/artifacts, none records where it was built

==============================================================================
== artifacts_match_committed
==============================================================================
working tree vs HEAD under exam/artifacts: clean
comparing an existing build: C:\Users\user\AppData\Local\Temp\exam-verify-_o93iqps\artifacts
producers rewrote 42 of 51 tracked artefacts; 0 of those differ from the seed
artifacts match committed: 51 tracked files, all reproduced

==============================================================================
== determinism: two builds, fresh interpreters, PYTHONHASHSEED 7 vs 99
==============================================================================
  PYTHONHASHSEED=7   bb2c3ceea6522ada797c30d3178fc04368e9862b5cd33384fb46f1f9cf87e276 0018be29076302d38b180f982aaa57375679d38c1df6bdb7ae75c19118b7eb65 ede01081503181482fa0ccad590fb8d9ffa4e1068806338e3b57c0f7c6914d85 b5223c789c79b7a91e59d602d46f755e2e0c702b290e3bca179949cc3a5365b5
  PYTHONHASHSEED=99  bb2c3ceea6522ada797c30d3178fc04368e9862b5cd33384fb46f1f9cf87e276 0018be29076302d38b180f982aaa57375679d38c1df6bdb7ae75c19118b7eb65 ede01081503181482fa0ccad590fb8d9ffa4e1068806338e3b57c0f7c6914d85 b5223c789c79b7a91e59d602d46f755e2e0c702b290e3bca179949cc3a5365b5
  identical: True

==============================================================================
== summary
==============================================================================
  build_papers               ok
  pytest                     FAILED(1)
  run_exam --calibrate       ok
  run_selftest               ok
  build_prereg               ok
  withdrawn_claims           ok
  artefact_locations         ok
  artifacts_match_committed  ok
  determinism                ok

RED: pytest

```
