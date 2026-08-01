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
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 5],
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
    Ink1_r38c16_pos: object = (38, 16)
    Ink1_r38c16_color: object = 1
    Ink1_r38c18_pos: object = (38, 18)
    Ink1_r38c18_color: object = 1
    Ink1_r38c19_pos: object = (38, 19)
    Ink1_r38c19_color: object = 1
    Ink1_r38c21_pos: object = (38, 21)
    Ink1_r38c21_color: object = 1
    Ink1_r38c22_pos: object = (38, 22)
    Ink1_r38c22_color: object = 1
    Ink1_r39c17_pos: object = (39, 17)
    Ink1_r39c17_color: object = 1
    Ink1_r39c18_pos: object = (39, 18)
    Ink1_r39c18_color: object = 1
    Ink1_r39c20_pos: object = (39, 20)
    Ink1_r39c20_color: object = 1
    Ink1_r39c21_pos: object = (39, 21)
    Ink1_r39c21_color: object = 1
    Ink2_r32c13_pos: object = (32, 13)
    Ink2_r32c13_color: object = 2
    Ink2_r32c14_pos: object = (32, 14)
    Ink2_r32c14_color: object = 2
    Ink2_r33c13_pos: object = (33, 13)
    Ink2_r33c13_color: object = 2
    Ink2_r33c14_pos: object = (33, 14)
    Ink2_r33c14_color: object = 2
    Ink2_r38c17_pos: object = (38, 17)
    Ink2_r38c17_color: object = 2
    Ink2_r38c20_pos: object = (38, 20)
    Ink2_r38c20_color: object = 2
    Ink2_r39c16_pos: object = (39, 16)
    Ink2_r39c16_color: object = 2
    Ink2_r39c19_pos: object = (39, 19)
    Ink2_r39c19_color: object = 2
    Ink2_r39c22_pos: object = (39, 22)
    Ink2_r39c22_color: object = 2
    Ink2_r53c63_pos: object = (53, 63)
    Ink2_r53c63_color: object = 2
    Ink3_r30c13_pos: object = (30, 13)
    Ink3_r30c13_color: object = 3
    Ink3_r30c14_pos: object = (30, 14)
    Ink3_r30c14_color: object = 3
    Ink3_r31c13_pos: object = (31, 13)
    Ink3_r31c13_color: object = 3
    Ink3_r31c14_pos: object = (31, 14)
    Ink3_r31c14_color: object = 3
    Ink3_r34c13_pos: object = (34, 13)
    Ink3_r34c13_color: object = 3
    Ink3_r34c14_pos: object = (34, 14)
    Ink3_r34c14_color: object = 3
    Ink3_r35c13_pos: object = (35, 13)
    Ink3_r35c13_color: object = 3
    Ink3_r35c14_pos: object = (35, 14)
    Ink3_r35c14_color: object = 3
    Dark_r37c12_pos: object = (37, 12)
    Dark_r37c12_color: object = 0
    Dark_r37c13_pos: object = (37, 13)
    Dark_r37c13_color: object = 0
    Dark_r37c14_pos: object = (37, 14)
    Dark_r37c14_color: object = 0
    Dark_r37c15_pos: object = (37, 15)
    Dark_r37c15_color: object = 0
    Dark_r38c12_pos: object = (38, 12)
    Dark_r38c12_color: object = 0
    Dark_r38c15_pos: object = (38, 15)
    Dark_r38c15_color: object = 0
    Dark_r39c12_pos: object = (39, 12)
    Dark_r39c12_color: object = 0
    Dark_r39c15_pos: object = (39, 15)
    Dark_r39c15_color: object = 0
    Dark_r40c12_pos: object = (40, 12)
    Dark_r40c12_color: object = 0
    Dark_r40c13_pos: object = (40, 13)
    Dark_r40c13_color: object = 0
    Dark_r40c14_pos: object = (40, 14)
    Dark_r40c14_color: object = 0
    Dark_r40c15_pos: object = (40, 15)
    Dark_r40c15_color: object = 0
    Frame6_r36c11_pos: object = (36, 11)
    Frame6_r36c11_color: object = 6
    Frame6_r36c12_pos: object = (36, 12)
    Frame6_r36c12_color: object = 6
    Frame6_r36c13_pos: object = (36, 13)
    Frame6_r36c13_color: object = 6
    Frame6_r36c14_pos: object = (36, 14)
    Frame6_r36c14_color: object = 6
    Frame6_r36c15_pos: object = (36, 15)
    Frame6_r36c15_color: object = 6
    Frame6_r36c16_pos: object = (36, 16)
    Frame6_r36c16_color: object = 6
    Frame6_r37c11_pos: object = (37, 11)
    Frame6_r37c11_color: object = 6
    Frame6_r37c16_pos: object = (37, 16)
    Frame6_r37c16_color: object = 6
    Frame6_r38c11_pos: object = (38, 11)
    Frame6_r38c11_color: object = 6
    Frame6_r38c13_pos: object = (38, 13)
    Frame6_r38c13_color: object = 6
    Frame6_r38c14_pos: object = (38, 14)
    Frame6_r38c14_color: object = 6
    Frame6_r39c11_pos: object = (39, 11)
    Frame6_r39c11_color: object = 6
    Frame6_r39c13_pos: object = (39, 13)
    Frame6_r39c13_color: object = 6
    Frame6_r39c14_pos: object = (39, 14)
    Frame6_r39c14_color: object = 6
    Frame6_r40c11_pos: object = (40, 11)
    Frame6_r40c11_color: object = 6
    Frame6_r40c16_pos: object = (40, 16)
    Frame6_r40c16_color: object = 6
    Frame6_r41c11_pos: object = (41, 11)
    Frame6_r41c11_color: object = 6
    Frame6_r41c12_pos: object = (41, 12)
    Frame6_r41c12_color: object = 6
    Frame6_r41c13_pos: object = (41, 13)
    Frame6_r41c13_color: object = 6
    Frame6_r41c14_pos: object = (41, 14)
    Frame6_r41c14_color: object = 6
    Frame6_r41c15_pos: object = (41, 15)
    Frame6_r41c15_color: object = 6
    Frame6_r41c16_pos: object = (41, 16)
    Frame6_r41c16_color: object = 6
    Field_r32c17_pos: object = (32, 17)
    Field_r32c17_color: object = 4
    Field_r32c18_pos: object = (32, 18)
    Field_r32c18_color: object = 4
    Field_r32c19_pos: object = (32, 19)
    Field_r32c19_color: object = 4
    Field_r32c20_pos: object = (32, 20)
    Field_r32c20_color: object = 4
    Field_r32c21_pos: object = (32, 21)
    Field_r32c21_color: object = 4
    Field_r32c22_pos: object = (32, 22)
    Field_r32c22_color: object = 4
    Field_r33c17_pos: object = (33, 17)
    Field_r33c17_color: object = 4
    Field_r33c18_pos: object = (33, 18)
    Field_r33c18_color: object = 4
    Field_r33c19_pos: object = (33, 19)
    Field_r33c19_color: object = 4
    Field_r33c20_pos: object = (33, 20)
    Field_r33c20_color: object = 4
    Field_r33c21_pos: object = (33, 21)
    Field_r33c21_color: object = 4
    Field_r33c22_pos: object = (33, 22)
    Field_r33c22_color: object = 4
    Ground_r30c11_pos: object = (30, 11)
    Ground_r30c11_color: object = 5
    Ground_r30c12_pos: object = (30, 12)
    Ground_r30c12_color: object = 5
    Ground_r30c15_pos: object = (30, 15)
    Ground_r30c15_color: object = 5
    Ground_r30c16_pos: object = (30, 16)
    Ground_r30c16_color: object = 5
    Ground_r31c11_pos: object = (31, 11)
    Ground_r31c11_color: object = 5
    Ground_r31c12_pos: object = (31, 12)
    Ground_r31c12_color: object = 5
    Ground_r31c15_pos: object = (31, 15)
    Ground_r31c15_color: object = 5
    Ground_r31c16_pos: object = (31, 16)
    Ground_r31c16_color: object = 5
    Ground_r32c11_pos: object = (32, 11)
    Ground_r32c11_color: object = 5
    Ground_r32c12_pos: object = (32, 12)
    Ground_r32c12_color: object = 5
    Ground_r32c15_pos: object = (32, 15)
    Ground_r32c15_color: object = 5
    Ground_r32c16_pos: object = (32, 16)
    Ground_r32c16_color: object = 5
    Ground_r33c11_pos: object = (33, 11)
    Ground_r33c11_color: object = 5
    Ground_r33c12_pos: object = (33, 12)
    Ground_r33c12_color: object = 5
    Ground_r33c15_pos: object = (33, 15)
    Ground_r33c15_color: object = 5
    Ground_r33c16_pos: object = (33, 16)
    Ground_r33c16_color: object = 5
    Ground_r34c11_pos: object = (34, 11)
    Ground_r34c11_color: object = 5
    Ground_r34c12_pos: object = (34, 12)
    Ground_r34c12_color: object = 5
    Ground_r34c15_pos: object = (34, 15)
    Ground_r34c15_color: object = 5
    Ground_r34c16_pos: object = (34, 16)
    Ground_r34c16_color: object = 5
    Ground_r35c11_pos: object = (35, 11)
    Ground_r35c11_color: object = 5
    Ground_r35c12_pos: object = (35, 12)
    Ground_r35c12_color: object = 5
    Ground_r35c15_pos: object = (35, 15)
    Ground_r35c15_color: object = 5
    Ground_r35c16_pos: object = (35, 16)
    Ground_r35c16_color: object = 5

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Ink1_r38c16_pos, self.Ink1_r38c16_color, self.Ink1_r38c18_pos, self.Ink1_r38c18_color, self.Ink1_r38c19_pos, self.Ink1_r38c19_color, self.Ink1_r38c21_pos, self.Ink1_r38c21_color, self.Ink1_r38c22_pos, self.Ink1_r38c22_color, self.Ink1_r39c17_pos, self.Ink1_r39c17_color, self.Ink1_r39c18_pos, self.Ink1_r39c18_color, self.Ink1_r39c20_pos, self.Ink1_r39c20_color, self.Ink1_r39c21_pos, self.Ink1_r39c21_color, self.Ink2_r32c13_pos, self.Ink2_r32c13_color, self.Ink2_r32c14_pos, self.Ink2_r32c14_color, self.Ink2_r33c13_pos, self.Ink2_r33c13_color, self.Ink2_r33c14_pos, self.Ink2_r33c14_color, self.Ink2_r38c17_pos, self.Ink2_r38c17_color, self.Ink2_r38c20_pos, self.Ink2_r38c20_color, self.Ink2_r39c16_pos, self.Ink2_r39c16_color, self.Ink2_r39c19_pos, self.Ink2_r39c19_color, self.Ink2_r39c22_pos, self.Ink2_r39c22_color, self.Ink2_r53c63_pos, self.Ink2_r53c63_color, self.Ink3_r30c13_pos, self.Ink3_r30c13_color, self.Ink3_r30c14_pos, self.Ink3_r30c14_color, self.Ink3_r31c13_pos, self.Ink3_r31c13_color, self.Ink3_r31c14_pos, self.Ink3_r31c14_color, self.Ink3_r34c13_pos, self.Ink3_r34c13_color, self.Ink3_r34c14_pos, self.Ink3_r34c14_color, self.Ink3_r35c13_pos, self.Ink3_r35c13_color, self.Ink3_r35c14_pos, self.Ink3_r35c14_color, self.Dark_r37c12_pos, self.Dark_r37c12_color, self.Dark_r37c13_pos, self.Dark_r37c13_color, self.Dark_r37c14_pos, self.Dark_r37c14_color, self.Dark_r37c15_pos, self.Dark_r37c15_color, self.Dark_r38c12_pos, self.Dark_r38c12_color, self.Dark_r38c15_pos, self.Dark_r38c15_color, self.Dark_r39c12_pos, self.Dark_r39c12_color, self.Dark_r39c15_pos, self.Dark_r39c15_color, self.Dark_r40c12_pos, self.Dark_r40c12_color, self.Dark_r40c13_pos, self.Dark_r40c13_color, self.Dark_r40c14_pos, self.Dark_r40c14_color, self.Dark_r40c15_pos, self.Dark_r40c15_color, self.Frame6_r36c11_pos, self.Frame6_r36c11_color, self.Frame6_r36c12_pos, self.Frame6_r36c12_color, self.Frame6_r36c13_pos, self.Frame6_r36c13_color, self.Frame6_r36c14_pos, self.Frame6_r36c14_color, self.Frame6_r36c15_pos, self.Frame6_r36c15_color, self.Frame6_r36c16_pos, self.Frame6_r36c16_color, self.Frame6_r37c11_pos, self.Frame6_r37c11_color, self.Frame6_r37c16_pos, self.Frame6_r37c16_color, self.Frame6_r38c11_pos, self.Frame6_r38c11_color, self.Frame6_r38c13_pos, self.Frame6_r38c13_color, self.Frame6_r38c14_pos, self.Frame6_r38c14_color, self.Frame6_r39c11_pos, self.Frame6_r39c11_color, self.Frame6_r39c13_pos, self.Frame6_r39c13_color, self.Frame6_r39c14_pos, self.Frame6_r39c14_color, self.Frame6_r40c11_pos, self.Frame6_r40c11_color, self.Frame6_r40c16_pos, self.Frame6_r40c16_color, self.Frame6_r41c11_pos, self.Frame6_r41c11_color, self.Frame6_r41c12_pos, self.Frame6_r41c12_color, self.Frame6_r41c13_pos, self.Frame6_r41c13_color, self.Frame6_r41c14_pos, self.Frame6_r41c14_color, self.Frame6_r41c15_pos, self.Frame6_r41c15_color, self.Frame6_r41c16_pos, self.Frame6_r41c16_color, self.Field_r32c17_pos, self.Field_r32c17_color, self.Field_r32c18_pos, self.Field_r32c18_color, self.Field_r32c19_pos, self.Field_r32c19_color, self.Field_r32c20_pos, self.Field_r32c20_color, self.Field_r32c21_pos, self.Field_r32c21_color, self.Field_r32c22_pos, self.Field_r32c22_color, self.Field_r33c17_pos, self.Field_r33c17_color, self.Field_r33c18_pos, self.Field_r33c18_color, self.Field_r33c19_pos, self.Field_r33c19_color, self.Field_r33c20_pos, self.Field_r33c20_color, self.Field_r33c21_pos, self.Field_r33c21_color, self.Field_r33c22_pos, self.Field_r33c22_color, self.Ground_r30c11_pos, self.Ground_r30c11_color, self.Ground_r30c12_pos, self.Ground_r30c12_color, self.Ground_r30c15_pos, self.Ground_r30c15_color, self.Ground_r30c16_pos, self.Ground_r30c16_color, self.Ground_r31c11_pos, self.Ground_r31c11_color, self.Ground_r31c12_pos, self.Ground_r31c12_color, self.Ground_r31c15_pos, self.Ground_r31c15_color, self.Ground_r31c16_pos, self.Ground_r31c16_color, self.Ground_r32c11_pos, self.Ground_r32c11_color, self.Ground_r32c12_pos, self.Ground_r32c12_color, self.Ground_r32c15_pos, self.Ground_r32c15_color, self.Ground_r32c16_pos, self.Ground_r32c16_color, self.Ground_r33c11_pos, self.Ground_r33c11_color, self.Ground_r33c12_pos, self.Ground_r33c12_color, self.Ground_r33c15_pos, self.Ground_r33c15_color, self.Ground_r33c16_pos, self.Ground_r33c16_color, self.Ground_r34c11_pos, self.Ground_r34c11_color, self.Ground_r34c12_pos, self.Ground_r34c12_color, self.Ground_r34c15_pos, self.Ground_r34c15_color, self.Ground_r34c16_pos, self.Ground_r34c16_color, self.Ground_r35c11_pos, self.Ground_r35c11_color, self.Ground_r35c12_pos, self.Ground_r35c12_color, self.Ground_r35c15_pos, self.Ground_r35c15_color, self.Ground_r35c16_pos, self.Ground_r35c16_color,)


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
    if 'Ink1_r38c16' not in _exclude:
        r, c = state.Ink1_r38c16_pos
        grid[r][c] = state.Ink1_r38c16_color
    if 'Ink1_r38c18' not in _exclude:
        r, c = state.Ink1_r38c18_pos
        grid[r][c] = state.Ink1_r38c18_color
    if 'Ink1_r38c19' not in _exclude:
        r, c = state.Ink1_r38c19_pos
        grid[r][c] = state.Ink1_r38c19_color
    if 'Ink1_r38c21' not in _exclude:
        r, c = state.Ink1_r38c21_pos
        grid[r][c] = state.Ink1_r38c21_color
    if 'Ink1_r38c22' not in _exclude:
        r, c = state.Ink1_r38c22_pos
        grid[r][c] = state.Ink1_r38c22_color
    if 'Ink1_r39c17' not in _exclude:
        r, c = state.Ink1_r39c17_pos
        grid[r][c] = state.Ink1_r39c17_color
    if 'Ink1_r39c18' not in _exclude:
        r, c = state.Ink1_r39c18_pos
        grid[r][c] = state.Ink1_r39c18_color
    if 'Ink1_r39c20' not in _exclude:
        r, c = state.Ink1_r39c20_pos
        grid[r][c] = state.Ink1_r39c20_color
    if 'Ink1_r39c21' not in _exclude:
        r, c = state.Ink1_r39c21_pos
        grid[r][c] = state.Ink1_r39c21_color
    if 'Ink2_r32c13' not in _exclude:
        r, c = state.Ink2_r32c13_pos
        grid[r][c] = state.Ink2_r32c13_color
    if 'Ink2_r32c14' not in _exclude:
        r, c = state.Ink2_r32c14_pos
        grid[r][c] = state.Ink2_r32c14_color
    if 'Ink2_r33c13' not in _exclude:
        r, c = state.Ink2_r33c13_pos
        grid[r][c] = state.Ink2_r33c13_color
    if 'Ink2_r33c14' not in _exclude:
        r, c = state.Ink2_r33c14_pos
        grid[r][c] = state.Ink2_r33c14_color
    if 'Ink2_r38c17' not in _exclude:
        r, c = state.Ink2_r38c17_pos
        grid[r][c] = state.Ink2_r38c17_color
    if 'Ink2_r38c20' not in _exclude:
        r, c = state.Ink2_r38c20_pos
        grid[r][c] = state.Ink2_r38c20_color
    if 'Ink2_r39c16' not in _exclude:
        r, c = state.Ink2_r39c16_pos
        grid[r][c] = state.Ink2_r39c16_color
    if 'Ink2_r39c19' not in _exclude:
        r, c = state.Ink2_r39c19_pos
        grid[r][c] = state.Ink2_r39c19_color
    if 'Ink2_r39c22' not in _exclude:
        r, c = state.Ink2_r39c22_pos
        grid[r][c] = state.Ink2_r39c22_color
    if 'Ink2_r53c63' not in _exclude:
        r, c = state.Ink2_r53c63_pos
        grid[r][c] = state.Ink2_r53c63_color
    if 'Ink3_r30c13' not in _exclude:
        r, c = state.Ink3_r30c13_pos
        grid[r][c] = state.Ink3_r30c13_color
    if 'Ink3_r30c14' not in _exclude:
        r, c = state.Ink3_r30c14_pos
        grid[r][c] = state.Ink3_r30c14_color
    if 'Ink3_r31c13' not in _exclude:
        r, c = state.Ink3_r31c13_pos
        grid[r][c] = state.Ink3_r31c13_color
    if 'Ink3_r31c14' not in _exclude:
        r, c = state.Ink3_r31c14_pos
        grid[r][c] = state.Ink3_r31c14_color
    if 'Ink3_r34c13' not in _exclude:
        r, c = state.Ink3_r34c13_pos
        grid[r][c] = state.Ink3_r34c13_color
    if 'Ink3_r34c14' not in _exclude:
        r, c = state.Ink3_r34c14_pos
        grid[r][c] = state.Ink3_r34c14_color
    if 'Ink3_r35c13' not in _exclude:
        r, c = state.Ink3_r35c13_pos
        grid[r][c] = state.Ink3_r35c13_color
    if 'Ink3_r35c14' not in _exclude:
        r, c = state.Ink3_r35c14_pos
        grid[r][c] = state.Ink3_r35c14_color
    if 'Dark_r37c12' not in _exclude:
        r, c = state.Dark_r37c12_pos
        grid[r][c] = state.Dark_r37c12_color
    if 'Dark_r37c13' not in _exclude:
        r, c = state.Dark_r37c13_pos
        grid[r][c] = state.Dark_r37c13_color
    if 'Dark_r37c14' not in _exclude:
        r, c = state.Dark_r37c14_pos
        grid[r][c] = state.Dark_r37c14_color
    if 'Dark_r37c15' not in _exclude:
        r, c = state.Dark_r37c15_pos
        grid[r][c] = state.Dark_r37c15_color
    if 'Dark_r38c12' not in _exclude:
        r, c = state.Dark_r38c12_pos
        grid[r][c] = state.Dark_r38c12_color
    if 'Dark_r38c15' not in _exclude:
        r, c = state.Dark_r38c15_pos
        grid[r][c] = state.Dark_r38c15_color
    if 'Dark_r39c12' not in _exclude:
        r, c = state.Dark_r39c12_pos
        grid[r][c] = state.Dark_r39c12_color
    if 'Dark_r39c15' not in _exclude:
        r, c = state.Dark_r39c15_pos
        grid[r][c] = state.Dark_r39c15_color
    if 'Dark_r40c12' not in _exclude:
        r, c = state.Dark_r40c12_pos
        grid[r][c] = state.Dark_r40c12_color
    if 'Dark_r40c13' not in _exclude:
        r, c = state.Dark_r40c13_pos
        grid[r][c] = state.Dark_r40c13_color
    if 'Dark_r40c14' not in _exclude:
        r, c = state.Dark_r40c14_pos
        grid[r][c] = state.Dark_r40c14_color
    if 'Dark_r40c15' not in _exclude:
        r, c = state.Dark_r40c15_pos
        grid[r][c] = state.Dark_r40c15_color
    if 'Frame6_r36c11' not in _exclude:
        r, c = state.Frame6_r36c11_pos
        grid[r][c] = state.Frame6_r36c11_color
    if 'Frame6_r36c12' not in _exclude:
        r, c = state.Frame6_r36c12_pos
        grid[r][c] = state.Frame6_r36c12_color
    if 'Frame6_r36c13' not in _exclude:
        r, c = state.Frame6_r36c13_pos
        grid[r][c] = state.Frame6_r36c13_color
    if 'Frame6_r36c14' not in _exclude:
        r, c = state.Frame6_r36c14_pos
        grid[r][c] = state.Frame6_r36c14_color
    if 'Frame6_r36c15' not in _exclude:
        r, c = state.Frame6_r36c15_pos
        grid[r][c] = state.Frame6_r36c15_color
    if 'Frame6_r36c16' not in _exclude:
        r, c = state.Frame6_r36c16_pos
        grid[r][c] = state.Frame6_r36c16_color
    if 'Frame6_r37c11' not in _exclude:
        r, c = state.Frame6_r37c11_pos
        grid[r][c] = state.Frame6_r37c11_color
    if 'Frame6_r37c16' not in _exclude:
        r, c = state.Frame6_r37c16_pos
        grid[r][c] = state.Frame6_r37c16_color
    if 'Frame6_r38c11' not in _exclude:
        r, c = state.Frame6_r38c11_pos
        grid[r][c] = state.Frame6_r38c11_color
    if 'Frame6_r38c13' not in _exclude:
        r, c = state.Frame6_r38c13_pos
        grid[r][c] = state.Frame6_r38c13_color
    if 'Frame6_r38c14' not in _exclude:
        r, c = state.Frame6_r38c14_pos
        grid[r][c] = state.Frame6_r38c14_color
    if 'Frame6_r39c11' not in _exclude:
        r, c = state.Frame6_r39c11_pos
        grid[r][c] = state.Frame6_r39c11_color
    if 'Frame6_r39c13' not in _exclude:
        r, c = state.Frame6_r39c13_pos
        grid[r][c] = state.Frame6_r39c13_color
    if 'Frame6_r39c14' not in _exclude:
        r, c = state.Frame6_r39c14_pos
        grid[r][c] = state.Frame6_r39c14_color
    if 'Frame6_r40c11' not in _exclude:
        r, c = state.Frame6_r40c11_pos
        grid[r][c] = state.Frame6_r40c11_color
    if 'Frame6_r40c16' not in _exclude:
        r, c = state.Frame6_r40c16_pos
        grid[r][c] = state.Frame6_r40c16_color
    if 'Frame6_r41c11' not in _exclude:
        r, c = state.Frame6_r41c11_pos
        grid[r][c] = state.Frame6_r41c11_color
    if 'Frame6_r41c12' not in _exclude:
        r, c = state.Frame6_r41c12_pos
        grid[r][c] = state.Frame6_r41c12_color
    if 'Frame6_r41c13' not in _exclude:
        r, c = state.Frame6_r41c13_pos
        grid[r][c] = state.Frame6_r41c13_color
    if 'Frame6_r41c14' not in _exclude:
        r, c = state.Frame6_r41c14_pos
        grid[r][c] = state.Frame6_r41c14_color
    if 'Frame6_r41c15' not in _exclude:
        r, c = state.Frame6_r41c15_pos
        grid[r][c] = state.Frame6_r41c15_color
    if 'Frame6_r41c16' not in _exclude:
        r, c = state.Frame6_r41c16_pos
        grid[r][c] = state.Frame6_r41c16_color
    if 'Field_r32c17' not in _exclude:
        r, c = state.Field_r32c17_pos
        grid[r][c] = state.Field_r32c17_color
    if 'Field_r32c18' not in _exclude:
        r, c = state.Field_r32c18_pos
        grid[r][c] = state.Field_r32c18_color
    if 'Field_r32c19' not in _exclude:
        r, c = state.Field_r32c19_pos
        grid[r][c] = state.Field_r32c19_color
    if 'Field_r32c20' not in _exclude:
        r, c = state.Field_r32c20_pos
        grid[r][c] = state.Field_r32c20_color
    if 'Field_r32c21' not in _exclude:
        r, c = state.Field_r32c21_pos
        grid[r][c] = state.Field_r32c21_color
    if 'Field_r32c22' not in _exclude:
        r, c = state.Field_r32c22_pos
        grid[r][c] = state.Field_r32c22_color
    if 'Field_r33c17' not in _exclude:
        r, c = state.Field_r33c17_pos
        grid[r][c] = state.Field_r33c17_color
    if 'Field_r33c18' not in _exclude:
        r, c = state.Field_r33c18_pos
        grid[r][c] = state.Field_r33c18_color
    if 'Field_r33c19' not in _exclude:
        r, c = state.Field_r33c19_pos
        grid[r][c] = state.Field_r33c19_color
    if 'Field_r33c20' not in _exclude:
        r, c = state.Field_r33c20_pos
        grid[r][c] = state.Field_r33c20_color
    if 'Field_r33c21' not in _exclude:
        r, c = state.Field_r33c21_pos
        grid[r][c] = state.Field_r33c21_color
    if 'Field_r33c22' not in _exclude:
        r, c = state.Field_r33c22_pos
        grid[r][c] = state.Field_r33c22_color
    if 'Ground_r30c11' not in _exclude:
        r, c = state.Ground_r30c11_pos
        grid[r][c] = state.Ground_r30c11_color
    if 'Ground_r30c12' not in _exclude:
        r, c = state.Ground_r30c12_pos
        grid[r][c] = state.Ground_r30c12_color
    if 'Ground_r30c15' not in _exclude:
        r, c = state.Ground_r30c15_pos
        grid[r][c] = state.Ground_r30c15_color
    if 'Ground_r30c16' not in _exclude:
        r, c = state.Ground_r30c16_pos
        grid[r][c] = state.Ground_r30c16_color
    if 'Ground_r31c11' not in _exclude:
        r, c = state.Ground_r31c11_pos
        grid[r][c] = state.Ground_r31c11_color
    if 'Ground_r31c12' not in _exclude:
        r, c = state.Ground_r31c12_pos
        grid[r][c] = state.Ground_r31c12_color
    if 'Ground_r31c15' not in _exclude:
        r, c = state.Ground_r31c15_pos
        grid[r][c] = state.Ground_r31c15_color
    if 'Ground_r31c16' not in _exclude:
        r, c = state.Ground_r31c16_pos
        grid[r][c] = state.Ground_r31c16_color
    if 'Ground_r32c11' not in _exclude:
        r, c = state.Ground_r32c11_pos
        grid[r][c] = state.Ground_r32c11_color
    if 'Ground_r32c12' not in _exclude:
        r, c = state.Ground_r32c12_pos
        grid[r][c] = state.Ground_r32c12_color
    if 'Ground_r32c15' not in _exclude:
        r, c = state.Ground_r32c15_pos
        grid[r][c] = state.Ground_r32c15_color
    if 'Ground_r32c16' not in _exclude:
        r, c = state.Ground_r32c16_pos
        grid[r][c] = state.Ground_r32c16_color
    if 'Ground_r33c11' not in _exclude:
        r, c = state.Ground_r33c11_pos
        grid[r][c] = state.Ground_r33c11_color
    if 'Ground_r33c12' not in _exclude:
        r, c = state.Ground_r33c12_pos
        grid[r][c] = state.Ground_r33c12_color
    if 'Ground_r33c15' not in _exclude:
        r, c = state.Ground_r33c15_pos
        grid[r][c] = state.Ground_r33c15_color
    if 'Ground_r33c16' not in _exclude:
        r, c = state.Ground_r33c16_pos
        grid[r][c] = state.Ground_r33c16_color
    if 'Ground_r34c11' not in _exclude:
        r, c = state.Ground_r34c11_pos
        grid[r][c] = state.Ground_r34c11_color
    if 'Ground_r34c12' not in _exclude:
        r, c = state.Ground_r34c12_pos
        grid[r][c] = state.Ground_r34c12_color
    if 'Ground_r34c15' not in _exclude:
        r, c = state.Ground_r34c15_pos
        grid[r][c] = state.Ground_r34c15_color
    if 'Ground_r34c16' not in _exclude:
        r, c = state.Ground_r34c16_pos
        grid[r][c] = state.Ground_r34c16_color
    if 'Ground_r35c11' not in _exclude:
        r, c = state.Ground_r35c11_pos
        grid[r][c] = state.Ground_r35c11_color
    if 'Ground_r35c12' not in _exclude:
        r, c = state.Ground_r35c12_pos
        grid[r][c] = state.Ground_r35c12_color
    if 'Ground_r35c15' not in _exclude:
        r, c = state.Ground_r35c15_pos
        grid[r][c] = state.Ground_r35c15_color
    if 'Ground_r35c16' not in _exclude:
        r, c = state.Ground_r35c16_pos
        grid[r][c] = state.Ground_r35c16_color
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


