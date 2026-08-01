"""`--anchor observed`: the frontier is seated on the world, certify is not.

What is under test is the *duality*, not one anchor. `inner/loop._roll_forward`
answers "where would the manual be if it were right?", and the arm uses that
answer both to audit the manual (certify's open-loop replay, which is only a
test because it is allowed to drift) and to design experiments (the probe
frontier, which is only an experiment if it is anchored on the frame the world
is showing). One state cannot do both jobs, and today the audit job wins
silently.

The acceptance that matters most here is the **negative control**. A manual
that has not drifted renders exactly the world's frame, so the transplant is
the identity and every anchored prediction is byte-identical to the rolled one.
A switch that changed the answer even then would not be re-anchoring, it would
be perturbing, and no measurement taken through it would mean anything. That is
`test_no_drift_means_no_change`, and it is the reason to trust the other
numbers in this file.

Offline: no key, no network, no model call, no ARC action.
"""

import os
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import anchor as anchor_mod                # noqa: E402
from inner import probe as probe_beat                 # noqa: E402
from world.frames import FrameStore, Step, grid_hash  # noqa: E402

BACKGROUND = 0


def _grid(marks):
    """A 4x4 frame with `{(r, c): colour}` painted onto a background of 0."""
    out = [[BACKGROUND] * 4 for _ in range(4)]
    for (r, c), value in marks.items():
        out[r][c] = value
    return out


def _namespace(*, at=(0, 0), fires=True, render_raises=False):
    """A one-object manual: `step` moves the object right by one, `render` paints it.

    `fires` controls whether the single rule `slide` reports itself as having
    fired, which is what the `without_slide` ablation keys off.
    """
    def initial_state():
        return {"pos": at}

    def step(state, _action):
        r, c = state["pos"]
        return {"pos": (r, min(c + 1, 3))}

    def render(state):
        if render_raises:
            raise RuntimeError("the manual cannot draw its own level")
        return _grid({state["pos"]: 7})

    return {
        "initial_state": initial_state,
        "step": step,
        "render": render,
        "fired": lambda _s, _a: (["slide__obj"] if fires else []),
        "RULES": [("slide__obj", None, None, None)],
    }


def _store(grids):
    """A `FrameStore` whose observed frames are exactly `grids`."""
    store = FrameStore()
    for idx, grid in enumerate(grids):
        store.add(Step(idx, "ACTION5", [grid]))
    return store


def _predict_all(hypotheses, state, action=("key", 5)):
    out = {}
    for hypothesis in hypotheses:
        try:
            out[hypothesis.id] = hypothesis.predict(state, action)
        except Exception as exc:                       # noqa: BLE001
            out[hypothesis.id] = "raised:%s" % type(exc).__name__
    return out


# -- the switch itself ----------------------------------------------------

def test_the_default_is_rolled_and_the_env_switch_is_a_whitelist():
    assert anchor_mod.AnchorConfig().mode == "rolled"
    assert anchor_mod.AnchorConfig().observed is False
    assert anchor_mod.AnchorConfig.from_env({}).mode == "rolled"
    assert anchor_mod.AnchorConfig.from_env(
        {"THEORIA_ANCHOR": "observed"}).observed is True
    # A misspelt switch must leave the arm on the historic anchor rather than
    # quietly changing the thing a round is trying to measure.
    for raw in ("1", "true", "OBSERVED", "observed!", "", " ", "banana",
                "rolled", "Observed"):
        cfg = anchor_mod.AnchorConfig.from_env({"THEORIA_ANCHOR": raw})
        assert cfg.mode == "rolled", raw
        assert cfg.observed is False, raw


