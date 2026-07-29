"""pytest plugin: revert BOTH (the pre-fix state, as far as monkeypatching reaches)."""
def pytest_configure(config):
    import fuzzlab.props.lp_potential as props
    from fuzzlab.props import finding
    def _rethrow(world, invariant, exc):
        raise exc
    props._skip_solver_unavailable = _rethrow
    finding.failures = lambda fs: [f for f in fs if f.kind == finding.VIOLATED]
    print("\n[revert_both] catch removed AND failures() narrowed")