def _guard_key3_strip_blanks_ink1__Ink1_r38c16(state, action):
    """key3_strip_blanks_ink1__Ink1_r38c16  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r38c18(state, action):
    """key3_strip_blanks_ink1__Ink1_r38c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r38c19(state, action):
    """key3_strip_blanks_ink1__Ink1_r38c19  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r38c21(state, action):
    """key3_strip_blanks_ink1__Ink1_r38c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r38c22(state, action):
    """key3_strip_blanks_ink1__Ink1_r38c22  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r39c17(state, action):
    """key3_strip_blanks_ink1__Ink1_r39c17  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r39c18(state, action):
    """key3_strip_blanks_ink1__Ink1_r39c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r39c20(state, action):
    """key3_strip_blanks_ink1__Ink1_r39c20  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 4


def _guard_key3_strip_blanks_ink1__Ink1_r39c21(state, action):
    """key3_strip_blanks_ink1__Ink1_r39c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink1__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r32c13(state, action):
    """key3_strip_blanks_ink2__Ink2_r32c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r32c14(state, action):
    """key3_strip_blanks_ink2__Ink2_r32c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r33c13(state, action):
    """key3_strip_blanks_ink2__Ink2_r33c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r33c14(state, action):
    """key3_strip_blanks_ink2__Ink2_r33c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r38c17(state, action):
    """key3_strip_blanks_ink2__Ink2_r38c17  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r38c20(state, action):
    """key3_strip_blanks_ink2__Ink2_r38c20  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r39c16(state, action):
    """key3_strip_blanks_ink2__Ink2_r39c16  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r39c19(state, action):
    """key3_strip_blanks_ink2__Ink2_r39c19  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r39c22(state, action):
    """key3_strip_blanks_ink2__Ink2_r39c22  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 4