def test_measure_is_independent_of_mode():
    """A leg can measure its drift while still designing from the old anchor.

    That separation is what makes the A/B honest: the leg that argues for the
    change must not be the only leg that can see the quantity it argues from.
    """
    cfg = anchor_mod.AnchorConfig.from_env({"THEORIA_ANCHOR_MEASURE": "1"})
    assert cfg.mode == "rolled" and cfg.measure is True
    # …and turning the anchor on implies the measurement, because a leg that
    # moved its anchor and cannot say how far it moved has reported nothing.
    assert anchor_mod.AnchorConfig.from_env(
        {"THEORIA_ANCHOR": "observed"}).measure is True


# -- the negative control -------------------------------------------------

def test_no_drift_means_no_change():
    """The acceptance. On an undrifted manual the switch is provably a no-op.

    `render(state)` is the world's frame, so every hypothesis's delta is
    applied to the frame it was computed against and the transplant is the
    identity. Every prediction must come back byte-identical, hypothesis for
    hypothesis. A check that has never been seen to say "nothing changed" has
    not been shown to be measuring drift.
    """
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    # The world is showing exactly what the manual draws: no drift.
    store = _store([namespace["render"](state)])
    assert anchor_mod.divergence(namespace, state, store)["cells_wrong"] == 0

    rolled = probe_beat.build_hypotheses(namespace)
    observed = probe_beat.build_hypotheses(
        namespace, anchor=anchor_mod.AnchorConfig(mode="observed"),
        store=store)

    assert [h.id for h in rolled] == [h.id for h in observed]
    assert _predict_all(rolled, state) == _predict_all(observed, state)


def test_drift_means_the_predictions_move_and_the_anchor_is_the_world():
    """The positive control, so the negative one is not vacuous."""
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    # The world has moved on: the object is at (1, 3), the manual thinks (1, 1).
    world = _grid({(1, 3): 7})
    store = _store([world])
    reading = anchor_mod.divergence(namespace, state, store)
    assert reading["drifted"] is True
    assert reading["cells_wrong"] == 2          # (1,1) vacated, (1,3) painted

    rolled = _predict_all(probe_beat.build_hypotheses(namespace), state)
    observed = _predict_all(probe_beat.build_hypotheses(
        namespace, anchor=anchor_mod.AnchorConfig(mode="observed"),
        store=store), state)
    assert rolled != observed

    # `inert` anchored on the world is "the world's frame, unchanged".
    assert observed["inert"] == grid_hash(world)
    # `manual` anchored on the world is the manual's own delta -- vacate
    # (1, 1), paint (1, 2) -- transplanted onto the world's frame.
    assert observed["manual"] == grid_hash(_grid({(1, 2): 7, (1, 3): 7}))


def test_the_anchor_switch_subsumes_two_of_the_generated_generators():
    """Provable, so pinned rather than measured.

    R2 shipped `world_inert` and `world_anchored_manual` as two *extra*
    hypotheses, which widens the frontier and lowers every action's split
    entropy. Re-anchoring gets the same two predictions out of `inert` and
    `manual` at the width the ablation frontier already had. Only the `*_edge`
    pair is not subsumed, and that pair is about expressivity -- a board cell
    no rule can name -- not about anchoring.
    """
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    store = _store([_grid({(1, 1): 7}), _grid({(1, 3): 7})])

    generated = _predict_all(probe_beat.build_hypotheses(
        namespace, frontier=probe_beat.FrontierConfig(mode="generated"),
        store=store), state)
    observed = _predict_all(probe_beat.build_hypotheses(
        namespace, anchor=anchor_mod.AnchorConfig(mode="observed"),
        store=store), state)

    assert observed["inert"] == generated["world_inert"]
    assert observed["manual"] == generated["world_anchored_manual"]


def test_reanchoring_leaves_the_generated_hypotheses_alone():
    """They are already world-anchored; transplanting twice would be wrong."""
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    store = _store([_grid({(1, 1): 7}), _grid({(1, 3): 7})])
    cfg = probe_beat.FrontierConfig(mode="generated")

    without = _predict_all(probe_beat.build_hypotheses(
        namespace, frontier=cfg, store=store), state)
    with_anchor = _predict_all(probe_beat.build_hypotheses(
        namespace, frontier=cfg, store=store,
        anchor=anchor_mod.AnchorConfig(mode="observed")), state)

    for hid in without:
        if hid in ("manual", "inert") or hid.startswith("without_"):
            continue
        assert with_anchor[hid] == without[hid], hid


