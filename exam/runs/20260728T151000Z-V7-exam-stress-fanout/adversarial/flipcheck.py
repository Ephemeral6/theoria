"""Prove both strict xfails are genuinely flippable: patch the defect, expect XPASS."""
import exam.grading.rubrics_adaptation as ra
_orig = ra._read_set
def fixed(answer, key):
    if not isinstance(answer, dict):
        return None                     # the fix: no key, no claim
    return _orig(answer, key)
ra._read_set = fixed