def _guard_key3_strip_blanks_ink2__Ink2_r53c63(state, action):
    """key3_strip_blanks_ink2__Ink2_r53c63  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key3_strip_blanks_ink2__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r38c16(state, action):
    """key7_strip_blanks_ink1__Ink1_r38c16  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r38c18(state, action):
    """key7_strip_blanks_ink1__Ink1_r38c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r38c19(state, action):
    """key7_strip_blanks_ink1__Ink1_r38c19  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r38c21(state, action):
    """key7_strip_blanks_ink1__Ink1_r38c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r38c22(state, action):
    """key7_strip_blanks_ink1__Ink1_r38c22  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r39c17(state, action):
    """key7_strip_blanks_ink1__Ink1_r39c17  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r39c18(state, action):
    """key7_strip_blanks_ink1__Ink1_r39c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r39c20(state, action):
    """key7_strip_blanks_ink1__Ink1_r39c20  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 4


def _guard_key7_strip_blanks_ink1__Ink1_r39c21(state, action):
    """key7_strip_blanks_ink1__Ink1_r39c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink1__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r32c13(state, action):
    """key7_strip_blanks_ink2__Ink2_r32c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r32c14(state, action):
    """key7_strip_blanks_ink2__Ink2_r32c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r33c13(state, action):
    """key7_strip_blanks_ink2__Ink2_r33c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r33c14(state, action):
    """key7_strip_blanks_ink2__Ink2_r33c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r38c17(state, action):
    """key7_strip_blanks_ink2__Ink2_r38c17  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r38c20(state, action):
    """key7_strip_blanks_ink2__Ink2_r38c20  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r39c16(state, action):
    """key7_strip_blanks_ink2__Ink2_r39c16  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r39c19(state, action):
    """key7_strip_blanks_ink2__Ink2_r39c19  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r39c22(state, action):
    """key7_strip_blanks_ink2__Ink2_r39c22  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 4


def _guard_key7_strip_blanks_ink2__Ink2_r53c63(state, action):
    """key7_strip_blanks_ink2__Ink2_r53c63  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_key7_strip_blanks_ink2__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 4


