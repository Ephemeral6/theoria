"""pytest plugin: revert ONLY the V-21 catch in props/lp_potential."""
def pytest_configure(config):
    import fuzzlab.props.lp_potential as props
    def _rethrow(world, invariant, exc):
        raise exc
    props._skip_solver_unavailable = _rethrow
    print("\n[revert_catch] _skip_solver_unavailable rebound to re-raise")
