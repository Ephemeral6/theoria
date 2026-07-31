"""Auto-generated from theory.dsl — DO NOT EDIT.

Change the manual and recompile. This module is the only predictor
in the system: certify's replay, the Lean generator's transition
table and the plan validator all read the world through `step`.

`step` implements the semantics the manual *declares*; nothing
about the frame axiom, the conflict policy or the cascade shape is
assumed here, and a manual that does not say is refused.
"""

from dataclasses import dataclass, replace

SEMANTICS = {'frame': 'persist', 'conflict': 'exclusive', 'cascade': 'single_frame'}
GEOMETRY = 'grid'
DIRECTIONS = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
LANDMARKS = {}
BACKGROUND = 5
N_POS = None
GRID = (64, 64)
BOARD = [
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 8, 8, 8, 8, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2, 2, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 3, 3, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 14, 14, 14, 14, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 14, 14, 14, 14, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 14, 14, 14, 14, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 14, 14, 14, 14, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5, 5, 5, 5, 5],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 6, 6, 6, 6, 6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 0, 0, 0, 0, 6, 4, 8, 8, 8, 8, 4, 4, 14, 14, 14, 14, 4, 4, 9, 9, 9, 9, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 0, 6, 6, 0, 1, 2, 8, 8, 8, 8, 1, 2, 14, 14, 14, 14, 1, 2, 9, 9, 9, 9, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 0, 6, 6, 0, 2, 1, 8, 8, 8, 8, 2, 1, 14, 14, 14, 14, 2, 1, 9, 9, 9, 9, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 0, 0, 0, 0, 6, 4, 8, 8, 8, 8, 4, 4, 14, 14, 14, 14, 4, 4, 9, 9, 9, 9, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 6, 6, 6, 6, 6, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
    [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
]
ACTIONS = [('key', 3), ('key', 7), ('key', 4)]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Casing_r36c11_pos: object = (36, 11)
    Casing_r36c11_color: object = 6
    Casing_r36c12_pos: object = (36, 12)
    Casing_r36c12_color: object = 6
    Casing_r36c13_pos: object = (36, 13)
    Casing_r36c13_color: object = 6
    Casing_r36c14_pos: object = (36, 14)
    Casing_r36c14_color: object = 6
    Casing_r36c15_pos: object = (36, 15)
    Casing_r36c15_color: object = 6
    Casing_r36c16_pos: object = (36, 16)
    Casing_r36c16_color: object = 6
    Casing_r37c11_pos: object = (37, 11)
    Casing_r37c11_color: object = 6
    Casing_r37c16_pos: object = (37, 16)
    Casing_r37c16_color: object = 6
    Casing_r38c11_pos: object = (38, 11)
    Casing_r38c11_color: object = 6
    Casing_r38c13_pos: object = (38, 13)
    Casing_r38c13_color: object = 6
    Casing_r38c14_pos: object = (38, 14)
    Casing_r38c14_color: object = 6
    Casing_r39c11_pos: object = (39, 11)
    Casing_r39c11_color: object = 6
    Casing_r39c13_pos: object = (39, 13)
    Casing_r39c13_color: object = 6
    Casing_r39c14_pos: object = (39, 14)
    Casing_r39c14_color: object = 6
    Casing_r40c11_pos: object = (40, 11)
    Casing_r40c11_color: object = 6
    Casing_r40c16_pos: object = (40, 16)
    Casing_r40c16_color: object = 6
    Casing_r41c11_pos: object = (41, 11)
    Casing_r41c11_color: object = 6
    Casing_r41c12_pos: object = (41, 12)
    Casing_r41c12_color: object = 6
    Casing_r41c13_pos: object = (41, 13)
    Casing_r41c13_color: object = 6
    Casing_r41c14_pos: object = (41, 14)
    Casing_r41c14_color: object = 6
    Casing_r41c15_pos: object = (41, 15)
    Casing_r41c15_color: object = 6
    Casing_r41c16_pos: object = (41, 16)
    Casing_r41c16_color: object = 6
    Cavity_r37c12_pos: object = (37, 12)
    Cavity_r37c12_color: object = 0
    Cavity_r37c13_pos: object = (37, 13)
    Cavity_r37c13_color: object = 0
    Cavity_r37c14_pos: object = (37, 14)
    Cavity_r37c14_color: object = 0
    Cavity_r37c15_pos: object = (37, 15)
    Cavity_r37c15_color: object = 0
    Cavity_r38c12_pos: object = (38, 12)
    Cavity_r38c12_color: object = 0
    Cavity_r38c15_pos: object = (38, 15)
    Cavity_r38c15_color: object = 0
    Cavity_r39c12_pos: object = (39, 12)
    Cavity_r39c12_color: object = 0
    Cavity_r39c15_pos: object = (39, 15)
    Cavity_r39c15_color: object = 0
    Cavity_r40c12_pos: object = (40, 12)
    Cavity_r40c12_color: object = 0
    Cavity_r40c13_pos: object = (40, 13)
    Cavity_r40c13_color: object = 0
    Cavity_r40c14_pos: object = (40, 14)
    Cavity_r40c14_color: object = 0
    Cavity_r40c15_pos: object = (40, 15)
    Cavity_r40c15_color: object = 0
    Rail_r30c13_pos: object = (30, 13)
    Rail_r30c13_color: object = 3
    Rail_r30c14_pos: object = (30, 14)
    Rail_r30c14_color: object = 3
    Rail_r31c13_pos: object = (31, 13)
    Rail_r31c13_color: object = 3
    Rail_r31c14_pos: object = (31, 14)
    Rail_r31c14_color: object = 3
    Rail_r34c13_pos: object = (34, 13)
    Rail_r34c13_color: object = 3
    Rail_r34c14_pos: object = (34, 14)
    Rail_r34c14_color: object = 3
    Rail_r35c13_pos: object = (35, 13)
    Rail_r35c13_color: object = 3
    Rail_r35c14_pos: object = (35, 14)
    Rail_r35c14_color: object = 3
    Pip_r38c16_pos: object = (38, 16)
    Pip_r38c16_color: object = 1
    Pip_r38c18_pos: object = (38, 18)
    Pip_r38c18_color: object = 1
    Pip_r38c19_pos: object = (38, 19)
    Pip_r38c19_color: object = 1
    Pip_r38c21_pos: object = (38, 21)
    Pip_r38c21_color: object = 1
    Pip_r38c22_pos: object = (38, 22)
    Pip_r38c22_color: object = 1
    Pip_r39c17_pos: object = (39, 17)
    Pip_r39c17_color: object = 1
    Pip_r39c18_pos: object = (39, 18)
    Pip_r39c18_color: object = 1
    Pip_r39c20_pos: object = (39, 20)
    Pip_r39c20_color: object = 1
    Pip_r39c21_pos: object = (39, 21)
    Pip_r39c21_color: object = 1
    Stud_r32c13_pos: object = (32, 13)
    Stud_r32c13_color: object = 2
    Stud_r32c14_pos: object = (32, 14)
    Stud_r32c14_color: object = 2
    Stud_r33c13_pos: object = (33, 13)
    Stud_r33c13_color: object = 2
    Stud_r33c14_pos: object = (33, 14)
    Stud_r33c14_color: object = 2
    Stud_r38c17_pos: object = (38, 17)
    Stud_r38c17_color: object = 2
    Stud_r38c20_pos: object = (38, 20)
    Stud_r38c20_color: object = 2
    Stud_r39c16_pos: object = (39, 16)
    Stud_r39c16_color: object = 2
    Stud_r39c19_pos: object = (39, 19)
    Stud_r39c19_color: object = 2
    Stud_r39c22_pos: object = (39, 22)
    Stud_r39c22_color: object = 2
    Stud_r53c59_pos: object = (53, 59)
    Stud_r53c59_color: object = 2
    Stud_r53c60_pos: object = (53, 60)
    Stud_r53c60_color: object = 2
    Stud_r53c61_pos: object = (53, 61)
    Stud_r53c61_color: object = 2
    Stud_r53c62_pos: object = (53, 62)
    Stud_r53c62_color: object = 2
    Stud_r53c63_pos: object = (53, 63)
    Stud_r53c63_color: object = 2
    Erased_r32c17_pos: object = (32, 17)
    Erased_r32c17_color: object = 4
    Erased_r32c18_pos: object = (32, 18)
    Erased_r32c18_color: object = 4
    Erased_r32c19_pos: object = (32, 19)
    Erased_r32c19_color: object = 4
    Erased_r32c20_pos: object = (32, 20)
    Erased_r32c20_color: object = 4
    Erased_r32c21_pos: object = (32, 21)
    Erased_r32c21_color: object = 4
    Erased_r32c22_pos: object = (32, 22)
    Erased_r32c22_color: object = 4
    Erased_r33c17_pos: object = (33, 17)
    Erased_r33c17_color: object = 4
    Erased_r33c18_pos: object = (33, 18)
    Erased_r33c18_color: object = 4
    Erased_r33c19_pos: object = (33, 19)
    Erased_r33c19_color: object = 4
    Erased_r33c20_pos: object = (33, 20)
    Erased_r33c20_color: object = 4
    Erased_r33c21_pos: object = (33, 21)
    Erased_r33c21_color: object = 4
    Erased_r33c22_pos: object = (33, 22)
    Erased_r33c22_color: object = 4

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Casing_r36c11_pos, self.Casing_r36c11_color, self.Casing_r36c12_pos, self.Casing_r36c12_color, self.Casing_r36c13_pos, self.Casing_r36c13_color, self.Casing_r36c14_pos, self.Casing_r36c14_color, self.Casing_r36c15_pos, self.Casing_r36c15_color, self.Casing_r36c16_pos, self.Casing_r36c16_color, self.Casing_r37c11_pos, self.Casing_r37c11_color, self.Casing_r37c16_pos, self.Casing_r37c16_color, self.Casing_r38c11_pos, self.Casing_r38c11_color, self.Casing_r38c13_pos, self.Casing_r38c13_color, self.Casing_r38c14_pos, self.Casing_r38c14_color, self.Casing_r39c11_pos, self.Casing_r39c11_color, self.Casing_r39c13_pos, self.Casing_r39c13_color, self.Casing_r39c14_pos, self.Casing_r39c14_color, self.Casing_r40c11_pos, self.Casing_r40c11_color, self.Casing_r40c16_pos, self.Casing_r40c16_color, self.Casing_r41c11_pos, self.Casing_r41c11_color, self.Casing_r41c12_pos, self.Casing_r41c12_color, self.Casing_r41c13_pos, self.Casing_r41c13_color, self.Casing_r41c14_pos, self.Casing_r41c14_color, self.Casing_r41c15_pos, self.Casing_r41c15_color, self.Casing_r41c16_pos, self.Casing_r41c16_color, self.Cavity_r37c12_pos, self.Cavity_r37c12_color, self.Cavity_r37c13_pos, self.Cavity_r37c13_color, self.Cavity_r37c14_pos, self.Cavity_r37c14_color, self.Cavity_r37c15_pos, self.Cavity_r37c15_color, self.Cavity_r38c12_pos, self.Cavity_r38c12_color, self.Cavity_r38c15_pos, self.Cavity_r38c15_color, self.Cavity_r39c12_pos, self.Cavity_r39c12_color, self.Cavity_r39c15_pos, self.Cavity_r39c15_color, self.Cavity_r40c12_pos, self.Cavity_r40c12_color, self.Cavity_r40c13_pos, self.Cavity_r40c13_color, self.Cavity_r40c14_pos, self.Cavity_r40c14_color, self.Cavity_r40c15_pos, self.Cavity_r40c15_color, self.Rail_r30c13_pos, self.Rail_r30c13_color, self.Rail_r30c14_pos, self.Rail_r30c14_color, self.Rail_r31c13_pos, self.Rail_r31c13_color, self.Rail_r31c14_pos, self.Rail_r31c14_color, self.Rail_r34c13_pos, self.Rail_r34c13_color, self.Rail_r34c14_pos, self.Rail_r34c14_color, self.Rail_r35c13_pos, self.Rail_r35c13_color, self.Rail_r35c14_pos, self.Rail_r35c14_color, self.Pip_r38c16_pos, self.Pip_r38c16_color, self.Pip_r38c18_pos, self.Pip_r38c18_color, self.Pip_r38c19_pos, self.Pip_r38c19_color, self.Pip_r38c21_pos, self.Pip_r38c21_color, self.Pip_r38c22_pos, self.Pip_r38c22_color, self.Pip_r39c17_pos, self.Pip_r39c17_color, self.Pip_r39c18_pos, self.Pip_r39c18_color, self.Pip_r39c20_pos, self.Pip_r39c20_color, self.Pip_r39c21_pos, self.Pip_r39c21_color, self.Stud_r32c13_pos, self.Stud_r32c13_color, self.Stud_r32c14_pos, self.Stud_r32c14_color, self.Stud_r33c13_pos, self.Stud_r33c13_color, self.Stud_r33c14_pos, self.Stud_r33c14_color, self.Stud_r38c17_pos, self.Stud_r38c17_color, self.Stud_r38c20_pos, self.Stud_r38c20_color, self.Stud_r39c16_pos, self.Stud_r39c16_color, self.Stud_r39c19_pos, self.Stud_r39c19_color, self.Stud_r39c22_pos, self.Stud_r39c22_color, self.Stud_r53c59_pos, self.Stud_r53c59_color, self.Stud_r53c60_pos, self.Stud_r53c60_color, self.Stud_r53c61_pos, self.Stud_r53c61_color, self.Stud_r53c62_pos, self.Stud_r53c62_color, self.Stud_r53c63_pos, self.Stud_r53c63_color, self.Erased_r32c17_pos, self.Erased_r32c17_color, self.Erased_r32c18_pos, self.Erased_r32c18_color, self.Erased_r32c19_pos, self.Erased_r32c19_color, self.Erased_r32c20_pos, self.Erased_r32c20_color, self.Erased_r32c21_pos, self.Erased_r32c21_color, self.Erased_r32c22_pos, self.Erased_r32c22_color, self.Erased_r33c17_pos, self.Erased_r33c17_color, self.Erased_r33c18_pos, self.Erased_r33c18_color, self.Erased_r33c19_pos, self.Erased_r33c19_color, self.Erased_r33c20_pos, self.Erased_r33c20_color, self.Erased_r33c21_pos, self.Erased_r33c21_color, self.Erased_r33c22_pos, self.Erased_r33c22_color,)