def _guard_key4_strip_restores_ink1__Ink1_r38c16(state, action):
    """key4_strip_restores_ink1__Ink1_r38c16  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r38c18(state, action):
    """key4_strip_restores_ink1__Ink1_r38c18  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r38c19(state, action):
    """key4_strip_restores_ink1__Ink1_r38c19  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r38c21(state, action):
    """key4_strip_restores_ink1__Ink1_r38c21  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r38c22(state, action):
    """key4_strip_restores_ink1__Ink1_r38c22  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r39c17(state, action):
    """key4_strip_restores_ink1__Ink1_r39c17  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r39c18(state, action):
    """key4_strip_restores_ink1__Ink1_r39c18  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r39c20(state, action):
    """key4_strip_restores_ink1__Ink1_r39c20  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 1


def _guard_key4_strip_restores_ink1__Ink1_r39c21(state, action):
    """key4_strip_restores_ink1__Ink1_r39c21  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink1__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 1


def _guard_key4_strip_restores_ink2__Ink2_r32c13(state, action):
    """key4_strip_restores_ink2__Ink2_r32c13  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r32c14(state, action):
    """key4_strip_restores_ink2__Ink2_r32c14  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r33c13(state, action):
    """key4_strip_restores_ink2__Ink2_r33c13  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r33c14(state, action):
    """key4_strip_restores_ink2__Ink2_r33c14  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r38c17(state, action):
    """key4_strip_restores_ink2__Ink2_r38c17  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r38c20(state, action):
    """key4_strip_restores_ink2__Ink2_r38c20  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r39c16(state, action):
    """key4_strip_restores_ink2__Ink2_r39c16  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r39c19(state, action):
    """key4_strip_restores_ink2__Ink2_r39c19  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r39c22(state, action):
    """key4_strip_restores_ink2__Ink2_r39c22  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 2


