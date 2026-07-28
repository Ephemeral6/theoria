"""判卷机 -- the marking side.

`registry` holds the rubrics and the digest that freezes them; `mark` applies
them to a submission; `calibration` proves the marker works by running it
against examinees whose scores are known before the run.
"""

from .registry import all_rubrics, digest, manifest, module_digests, rubric  # noqa: F401

__all__ = ["all_rubrics", "digest", "manifest", "module_digests", "rubric",
           "mark", "calibration"]
