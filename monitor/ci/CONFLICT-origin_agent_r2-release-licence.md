# CONFLICT-origin_agent_r2-release-licence.md
branch: origin/agent/r2-release-licence
reason: tests red in release

```
.F
================================== FAILURES ===================================
______________________ test_the_partition_loses_nothing _______________________

    def test_the_partition_loses_nothing():
        """Every tracked file is either shipped or named as withheld. A file in
        neither list is the one omission no reader can detect."""
        manifest = {r["path"] for r in bundle.read_manifest()}
        shipped = {r["path"] for r in rows("BUNDLE.jsonl")}
        withheld = {r["path"] for r in rows("FRAME_HASHES.jsonl")}
>       assert shipped | withheld == manifest
E       AssertionError: assert {'.env.exampl...v0.2.md', ...} == {'.env.exampl...v0.2.md', ...}
E         
E         Extra items in the right set:
E         'release/.gitattributes'
E         Use -v to get more diff

tests\test_bundle.py:44: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_bundle.py::test_the_partition_loses_nothing - AssertionErro...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 1 passed in 0.19s

```
