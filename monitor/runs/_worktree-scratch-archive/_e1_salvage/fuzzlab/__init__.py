"""fuzzlab -- property-testing battery for the engine-rig engines.

engine-rig is imported read-only.  Nothing in this package edits, monkey-patches
or re-exports engine-rig code; when a property fails the finding is written to
`BUGS.md`, never fixed in place.  See `README.md` for the contract.
"""

__all__ = ["rig", "prng", "worlds", "oracles"]