# -- what it must not do --------------------------------------------------

def test_the_default_report_grows_no_anchor_key():
    """`--anchor rolled` must leave `design`'s report byte-identical."""
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    store = _store([_grid({(1, 3): 7})])

    plain = probe_beat.design(namespace, state, [("key", 5)], store=store)
    defaulted = probe_beat.design(namespace, state, [("key", 5)], store=store,
                                  anchor=anchor_mod.AnchorConfig())
    assert "anchor" not in plain
    assert "anchor" not in defaulted
    assert plain == defaulted

    on = probe_beat.design(namespace, state, [("key", 5)], store=store,
                           anchor=anchor_mod.AnchorConfig(mode="observed"))
    assert on["anchor"]["mode"] == "observed"
    assert on["anchor"]["frontier_is_seated_on_the_world"] is True
    assert on["anchor"]["divergence"]["drifted"] is True


def test_measure_reports_the_drift_without_moving_the_frontier():
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    store = _store([_grid({(1, 3): 7})])

    plain = probe_beat.design(namespace, state, [("key", 5)], store=store)
    measured = probe_beat.design(
        namespace, state, [("key", 5)], store=store,
        anchor=anchor_mod.AnchorConfig(mode="rolled", measure=True))

    assert measured["anchor"]["mode"] == "rolled"
    assert measured["anchor"]["frontier_is_seated_on_the_world"] is False
    assert measured["anchor"]["divergence"]["cells_wrong"] == 2
    # Everything except the new block is the old report, hypothesis for
    # hypothesis and ranking for ranking.
    assert {k: v for k, v in measured.items() if k != "anchor"} == plain


def test_certify_never_reads_the_anchor():
    """The instrument this change exists to protect.

    `certify.cheap` keeps its own `state = initial_state()` and its own replay
    loop. It does not call `_roll_forward`, it takes no anchor argument, and it
    must not acquire one: an open-loop replay is the arm's only detector of a
    wrong rule, and a re-seated replay cannot diverge by more than one step, so
    it would go green on a manual that is wrong everywhere.
    """
    import inspect                                     # noqa: PLC0415

    from inner import certify                          # noqa: PLC0415

    for name in ("cheap", "run", "expensive"):
        params = inspect.signature(getattr(certify, name)).parameters
        assert "anchor" not in params, name
    source = inspect.getsource(certify)
    assert "anchor" not in source
    assert "_roll_forward" not in source


# -- the divergence measurement -------------------------------------------

def test_divergence_records_absence_as_absence():
    namespace = _namespace()
    state = namespace["initial_state"]()

    empty = anchor_mod.divergence(namespace, state, FrameStore())
    assert empty["cells_wrong"] is None
    assert empty["drifted"] is None
    assert empty["unmeasurable"] == "no frame observed yet"

    store = _store([_grid({(0, 0): 7})])
    blind = anchor_mod.divergence({"step": lambda s, a: s}, state, store)
    assert blind["cells_wrong"] is None
    assert blind["unmeasurable"] == "the namespace exposes no render"

    raising = anchor_mod.divergence(_namespace(render_raises=True), state,
                                    store)
    assert raising["cells_wrong"] is None
    assert raising["anchor_hash"] == "error"
    assert "raised" in raising["unmeasurable"]