def _neighbour(cell, direction):
    dr, dc = DIRECTIONS[direction]
    return (cell[0] + dr, cell[1] + dc)


def _in_bounds(cell):
    return 0 <= cell[0] < GRID[0] and 0 <= cell[1] < GRID[1]


def _adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def render(state, _exclude=()):
    """The manual drawn back onto a frame.

    `_exclude` leaves the named instances off the frame. It exists
    for `_free_except` and ledger X-5: asking whether an object's
    own cell is free is a question about the board and the *other*
    objects, and painting the asker onto the frame first makes the
    answer unconditionally False.
    """
    grid = [list(row) for row in BOARD]
    if 'Casing_r36c11' not in _exclude:
        r, c = state.Casing_r36c11_pos
        grid[r][c] = state.Casing_r36c11_color
    if 'Casing_r36c12' not in _exclude:
        r, c = state.Casing_r36c12_pos
        grid[r][c] = state.Casing_r36c12_color
    if 'Casing_r36c13' not in _exclude:
        r, c = state.Casing_r36c13_pos
        grid[r][c] = state.Casing_r36c13_color
    if 'Casing_r36c14' not in _exclude:
        r, c = state.Casing_r36c14_pos
        grid[r][c] = state.Casing_r36c14_color
    if 'Casing_r36c15' not in _exclude:
        r, c = state.Casing_r36c15_pos
        grid[r][c] = state.Casing_r36c15_color
    if 'Casing_r36c16' not in _exclude:
        r, c = state.Casing_r36c16_pos
        grid[r][c] = state.Casing_r36c16_color
    if 'Casing_r37c11' not in _exclude:
        r, c = state.Casing_r37c11_pos
        grid[r][c] = state.Casing_r37c11_color
    if 'Casing_r37c16' not in _exclude:
        r, c = state.Casing_r37c16_pos
        grid[r][c] = state.Casing_r37c16_color
    if 'Casing_r38c11' not in _exclude:
        r, c = state.Casing_r38c11_pos
        grid[r][c] = state.Casing_r38c11_color
    if 'Casing_r38c13' not in _exclude:
        r, c = state.Casing_r38c13_pos
        grid[r][c] = state.Casing_r38c13_color
    if 'Casing_r38c14' not in _exclude:
        r, c = state.Casing_r38c14_pos
        grid[r][c] = state.Casing_r38c14_color
    if 'Casing_r39c11' not in _exclude:
        r, c = state.Casing_r39c11_pos
        grid[r][c] = state.Casing_r39c11_color
    if 'Casing_r39c13' not in _exclude:
        r, c = state.Casing_r39c13_pos
        grid[r][c] = state.Casing_r39c13_color
    if 'Casing_r39c14' not in _exclude:
        r, c = state.Casing_r39c14_pos
        grid[r][c] = state.Casing_r39c14_color
    if 'Casing_r40c11' not in _exclude:
        r, c = state.Casing_r40c11_pos
        grid[r][c] = state.Casing_r40c11_color
    if 'Casing_r40c16' not in _exclude:
        r, c = state.Casing_r40c16_pos
        grid[r][c] = state.Casing_r40c16_color
    if 'Casing_r41c11' not in _exclude:
        r, c = state.Casing_r41c11_pos
        grid[r][c] = state.Casing_r41c11_color
    if 'Casing_r41c12' not in _exclude:
        r, c = state.Casing_r41c12_pos
        grid[r][c] = state.Casing_r41c12_color
    if 'Casing_r41c13' not in _exclude:
        r, c = state.Casing_r41c13_pos
        grid[r][c] = state.Casing_r41c13_color
    if 'Casing_r41c14' not in _exclude:
        r, c = state.Casing_r41c14_pos
        grid[r][c] = state.Casing_r41c14_color
    if 'Casing_r41c15' not in _exclude:
        r, c = state.Casing_r41c15_pos
        grid[r][c] = state.Casing_r41c15_color
    if 'Casing_r41c16' not in _exclude:
        r, c = state.Casing_r41c16_pos
        grid[r][c] = state.Casing_r41c16_color
    if 'Cavity_r37c12' not in _exclude:
        r, c = state.Cavity_r37c12_pos
        grid[r][c] = state.Cavity_r37c12_color
    if 'Cavity_r37c13' not in _exclude:
        r, c = state.Cavity_r37c13_pos
        grid[r][c] = state.Cavity_r37c13_color
    if 'Cavity_r37c14' not in _exclude:
        r, c = state.Cavity_r37c14_pos
        grid[r][c] = state.Cavity_r37c14_color
    if 'Cavity_r37c15' not in _exclude:
        r, c = state.Cavity_r37c15_pos
        grid[r][c] = state.Cavity_r37c15_color
    if 'Cavity_r38c12' not in _exclude:
        r, c = state.Cavity_r38c12_pos
        grid[r][c] = state.Cavity_r38c12_color
    if 'Cavity_r38c15' not in _exclude:
        r, c = state.Cavity_r38c15_pos
        grid[r][c] = state.Cavity_r38c15_color
    if 'Cavity_r39c12' not in _exclude:
        r, c = state.Cavity_r39c12_pos
        grid[r][c] = state.Cavity_r39c12_color
    if 'Cavity_r39c15' not in _exclude:
        r, c = state.Cavity_r39c15_pos
        grid[r][c] = state.Cavity_r39c15_color
    if 'Cavity_r40c12' not in _exclude:
        r, c = state.Cavity_r40c12_pos
        grid[r][c] = state.Cavity_r40c12_color
    if 'Cavity_r40c13' not in _exclude:
        r, c = state.Cavity_r40c13_pos
        grid[r][c] = state.Cavity_r40c13_color
    if 'Cavity_r40c14' not in _exclude:
        r, c = state.Cavity_r40c14_pos
        grid[r][c] = state.Cavity_r40c14_color
    if 'Cavity_r40c15' not in _exclude:
        r, c = state.Cavity_r40c15_pos
        grid[r][c] = state.Cavity_r40c15_color
    if 'Rail_r30c13' not in _exclude:
        r, c = state.Rail_r30c13_pos
        grid[r][c] = state.Rail_r30c13_color
    if 'Rail_r30c14' not in _exclude:
        r, c = state.Rail_r30c14_pos
        grid[r][c] = state.Rail_r30c14_color
    if 'Rail_r31c13' not in _exclude:
        r, c = state.Rail_r31c13_pos
        grid[r][c] = state.Rail_r31c13_color
    if 'Rail_r31c14' not in _exclude:
        r, c = state.Rail_r31c14_pos
        grid[r][c] = state.Rail_r31c14_color
    if 'Rail_r34c13' not in _exclude:
        r, c = state.Rail_r34c13_pos
        grid[r][c] = state.Rail_r34c13_color
    if 'Rail_r34c14' not in _exclude:
        r, c = state.Rail_r34c14_pos
        grid[r][c] = state.Rail_r34c14_color
    if 'Rail_r35c13' not in _exclude:
        r, c = state.Rail_r35c13_pos
        grid[r][c] = state.Rail_r35c13_color
    if 'Rail_r35c14' not in _exclude:
        r, c = state.Rail_r35c14_pos
        grid[r][c] = state.Rail_r35c14_color
    if 'Pip_r38c16' not in _exclude:
        r, c = state.Pip_r38c16_pos
        grid[r][c] = state.Pip_r38c16_color
    if 'Pip_r38c18' not in _exclude:
        r, c = state.Pip_r38c18_pos
        grid[r][c] = state.Pip_r38c18_color
    if 'Pip_r38c19' not in _exclude:
        r, c = state.Pip_r38c19_pos
        grid[r][c] = state.Pip_r38c19_color
    if 'Pip_r38c21' not in _exclude:
        r, c = state.Pip_r38c21_pos
        grid[r][c] = state.Pip_r38c21_color
    if 'Pip_r38c22' not in _exclude:
        r, c = state.Pip_r38c22_pos
        grid[r][c] = state.Pip_r38c22_color
    if 'Pip_r39c17' not in _exclude:
        r, c = state.Pip_r39c17_pos
        grid[r][c] = state.Pip_r39c17_color
    if 'Pip_r39c18' not in _exclude:
        r, c = state.Pip_r39c18_pos
        grid[r][c] = state.Pip_r39c18_color
    if 'Pip_r39c20' not in _exclude:
        r, c = state.Pip_r39c20_pos
        grid[r][c] = state.Pip_r39c20_color
    if 'Pip_r39c21' not in _exclude:
        r, c = state.Pip_r39c21_pos
        grid[r][c] = state.Pip_r39c21_color
    if 'Stud_r32c13' not in _exclude:
        r, c = state.Stud_r32c13_pos
        grid[r][c] = state.Stud_r32c13_color
    if 'Stud_r32c14' not in _exclude:
        r, c = state.Stud_r32c14_pos
        grid[r][c] = state.Stud_r32c14_color
    if 'Stud_r33c13' not in _exclude:
        r, c = state.Stud_r33c13_pos
        grid[r][c] = state.Stud_r33c13_color
    if 'Stud_r33c14' not in _exclude:
        r, c = state.Stud_r33c14_pos
        grid[r][c] = state.Stud_r33c14_color
    if 'Stud_r38c17' not in _exclude:
        r, c = state.Stud_r38c17_pos
        grid[r][c] = state.Stud_r38c17_color
    if 'Stud_r38c20' not in _exclude:
        r, c = state.Stud_r38c20_pos
        grid[r][c] = state.Stud_r38c20_color
    if 'Stud_r39c16' not in _exclude:
        r, c = state.Stud_r39c16_pos
        grid[r][c] = state.Stud_r39c16_color
    if 'Stud_r39c19' not in _exclude:
        r, c = state.Stud_r39c19_pos
        grid[r][c] = state.Stud_r39c19_color
    if 'Stud_r39c22' not in _exclude:
        r, c = state.Stud_r39c22_pos
        grid[r][c] = state.Stud_r39c22_color
    if 'Stud_r53c59' not in _exclude:
        r, c = state.Stud_r53c59_pos
        grid[r][c] = state.Stud_r53c59_color
    if 'Stud_r53c60' not in _exclude:
        r, c = state.Stud_r53c60_pos
        grid[r][c] = state.Stud_r53c60_color
    if 'Stud_r53c61' not in _exclude:
        r, c = state.Stud_r53c61_pos
        grid[r][c] = state.Stud_r53c61_color
    if 'Stud_r53c62' not in _exclude:
        r, c = state.Stud_r53c62_pos
        grid[r][c] = state.Stud_r53c62_color
    if 'Stud_r53c63' not in _exclude:
        r, c = state.Stud_r53c63_pos
        grid[r][c] = state.Stud_r53c63_color
    if 'Erased_r32c17' not in _exclude:
        r, c = state.Erased_r32c17_pos
        grid[r][c] = state.Erased_r32c17_color
    if 'Erased_r32c18' not in _exclude:
        r, c = state.Erased_r32c18_pos
        grid[r][c] = state.Erased_r32c18_color
    if 'Erased_r32c19' not in _exclude:
        r, c = state.Erased_r32c19_pos
        grid[r][c] = state.Erased_r32c19_color
    if 'Erased_r32c20' not in _exclude:
        r, c = state.Erased_r32c20_pos
        grid[r][c] = state.Erased_r32c20_color
    if 'Erased_r32c21' not in _exclude:
        r, c = state.Erased_r32c21_pos
        grid[r][c] = state.Erased_r32c21_color
    if 'Erased_r32c22' not in _exclude:
        r, c = state.Erased_r32c22_pos
        grid[r][c] = state.Erased_r32c22_color
    if 'Erased_r33c17' not in _exclude:
        r, c = state.Erased_r33c17_pos
        grid[r][c] = state.Erased_r33c17_color
    if 'Erased_r33c18' not in _exclude:
        r, c = state.Erased_r33c18_pos
        grid[r][c] = state.Erased_r33c18_color
    if 'Erased_r33c19' not in _exclude:
        r, c = state.Erased_r33c19_pos
        grid[r][c] = state.Erased_r33c19_color
    if 'Erased_r33c20' not in _exclude:
        r, c = state.Erased_r33c20_pos
        grid[r][c] = state.Erased_r33c20_color
    if 'Erased_r33c21' not in _exclude:
        r, c = state.Erased_r33c21_pos
        grid[r][c] = state.Erased_r33c21_color
    if 'Erased_r33c22' not in _exclude:
        r, c = state.Erased_r33c22_pos
        grid[r][c] = state.Erased_r33c22_color
    return grid


