"""The pre-registration and the poverty certificate are themselves testable.

Two things are checked here and they are different in kind:

* the pre-registration is **frozen** — every registered metric has a band, the
  band decides the number, and no metric carries a hand-picked threshold.  This
  is what makes "the threshold was chosen to fit the attack" unavailable as an
  explanation.
* the certificate **rejects work** — a builder that searches, reads a file or
  varies between calls must fail.  A checker nobody tries to fool is a checker
  that passes everything.
"""

from __future__ import annotations

import pytest

from battery.audit.v9 import prereg
from battery.audit.v9.check import certificate
from battery.metrics import REGISTRY
from battery.model import Run, Step


# --- the pre-registration is frozen ---------------------------------------

def test_every_registered_metric_has_a_band():
    assert set(prereg.BAND) == set(REGISTRY)


def test_every_threshold_comes_from_its_band():
    for metric_id, band in prereg.BAND.items():
        assert prereg.TARGETS[metric_id] == prereg.BAND_TARGET[band], metric_id


def test_neutral_metrics_carry_no_threshold():
    for metric_id, card in REGISTRY.items():
        if card.direction == "neutral":
            assert prereg.TARGETS[metric_id] is None, metric_id
        else:
            assert prereg.TARGETS[metric_id] is not None, metric_id


def test_meets_respects_direction():
    assert prereg.meets("X2", "higher", 0.96)
    assert not prereg.meets("X2", "higher", 0.94)
    assert prereg.meets("X1", "lower", 0.04)
    assert not prereg.meets("X1", "lower", 0.06)
    assert not prereg.meets("X1", "lower", None)


def test_controllability_needs_an_order_of_magnitude():
    assert prereg.controllable(1.0, 10.0)
    assert not prereg.controllable(1.0, 9.0)
    assert prereg.controllable(100.0, 111.0)      # absolute limb
    assert not prereg.controllable(None, 10.0)


# --- the certificate rejects work -----------------------------------------

def _trivial() -> Run:
    return Run(run_id="t", arm="a", source="v9",
               steps=[Step(idx=i, action="a", state_key="s%d" % i)
                      for i in range(4)])


def test_a_laid_out_run_certifies():
    cert = certificate(_trivial)
    assert cert["ok"], cert["violations"]


def test_a_searching_builder_is_refused():
    def searching() -> Run:
        i = 0
        while i < 4:
            i += 1
        return Run(run_id="t", arm="a", source="v9")

    cert = certificate(searching)
    assert not cert["ok"]
    assert any(v.startswith("C3") for v in cert["violations"])


def test_a_builder_that_reads_a_file_is_refused():
    def reads() -> Run:
        handle = open(__file__)          # noqa: SIM115
        handle.close()
        return Run(run_id="t", arm="a", source="v9")

    cert = certificate(reads)
    assert not cert["ok"]
    assert any(v.startswith("C2") for v in cert["violations"])


def test_a_nondeterministic_builder_is_refused():
    counter = {"n": 0}

    def drifting() -> Run:
        counter["n"] += 1
        return Run(run_id="t%d" % counter["n"], arm="a", source="v9")

    cert = certificate(drifting)
    assert not cert["ok"]
    assert any(v.startswith("C1") for v in cert["violations"])


def test_a_builder_calling_an_unlisted_helper_is_refused():
    def helper() -> int:
        return 3

    def leaning() -> Run:
        return Run(run_id="t", arm="a", source="v9",
                   steps=[Step(idx=helper(), action="a", state_key="s")])

    cert = certificate(leaning)
    assert not cert["ok"]
    assert any("helper" in v for v in cert["violations"])


def test_smuggled_ground_truth_in_notes_is_refused():
    def smuggler() -> Run:
        return Run(run_id="t", arm="a", source="v9",
                   notes={"optimal_plan": [1, 2, 3]})

    cert = certificate(smuggler)
    assert not cert["ok"]
    assert any(v.startswith("C4") for v in cert["violations"])


def test_no_attack_module_does_work_at_import_time():
    """The one hole C3 cannot see, closed here instead of hoped about.

    `check.py` reads the *builder's* source, so a module that computed a plan
    at import time and had the builder merely lay the answer out would pass C3
    while having done exactly the work the certificate exists to rule out.
    Nothing in the delivered modules does this -- but "I looked and it was
    fine" is the kind of assurance this package was written to replace, so it
    is a check.

    An attack module may contain imports of the two modules it needs, function
    definitions, its docstring, and inert module-level constants — four of the
    six delivered modules end with an `ATTACKS = [...]` list of their own
    functions. Inert means the right-hand side calls nothing and loops nowhere,
    which is the same standard C3 applies inside a builder.
    """
    import ast
    import os

    directory = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "audit", "v9", "attacks")
    allowed_imports = {"battery.model", "battery.audit.v9.attack"}
    offences = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".py") or name == "__init__.py":
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                if node.module not in allowed_imports:
                    offences.append("%s: imports %s" % (name, node.module))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in allowed_imports:
                        offences.append("%s: imports %s" % (name, alias.name))
            elif isinstance(node, ast.FunctionDef):
                continue
            elif (isinstance(node, ast.Expr)
                  and isinstance(node.value, ast.Constant)):
                continue                      # the module docstring
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                working = [n for n in ast.walk(node)
                           if isinstance(n, (ast.Call, ast.While, ast.For))]
                if working:
                    offences.append(
                        "%s: module-level constant at line %d evaluates "
                        "something at import time" % (name, node.lineno))
            else:
                offences.append("%s: top-level %s at line %d -- an attack "
                                "module may not run anything at import time"
                                % (name, type(node).__name__, node.lineno))
    assert not offences, offences


@pytest.mark.parametrize("prediction", prereg.PREDICTIONS)
def test_predictions_are_recorded_with_an_id(prediction):
    identifier, text = prediction
    assert identifier.startswith("V9-P")
    assert len(text) > 30
