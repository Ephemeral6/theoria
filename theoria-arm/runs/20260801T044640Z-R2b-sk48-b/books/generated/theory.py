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
ACTIONS = [('key', 1), ('key', 2), ('key', 3), ('key', 7), ('key', 4)]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Ink0_r37c12_pos: object = (37, 12)
    Ink0_r37c12_color: object = 0
    Ink0_r37c13_pos: object = (37, 13)
    Ink0_r37c13_color: object = 0
    Ink0_r37c14_pos: object = (37, 14)
    Ink0_r37c14_color: object = 0
    Ink0_r37c15_pos: object = (37, 15)
    Ink0_r37c15_color: object = 0
    Ink0_r38c12_pos: object = (38, 12)
    Ink0_r38c12_color: object = 0
    Ink0_r38c15_pos: object = (38, 15)
    Ink0_r38c15_color: object = 0
    Ink0_r39c12_pos: object = (39, 12)
    Ink0_r39c12_color: object = 0
    Ink0_r39c15_pos: object = (39, 15)
    Ink0_r39c15_color: object = 0
    Ink0_r40c12_pos: object = (40, 12)
    Ink0_r40c12_color: object = 0
    Ink0_r40c13_pos: object = (40, 13)
    Ink0_r40c13_color: object = 0
    Ink0_r40c14_pos: object = (40, 14)
    Ink0_r40c14_color: object = 0
    Ink0_r40c15_pos: object = (40, 15)
    Ink0_r40c15_color: object = 0
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
    Ink4_r32c17_pos: object = (32, 17)
    Ink4_r32c17_color: object = 4
    Ink4_r32c18_pos: object = (32, 18)
    Ink4_r32c18_color: object = 4
    Ink4_r32c19_pos: object = (32, 19)
    Ink4_r32c19_color: object = 4
    Ink4_r32c20_pos: object = (32, 20)
    Ink4_r32c20_color: object = 4
    Ink4_r32c21_pos: object = (32, 21)
    Ink4_r32c21_color: object = 4
    Ink4_r32c22_pos: object = (32, 22)
    Ink4_r32c22_color: object = 4
    Ink4_r33c17_pos: object = (33, 17)
    Ink4_r33c17_color: object = 4
    Ink4_r33c18_pos: object = (33, 18)
    Ink4_r33c18_color: object = 4
    Ink4_r33c19_pos: object = (33, 19)
    Ink4_r33c19_color: object = 4
    Ink4_r33c20_pos: object = (33, 20)
    Ink4_r33c20_color: object = 4
    Ink4_r33c21_pos: object = (33, 21)
    Ink4_r33c21_color: object = 4
    Ink4_r33c22_pos: object = (33, 22)
    Ink4_r33c22_color: object = 4
    Ink5_r30c11_pos: object = (30, 11)
    Ink5_r30c11_color: object = 5
    Ink5_r30c12_pos: object = (30, 12)
    Ink5_r30c12_color: object = 5
    Ink5_r30c15_pos: object = (30, 15)
    Ink5_r30c15_color: object = 5
    Ink5_r30c16_pos: object = (30, 16)
    Ink5_r30c16_color: object = 5
    Ink5_r31c11_pos: object = (31, 11)
    Ink5_r31c11_color: object = 5
    Ink5_r31c12_pos: object = (31, 12)
    Ink5_r31c12_color: object = 5
    Ink5_r31c15_pos: object = (31, 15)
    Ink5_r31c15_color: object = 5
    Ink5_r31c16_pos: object = (31, 16)
    Ink5_r31c16_color: object = 5
    Ink5_r32c11_pos: object = (32, 11)
    Ink5_r32c11_color: object = 5
    Ink5_r32c12_pos: object = (32, 12)
    Ink5_r32c12_color: object = 5
    Ink5_r32c15_pos: object = (32, 15)
    Ink5_r32c15_color: object = 5
    Ink5_r32c16_pos: object = (32, 16)
    Ink5_r32c16_color: object = 5
    Ink5_r33c11_pos: object = (33, 11)
    Ink5_r33c11_color: object = 5
    Ink5_r33c12_pos: object = (33, 12)
    Ink5_r33c12_color: object = 5
    Ink5_r33c15_pos: object = (33, 15)
    Ink5_r33c15_color: object = 5
    Ink5_r33c16_pos: object = (33, 16)
    Ink5_r33c16_color: object = 5
    Ink5_r34c11_pos: object = (34, 11)
    Ink5_r34c11_color: object = 5
    Ink5_r34c12_pos: object = (34, 12)
    Ink5_r34c12_color: object = 5
    Ink5_r34c15_pos: object = (34, 15)
    Ink5_r34c15_color: object = 5
    Ink5_r34c16_pos: object = (34, 16)
    Ink5_r34c16_color: object = 5
    Ink5_r35c11_pos: object = (35, 11)
    Ink5_r35c11_color: object = 5
    Ink5_r35c12_pos: object = (35, 12)
    Ink5_r35c12_color: object = 5
    Ink5_r35c15_pos: object = (35, 15)
    Ink5_r35c15_color: object = 5
    Ink5_r35c16_pos: object = (35, 16)
    Ink5_r35c16_color: object = 5
    Ink6_r36c11_pos: object = (36, 11)
    Ink6_r36c11_color: object = 6
    Ink6_r36c12_pos: object = (36, 12)
    Ink6_r36c12_color: object = 6
    Ink6_r36c13_pos: object = (36, 13)
    Ink6_r36c13_color: object = 6
    Ink6_r36c14_pos: object = (36, 14)
    Ink6_r36c14_color: object = 6
    Ink6_r36c15_pos: object = (36, 15)
    Ink6_r36c15_color: object = 6
    Ink6_r36c16_pos: object = (36, 16)
    Ink6_r36c16_color: object = 6
    Ink6_r37c11_pos: object = (37, 11)
    Ink6_r37c11_color: object = 6
    Ink6_r37c16_pos: object = (37, 16)
    Ink6_r37c16_color: object = 6
    Ink6_r38c11_pos: object = (38, 11)
    Ink6_r38c11_color: object = 6
    Ink6_r38c13_pos: object = (38, 13)
    Ink6_r38c13_color: object = 6
    Ink6_r38c14_pos: object = (38, 14)
    Ink6_r38c14_color: object = 6
    Ink6_r39c11_pos: object = (39, 11)
    Ink6_r39c11_color: object = 6
    Ink6_r39c13_pos: object = (39, 13)
    Ink6_r39c13_color: object = 6
    Ink6_r39c14_pos: object = (39, 14)
    Ink6_r39c14_color: object = 6
    Ink6_r40c11_pos: object = (40, 11)
    Ink6_r40c11_color: object = 6
    Ink6_r40c16_pos: object = (40, 16)
    Ink6_r40c16_color: object = 6
    Ink6_r41c11_pos: object = (41, 11)
    Ink6_r41c11_color: object = 6
    Ink6_r41c12_pos: object = (41, 12)
    Ink6_r41c12_color: object = 6
    Ink6_r41c13_pos: object = (41, 13)
    Ink6_r41c13_color: object = 6
    Ink6_r41c14_pos: object = (41, 14)
    Ink6_r41c14_color: object = 6
    Ink6_r41c15_pos: object = (41, 15)
    Ink6_r41c15_color: object = 6
    Ink6_r41c16_pos: object = (41, 16)
    Ink6_r41c16_color: object = 6

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Ink0_r37c12_pos, self.Ink0_r37c12_color, self.Ink0_r37c13_pos, self.Ink0_r37c13_color, self.Ink0_r37c14_pos, self.Ink0_r37c14_color, self.Ink0_r37c15_pos, self.Ink0_r37c15_color, self.Ink0_r38c12_pos, self.Ink0_r38c12_color, self.Ink0_r38c15_pos, self.Ink0_r38c15_color, self.Ink0_r39c12_pos, self.Ink0_r39c12_color, self.Ink0_r39c15_pos, self.Ink0_r39c15_color, self.Ink0_r40c12_pos, self.Ink0_r40c12_color, self.Ink0_r40c13_pos, self.Ink0_r40c13_color, self.Ink0_r40c14_pos, self.Ink0_r40c14_color, self.Ink0_r40c15_pos, self.Ink0_r40c15_color, self.Ink1_r38c16_pos, self.Ink1_r38c16_color, self.Ink1_r38c18_pos, self.Ink1_r38c18_color, self.Ink1_r38c19_pos, self.Ink1_r38c19_color, self.Ink1_r38c21_pos, self.Ink1_r38c21_color, self.Ink1_r38c22_pos, self.Ink1_r38c22_color, self.Ink1_r39c17_pos, self.Ink1_r39c17_color, self.Ink1_r39c18_pos, self.Ink1_r39c18_color, self.Ink1_r39c20_pos, self.Ink1_r39c20_color, self.Ink1_r39c21_pos, self.Ink1_r39c21_color, self.Ink2_r32c13_pos, self.Ink2_r32c13_color, self.Ink2_r32c14_pos, self.Ink2_r32c14_color, self.Ink2_r33c13_pos, self.Ink2_r33c13_color, self.Ink2_r33c14_pos, self.Ink2_r33c14_color, self.Ink2_r38c17_pos, self.Ink2_r38c17_color, self.Ink2_r38c20_pos, self.Ink2_r38c20_color, self.Ink2_r39c16_pos, self.Ink2_r39c16_color, self.Ink2_r39c19_pos, self.Ink2_r39c19_color, self.Ink2_r39c22_pos, self.Ink2_r39c22_color, self.Ink2_r53c63_pos, self.Ink2_r53c63_color, self.Ink3_r30c13_pos, self.Ink3_r30c13_color, self.Ink3_r30c14_pos, self.Ink3_r30c14_color, self.Ink3_r31c13_pos, self.Ink3_r31c13_color, self.Ink3_r31c14_pos, self.Ink3_r31c14_color, self.Ink3_r34c13_pos, self.Ink3_r34c13_color, self.Ink3_r34c14_pos, self.Ink3_r34c14_color, self.Ink3_r35c13_pos, self.Ink3_r35c13_color, self.Ink3_r35c14_pos, self.Ink3_r35c14_color, self.Ink4_r32c17_pos, self.Ink4_r32c17_color, self.Ink4_r32c18_pos, self.Ink4_r32c18_color, self.Ink4_r32c19_pos, self.Ink4_r32c19_color, self.Ink4_r32c20_pos, self.Ink4_r32c20_color, self.Ink4_r32c21_pos, self.Ink4_r32c21_color, self.Ink4_r32c22_pos, self.Ink4_r32c22_color, self.Ink4_r33c17_pos, self.Ink4_r33c17_color, self.Ink4_r33c18_pos, self.Ink4_r33c18_color, self.Ink4_r33c19_pos, self.Ink4_r33c19_color, self.Ink4_r33c20_pos, self.Ink4_r33c20_color, self.Ink4_r33c21_pos, self.Ink4_r33c21_color, self.Ink4_r33c22_pos, self.Ink4_r33c22_color, self.Ink5_r30c11_pos, self.Ink5_r30c11_color, self.Ink5_r30c12_pos, self.Ink5_r30c12_color, self.Ink5_r30c15_pos, self.Ink5_r30c15_color, self.Ink5_r30c16_pos, self.Ink5_r30c16_color, self.Ink5_r31c11_pos, self.Ink5_r31c11_color, self.Ink5_r31c12_pos, self.Ink5_r31c12_color, self.Ink5_r31c15_pos, self.Ink5_r31c15_color, self.Ink5_r31c16_pos, self.Ink5_r31c16_color, self.Ink5_r32c11_pos, self.Ink5_r32c11_color, self.Ink5_r32c12_pos, self.Ink5_r32c12_color, self.Ink5_r32c15_pos, self.Ink5_r32c15_color, self.Ink5_r32c16_pos, self.Ink5_r32c16_color, self.Ink5_r33c11_pos, self.Ink5_r33c11_color, self.Ink5_r33c12_pos, self.Ink5_r33c12_color, self.Ink5_r33c15_pos, self.Ink5_r33c15_color, self.Ink5_r33c16_pos, self.Ink5_r33c16_color, self.Ink5_r34c11_pos, self.Ink5_r34c11_color, self.Ink5_r34c12_pos, self.Ink5_r34c12_color, self.Ink5_r34c15_pos, self.Ink5_r34c15_color, self.Ink5_r34c16_pos, self.Ink5_r34c16_color, self.Ink5_r35c11_pos, self.Ink5_r35c11_color, self.Ink5_r35c12_pos, self.Ink5_r35c12_color, self.Ink5_r35c15_pos, self.Ink5_r35c15_color, self.Ink5_r35c16_pos, self.Ink5_r35c16_color, self.Ink6_r36c11_pos, self.Ink6_r36c11_color, self.Ink6_r36c12_pos, self.Ink6_r36c12_color, self.Ink6_r36c13_pos, self.Ink6_r36c13_color, self.Ink6_r36c14_pos, self.Ink6_r36c14_color, self.Ink6_r36c15_pos, self.Ink6_r36c15_color, self.Ink6_r36c16_pos, self.Ink6_r36c16_color, self.Ink6_r37c11_pos, self.Ink6_r37c11_color, self.Ink6_r37c16_pos, self.Ink6_r37c16_color, self.Ink6_r38c11_pos, self.Ink6_r38c11_color, self.Ink6_r38c13_pos, self.Ink6_r38c13_color, self.Ink6_r38c14_pos, self.Ink6_r38c14_color, self.Ink6_r39c11_pos, self.Ink6_r39c11_color, self.Ink6_r39c13_pos, self.Ink6_r39c13_color, self.Ink6_r39c14_pos, self.Ink6_r39c14_color, self.Ink6_r40c11_pos, self.Ink6_r40c11_color, self.Ink6_r40c16_pos, self.Ink6_r40c16_color, self.Ink6_r41c11_pos, self.Ink6_r41c11_color, self.Ink6_r41c12_pos, self.Ink6_r41c12_color, self.Ink6_r41c13_pos, self.Ink6_r41c13_color, self.Ink6_r41c14_pos, self.Ink6_r41c14_color, self.Ink6_r41c15_pos, self.Ink6_r41c15_color, self.Ink6_r41c16_pos, self.Ink6_r41c16_color,)


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
    if 'Ink0_r37c12' not in _exclude:
        r, c = state.Ink0_r37c12_pos
        grid[r][c] = state.Ink0_r37c12_color
    if 'Ink0_r37c13' not in _exclude:
        r, c = state.Ink0_r37c13_pos
        grid[r][c] = state.Ink0_r37c13_color
    if 'Ink0_r37c14' not in _exclude:
        r, c = state.Ink0_r37c14_pos
        grid[r][c] = state.Ink0_r37c14_color
    if 'Ink0_r37c15' not in _exclude:
        r, c = state.Ink0_r37c15_pos
        grid[r][c] = state.Ink0_r37c15_color
    if 'Ink0_r38c12' not in _exclude:
        r, c = state.Ink0_r38c12_pos
        grid[r][c] = state.Ink0_r38c12_color
    if 'Ink0_r38c15' not in _exclude:
        r, c = state.Ink0_r38c15_pos
        grid[r][c] = state.Ink0_r38c15_color
    if 'Ink0_r39c12' not in _exclude:
        r, c = state.Ink0_r39c12_pos
        grid[r][c] = state.Ink0_r39c12_color
    if 'Ink0_r39c15' not in _exclude:
        r, c = state.Ink0_r39c15_pos
        grid[r][c] = state.Ink0_r39c15_color
    if 'Ink0_r40c12' not in _exclude:
        r, c = state.Ink0_r40c12_pos
        grid[r][c] = state.Ink0_r40c12_color
    if 'Ink0_r40c13' not in _exclude:
        r, c = state.Ink0_r40c13_pos
        grid[r][c] = state.Ink0_r40c13_color
    if 'Ink0_r40c14' not in _exclude:
        r, c = state.Ink0_r40c14_pos
        grid[r][c] = state.Ink0_r40c14_color
    if 'Ink0_r40c15' not in _exclude:
        r, c = state.Ink0_r40c15_pos
        grid[r][c] = state.Ink0_r40c15_color
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
    if 'Ink4_r32c17' not in _exclude:
        r, c = state.Ink4_r32c17_pos
        grid[r][c] = state.Ink4_r32c17_color
    if 'Ink4_r32c18' not in _exclude:
        r, c = state.Ink4_r32c18_pos
        grid[r][c] = state.Ink4_r32c18_color
    if 'Ink4_r32c19' not in _exclude:
        r, c = state.Ink4_r32c19_pos
        grid[r][c] = state.Ink4_r32c19_color
    if 'Ink4_r32c20' not in _exclude:
        r, c = state.Ink4_r32c20_pos
        grid[r][c] = state.Ink4_r32c20_color
    if 'Ink4_r32c21' not in _exclude:
        r, c = state.Ink4_r32c21_pos
        grid[r][c] = state.Ink4_r32c21_color
    if 'Ink4_r32c22' not in _exclude:
        r, c = state.Ink4_r32c22_pos
        grid[r][c] = state.Ink4_r32c22_color
    if 'Ink4_r33c17' not in _exclude:
        r, c = state.Ink4_r33c17_pos
        grid[r][c] = state.Ink4_r33c17_color
    if 'Ink4_r33c18' not in _exclude:
        r, c = state.Ink4_r33c18_pos
        grid[r][c] = state.Ink4_r33c18_color
    if 'Ink4_r33c19' not in _exclude:
        r, c = state.Ink4_r33c19_pos
        grid[r][c] = state.Ink4_r33c19_color
    if 'Ink4_r33c20' not in _exclude:
        r, c = state.Ink4_r33c20_pos
        grid[r][c] = state.Ink4_r33c20_color
    if 'Ink4_r33c21' not in _exclude:
        r, c = state.Ink4_r33c21_pos
        grid[r][c] = state.Ink4_r33c21_color
    if 'Ink4_r33c22' not in _exclude:
        r, c = state.Ink4_r33c22_pos
        grid[r][c] = state.Ink4_r33c22_color
    if 'Ink5_r30c11' not in _exclude:
        r, c = state.Ink5_r30c11_pos
        grid[r][c] = state.Ink5_r30c11_color
    if 'Ink5_r30c12' not in _exclude:
        r, c = state.Ink5_r30c12_pos
        grid[r][c] = state.Ink5_r30c12_color
    if 'Ink5_r30c15' not in _exclude:
        r, c = state.Ink5_r30c15_pos
        grid[r][c] = state.Ink5_r30c15_color
    if 'Ink5_r30c16' not in _exclude:
        r, c = state.Ink5_r30c16_pos
        grid[r][c] = state.Ink5_r30c16_color
    if 'Ink5_r31c11' not in _exclude:
        r, c = state.Ink5_r31c11_pos
        grid[r][c] = state.Ink5_r31c11_color
    if 'Ink5_r31c12' not in _exclude:
        r, c = state.Ink5_r31c12_pos
        grid[r][c] = state.Ink5_r31c12_color
    if 'Ink5_r31c15' not in _exclude:
        r, c = state.Ink5_r31c15_pos
        grid[r][c] = state.Ink5_r31c15_color
    if 'Ink5_r31c16' not in _exclude:
        r, c = state.Ink5_r31c16_pos
        grid[r][c] = state.Ink5_r31c16_color
    if 'Ink5_r32c11' not in _exclude:
        r, c = state.Ink5_r32c11_pos
        grid[r][c] = state.Ink5_r32c11_color
    if 'Ink5_r32c12' not in _exclude:
        r, c = state.Ink5_r32c12_pos
        grid[r][c] = state.Ink5_r32c12_color
    if 'Ink5_r32c15' not in _exclude:
        r, c = state.Ink5_r32c15_pos
        grid[r][c] = state.Ink5_r32c15_color
    if 'Ink5_r32c16' not in _exclude:
        r, c = state.Ink5_r32c16_pos
        grid[r][c] = state.Ink5_r32c16_color
    if 'Ink5_r33c11' not in _exclude:
        r, c = state.Ink5_r33c11_pos
        grid[r][c] = state.Ink5_r33c11_color
    if 'Ink5_r33c12' not in _exclude:
        r, c = state.Ink5_r33c12_pos
        grid[r][c] = state.Ink5_r33c12_color
    if 'Ink5_r33c15' not in _exclude:
        r, c = state.Ink5_r33c15_pos
        grid[r][c] = state.Ink5_r33c15_color
    if 'Ink5_r33c16' not in _exclude:
        r, c = state.Ink5_r33c16_pos
        grid[r][c] = state.Ink5_r33c16_color
    if 'Ink5_r34c11' not in _exclude:
        r, c = state.Ink5_r34c11_pos
        grid[r][c] = state.Ink5_r34c11_color
    if 'Ink5_r34c12' not in _exclude:
        r, c = state.Ink5_r34c12_pos
        grid[r][c] = state.Ink5_r34c12_color
    if 'Ink5_r34c15' not in _exclude:
        r, c = state.Ink5_r34c15_pos
        grid[r][c] = state.Ink5_r34c15_color
    if 'Ink5_r34c16' not in _exclude:
        r, c = state.Ink5_r34c16_pos
        grid[r][c] = state.Ink5_r34c16_color
    if 'Ink5_r35c11' not in _exclude:
        r, c = state.Ink5_r35c11_pos
        grid[r][c] = state.Ink5_r35c11_color
    if 'Ink5_r35c12' not in _exclude:
        r, c = state.Ink5_r35c12_pos
        grid[r][c] = state.Ink5_r35c12_color
    if 'Ink5_r35c15' not in _exclude:
        r, c = state.Ink5_r35c15_pos
        grid[r][c] = state.Ink5_r35c15_color
    if 'Ink5_r35c16' not in _exclude:
        r, c = state.Ink5_r35c16_pos
        grid[r][c] = state.Ink5_r35c16_color
    if 'Ink6_r36c11' not in _exclude:
        r, c = state.Ink6_r36c11_pos
        grid[r][c] = state.Ink6_r36c11_color
    if 'Ink6_r36c12' not in _exclude:
        r, c = state.Ink6_r36c12_pos
        grid[r][c] = state.Ink6_r36c12_color
    if 'Ink6_r36c13' not in _exclude:
        r, c = state.Ink6_r36c13_pos
        grid[r][c] = state.Ink6_r36c13_color
    if 'Ink6_r36c14' not in _exclude:
        r, c = state.Ink6_r36c14_pos
        grid[r][c] = state.Ink6_r36c14_color
    if 'Ink6_r36c15' not in _exclude:
        r, c = state.Ink6_r36c15_pos
        grid[r][c] = state.Ink6_r36c15_color
    if 'Ink6_r36c16' not in _exclude:
        r, c = state.Ink6_r36c16_pos
        grid[r][c] = state.Ink6_r36c16_color
    if 'Ink6_r37c11' not in _exclude:
        r, c = state.Ink6_r37c11_pos
        grid[r][c] = state.Ink6_r37c11_color
    if 'Ink6_r37c16' not in _exclude:
        r, c = state.Ink6_r37c16_pos
        grid[r][c] = state.Ink6_r37c16_color
    if 'Ink6_r38c11' not in _exclude:
        r, c = state.Ink6_r38c11_pos
        grid[r][c] = state.Ink6_r38c11_color
    if 'Ink6_r38c13' not in _exclude:
        r, c = state.Ink6_r38c13_pos
        grid[r][c] = state.Ink6_r38c13_color
    if 'Ink6_r38c14' not in _exclude:
        r, c = state.Ink6_r38c14_pos
        grid[r][c] = state.Ink6_r38c14_color
    if 'Ink6_r39c11' not in _exclude:
        r, c = state.Ink6_r39c11_pos
        grid[r][c] = state.Ink6_r39c11_color
    if 'Ink6_r39c13' not in _exclude:
        r, c = state.Ink6_r39c13_pos
        grid[r][c] = state.Ink6_r39c13_color
    if 'Ink6_r39c14' not in _exclude:
        r, c = state.Ink6_r39c14_pos
        grid[r][c] = state.Ink6_r39c14_color
    if 'Ink6_r40c11' not in _exclude:
        r, c = state.Ink6_r40c11_pos
        grid[r][c] = state.Ink6_r40c11_color
    if 'Ink6_r40c16' not in _exclude:
        r, c = state.Ink6_r40c16_pos
        grid[r][c] = state.Ink6_r40c16_color
    if 'Ink6_r41c11' not in _exclude:
        r, c = state.Ink6_r41c11_pos
        grid[r][c] = state.Ink6_r41c11_color
    if 'Ink6_r41c12' not in _exclude:
        r, c = state.Ink6_r41c12_pos
        grid[r][c] = state.Ink6_r41c12_color
    if 'Ink6_r41c13' not in _exclude:
        r, c = state.Ink6_r41c13_pos
        grid[r][c] = state.Ink6_r41c13_color
    if 'Ink6_r41c14' not in _exclude:
        r, c = state.Ink6_r41c14_pos
        grid[r][c] = state.Ink6_r41c14_color
    if 'Ink6_r41c15' not in _exclude:
        r, c = state.Ink6_r41c15_pos
        grid[r][c] = state.Ink6_r41c15_color
    if 'Ink6_r41c16' not in _exclude:
        r, c = state.Ink6_r41c16_pos
        grid[r][c] = state.Ink6_r41c16_color
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


