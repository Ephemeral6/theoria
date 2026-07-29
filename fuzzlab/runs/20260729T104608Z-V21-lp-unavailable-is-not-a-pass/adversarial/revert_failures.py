"""pytest plugin: revert ONLY the failures() widening (VIOLATED-only)."""
def pytest_configure(config):
    from fuzzlab.props import finding
    finding.failures = lambda fs: [f for f in fs if f.kind == finding.VIOLATED]
    print("\n[revert_failures] failures() narrowed back to VIOLATED only")