def _guard_key4_strip_restores_ink2__Ink2_r53c63(state, action):
    """key4_strip_restores_ink2__Ink2_r53c63  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 4): return False
    return True


def _effect_key4_strip_restores_ink2__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 2


def _guard_key4_meter_burns_right_end__Ink2_r32c13(state, action):
    """key4_meter_burns_right_end__Ink2_r32c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r32c14(state, action):
    """key4_meter_burns_right_end__Ink2_r32c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r33c13(state, action):
    """key4_meter_burns_right_end__Ink2_r33c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r33c14(state, action):
    """key4_meter_burns_right_end__Ink2_r33c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r38c17(state, action):
    """key4_meter_burns_right_end__Ink2_r38c17  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r38c20(state, action):
    """key4_meter_burns_right_end__Ink2_r38c20  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r39c16(state, action):
    """key4_meter_burns_right_end__Ink2_r39c16  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r39c19(state, action):
    """key4_meter_burns_right_end__Ink2_r39c19  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r39c22(state, action):
    """key4_meter_burns_right_end__Ink2_r39c22  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 3


def _guard_key4_meter_burns_right_end__Ink2_r53c63(state, action):
    """key4_meter_burns_right_end__Ink2_r53c63  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    return True


def _effect_key4_meter_burns_right_end__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 3


RULES = [
    ('key3_strip_blanks_ink1__Ink1_r38c16', _guard_key3_strip_blanks_ink1__Ink1_r38c16, _effect_key3_strip_blanks_ink1__Ink1_r38c16, ['Ink1_r38c16']),
    ('key3_strip_blanks_ink1__Ink1_r38c18', _guard_key3_strip_blanks_ink1__Ink1_r38c18, _effect_key3_strip_blanks_ink1__Ink1_r38c18, ['Ink1_r38c18']),
    ('key3_strip_blanks_ink1__Ink1_r38c19', _guard_key3_strip_blanks_ink1__Ink1_r38c19, _effect_key3_strip_blanks_ink1__Ink1_r38c19, ['Ink1_r38c19']),
    ('key3_strip_blanks_ink1__Ink1_r38c21', _guard_key3_strip_blanks_ink1__Ink1_r38c21, _effect_key3_strip_blanks_ink1__Ink1_r38c21, ['Ink1_r38c21']),
    ('key3_strip_blanks_ink1__Ink1_r38c22', _guard_key3_strip_blanks_ink1__Ink1_r38c22, _effect_key3_strip_blanks_ink1__Ink1_r38c22, ['Ink1_r38c22']),
    ('key3_strip_blanks_ink1__Ink1_r39c17', _guard_key3_strip_blanks_ink1__Ink1_r39c17, _effect_key3_strip_blanks_ink1__Ink1_r39c17, ['Ink1_r39c17']),
    ('key3_strip_blanks_ink1__Ink1_r39c18', _guard_key3_strip_blanks_ink1__Ink1_r39c18, _effect_key3_strip_blanks_ink1__Ink1_r39c18, ['Ink1_r39c18']),
    ('key3_strip_blanks_ink1__Ink1_r39c20', _guard_key3_strip_blanks_ink1__Ink1_r39c20, _effect_key3_strip_blanks_ink1__Ink1_r39c20, ['Ink1_r39c20']),
    ('key3_strip_blanks_ink1__Ink1_r39c21', _guard_key3_strip_blanks_ink1__Ink1_r39c21, _effect_key3_strip_blanks_ink1__Ink1_r39c21, ['Ink1_r39c21']),
    ('key3_strip_blanks_ink2__Ink2_r32c13', _guard_key3_strip_blanks_ink2__Ink2_r32c13, _effect_key3_strip_blanks_ink2__Ink2_r32c13, ['Ink2_r32c13']),
    ('key3_strip_blanks_ink2__Ink2_r32c14', _guard_key3_strip_blanks_ink2__Ink2_r32c14, _effect_key3_strip_blanks_ink2__Ink2_r32c14, ['Ink2_r32c14']),
    ('key3_strip_blanks_ink2__Ink2_r33c13', _guard_key3_strip_blanks_ink2__Ink2_r33c13, _effect_key3_strip_blanks_ink2__Ink2_r33c13, ['Ink2_r33c13']),
    ('key3_strip_blanks_ink2__Ink2_r33c14', _guard_key3_strip_blanks_ink2__Ink2_r33c14, _effect_key3_strip_blanks_ink2__Ink2_r33c14, ['Ink2_r33c14']),
    ('key3_strip_blanks_ink2__Ink2_r38c17', _guard_key3_strip_blanks_ink2__Ink2_r38c17, _effect_key3_strip_blanks_ink2__Ink2_r38c17, ['Ink2_r38c17']),
    ('key3_strip_blanks_ink2__Ink2_r38c20', _guard_key3_strip_blanks_ink2__Ink2_r38c20, _effect_key3_strip_blanks_ink2__Ink2_r38c20, ['Ink2_r38c20']),
    ('key3_strip_blanks_ink2__Ink2_r39c16', _guard_key3_strip_blanks_ink2__Ink2_r39c16, _effect_key3_strip_blanks_ink2__Ink2_r39c16, ['Ink2_r39c16']),
    ('key3_strip_blanks_ink2__Ink2_r39c19', _guard_key3_strip_blanks_ink2__Ink2_r39c19, _effect_key3_strip_blanks_ink2__Ink2_r39c19, ['Ink2_r39c19']),
    ('key3_strip_blanks_ink2__Ink2_r39c22', _guard_key3_strip_blanks_ink2__Ink2_r39c22, _effect_key3_strip_blanks_ink2__Ink2_r39c22, ['Ink2_r39c22']),
    ('key3_strip_blanks_ink2__Ink2_r53c63', _guard_key3_strip_blanks_ink2__Ink2_r53c63, _effect_key3_strip_blanks_ink2__Ink2_r53c63, ['Ink2_r53c63']),
    ('key7_strip_blanks_ink1__Ink1_r38c16', _guard_key7_strip_blanks_ink1__Ink1_r38c16, _effect_key7_strip_blanks_ink1__Ink1_r38c16, ['Ink1_r38c16']),
    ('key7_strip_blanks_ink1__Ink1_r38c18', _guard_key7_strip_blanks_ink1__Ink1_r38c18, _effect_key7_strip_blanks_ink1__Ink1_r38c18, ['Ink1_r38c18']),
    ('key7_strip_blanks_ink1__Ink1_r38c19', _guard_key7_strip_blanks_ink1__Ink1_r38c19, _effect_key7_strip_blanks_ink1__Ink1_r38c19, ['Ink1_r38c19']),
    ('key7_strip_blanks_ink1__Ink1_r38c21', _guard_key7_strip_blanks_ink1__Ink1_r38c21, _effect_key7_strip_blanks_ink1__Ink1_r38c21, ['Ink1_r38c21']),
    ('key7_strip_blanks_ink1__Ink1_r38c22', _guard_key7_strip_blanks_ink1__Ink1_r38c22, _effect_key7_strip_blanks_ink1__Ink1_r38c22, ['Ink1_r38c22']),
    ('key7_strip_blanks_ink1__Ink1_r39c17', _guard_key7_strip_blanks_ink1__Ink1_r39c17, _effect_key7_strip_blanks_ink1__Ink1_r39c17, ['Ink1_r39c17']),
    ('key7_strip_blanks_ink1__Ink1_r39c18', _guard_key7_strip_blanks_ink1__Ink1_r39c18, _effect_key7_strip_blanks_ink1__Ink1_r39c18, ['Ink1_r39c18']),
    ('key7_strip_blanks_ink1__Ink1_r39c20', _guard_key7_strip_blanks_ink1__Ink1_r39c20, _effect_key7_strip_blanks_ink1__Ink1_r39c20, ['Ink1_r39c20']),
    ('key7_strip_blanks_ink1__Ink1_r39c21', _guard_key7_strip_blanks_ink1__Ink1_r39c21, _effect_key7_strip_blanks_ink1__Ink1_r39c21, ['Ink1_r39c21']),
    ('key7_strip_blanks_ink2__Ink2_r32c13', _guard_key7_strip_blanks_ink2__Ink2_r32c13, _effect_key7_strip_blanks_ink2__Ink2_r32c13, ['Ink2_r32c13']),
    ('key7_strip_blanks_ink2__Ink2_r32c14', _guard_key7_strip_blanks_ink2__Ink2_r32c14, _effect_key7_strip_blanks_ink2__Ink2_r32c14, ['Ink2_r32c14']),
    ('key7_strip_blanks_ink2__Ink2_r33c13', _guard_key7_strip_blanks_ink2__Ink2_r33c13, _effect_key7_strip_blanks_ink2__Ink2_r33c13, ['Ink2_r33c13']),
    ('key7_strip_blanks_ink2__Ink2_r33c14', _guard_key7_strip_blanks_ink2__Ink2_r33c14, _effect_key7_strip_blanks_ink2__Ink2_r33c14, ['Ink2_r33c14']),
    ('key7_strip_blanks_ink2__Ink2_r38c17', _guard_key7_strip_blanks_ink2__Ink2_r38c17, _effect_key7_strip_blanks_ink2__Ink2_r38c17, ['Ink2_r38c17']),
    ('key7_strip_blanks_ink2__Ink2_r38c20', _guard_key7_strip_blanks_ink2__Ink2_r38c20, _effect_key7_strip_blanks_ink2__Ink2_r38c20, ['Ink2_r38c20']),
    ('key7_strip_blanks_ink2__Ink2_r39c16', _guard_key7_strip_blanks_ink2__Ink2_r39c16, _effect_key7_strip_blanks_ink2__Ink2_r39c16, ['Ink2_r39c16']),
    ('key7_strip_blanks_ink2__Ink2_r39c19', _guard_key7_strip_blanks_ink2__Ink2_r39c19, _effect_key7_strip_blanks_ink2__Ink2_r39c19, ['Ink2_r39c19']),
    ('key7_strip_blanks_ink2__Ink2_r39c22', _guard_key7_strip_blanks_ink2__Ink2_r39c22, _effect_key7_strip_blanks_ink2__Ink2_r39c22, ['Ink2_r39c22']),
    ('key7_strip_blanks_ink2__Ink2_r53c63', _guard_key7_strip_blanks_ink2__Ink2_r53c63, _effect_key7_strip_blanks_ink2__Ink2_r53c63, ['Ink2_r53c63']),
    ('key4_strip_restores_ink1__Ink1_r38c16', _guard_key4_strip_restores_ink1__Ink1_r38c16, _effect_key4_strip_restores_ink1__Ink1_r38c16, ['Ink1_r38c16']),
    ('key4_strip_restores_ink1__Ink1_r38c18', _guard_key4_strip_restores_ink1__Ink1_r38c18, _effect_key4_strip_restores_ink1__Ink1_r38c18, ['Ink1_r38c18']),
    ('key4_strip_restores_ink1__Ink1_r38c19', _guard_key4_strip_restores_ink1__Ink1_r38c19, _effect_key4_strip_restores_ink1__Ink1_r38c19, ['Ink1_r38c19']),
    ('key4_strip_restores_ink1__Ink1_r38c21', _guard_key4_strip_restores_ink1__Ink1_r38c21, _effect_key4_strip_restores_ink1__Ink1_r38c21, ['Ink1_r38c21']),
    ('key4_strip_restores_ink1__Ink1_r38c22', _guard_key4_strip_restores_ink1__Ink1_r38c22, _effect_key4_strip_restores_ink1__Ink1_r38c22, ['Ink1_r38c22']),
    ('key4_strip_restores_ink1__Ink1_r39c17', _guard_key4_strip_restores_ink1__Ink1_r39c17, _effect_key4_strip_restores_ink1__Ink1_r39c17, ['Ink1_r39c17']),
    ('key4_strip_restores_ink1__Ink1_r39c18', _guard_key4_strip_restores_ink1__Ink1_r39c18, _effect_key4_strip_restores_ink1__Ink1_r39c18, ['Ink1_r39c18']),
    ('key4_strip_restores_ink1__Ink1_r39c20', _guard_key4_strip_restores_ink1__Ink1_r39c20, _effect_key4_strip_restores_ink1__Ink1_r39c20, ['Ink1_r39c20']),
    ('key4_strip_restores_ink1__Ink1_r39c21', _guard_key4_strip_restores_ink1__Ink1_r39c21, _effect_key4_strip_restores_ink1__Ink1_r39c21, ['Ink1_r39c21']),
    ('key4_strip_restores_ink2__Ink2_r32c13', _guard_key4_strip_restores_ink2__Ink2_r32c13, _effect_key4_strip_restores_ink2__Ink2_r32c13, ['Ink2_r32c13']),
    ('key4_strip_restores_ink2__Ink2_r32c14', _guard_key4_strip_restores_ink2__Ink2_r32c14, _effect_key4_strip_restores_ink2__Ink2_r32c14, ['Ink2_r32c14']),
    ('key4_strip_restores_ink2__Ink2_r33c13', _guard_key4_strip_restores_ink2__Ink2_r33c13, _effect_key4_strip_restores_ink2__Ink2_r33c13, ['Ink2_r33c13']),
    ('key4_strip_restores_ink2__Ink2_r33c14', _guard_key4_strip_restores_ink2__Ink2_r33c14, _effect_key4_strip_restores_ink2__Ink2_r33c14, ['Ink2_r33c14']),
    ('key4_strip_restores_ink2__Ink2_r38c17', _guard_key4_strip_restores_ink2__Ink2_r38c17, _effect_key4_strip_restores_ink2__Ink2_r38c17, ['Ink2_r38c17']),
    ('key4_strip_restores_ink2__Ink2_r38c20', _guard_key4_strip_restores_ink2__Ink2_r38c20, _effect_key4_strip_restores_ink2__Ink2_r38c20, ['Ink2_r38c20']),
    ('key4_strip_restores_ink2__Ink2_r39c16', _guard_key4_strip_restores_ink2__Ink2_r39c16, _effect_key4_strip_restores_ink2__Ink2_r39c16, ['Ink2_r39c16']),
    ('key4_strip_restores_ink2__Ink2_r39c19', _guard_key4_strip_restores_ink2__Ink2_r39c19, _effect_key4_strip_restores_ink2__Ink2_r39c19, ['Ink2_r39c19']),
    ('key4_strip_restores_ink2__Ink2_r39c22', _guard_key4_strip_restores_ink2__Ink2_r39c22, _effect_key4_strip_restores_ink2__Ink2_r39c22, ['Ink2_r39c22']),
    ('key4_strip_restores_ink2__Ink2_r53c63', _guard_key4_strip_restores_ink2__Ink2_r53c63, _effect_key4_strip_restores_ink2__Ink2_r53c63, ['Ink2_r53c63']),
    ('key4_meter_burns_right_end__Ink2_r32c13', _guard_key4_meter_burns_right_end__Ink2_r32c13, _effect_key4_meter_burns_right_end__Ink2_r32c13, ['Ink2_r32c13']),
    ('key4_meter_burns_right_end__Ink2_r32c14', _guard_key4_meter_burns_right_end__Ink2_r32c14, _effect_key4_meter_burns_right_end__Ink2_r32c14, ['Ink2_r32c14']),
    ('key4_meter_burns_right_end__Ink2_r33c13', _guard_key4_meter_burns_right_end__Ink2_r33c13, _effect_key4_meter_burns_right_end__Ink2_r33c13, ['Ink2_r33c13']),
    ('key4_meter_burns_right_end__Ink2_r33c14', _guard_key4_meter_burns_right_end__Ink2_r33c14, _effect_key4_meter_burns_right_end__Ink2_r33c14, ['Ink2_r33c14']),
    ('key4_meter_burns_right_end__Ink2_r38c17', _guard_key4_meter_burns_right_end__Ink2_r38c17, _effect_key4_meter_burns_right_end__Ink2_r38c17, ['Ink2_r38c17']),
    ('key4_meter_burns_right_end__Ink2_r38c20', _guard_key4_meter_burns_right_end__Ink2_r38c20, _effect_key4_meter_burns_right_end__Ink2_r38c20, ['Ink2_r38c20']),
    ('key4_meter_burns_right_end__Ink2_r39c16', _guard_key4_meter_burns_right_end__Ink2_r39c16, _effect_key4_meter_burns_right_end__Ink2_r39c16, ['Ink2_r39c16']),
    ('key4_meter_burns_right_end__Ink2_r39c19', _guard_key4_meter_burns_right_end__Ink2_r39c19, _effect_key4_meter_burns_right_end__Ink2_r39c19, ['Ink2_r39c19']),
    ('key4_meter_burns_right_end__Ink2_r39c22', _guard_key4_meter_burns_right_end__Ink2_r39c22, _effect_key4_meter_burns_right_end__Ink2_r39c22, ['Ink2_r39c22']),
    ('key4_meter_burns_right_end__Ink2_r53c63', _guard_key4_meter_burns_right_end__Ink2_r53c63, _effect_key4_meter_burns_right_end__Ink2_r53c63, ['Ink2_r53c63']),
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
        Ink1_r38c16_pos=(38, 16),
        Ink1_r38c16_color=1,
        Ink1_r38c18_pos=(38, 18),
        Ink1_r38c18_color=1,
        Ink1_r38c19_pos=(38, 19),
        Ink1_r38c19_color=1,
        Ink1_r38c21_pos=(38, 21),
        Ink1_r38c21_color=1,
        Ink1_r38c22_pos=(38, 22),
        Ink1_r38c22_color=1,
        Ink1_r39c17_pos=(39, 17),
        Ink1_r39c17_color=1,
        Ink1_r39c18_pos=(39, 18),
        Ink1_r39c18_color=1,
        Ink1_r39c20_pos=(39, 20),
        Ink1_r39c20_color=1,
        Ink1_r39c21_pos=(39, 21),
        Ink1_r39c21_color=1,
        Ink2_r32c13_pos=(32, 13),
        Ink2_r32c13_color=2,
        Ink2_r32c14_pos=(32, 14),
        Ink2_r32c14_color=2,
        Ink2_r33c13_pos=(33, 13),
        Ink2_r33c13_color=2,
        Ink2_r33c14_pos=(33, 14),
        Ink2_r33c14_color=2,
        Ink2_r38c17_pos=(38, 17),
        Ink2_r38c17_color=2,
        Ink2_r38c20_pos=(38, 20),
        Ink2_r38c20_color=2,
        Ink2_r39c16_pos=(39, 16),
        Ink2_r39c16_color=2,
        Ink2_r39c19_pos=(39, 19),
        Ink2_r39c19_color=2,
        Ink2_r39c22_pos=(39, 22),
        Ink2_r39c22_color=2,
        Ink2_r53c63_pos=(53, 63),
        Ink2_r53c63_color=2,
        Ink3_r30c13_pos=(30, 13),
        Ink3_r30c13_color=3,
        Ink3_r30c14_pos=(30, 14),
        Ink3_r30c14_color=3,
        Ink3_r31c13_pos=(31, 13),
        Ink3_r31c13_color=3,
        Ink3_r31c14_pos=(31, 14),
        Ink3_r31c14_color=3,
        Ink3_r34c13_pos=(34, 13),
        Ink3_r34c13_color=3,
        Ink3_r34c14_pos=(34, 14),
        Ink3_r34c14_color=3,
        Ink3_r35c13_pos=(35, 13),
        Ink3_r35c13_color=3,
        Ink3_r35c14_pos=(35, 14),
        Ink3_r35c14_color=3,
        Dark_r37c12_pos=(37, 12),
        Dark_r37c12_color=0,
        Dark_r37c13_pos=(37, 13),
        Dark_r37c13_color=0,
        Dark_r37c14_pos=(37, 14),
        Dark_r37c14_color=0,
        Dark_r37c15_pos=(37, 15),
        Dark_r37c15_color=0,
        Dark_r38c12_pos=(38, 12),
        Dark_r38c12_color=0,
        Dark_r38c15_pos=(38, 15),
        Dark_r38c15_color=0,
        Dark_r39c12_pos=(39, 12),
        Dark_r39c12_color=0,
        Dark_r39c15_pos=(39, 15),
        Dark_r39c15_color=0,
        Dark_r40c12_pos=(40, 12),
        Dark_r40c12_color=0,
        Dark_r40c13_pos=(40, 13),
        Dark_r40c13_color=0,
        Dark_r40c14_pos=(40, 14),
        Dark_r40c14_color=0,
        Dark_r40c15_pos=(40, 15),
        Dark_r40c15_color=0,
        Frame6_r36c11_pos=(36, 11),
        Frame6_r36c11_color=6,
        Frame6_r36c12_pos=(36, 12),
        Frame6_r36c12_color=6,
        Frame6_r36c13_pos=(36, 13),
        Frame6_r36c13_color=6,
        Frame6_r36c14_pos=(36, 14),
        Frame6_r36c14_color=6,
        Frame6_r36c15_pos=(36, 15),
        Frame6_r36c15_color=6,
        Frame6_r36c16_pos=(36, 16),
        Frame6_r36c16_color=6,
        Frame6_r37c11_pos=(37, 11),
        Frame6_r37c11_color=6,
        Frame6_r37c16_pos=(37, 16),
        Frame6_r37c16_color=6,
        Frame6_r38c11_pos=(38, 11),
        Frame6_r38c11_color=6,
        Frame6_r38c13_pos=(38, 13),
        Frame6_r38c13_color=6,
        Frame6_r38c14_pos=(38, 14),
        Frame6_r38c14_color=6,
        Frame6_r39c11_pos=(39, 11),
        Frame6_r39c11_color=6,
        Frame6_r39c13_pos=(39, 13),
        Frame6_r39c13_color=6,
        Frame6_r39c14_pos=(39, 14),
        Frame6_r39c14_color=6,
        Frame6_r40c11_pos=(40, 11),
        Frame6_r40c11_color=6,
        Frame6_r40c16_pos=(40, 16),
        Frame6_r40c16_color=6,
        Frame6_r41c11_pos=(41, 11),
        Frame6_r41c11_color=6,
        Frame6_r41c12_pos=(41, 12),
        Frame6_r41c12_color=6,
        Frame6_r41c13_pos=(41, 13),
        Frame6_r41c13_color=6,
        Frame6_r41c14_pos=(41, 14),
        Frame6_r41c14_color=6,
        Frame6_r41c15_pos=(41, 15),
        Frame6_r41c15_color=6,
        Frame6_r41c16_pos=(41, 16),
        Frame6_r41c16_color=6,
        Field_r32c17_pos=(32, 17),
        Field_r32c17_color=4,
        Field_r32c18_pos=(32, 18),
        Field_r32c18_color=4,
        Field_r32c19_pos=(32, 19),
        Field_r32c19_color=4,
        Field_r32c20_pos=(32, 20),
        Field_r32c20_color=4,
        Field_r32c21_pos=(32, 21),
        Field_r32c21_color=4,
        Field_r32c22_pos=(32, 22),
        Field_r32c22_color=4,
        Field_r33c17_pos=(33, 17),
        Field_r33c17_color=4,
        Field_r33c18_pos=(33, 18),
        Field_r33c18_color=4,
        Field_r33c19_pos=(33, 19),
        Field_r33c19_color=4,
        Field_r33c20_pos=(33, 20),
        Field_r33c20_color=4,
        Field_r33c21_pos=(33, 21),
        Field_r33c21_color=4,
        Field_r33c22_pos=(33, 22),
        Field_r33c22_color=4,
        Ground_r30c11_pos=(30, 11),
        Ground_r30c11_color=5,
        Ground_r30c12_pos=(30, 12),
        Ground_r30c12_color=5,
        Ground_r30c15_pos=(30, 15),
        Ground_r30c15_color=5,
        Ground_r30c16_pos=(30, 16),
        Ground_r30c16_color=5,
        Ground_r31c11_pos=(31, 11),
        Ground_r31c11_color=5,
        Ground_r31c12_pos=(31, 12),
        Ground_r31c12_color=5,
        Ground_r31c15_pos=(31, 15),
        Ground_r31c15_color=5,
        Ground_r31c16_pos=(31, 16),
        Ground_r31c16_color=5,
        Ground_r32c11_pos=(32, 11),
        Ground_r32c11_color=5,
        Ground_r32c12_pos=(32, 12),
        Ground_r32c12_color=5,
        Ground_r32c15_pos=(32, 15),
        Ground_r32c15_color=5,
        Ground_r32c16_pos=(32, 16),
        Ground_r32c16_color=5,
        Ground_r33c11_pos=(33, 11),
        Ground_r33c11_color=5,
        Ground_r33c12_pos=(33, 12),
        Ground_r33c12_color=5,
        Ground_r33c15_pos=(33, 15),
        Ground_r33c15_color=5,
        Ground_r33c16_pos=(33, 16),
        Ground_r33c16_color=5,
        Ground_r34c11_pos=(34, 11),
        Ground_r34c11_color=5,
        Ground_r34c12_pos=(34, 12),
        Ground_r34c12_color=5,
        Ground_r34c15_pos=(34, 15),
        Ground_r34c15_color=5,
        Ground_r34c16_pos=(34, 16),
        Ground_r34c16_color=5,
        Ground_r35c11_pos=(35, 11),
        Ground_r35c11_color=5,
        Ground_r35c12_pos=(35, 12),
        Ground_r35c12_color=5,
        Ground_r35c15_pos=(35, 15),
        Ground_r35c15_color=5,
        Ground_r35c16_pos=(35, 16),
        Ground_r35c16_color=5,
    )