def _guard_a1_icon1_field_takes_6__Ink5_r30c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r30c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r30c11(state):
    state.Ink5_r30c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r30c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r30c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r30c12(state):
    state.Ink5_r30c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r30c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r30c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r30c15(state):
    state.Ink5_r30c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r30c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r30c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r30c16(state):
    state.Ink5_r30c16_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r31c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r31c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r31c11(state):
    state.Ink5_r31c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r31c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r31c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r31c12(state):
    state.Ink5_r31c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r31c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r31c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r31c15(state):
    state.Ink5_r31c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r31c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r31c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r31c16(state):
    state.Ink5_r31c16_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r32c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r32c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r32c11(state):
    state.Ink5_r32c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r32c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r32c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r32c12(state):
    state.Ink5_r32c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r32c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r32c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r32c15(state):
    state.Ink5_r32c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r32c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r32c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r32c16(state):
    state.Ink5_r32c16_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r33c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r33c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r33c11(state):
    state.Ink5_r33c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r33c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r33c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r33c12(state):
    state.Ink5_r33c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r33c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r33c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r33c15(state):
    state.Ink5_r33c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r33c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r33c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r33c16(state):
    state.Ink5_r33c16_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r34c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r34c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r34c11(state):
    state.Ink5_r34c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r34c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r34c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r34c12(state):
    state.Ink5_r34c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r34c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r34c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r34c15(state):
    state.Ink5_r34c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r34c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r34c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r34c16(state):
    state.Ink5_r34c16_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r35c11(state, action):
    """a1_icon1_field_takes_6__Ink5_r35c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r35c11(state):
    state.Ink5_r35c11_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r35c12(state, action):
    """a1_icon1_field_takes_6__Ink5_r35c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r35c12(state):
    state.Ink5_r35c12_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r35c15(state, action):
    """a1_icon1_field_takes_6__Ink5_r35c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r35c15(state):
    state.Ink5_r35c15_color = 6


def _guard_a1_icon1_field_takes_6__Ink5_r35c16(state, action):
    """a1_icon1_field_takes_6__Ink5_r35c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_icon1_field_takes_6__Ink5_r35c16(state):
    state.Ink5_r35c16_color = 6


def _guard_a1_icon1_field_takes_0__Ink5_r30c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r30c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r30c11(state):
    state.Ink5_r30c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r30c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r30c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r30c12(state):
    state.Ink5_r30c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r30c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r30c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r30c15(state):
    state.Ink5_r30c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r30c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r30c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r30c16(state):
    state.Ink5_r30c16_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r31c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r31c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r31c11(state):
    state.Ink5_r31c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r31c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r31c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r31c12(state):
    state.Ink5_r31c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r31c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r31c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r31c15(state):
    state.Ink5_r31c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r31c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r31c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r31c16(state):
    state.Ink5_r31c16_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r32c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r32c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r32c11(state):
    state.Ink5_r32c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r32c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r32c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r32c12(state):
    state.Ink5_r32c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r32c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r32c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r32c15(state):
    state.Ink5_r32c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r32c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r32c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r32c16(state):
    state.Ink5_r32c16_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r33c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r33c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r33c11(state):
    state.Ink5_r33c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r33c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r33c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r33c12(state):
    state.Ink5_r33c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r33c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r33c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r33c15(state):
    state.Ink5_r33c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r33c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r33c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r33c16(state):
    state.Ink5_r33c16_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r34c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r34c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r34c11(state):
    state.Ink5_r34c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r34c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r34c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r34c12(state):
    state.Ink5_r34c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r34c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r34c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r34c15(state):
    state.Ink5_r34c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r34c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r34c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r34c16(state):
    state.Ink5_r34c16_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r35c11(state, action):
    """a1_icon1_field_takes_0__Ink5_r35c11  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r35c11(state):
    state.Ink5_r35c11_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r35c12(state, action):
    """a1_icon1_field_takes_0__Ink5_r35c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r35c12(state):
    state.Ink5_r35c12_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r35c15(state, action):
    """a1_icon1_field_takes_0__Ink5_r35c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r35c15(state):
    state.Ink5_r35c15_color = 0


def _guard_a1_icon1_field_takes_0__Ink5_r35c16(state, action):
    """a1_icon1_field_takes_0__Ink5_r35c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_icon1_field_takes_0__Ink5_r35c16(state):
    state.Ink5_r35c16_color = 0


def _guard_a1_icon1_field_takes_1__Ink5_r30c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r30c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r30c11(state):
    state.Ink5_r30c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r30c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r30c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r30c12(state):
    state.Ink5_r30c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r30c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r30c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r30c15(state):
    state.Ink5_r30c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r30c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r30c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r30c16(state):
    state.Ink5_r30c16_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r31c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r31c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r31c11(state):
    state.Ink5_r31c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r31c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r31c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r31c12(state):
    state.Ink5_r31c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r31c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r31c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r31c15(state):
    state.Ink5_r31c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r31c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r31c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r31c16(state):
    state.Ink5_r31c16_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r32c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r32c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r32c11(state):
    state.Ink5_r32c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r32c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r32c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r32c12(state):
    state.Ink5_r32c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r32c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r32c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r32c15(state):
    state.Ink5_r32c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r32c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r32c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r32c16(state):
    state.Ink5_r32c16_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r33c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r33c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r33c11(state):
    state.Ink5_r33c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r33c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r33c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r33c12(state):
    state.Ink5_r33c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r33c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r33c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r33c15(state):
    state.Ink5_r33c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r33c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r33c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r33c16(state):
    state.Ink5_r33c16_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r34c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r34c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r34c11(state):
    state.Ink5_r34c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r34c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r34c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r34c12(state):
    state.Ink5_r34c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r34c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r34c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r34c15(state):
    state.Ink5_r34c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r34c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r34c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r34c16(state):
    state.Ink5_r34c16_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r35c11(state, action):
    """a1_icon1_field_takes_1__Ink5_r35c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r35c11(state):
    state.Ink5_r35c11_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r35c12(state, action):
    """a1_icon1_field_takes_1__Ink5_r35c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r35c12(state):
    state.Ink5_r35c12_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r35c15(state, action):
    """a1_icon1_field_takes_1__Ink5_r35c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r35c15(state):
    state.Ink5_r35c15_color = 1


def _guard_a1_icon1_field_takes_1__Ink5_r35c16(state, action):
    """a1_icon1_field_takes_1__Ink5_r35c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_icon1_field_takes_1__Ink5_r35c16(state):
    state.Ink5_r35c16_color = 1


def _guard_a1_icon1_field_takes_2__Ink5_r30c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r30c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r30c11(state):
    state.Ink5_r30c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r30c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r30c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r30c12(state):
    state.Ink5_r30c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r30c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r30c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r30c15(state):
    state.Ink5_r30c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r30c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r30c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r30c16(state):
    state.Ink5_r30c16_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r31c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r31c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r31c11(state):
    state.Ink5_r31c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r31c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r31c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r31c12(state):
    state.Ink5_r31c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r31c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r31c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r31c15(state):
    state.Ink5_r31c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r31c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r31c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r31c16(state):
    state.Ink5_r31c16_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r32c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r32c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r32c11(state):
    state.Ink5_r32c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r32c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r32c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r32c12(state):
    state.Ink5_r32c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r32c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r32c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r32c15(state):
    state.Ink5_r32c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r32c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r32c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r32c16(state):
    state.Ink5_r32c16_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r33c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r33c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r33c11(state):
    state.Ink5_r33c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r33c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r33c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r33c12(state):
    state.Ink5_r33c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r33c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r33c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r33c15(state):
    state.Ink5_r33c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r33c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r33c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r33c16(state):
    state.Ink5_r33c16_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r34c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r34c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r34c11(state):
    state.Ink5_r34c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r34c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r34c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r34c12(state):
    state.Ink5_r34c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r34c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r34c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r34c15(state):
    state.Ink5_r34c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r34c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r34c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r34c16(state):
    state.Ink5_r34c16_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r35c11(state, action):
    """a1_icon1_field_takes_2__Ink5_r35c11  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r35c11(state):
    state.Ink5_r35c11_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r35c12(state, action):
    """a1_icon1_field_takes_2__Ink5_r35c12  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r35c12(state):
    state.Ink5_r35c12_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r35c15(state, action):
    """a1_icon1_field_takes_2__Ink5_r35c15  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r35c15(state):
    state.Ink5_r35c15_color = 2


def _guard_a1_icon1_field_takes_2__Ink5_r35c16(state, action):
    """a1_icon1_field_takes_2__Ink5_r35c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_icon1_field_takes_2__Ink5_r35c16(state):
    state.Ink5_r35c16_color = 2


def _guard_a1_track_takes_6__Ink3_r30c13(state, action):
    """a1_track_takes_6__Ink3_r30c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r30c13(state):
    state.Ink3_r30c13_color = 6


def _guard_a1_track_takes_6__Ink3_r30c14(state, action):
    """a1_track_takes_6__Ink3_r30c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r30c14(state):
    state.Ink3_r30c14_color = 6


def _guard_a1_track_takes_6__Ink3_r31c13(state, action):
    """a1_track_takes_6__Ink3_r31c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r31c13(state):
    state.Ink3_r31c13_color = 6


def _guard_a1_track_takes_6__Ink3_r31c14(state, action):
    """a1_track_takes_6__Ink3_r31c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r31c14(state):
    state.Ink3_r31c14_color = 6


def _guard_a1_track_takes_6__Ink3_r34c13(state, action):
    """a1_track_takes_6__Ink3_r34c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r34c13(state):
    state.Ink3_r34c13_color = 6


def _guard_a1_track_takes_6__Ink3_r34c14(state, action):
    """a1_track_takes_6__Ink3_r34c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r34c14(state):
    state.Ink3_r34c14_color = 6


def _guard_a1_track_takes_6__Ink3_r35c13(state, action):
    """a1_track_takes_6__Ink3_r35c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r35c13(state):
    state.Ink3_r35c13_color = 6


def _guard_a1_track_takes_6__Ink3_r35c14(state, action):
    """a1_track_takes_6__Ink3_r35c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_track_takes_6__Ink3_r35c14(state):
    state.Ink3_r35c14_color = 6


def _guard_a1_track_takes_0__Ink3_r30c13(state, action):
    """a1_track_takes_0__Ink3_r30c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r30c13(state):
    state.Ink3_r30c13_color = 0


def _guard_a1_track_takes_0__Ink3_r30c14(state, action):
    """a1_track_takes_0__Ink3_r30c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r30c14(state):
    state.Ink3_r30c14_color = 0


def _guard_a1_track_takes_0__Ink3_r31c13(state, action):
    """a1_track_takes_0__Ink3_r31c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r31c13(state):
    state.Ink3_r31c13_color = 0


def _guard_a1_track_takes_0__Ink3_r31c14(state, action):
    """a1_track_takes_0__Ink3_r31c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r31c14(state):
    state.Ink3_r31c14_color = 0


def _guard_a1_track_takes_0__Ink3_r34c13(state, action):
    """a1_track_takes_0__Ink3_r34c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r34c13(state):
    state.Ink3_r34c13_color = 0


def _guard_a1_track_takes_0__Ink3_r34c14(state, action):
    """a1_track_takes_0__Ink3_r34c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r34c14(state):
    state.Ink3_r34c14_color = 0


def _guard_a1_track_takes_0__Ink3_r35c13(state, action):
    """a1_track_takes_0__Ink3_r35c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r35c13(state):
    state.Ink3_r35c13_color = 0


def _guard_a1_track_takes_0__Ink3_r35c14(state, action):
    """a1_track_takes_0__Ink3_r35c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_a1_track_takes_0__Ink3_r35c14(state):
    state.Ink3_r35c14_color = 0


def _guard_a1_tape1_takes_2__Ink4_r32c17(state, action):
    """a1_tape1_takes_2__Ink4_r32c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c17(state):
    state.Ink4_r32c17_color = 2


def _guard_a1_tape1_takes_2__Ink4_r32c18(state, action):
    """a1_tape1_takes_2__Ink4_r32c18  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c18(state):
    state.Ink4_r32c18_color = 2


def _guard_a1_tape1_takes_2__Ink4_r32c19(state, action):
    """a1_tape1_takes_2__Ink4_r32c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c19(state):
    state.Ink4_r32c19_color = 2


def _guard_a1_tape1_takes_2__Ink4_r32c20(state, action):
    """a1_tape1_takes_2__Ink4_r32c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c20(state):
    state.Ink4_r32c20_color = 2


def _guard_a1_tape1_takes_2__Ink4_r32c21(state, action):
    """a1_tape1_takes_2__Ink4_r32c21  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c21(state):
    state.Ink4_r32c21_color = 2


def _guard_a1_tape1_takes_2__Ink4_r32c22(state, action):
    """a1_tape1_takes_2__Ink4_r32c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r32c22(state):
    state.Ink4_r32c22_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c17(state, action):
    """a1_tape1_takes_2__Ink4_r33c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c17(state):
    state.Ink4_r33c17_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c18(state, action):
    """a1_tape1_takes_2__Ink4_r33c18  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c18(state):
    state.Ink4_r33c18_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c19(state, action):
    """a1_tape1_takes_2__Ink4_r33c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c19(state):
    state.Ink4_r33c19_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c20(state, action):
    """a1_tape1_takes_2__Ink4_r33c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c20(state):
    state.Ink4_r33c20_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c21(state, action):
    """a1_tape1_takes_2__Ink4_r33c21  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c21(state):
    state.Ink4_r33c21_color = 2


def _guard_a1_tape1_takes_2__Ink4_r33c22(state, action):
    """a1_tape1_takes_2__Ink4_r33c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a1_tape1_takes_2__Ink4_r33c22(state):
    state.Ink4_r33c22_color = 2


def _guard_a1_tape1_takes_1__Ink4_r32c17(state, action):
    """a1_tape1_takes_1__Ink4_r32c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c17(state):
    state.Ink4_r32c17_color = 1


def _guard_a1_tape1_takes_1__Ink4_r32c18(state, action):
    """a1_tape1_takes_1__Ink4_r32c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c18(state):
    state.Ink4_r32c18_color = 1


def _guard_a1_tape1_takes_1__Ink4_r32c19(state, action):
    """a1_tape1_takes_1__Ink4_r32c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c19(state):
    state.Ink4_r32c19_color = 1


def _guard_a1_tape1_takes_1__Ink4_r32c20(state, action):
    """a1_tape1_takes_1__Ink4_r32c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c20(state):
    state.Ink4_r32c20_color = 1


def _guard_a1_tape1_takes_1__Ink4_r32c21(state, action):
    """a1_tape1_takes_1__Ink4_r32c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c21(state):
    state.Ink4_r32c21_color = 1


def _guard_a1_tape1_takes_1__Ink4_r32c22(state, action):
    """a1_tape1_takes_1__Ink4_r32c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r32c22(state):
    state.Ink4_r32c22_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c17(state, action):
    """a1_tape1_takes_1__Ink4_r33c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c17(state):
    state.Ink4_r33c17_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c18(state, action):
    """a1_tape1_takes_1__Ink4_r33c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c18(state):
    state.Ink4_r33c18_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c19(state, action):
    """a1_tape1_takes_1__Ink4_r33c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c19(state):
    state.Ink4_r33c19_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c20(state, action):
    """a1_tape1_takes_1__Ink4_r33c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c20(state):
    state.Ink4_r33c20_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c21(state, action):
    """a1_tape1_takes_1__Ink4_r33c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c21(state):
    state.Ink4_r33c21_color = 1


def _guard_a1_tape1_takes_1__Ink4_r33c22(state, action):
    """a1_tape1_takes_1__Ink4_r33c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_a1_tape1_takes_1__Ink4_r33c22(state):
    state.Ink4_r33c22_color = 1


def _guard_a1_thumb_takes_6__Ink2_r32c13(state, action):
    """a1_thumb_takes_6__Ink2_r32c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 6


def _guard_a1_thumb_takes_6__Ink2_r32c14(state, action):
    """a1_thumb_takes_6__Ink2_r32c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 6


def _guard_a1_thumb_takes_6__Ink2_r33c13(state, action):
    """a1_thumb_takes_6__Ink2_r33c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 6


def _guard_a1_thumb_takes_6__Ink2_r33c14(state, action):
    """a1_thumb_takes_6__Ink2_r33c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 6


def _guard_a1_thumb_takes_6__Ink2_r38c17(state, action):
    """a1_thumb_takes_6__Ink2_r38c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 6


def _guard_a1_thumb_takes_6__Ink2_r38c20(state, action):
    """a1_thumb_takes_6__Ink2_r38c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 6


def _guard_a1_thumb_takes_6__Ink2_r39c16(state, action):
    """a1_thumb_takes_6__Ink2_r39c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 6


def _guard_a1_thumb_takes_6__Ink2_r39c19(state, action):
    """a1_thumb_takes_6__Ink2_r39c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 6


def _guard_a1_thumb_takes_6__Ink2_r39c22(state, action):
    """a1_thumb_takes_6__Ink2_r39c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 6


def _guard_a1_thumb_takes_6__Ink2_r53c63(state, action):
    """a1_thumb_takes_6__Ink2_r53c63  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_a1_thumb_takes_6__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 6


def _guard_a1_lower_ink2_takes_4__Ink2_r32c13(state, action):
    """a1_lower_ink2_takes_4__Ink2_r32c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r32c14(state, action):
    """a1_lower_ink2_takes_4__Ink2_r32c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r33c13(state, action):
    """a1_lower_ink2_takes_4__Ink2_r33c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r33c14(state, action):
    """a1_lower_ink2_takes_4__Ink2_r33c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r38c17(state, action):
    """a1_lower_ink2_takes_4__Ink2_r38c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r38c20(state, action):
    """a1_lower_ink2_takes_4__Ink2_r38c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r39c16(state, action):
    """a1_lower_ink2_takes_4__Ink2_r39c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r39c19(state, action):
    """a1_lower_ink2_takes_4__Ink2_r39c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r39c22(state, action):
    """a1_lower_ink2_takes_4__Ink2_r39c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 4


def _guard_a1_lower_ink2_takes_4__Ink2_r53c63(state, action):
    """a1_lower_ink2_takes_4__Ink2_r53c63  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_lower_ink2_takes_4__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 4