def test_an_unanchorable_turn_says_so_rather_than_anchoring_on_nothing():
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    report = probe_beat.design(namespace, state, [("key", 5)],
                               store=FrameStore(),
                               anchor=anchor_mod.AnchorConfig(mode="observed"))
    assert report["anchor"]["frontier_is_seated_on_the_world"] is False
    assert report["anchor"]["why_not"] == "no frame observed yet"
    # …and it falls back to the rolled frontier rather than to nothing.
    plain = probe_beat.design(namespace, state, [("key", 5)],
                              store=FrameStore())
    assert {k: v for k, v in report.items() if k != "anchor"} == plain


# -- the refactor this rests on -------------------------------------------

def test_the_grid_specs_and_the_hypotheses_are_one_definition():
    """`ablation_grid_specs` is the single source `build_hypotheses` wraps.

    Two builders that must be kept in step by hand drift apart, and the way
    this one would break is silent: the anchored frontier would answer a
    question the rolled one never asked, and the A/B would compare two
    different arms.
    """
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    specs = probe_beat.ablation_grid_specs(namespace)
    hypotheses = probe_beat.build_hypotheses(namespace)

    assert [s[0] for s in specs] == [h.id for h in hypotheses]
    assert [s[1] for s in specs] == [h.description for h in hypotheses]
    for (hid, _desc, grid_of, _swallow), hypothesis in zip(specs, hypotheses):
        assert (probe_beat._observation(grid_of(state, ("key", 5)))    # noqa: SLF001
                == hypothesis.predict(state, ("key", 5))), hid


@pytest.mark.parametrize("mode", ["rolled", "observed"])
def test_the_error_behaviour_is_not_made_uniform(mode):
    """`manual` swallows, `inert` propagates -- on both anchors.

    That asymmetry is 2026-07-31's and is load-bearing: `inert`'s raise is
    caught by the caller and turns the whole design into an error, which is
    what a leg whose `render` cannot draw its own level recorded. Making the
    two uniform would silently change what such a leg reports.
    """
    namespace = _namespace(render_raises=True)
    state = {"pos": (0, 0)}
    store = _store([_grid({(0, 0): 7})])
    by_id = {h.id: h for h in probe_beat.build_hypotheses(
        namespace, store=store, anchor=anchor_mod.AnchorConfig(mode=mode))}

    assert by_id["manual"].predict(state, ("key", 5)) == "error"
    with pytest.raises(RuntimeError):
        by_id["inert"].predict(state, ("key", 5))


# -- the leg-level record -------------------------------------------------

def _arm(tmp_path, **kwargs):
    from inner.loop import TheoriaArm                  # noqa: PLC0415

    run = types.SimpleNamespace(dir=str(tmp_path), run=None, run_id="r-pytest")
    return TheoriaArm(env_base="http://127.0.0.1:1", run=run,
                      game_id="g50t-5849a774", offline=True, **kwargs)


def test_the_arm_defaults_to_the_rolled_anchor(tmp_path):
    assert _arm(tmp_path).anchor.mode == "rolled"
    assert _arm(tmp_path,
                anchor=anchor_mod.AnchorConfig(mode="observed")).anchor.observed


def test_the_drift_summary_never_reads_an_unmeasured_turn_as_zero(tmp_path):
    arm = _arm(tmp_path)
    namespace = _namespace(at=(1, 1))
    state = namespace["initial_state"]()
    arm.store.add(Step(0, "ACTION5", [_grid({(1, 3): 7})]))

    arm._record_drift(namespace, state)                # noqa: SLF001
    arm._record_drift(None, None)                      # noqa: SLF001

    summary = arm.drift_summary()
    assert summary["turns_recorded"] == 2
    assert summary["turns_measured"] == 1
    assert summary["turns_unmeasurable"] == 1
    assert summary["why_unmeasurable"] == ["no compiled manual on this turn"]
    assert summary["turns_drifted"] == 1
    assert summary["cells_wrong_max"] == 2
    assert summary["series"] == [2]
    # The denominator is the measured turns, not the recorded ones: a mean of
    # 1.0 here would be an unmeasured turn folded in as a clean one.
    assert summary["cells_wrong_mean"] == 2.0