def _cell_colour(state, cell, _exclude=()):
    if not _in_bounds(cell):
        return None
    return render(state, _exclude)[cell[0]][cell[1]]


def _free(state, cell):
    return _cell_colour(state, cell) == BACKGROUND


def _free_except(state, cell, exclude):
    """`free(<obj>.pos)` — is the asker's own cell a legal empty one?

    Ledger X-5. On the board, not a wall, and nobody *else* on it.
    False exactly when the object stands off the board, on a wall,
    or on top of another object.
    """
    return _cell_colour(state, cell, exclude) == BACKGROUND


def occupancy(state):
    """The frame as a bitstring — the view a pagoda weight sees."""
    return ''.join('0' if v == BACKGROUND else '1'
                   for row in render(state) for v in row)


def _guard_key3_blanks_the_strip_pips__Pip_r38c16(state, action):
    """key3_blanks_the_strip_pips__Pip_r38c16  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r38c16_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c16_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r38c16(state):
    state.Pip_r38c16_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r38c18(state, action):
    """key3_blanks_the_strip_pips__Pip_r38c18  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r38c18_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c18_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r38c18(state):
    state.Pip_r38c18_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r38c19(state, action):
    """key3_blanks_the_strip_pips__Pip_r38c19  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r38c19_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c19_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r38c19(state):
    state.Pip_r38c19_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r38c21(state, action):
    """key3_blanks_the_strip_pips__Pip_r38c21  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r38c21_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c21_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r38c21(state):
    state.Pip_r38c21_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r38c22(state, action):
    """key3_blanks_the_strip_pips__Pip_r38c22  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r38c22_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c22_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r38c22(state):
    state.Pip_r38c22_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r39c17(state, action):
    """key3_blanks_the_strip_pips__Pip_r39c17  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r39c17_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c17_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r39c17(state):
    state.Pip_r39c17_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r39c18(state, action):
    """key3_blanks_the_strip_pips__Pip_r39c18  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r39c18_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c18_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r39c18(state):
    state.Pip_r39c18_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r39c20(state, action):
    """key3_blanks_the_strip_pips__Pip_r39c20  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r39c20_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c20_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r39c20(state):
    state.Pip_r39c20_color = 4