def _guard_a1_lower_ink2_takes_5__Ink2_r32c13(state, action):
    """a1_lower_ink2_takes_5__Ink2_r32c13  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r32c14(state, action):
    """a1_lower_ink2_takes_5__Ink2_r32c14  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r33c13(state, action):
    """a1_lower_ink2_takes_5__Ink2_r33c13  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r33c14(state, action):
    """a1_lower_ink2_takes_5__Ink2_r33c14  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r38c17(state, action):
    """a1_lower_ink2_takes_5__Ink2_r38c17  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r38c20(state, action):
    """a1_lower_ink2_takes_5__Ink2_r38c20  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r39c16(state, action):
    """a1_lower_ink2_takes_5__Ink2_r39c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r39c19(state, action):
    """a1_lower_ink2_takes_5__Ink2_r39c19  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r39c22(state, action):
    """a1_lower_ink2_takes_5__Ink2_r39c22  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 5


def _guard_a1_lower_ink2_takes_5__Ink2_r53c63(state, action):
    """a1_lower_ink2_takes_5__Ink2_r53c63  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_lower_ink2_takes_5__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c11(state):
    state.Ink6_r36c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c12(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c12(state):
    state.Ink6_r36c12_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c13(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c13  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c13(state):
    state.Ink6_r36c13_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c14(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c14  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c14(state):
    state.Ink6_r36c14_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c15(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c15(state):
    state.Ink6_r36c15_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r36c16(state, action):
    """a1_icon2_body_takes_5__Ink6_r36c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r36c16(state):
    state.Ink6_r36c16_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r37c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r37c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r37c11(state):
    state.Ink6_r37c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r37c16(state, action):
    """a1_icon2_body_takes_5__Ink6_r37c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r37c16(state):
    state.Ink6_r37c16_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r38c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r38c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r38c11(state):
    state.Ink6_r38c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r38c13(state, action):
    """a1_icon2_body_takes_5__Ink6_r38c13  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r38c13(state):
    state.Ink6_r38c13_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r38c14(state, action):
    """a1_icon2_body_takes_5__Ink6_r38c14  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r38c14(state):
    state.Ink6_r38c14_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r39c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r39c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r39c11(state):
    state.Ink6_r39c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r39c13(state, action):
    """a1_icon2_body_takes_5__Ink6_r39c13  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r39c13(state):
    state.Ink6_r39c13_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r39c14(state, action):
    """a1_icon2_body_takes_5__Ink6_r39c14  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r39c14(state):
    state.Ink6_r39c14_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r40c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r40c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r40c11(state):
    state.Ink6_r40c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r40c16(state, action):
    """a1_icon2_body_takes_5__Ink6_r40c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r40c16(state):
    state.Ink6_r40c16_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c11(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c11  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c11(state):
    state.Ink6_r41c11_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c12(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c12  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c12(state):
    state.Ink6_r41c12_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c13(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c13  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c13(state):
    state.Ink6_r41c13_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c14(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c14  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c14(state):
    state.Ink6_r41c14_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c15(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c15  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c15(state):
    state.Ink6_r41c15_color = 5


def _guard_a1_icon2_body_takes_5__Ink6_r41c16(state, action):
    """a1_icon2_body_takes_5__Ink6_r41c16  [ev: t1  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_body_takes_5__Ink6_r41c16(state):
    state.Ink6_r41c16_color = 5


def _guard_a1_icon2_body_takes_3__Ink6_r36c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c11(state):
    state.Ink6_r36c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r36c12(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c12(state):
    state.Ink6_r36c12_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r36c13(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c13(state):
    state.Ink6_r36c13_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r36c14(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c14(state):
    state.Ink6_r36c14_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r36c15(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c15(state):
    state.Ink6_r36c15_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r36c16(state, action):
    """a1_icon2_body_takes_3__Ink6_r36c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r36c16(state):
    state.Ink6_r36c16_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r37c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r37c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r37c11(state):
    state.Ink6_r37c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r37c16(state, action):
    """a1_icon2_body_takes_3__Ink6_r37c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r37c16(state):
    state.Ink6_r37c16_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r38c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r38c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r38c11(state):
    state.Ink6_r38c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r38c13(state, action):
    """a1_icon2_body_takes_3__Ink6_r38c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r38c13(state):
    state.Ink6_r38c13_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r38c14(state, action):
    """a1_icon2_body_takes_3__Ink6_r38c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r38c14(state):
    state.Ink6_r38c14_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r39c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r39c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r39c11(state):
    state.Ink6_r39c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r39c13(state, action):
    """a1_icon2_body_takes_3__Ink6_r39c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r39c13(state):
    state.Ink6_r39c13_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r39c14(state, action):
    """a1_icon2_body_takes_3__Ink6_r39c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r39c14(state):
    state.Ink6_r39c14_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r40c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r40c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r40c11(state):
    state.Ink6_r40c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r40c16(state, action):
    """a1_icon2_body_takes_3__Ink6_r40c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r40c16(state):
    state.Ink6_r40c16_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c11(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c11(state):
    state.Ink6_r41c11_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c12(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c12(state):
    state.Ink6_r41c12_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c13(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c13(state):
    state.Ink6_r41c13_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c14(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c14(state):
    state.Ink6_r41c14_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c15(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c15(state):
    state.Ink6_r41c15_color = 3


def _guard_a1_icon2_body_takes_3__Ink6_r41c16(state, action):
    """a1_icon2_body_takes_3__Ink6_r41c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_body_takes_3__Ink6_r41c16(state):
    state.Ink6_r41c16_color = 3


def _guard_a1_icon2_body_takes_2__Ink6_r36c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c11(state):
    state.Ink6_r36c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r36c12(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c12(state):
    state.Ink6_r36c12_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r36c13(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c13(state):
    state.Ink6_r36c13_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r36c14(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c14(state):
    state.Ink6_r36c14_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r36c15(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c15(state):
    state.Ink6_r36c15_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r36c16(state, action):
    """a1_icon2_body_takes_2__Ink6_r36c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r36c16(state):
    state.Ink6_r36c16_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r37c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r37c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r37c11(state):
    state.Ink6_r37c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r37c16(state, action):
    """a1_icon2_body_takes_2__Ink6_r37c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r37c16(state):
    state.Ink6_r37c16_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r38c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r38c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r38c11(state):
    state.Ink6_r38c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r38c13(state, action):
    """a1_icon2_body_takes_2__Ink6_r38c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r38c13(state):
    state.Ink6_r38c13_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r38c14(state, action):
    """a1_icon2_body_takes_2__Ink6_r38c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r38c14(state):
    state.Ink6_r38c14_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r39c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r39c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r39c11(state):
    state.Ink6_r39c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r39c13(state, action):
    """a1_icon2_body_takes_2__Ink6_r39c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r39c13(state):
    state.Ink6_r39c13_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r39c14(state, action):
    """a1_icon2_body_takes_2__Ink6_r39c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r39c14(state):
    state.Ink6_r39c14_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r40c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r40c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r40c11(state):
    state.Ink6_r40c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r40c16(state, action):
    """a1_icon2_body_takes_2__Ink6_r40c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r40c16(state):
    state.Ink6_r40c16_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c11(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c11  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c11(state):
    state.Ink6_r41c11_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c12(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c12(state):
    state.Ink6_r41c12_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c13(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c13(state):
    state.Ink6_r41c13_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c14(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c14(state):
    state.Ink6_r41c14_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c15(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c15(state):
    state.Ink6_r41c15_color = 2


def _guard_a1_icon2_body_takes_2__Ink6_r41c16(state, action):
    """a1_icon2_body_takes_2__Ink6_r41c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a1_icon2_body_takes_2__Ink6_r41c16(state):
    state.Ink6_r41c16_color = 2


def _guard_a1_icon2_hole_takes_5__Ink0_r37c12(state, action):
    """a1_icon2_hole_takes_5__Ink0_r37c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r37c12(state):
    state.Ink0_r37c12_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r37c13(state, action):
    """a1_icon2_hole_takes_5__Ink0_r37c13  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r37c13(state):
    state.Ink0_r37c13_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r37c14(state, action):
    """a1_icon2_hole_takes_5__Ink0_r37c14  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r37c14(state):
    state.Ink0_r37c14_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r37c15(state, action):
    """a1_icon2_hole_takes_5__Ink0_r37c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r37c15(state):
    state.Ink0_r37c15_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r38c12(state, action):
    """a1_icon2_hole_takes_5__Ink0_r38c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r38c12(state):
    state.Ink0_r38c12_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r38c15(state, action):
    """a1_icon2_hole_takes_5__Ink0_r38c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r38c15(state):
    state.Ink0_r38c15_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r39c12(state, action):
    """a1_icon2_hole_takes_5__Ink0_r39c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r39c12(state):
    state.Ink0_r39c12_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r39c15(state, action):
    """a1_icon2_hole_takes_5__Ink0_r39c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r39c15(state):
    state.Ink0_r39c15_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r40c12(state, action):
    """a1_icon2_hole_takes_5__Ink0_r40c12  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r40c12(state):
    state.Ink0_r40c12_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r40c13(state, action):
    """a1_icon2_hole_takes_5__Ink0_r40c13  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r40c13(state):
    state.Ink0_r40c13_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r40c14(state, action):
    """a1_icon2_hole_takes_5__Ink0_r40c14  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r40c14(state):
    state.Ink0_r40c14_color = 5


def _guard_a1_icon2_hole_takes_5__Ink0_r40c15(state, action):
    """a1_icon2_hole_takes_5__Ink0_r40c15  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_icon2_hole_takes_5__Ink0_r40c15(state):
    state.Ink0_r40c15_color = 5


def _guard_a1_icon2_hole_takes_3__Ink0_r37c12(state, action):
    """a1_icon2_hole_takes_3__Ink0_r37c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r37c12(state):
    state.Ink0_r37c12_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r37c13(state, action):
    """a1_icon2_hole_takes_3__Ink0_r37c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r37c13(state):
    state.Ink0_r37c13_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r37c14(state, action):
    """a1_icon2_hole_takes_3__Ink0_r37c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r37c14(state):
    state.Ink0_r37c14_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r37c15(state, action):
    """a1_icon2_hole_takes_3__Ink0_r37c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r37c15(state):
    state.Ink0_r37c15_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r38c12(state, action):
    """a1_icon2_hole_takes_3__Ink0_r38c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r38c12(state):
    state.Ink0_r38c12_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r38c15(state, action):
    """a1_icon2_hole_takes_3__Ink0_r38c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r38c15(state):
    state.Ink0_r38c15_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r39c12(state, action):
    """a1_icon2_hole_takes_3__Ink0_r39c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r39c12(state):
    state.Ink0_r39c12_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r39c15(state, action):
    """a1_icon2_hole_takes_3__Ink0_r39c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r39c15(state):
    state.Ink0_r39c15_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r40c12(state, action):
    """a1_icon2_hole_takes_3__Ink0_r40c12  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r40c12(state):
    state.Ink0_r40c12_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r40c13(state, action):
    """a1_icon2_hole_takes_3__Ink0_r40c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r40c13(state):
    state.Ink0_r40c13_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r40c14(state, action):
    """a1_icon2_hole_takes_3__Ink0_r40c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r40c14(state):
    state.Ink0_r40c14_color = 3


def _guard_a1_icon2_hole_takes_3__Ink0_r40c15(state, action):
    """a1_icon2_hole_takes_3__Ink0_r40c15  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_a1_icon2_hole_takes_3__Ink0_r40c15(state):
    state.Ink0_r40c15_color = 3


def _guard_a1_tape2_takes_4__Ink1_r38c16(state, action):
    """a1_tape2_takes_4__Ink1_r38c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 4


def _guard_a1_tape2_takes_4__Ink1_r38c18(state, action):
    """a1_tape2_takes_4__Ink1_r38c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 4


def _guard_a1_tape2_takes_4__Ink1_r38c19(state, action):
    """a1_tape2_takes_4__Ink1_r38c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 4


def _guard_a1_tape2_takes_4__Ink1_r38c21(state, action):
    """a1_tape2_takes_4__Ink1_r38c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 4


def _guard_a1_tape2_takes_4__Ink1_r38c22(state, action):
    """a1_tape2_takes_4__Ink1_r38c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 4


def _guard_a1_tape2_takes_4__Ink1_r39c17(state, action):
    """a1_tape2_takes_4__Ink1_r39c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 4


def _guard_a1_tape2_takes_4__Ink1_r39c18(state, action):
    """a1_tape2_takes_4__Ink1_r39c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 4


def _guard_a1_tape2_takes_4__Ink1_r39c20(state, action):
    """a1_tape2_takes_4__Ink1_r39c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 4


def _guard_a1_tape2_takes_4__Ink1_r39c21(state, action):
    """a1_tape2_takes_4__Ink1_r39c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_a1_tape2_takes_4__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 4


def _guard_a1_tape2_takes_5__Ink1_r38c16(state, action):
    """a1_tape2_takes_5__Ink1_r38c16  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 5


def _guard_a1_tape2_takes_5__Ink1_r38c18(state, action):
    """a1_tape2_takes_5__Ink1_r38c18  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 5


def _guard_a1_tape2_takes_5__Ink1_r38c19(state, action):
    """a1_tape2_takes_5__Ink1_r38c19  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 5


def _guard_a1_tape2_takes_5__Ink1_r38c21(state, action):
    """a1_tape2_takes_5__Ink1_r38c21  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 5


def _guard_a1_tape2_takes_5__Ink1_r38c22(state, action):
    """a1_tape2_takes_5__Ink1_r38c22  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 5


def _guard_a1_tape2_takes_5__Ink1_r39c17(state, action):
    """a1_tape2_takes_5__Ink1_r39c17  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 5


def _guard_a1_tape2_takes_5__Ink1_r39c18(state, action):
    """a1_tape2_takes_5__Ink1_r39c18  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 5


def _guard_a1_tape2_takes_5__Ink1_r39c20(state, action):
    """a1_tape2_takes_5__Ink1_r39c20  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 5


def _guard_a1_tape2_takes_5__Ink1_r39c21(state, action):
    """a1_tape2_takes_5__Ink1_r39c21  [ev: t1  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_a1_tape2_takes_5__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r30c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r30c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r30c11(state):
    state.Ink5_r30c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r30c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r30c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r30c12(state):
    state.Ink5_r30c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r30c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r30c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r30c15(state):
    state.Ink5_r30c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r30c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r30c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r30c16(state):
    state.Ink5_r30c16_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r31c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r31c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r31c11(state):
    state.Ink5_r31c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r31c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r31c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r31c12(state):
    state.Ink5_r31c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r31c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r31c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r31c15(state):
    state.Ink5_r31c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r31c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r31c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r31c16(state):
    state.Ink5_r31c16_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r32c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r32c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r32c11(state):
    state.Ink5_r32c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r32c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r32c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r32c12(state):
    state.Ink5_r32c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r32c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r32c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r32c15(state):
    state.Ink5_r32c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r32c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r32c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r32c16(state):
    state.Ink5_r32c16_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r33c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r33c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r33c11(state):
    state.Ink5_r33c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r33c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r33c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r33c12(state):
    state.Ink5_r33c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r33c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r33c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r33c15(state):
    state.Ink5_r33c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r33c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r33c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r33c16(state):
    state.Ink5_r33c16_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r34c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r34c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r34c11(state):
    state.Ink5_r34c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r34c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r34c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r34c12(state):
    state.Ink5_r34c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r34c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r34c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r34c15(state):
    state.Ink5_r34c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r34c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r34c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r34c16(state):
    state.Ink5_r34c16_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r35c11(state, action):
    """a2_icon1_field_takes_5__Ink5_r35c11  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r35c11(state):
    state.Ink5_r35c11_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r35c12(state, action):
    """a2_icon1_field_takes_5__Ink5_r35c12  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r35c12(state):
    state.Ink5_r35c12_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r35c15(state, action):
    """a2_icon1_field_takes_5__Ink5_r35c15  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r35c15(state):
    state.Ink5_r35c15_color = 5


def _guard_a2_icon1_field_takes_5__Ink5_r35c16(state, action):
    """a2_icon1_field_takes_5__Ink5_r35c16  [ev: t2  cov: 24/24]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink5_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_a2_icon1_field_takes_5__Ink5_r35c16(state):
    state.Ink5_r35c16_color = 5


def _guard_a2_track_takes_3__Ink3_r30c13(state, action):
    """a2_track_takes_3__Ink3_r30c13  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r30c13(state):
    state.Ink3_r30c13_color = 3


def _guard_a2_track_takes_3__Ink3_r30c14(state, action):
    """a2_track_takes_3__Ink3_r30c14  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r30c14(state):
    state.Ink3_r30c14_color = 3


def _guard_a2_track_takes_3__Ink3_r31c13(state, action):
    """a2_track_takes_3__Ink3_r31c13  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r31c13(state):
    state.Ink3_r31c13_color = 3


def _guard_a2_track_takes_3__Ink3_r31c14(state, action):
    """a2_track_takes_3__Ink3_r31c14  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r31c14(state):
    state.Ink3_r31c14_color = 3


def _guard_a2_track_takes_3__Ink3_r34c13(state, action):
    """a2_track_takes_3__Ink3_r34c13  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r34c13(state):
    state.Ink3_r34c13_color = 3


def _guard_a2_track_takes_3__Ink3_r34c14(state, action):
    """a2_track_takes_3__Ink3_r34c14  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r34c14(state):
    state.Ink3_r34c14_color = 3


def _guard_a2_track_takes_3__Ink3_r35c13(state, action):
    """a2_track_takes_3__Ink3_r35c13  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r35c13(state):
    state.Ink3_r35c13_color = 3


def _guard_a2_track_takes_3__Ink3_r35c14(state, action):
    """a2_track_takes_3__Ink3_r35c14  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink3_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_a2_track_takes_3__Ink3_r35c14(state):
    state.Ink3_r35c14_color = 3


def _guard_a2_tape1_takes_4__Ink4_r32c17(state, action):
    """a2_tape1_takes_4__Ink4_r32c17  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c17(state):
    state.Ink4_r32c17_color = 4


def _guard_a2_tape1_takes_4__Ink4_r32c18(state, action):
    """a2_tape1_takes_4__Ink4_r32c18  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c18(state):
    state.Ink4_r32c18_color = 4


def _guard_a2_tape1_takes_4__Ink4_r32c19(state, action):
    """a2_tape1_takes_4__Ink4_r32c19  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c19(state):
    state.Ink4_r32c19_color = 4


def _guard_a2_tape1_takes_4__Ink4_r32c20(state, action):
    """a2_tape1_takes_4__Ink4_r32c20  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c20(state):
    state.Ink4_r32c20_color = 4


def _guard_a2_tape1_takes_4__Ink4_r32c21(state, action):
    """a2_tape1_takes_4__Ink4_r32c21  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c21(state):
    state.Ink4_r32c21_color = 4


def _guard_a2_tape1_takes_4__Ink4_r32c22(state, action):
    """a2_tape1_takes_4__Ink4_r32c22  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r32c22(state):
    state.Ink4_r32c22_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c17(state, action):
    """a2_tape1_takes_4__Ink4_r33c17  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c17(state):
    state.Ink4_r33c17_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c18(state, action):
    """a2_tape1_takes_4__Ink4_r33c18  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c18(state):
    state.Ink4_r33c18_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c19(state, action):
    """a2_tape1_takes_4__Ink4_r33c19  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c19(state):
    state.Ink4_r33c19_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c20(state, action):
    """a2_tape1_takes_4__Ink4_r33c20  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c20(state):
    state.Ink4_r33c20_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c21(state, action):
    """a2_tape1_takes_4__Ink4_r33c21  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c21(state):
    state.Ink4_r33c21_color = 4


def _guard_a2_tape1_takes_4__Ink4_r33c22(state, action):
    """a2_tape1_takes_4__Ink4_r33c22  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink4_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_a2_tape1_takes_4__Ink4_r33c22(state):
    state.Ink4_r33c22_color = 4


def _guard_a2_thumb_takes_2__Ink2_r32c13(state, action):
    """a2_thumb_takes_2__Ink2_r32c13  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 2


def _guard_a2_thumb_takes_2__Ink2_r32c14(state, action):
    """a2_thumb_takes_2__Ink2_r32c14  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 2


def _guard_a2_thumb_takes_2__Ink2_r33c13(state, action):
    """a2_thumb_takes_2__Ink2_r33c13  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 2


def _guard_a2_thumb_takes_2__Ink2_r33c14(state, action):
    """a2_thumb_takes_2__Ink2_r33c14  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 2


def _guard_a2_thumb_takes_2__Ink2_r38c17(state, action):
    """a2_thumb_takes_2__Ink2_r38c17  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 2


def _guard_a2_thumb_takes_2__Ink2_r38c20(state, action):
    """a2_thumb_takes_2__Ink2_r38c20  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 2


def _guard_a2_thumb_takes_2__Ink2_r39c16(state, action):
    """a2_thumb_takes_2__Ink2_r39c16  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 2


def _guard_a2_thumb_takes_2__Ink2_r39c19(state, action):
    """a2_thumb_takes_2__Ink2_r39c19  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 2


def _guard_a2_thumb_takes_2__Ink2_r39c22(state, action):
    """a2_thumb_takes_2__Ink2_r39c22  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 2


def _guard_a2_thumb_takes_2__Ink2_r53c63(state, action):
    """a2_thumb_takes_2__Ink2_r53c63  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_a2_thumb_takes_2__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r32c13(state, action):
    """a2_lower_ink2_takes_2__Ink2_r32c13  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r32c14(state, action):
    """a2_lower_ink2_takes_2__Ink2_r32c14  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r33c13(state, action):
    """a2_lower_ink2_takes_2__Ink2_r33c13  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r33c14(state, action):
    """a2_lower_ink2_takes_2__Ink2_r33c14  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r38c17(state, action):
    """a2_lower_ink2_takes_2__Ink2_r38c17  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r38c20(state, action):
    """a2_lower_ink2_takes_2__Ink2_r38c20  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r39c16(state, action):
    """a2_lower_ink2_takes_2__Ink2_r39c16  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r39c19(state, action):
    """a2_lower_ink2_takes_2__Ink2_r39c19  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r39c22(state, action):
    """a2_lower_ink2_takes_2__Ink2_r39c22  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 2


def _guard_a2_lower_ink2_takes_2__Ink2_r53c63(state, action):
    """a2_lower_ink2_takes_2__Ink2_r53c63  [ev: t2  cov: 5/5]"""
    if action != ('key', 2): return False
    if (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    if not (_free(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down'))): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_a2_lower_ink2_takes_2__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 2


def _guard_a2_icon2_body_takes_6__Ink6_r36c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c11(state):
    state.Ink6_r36c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r36c12(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c12  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c12(state):
    state.Ink6_r36c12_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r36c13(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c13  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c13(state):
    state.Ink6_r36c13_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r36c14(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c14  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c14(state):
    state.Ink6_r36c14_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r36c15(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c15  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c15(state):
    state.Ink6_r36c15_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r36c16(state, action):
    """a2_icon2_body_takes_6__Ink6_r36c16  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r36c16(state):
    state.Ink6_r36c16_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r37c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r37c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r37c11(state):
    state.Ink6_r37c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r37c16(state, action):
    """a2_icon2_body_takes_6__Ink6_r37c16  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r37c16(state):
    state.Ink6_r37c16_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r38c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r38c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r38c11(state):
    state.Ink6_r38c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r38c13(state, action):
    """a2_icon2_body_takes_6__Ink6_r38c13  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r38c13(state):
    state.Ink6_r38c13_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r38c14(state, action):
    """a2_icon2_body_takes_6__Ink6_r38c14  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r38c14(state):
    state.Ink6_r38c14_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r39c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r39c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r39c11(state):
    state.Ink6_r39c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r39c13(state, action):
    """a2_icon2_body_takes_6__Ink6_r39c13  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r39c13(state):
    state.Ink6_r39c13_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r39c14(state, action):
    """a2_icon2_body_takes_6__Ink6_r39c14  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r39c14(state):
    state.Ink6_r39c14_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r40c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r40c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r40c11(state):
    state.Ink6_r40c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r40c16(state, action):
    """a2_icon2_body_takes_6__Ink6_r40c16  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r40c16(state):
    state.Ink6_r40c16_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c11(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c11  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c11(state):
    state.Ink6_r41c11_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c12(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c12  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c12(state):
    state.Ink6_r41c12_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c13(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c13  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c13(state):
    state.Ink6_r41c13_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c14(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c14  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c14(state):
    state.Ink6_r41c14_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c15(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c15  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c15(state):
    state.Ink6_r41c15_color = 6


def _guard_a2_icon2_body_takes_6__Ink6_r41c16(state, action):
    """a2_icon2_body_takes_6__Ink6_r41c16  [ev: t2  cov: 22/22]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink6_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_a2_icon2_body_takes_6__Ink6_r41c16(state):
    state.Ink6_r41c16_color = 6


def _guard_a2_icon2_hole_takes_0__Ink0_r37c12(state, action):
    """a2_icon2_hole_takes_0__Ink0_r37c12  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r37c12(state):
    state.Ink0_r37c12_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r37c13(state, action):
    """a2_icon2_hole_takes_0__Ink0_r37c13  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r37c13(state):
    state.Ink0_r37c13_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r37c14(state, action):
    """a2_icon2_hole_takes_0__Ink0_r37c14  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r37c14(state):
    state.Ink0_r37c14_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r37c15(state, action):
    """a2_icon2_hole_takes_0__Ink0_r37c15  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r37c15(state):
    state.Ink0_r37c15_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r38c12(state, action):
    """a2_icon2_hole_takes_0__Ink0_r38c12  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r38c12(state):
    state.Ink0_r38c12_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r38c15(state, action):
    """a2_icon2_hole_takes_0__Ink0_r38c15  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r38c15(state):
    state.Ink0_r38c15_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r39c12(state, action):
    """a2_icon2_hole_takes_0__Ink0_r39c12  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r39c12(state):
    state.Ink0_r39c12_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r39c15(state, action):
    """a2_icon2_hole_takes_0__Ink0_r39c15  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r39c15(state):
    state.Ink0_r39c15_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r40c12(state, action):
    """a2_icon2_hole_takes_0__Ink0_r40c12  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r40c12(state):
    state.Ink0_r40c12_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r40c13(state, action):
    """a2_icon2_hole_takes_0__Ink0_r40c13  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r40c13(state):
    state.Ink0_r40c13_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r40c14(state, action):
    """a2_icon2_hole_takes_0__Ink0_r40c14  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r40c14(state):
    state.Ink0_r40c14_color = 0


def _guard_a2_icon2_hole_takes_0__Ink0_r40c15(state, action):
    """a2_icon2_hole_takes_0__Ink0_r40c15  [ev: t2  cov: 12/12]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink0_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_a2_icon2_hole_takes_0__Ink0_r40c15(state):
    state.Ink0_r40c15_color = 0


def _guard_a2_tape2_takes_1__Ink1_r38c16(state, action):
    """a2_tape2_takes_1__Ink1_r38c16  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 1


def _guard_a2_tape2_takes_1__Ink1_r38c18(state, action):
    """a2_tape2_takes_1__Ink1_r38c18  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 1


def _guard_a2_tape2_takes_1__Ink1_r38c19(state, action):
    """a2_tape2_takes_1__Ink1_r38c19  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 1


def _guard_a2_tape2_takes_1__Ink1_r38c21(state, action):
    """a2_tape2_takes_1__Ink1_r38c21  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 1


def _guard_a2_tape2_takes_1__Ink1_r38c22(state, action):
    """a2_tape2_takes_1__Ink1_r38c22  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 1


def _guard_a2_tape2_takes_1__Ink1_r39c17(state, action):
    """a2_tape2_takes_1__Ink1_r39c17  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 1


def _guard_a2_tape2_takes_1__Ink1_r39c18(state, action):
    """a2_tape2_takes_1__Ink1_r39c18  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 1


def _guard_a2_tape2_takes_1__Ink1_r39c20(state, action):
    """a2_tape2_takes_1__Ink1_r39c20  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 1


def _guard_a2_tape2_takes_1__Ink1_r39c21(state, action):
    """a2_tape2_takes_1__Ink1_r39c21  [ev: t2  cov: 9/9]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_a2_tape2_takes_1__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 1


def _guard_a3_hides_tape2_ones__Ink1_r38c16(state, action):
    """a3_hides_tape2_ones__Ink1_r38c16  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r38c18(state, action):
    """a3_hides_tape2_ones__Ink1_r38c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r38c19(state, action):
    """a3_hides_tape2_ones__Ink1_r38c19  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r38c21(state, action):
    """a3_hides_tape2_ones__Ink1_r38c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r38c22(state, action):
    """a3_hides_tape2_ones__Ink1_r38c22  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r39c17(state, action):
    """a3_hides_tape2_ones__Ink1_r39c17  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r39c18(state, action):
    """a3_hides_tape2_ones__Ink1_r39c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r39c20(state, action):
    """a3_hides_tape2_ones__Ink1_r39c20  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 4


def _guard_a3_hides_tape2_ones__Ink1_r39c21(state, action):
    """a3_hides_tape2_ones__Ink1_r39c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_ones__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r32c13(state, action):
    """a3_hides_tape2_twos__Ink2_r32c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r32c14(state, action):
    """a3_hides_tape2_twos__Ink2_r32c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r33c13(state, action):
    """a3_hides_tape2_twos__Ink2_r33c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r33c14(state, action):
    """a3_hides_tape2_twos__Ink2_r33c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r38c17(state, action):
    """a3_hides_tape2_twos__Ink2_r38c17  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r38c20(state, action):
    """a3_hides_tape2_twos__Ink2_r38c20  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r39c16(state, action):
    """a3_hides_tape2_twos__Ink2_r39c16  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r39c19(state, action):
    """a3_hides_tape2_twos__Ink2_r39c19  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r39c22(state, action):
    """a3_hides_tape2_twos__Ink2_r39c22  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 4


def _guard_a3_hides_tape2_twos__Ink2_r53c63(state, action):
    """a3_hides_tape2_twos__Ink2_r53c63  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a3_hides_tape2_twos__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r38c16(state, action):
    """a7_hides_tape2_ones__Ink1_r38c16  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r38c18(state, action):
    """a7_hides_tape2_ones__Ink1_r38c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r38c19(state, action):
    """a7_hides_tape2_ones__Ink1_r38c19  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r38c21(state, action):
    """a7_hides_tape2_ones__Ink1_r38c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r38c22(state, action):
    """a7_hides_tape2_ones__Ink1_r38c22  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r39c17(state, action):
    """a7_hides_tape2_ones__Ink1_r39c17  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r39c18(state, action):
    """a7_hides_tape2_ones__Ink1_r39c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r39c20(state, action):
    """a7_hides_tape2_ones__Ink1_r39c20  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 4


def _guard_a7_hides_tape2_ones__Ink1_r39c21(state, action):
    """a7_hides_tape2_ones__Ink1_r39c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_ones__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r32c13(state, action):
    """a7_hides_tape2_twos__Ink2_r32c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r32c14(state, action):
    """a7_hides_tape2_twos__Ink2_r32c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r33c13(state, action):
    """a7_hides_tape2_twos__Ink2_r33c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r33c14(state, action):
    """a7_hides_tape2_twos__Ink2_r33c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r38c17(state, action):
    """a7_hides_tape2_twos__Ink2_r38c17  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r38c20(state, action):
    """a7_hides_tape2_twos__Ink2_r38c20  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r39c16(state, action):
    """a7_hides_tape2_twos__Ink2_r39c16  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r39c19(state, action):
    """a7_hides_tape2_twos__Ink2_r39c19  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r39c22(state, action):
    """a7_hides_tape2_twos__Ink2_r39c22  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 4


def _guard_a7_hides_tape2_twos__Ink2_r53c63(state, action):
    """a7_hides_tape2_twos__Ink2_r53c63  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a7_hides_tape2_twos__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 4


def _guard_a4_shows_tape2_ones__Ink1_r38c16(state, action):
    """a4_shows_tape2_ones__Ink1_r38c16  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c16_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r38c16(state):
    state.Ink1_r38c16_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r38c18(state, action):
    """a4_shows_tape2_ones__Ink1_r38c18  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r38c18(state):
    state.Ink1_r38c18_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r38c19(state, action):
    """a4_shows_tape2_ones__Ink1_r38c19  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r38c19(state):
    state.Ink1_r38c19_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r38c21(state, action):
    """a4_shows_tape2_ones__Ink1_r38c21  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r38c21(state):
    state.Ink1_r38c21_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r38c22(state, action):
    """a4_shows_tape2_ones__Ink1_r38c22  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r38c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r38c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r38c22(state):
    state.Ink1_r38c22_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r39c17(state, action):
    """a4_shows_tape2_ones__Ink1_r39c17  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r39c17(state):
    state.Ink1_r39c17_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r39c18(state, action):
    """a4_shows_tape2_ones__Ink1_r39c18  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c18_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r39c18(state):
    state.Ink1_r39c18_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r39c20(state, action):
    """a4_shows_tape2_ones__Ink1_r39c20  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r39c20(state):
    state.Ink1_r39c20_color = 1


def _guard_a4_shows_tape2_ones__Ink1_r39c21(state, action):
    """a4_shows_tape2_ones__Ink1_r39c21  [ev: t4  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink1_r39c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink1_r39c21_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_ones__Ink1_r39c21(state):
    state.Ink1_r39c21_color = 1


def _guard_a4_shows_tape2_twos__Ink2_r32c13(state, action):
    """a4_shows_tape2_twos__Ink2_r32c13  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r32c14(state, action):
    """a4_shows_tape2_twos__Ink2_r32c14  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r32c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r33c13(state, action):
    """a4_shows_tape2_twos__Ink2_r33c13  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c13_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r33c14(state, action):
    """a4_shows_tape2_twos__Ink2_r33c14  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r33c14_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r38c17(state, action):
    """a4_shows_tape2_twos__Ink2_r38c17  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c17_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r38c20(state, action):
    """a4_shows_tape2_twos__Ink2_r38c20  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r38c20_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r39c16(state, action):
    """a4_shows_tape2_twos__Ink2_r39c16  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c16_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r39c19(state, action):
    """a4_shows_tape2_twos__Ink2_r39c19  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c19_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r39c22(state, action):
    """a4_shows_tape2_twos__Ink2_r39c22  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r39c22_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 2


def _guard_a4_shows_tape2_twos__Ink2_r53c63(state, action):
    """a4_shows_tape2_twos__Ink2_r53c63  [ev: t4  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Ink2_r53c63_pos, 'up'), 'up')) == 4): return False
    return True


def _effect_a4_shows_tape2_twos__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 2


def _guard_a4_advances_the_corner_pixel__Ink2_r32c13(state, action):
    """a4_advances_the_corner_pixel__Ink2_r32c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r32c13_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r32c13(state):
    state.Ink2_r32c13_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r32c14(state, action):
    """a4_advances_the_corner_pixel__Ink2_r32c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r32c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r32c14_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r32c14(state):
    state.Ink2_r32c14_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r33c13(state, action):
    """a4_advances_the_corner_pixel__Ink2_r33c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r33c13_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r33c13(state):
    state.Ink2_r33c13_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r33c14(state, action):
    """a4_advances_the_corner_pixel__Ink2_r33c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r33c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r33c14_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r33c14(state):
    state.Ink2_r33c14_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r38c17(state, action):
    """a4_advances_the_corner_pixel__Ink2_r38c17  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c17_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r38c17_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r38c17(state):
    state.Ink2_r38c17_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r38c20(state, action):
    """a4_advances_the_corner_pixel__Ink2_r38c20  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r38c20_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r38c20_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r38c20(state):
    state.Ink2_r38c20_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r39c16(state, action):
    """a4_advances_the_corner_pixel__Ink2_r39c16  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c16_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c16_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r39c16(state):
    state.Ink2_r39c16_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r39c19(state, action):
    """a4_advances_the_corner_pixel__Ink2_r39c19  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c19_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c19_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r39c19(state):
    state.Ink2_r39c19_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r39c22(state, action):
    """a4_advances_the_corner_pixel__Ink2_r39c22  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r39c22_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r39c22_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r39c22(state):
    state.Ink2_r39c22_color = 3


def _guard_a4_advances_the_corner_pixel__Ink2_r53c63(state, action):
    """a4_advances_the_corner_pixel__Ink2_r53c63  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Ink2_r53c63_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.Ink2_r53c63_pos, 'right'))): return False
    return True


def _effect_a4_advances_the_corner_pixel__Ink2_r53c63(state):
    state.Ink2_r53c63_color = 3


RULES = [
    ('a1_icon1_field_takes_6__Ink5_r30c11', _guard_a1_icon1_field_takes_6__Ink5_r30c11, _effect_a1_icon1_field_takes_6__Ink5_r30c11, ['Ink5_r30c11']),
    ('a1_icon1_field_takes_6__Ink5_r30c12', _guard_a1_icon1_field_takes_6__Ink5_r30c12, _effect_a1_icon1_field_takes_6__Ink5_r30c12, ['Ink5_r30c12']),
    ('a1_icon1_field_takes_6__Ink5_r30c15', _guard_a1_icon1_field_takes_6__Ink5_r30c15, _effect_a1_icon1_field_takes_6__Ink5_r30c15, ['Ink5_r30c15']),
    ('a1_icon1_field_takes_6__Ink5_r30c16', _guard_a1_icon1_field_takes_6__Ink5_r30c16, _effect_a1_icon1_field_takes_6__Ink5_r30c16, ['Ink5_r30c16']),
    ('a1_icon1_field_takes_6__Ink5_r31c11', _guard_a1_icon1_field_takes_6__Ink5_r31c11, _effect_a1_icon1_field_takes_6__Ink5_r31c11, ['Ink5_r31c11']),
    ('a1_icon1_field_takes_6__Ink5_r31c12', _guard_a1_icon1_field_takes_6__Ink5_r31c12, _effect_a1_icon1_field_takes_6__Ink5_r31c12, ['Ink5_r31c12']),
    ('a1_icon1_field_takes_6__Ink5_r31c15', _guard_a1_icon1_field_takes_6__Ink5_r31c15, _effect_a1_icon1_field_takes_6__Ink5_r31c15, ['Ink5_r31c15']),
    ('a1_icon1_field_takes_6__Ink5_r31c16', _guard_a1_icon1_field_takes_6__Ink5_r31c16, _effect_a1_icon1_field_takes_6__Ink5_r31c16, ['Ink5_r31c16']),
    ('a1_icon1_field_takes_6__Ink5_r32c11', _guard_a1_icon1_field_takes_6__Ink5_r32c11, _effect_a1_icon1_field_takes_6__Ink5_r32c11, ['Ink5_r32c11']),
    ('a1_icon1_field_takes_6__Ink5_r32c12', _guard_a1_icon1_field_takes_6__Ink5_r32c12, _effect_a1_icon1_field_takes_6__Ink5_r32c12, ['Ink5_r32c12']),
    ('a1_icon1_field_takes_6__Ink5_r32c15', _guard_a1_icon1_field_takes_6__Ink5_r32c15, _effect_a1_icon1_field_takes_6__Ink5_r32c15, ['Ink5_r32c15']),
    ('a1_icon1_field_takes_6__Ink5_r32c16', _guard_a1_icon1_field_takes_6__Ink5_r32c16, _effect_a1_icon1_field_takes_6__Ink5_r32c16, ['Ink5_r32c16']),
    ('a1_icon1_field_takes_6__Ink5_r33c11', _guard_a1_icon1_field_takes_6__Ink5_r33c11, _effect_a1_icon1_field_takes_6__Ink5_r33c11, ['Ink5_r33c11']),
    ('a1_icon1_field_takes_6__Ink5_r33c12', _guard_a1_icon1_field_takes_6__Ink5_r33c12, _effect_a1_icon1_field_takes_6__Ink5_r33c12, ['Ink5_r33c12']),
    ('a1_icon1_field_takes_6__Ink5_r33c15', _guard_a1_icon1_field_takes_6__Ink5_r33c15, _effect_a1_icon1_field_takes_6__Ink5_r33c15, ['Ink5_r33c15']),
    ('a1_icon1_field_takes_6__Ink5_r33c16', _guard_a1_icon1_field_takes_6__Ink5_r33c16, _effect_a1_icon1_field_takes_6__Ink5_r33c16, ['Ink5_r33c16']),
    ('a1_icon1_field_takes_6__Ink5_r34c11', _guard_a1_icon1_field_takes_6__Ink5_r34c11, _effect_a1_icon1_field_takes_6__Ink5_r34c11, ['Ink5_r34c11']),
    ('a1_icon1_field_takes_6__Ink5_r34c12', _guard_a1_icon1_field_takes_6__Ink5_r34c12, _effect_a1_icon1_field_takes_6__Ink5_r34c12, ['Ink5_r34c12']),
    ('a1_icon1_field_takes_6__Ink5_r34c15', _guard_a1_icon1_field_takes_6__Ink5_r34c15, _effect_a1_icon1_field_takes_6__Ink5_r34c15, ['Ink5_r34c15']),
    ('a1_icon1_field_takes_6__Ink5_r34c16', _guard_a1_icon1_field_takes_6__Ink5_r34c16, _effect_a1_icon1_field_takes_6__Ink5_r34c16, ['Ink5_r34c16']),
    ('a1_icon1_field_takes_6__Ink5_r35c11', _guard_a1_icon1_field_takes_6__Ink5_r35c11, _effect_a1_icon1_field_takes_6__Ink5_r35c11, ['Ink5_r35c11']),
    ('a1_icon1_field_takes_6__Ink5_r35c12', _guard_a1_icon1_field_takes_6__Ink5_r35c12, _effect_a1_icon1_field_takes_6__Ink5_r35c12, ['Ink5_r35c12']),
    ('a1_icon1_field_takes_6__Ink5_r35c15', _guard_a1_icon1_field_takes_6__Ink5_r35c15, _effect_a1_icon1_field_takes_6__Ink5_r35c15, ['Ink5_r35c15']),
    ('a1_icon1_field_takes_6__Ink5_r35c16', _guard_a1_icon1_field_takes_6__Ink5_r35c16, _effect_a1_icon1_field_takes_6__Ink5_r35c16, ['Ink5_r35c16']),
    ('a1_icon1_field_takes_0__Ink5_r30c11', _guard_a1_icon1_field_takes_0__Ink5_r30c11, _effect_a1_icon1_field_takes_0__Ink5_r30c11, ['Ink5_r30c11']),
    ('a1_icon1_field_takes_0__Ink5_r30c12', _guard_a1_icon1_field_takes_0__Ink5_r30c12, _effect_a1_icon1_field_takes_0__Ink5_r30c12, ['Ink5_r30c12']),
    ('a1_icon1_field_takes_0__Ink5_r30c15', _guard_a1_icon1_field_takes_0__Ink5_r30c15, _effect_a1_icon1_field_takes_0__Ink5_r30c15, ['Ink5_r30c15']),
    ('a1_icon1_field_takes_0__Ink5_r30c16', _guard_a1_icon1_field_takes_0__Ink5_r30c16, _effect_a1_icon1_field_takes_0__Ink5_r30c16, ['Ink5_r30c16']),
    ('a1_icon1_field_takes_0__Ink5_r31c11', _guard_a1_icon1_field_takes_0__Ink5_r31c11, _effect_a1_icon1_field_takes_0__Ink5_r31c11, ['Ink5_r31c11']),
    ('a1_icon1_field_takes_0__Ink5_r31c12', _guard_a1_icon1_field_takes_0__Ink5_r31c12, _effect_a1_icon1_field_takes_0__Ink5_r31c12, ['Ink5_r31c12']),
    ('a1_icon1_field_takes_0__Ink5_r31c15', _guard_a1_icon1_field_takes_0__Ink5_r31c15, _effect_a1_icon1_field_takes_0__Ink5_r31c15, ['Ink5_r31c15']),
    ('a1_icon1_field_takes_0__Ink5_r31c16', _guard_a1_icon1_field_takes_0__Ink5_r31c16, _effect_a1_icon1_field_takes_0__Ink5_r31c16, ['Ink5_r31c16']),
    ('a1_icon1_field_takes_0__Ink5_r32c11', _guard_a1_icon1_field_takes_0__Ink5_r32c11, _effect_a1_icon1_field_takes_0__Ink5_r32c11, ['Ink5_r32c11']),
    ('a1_icon1_field_takes_0__Ink5_r32c12', _guard_a1_icon1_field_takes_0__Ink5_r32c12, _effect_a1_icon1_field_takes_0__Ink5_r32c12, ['Ink5_r32c12']),
    ('a1_icon1_field_takes_0__Ink5_r32c15', _guard_a1_icon1_field_takes_0__Ink5_r32c15, _effect_a1_icon1_field_takes_0__Ink5_r32c15, ['Ink5_r32c15']),
    ('a1_icon1_field_takes_0__Ink5_r32c16', _guard_a1_icon1_field_takes_0__Ink5_r32c16, _effect_a1_icon1_field_takes_0__Ink5_r32c16, ['Ink5_r32c16']),
    ('a1_icon1_field_takes_0__Ink5_r33c11', _guard_a1_icon1_field_takes_0__Ink5_r33c11, _effect_a1_icon1_field_takes_0__Ink5_r33c11, ['Ink5_r33c11']),
    ('a1_icon1_field_takes_0__Ink5_r33c12', _guard_a1_icon1_field_takes_0__Ink5_r33c12, _effect_a1_icon1_field_takes_0__Ink5_r33c12, ['Ink5_r33c12']),
    ('a1_icon1_field_takes_0__Ink5_r33c15', _guard_a1_icon1_field_takes_0__Ink5_r33c15, _effect_a1_icon1_field_takes_0__Ink5_r33c15, ['Ink5_r33c15']),
    ('a1_icon1_field_takes_0__Ink5_r33c16', _guard_a1_icon1_field_takes_0__Ink5_r33c16, _effect_a1_icon1_field_takes_0__Ink5_r33c16, ['Ink5_r33c16']),
    ('a1_icon1_field_takes_0__Ink5_r34c11', _guard_a1_icon1_field_takes_0__Ink5_r34c11, _effect_a1_icon1_field_takes_0__Ink5_r34c11, ['Ink5_r34c11']),
    ('a1_icon1_field_takes_0__Ink5_r34c12', _guard_a1_icon1_field_takes_0__Ink5_r34c12, _effect_a1_icon1_field_takes_0__Ink5_r34c12, ['Ink5_r34c12']),
    ('a1_icon1_field_takes_0__Ink5_r34c15', _guard_a1_icon1_field_takes_0__Ink5_r34c15, _effect_a1_icon1_field_takes_0__Ink5_r34c15, ['Ink5_r34c15']),
    ('a1_icon1_field_takes_0__Ink5_r34c16', _guard_a1_icon1_field_takes_0__Ink5_r34c16, _effect_a1_icon1_field_takes_0__Ink5_r34c16, ['Ink5_r34c16']),
    ('a1_icon1_field_takes_0__Ink5_r35c11', _guard_a1_icon1_field_takes_0__Ink5_r35c11, _effect_a1_icon1_field_takes_0__Ink5_r35c11, ['Ink5_r35c11']),
    ('a1_icon1_field_takes_0__Ink5_r35c12', _guard_a1_icon1_field_takes_0__Ink5_r35c12, _effect_a1_icon1_field_takes_0__Ink5_r35c12, ['Ink5_r35c12']),
    ('a1_icon1_field_takes_0__Ink5_r35c15', _guard_a1_icon1_field_takes_0__Ink5_r35c15, _effect_a1_icon1_field_takes_0__Ink5_r35c15, ['Ink5_r35c15']),
    ('a1_icon1_field_takes_0__Ink5_r35c16', _guard_a1_icon1_field_takes_0__Ink5_r35c16, _effect_a1_icon1_field_takes_0__Ink5_r35c16, ['Ink5_r35c16']),
    ('a1_icon1_field_takes_1__Ink5_r30c11', _guard_a1_icon1_field_takes_1__Ink5_r30c11, _effect_a1_icon1_field_takes_1__Ink5_r30c11, ['Ink5_r30c11']),
    ('a1_icon1_field_takes_1__Ink5_r30c12', _guard_a1_icon1_field_takes_1__Ink5_r30c12, _effect_a1_icon1_field_takes_1__Ink5_r30c12, ['Ink5_r30c12']),
    ('a1_icon1_field_takes_1__Ink5_r30c15', _guard_a1_icon1_field_takes_1__Ink5_r30c15, _effect_a1_icon1_field_takes_1__Ink5_r30c15, ['Ink5_r30c15']),
    ('a1_icon1_field_takes_1__Ink5_r30c16', _guard_a1_icon1_field_takes_1__Ink5_r30c16, _effect_a1_icon1_field_takes_1__Ink5_r30c16, ['Ink5_r30c16']),
    ('a1_icon1_field_takes_1__Ink5_r31c11', _guard_a1_icon1_field_takes_1__Ink5_r31c11, _effect_a1_icon1_field_takes_1__Ink5_r31c11, ['Ink5_r31c11']),
    ('a1_icon1_field_takes_1__Ink5_r31c12', _guard_a1_icon1_field_takes_1__Ink5_r31c12, _effect_a1_icon1_field_takes_1__Ink5_r31c12, ['Ink5_r31c12']),
    ('a1_icon1_field_takes_1__Ink5_r31c15', _guard_a1_icon1_field_takes_1__Ink5_r31c15, _effect_a1_icon1_field_takes_1__Ink5_r31c15, ['Ink5_r31c15']),
    ('a1_icon1_field_takes_1__Ink5_r31c16', _guard_a1_icon1_field_takes_1__Ink5_r31c16, _effect_a1_icon1_field_takes_1__Ink5_r31c16, ['Ink5_r31c16']),
    ('a1_icon1_field_takes_1__Ink5_r32c11', _guard_a1_icon1_field_takes_1__Ink5_r32c11, _effect_a1_icon1_field_takes_1__Ink5_r32c11, ['Ink5_r32c11']),
    ('a1_icon1_field_takes_1__Ink5_r32c12', _guard_a1_icon1_field_takes_1__Ink5_r32c12, _effect_a1_icon1_field_takes_1__Ink5_r32c12, ['Ink5_r32c12']),
    ('a1_icon1_field_takes_1__Ink5_r32c15', _guard_a1_icon1_field_takes_1__Ink5_r32c15, _effect_a1_icon1_field_takes_1__Ink5_r32c15, ['Ink5_r32c15']),
    ('a1_icon1_field_takes_1__Ink5_r32c16', _guard_a1_icon1_field_takes_1__Ink5_r32c16, _effect_a1_icon1_field_takes_1__Ink5_r32c16, ['Ink5_r32c16']),
    ('a1_icon1_field_takes_1__Ink5_r33c11', _guard_a1_icon1_field_takes_1__Ink5_r33c11, _effect_a1_icon1_field_takes_1__Ink5_r33c11, ['Ink5_r33c11']),
    ('a1_icon1_field_takes_1__Ink5_r33c12', _guard_a1_icon1_field_takes_1__Ink5_r33c12, _effect_a1_icon1_field_takes_1__Ink5_r33c12, ['Ink5_r33c12']),
    ('a1_icon1_field_takes_1__Ink5_r33c15', _guard_a1_icon1_field_takes_1__Ink5_r33c15, _effect_a1_icon1_field_takes_1__Ink5_r33c15, ['Ink5_r33c15']),
    ('a1_icon1_field_takes_1__Ink5_r33c16', _guard_a1_icon1_field_takes_1__Ink5_r33c16, _effect_a1_icon1_field_takes_1__Ink5_r33c16, ['Ink5_r33c16']),
    ('a1_icon1_field_takes_1__Ink5_r34c11', _guard_a1_icon1_field_takes_1__Ink5_r34c11, _effect_a1_icon1_field_takes_1__Ink5_r34c11, ['Ink5_r34c11']),
    ('a1_icon1_field_takes_1__Ink5_r34c12', _guard_a1_icon1_field_takes_1__Ink5_r34c12, _effect_a1_icon1_field_takes_1__Ink5_r34c12, ['Ink5_r34c12']),
    ('a1_icon1_field_takes_1__Ink5_r34c15', _guard_a1_icon1_field_takes_1__Ink5_r34c15, _effect_a1_icon1_field_takes_1__Ink5_r34c15, ['Ink5_r34c15']),
    ('a1_icon1_field_takes_1__Ink5_r34c16', _guard_a1_icon1_field_takes_1__Ink5_r34c16, _effect_a1_icon1_field_takes_1__Ink5_r34c16, ['Ink5_r34c16']),
    ('a1_icon1_field_takes_1__Ink5_r35c11', _guard_a1_icon1_field_takes_1__Ink5_r35c11, _effect_a1_icon1_field_takes_1__Ink5_r35c11, ['Ink5_r35c11']),
    ('a1_icon1_field_takes_1__Ink5_r35c12', _guard_a1_icon1_field_takes_1__Ink5_r35c12, _effect_a1_icon1_field_takes_1__Ink5_r35c12, ['Ink5_r35c12']),
    ('a1_icon1_field_takes_1__Ink5_r35c15', _guard_a1_icon1_field_takes_1__Ink5_r35c15, _effect_a1_icon1_field_takes_1__Ink5_r35c15, ['Ink5_r35c15']),
    ('a1_icon1_field_takes_1__Ink5_r35c16', _guard_a1_icon1_field_takes_1__Ink5_r35c16, _effect_a1_icon1_field_takes_1__Ink5_r35c16, ['Ink5_r35c16']),
    ('a1_icon1_field_takes_2__Ink5_r30c11', _guard_a1_icon1_field_takes_2__Ink5_r30c11, _effect_a1_icon1_field_takes_2__Ink5_r30c11, ['Ink5_r30c11']),
    ('a1_icon1_field_takes_2__Ink5_r30c12', _guard_a1_icon1_field_takes_2__Ink5_r30c12, _effect_a1_icon1_field_takes_2__Ink5_r30c12, ['Ink5_r30c12']),
    ('a1_icon1_field_takes_2__Ink5_r30c15', _guard_a1_icon1_field_takes_2__Ink5_r30c15, _effect_a1_icon1_field_takes_2__Ink5_r30c15, ['Ink5_r30c15']),
    ('a1_icon1_field_takes_2__Ink5_r30c16', _guard_a1_icon1_field_takes_2__Ink5_r30c16, _effect_a1_icon1_field_takes_2__Ink5_r30c16, ['Ink5_r30c16']),
    ('a1_icon1_field_takes_2__Ink5_r31c11', _guard_a1_icon1_field_takes_2__Ink5_r31c11, _effect_a1_icon1_field_takes_2__Ink5_r31c11, ['Ink5_r31c11']),
    ('a1_icon1_field_takes_2__Ink5_r31c12', _guard_a1_icon1_field_takes_2__Ink5_r31c12, _effect_a1_icon1_field_takes_2__Ink5_r31c12, ['Ink5_r31c12']),
    ('a1_icon1_field_takes_2__Ink5_r31c15', _guard_a1_icon1_field_takes_2__Ink5_r31c15, _effect_a1_icon1_field_takes_2__Ink5_r31c15, ['Ink5_r31c15']),
    ('a1_icon1_field_takes_2__Ink5_r31c16', _guard_a1_icon1_field_takes_2__Ink5_r31c16, _effect_a1_icon1_field_takes_2__Ink5_r31c16, ['Ink5_r31c16']),
    ('a1_icon1_field_takes_2__Ink5_r32c11', _guard_a1_icon1_field_takes_2__Ink5_r32c11, _effect_a1_icon1_field_takes_2__Ink5_r32c11, ['Ink5_r32c11']),
    ('a1_icon1_field_takes_2__Ink5_r32c12', _guard_a1_icon1_field_takes_2__Ink5_r32c12, _effect_a1_icon1_field_takes_2__Ink5_r32c12, ['Ink5_r32c12']),
    ('a1_icon1_field_takes_2__Ink5_r32c15', _guard_a1_icon1_field_takes_2__Ink5_r32c15, _effect_a1_icon1_field_takes_2__Ink5_r32c15, ['Ink5_r32c15']),
    ('a1_icon1_field_takes_2__Ink5_r32c16', _guard_a1_icon1_field_takes_2__Ink5_r32c16, _effect_a1_icon1_field_takes_2__Ink5_r32c16, ['Ink5_r32c16']),
    ('a1_icon1_field_takes_2__Ink5_r33c11', _guard_a1_icon1_field_takes_2__Ink5_r33c11, _effect_a1_icon1_field_takes_2__Ink5_r33c11, ['Ink5_r33c11']),
    ('a1_icon1_field_takes_2__Ink5_r33c12', _guard_a1_icon1_field_takes_2__Ink5_r33c12, _effect_a1_icon1_field_takes_2__Ink5_r33c12, ['Ink5_r33c12']),
    ('a1_icon1_field_takes_2__Ink5_r33c15', _guard_a1_icon1_field_takes_2__Ink5_r33c15, _effect_a1_icon1_field_takes_2__Ink5_r33c15, ['Ink5_r33c15']),
    ('a1_icon1_field_takes_2__Ink5_r33c16', _guard_a1_icon1_field_takes_2__Ink5_r33c16, _effect_a1_icon1_field_takes_2__Ink5_r33c16, ['Ink5_r33c16']),
    ('a1_icon1_field_takes_2__Ink5_r34c11', _guard_a1_icon1_field_takes_2__Ink5_r34c11, _effect_a1_icon1_field_takes_2__Ink5_r34c11, ['Ink5_r34c11']),
    ('a1_icon1_field_takes_2__Ink5_r34c12', _guard_a1_icon1_field_takes_2__Ink5_r34c12, _effect_a1_icon1_field_takes_2__Ink5_r34c12, ['Ink5_r34c12']),
    ('a1_icon1_field_takes_2__Ink5_r34c15', _guard_a1_icon1_field_takes_2__Ink5_r34c15, _effect_a1_icon1_field_takes_2__Ink5_r34c15, ['Ink5_r34c15']),
    ('a1_icon1_field_takes_2__Ink5_r34c16', _guard_a1_icon1_field_takes_2__Ink5_r34c16, _effect_a1_icon1_field_takes_2__Ink5_r34c16, ['Ink5_r34c16']),
    ('a1_icon1_field_takes_2__Ink5_r35c11', _guard_a1_icon1_field_takes_2__Ink5_r35c11, _effect_a1_icon1_field_takes_2__Ink5_r35c11, ['Ink5_r35c11']),
    ('a1_icon1_field_takes_2__Ink5_r35c12', _guard_a1_icon1_field_takes_2__Ink5_r35c12, _effect_a1_icon1_field_takes_2__Ink5_r35c12, ['Ink5_r35c12']),
    ('a1_icon1_field_takes_2__Ink5_r35c15', _guard_a1_icon1_field_takes_2__Ink5_r35c15, _effect_a1_icon1_field_takes_2__Ink5_r35c15, ['Ink5_r35c15']),
    ('a1_icon1_field_takes_2__Ink5_r35c16', _guard_a1_icon1_field_takes_2__Ink5_r35c16, _effect_a1_icon1_field_takes_2__Ink5_r35c16, ['Ink5_r35c16']),
    ('a1_track_takes_6__Ink3_r30c13', _guard_a1_track_takes_6__Ink3_r30c13, _effect_a1_track_takes_6__Ink3_r30c13, ['Ink3_r30c13']),
    ('a1_track_takes_6__Ink3_r30c14', _guard_a1_track_takes_6__Ink3_r30c14, _effect_a1_track_takes_6__Ink3_r30c14, ['Ink3_r30c14']),
    ('a1_track_takes_6__Ink3_r31c13', _guard_a1_track_takes_6__Ink3_r31c13, _effect_a1_track_takes_6__Ink3_r31c13, ['Ink3_r31c13']),
    ('a1_track_takes_6__Ink3_r31c14', _guard_a1_track_takes_6__Ink3_r31c14, _effect_a1_track_takes_6__Ink3_r31c14, ['Ink3_r31c14']),
    ('a1_track_takes_6__Ink3_r34c13', _guard_a1_track_takes_6__Ink3_r34c13, _effect_a1_track_takes_6__Ink3_r34c13, ['Ink3_r34c13']),
    ('a1_track_takes_6__Ink3_r34c14', _guard_a1_track_takes_6__Ink3_r34c14, _effect_a1_track_takes_6__Ink3_r34c14, ['Ink3_r34c14']),
    ('a1_track_takes_6__Ink3_r35c13', _guard_a1_track_takes_6__Ink3_r35c13, _effect_a1_track_takes_6__Ink3_r35c13, ['Ink3_r35c13']),
    ('a1_track_takes_6__Ink3_r35c14', _guard_a1_track_takes_6__Ink3_r35c14, _effect_a1_track_takes_6__Ink3_r35c14, ['Ink3_r35c14']),
    ('a1_track_takes_0__Ink3_r30c13', _guard_a1_track_takes_0__Ink3_r30c13, _effect_a1_track_takes_0__Ink3_r30c13, ['Ink3_r30c13']),
    ('a1_track_takes_0__Ink3_r30c14', _guard_a1_track_takes_0__Ink3_r30c14, _effect_a1_track_takes_0__Ink3_r30c14, ['Ink3_r30c14']),
    ('a1_track_takes_0__Ink3_r31c13', _guard_a1_track_takes_0__Ink3_r31c13, _effect_a1_track_takes_0__Ink3_r31c13, ['Ink3_r31c13']),
    ('a1_track_takes_0__Ink3_r31c14', _guard_a1_track_takes_0__Ink3_r31c14, _effect_a1_track_takes_0__Ink3_r31c14, ['Ink3_r31c14']),
    ('a1_track_takes_0__Ink3_r34c13', _guard_a1_track_takes_0__Ink3_r34c13, _effect_a1_track_takes_0__Ink3_r34c13, ['Ink3_r34c13']),
    ('a1_track_takes_0__Ink3_r34c14', _guard_a1_track_takes_0__Ink3_r34c14, _effect_a1_track_takes_0__Ink3_r34c14, ['Ink3_r34c14']),
    ('a1_track_takes_0__Ink3_r35c13', _guard_a1_track_takes_0__Ink3_r35c13, _effect_a1_track_takes_0__Ink3_r35c13, ['Ink3_r35c13']),
    ('a1_track_takes_0__Ink3_r35c14', _guard_a1_track_takes_0__Ink3_r35c14, _effect_a1_track_takes_0__Ink3_r35c14, ['Ink3_r35c14']),
    ('a1_tape1_takes_2__Ink4_r32c17', _guard_a1_tape1_takes_2__Ink4_r32c17, _effect_a1_tape1_takes_2__Ink4_r32c17, ['Ink4_r32c17']),
    ('a1_tape1_takes_2__Ink4_r32c18', _guard_a1_tape1_takes_2__Ink4_r32c18, _effect_a1_tape1_takes_2__Ink4_r32c18, ['Ink4_r32c18']),
    ('a1_tape1_takes_2__Ink4_r32c19', _guard_a1_tape1_takes_2__Ink4_r32c19, _effect_a1_tape1_takes_2__Ink4_r32c19, ['Ink4_r32c19']),
    ('a1_tape1_takes_2__Ink4_r32c20', _guard_a1_tape1_takes_2__Ink4_r32c20, _effect_a1_tape1_takes_2__Ink4_r32c20, ['Ink4_r32c20']),
    ('a1_tape1_takes_2__Ink4_r32c21', _guard_a1_tape1_takes_2__Ink4_r32c21, _effect_a1_tape1_takes_2__Ink4_r32c21, ['Ink4_r32c21']),
    ('a1_tape1_takes_2__Ink4_r32c22', _guard_a1_tape1_takes_2__Ink4_r32c22, _effect_a1_tape1_takes_2__Ink4_r32c22, ['Ink4_r32c22']),
    ('a1_tape1_takes_2__Ink4_r33c17', _guard_a1_tape1_takes_2__Ink4_r33c17, _effect_a1_tape1_takes_2__Ink4_r33c17, ['Ink4_r33c17']),
    ('a1_tape1_takes_2__Ink4_r33c18', _guard_a1_tape1_takes_2__Ink4_r33c18, _effect_a1_tape1_takes_2__Ink4_r33c18, ['Ink4_r33c18']),
    ('a1_tape1_takes_2__Ink4_r33c19', _guard_a1_tape1_takes_2__Ink4_r33c19, _effect_a1_tape1_takes_2__Ink4_r33c19, ['Ink4_r33c19']),
    ('a1_tape1_takes_2__Ink4_r33c20', _guard_a1_tape1_takes_2__Ink4_r33c20, _effect_a1_tape1_takes_2__Ink4_r33c20, ['Ink4_r33c20']),
    ('a1_tape1_takes_2__Ink4_r33c21', _guard_a1_tape1_takes_2__Ink4_r33c21, _effect_a1_tape1_takes_2__Ink4_r33c21, ['Ink4_r33c21']),
    ('a1_tape1_takes_2__Ink4_r33c22', _guard_a1_tape1_takes_2__Ink4_r33c22, _effect_a1_tape1_takes_2__Ink4_r33c22, ['Ink4_r33c22']),
    ('a1_tape1_takes_1__Ink4_r32c17', _guard_a1_tape1_takes_1__Ink4_r32c17, _effect_a1_tape1_takes_1__Ink4_r32c17, ['Ink4_r32c17']),
    ('a1_tape1_takes_1__Ink4_r32c18', _guard_a1_tape1_takes_1__Ink4_r32c18, _effect_a1_tape1_takes_1__Ink4_r32c18, ['Ink4_r32c18']),
    ('a1_tape1_takes_1__Ink4_r32c19', _guard_a1_tape1_takes_1__Ink4_r32c19, _effect_a1_tape1_takes_1__Ink4_r32c19, ['Ink4_r32c19']),
    ('a1_tape1_takes_1__Ink4_r32c20', _guard_a1_tape1_takes_1__Ink4_r32c20, _effect_a1_tape1_takes_1__Ink4_r32c20, ['Ink4_r32c20']),
    ('a1_tape1_takes_1__Ink4_r32c21', _guard_a1_tape1_takes_1__Ink4_r32c21, _effect_a1_tape1_takes_1__Ink4_r32c21, ['Ink4_r32c21']),
    ('a1_tape1_takes_1__Ink4_r32c22', _guard_a1_tape1_takes_1__Ink4_r32c22, _effect_a1_tape1_takes_1__Ink4_r32c22, ['Ink4_r32c22']),
    ('a1_tape1_takes_1__Ink4_r33c17', _guard_a1_tape1_takes_1__Ink4_r33c17, _effect_a1_tape1_takes_1__Ink4_r33c17, ['Ink4_r33c17']),
    ('a1_tape1_takes_1__Ink4_r33c18', _guard_a1_tape1_takes_1__Ink4_r33c18, _effect_a1_tape1_takes_1__Ink4_r33c18, ['Ink4_r33c18']),
    ('a1_tape1_takes_1__Ink4_r33c19', _guard_a1_tape1_takes_1__Ink4_r33c19, _effect_a1_tape1_takes_1__Ink4_r33c19, ['Ink4_r33c19']),
    ('a1_tape1_takes_1__Ink4_r33c20', _guard_a1_tape1_takes_1__Ink4_r33c20, _effect_a1_tape1_takes_1__Ink4_r33c20, ['Ink4_r33c20']),
    ('a1_tape1_takes_1__Ink4_r33c21', _guard_a1_tape1_takes_1__Ink4_r33c21, _effect_a1_tape1_takes_1__Ink4_r33c21, ['Ink4_r33c21']),
    ('a1_tape1_takes_1__Ink4_r33c22', _guard_a1_tape1_takes_1__Ink4_r33c22, _effect_a1_tape1_takes_1__Ink4_r33c22, ['Ink4_r33c22']),
    ('a1_thumb_takes_6__Ink2_r32c13', _guard_a1_thumb_takes_6__Ink2_r32c13, _effect_a1_thumb_takes_6__Ink2_r32c13, ['Ink2_r32c13']),
    ('a1_thumb_takes_6__Ink2_r32c14', _guard_a1_thumb_takes_6__Ink2_r32c14, _effect_a1_thumb_takes_6__Ink2_r32c14, ['Ink2_r32c14']),
    ('a1_thumb_takes_6__Ink2_r33c13', _guard_a1_thumb_takes_6__Ink2_r33c13, _effect_a1_thumb_takes_6__Ink2_r33c13, ['Ink2_r33c13']),
    ('a1_thumb_takes_6__Ink2_r33c14', _guard_a1_thumb_takes_6__Ink2_r33c14, _effect_a1_thumb_takes_6__Ink2_r33c14, ['Ink2_r33c14']),
    ('a1_thumb_takes_6__Ink2_r38c17', _guard_a1_thumb_takes_6__Ink2_r38c17, _effect_a1_thumb_takes_6__Ink2_r38c17, ['Ink2_r38c17']),
    ('a1_thumb_takes_6__Ink2_r38c20', _guard_a1_thumb_takes_6__Ink2_r38c20, _effect_a1_thumb_takes_6__Ink2_r38c20, ['Ink2_r38c20']),
    ('a1_thumb_takes_6__Ink2_r39c16', _guard_a1_thumb_takes_6__Ink2_r39c16, _effect_a1_thumb_takes_6__Ink2_r39c16, ['Ink2_r39c16']),
    ('a1_thumb_takes_6__Ink2_r39c19', _guard_a1_thumb_takes_6__Ink2_r39c19, _effect_a1_thumb_takes_6__Ink2_r39c19, ['Ink2_r39c19']),
    ('a1_thumb_takes_6__Ink2_r39c22', _guard_a1_thumb_takes_6__Ink2_r39c22, _effect_a1_thumb_takes_6__Ink2_r39c22, ['Ink2_r39c22']),
    ('a1_thumb_takes_6__Ink2_r53c63', _guard_a1_thumb_takes_6__Ink2_r53c63, _effect_a1_thumb_takes_6__Ink2_r53c63, ['Ink2_r53c63']),
    ('a1_lower_ink2_takes_4__Ink2_r32c13', _guard_a1_lower_ink2_takes_4__Ink2_r32c13, _effect_a1_lower_ink2_takes_4__Ink2_r32c13, ['Ink2_r32c13']),
    ('a1_lower_ink2_takes_4__Ink2_r32c14', _guard_a1_lower_ink2_takes_4__Ink2_r32c14, _effect_a1_lower_ink2_takes_4__Ink2_r32c14, ['Ink2_r32c14']),
    ('a1_lower_ink2_takes_4__Ink2_r33c13', _guard_a1_lower_ink2_takes_4__Ink2_r33c13, _effect_a1_lower_ink2_takes_4__Ink2_r33c13, ['Ink2_r33c13']),
    ('a1_lower_ink2_takes_4__Ink2_r33c14', _guard_a1_lower_ink2_takes_4__Ink2_r33c14, _effect_a1_lower_ink2_takes_4__Ink2_r33c14, ['Ink2_r33c14']),
    ('a1_lower_ink2_takes_4__Ink2_r38c17', _guard_a1_lower_ink2_takes_4__Ink2_r38c17, _effect_a1_lower_ink2_takes_4__Ink2_r38c17, ['Ink2_r38c17']),
    ('a1_lower_ink2_takes_4__Ink2_r38c20', _guard_a1_lower_ink2_takes_4__Ink2_r38c20, _effect_a1_lower_ink2_takes_4__Ink2_r38c20, ['Ink2_r38c20']),
    ('a1_lower_ink2_takes_4__Ink2_r39c16', _guard_a1_lower_ink2_takes_4__Ink2_r39c16, _effect_a1_lower_ink2_takes_4__Ink2_r39c16, ['Ink2_r39c16']),
    ('a1_lower_ink2_takes_4__Ink2_r39c19', _guard_a1_lower_ink2_takes_4__Ink2_r39c19, _effect_a1_lower_ink2_takes_4__Ink2_r39c19, ['Ink2_r39c19']),
    ('a1_lower_ink2_takes_4__Ink2_r39c22', _guard_a1_lower_ink2_takes_4__Ink2_r39c22, _effect_a1_lower_ink2_takes_4__Ink2_r39c22, ['Ink2_r39c22']),
    ('a1_lower_ink2_takes_4__Ink2_r53c63', _guard_a1_lower_ink2_takes_4__Ink2_r53c63, _effect_a1_lower_ink2_takes_4__Ink2_r53c63, ['Ink2_r53c63']),
    ('a1_lower_ink2_takes_5__Ink2_r32c13', _guard_a1_lower_ink2_takes_5__Ink2_r32c13, _effect_a1_lower_ink2_takes_5__Ink2_r32c13, ['Ink2_r32c13']),
    ('a1_lower_ink2_takes_5__Ink2_r32c14', _guard_a1_lower_ink2_takes_5__Ink2_r32c14, _effect_a1_lower_ink2_takes_5__Ink2_r32c14, ['Ink2_r32c14']),
    ('a1_lower_ink2_takes_5__Ink2_r33c13', _guard_a1_lower_ink2_takes_5__Ink2_r33c13, _effect_a1_lower_ink2_takes_5__Ink2_r33c13, ['Ink2_r33c13']),
    ('a1_lower_ink2_takes_5__Ink2_r33c14', _guard_a1_lower_ink2_takes_5__Ink2_r33c14, _effect_a1_lower_ink2_takes_5__Ink2_r33c14, ['Ink2_r33c14']),
    ('a1_lower_ink2_takes_5__Ink2_r38c17', _guard_a1_lower_ink2_takes_5__Ink2_r38c17, _effect_a1_lower_ink2_takes_5__Ink2_r38c17, ['Ink2_r38c17']),
    ('a1_lower_ink2_takes_5__Ink2_r38c20', _guard_a1_lower_ink2_takes_5__Ink2_r38c20, _effect_a1_lower_ink2_takes_5__Ink2_r38c20, ['Ink2_r38c20']),
    ('a1_lower_ink2_takes_5__Ink2_r39c16', _guard_a1_lower_ink2_takes_5__Ink2_r39c16, _effect_a1_lower_ink2_takes_5__Ink2_r39c16, ['Ink2_r39c16']),
    ('a1_lower_ink2_takes_5__Ink2_r39c19', _guard_a1_lower_ink2_takes_5__Ink2_r39c19, _effect_a1_lower_ink2_takes_5__Ink2_r39c19, ['Ink2_r39c19']),
    ('a1_lower_ink2_takes_5__Ink2_r39c22', _guard_a1_lower_ink2_takes_5__Ink2_r39c22, _effect_a1_lower_ink2_takes_5__Ink2_r39c22, ['Ink2_r39c22']),
    ('a1_lower_ink2_takes_5__Ink2_r53c63', _guard_a1_lower_ink2_takes_5__Ink2_r53c63, _effect_a1_lower_ink2_takes_5__Ink2_r53c63, ['Ink2_r53c63']),
    ('a1_icon2_body_takes_5__Ink6_r36c11', _guard_a1_icon2_body_takes_5__Ink6_r36c11, _effect_a1_icon2_body_takes_5__Ink6_r36c11, ['Ink6_r36c11']),
    ('a1_icon2_body_takes_5__Ink6_r36c12', _guard_a1_icon2_body_takes_5__Ink6_r36c12, _effect_a1_icon2_body_takes_5__Ink6_r36c12, ['Ink6_r36c12']),
    ('a1_icon2_body_takes_5__Ink6_r36c13', _guard_a1_icon2_body_takes_5__Ink6_r36c13, _effect_a1_icon2_body_takes_5__Ink6_r36c13, ['Ink6_r36c13']),
    ('a1_icon2_body_takes_5__Ink6_r36c14', _guard_a1_icon2_body_takes_5__Ink6_r36c14, _effect_a1_icon2_body_takes_5__Ink6_r36c14, ['Ink6_r36c14']),
    ('a1_icon2_body_takes_5__Ink6_r36c15', _guard_a1_icon2_body_takes_5__Ink6_r36c15, _effect_a1_icon2_body_takes_5__Ink6_r36c15, ['Ink6_r36c15']),
    ('a1_icon2_body_takes_5__Ink6_r36c16', _guard_a1_icon2_body_takes_5__Ink6_r36c16, _effect_a1_icon2_body_takes_5__Ink6_r36c16, ['Ink6_r36c16']),
    ('a1_icon2_body_takes_5__Ink6_r37c11', _guard_a1_icon2_body_takes_5__Ink6_r37c11, _effect_a1_icon2_body_takes_5__Ink6_r37c11, ['Ink6_r37c11']),
    ('a1_icon2_body_takes_5__Ink6_r37c16', _guard_a1_icon2_body_takes_5__Ink6_r37c16, _effect_a1_icon2_body_takes_5__Ink6_r37c16, ['Ink6_r37c16']),
    ('a1_icon2_body_takes_5__Ink6_r38c11', _guard_a1_icon2_body_takes_5__Ink6_r38c11, _effect_a1_icon2_body_takes_5__Ink6_r38c11, ['Ink6_r38c11']),
    ('a1_icon2_body_takes_5__Ink6_r38c13', _guard_a1_icon2_body_takes_5__Ink6_r38c13, _effect_a1_icon2_body_takes_5__Ink6_r38c13, ['Ink6_r38c13']),
    ('a1_icon2_body_takes_5__Ink6_r38c14', _guard_a1_icon2_body_takes_5__Ink6_r38c14, _effect_a1_icon2_body_takes_5__Ink6_r38c14, ['Ink6_r38c14']),
    ('a1_icon2_body_takes_5__Ink6_r39c11', _guard_a1_icon2_body_takes_5__Ink6_r39c11, _effect_a1_icon2_body_takes_5__Ink6_r39c11, ['Ink6_r39c11']),
    ('a1_icon2_body_takes_5__Ink6_r39c13', _guard_a1_icon2_body_takes_5__Ink6_r39c13, _effect_a1_icon2_body_takes_5__Ink6_r39c13, ['Ink6_r39c13']),
    ('a1_icon2_body_takes_5__Ink6_r39c14', _guard_a1_icon2_body_takes_5__Ink6_r39c14, _effect_a1_icon2_body_takes_5__Ink6_r39c14, ['Ink6_r39c14']),
    ('a1_icon2_body_takes_5__Ink6_r40c11', _guard_a1_icon2_body_takes_5__Ink6_r40c11, _effect_a1_icon2_body_takes_5__Ink6_r40c11, ['Ink6_r40c11']),
    ('a1_icon2_body_takes_5__Ink6_r40c16', _guard_a1_icon2_body_takes_5__Ink6_r40c16, _effect_a1_icon2_body_takes_5__Ink6_r40c16, ['Ink6_r40c16']),
    ('a1_icon2_body_takes_5__Ink6_r41c11', _guard_a1_icon2_body_takes_5__Ink6_r41c11, _effect_a1_icon2_body_takes_5__Ink6_r41c11, ['Ink6_r41c11']),
    ('a1_icon2_body_takes_5__Ink6_r41c12', _guard_a1_icon2_body_takes_5__Ink6_r41c12, _effect_a1_icon2_body_takes_5__Ink6_r41c12, ['Ink6_r41c12']),
    ('a1_icon2_body_takes_5__Ink6_r41c13', _guard_a1_icon2_body_takes_5__Ink6_r41c13, _effect_a1_icon2_body_takes_5__Ink6_r41c13, ['Ink6_r41c13']),
    ('a1_icon2_body_takes_5__Ink6_r41c14', _guard_a1_icon2_body_takes_5__Ink6_r41c14, _effect_a1_icon2_body_takes_5__Ink6_r41c14, ['Ink6_r41c14']),
    ('a1_icon2_body_takes_5__Ink6_r41c15', _guard_a1_icon2_body_takes_5__Ink6_r41c15, _effect_a1_icon2_body_takes_5__Ink6_r41c15, ['Ink6_r41c15']),
    ('a1_icon2_body_takes_5__Ink6_r41c16', _guard_a1_icon2_body_takes_5__Ink6_r41c16, _effect_a1_icon2_body_takes_5__Ink6_r41c16, ['Ink6_r41c16']),
    ('a1_icon2_body_takes_3__Ink6_r36c11', _guard_a1_icon2_body_takes_3__Ink6_r36c11, _effect_a1_icon2_body_takes_3__Ink6_r36c11, ['Ink6_r36c11']),
    ('a1_icon2_body_takes_3__Ink6_r36c12', _guard_a1_icon2_body_takes_3__Ink6_r36c12, _effect_a1_icon2_body_takes_3__Ink6_r36c12, ['Ink6_r36c12']),
    ('a1_icon2_body_takes_3__Ink6_r36c13', _guard_a1_icon2_body_takes_3__Ink6_r36c13, _effect_a1_icon2_body_takes_3__Ink6_r36c13, ['Ink6_r36c13']),
    ('a1_icon2_body_takes_3__Ink6_r36c14', _guard_a1_icon2_body_takes_3__Ink6_r36c14, _effect_a1_icon2_body_takes_3__Ink6_r36c14, ['Ink6_r36c14']),
    ('a1_icon2_body_takes_3__Ink6_r36c15', _guard_a1_icon2_body_takes_3__Ink6_r36c15, _effect_a1_icon2_body_takes_3__Ink6_r36c15, ['Ink6_r36c15']),
    ('a1_icon2_body_takes_3__Ink6_r36c16', _guard_a1_icon2_body_takes_3__Ink6_r36c16, _effect_a1_icon2_body_takes_3__Ink6_r36c16, ['Ink6_r36c16']),
    ('a1_icon2_body_takes_3__Ink6_r37c11', _guard_a1_icon2_body_takes_3__Ink6_r37c11, _effect_a1_icon2_body_takes_3__Ink6_r37c11, ['Ink6_r37c11']),
    ('a1_icon2_body_takes_3__Ink6_r37c16', _guard_a1_icon2_body_takes_3__Ink6_r37c16, _effect_a1_icon2_body_takes_3__Ink6_r37c16, ['Ink6_r37c16']),
    ('a1_icon2_body_takes_3__Ink6_r38c11', _guard_a1_icon2_body_takes_3__Ink6_r38c11, _effect_a1_icon2_body_takes_3__Ink6_r38c11, ['Ink6_r38c11']),
    ('a1_icon2_body_takes_3__Ink6_r38c13', _guard_a1_icon2_body_takes_3__Ink6_r38c13, _effect_a1_icon2_body_takes_3__Ink6_r38c13, ['Ink6_r38c13']),
    ('a1_icon2_body_takes_3__Ink6_r38c14', _guard_a1_icon2_body_takes_3__Ink6_r38c14, _effect_a1_icon2_body_takes_3__Ink6_r38c14, ['Ink6_r38c14']),
    ('a1_icon2_body_takes_3__Ink6_r39c11', _guard_a1_icon2_body_takes_3__Ink6_r39c11, _effect_a1_icon2_body_takes_3__Ink6_r39c11, ['Ink6_r39c11']),
    ('a1_icon2_body_takes_3__Ink6_r39c13', _guard_a1_icon2_body_takes_3__Ink6_r39c13, _effect_a1_icon2_body_takes_3__Ink6_r39c13, ['Ink6_r39c13']),
    ('a1_icon2_body_takes_3__Ink6_r39c14', _guard_a1_icon2_body_takes_3__Ink6_r39c14, _effect_a1_icon2_body_takes_3__Ink6_r39c14, ['Ink6_r39c14']),
    ('a1_icon2_body_takes_3__Ink6_r40c11', _guard_a1_icon2_body_takes_3__Ink6_r40c11, _effect_a1_icon2_body_takes_3__Ink6_r40c11, ['Ink6_r40c11']),
    ('a1_icon2_body_takes_3__Ink6_r40c16', _guard_a1_icon2_body_takes_3__Ink6_r40c16, _effect_a1_icon2_body_takes_3__Ink6_r40c16, ['Ink6_r40c16']),
    ('a1_icon2_body_takes_3__Ink6_r41c11', _guard_a1_icon2_body_takes_3__Ink6_r41c11, _effect_a1_icon2_body_takes_3__Ink6_r41c11, ['Ink6_r41c11']),
    ('a1_icon2_body_takes_3__Ink6_r41c12', _guard_a1_icon2_body_takes_3__Ink6_r41c12, _effect_a1_icon2_body_takes_3__Ink6_r41c12, ['Ink6_r41c12']),
    ('a1_icon2_body_takes_3__Ink6_r41c13', _guard_a1_icon2_body_takes_3__Ink6_r41c13, _effect_a1_icon2_body_takes_3__Ink6_r41c13, ['Ink6_r41c13']),
    ('a1_icon2_body_takes_3__Ink6_r41c14', _guard_a1_icon2_body_takes_3__Ink6_r41c14, _effect_a1_icon2_body_takes_3__Ink6_r41c14, ['Ink6_r41c14']),
    ('a1_icon2_body_takes_3__Ink6_r41c15', _guard_a1_icon2_body_takes_3__Ink6_r41c15, _effect_a1_icon2_body_takes_3__Ink6_r41c15, ['Ink6_r41c15']),
    ('a1_icon2_body_takes_3__Ink6_r41c16', _guard_a1_icon2_body_takes_3__Ink6_r41c16, _effect_a1_icon2_body_takes_3__Ink6_r41c16, ['Ink6_r41c16']),
    ('a1_icon2_body_takes_2__Ink6_r36c11', _guard_a1_icon2_body_takes_2__Ink6_r36c11, _effect_a1_icon2_body_takes_2__Ink6_r36c11, ['Ink6_r36c11']),
    ('a1_icon2_body_takes_2__Ink6_r36c12', _guard_a1_icon2_body_takes_2__Ink6_r36c12, _effect_a1_icon2_body_takes_2__Ink6_r36c12, ['Ink6_r36c12']),
    ('a1_icon2_body_takes_2__Ink6_r36c13', _guard_a1_icon2_body_takes_2__Ink6_r36c13, _effect_a1_icon2_body_takes_2__Ink6_r36c13, ['Ink6_r36c13']),
    ('a1_icon2_body_takes_2__Ink6_r36c14', _guard_a1_icon2_body_takes_2__Ink6_r36c14, _effect_a1_icon2_body_takes_2__Ink6_r36c14, ['Ink6_r36c14']),
    ('a1_icon2_body_takes_2__Ink6_r36c15', _guard_a1_icon2_body_takes_2__Ink6_r36c15, _effect_a1_icon2_body_takes_2__Ink6_r36c15, ['Ink6_r36c15']),
    ('a1_icon2_body_takes_2__Ink6_r36c16', _guard_a1_icon2_body_takes_2__Ink6_r36c16, _effect_a1_icon2_body_takes_2__Ink6_r36c16, ['Ink6_r36c16']),
    ('a1_icon2_body_takes_2__Ink6_r37c11', _guard_a1_icon2_body_takes_2__Ink6_r37c11, _effect_a1_icon2_body_takes_2__Ink6_r37c11, ['Ink6_r37c11']),
    ('a1_icon2_body_takes_2__Ink6_r37c16', _guard_a1_icon2_body_takes_2__Ink6_r37c16, _effect_a1_icon2_body_takes_2__Ink6_r37c16, ['Ink6_r37c16']),
    ('a1_icon2_body_takes_2__Ink6_r38c11', _guard_a1_icon2_body_takes_2__Ink6_r38c11, _effect_a1_icon2_body_takes_2__Ink6_r38c11, ['Ink6_r38c11']),
    ('a1_icon2_body_takes_2__Ink6_r38c13', _guard_a1_icon2_body_takes_2__Ink6_r38c13, _effect_a1_icon2_body_takes_2__Ink6_r38c13, ['Ink6_r38c13']),
    ('a1_icon2_body_takes_2__Ink6_r38c14', _guard_a1_icon2_body_takes_2__Ink6_r38c14, _effect_a1_icon2_body_takes_2__Ink6_r38c14, ['Ink6_r38c14']),
    ('a1_icon2_body_takes_2__Ink6_r39c11', _guard_a1_icon2_body_takes_2__Ink6_r39c11, _effect_a1_icon2_body_takes_2__Ink6_r39c11, ['Ink6_r39c11']),
    ('a1_icon2_body_takes_2__Ink6_r39c13', _guard_a1_icon2_body_takes_2__Ink6_r39c13, _effect_a1_icon2_body_takes_2__Ink6_r39c13, ['Ink6_r39c13']),
    ('a1_icon2_body_takes_2__Ink6_r39c14', _guard_a1_icon2_body_takes_2__Ink6_r39c14, _effect_a1_icon2_body_takes_2__Ink6_r39c14, ['Ink6_r39c14']),
    ('a1_icon2_body_takes_2__Ink6_r40c11', _guard_a1_icon2_body_takes_2__Ink6_r40c11, _effect_a1_icon2_body_takes_2__Ink6_r40c11, ['Ink6_r40c11']),
    ('a1_icon2_body_takes_2__Ink6_r40c16', _guard_a1_icon2_body_takes_2__Ink6_r40c16, _effect_a1_icon2_body_takes_2__Ink6_r40c16, ['Ink6_r40c16']),
    ('a1_icon2_body_takes_2__Ink6_r41c11', _guard_a1_icon2_body_takes_2__Ink6_r41c11, _effect_a1_icon2_body_takes_2__Ink6_r41c11, ['Ink6_r41c11']),
    ('a1_icon2_body_takes_2__Ink6_r41c12', _guard_a1_icon2_body_takes_2__Ink6_r41c12, _effect_a1_icon2_body_takes_2__Ink6_r41c12, ['Ink6_r41c12']),
    ('a1_icon2_body_takes_2__Ink6_r41c13', _guard_a1_icon2_body_takes_2__Ink6_r41c13, _effect_a1_icon2_body_takes_2__Ink6_r41c13, ['Ink6_r41c13']),
    ('a1_icon2_body_takes_2__Ink6_r41c14', _guard_a1_icon2_body_takes_2__Ink6_r41c14, _effect_a1_icon2_body_takes_2__Ink6_r41c14, ['Ink6_r41c14']),
    ('a1_icon2_body_takes_2__Ink6_r41c15', _guard_a1_icon2_body_takes_2__Ink6_r41c15, _effect_a1_icon2_body_takes_2__Ink6_r41c15, ['Ink6_r41c15']),
    ('a1_icon2_body_takes_2__Ink6_r41c16', _guard_a1_icon2_body_takes_2__Ink6_r41c16, _effect_a1_icon2_body_takes_2__Ink6_r41c16, ['Ink6_r41c16']),
    ('a1_icon2_hole_takes_5__Ink0_r37c12', _guard_a1_icon2_hole_takes_5__Ink0_r37c12, _effect_a1_icon2_hole_takes_5__Ink0_r37c12, ['Ink0_r37c12']),
    ('a1_icon2_hole_takes_5__Ink0_r37c13', _guard_a1_icon2_hole_takes_5__Ink0_r37c13, _effect_a1_icon2_hole_takes_5__Ink0_r37c13, ['Ink0_r37c13']),
    ('a1_icon2_hole_takes_5__Ink0_r37c14', _guard_a1_icon2_hole_takes_5__Ink0_r37c14, _effect_a1_icon2_hole_takes_5__Ink0_r37c14, ['Ink0_r37c14']),
    ('a1_icon2_hole_takes_5__Ink0_r37c15', _guard_a1_icon2_hole_takes_5__Ink0_r37c15, _effect_a1_icon2_hole_takes_5__Ink0_r37c15, ['Ink0_r37c15']),
    ('a1_icon2_hole_takes_5__Ink0_r38c12', _guard_a1_icon2_hole_takes_5__Ink0_r38c12, _effect_a1_icon2_hole_takes_5__Ink0_r38c12, ['Ink0_r38c12']),
    ('a1_icon2_hole_takes_5__Ink0_r38c15', _guard_a1_icon2_hole_takes_5__Ink0_r38c15, _effect_a1_icon2_hole_takes_5__Ink0_r38c15, ['Ink0_r38c15']),
    ('a1_icon2_hole_takes_5__Ink0_r39c12', _guard_a1_icon2_hole_takes_5__Ink0_r39c12, _effect_a1_icon2_hole_takes_5__Ink0_r39c12, ['Ink0_r39c12']),
    ('a1_icon2_hole_takes_5__Ink0_r39c15', _guard_a1_icon2_hole_takes_5__Ink0_r39c15, _effect_a1_icon2_hole_takes_5__Ink0_r39c15, ['Ink0_r39c15']),
    ('a1_icon2_hole_takes_5__Ink0_r40c12', _guard_a1_icon2_hole_takes_5__Ink0_r40c12, _effect_a1_icon2_hole_takes_5__Ink0_r40c12, ['Ink0_r40c12']),
    ('a1_icon2_hole_takes_5__Ink0_r40c13', _guard_a1_icon2_hole_takes_5__Ink0_r40c13, _effect_a1_icon2_hole_takes_5__Ink0_r40c13, ['Ink0_r40c13']),
    ('a1_icon2_hole_takes_5__Ink0_r40c14', _guard_a1_icon2_hole_takes_5__Ink0_r40c14, _effect_a1_icon2_hole_takes_5__Ink0_r40c14, ['Ink0_r40c14']),
    ('a1_icon2_hole_takes_5__Ink0_r40c15', _guard_a1_icon2_hole_takes_5__Ink0_r40c15, _effect_a1_icon2_hole_takes_5__Ink0_r40c15, ['Ink0_r40c15']),
    ('a1_icon2_hole_takes_3__Ink0_r37c12', _guard_a1_icon2_hole_takes_3__Ink0_r37c12, _effect_a1_icon2_hole_takes_3__Ink0_r37c12, ['Ink0_r37c12']),
    ('a1_icon2_hole_takes_3__Ink0_r37c13', _guard_a1_icon2_hole_takes_3__Ink0_r37c13, _effect_a1_icon2_hole_takes_3__Ink0_r37c13, ['Ink0_r37c13']),
    ('a1_icon2_hole_takes_3__Ink0_r37c14', _guard_a1_icon2_hole_takes_3__Ink0_r37c14, _effect_a1_icon2_hole_takes_3__Ink0_r37c14, ['Ink0_r37c14']),
    ('a1_icon2_hole_takes_3__Ink0_r37c15', _guard_a1_icon2_hole_takes_3__Ink0_r37c15, _effect_a1_icon2_hole_takes_3__Ink0_r37c15, ['Ink0_r37c15']),
    ('a1_icon2_hole_takes_3__Ink0_r38c12', _guard_a1_icon2_hole_takes_3__Ink0_r38c12, _effect_a1_icon2_hole_takes_3__Ink0_r38c12, ['Ink0_r38c12']),
    ('a1_icon2_hole_takes_3__Ink0_r38c15', _guard_a1_icon2_hole_takes_3__Ink0_r38c15, _effect_a1_icon2_hole_takes_3__Ink0_r38c15, ['Ink0_r38c15']),
    ('a1_icon2_hole_takes_3__Ink0_r39c12', _guard_a1_icon2_hole_takes_3__Ink0_r39c12, _effect_a1_icon2_hole_takes_3__Ink0_r39c12, ['Ink0_r39c12']),
    ('a1_icon2_hole_takes_3__Ink0_r39c15', _guard_a1_icon2_hole_takes_3__Ink0_r39c15, _effect_a1_icon2_hole_takes_3__Ink0_r39c15, ['Ink0_r39c15']),
    ('a1_icon2_hole_takes_3__Ink0_r40c12', _guard_a1_icon2_hole_takes_3__Ink0_r40c12, _effect_a1_icon2_hole_takes_3__Ink0_r40c12, ['Ink0_r40c12']),
    ('a1_icon2_hole_takes_3__Ink0_r40c13', _guard_a1_icon2_hole_takes_3__Ink0_r40c13, _effect_a1_icon2_hole_takes_3__Ink0_r40c13, ['Ink0_r40c13']),
    ('a1_icon2_hole_takes_3__Ink0_r40c14', _guard_a1_icon2_hole_takes_3__Ink0_r40c14, _effect_a1_icon2_hole_takes_3__Ink0_r40c14, ['Ink0_r40c14']),
    ('a1_icon2_hole_takes_3__Ink0_r40c15', _guard_a1_icon2_hole_takes_3__Ink0_r40c15, _effect_a1_icon2_hole_takes_3__Ink0_r40c15, ['Ink0_r40c15']),
    ('a1_tape2_takes_4__Ink1_r38c16', _guard_a1_tape2_takes_4__Ink1_r38c16, _effect_a1_tape2_takes_4__Ink1_r38c16, ['Ink1_r38c16']),
    ('a1_tape2_takes_4__Ink1_r38c18', _guard_a1_tape2_takes_4__Ink1_r38c18, _effect_a1_tape2_takes_4__Ink1_r38c18, ['Ink1_r38c18']),
    ('a1_tape2_takes_4__Ink1_r38c19', _guard_a1_tape2_takes_4__Ink1_r38c19, _effect_a1_tape2_takes_4__Ink1_r38c19, ['Ink1_r38c19']),
    ('a1_tape2_takes_4__Ink1_r38c21', _guard_a1_tape2_takes_4__Ink1_r38c21, _effect_a1_tape2_takes_4__Ink1_r38c21, ['Ink1_r38c21']),
    ('a1_tape2_takes_4__Ink1_r38c22', _guard_a1_tape2_takes_4__Ink1_r38c22, _effect_a1_tape2_takes_4__Ink1_r38c22, ['Ink1_r38c22']),
    ('a1_tape2_takes_4__Ink1_r39c17', _guard_a1_tape2_takes_4__Ink1_r39c17, _effect_a1_tape2_takes_4__Ink1_r39c17, ['Ink1_r39c17']),
    ('a1_tape2_takes_4__Ink1_r39c18', _guard_a1_tape2_takes_4__Ink1_r39c18, _effect_a1_tape2_takes_4__Ink1_r39c18, ['Ink1_r39c18']),
    ('a1_tape2_takes_4__Ink1_r39c20', _guard_a1_tape2_takes_4__Ink1_r39c20, _effect_a1_tape2_takes_4__Ink1_r39c20, ['Ink1_r39c20']),
    ('a1_tape2_takes_4__Ink1_r39c21', _guard_a1_tape2_takes_4__Ink1_r39c21, _effect_a1_tape2_takes_4__Ink1_r39c21, ['Ink1_r39c21']),
    ('a1_tape2_takes_5__Ink1_r38c16', _guard_a1_tape2_takes_5__Ink1_r38c16, _effect_a1_tape2_takes_5__Ink1_r38c16, ['Ink1_r38c16']),
    ('a1_tape2_takes_5__Ink1_r38c18', _guard_a1_tape2_takes_5__Ink1_r38c18, _effect_a1_tape2_takes_5__Ink1_r38c18, ['Ink1_r38c18']),
    ('a1_tape2_takes_5__Ink1_r38c19', _guard_a1_tape2_takes_5__Ink1_r38c19, _effect_a1_tape2_takes_5__Ink1_r38c19, ['Ink1_r38c19']),
    ('a1_tape2_takes_5__Ink1_r38c21', _guard_a1_tape2_takes_5__Ink1_r38c21, _effect_a1_tape2_takes_5__Ink1_r38c21, ['Ink1_r38c21']),
    ('a1_tape2_takes_5__Ink1_r38c22', _guard_a1_tape2_takes_5__Ink1_r38c22, _effect_a1_tape2_takes_5__Ink1_r38c22, ['Ink1_r38c22']),
    ('a1_tape2_takes_5__Ink1_r39c17', _guard_a1_tape2_takes_5__Ink1_r39c17, _effect_a1_tape2_takes_5__Ink1_r39c17, ['Ink1_r39c17']),
    ('a1_tape2_takes_5__Ink1_r39c18', _guard_a1_tape2_takes_5__Ink1_r39c18, _effect_a1_tape2_takes_5__Ink1_r39c18, ['Ink1_r39c18']),
    ('a1_tape2_takes_5__Ink1_r39c20', _guard_a1_tape2_takes_5__Ink1_r39c20, _effect_a1_tape2_takes_5__Ink1_r39c20, ['Ink1_r39c20']),
    ('a1_tape2_takes_5__Ink1_r39c21', _guard_a1_tape2_takes_5__Ink1_r39c21, _effect_a1_tape2_takes_5__Ink1_r39c21, ['Ink1_r39c21']),
    ('a2_icon1_field_takes_5__Ink5_r30c11', _guard_a2_icon1_field_takes_5__Ink5_r30c11, _effect_a2_icon1_field_takes_5__Ink5_r30c11, ['Ink5_r30c11']),
    ('a2_icon1_field_takes_5__Ink5_r30c12', _guard_a2_icon1_field_takes_5__Ink5_r30c12, _effect_a2_icon1_field_takes_5__Ink5_r30c12, ['Ink5_r30c12']),
    ('a2_icon1_field_takes_5__Ink5_r30c15', _guard_a2_icon1_field_takes_5__Ink5_r30c15, _effect_a2_icon1_field_takes_5__Ink5_r30c15, ['Ink5_r30c15']),
    ('a2_icon1_field_takes_5__Ink5_r30c16', _guard_a2_icon1_field_takes_5__Ink5_r30c16, _effect_a2_icon1_field_takes_5__Ink5_r30c16, ['Ink5_r30c16']),
    ('a2_icon1_field_takes_5__Ink5_r31c11', _guard_a2_icon1_field_takes_5__Ink5_r31c11, _effect_a2_icon1_field_takes_5__Ink5_r31c11, ['Ink5_r31c11']),
    ('a2_icon1_field_takes_5__Ink5_r31c12', _guard_a2_icon1_field_takes_5__Ink5_r31c12, _effect_a2_icon1_field_takes_5__Ink5_r31c12, ['Ink5_r31c12']),
    ('a2_icon1_field_takes_5__Ink5_r31c15', _guard_a2_icon1_field_takes_5__Ink5_r31c15, _effect_a2_icon1_field_takes_5__Ink5_r31c15, ['Ink5_r31c15']),
    ('a2_icon1_field_takes_5__Ink5_r31c16', _guard_a2_icon1_field_takes_5__Ink5_r31c16, _effect_a2_icon1_field_takes_5__Ink5_r31c16, ['Ink5_r31c16']),
    ('a2_icon1_field_takes_5__Ink5_r32c11', _guard_a2_icon1_field_takes_5__Ink5_r32c11, _effect_a2_icon1_field_takes_5__Ink5_r32c11, ['Ink5_r32c11']),
    ('a2_icon1_field_takes_5__Ink5_r32c12', _guard_a2_icon1_field_takes_5__Ink5_r32c12, _effect_a2_icon1_field_takes_5__Ink5_r32c12, ['Ink5_r32c12']),
    ('a2_icon1_field_takes_5__Ink5_r32c15', _guard_a2_icon1_field_takes_5__Ink5_r32c15, _effect_a2_icon1_field_takes_5__Ink5_r32c15, ['Ink5_r32c15']),
    ('a2_icon1_field_takes_5__Ink5_r32c16', _guard_a2_icon1_field_takes_5__Ink5_r32c16, _effect_a2_icon1_field_takes_5__Ink5_r32c16, ['Ink5_r32c16']),
    ('a2_icon1_field_takes_5__Ink5_r33c11', _guard_a2_icon1_field_takes_5__Ink5_r33c11, _effect_a2_icon1_field_takes_5__Ink5_r33c11, ['Ink5_r33c11']),
    ('a2_icon1_field_takes_5__Ink5_r33c12', _guard_a2_icon1_field_takes_5__Ink5_r33c12, _effect_a2_icon1_field_takes_5__Ink5_r33c12, ['Ink5_r33c12']),
    ('a2_icon1_field_takes_5__Ink5_r33c15', _guard_a2_icon1_field_takes_5__Ink5_r33c15, _effect_a2_icon1_field_takes_5__Ink5_r33c15, ['Ink5_r33c15']),
    ('a2_icon1_field_takes_5__Ink5_r33c16', _guard_a2_icon1_field_takes_5__Ink5_r33c16, _effect_a2_icon1_field_takes_5__Ink5_r33c16, ['Ink5_r33c16']),
    ('a2_icon1_field_takes_5__Ink5_r34c11', _guard_a2_icon1_field_takes_5__Ink5_r34c11, _effect_a2_icon1_field_takes_5__Ink5_r34c11, ['Ink5_r34c11']),
    ('a2_icon1_field_takes_5__Ink5_r34c12', _guard_a2_icon1_field_takes_5__Ink5_r34c12, _effect_a2_icon1_field_takes_5__Ink5_r34c12, ['Ink5_r34c12']),
    ('a2_icon1_field_takes_5__Ink5_r34c15', _guard_a2_icon1_field_takes_5__Ink5_r34c15, _effect_a2_icon1_field_takes_5__Ink5_r34c15, ['Ink5_r34c15']),
    ('a2_icon1_field_takes_5__Ink5_r34c16', _guard_a2_icon1_field_takes_5__Ink5_r34c16, _effect_a2_icon1_field_takes_5__Ink5_r34c16, ['Ink5_r34c16']),
    ('a2_icon1_field_takes_5__Ink5_r35c11', _guard_a2_icon1_field_takes_5__Ink5_r35c11, _effect_a2_icon1_field_takes_5__Ink5_r35c11, ['Ink5_r35c11']),
    ('a2_icon1_field_takes_5__Ink5_r35c12', _guard_a2_icon1_field_takes_5__Ink5_r35c12, _effect_a2_icon1_field_takes_5__Ink5_r35c12, ['Ink5_r35c12']),
    ('a2_icon1_field_takes_5__Ink5_r35c15', _guard_a2_icon1_field_takes_5__Ink5_r35c15, _effect_a2_icon1_field_takes_5__Ink5_r35c15, ['Ink5_r35c15']),
    ('a2_icon1_field_takes_5__Ink5_r35c16', _guard_a2_icon1_field_takes_5__Ink5_r35c16, _effect_a2_icon1_field_takes_5__Ink5_r35c16, ['Ink5_r35c16']),
    ('a2_track_takes_3__Ink3_r30c13', _guard_a2_track_takes_3__Ink3_r30c13, _effect_a2_track_takes_3__Ink3_r30c13, ['Ink3_r30c13']),
    ('a2_track_takes_3__Ink3_r30c14', _guard_a2_track_takes_3__Ink3_r30c14, _effect_a2_track_takes_3__Ink3_r30c14, ['Ink3_r30c14']),
    ('a2_track_takes_3__Ink3_r31c13', _guard_a2_track_takes_3__Ink3_r31c13, _effect_a2_track_takes_3__Ink3_r31c13, ['Ink3_r31c13']),
    ('a2_track_takes_3__Ink3_r31c14', _guard_a2_track_takes_3__Ink3_r31c14, _effect_a2_track_takes_3__Ink3_r31c14, ['Ink3_r31c14']),
    ('a2_track_takes_3__Ink3_r34c13', _guard_a2_track_takes_3__Ink3_r34c13, _effect_a2_track_takes_3__Ink3_r34c13, ['Ink3_r34c13']),
    ('a2_track_takes_3__Ink3_r34c14', _guard_a2_track_takes_3__Ink3_r34c14, _effect_a2_track_takes_3__Ink3_r34c14, ['Ink3_r34c14']),
    ('a2_track_takes_3__Ink3_r35c13', _guard_a2_track_takes_3__Ink3_r35c13, _effect_a2_track_takes_3__Ink3_r35c13, ['Ink3_r35c13']),
    ('a2_track_takes_3__Ink3_r35c14', _guard_a2_track_takes_3__Ink3_r35c14, _effect_a2_track_takes_3__Ink3_r35c14, ['Ink3_r35c14']),
    ('a2_tape1_takes_4__Ink4_r32c17', _guard_a2_tape1_takes_4__Ink4_r32c17, _effect_a2_tape1_takes_4__Ink4_r32c17, ['Ink4_r32c17']),
    ('a2_tape1_takes_4__Ink4_r32c18', _guard_a2_tape1_takes_4__Ink4_r32c18, _effect_a2_tape1_takes_4__Ink4_r32c18, ['Ink4_r32c18']),
    ('a2_tape1_takes_4__Ink4_r32c19', _guard_a2_tape1_takes_4__Ink4_r32c19, _effect_a2_tape1_takes_4__Ink4_r32c19, ['Ink4_r32c19']),
    ('a2_tape1_takes_4__Ink4_r32c20', _guard_a2_tape1_takes_4__Ink4_r32c20, _effect_a2_tape1_takes_4__Ink4_r32c20, ['Ink4_r32c20']),
    ('a2_tape1_takes_4__Ink4_r32c21', _guard_a2_tape1_takes_4__Ink4_r32c21, _effect_a2_tape1_takes_4__Ink4_r32c21, ['Ink4_r32c21']),
    ('a2_tape1_takes_4__Ink4_r32c22', _guard_a2_tape1_takes_4__Ink4_r32c22, _effect_a2_tape1_takes_4__Ink4_r32c22, ['Ink4_r32c22']),
    ('a2_tape1_takes_4__Ink4_r33c17', _guard_a2_tape1_takes_4__Ink4_r33c17, _effect_a2_tape1_takes_4__Ink4_r33c17, ['Ink4_r33c17']),
    ('a2_tape1_takes_4__Ink4_r33c18', _guard_a2_tape1_takes_4__Ink4_r33c18, _effect_a2_tape1_takes_4__Ink4_r33c18, ['Ink4_r33c18']),
    ('a2_tape1_takes_4__Ink4_r33c19', _guard_a2_tape1_takes_4__Ink4_r33c19, _effect_a2_tape1_takes_4__Ink4_r33c19, ['Ink4_r33c19']),
    ('a2_tape1_takes_4__Ink4_r33c20', _guard_a2_tape1_takes_4__Ink4_r33c20, _effect_a2_tape1_takes_4__Ink4_r33c20, ['Ink4_r33c20']),
    ('a2_tape1_takes_4__Ink4_r33c21', _guard_a2_tape1_takes_4__Ink4_r33c21, _effect_a2_tape1_takes_4__Ink4_r33c21, ['Ink4_r33c21']),
    ('a2_tape1_takes_4__Ink4_r33c22', _guard_a2_tape1_takes_4__Ink4_r33c22, _effect_a2_tape1_takes_4__Ink4_r33c22, ['Ink4_r33c22']),
    ('a2_thumb_takes_2__Ink2_r32c13', _guard_a2_thumb_takes_2__Ink2_r32c13, _effect_a2_thumb_takes_2__Ink2_r32c13, ['Ink2_r32c13']),
    ('a2_thumb_takes_2__Ink2_r32c14', _guard_a2_thumb_takes_2__Ink2_r32c14, _effect_a2_thumb_takes_2__Ink2_r32c14, ['Ink2_r32c14']),
    ('a2_thumb_takes_2__Ink2_r33c13', _guard_a2_thumb_takes_2__Ink2_r33c13, _effect_a2_thumb_takes_2__Ink2_r33c13, ['Ink2_r33c13']),
    ('a2_thumb_takes_2__Ink2_r33c14', _guard_a2_thumb_takes_2__Ink2_r33c14, _effect_a2_thumb_takes_2__Ink2_r33c14, ['Ink2_r33c14']),
    ('a2_thumb_takes_2__Ink2_r38c17', _guard_a2_thumb_takes_2__Ink2_r38c17, _effect_a2_thumb_takes_2__Ink2_r38c17, ['Ink2_r38c17']),
    ('a2_thumb_takes_2__Ink2_r38c20', _guard_a2_thumb_takes_2__Ink2_r38c20, _effect_a2_thumb_takes_2__Ink2_r38c20, ['Ink2_r38c20']),
    ('a2_thumb_takes_2__Ink2_r39c16', _guard_a2_thumb_takes_2__Ink2_r39c16, _effect_a2_thumb_takes_2__Ink2_r39c16, ['Ink2_r39c16']),
    ('a2_thumb_takes_2__Ink2_r39c19', _guard_a2_thumb_takes_2__Ink2_r39c19, _effect_a2_thumb_takes_2__Ink2_r39c19, ['Ink2_r39c19']),
    ('a2_thumb_takes_2__Ink2_r39c22', _guard_a2_thumb_takes_2__Ink2_r39c22, _effect_a2_thumb_takes_2__Ink2_r39c22, ['Ink2_r39c22']),
    ('a2_thumb_takes_2__Ink2_r53c63', _guard_a2_thumb_takes_2__Ink2_r53c63, _effect_a2_thumb_takes_2__Ink2_r53c63, ['Ink2_r53c63']),
    ('a2_lower_ink2_takes_2__Ink2_r32c13', _guard_a2_lower_ink2_takes_2__Ink2_r32c13, _effect_a2_lower_ink2_takes_2__Ink2_r32c13, ['Ink2_r32c13']),
    ('a2_lower_ink2_takes_2__Ink2_r32c14', _guard_a2_lower_ink2_takes_2__Ink2_r32c14, _effect_a2_lower_ink2_takes_2__Ink2_r32c14, ['Ink2_r32c14']),
    ('a2_lower_ink2_takes_2__Ink2_r33c13', _guard_a2_lower_ink2_takes_2__Ink2_r33c13, _effect_a2_lower_ink2_takes_2__Ink2_r33c13, ['Ink2_r33c13']),
    ('a2_lower_ink2_takes_2__Ink2_r33c14', _guard_a2_lower_ink2_takes_2__Ink2_r33c14, _effect_a2_lower_ink2_takes_2__Ink2_r33c14, ['Ink2_r33c14']),
    ('a2_lower_ink2_takes_2__Ink2_r38c17', _guard_a2_lower_ink2_takes_2__Ink2_r38c17, _effect_a2_lower_ink2_takes_2__Ink2_r38c17, ['Ink2_r38c17']),
    ('a2_lower_ink2_takes_2__Ink2_r38c20', _guard_a2_lower_ink2_takes_2__Ink2_r38c20, _effect_a2_lower_ink2_takes_2__Ink2_r38c20, ['Ink2_r38c20']),
    ('a2_lower_ink2_takes_2__Ink2_r39c16', _guard_a2_lower_ink2_takes_2__Ink2_r39c16, _effect_a2_lower_ink2_takes_2__Ink2_r39c16, ['Ink2_r39c16']),
    ('a2_lower_ink2_takes_2__Ink2_r39c19', _guard_a2_lower_ink2_takes_2__Ink2_r39c19, _effect_a2_lower_ink2_takes_2__Ink2_r39c19, ['Ink2_r39c19']),
    ('a2_lower_ink2_takes_2__Ink2_r39c22', _guard_a2_lower_ink2_takes_2__Ink2_r39c22, _effect_a2_lower_ink2_takes_2__Ink2_r39c22, ['Ink2_r39c22']),
    ('a2_lower_ink2_takes_2__Ink2_r53c63', _guard_a2_lower_ink2_takes_2__Ink2_r53c63, _effect_a2_lower_ink2_takes_2__Ink2_r53c63, ['Ink2_r53c63']),
    ('a2_icon2_body_takes_6__Ink6_r36c11', _guard_a2_icon2_body_takes_6__Ink6_r36c11, _effect_a2_icon2_body_takes_6__Ink6_r36c11, ['Ink6_r36c11']),
    ('a2_icon2_body_takes_6__Ink6_r36c12', _guard_a2_icon2_body_takes_6__Ink6_r36c12, _effect_a2_icon2_body_takes_6__Ink6_r36c12, ['Ink6_r36c12']),
    ('a2_icon2_body_takes_6__Ink6_r36c13', _guard_a2_icon2_body_takes_6__Ink6_r36c13, _effect_a2_icon2_body_takes_6__Ink6_r36c13, ['Ink6_r36c13']),
    ('a2_icon2_body_takes_6__Ink6_r36c14', _guard_a2_icon2_body_takes_6__Ink6_r36c14, _effect_a2_icon2_body_takes_6__Ink6_r36c14, ['Ink6_r36c14']),
    ('a2_icon2_body_takes_6__Ink6_r36c15', _guard_a2_icon2_body_takes_6__Ink6_r36c15, _effect_a2_icon2_body_takes_6__Ink6_r36c15, ['Ink6_r36c15']),
    ('a2_icon2_body_takes_6__Ink6_r36c16', _guard_a2_icon2_body_takes_6__Ink6_r36c16, _effect_a2_icon2_body_takes_6__Ink6_r36c16, ['Ink6_r36c16']),
    ('a2_icon2_body_takes_6__Ink6_r37c11', _guard_a2_icon2_body_takes_6__Ink6_r37c11, _effect_a2_icon2_body_takes_6__Ink6_r37c11, ['Ink6_r37c11']),
    ('a2_icon2_body_takes_6__Ink6_r37c16', _guard_a2_icon2_body_takes_6__Ink6_r37c16, _effect_a2_icon2_body_takes_6__Ink6_r37c16, ['Ink6_r37c16']),
    ('a2_icon2_body_takes_6__Ink6_r38c11', _guard_a2_icon2_body_takes_6__Ink6_r38c11, _effect_a2_icon2_body_takes_6__Ink6_r38c11, ['Ink6_r38c11']),
    ('a2_icon2_body_takes_6__Ink6_r38c13', _guard_a2_icon2_body_takes_6__Ink6_r38c13, _effect_a2_icon2_body_takes_6__Ink6_r38c13, ['Ink6_r38c13']),
    ('a2_icon2_body_takes_6__Ink6_r38c14', _guard_a2_icon2_body_takes_6__Ink6_r38c14, _effect_a2_icon2_body_takes_6__Ink6_r38c14, ['Ink6_r38c14']),
    ('a2_icon2_body_takes_6__Ink6_r39c11', _guard_a2_icon2_body_takes_6__Ink6_r39c11, _effect_a2_icon2_body_takes_6__Ink6_r39c11, ['Ink6_r39c11']),
    ('a2_icon2_body_takes_6__Ink6_r39c13', _guard_a2_icon2_body_takes_6__Ink6_r39c13, _effect_a2_icon2_body_takes_6__Ink6_r39c13, ['Ink6_r39c13']),
    ('a2_icon2_body_takes_6__Ink6_r39c14', _guard_a2_icon2_body_takes_6__Ink6_r39c14, _effect_a2_icon2_body_takes_6__Ink6_r39c14, ['Ink6_r39c14']),
    ('a2_icon2_body_takes_6__Ink6_r40c11', _guard_a2_icon2_body_takes_6__Ink6_r40c11, _effect_a2_icon2_body_takes_6__Ink6_r40c11, ['Ink6_r40c11']),
    ('a2_icon2_body_takes_6__Ink6_r40c16', _guard_a2_icon2_body_takes_6__Ink6_r40c16, _effect_a2_icon2_body_takes_6__Ink6_r40c16, ['Ink6_r40c16']),
    ('a2_icon2_body_takes_6__Ink6_r41c11', _guard_a2_icon2_body_takes_6__Ink6_r41c11, _effect_a2_icon2_body_takes_6__Ink6_r41c11, ['Ink6_r41c11']),
    ('a2_icon2_body_takes_6__Ink6_r41c12', _guard_a2_icon2_body_takes_6__Ink6_r41c12, _effect_a2_icon2_body_takes_6__Ink6_r41c12, ['Ink6_r41c12']),
    ('a2_icon2_body_takes_6__Ink6_r41c13', _guard_a2_icon2_body_takes_6__Ink6_r41c13, _effect_a2_icon2_body_takes_6__Ink6_r41c13, ['Ink6_r41c13']),
    ('a2_icon2_body_takes_6__Ink6_r41c14', _guard_a2_icon2_body_takes_6__Ink6_r41c14, _effect_a2_icon2_body_takes_6__Ink6_r41c14, ['Ink6_r41c14']),
    ('a2_icon2_body_takes_6__Ink6_r41c15', _guard_a2_icon2_body_takes_6__Ink6_r41c15, _effect_a2_icon2_body_takes_6__Ink6_r41c15, ['Ink6_r41c15']),
    ('a2_icon2_body_takes_6__Ink6_r41c16', _guard_a2_icon2_body_takes_6__Ink6_r41c16, _effect_a2_icon2_body_takes_6__Ink6_r41c16, ['Ink6_r41c16']),
    ('a2_icon2_hole_takes_0__Ink0_r37c12', _guard_a2_icon2_hole_takes_0__Ink0_r37c12, _effect_a2_icon2_hole_takes_0__Ink0_r37c12, ['Ink0_r37c12']),
    ('a2_icon2_hole_takes_0__Ink0_r37c13', _guard_a2_icon2_hole_takes_0__Ink0_r37c13, _effect_a2_icon2_hole_takes_0__Ink0_r37c13, ['Ink0_r37c13']),
    ('a2_icon2_hole_takes_0__Ink0_r37c14', _guard_a2_icon2_hole_takes_0__Ink0_r37c14, _effect_a2_icon2_hole_takes_0__Ink0_r37c14, ['Ink0_r37c14']),
    ('a2_icon2_hole_takes_0__Ink0_r37c15', _guard_a2_icon2_hole_takes_0__Ink0_r37c15, _effect_a2_icon2_hole_takes_0__Ink0_r37c15, ['Ink0_r37c15']),
    ('a2_icon2_hole_takes_0__Ink0_r38c12', _guard_a2_icon2_hole_takes_0__Ink0_r38c12, _effect_a2_icon2_hole_takes_0__Ink0_r38c12, ['Ink0_r38c12']),
    ('a2_icon2_hole_takes_0__Ink0_r38c15', _guard_a2_icon2_hole_takes_0__Ink0_r38c15, _effect_a2_icon2_hole_takes_0__Ink0_r38c15, ['Ink0_r38c15']),
    ('a2_icon2_hole_takes_0__Ink0_r39c12', _guard_a2_icon2_hole_takes_0__Ink0_r39c12, _effect_a2_icon2_hole_takes_0__Ink0_r39c12, ['Ink0_r39c12']),
    ('a2_icon2_hole_takes_0__Ink0_r39c15', _guard_a2_icon2_hole_takes_0__Ink0_r39c15, _effect_a2_icon2_hole_takes_0__Ink0_r39c15, ['Ink0_r39c15']),
    ('a2_icon2_hole_takes_0__Ink0_r40c12', _guard_a2_icon2_hole_takes_0__Ink0_r40c12, _effect_a2_icon2_hole_takes_0__Ink0_r40c12, ['Ink0_r40c12']),
    ('a2_icon2_hole_takes_0__Ink0_r40c13', _guard_a2_icon2_hole_takes_0__Ink0_r40c13, _effect_a2_icon2_hole_takes_0__Ink0_r40c13, ['Ink0_r40c13']),
    ('a2_icon2_hole_takes_0__Ink0_r40c14', _guard_a2_icon2_hole_takes_0__Ink0_r40c14, _effect_a2_icon2_hole_takes_0__Ink0_r40c14, ['Ink0_r40c14']),
    ('a2_icon2_hole_takes_0__Ink0_r40c15', _guard_a2_icon2_hole_takes_0__Ink0_r40c15, _effect_a2_icon2_hole_takes_0__Ink0_r40c15, ['Ink0_r40c15']),
    ('a2_tape2_takes_1__Ink1_r38c16', _guard_a2_tape2_takes_1__Ink1_r38c16, _effect_a2_tape2_takes_1__Ink1_r38c16, ['Ink1_r38c16']),
    ('a2_tape2_takes_1__Ink1_r38c18', _guard_a2_tape2_takes_1__Ink1_r38c18, _effect_a2_tape2_takes_1__Ink1_r38c18, ['Ink1_r38c18']),
    ('a2_tape2_takes_1__Ink1_r38c19', _guard_a2_tape2_takes_1__Ink1_r38c19, _effect_a2_tape2_takes_1__Ink1_r38c19, ['Ink1_r38c19']),
    ('a2_tape2_takes_1__Ink1_r38c21', _guard_a2_tape2_takes_1__Ink1_r38c21, _effect_a2_tape2_takes_1__Ink1_r38c21, ['Ink1_r38c21']),
    ('a2_tape2_takes_1__Ink1_r38c22', _guard_a2_tape2_takes_1__Ink1_r38c22, _effect_a2_tape2_takes_1__Ink1_r38c22, ['Ink1_r38c22']),
    ('a2_tape2_takes_1__Ink1_r39c17', _guard_a2_tape2_takes_1__Ink1_r39c17, _effect_a2_tape2_takes_1__Ink1_r39c17, ['Ink1_r39c17']),
    ('a2_tape2_takes_1__Ink1_r39c18', _guard_a2_tape2_takes_1__Ink1_r39c18, _effect_a2_tape2_takes_1__Ink1_r39c18, ['Ink1_r39c18']),
    ('a2_tape2_takes_1__Ink1_r39c20', _guard_a2_tape2_takes_1__Ink1_r39c20, _effect_a2_tape2_takes_1__Ink1_r39c20, ['Ink1_r39c20']),
    ('a2_tape2_takes_1__Ink1_r39c21', _guard_a2_tape2_takes_1__Ink1_r39c21, _effect_a2_tape2_takes_1__Ink1_r39c21, ['Ink1_r39c21']),
    ('a3_hides_tape2_ones__Ink1_r38c16', _guard_a3_hides_tape2_ones__Ink1_r38c16, _effect_a3_hides_tape2_ones__Ink1_r38c16, ['Ink1_r38c16']),
    ('a3_hides_tape2_ones__Ink1_r38c18', _guard_a3_hides_tape2_ones__Ink1_r38c18, _effect_a3_hides_tape2_ones__Ink1_r38c18, ['Ink1_r38c18']),
    ('a3_hides_tape2_ones__Ink1_r38c19', _guard_a3_hides_tape2_ones__Ink1_r38c19, _effect_a3_hides_tape2_ones__Ink1_r38c19, ['Ink1_r38c19']),
    ('a3_hides_tape2_ones__Ink1_r38c21', _guard_a3_hides_tape2_ones__Ink1_r38c21, _effect_a3_hides_tape2_ones__Ink1_r38c21, ['Ink1_r38c21']),
    ('a3_hides_tape2_ones__Ink1_r38c22', _guard_a3_hides_tape2_ones__Ink1_r38c22, _effect_a3_hides_tape2_ones__Ink1_r38c22, ['Ink1_r38c22']),
    ('a3_hides_tape2_ones__Ink1_r39c17', _guard_a3_hides_tape2_ones__Ink1_r39c17, _effect_a3_hides_tape2_ones__Ink1_r39c17, ['Ink1_r39c17']),
    ('a3_hides_tape2_ones__Ink1_r39c18', _guard_a3_hides_tape2_ones__Ink1_r39c18, _effect_a3_hides_tape2_ones__Ink1_r39c18, ['Ink1_r39c18']),
    ('a3_hides_tape2_ones__Ink1_r39c20', _guard_a3_hides_tape2_ones__Ink1_r39c20, _effect_a3_hides_tape2_ones__Ink1_r39c20, ['Ink1_r39c20']),
    ('a3_hides_tape2_ones__Ink1_r39c21', _guard_a3_hides_tape2_ones__Ink1_r39c21, _effect_a3_hides_tape2_ones__Ink1_r39c21, ['Ink1_r39c21']),
    ('a3_hides_tape2_twos__Ink2_r32c13', _guard_a3_hides_tape2_twos__Ink2_r32c13, _effect_a3_hides_tape2_twos__Ink2_r32c13, ['Ink2_r32c13']),
    ('a3_hides_tape2_twos__Ink2_r32c14', _guard_a3_hides_tape2_twos__Ink2_r32c14, _effect_a3_hides_tape2_twos__Ink2_r32c14, ['Ink2_r32c14']),
    ('a3_hides_tape2_twos__Ink2_r33c13', _guard_a3_hides_tape2_twos__Ink2_r33c13, _effect_a3_hides_tape2_twos__Ink2_r33c13, ['Ink2_r33c13']),
    ('a3_hides_tape2_twos__Ink2_r33c14', _guard_a3_hides_tape2_twos__Ink2_r33c14, _effect_a3_hides_tape2_twos__Ink2_r33c14, ['Ink2_r33c14']),
    ('a3_hides_tape2_twos__Ink2_r38c17', _guard_a3_hides_tape2_twos__Ink2_r38c17, _effect_a3_hides_tape2_twos__Ink2_r38c17, ['Ink2_r38c17']),
    ('a3_hides_tape2_twos__Ink2_r38c20', _guard_a3_hides_tape2_twos__Ink2_r38c20, _effect_a3_hides_tape2_twos__Ink2_r38c20, ['Ink2_r38c20']),
    ('a3_hides_tape2_twos__Ink2_r39c16', _guard_a3_hides_tape2_twos__Ink2_r39c16, _effect_a3_hides_tape2_twos__Ink2_r39c16, ['Ink2_r39c16']),
    ('a3_hides_tape2_twos__Ink2_r39c19', _guard_a3_hides_tape2_twos__Ink2_r39c19, _effect_a3_hides_tape2_twos__Ink2_r39c19, ['Ink2_r39c19']),
    ('a3_hides_tape2_twos__Ink2_r39c22', _guard_a3_hides_tape2_twos__Ink2_r39c22, _effect_a3_hides_tape2_twos__Ink2_r39c22, ['Ink2_r39c22']),
    ('a3_hides_tape2_twos__Ink2_r53c63', _guard_a3_hides_tape2_twos__Ink2_r53c63, _effect_a3_hides_tape2_twos__Ink2_r53c63, ['Ink2_r53c63']),
    ('a7_hides_tape2_ones__Ink1_r38c16', _guard_a7_hides_tape2_ones__Ink1_r38c16, _effect_a7_hides_tape2_ones__Ink1_r38c16, ['Ink1_r38c16']),
    ('a7_hides_tape2_ones__Ink1_r38c18', _guard_a7_hides_tape2_ones__Ink1_r38c18, _effect_a7_hides_tape2_ones__Ink1_r38c18, ['Ink1_r38c18']),
    ('a7_hides_tape2_ones__Ink1_r38c19', _guard_a7_hides_tape2_ones__Ink1_r38c19, _effect_a7_hides_tape2_ones__Ink1_r38c19, ['Ink1_r38c19']),
    ('a7_hides_tape2_ones__Ink1_r38c21', _guard_a7_hides_tape2_ones__Ink1_r38c21, _effect_a7_hides_tape2_ones__Ink1_r38c21, ['Ink1_r38c21']),
    ('a7_hides_tape2_ones__Ink1_r38c22', _guard_a7_hides_tape2_ones__Ink1_r38c22, _effect_a7_hides_tape2_ones__Ink1_r38c22, ['Ink1_r38c22']),
    ('a7_hides_tape2_ones__Ink1_r39c17', _guard_a7_hides_tape2_ones__Ink1_r39c17, _effect_a7_hides_tape2_ones__Ink1_r39c17, ['Ink1_r39c17']),
    ('a7_hides_tape2_ones__Ink1_r39c18', _guard_a7_hides_tape2_ones__Ink1_r39c18, _effect_a7_hides_tape2_ones__Ink1_r39c18, ['Ink1_r39c18']),
    ('a7_hides_tape2_ones__Ink1_r39c20', _guard_a7_hides_tape2_ones__Ink1_r39c20, _effect_a7_hides_tape2_ones__Ink1_r39c20, ['Ink1_r39c20']),
    ('a7_hides_tape2_ones__Ink1_r39c21', _guard_a7_hides_tape2_ones__Ink1_r39c21, _effect_a7_hides_tape2_ones__Ink1_r39c21, ['Ink1_r39c21']),
    ('a7_hides_tape2_twos__Ink2_r32c13', _guard_a7_hides_tape2_twos__Ink2_r32c13, _effect_a7_hides_tape2_twos__Ink2_r32c13, ['Ink2_r32c13']),
    ('a7_hides_tape2_twos__Ink2_r32c14', _guard_a7_hides_tape2_twos__Ink2_r32c14, _effect_a7_hides_tape2_twos__Ink2_r32c14, ['Ink2_r32c14']),
    ('a7_hides_tape2_twos__Ink2_r33c13', _guard_a7_hides_tape2_twos__Ink2_r33c13, _effect_a7_hides_tape2_twos__Ink2_r33c13, ['Ink2_r33c13']),
    ('a7_hides_tape2_twos__Ink2_r33c14', _guard_a7_hides_tape2_twos__Ink2_r33c14, _effect_a7_hides_tape2_twos__Ink2_r33c14, ['Ink2_r33c14']),
    ('a7_hides_tape2_twos__Ink2_r38c17', _guard_a7_hides_tape2_twos__Ink2_r38c17, _effect_a7_hides_tape2_twos__Ink2_r38c17, ['Ink2_r38c17']),
    ('a7_hides_tape2_twos__Ink2_r38c20', _guard_a7_hides_tape2_twos__Ink2_r38c20, _effect_a7_hides_tape2_twos__Ink2_r38c20, ['Ink2_r38c20']),
    ('a7_hides_tape2_twos__Ink2_r39c16', _guard_a7_hides_tape2_twos__Ink2_r39c16, _effect_a7_hides_tape2_twos__Ink2_r39c16, ['Ink2_r39c16']),
    ('a7_hides_tape2_twos__Ink2_r39c19', _guard_a7_hides_tape2_twos__Ink2_r39c19, _effect_a7_hides_tape2_twos__Ink2_r39c19, ['Ink2_r39c19']),
    ('a7_hides_tape2_twos__Ink2_r39c22', _guard_a7_hides_tape2_twos__Ink2_r39c22, _effect_a7_hides_tape2_twos__Ink2_r39c22, ['Ink2_r39c22']),
    ('a7_hides_tape2_twos__Ink2_r53c63', _guard_a7_hides_tape2_twos__Ink2_r53c63, _effect_a7_hides_tape2_twos__Ink2_r53c63, ['Ink2_r53c63']),
    ('a4_shows_tape2_ones__Ink1_r38c16', _guard_a4_shows_tape2_ones__Ink1_r38c16, _effect_a4_shows_tape2_ones__Ink1_r38c16, ['Ink1_r38c16']),
    ('a4_shows_tape2_ones__Ink1_r38c18', _guard_a4_shows_tape2_ones__Ink1_r38c18, _effect_a4_shows_tape2_ones__Ink1_r38c18, ['Ink1_r38c18']),
    ('a4_shows_tape2_ones__Ink1_r38c19', _guard_a4_shows_tape2_ones__Ink1_r38c19, _effect_a4_shows_tape2_ones__Ink1_r38c19, ['Ink1_r38c19']),
    ('a4_shows_tape2_ones__Ink1_r38c21', _guard_a4_shows_tape2_ones__Ink1_r38c21, _effect_a4_shows_tape2_ones__Ink1_r38c21, ['Ink1_r38c21']),
    ('a4_shows_tape2_ones__Ink1_r38c22', _guard_a4_shows_tape2_ones__Ink1_r38c22, _effect_a4_shows_tape2_ones__Ink1_r38c22, ['Ink1_r38c22']),
    ('a4_shows_tape2_ones__Ink1_r39c17', _guard_a4_shows_tape2_ones__Ink1_r39c17, _effect_a4_shows_tape2_ones__Ink1_r39c17, ['Ink1_r39c17']),
    ('a4_shows_tape2_ones__Ink1_r39c18', _guard_a4_shows_tape2_ones__Ink1_r39c18, _effect_a4_shows_tape2_ones__Ink1_r39c18, ['Ink1_r39c18']),
    ('a4_shows_tape2_ones__Ink1_r39c20', _guard_a4_shows_tape2_ones__Ink1_r39c20, _effect_a4_shows_tape2_ones__Ink1_r39c20, ['Ink1_r39c20']),
    ('a4_shows_tape2_ones__Ink1_r39c21', _guard_a4_shows_tape2_ones__Ink1_r39c21, _effect_a4_shows_tape2_ones__Ink1_r39c21, ['Ink1_r39c21']),
    ('a4_shows_tape2_twos__Ink2_r32c13', _guard_a4_shows_tape2_twos__Ink2_r32c13, _effect_a4_shows_tape2_twos__Ink2_r32c13, ['Ink2_r32c13']),
    ('a4_shows_tape2_twos__Ink2_r32c14', _guard_a4_shows_tape2_twos__Ink2_r32c14, _effect_a4_shows_tape2_twos__Ink2_r32c14, ['Ink2_r32c14']),
    ('a4_shows_tape2_twos__Ink2_r33c13', _guard_a4_shows_tape2_twos__Ink2_r33c13, _effect_a4_shows_tape2_twos__Ink2_r33c13, ['Ink2_r33c13']),
    ('a4_shows_tape2_twos__Ink2_r33c14', _guard_a4_shows_tape2_twos__Ink2_r33c14, _effect_a4_shows_tape2_twos__Ink2_r33c14, ['Ink2_r33c14']),
    ('a4_shows_tape2_twos__Ink2_r38c17', _guard_a4_shows_tape2_twos__Ink2_r38c17, _effect_a4_shows_tape2_twos__Ink2_r38c17, ['Ink2_r38c17']),
    ('a4_shows_tape2_twos__Ink2_r38c20', _guard_a4_shows_tape2_twos__Ink2_r38c20, _effect_a4_shows_tape2_twos__Ink2_r38c20, ['Ink2_r38c20']),
    ('a4_shows_tape2_twos__Ink2_r39c16', _guard_a4_shows_tape2_twos__Ink2_r39c16, _effect_a4_shows_tape2_twos__Ink2_r39c16, ['Ink2_r39c16']),
    ('a4_shows_tape2_twos__Ink2_r39c19', _guard_a4_shows_tape2_twos__Ink2_r39c19, _effect_a4_shows_tape2_twos__Ink2_r39c19, ['Ink2_r39c19']),
    ('a4_shows_tape2_twos__Ink2_r39c22', _guard_a4_shows_tape2_twos__Ink2_r39c22, _effect_a4_shows_tape2_twos__Ink2_r39c22, ['Ink2_r39c22']),
    ('a4_shows_tape2_twos__Ink2_r53c63', _guard_a4_shows_tape2_twos__Ink2_r53c63, _effect_a4_shows_tape2_twos__Ink2_r53c63, ['Ink2_r53c63']),
    ('a4_advances_the_corner_pixel__Ink2_r32c13', _guard_a4_advances_the_corner_pixel__Ink2_r32c13, _effect_a4_advances_the_corner_pixel__Ink2_r32c13, ['Ink2_r32c13']),
    ('a4_advances_the_corner_pixel__Ink2_r32c14', _guard_a4_advances_the_corner_pixel__Ink2_r32c14, _effect_a4_advances_the_corner_pixel__Ink2_r32c14, ['Ink2_r32c14']),
    ('a4_advances_the_corner_pixel__Ink2_r33c13', _guard_a4_advances_the_corner_pixel__Ink2_r33c13, _effect_a4_advances_the_corner_pixel__Ink2_r33c13, ['Ink2_r33c13']),
    ('a4_advances_the_corner_pixel__Ink2_r33c14', _guard_a4_advances_the_corner_pixel__Ink2_r33c14, _effect_a4_advances_the_corner_pixel__Ink2_r33c14, ['Ink2_r33c14']),
    ('a4_advances_the_corner_pixel__Ink2_r38c17', _guard_a4_advances_the_corner_pixel__Ink2_r38c17, _effect_a4_advances_the_corner_pixel__Ink2_r38c17, ['Ink2_r38c17']),
    ('a4_advances_the_corner_pixel__Ink2_r38c20', _guard_a4_advances_the_corner_pixel__Ink2_r38c20, _effect_a4_advances_the_corner_pixel__Ink2_r38c20, ['Ink2_r38c20']),
    ('a4_advances_the_corner_pixel__Ink2_r39c16', _guard_a4_advances_the_corner_pixel__Ink2_r39c16, _effect_a4_advances_the_corner_pixel__Ink2_r39c16, ['Ink2_r39c16']),
    ('a4_advances_the_corner_pixel__Ink2_r39c19', _guard_a4_advances_the_corner_pixel__Ink2_r39c19, _effect_a4_advances_the_corner_pixel__Ink2_r39c19, ['Ink2_r39c19']),
    ('a4_advances_the_corner_pixel__Ink2_r39c22', _guard_a4_advances_the_corner_pixel__Ink2_r39c22, _effect_a4_advances_the_corner_pixel__Ink2_r39c22, ['Ink2_r39c22']),
    ('a4_advances_the_corner_pixel__Ink2_r53c63', _guard_a4_advances_the_corner_pixel__Ink2_r53c63, _effect_a4_advances_the_corner_pixel__Ink2_r53c63, ['Ink2_r53c63']),
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
        Ink0_r37c12_pos=(37, 12),
        Ink0_r37c12_color=0,
        Ink0_r37c13_pos=(37, 13),
        Ink0_r37c13_color=0,
        Ink0_r37c14_pos=(37, 14),
        Ink0_r37c14_color=0,
        Ink0_r37c15_pos=(37, 15),
        Ink0_r37c15_color=0,
        Ink0_r38c12_pos=(38, 12),
        Ink0_r38c12_color=0,
        Ink0_r38c15_pos=(38, 15),
        Ink0_r38c15_color=0,
        Ink0_r39c12_pos=(39, 12),
        Ink0_r39c12_color=0,
        Ink0_r39c15_pos=(39, 15),
        Ink0_r39c15_color=0,
        Ink0_r40c12_pos=(40, 12),
        Ink0_r40c12_color=0,
        Ink0_r40c13_pos=(40, 13),
        Ink0_r40c13_color=0,
        Ink0_r40c14_pos=(40, 14),
        Ink0_r40c14_color=0,
        Ink0_r40c15_pos=(40, 15),
        Ink0_r40c15_color=0,
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
        Ink4_r32c17_pos=(32, 17),
        Ink4_r32c17_color=4,
        Ink4_r32c18_pos=(32, 18),
        Ink4_r32c18_color=4,
        Ink4_r32c19_pos=(32, 19),
        Ink4_r32c19_color=4,
        Ink4_r32c20_pos=(32, 20),
        Ink4_r32c20_color=4,
        Ink4_r32c21_pos=(32, 21),
        Ink4_r32c21_color=4,
        Ink4_r32c22_pos=(32, 22),
        Ink4_r32c22_color=4,
        Ink4_r33c17_pos=(33, 17),
        Ink4_r33c17_color=4,
        Ink4_r33c18_pos=(33, 18),
        Ink4_r33c18_color=4,
        Ink4_r33c19_pos=(33, 19),
        Ink4_r33c19_color=4,
        Ink4_r33c20_pos=(33, 20),
        Ink4_r33c20_color=4,
        Ink4_r33c21_pos=(33, 21),
        Ink4_r33c21_color=4,
        Ink4_r33c22_pos=(33, 22),
        Ink4_r33c22_color=4,
        Ink5_r30c11_pos=(30, 11),
        Ink5_r30c11_color=5,
        Ink5_r30c12_pos=(30, 12),
        Ink5_r30c12_color=5,
        Ink5_r30c15_pos=(30, 15),
        Ink5_r30c15_color=5,
        Ink5_r30c16_pos=(30, 16),
        Ink5_r30c16_color=5,
        Ink5_r31c11_pos=(31, 11),
        Ink5_r31c11_color=5,
        Ink5_r31c12_pos=(31, 12),
        Ink5_r31c12_color=5,
        Ink5_r31c15_pos=(31, 15),
        Ink5_r31c15_color=5,
        Ink5_r31c16_pos=(31, 16),
        Ink5_r31c16_color=5,
        Ink5_r32c11_pos=(32, 11),
        Ink5_r32c11_color=5,
        Ink5_r32c12_pos=(32, 12),
        Ink5_r32c12_color=5,
        Ink5_r32c15_pos=(32, 15),
        Ink5_r32c15_color=5,
        Ink5_r32c16_pos=(32, 16),
        Ink5_r32c16_color=5,
        Ink5_r33c11_pos=(33, 11),
        Ink5_r33c11_color=5,
        Ink5_r33c12_pos=(33, 12),
        Ink5_r33c12_color=5,
        Ink5_r33c15_pos=(33, 15),
        Ink5_r33c15_color=5,
        Ink5_r33c16_pos=(33, 16),
        Ink5_r33c16_color=5,
        Ink5_r34c11_pos=(34, 11),
        Ink5_r34c11_color=5,
        Ink5_r34c12_pos=(34, 12),
        Ink5_r34c12_color=5,
        Ink5_r34c15_pos=(34, 15),
        Ink5_r34c15_color=5,
        Ink5_r34c16_pos=(34, 16),
        Ink5_r34c16_color=5,
        Ink5_r35c11_pos=(35, 11),
        Ink5_r35c11_color=5,
        Ink5_r35c12_pos=(35, 12),
        Ink5_r35c12_color=5,
        Ink5_r35c15_pos=(35, 15),
        Ink5_r35c15_color=5,
        Ink5_r35c16_pos=(35, 16),
        Ink5_r35c16_color=5,
        Ink6_r36c11_pos=(36, 11),
        Ink6_r36c11_color=6,
        Ink6_r36c12_pos=(36, 12),
        Ink6_r36c12_color=6,
        Ink6_r36c13_pos=(36, 13),
        Ink6_r36c13_color=6,
        Ink6_r36c14_pos=(36, 14),
        Ink6_r36c14_color=6,
        Ink6_r36c15_pos=(36, 15),
        Ink6_r36c15_color=6,
        Ink6_r36c16_pos=(36, 16),
        Ink6_r36c16_color=6,
        Ink6_r37c11_pos=(37, 11),
        Ink6_r37c11_color=6,
        Ink6_r37c16_pos=(37, 16),
        Ink6_r37c16_color=6,
        Ink6_r38c11_pos=(38, 11),
        Ink6_r38c11_color=6,
        Ink6_r38c13_pos=(38, 13),
        Ink6_r38c13_color=6,
        Ink6_r38c14_pos=(38, 14),
        Ink6_r38c14_color=6,
        Ink6_r39c11_pos=(39, 11),
        Ink6_r39c11_color=6,
        Ink6_r39c13_pos=(39, 13),
        Ink6_r39c13_color=6,
        Ink6_r39c14_pos=(39, 14),
        Ink6_r39c14_color=6,
        Ink6_r40c11_pos=(40, 11),
        Ink6_r40c11_color=6,
        Ink6_r40c16_pos=(40, 16),
        Ink6_r40c16_color=6,
        Ink6_r41c11_pos=(41, 11),
        Ink6_r41c11_color=6,
        Ink6_r41c12_pos=(41, 12),
        Ink6_r41c12_color=6,
        Ink6_r41c13_pos=(41, 13),
        Ink6_r41c13_color=6,
        Ink6_r41c14_pos=(41, 14),
        Ink6_r41c14_color=6,
        Ink6_r41c15_pos=(41, 15),
        Ink6_r41c15_color=6,
        Ink6_r41c16_pos=(41, 16),
        Ink6_r41c16_color=6,
    )
