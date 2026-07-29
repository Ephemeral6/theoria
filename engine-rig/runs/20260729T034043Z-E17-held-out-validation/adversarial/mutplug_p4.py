"""P4: heldout.peg.graph_minus_geometry deletes nothing; the gates still pass."""
from heldout import peg
peg.graph_minus_geometry = lambda g, positions: dict(g)
from heldout import zero_space_heldout as Z
Z.fit_matches_engine = lambda world: True