def _guard_key3_blanks_the_strip_pips__Pip_r39c21(state, action):
    """key3_blanks_the_strip_pips__Pip_r39c21  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 56/56]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Pip_r39c21_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c21_pos, 'left')) == 0): return False
    return True


def _effect_key3_blanks_the_strip_pips__Pip_r39c21(state):
    state.Pip_r39c21_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r32c13(state, action):
    """key3_blanks_the_strip_studs__Stud_r32c13  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r32c13_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r32c13(state):
    state.Stud_r32c13_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r32c14(state, action):
    """key3_blanks_the_strip_studs__Stud_r32c14  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r32c14_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r32c14(state):
    state.Stud_r32c14_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r33c13(state, action):
    """key3_blanks_the_strip_studs__Stud_r33c13  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r33c13_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r33c13(state):
    state.Stud_r33c13_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r33c14(state, action):
    """key3_blanks_the_strip_studs__Stud_r33c14  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r33c14_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r33c14(state):
    state.Stud_r33c14_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r38c17(state, action):
    """key3_blanks_the_strip_studs__Stud_r38c17  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r38c17_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r38c17(state):
    state.Stud_r38c17_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r38c20(state, action):
    """key3_blanks_the_strip_studs__Stud_r38c20  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r38c20_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r38c20(state):
    state.Stud_r38c20_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r39c16(state, action):
    """key3_blanks_the_strip_studs__Stud_r39c16  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c16_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r39c16(state):
    state.Stud_r39c16_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r39c19(state, action):
    """key3_blanks_the_strip_studs__Stud_r39c19  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c19_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r39c19(state):
    state.Stud_r39c19_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r39c22(state, action):
    """key3_blanks_the_strip_studs__Stud_r39c22  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c22_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r39c22(state):
    state.Stud_r39c22_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r53c59(state, action):
    """key3_blanks_the_strip_studs__Stud_r53c59  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c59_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r53c59(state):
    state.Stud_r53c59_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r53c60(state, action):
    """key3_blanks_the_strip_studs__Stud_r53c60  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c60_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r53c60(state):
    state.Stud_r53c60_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r53c61(state, action):
    """key3_blanks_the_strip_studs__Stud_r53c61  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c61_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r53c61(state):
    state.Stud_r53c61_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r53c62(state, action):
    """key3_blanks_the_strip_studs__Stud_r53c62  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c62_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r53c62(state):
    state.Stud_r53c62_color = 4


def _guard_key3_blanks_the_strip_studs__Stud_r53c63(state, action):
    """key3_blanks_the_strip_studs__Stud_r53c63  [ev: t3,t7,t9,t11,t13,t15,t17  cov: 28/28]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c63_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'right')) == 2): return False
    return True


def _effect_key3_blanks_the_strip_studs__Stud_r53c63(state):
    state.Stud_r53c63_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r38c16(state, action):
    """key7_blanks_the_strip_pips__Pip_r38c16  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r38c16_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c16_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r38c16(state):
    state.Pip_r38c16_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r38c18(state, action):
    """key7_blanks_the_strip_pips__Pip_r38c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r38c18_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c18_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r38c18(state):
    state.Pip_r38c18_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r38c19(state, action):
    """key7_blanks_the_strip_pips__Pip_r38c19  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r38c19_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c19_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r38c19(state):
    state.Pip_r38c19_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r38c21(state, action):
    """key7_blanks_the_strip_pips__Pip_r38c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r38c21_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c21_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r38c21(state):
    state.Pip_r38c21_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r38c22(state, action):
    """key7_blanks_the_strip_pips__Pip_r38c22  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r38c22_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r38c22_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r38c22(state):
    state.Pip_r38c22_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r39c17(state, action):
    """key7_blanks_the_strip_pips__Pip_r39c17  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r39c17_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c17_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r39c17(state):
    state.Pip_r39c17_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r39c18(state, action):
    """key7_blanks_the_strip_pips__Pip_r39c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r39c18_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c18_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r39c18(state):
    state.Pip_r39c18_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r39c20(state, action):
    """key7_blanks_the_strip_pips__Pip_r39c20  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r39c20_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c20_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r39c20(state):
    state.Pip_r39c20_color = 4


def _guard_key7_blanks_the_strip_pips__Pip_r39c21(state, action):
    """key7_blanks_the_strip_pips__Pip_r39c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Pip_r39c21_pos) == 1): return False
    if (_cell_colour(state, _neighbour(state.Pip_r39c21_pos, 'left')) == 0): return False
    return True


def _effect_key7_blanks_the_strip_pips__Pip_r39c21(state):
    state.Pip_r39c21_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r32c13(state, action):
    """key7_blanks_the_strip_studs__Stud_r32c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r32c13_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r32c13(state):
    state.Stud_r32c13_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r32c14(state, action):
    """key7_blanks_the_strip_studs__Stud_r32c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r32c14_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r32c14(state):
    state.Stud_r32c14_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r33c13(state, action):
    """key7_blanks_the_strip_studs__Stud_r33c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r33c13_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r33c13(state):
    state.Stud_r33c13_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r33c14(state, action):
    """key7_blanks_the_strip_studs__Stud_r33c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r33c14_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r33c14(state):
    state.Stud_r33c14_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r38c17(state, action):
    """key7_blanks_the_strip_studs__Stud_r38c17  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r38c17_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r38c17(state):
    state.Stud_r38c17_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r38c20(state, action):
    """key7_blanks_the_strip_studs__Stud_r38c20  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r38c20_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r38c20(state):
    state.Stud_r38c20_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r39c16(state, action):
    """key7_blanks_the_strip_studs__Stud_r39c16  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r39c16_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r39c16(state):
    state.Stud_r39c16_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r39c19(state, action):
    """key7_blanks_the_strip_studs__Stud_r39c19  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r39c19_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r39c19(state):
    state.Stud_r39c19_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r39c22(state, action):
    """key7_blanks_the_strip_studs__Stud_r39c22  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r39c22_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r39c22(state):
    state.Stud_r39c22_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r53c59(state, action):
    """key7_blanks_the_strip_studs__Stud_r53c59  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r53c59_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r53c59(state):
    state.Stud_r53c59_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r53c60(state, action):
    """key7_blanks_the_strip_studs__Stud_r53c60  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r53c60_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r53c60(state):
    state.Stud_r53c60_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r53c61(state, action):
    """key7_blanks_the_strip_studs__Stud_r53c61  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r53c61_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r53c61(state):
    state.Stud_r53c61_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r53c62(state, action):
    """key7_blanks_the_strip_studs__Stud_r53c62  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r53c62_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r53c62(state):
    state.Stud_r53c62_color = 4


def _guard_key7_blanks_the_strip_studs__Stud_r53c63(state, action):
    """key7_blanks_the_strip_studs__Stud_r53c63  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Stud_r53c63_pos) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'left')) == 0): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'left')) == 2): return False
    if (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'right')) == 2): return False
    return True


def _effect_key7_blanks_the_strip_studs__Stud_r53c63(state):
    state.Stud_r53c63_color = 4


def _guard_key4_restores_the_strip_pips__Pip_r38c16(state, action):
    """key4_restores_the_strip_pips__Pip_r38c16  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r38c16_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r38c16(state):
    state.Pip_r38c16_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r38c18(state, action):
    """key4_restores_the_strip_pips__Pip_r38c18  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r38c18_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r38c18(state):
    state.Pip_r38c18_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r38c19(state, action):
    """key4_restores_the_strip_pips__Pip_r38c19  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r38c19_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r38c19(state):
    state.Pip_r38c19_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r38c21(state, action):
    """key4_restores_the_strip_pips__Pip_r38c21  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r38c21_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r38c21(state):
    state.Pip_r38c21_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r38c22(state, action):
    """key4_restores_the_strip_pips__Pip_r38c22  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r38c22_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r38c22(state):
    state.Pip_r38c22_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r39c17(state, action):
    """key4_restores_the_strip_pips__Pip_r39c17  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r39c17_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r39c17(state):
    state.Pip_r39c17_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r39c18(state, action):
    """key4_restores_the_strip_pips__Pip_r39c18  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r39c18_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r39c18(state):
    state.Pip_r39c18_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r39c20(state, action):
    """key4_restores_the_strip_pips__Pip_r39c20  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r39c20_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r39c20(state):
    state.Pip_r39c20_color = 1


def _guard_key4_restores_the_strip_pips__Pip_r39c21(state, action):
    """key4_restores_the_strip_pips__Pip_r39c21  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 56/56]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Pip_r39c21_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_pips__Pip_r39c21(state):
    state.Pip_r39c21_color = 1


def _guard_key4_restores_the_strip_studs__Stud_r32c13(state, action):
    """key4_restores_the_strip_studs__Stud_r32c13  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r32c13_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r32c13(state):
    state.Stud_r32c13_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r32c14(state, action):
    """key4_restores_the_strip_studs__Stud_r32c14  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r32c14_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r32c14(state):
    state.Stud_r32c14_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r33c13(state, action):
    """key4_restores_the_strip_studs__Stud_r33c13  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r33c13_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r33c13(state):
    state.Stud_r33c13_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r33c14(state, action):
    """key4_restores_the_strip_studs__Stud_r33c14  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r33c14_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r33c14(state):
    state.Stud_r33c14_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r38c17(state, action):
    """key4_restores_the_strip_studs__Stud_r38c17  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r38c17_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r38c17(state):
    state.Stud_r38c17_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r38c20(state, action):
    """key4_restores_the_strip_studs__Stud_r38c20  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r38c20_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r38c20(state):
    state.Stud_r38c20_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r39c16(state, action):
    """key4_restores_the_strip_studs__Stud_r39c16  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c16_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r39c16(state):
    state.Stud_r39c16_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r39c19(state, action):
    """key4_restores_the_strip_studs__Stud_r39c19  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c19_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r39c19(state):
    state.Stud_r39c19_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r39c22(state, action):
    """key4_restores_the_strip_studs__Stud_r39c22  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c22_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r39c22(state):
    state.Stud_r39c22_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r53c59(state, action):
    """key4_restores_the_strip_studs__Stud_r53c59  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c59_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r53c59(state):
    state.Stud_r53c59_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r53c60(state, action):
    """key4_restores_the_strip_studs__Stud_r53c60  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c60_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r53c60(state):
    state.Stud_r53c60_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r53c61(state, action):
    """key4_restores_the_strip_studs__Stud_r53c61  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c61_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r53c61(state):
    state.Stud_r53c61_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r53c62(state, action):
    """key4_restores_the_strip_studs__Stud_r53c62  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c62_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r53c62(state):
    state.Stud_r53c62_color = 2


def _guard_key4_restores_the_strip_studs__Stud_r53c63(state, action):
    """key4_restores_the_strip_studs__Stud_r53c63  [ev: t4,t6,t8,t10,t12,t14,t16  cov: 28/28]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c63_pos) == 4): return False
    return True


def _effect_key4_restores_the_strip_studs__Stud_r53c63(state):
    state.Stud_r53c63_color = 2


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r32c13(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r32c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r32c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r32c13_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r32c13(state):
    state.Stud_r32c13_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r32c14(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r32c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r32c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r32c14_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r32c14(state):
    state.Stud_r32c14_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r33c13(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r33c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r33c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r33c13_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r33c13(state):
    state.Stud_r33c13_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r33c14(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r33c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r33c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r33c14_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r33c14(state):
    state.Stud_r33c14_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r38c17(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r38c17  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r38c17_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r38c17_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r38c17(state):
    state.Stud_r38c17_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r38c20(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r38c20  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r38c20_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r38c20_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r38c20(state):
    state.Stud_r38c20_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c16(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r39c16  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c16_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r39c16_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c16(state):
    state.Stud_r39c16_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c19(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r39c19  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c19_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r39c19_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c19(state):
    state.Stud_r39c19_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c22(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r39c22  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r39c22_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r39c22_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c22(state):
    state.Stud_r39c22_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c59(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r53c59  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c59_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r53c59_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c59(state):
    state.Stud_r53c59_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c60(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r53c60  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c60_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r53c60_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c60(state):
    state.Stud_r53c60_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c61(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r53c61  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c61_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r53c61_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c61(state):
    state.Stud_r53c61_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c62(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r53c62  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c62_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r53c62_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c62(state):
    state.Stud_r53c62_color = 3


def _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c63(state, action):
    """key4_seeds_the_meter_at_the_right_edge__Stud_r53c63  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Stud_r53c63_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Stud_r53c63_pos, 'right'))): return False
    return True


def _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c63(state):
    state.Stud_r53c63_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r32c13(state, action):
    """key3_marches_the_meter_leftward__Stud_r32c13  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r32c13_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r32c13(state):
    state.Stud_r32c13_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r32c14(state, action):
    """key3_marches_the_meter_leftward__Stud_r32c14  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r32c14_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r32c14(state):
    state.Stud_r32c14_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r33c13(state, action):
    """key3_marches_the_meter_leftward__Stud_r33c13  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r33c13_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r33c13(state):
    state.Stud_r33c13_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r33c14(state, action):
    """key3_marches_the_meter_leftward__Stud_r33c14  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r33c14_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r33c14(state):
    state.Stud_r33c14_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r38c17(state, action):
    """key3_marches_the_meter_leftward__Stud_r38c17  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r38c17_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r38c17(state):
    state.Stud_r38c17_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r38c20(state, action):
    """key3_marches_the_meter_leftward__Stud_r38c20  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r38c20_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r38c20(state):
    state.Stud_r38c20_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r39c16(state, action):
    """key3_marches_the_meter_leftward__Stud_r39c16  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r39c16_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r39c16(state):
    state.Stud_r39c16_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r39c19(state, action):
    """key3_marches_the_meter_leftward__Stud_r39c19  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r39c19_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r39c19(state):
    state.Stud_r39c19_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r39c22(state, action):
    """key3_marches_the_meter_leftward__Stud_r39c22  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r39c22_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r39c22(state):
    state.Stud_r39c22_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r53c59(state, action):
    """key3_marches_the_meter_leftward__Stud_r53c59  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r53c59_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r53c59(state):
    state.Stud_r53c59_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r53c60(state, action):
    """key3_marches_the_meter_leftward__Stud_r53c60  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r53c60_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r53c60(state):
    state.Stud_r53c60_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r53c61(state, action):
    """key3_marches_the_meter_leftward__Stud_r53c61  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r53c61_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r53c61(state):
    state.Stud_r53c61_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r53c62(state, action):
    """key3_marches_the_meter_leftward__Stud_r53c62  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r53c62_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r53c62(state):
    state.Stud_r53c62_color = 3


def _guard_key3_marches_the_meter_leftward__Stud_r53c63(state, action):
    """key3_marches_the_meter_leftward__Stud_r53c63  [ev: t8,t11,t14,t17  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Stud_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.Stud_r53c63_pos, 'right')) == 3): return False
    return True


def _effect_key3_marches_the_meter_leftward__Stud_r53c63(state):
    state.Stud_r53c63_color = 3


RULES = [
    ('key3_blanks_the_strip_pips__Pip_r38c16', _guard_key3_blanks_the_strip_pips__Pip_r38c16, _effect_key3_blanks_the_strip_pips__Pip_r38c16, ['Pip_r38c16']),
    ('key3_blanks_the_strip_pips__Pip_r38c18', _guard_key3_blanks_the_strip_pips__Pip_r38c18, _effect_key3_blanks_the_strip_pips__Pip_r38c18, ['Pip_r38c18']),
    ('key3_blanks_the_strip_pips__Pip_r38c19', _guard_key3_blanks_the_strip_pips__Pip_r38c19, _effect_key3_blanks_the_strip_pips__Pip_r38c19, ['Pip_r38c19']),
    ('key3_blanks_the_strip_pips__Pip_r38c21', _guard_key3_blanks_the_strip_pips__Pip_r38c21, _effect_key3_blanks_the_strip_pips__Pip_r38c21, ['Pip_r38c21']),
    ('key3_blanks_the_strip_pips__Pip_r38c22', _guard_key3_blanks_the_strip_pips__Pip_r38c22, _effect_key3_blanks_the_strip_pips__Pip_r38c22, ['Pip_r38c22']),
    ('key3_blanks_the_strip_pips__Pip_r39c17', _guard_key3_blanks_the_strip_pips__Pip_r39c17, _effect_key3_blanks_the_strip_pips__Pip_r39c17, ['Pip_r39c17']),
    ('key3_blanks_the_strip_pips__Pip_r39c18', _guard_key3_blanks_the_strip_pips__Pip_r39c18, _effect_key3_blanks_the_strip_pips__Pip_r39c18, ['Pip_r39c18']),
    ('key3_blanks_the_strip_pips__Pip_r39c20', _guard_key3_blanks_the_strip_pips__Pip_r39c20, _effect_key3_blanks_the_strip_pips__Pip_r39c20, ['Pip_r39c20']),
    ('key3_blanks_the_strip_pips__Pip_r39c21', _guard_key3_blanks_the_strip_pips__Pip_r39c21, _effect_key3_blanks_the_strip_pips__Pip_r39c21, ['Pip_r39c21']),
    ('key3_blanks_the_strip_studs__Stud_r32c13', _guard_key3_blanks_the_strip_studs__Stud_r32c13, _effect_key3_blanks_the_strip_studs__Stud_r32c13, ['Stud_r32c13']),
    ('key3_blanks_the_strip_studs__Stud_r32c14', _guard_key3_blanks_the_strip_studs__Stud_r32c14, _effect_key3_blanks_the_strip_studs__Stud_r32c14, ['Stud_r32c14']),
    ('key3_blanks_the_strip_studs__Stud_r33c13', _guard_key3_blanks_the_strip_studs__Stud_r33c13, _effect_key3_blanks_the_strip_studs__Stud_r33c13, ['Stud_r33c13']),
    ('key3_blanks_the_strip_studs__Stud_r33c14', _guard_key3_blanks_the_strip_studs__Stud_r33c14, _effect_key3_blanks_the_strip_studs__Stud_r33c14, ['Stud_r33c14']),
    ('key3_blanks_the_strip_studs__Stud_r38c17', _guard_key3_blanks_the_strip_studs__Stud_r38c17, _effect_key3_blanks_the_strip_studs__Stud_r38c17, ['Stud_r38c17']),
    ('key3_blanks_the_strip_studs__Stud_r38c20', _guard_key3_blanks_the_strip_studs__Stud_r38c20, _effect_key3_blanks_the_strip_studs__Stud_r38c20, ['Stud_r38c20']),
    ('key3_blanks_the_strip_studs__Stud_r39c16', _guard_key3_blanks_the_strip_studs__Stud_r39c16, _effect_key3_blanks_the_strip_studs__Stud_r39c16, ['Stud_r39c16']),
    ('key3_blanks_the_strip_studs__Stud_r39c19', _guard_key3_blanks_the_strip_studs__Stud_r39c19, _effect_key3_blanks_the_strip_studs__Stud_r39c19, ['Stud_r39c19']),
    ('key3_blanks_the_strip_studs__Stud_r39c22', _guard_key3_blanks_the_strip_studs__Stud_r39c22, _effect_key3_blanks_the_strip_studs__Stud_r39c22, ['Stud_r39c22']),
    ('key3_blanks_the_strip_studs__Stud_r53c59', _guard_key3_blanks_the_strip_studs__Stud_r53c59, _effect_key3_blanks_the_strip_studs__Stud_r53c59, ['Stud_r53c59']),
    ('key3_blanks_the_strip_studs__Stud_r53c60', _guard_key3_blanks_the_strip_studs__Stud_r53c60, _effect_key3_blanks_the_strip_studs__Stud_r53c60, ['Stud_r53c60']),
    ('key3_blanks_the_strip_studs__Stud_r53c61', _guard_key3_blanks_the_strip_studs__Stud_r53c61, _effect_key3_blanks_the_strip_studs__Stud_r53c61, ['Stud_r53c61']),
    ('key3_blanks_the_strip_studs__Stud_r53c62', _guard_key3_blanks_the_strip_studs__Stud_r53c62, _effect_key3_blanks_the_strip_studs__Stud_r53c62, ['Stud_r53c62']),
    ('key3_blanks_the_strip_studs__Stud_r53c63', _guard_key3_blanks_the_strip_studs__Stud_r53c63, _effect_key3_blanks_the_strip_studs__Stud_r53c63, ['Stud_r53c63']),
    ('key7_blanks_the_strip_pips__Pip_r38c16', _guard_key7_blanks_the_strip_pips__Pip_r38c16, _effect_key7_blanks_the_strip_pips__Pip_r38c16, ['Pip_r38c16']),
    ('key7_blanks_the_strip_pips__Pip_r38c18', _guard_key7_blanks_the_strip_pips__Pip_r38c18, _effect_key7_blanks_the_strip_pips__Pip_r38c18, ['Pip_r38c18']),
    ('key7_blanks_the_strip_pips__Pip_r38c19', _guard_key7_blanks_the_strip_pips__Pip_r38c19, _effect_key7_blanks_the_strip_pips__Pip_r38c19, ['Pip_r38c19']),
    ('key7_blanks_the_strip_pips__Pip_r38c21', _guard_key7_blanks_the_strip_pips__Pip_r38c21, _effect_key7_blanks_the_strip_pips__Pip_r38c21, ['Pip_r38c21']),
    ('key7_blanks_the_strip_pips__Pip_r38c22', _guard_key7_blanks_the_strip_pips__Pip_r38c22, _effect_key7_blanks_the_strip_pips__Pip_r38c22, ['Pip_r38c22']),
    ('key7_blanks_the_strip_pips__Pip_r39c17', _guard_key7_blanks_the_strip_pips__Pip_r39c17, _effect_key7_blanks_the_strip_pips__Pip_r39c17, ['Pip_r39c17']),
    ('key7_blanks_the_strip_pips__Pip_r39c18', _guard_key7_blanks_the_strip_pips__Pip_r39c18, _effect_key7_blanks_the_strip_pips__Pip_r39c18, ['Pip_r39c18']),
    ('key7_blanks_the_strip_pips__Pip_r39c20', _guard_key7_blanks_the_strip_pips__Pip_r39c20, _effect_key7_blanks_the_strip_pips__Pip_r39c20, ['Pip_r39c20']),
    ('key7_blanks_the_strip_pips__Pip_r39c21', _guard_key7_blanks_the_strip_pips__Pip_r39c21, _effect_key7_blanks_the_strip_pips__Pip_r39c21, ['Pip_r39c21']),
    ('key7_blanks_the_strip_studs__Stud_r32c13', _guard_key7_blanks_the_strip_studs__Stud_r32c13, _effect_key7_blanks_the_strip_studs__Stud_r32c13, ['Stud_r32c13']),
    ('key7_blanks_the_strip_studs__Stud_r32c14', _guard_key7_blanks_the_strip_studs__Stud_r32c14, _effect_key7_blanks_the_strip_studs__Stud_r32c14, ['Stud_r32c14']),
    ('key7_blanks_the_strip_studs__Stud_r33c13', _guard_key7_blanks_the_strip_studs__Stud_r33c13, _effect_key7_blanks_the_strip_studs__Stud_r33c13, ['Stud_r33c13']),
    ('key7_blanks_the_strip_studs__Stud_r33c14', _guard_key7_blanks_the_strip_studs__Stud_r33c14, _effect_key7_blanks_the_strip_studs__Stud_r33c14, ['Stud_r33c14']),
    ('key7_blanks_the_strip_studs__Stud_r38c17', _guard_key7_blanks_the_strip_studs__Stud_r38c17, _effect_key7_blanks_the_strip_studs__Stud_r38c17, ['Stud_r38c17']),
    ('key7_blanks_the_strip_studs__Stud_r38c20', _guard_key7_blanks_the_strip_studs__Stud_r38c20, _effect_key7_blanks_the_strip_studs__Stud_r38c20, ['Stud_r38c20']),
    ('key7_blanks_the_strip_studs__Stud_r39c16', _guard_key7_blanks_the_strip_studs__Stud_r39c16, _effect_key7_blanks_the_strip_studs__Stud_r39c16, ['Stud_r39c16']),
    ('key7_blanks_the_strip_studs__Stud_r39c19', _guard_key7_blanks_the_strip_studs__Stud_r39c19, _effect_key7_blanks_the_strip_studs__Stud_r39c19, ['Stud_r39c19']),
    ('key7_blanks_the_strip_studs__Stud_r39c22', _guard_key7_blanks_the_strip_studs__Stud_r39c22, _effect_key7_blanks_the_strip_studs__Stud_r39c22, ['Stud_r39c22']),
    ('key7_blanks_the_strip_studs__Stud_r53c59', _guard_key7_blanks_the_strip_studs__Stud_r53c59, _effect_key7_blanks_the_strip_studs__Stud_r53c59, ['Stud_r53c59']),
    ('key7_blanks_the_strip_studs__Stud_r53c60', _guard_key7_blanks_the_strip_studs__Stud_r53c60, _effect_key7_blanks_the_strip_studs__Stud_r53c60, ['Stud_r53c60']),
    ('key7_blanks_the_strip_studs__Stud_r53c61', _guard_key7_blanks_the_strip_studs__Stud_r53c61, _effect_key7_blanks_the_strip_studs__Stud_r53c61, ['Stud_r53c61']),
    ('key7_blanks_the_strip_studs__Stud_r53c62', _guard_key7_blanks_the_strip_studs__Stud_r53c62, _effect_key7_blanks_the_strip_studs__Stud_r53c62, ['Stud_r53c62']),
    ('key7_blanks_the_strip_studs__Stud_r53c63', _guard_key7_blanks_the_strip_studs__Stud_r53c63, _effect_key7_blanks_the_strip_studs__Stud_r53c63, ['Stud_r53c63']),
    ('key4_restores_the_strip_pips__Pip_r38c16', _guard_key4_restores_the_strip_pips__Pip_r38c16, _effect_key4_restores_the_strip_pips__Pip_r38c16, ['Pip_r38c16']),
    ('key4_restores_the_strip_pips__Pip_r38c18', _guard_key4_restores_the_strip_pips__Pip_r38c18, _effect_key4_restores_the_strip_pips__Pip_r38c18, ['Pip_r38c18']),
    ('key4_restores_the_strip_pips__Pip_r38c19', _guard_key4_restores_the_strip_pips__Pip_r38c19, _effect_key4_restores_the_strip_pips__Pip_r38c19, ['Pip_r38c19']),
    ('key4_restores_the_strip_pips__Pip_r38c21', _guard_key4_restores_the_strip_pips__Pip_r38c21, _effect_key4_restores_the_strip_pips__Pip_r38c21, ['Pip_r38c21']),
    ('key4_restores_the_strip_pips__Pip_r38c22', _guard_key4_restores_the_strip_pips__Pip_r38c22, _effect_key4_restores_the_strip_pips__Pip_r38c22, ['Pip_r38c22']),
    ('key4_restores_the_strip_pips__Pip_r39c17', _guard_key4_restores_the_strip_pips__Pip_r39c17, _effect_key4_restores_the_strip_pips__Pip_r39c17, ['Pip_r39c17']),
    ('key4_restores_the_strip_pips__Pip_r39c18', _guard_key4_restores_the_strip_pips__Pip_r39c18, _effect_key4_restores_the_strip_pips__Pip_r39c18, ['Pip_r39c18']),
    ('key4_restores_the_strip_pips__Pip_r39c20', _guard_key4_restores_the_strip_pips__Pip_r39c20, _effect_key4_restores_the_strip_pips__Pip_r39c20, ['Pip_r39c20']),
    ('key4_restores_the_strip_pips__Pip_r39c21', _guard_key4_restores_the_strip_pips__Pip_r39c21, _effect_key4_restores_the_strip_pips__Pip_r39c21, ['Pip_r39c21']),
    ('key4_restores_the_strip_studs__Stud_r32c13', _guard_key4_restores_the_strip_studs__Stud_r32c13, _effect_key4_restores_the_strip_studs__Stud_r32c13, ['Stud_r32c13']),
    ('key4_restores_the_strip_studs__Stud_r32c14', _guard_key4_restores_the_strip_studs__Stud_r32c14, _effect_key4_restores_the_strip_studs__Stud_r32c14, ['Stud_r32c14']),
    ('key4_restores_the_strip_studs__Stud_r33c13', _guard_key4_restores_the_strip_studs__Stud_r33c13, _effect_key4_restores_the_strip_studs__Stud_r33c13, ['Stud_r33c13']),
    ('key4_restores_the_strip_studs__Stud_r33c14', _guard_key4_restores_the_strip_studs__Stud_r33c14, _effect_key4_restores_the_strip_studs__Stud_r33c14, ['Stud_r33c14']),
    ('key4_restores_the_strip_studs__Stud_r38c17', _guard_key4_restores_the_strip_studs__Stud_r38c17, _effect_key4_restores_the_strip_studs__Stud_r38c17, ['Stud_r38c17']),
    ('key4_restores_the_strip_studs__Stud_r38c20', _guard_key4_restores_the_strip_studs__Stud_r38c20, _effect_key4_restores_the_strip_studs__Stud_r38c20, ['Stud_r38c20']),
    ('key4_restores_the_strip_studs__Stud_r39c16', _guard_key4_restores_the_strip_studs__Stud_r39c16, _effect_key4_restores_the_strip_studs__Stud_r39c16, ['Stud_r39c16']),
    ('key4_restores_the_strip_studs__Stud_r39c19', _guard_key4_restores_the_strip_studs__Stud_r39c19, _effect_key4_restores_the_strip_studs__Stud_r39c19, ['Stud_r39c19']),
    ('key4_restores_the_strip_studs__Stud_r39c22', _guard_key4_restores_the_strip_studs__Stud_r39c22, _effect_key4_restores_the_strip_studs__Stud_r39c22, ['Stud_r39c22']),
    ('key4_restores_the_strip_studs__Stud_r53c59', _guard_key4_restores_the_strip_studs__Stud_r53c59, _effect_key4_restores_the_strip_studs__Stud_r53c59, ['Stud_r53c59']),
    ('key4_restores_the_strip_studs__Stud_r53c60', _guard_key4_restores_the_strip_studs__Stud_r53c60, _effect_key4_restores_the_strip_studs__Stud_r53c60, ['Stud_r53c60']),
    ('key4_restores_the_strip_studs__Stud_r53c61', _guard_key4_restores_the_strip_studs__Stud_r53c61, _effect_key4_restores_the_strip_studs__Stud_r53c61, ['Stud_r53c61']),
    ('key4_restores_the_strip_studs__Stud_r53c62', _guard_key4_restores_the_strip_studs__Stud_r53c62, _effect_key4_restores_the_strip_studs__Stud_r53c62, ['Stud_r53c62']),
    ('key4_restores_the_strip_studs__Stud_r53c63', _guard_key4_restores_the_strip_studs__Stud_r53c63, _effect_key4_restores_the_strip_studs__Stud_r53c63, ['Stud_r53c63']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r32c13', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r32c13, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r32c13, ['Stud_r32c13']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r32c14', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r32c14, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r32c14, ['Stud_r32c14']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r33c13', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r33c13, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r33c13, ['Stud_r33c13']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r33c14', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r33c14, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r33c14, ['Stud_r33c14']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r38c17', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r38c17, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r38c17, ['Stud_r38c17']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r38c20', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r38c20, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r38c20, ['Stud_r38c20']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r39c16', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c16, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c16, ['Stud_r39c16']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r39c19', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c19, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c19, ['Stud_r39c19']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r39c22', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r39c22, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r39c22, ['Stud_r39c22']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r53c59', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c59, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c59, ['Stud_r53c59']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r53c60', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c60, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c60, ['Stud_r53c60']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r53c61', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c61, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c61, ['Stud_r53c61']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r53c62', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c62, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c62, ['Stud_r53c62']),
    ('key4_seeds_the_meter_at_the_right_edge__Stud_r53c63', _guard_key4_seeds_the_meter_at_the_right_edge__Stud_r53c63, _effect_key4_seeds_the_meter_at_the_right_edge__Stud_r53c63, ['Stud_r53c63']),
    ('key3_marches_the_meter_leftward__Stud_r32c13', _guard_key3_marches_the_meter_leftward__Stud_r32c13, _effect_key3_marches_the_meter_leftward__Stud_r32c13, ['Stud_r32c13']),
    ('key3_marches_the_meter_leftward__Stud_r32c14', _guard_key3_marches_the_meter_leftward__Stud_r32c14, _effect_key3_marches_the_meter_leftward__Stud_r32c14, ['Stud_r32c14']),
    ('key3_marches_the_meter_leftward__Stud_r33c13', _guard_key3_marches_the_meter_leftward__Stud_r33c13, _effect_key3_marches_the_meter_leftward__Stud_r33c13, ['Stud_r33c13']),
    ('key3_marches_the_meter_leftward__Stud_r33c14', _guard_key3_marches_the_meter_leftward__Stud_r33c14, _effect_key3_marches_the_meter_leftward__Stud_r33c14, ['Stud_r33c14']),
    ('key3_marches_the_meter_leftward__Stud_r38c17', _guard_key3_marches_the_meter_leftward__Stud_r38c17, _effect_key3_marches_the_meter_leftward__Stud_r38c17, ['Stud_r38c17']),
    ('key3_marches_the_meter_leftward__Stud_r38c20', _guard_key3_marches_the_meter_leftward__Stud_r38c20, _effect_key3_marches_the_meter_leftward__Stud_r38c20, ['Stud_r38c20']),
    ('key3_marches_the_meter_leftward__Stud_r39c16', _guard_key3_marches_the_meter_leftward__Stud_r39c16, _effect_key3_marches_the_meter_leftward__Stud_r39c16, ['Stud_r39c16']),
    ('key3_marches_the_meter_leftward__Stud_r39c19', _guard_key3_marches_the_meter_leftward__Stud_r39c19, _effect_key3_marches_the_meter_leftward__Stud_r39c19, ['Stud_r39c19']),
    ('key3_marches_the_meter_leftward__Stud_r39c22', _guard_key3_marches_the_meter_leftward__Stud_r39c22, _effect_key3_marches_the_meter_leftward__Stud_r39c22, ['Stud_r39c22']),
    ('key3_marches_the_meter_leftward__Stud_r53c59', _guard_key3_marches_the_meter_leftward__Stud_r53c59, _effect_key3_marches_the_meter_leftward__Stud_r53c59, ['Stud_r53c59']),
    ('key3_marches_the_meter_leftward__Stud_r53c60', _guard_key3_marches_the_meter_leftward__Stud_r53c60, _effect_key3_marches_the_meter_leftward__Stud_r53c60, ['Stud_r53c60']),
    ('key3_marches_the_meter_leftward__Stud_r53c61', _guard_key3_marches_the_meter_leftward__Stud_r53c61, _effect_key3_marches_the_meter_leftward__Stud_r53c61, ['Stud_r53c61']),
    ('key3_marches_the_meter_leftward__Stud_r53c62', _guard_key3_marches_the_meter_leftward__Stud_r53c62, _effect_key3_marches_the_meter_leftward__Stud_r53c62, ['Stud_r53c62']),
    ('key3_marches_the_meter_leftward__Stud_r53c63', _guard_key3_marches_the_meter_leftward__Stud_r53c63, _effect_key3_marches_the_meter_leftward__Stud_r53c63, ['Stud_r53c63']),
]


class AmbiguousTransition(Exception):
    """Two rules claimed one object: `conflict exclusive` is violated."""


def step(state, action):
    """One action, one successor, per the manual's `semantics:`.

    frame persist        -- an object no firing rule touches is
                            unchanged, which is what makes this total.
    conflict exclusive   -- two rules claiming one object is an error,
                            not a precedence question.
    cascade single_frame -- every guard reads `state`, never the
                            partially updated result.
    """
    result = state.copy()
    claimed = {}
    for name, guard, effect, objs in RULES:
        if not guard(state, action):
            continue
        for obj in objs:
            if obj in claimed:
                raise AmbiguousTransition(
                    '%s and %s both fire on %s for %s'
                    % (claimed[obj], name, action, obj))
            claimed[obj] = name
        effect(result)
    return result


def fired(state, action):
    return [n for n, g, _e, _o in RULES if g(state, action)]


def is_goal(state):
    return False


def simulate(initial, actions):
    states = [initial]
    current = initial
    for action in actions:
        current = step(current, action)
        states.append(current)
    return states


def initial_state():
    return State(
        Casing_r36c11_pos=(36, 11),
        Casing_r36c11_color=6,
        Casing_r36c12_pos=(36, 12),
        Casing_r36c12_color=6,
        Casing_r36c13_pos=(36, 13),
        Casing_r36c13_color=6,
        Casing_r36c14_pos=(36, 14),
        Casing_r36c14_color=6,
        Casing_r36c15_pos=(36, 15),
        Casing_r36c15_color=6,
        Casing_r36c16_pos=(36, 16),
        Casing_r36c16_color=6,
        Casing_r37c11_pos=(37, 11),
        Casing_r37c11_color=6,
        Casing_r37c16_pos=(37, 16),
        Casing_r37c16_color=6,
        Casing_r38c11_pos=(38, 11),
        Casing_r38c11_color=6,
        Casing_r38c13_pos=(38, 13),
        Casing_r38c13_color=6,
        Casing_r38c14_pos=(38, 14),
        Casing_r38c14_color=6,
        Casing_r39c11_pos=(39, 11),
        Casing_r39c11_color=6,
        Casing_r39c13_pos=(39, 13),
        Casing_r39c13_color=6,
        Casing_r39c14_pos=(39, 14),
        Casing_r39c14_color=6,
        Casing_r40c11_pos=(40, 11),
        Casing_r40c11_color=6,
        Casing_r40c16_pos=(40, 16),
        Casing_r40c16_color=6,
        Casing_r41c11_pos=(41, 11),
        Casing_r41c11_color=6,
        Casing_r41c12_pos=(41, 12),
        Casing_r41c12_color=6,
        Casing_r41c13_pos=(41, 13),
        Casing_r41c13_color=6,
        Casing_r41c14_pos=(41, 14),
        Casing_r41c14_color=6,
        Casing_r41c15_pos=(41, 15),
        Casing_r41c15_color=6,
        Casing_r41c16_pos=(41, 16),
        Casing_r41c16_color=6,
        Cavity_r37c12_pos=(37, 12),
        Cavity_r37c12_color=0,
        Cavity_r37c13_pos=(37, 13),
        Cavity_r37c13_color=0,
        Cavity_r37c14_pos=(37, 14),
        Cavity_r37c14_color=0,
        Cavity_r37c15_pos=(37, 15),
        Cavity_r37c15_color=0,
        Cavity_r38c12_pos=(38, 12),
        Cavity_r38c12_color=0,
        Cavity_r38c15_pos=(38, 15),
        Cavity_r38c15_color=0,
        Cavity_r39c12_pos=(39, 12),
        Cavity_r39c12_color=0,
        Cavity_r39c15_pos=(39, 15),
        Cavity_r39c15_color=0,
        Cavity_r40c12_pos=(40, 12),
        Cavity_r40c12_color=0,
        Cavity_r40c13_pos=(40, 13),
        Cavity_r40c13_color=0,
        Cavity_r40c14_pos=(40, 14),
        Cavity_r40c14_color=0,
        Cavity_r40c15_pos=(40, 15),
        Cavity_r40c15_color=0,
        Rail_r30c13_pos=(30, 13),
        Rail_r30c13_color=3,
        Rail_r30c14_pos=(30, 14),
        Rail_r30c14_color=3,
        Rail_r31c13_pos=(31, 13),
        Rail_r31c13_color=3,
        Rail_r31c14_pos=(31, 14),
        Rail_r31c14_color=3,
        Rail_r34c13_pos=(34, 13),
        Rail_r34c13_color=3,
        Rail_r34c14_pos=(34, 14),
        Rail_r34c14_color=3,
        Rail_r35c13_pos=(35, 13),
        Rail_r35c13_color=3,
        Rail_r35c14_pos=(35, 14),
        Rail_r35c14_color=3,
        Pip_r38c16_pos=(38, 16),
        Pip_r38c16_color=1,
        Pip_r38c18_pos=(38, 18),
        Pip_r38c18_color=1,
        Pip_r38c19_pos=(38, 19),
        Pip_r38c19_color=1,
        Pip_r38c21_pos=(38, 21),
        Pip_r38c21_color=1,
        Pip_r38c22_pos=(38, 22),
        Pip_r38c22_color=1,
        Pip_r39c17_pos=(39, 17),
        Pip_r39c17_color=1,
        Pip_r39c18_pos=(39, 18),
        Pip_r39c18_color=1,
        Pip_r39c20_pos=(39, 20),
        Pip_r39c20_color=1,
        Pip_r39c21_pos=(39, 21),
        Pip_r39c21_color=1,
        Stud_r32c13_pos=(32, 13),
        Stud_r32c13_color=2,
        Stud_r32c14_pos=(32, 14),
        Stud_r32c14_color=2,
        Stud_r33c13_pos=(33, 13),
        Stud_r33c13_color=2,
        Stud_r33c14_pos=(33, 14),
        Stud_r33c14_color=2,
        Stud_r38c17_pos=(38, 17),
        Stud_r38c17_color=2,
        Stud_r38c20_pos=(38, 20),
        Stud_r38c20_color=2,
        Stud_r39c16_pos=(39, 16),
        Stud_r39c16_color=2,
        Stud_r39c19_pos=(39, 19),
        Stud_r39c19_color=2,
        Stud_r39c22_pos=(39, 22),
        Stud_r39c22_color=2,
        Stud_r53c59_pos=(53, 59),
        Stud_r53c59_color=2,
        Stud_r53c60_pos=(53, 60),
        Stud_r53c60_color=2,
        Stud_r53c61_pos=(53, 61),
        Stud_r53c61_color=2,
        Stud_r53c62_pos=(53, 62),
        Stud_r53c62_color=2,
        Stud_r53c63_pos=(53, 63),
        Stud_r53c63_color=2,
        Erased_r32c17_pos=(32, 17),
        Erased_r32c17_color=4,
        Erased_r32c18_pos=(32, 18),
        Erased_r32c18_color=4,
        Erased_r32c19_pos=(32, 19),
        Erased_r32c19_color=4,
        Erased_r32c20_pos=(32, 20),
        Erased_r32c20_color=4,
        Erased_r32c21_pos=(32, 21),
        Erased_r32c21_color=4,
        Erased_r32c22_pos=(32, 22),
        Erased_r32c22_color=4,
        Erased_r33c17_pos=(33, 17),
        Erased_r33c17_color=4,
        Erased_r33c18_pos=(33, 18),
        Erased_r33c18_color=4,
        Erased_r33c19_pos=(33, 19),
        Erased_r33c19_color=4,
        Erased_r33c20_pos=(33, 20),
        Erased_r33c20_color=4,
        Erased_r33c21_pos=(33, 21),
        Erased_r33c21_color=4,
        Erased_r33c22_pos=(33, 22),
        Erased_r33c22_color=4,
    )
