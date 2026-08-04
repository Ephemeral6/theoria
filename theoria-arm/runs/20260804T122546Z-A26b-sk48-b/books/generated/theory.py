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
LANDMARKS = {'bottom_port': (38, 16)}
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
ACTIONS = [('key', 1), ('key', 2), ('key', 3), ('key', 4), ('key', 7)]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Field_r30c11_pos: object = (30, 11)
    Field_r30c11_color: object = 5
    Field_r30c12_pos: object = (30, 12)
    Field_r30c12_color: object = 5
    Field_r30c15_pos: object = (30, 15)
    Field_r30c15_color: object = 5
    Field_r30c16_pos: object = (30, 16)
    Field_r30c16_color: object = 5
    Field_r31c11_pos: object = (31, 11)
    Field_r31c11_color: object = 5
    Field_r31c12_pos: object = (31, 12)
    Field_r31c12_color: object = 5
    Field_r31c15_pos: object = (31, 15)
    Field_r31c15_color: object = 5
    Field_r31c16_pos: object = (31, 16)
    Field_r31c16_color: object = 5
    Field_r32c11_pos: object = (32, 11)
    Field_r32c11_color: object = 5
    Field_r32c12_pos: object = (32, 12)
    Field_r32c12_color: object = 5
    Field_r32c15_pos: object = (32, 15)
    Field_r32c15_color: object = 5
    Field_r32c16_pos: object = (32, 16)
    Field_r32c16_color: object = 5
    Field_r33c11_pos: object = (33, 11)
    Field_r33c11_color: object = 5
    Field_r33c12_pos: object = (33, 12)
    Field_r33c12_color: object = 5
    Field_r33c15_pos: object = (33, 15)
    Field_r33c15_color: object = 5
    Field_r33c16_pos: object = (33, 16)
    Field_r33c16_color: object = 5
    Field_r34c11_pos: object = (34, 11)
    Field_r34c11_color: object = 5
    Field_r34c12_pos: object = (34, 12)
    Field_r34c12_color: object = 5
    Field_r34c15_pos: object = (34, 15)
    Field_r34c15_color: object = 5
    Field_r34c16_pos: object = (34, 16)
    Field_r34c16_color: object = 5
    Field_r35c11_pos: object = (35, 11)
    Field_r35c11_color: object = 5
    Field_r35c12_pos: object = (35, 12)
    Field_r35c12_color: object = 5
    Field_r35c15_pos: object = (35, 15)
    Field_r35c15_color: object = 5
    Field_r35c16_pos: object = (35, 16)
    Field_r35c16_color: object = 5
    BarBody_r30c13_pos: object = (30, 13)
    BarBody_r30c13_color: object = 3
    BarBody_r30c14_pos: object = (30, 14)
    BarBody_r30c14_color: object = 3
    BarBody_r31c13_pos: object = (31, 13)
    BarBody_r31c13_color: object = 3
    BarBody_r31c14_pos: object = (31, 14)
    BarBody_r31c14_color: object = 3
    BarBody_r34c13_pos: object = (34, 13)
    BarBody_r34c13_color: object = 3
    BarBody_r34c14_pos: object = (34, 14)
    BarBody_r34c14_color: object = 3
    BarBody_r35c13_pos: object = (35, 13)
    BarBody_r35c13_color: object = 3
    BarBody_r35c14_pos: object = (35, 14)
    BarBody_r35c14_color: object = 3
    BarCore_r32c13_pos: object = (32, 13)
    BarCore_r32c13_color: object = 2
    BarCore_r32c14_pos: object = (32, 14)
    BarCore_r32c14_color: object = 2
    BarCore_r33c13_pos: object = (33, 13)
    BarCore_r33c13_color: object = 2
    BarCore_r33c14_pos: object = (33, 14)
    BarCore_r33c14_color: object = 2
    BarCore_r38c17_pos: object = (38, 17)
    BarCore_r38c17_color: object = 2
    BarCore_r38c20_pos: object = (38, 20)
    BarCore_r38c20_color: object = 2
    BarCore_r39c16_pos: object = (39, 16)
    BarCore_r39c16_color: object = 2
    BarCore_r39c19_pos: object = (39, 19)
    BarCore_r39c19_color: object = 2
    BarCore_r39c22_pos: object = (39, 22)
    BarCore_r39c22_color: object = 2
    BarCore_r53c59_pos: object = (53, 59)
    BarCore_r53c59_color: object = 2
    BarCore_r53c60_pos: object = (53, 60)
    BarCore_r53c60_color: object = 2
    BarCore_r53c61_pos: object = (53, 61)
    BarCore_r53c61_color: object = 2
    BarCore_r53c62_pos: object = (53, 62)
    BarCore_r53c62_color: object = 2
    BarCore_r53c63_pos: object = (53, 63)
    BarCore_r53c63_color: object = 2
    Blank_r32c17_pos: object = (32, 17)
    Blank_r32c17_color: object = 4
    Blank_r32c18_pos: object = (32, 18)
    Blank_r32c18_color: object = 4
    Blank_r32c19_pos: object = (32, 19)
    Blank_r32c19_color: object = 4
    Blank_r32c20_pos: object = (32, 20)
    Blank_r32c20_color: object = 4
    Blank_r32c21_pos: object = (32, 21)
    Blank_r32c21_color: object = 4
    Blank_r32c22_pos: object = (32, 22)
    Blank_r32c22_color: object = 4
    Blank_r33c17_pos: object = (33, 17)
    Blank_r33c17_color: object = 4
    Blank_r33c18_pos: object = (33, 18)
    Blank_r33c18_color: object = 4
    Blank_r33c19_pos: object = (33, 19)
    Blank_r33c19_color: object = 4
    Blank_r33c20_pos: object = (33, 20)
    Blank_r33c20_color: object = 4
    Blank_r33c21_pos: object = (33, 21)
    Blank_r33c21_color: object = 4
    Blank_r33c22_pos: object = (33, 22)
    Blank_r33c22_color: object = 4
    Frame_r36c11_pos: object = (36, 11)
    Frame_r36c11_color: object = 6
    Frame_r36c12_pos: object = (36, 12)
    Frame_r36c12_color: object = 6
    Frame_r36c13_pos: object = (36, 13)
    Frame_r36c13_color: object = 6
    Frame_r36c14_pos: object = (36, 14)
    Frame_r36c14_color: object = 6
    Frame_r36c15_pos: object = (36, 15)
    Frame_r36c15_color: object = 6
    Frame_r36c16_pos: object = (36, 16)
    Frame_r36c16_color: object = 6
    Frame_r37c11_pos: object = (37, 11)
    Frame_r37c11_color: object = 6
    Frame_r37c16_pos: object = (37, 16)
    Frame_r37c16_color: object = 6
    Frame_r38c11_pos: object = (38, 11)
    Frame_r38c11_color: object = 6
    Frame_r38c13_pos: object = (38, 13)
    Frame_r38c13_color: object = 6
    Frame_r38c14_pos: object = (38, 14)
    Frame_r38c14_color: object = 6
    Frame_r39c11_pos: object = (39, 11)
    Frame_r39c11_color: object = 6
    Frame_r39c13_pos: object = (39, 13)
    Frame_r39c13_color: object = 6
    Frame_r39c14_pos: object = (39, 14)
    Frame_r39c14_color: object = 6
    Frame_r40c11_pos: object = (40, 11)
    Frame_r40c11_color: object = 6
    Frame_r40c16_pos: object = (40, 16)
    Frame_r40c16_color: object = 6
    Frame_r41c11_pos: object = (41, 11)
    Frame_r41c11_color: object = 6
    Frame_r41c12_pos: object = (41, 12)
    Frame_r41c12_color: object = 6
    Frame_r41c13_pos: object = (41, 13)
    Frame_r41c13_color: object = 6
    Frame_r41c14_pos: object = (41, 14)
    Frame_r41c14_color: object = 6
    Frame_r41c15_pos: object = (41, 15)
    Frame_r41c15_color: object = 6
    Frame_r41c16_pos: object = (41, 16)
    Frame_r41c16_color: object = 6
    Hollow_r37c12_pos: object = (37, 12)
    Hollow_r37c12_color: object = 0
    Hollow_r37c13_pos: object = (37, 13)
    Hollow_r37c13_color: object = 0
    Hollow_r37c14_pos: object = (37, 14)
    Hollow_r37c14_color: object = 0
    Hollow_r37c15_pos: object = (37, 15)
    Hollow_r37c15_color: object = 0
    Hollow_r38c12_pos: object = (38, 12)
    Hollow_r38c12_color: object = 0
    Hollow_r38c15_pos: object = (38, 15)
    Hollow_r38c15_color: object = 0
    Hollow_r39c12_pos: object = (39, 12)
    Hollow_r39c12_color: object = 0
    Hollow_r39c15_pos: object = (39, 15)
    Hollow_r39c15_color: object = 0
    Hollow_r40c12_pos: object = (40, 12)
    Hollow_r40c12_color: object = 0
    Hollow_r40c13_pos: object = (40, 13)
    Hollow_r40c13_color: object = 0
    Hollow_r40c14_pos: object = (40, 14)
    Hollow_r40c14_color: object = 0
    Hollow_r40c15_pos: object = (40, 15)
    Hollow_r40c15_color: object = 0
    Dot_r38c16_pos: object = (38, 16)
    Dot_r38c16_color: object = 1
    Dot_r38c18_pos: object = (38, 18)
    Dot_r38c18_color: object = 1
    Dot_r38c19_pos: object = (38, 19)
    Dot_r38c19_color: object = 1
    Dot_r38c21_pos: object = (38, 21)
    Dot_r38c21_color: object = 1
    Dot_r38c22_pos: object = (38, 22)
    Dot_r38c22_color: object = 1
    Dot_r39c17_pos: object = (39, 17)
    Dot_r39c17_color: object = 1
    Dot_r39c18_pos: object = (39, 18)
    Dot_r39c18_color: object = 1
    Dot_r39c20_pos: object = (39, 20)
    Dot_r39c20_color: object = 1
    Dot_r39c21_pos: object = (39, 21)
    Dot_r39c21_color: object = 1

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Field_r30c11_pos, self.Field_r30c11_color, self.Field_r30c12_pos, self.Field_r30c12_color, self.Field_r30c15_pos, self.Field_r30c15_color, self.Field_r30c16_pos, self.Field_r30c16_color, self.Field_r31c11_pos, self.Field_r31c11_color, self.Field_r31c12_pos, self.Field_r31c12_color, self.Field_r31c15_pos, self.Field_r31c15_color, self.Field_r31c16_pos, self.Field_r31c16_color, self.Field_r32c11_pos, self.Field_r32c11_color, self.Field_r32c12_pos, self.Field_r32c12_color, self.Field_r32c15_pos, self.Field_r32c15_color, self.Field_r32c16_pos, self.Field_r32c16_color, self.Field_r33c11_pos, self.Field_r33c11_color, self.Field_r33c12_pos, self.Field_r33c12_color, self.Field_r33c15_pos, self.Field_r33c15_color, self.Field_r33c16_pos, self.Field_r33c16_color, self.Field_r34c11_pos, self.Field_r34c11_color, self.Field_r34c12_pos, self.Field_r34c12_color, self.Field_r34c15_pos, self.Field_r34c15_color, self.Field_r34c16_pos, self.Field_r34c16_color, self.Field_r35c11_pos, self.Field_r35c11_color, self.Field_r35c12_pos, self.Field_r35c12_color, self.Field_r35c15_pos, self.Field_r35c15_color, self.Field_r35c16_pos, self.Field_r35c16_color, self.BarBody_r30c13_pos, self.BarBody_r30c13_color, self.BarBody_r30c14_pos, self.BarBody_r30c14_color, self.BarBody_r31c13_pos, self.BarBody_r31c13_color, self.BarBody_r31c14_pos, self.BarBody_r31c14_color, self.BarBody_r34c13_pos, self.BarBody_r34c13_color, self.BarBody_r34c14_pos, self.BarBody_r34c14_color, self.BarBody_r35c13_pos, self.BarBody_r35c13_color, self.BarBody_r35c14_pos, self.BarBody_r35c14_color, self.BarCore_r32c13_pos, self.BarCore_r32c13_color, self.BarCore_r32c14_pos, self.BarCore_r32c14_color, self.BarCore_r33c13_pos, self.BarCore_r33c13_color, self.BarCore_r33c14_pos, self.BarCore_r33c14_color, self.BarCore_r38c17_pos, self.BarCore_r38c17_color, self.BarCore_r38c20_pos, self.BarCore_r38c20_color, self.BarCore_r39c16_pos, self.BarCore_r39c16_color, self.BarCore_r39c19_pos, self.BarCore_r39c19_color, self.BarCore_r39c22_pos, self.BarCore_r39c22_color, self.BarCore_r53c59_pos, self.BarCore_r53c59_color, self.BarCore_r53c60_pos, self.BarCore_r53c60_color, self.BarCore_r53c61_pos, self.BarCore_r53c61_color, self.BarCore_r53c62_pos, self.BarCore_r53c62_color, self.BarCore_r53c63_pos, self.BarCore_r53c63_color, self.Blank_r32c17_pos, self.Blank_r32c17_color, self.Blank_r32c18_pos, self.Blank_r32c18_color, self.Blank_r32c19_pos, self.Blank_r32c19_color, self.Blank_r32c20_pos, self.Blank_r32c20_color, self.Blank_r32c21_pos, self.Blank_r32c21_color, self.Blank_r32c22_pos, self.Blank_r32c22_color, self.Blank_r33c17_pos, self.Blank_r33c17_color, self.Blank_r33c18_pos, self.Blank_r33c18_color, self.Blank_r33c19_pos, self.Blank_r33c19_color, self.Blank_r33c20_pos, self.Blank_r33c20_color, self.Blank_r33c21_pos, self.Blank_r33c21_color, self.Blank_r33c22_pos, self.Blank_r33c22_color, self.Frame_r36c11_pos, self.Frame_r36c11_color, self.Frame_r36c12_pos, self.Frame_r36c12_color, self.Frame_r36c13_pos, self.Frame_r36c13_color, self.Frame_r36c14_pos, self.Frame_r36c14_color, self.Frame_r36c15_pos, self.Frame_r36c15_color, self.Frame_r36c16_pos, self.Frame_r36c16_color, self.Frame_r37c11_pos, self.Frame_r37c11_color, self.Frame_r37c16_pos, self.Frame_r37c16_color, self.Frame_r38c11_pos, self.Frame_r38c11_color, self.Frame_r38c13_pos, self.Frame_r38c13_color, self.Frame_r38c14_pos, self.Frame_r38c14_color, self.Frame_r39c11_pos, self.Frame_r39c11_color, self.Frame_r39c13_pos, self.Frame_r39c13_color, self.Frame_r39c14_pos, self.Frame_r39c14_color, self.Frame_r40c11_pos, self.Frame_r40c11_color, self.Frame_r40c16_pos, self.Frame_r40c16_color, self.Frame_r41c11_pos, self.Frame_r41c11_color, self.Frame_r41c12_pos, self.Frame_r41c12_color, self.Frame_r41c13_pos, self.Frame_r41c13_color, self.Frame_r41c14_pos, self.Frame_r41c14_color, self.Frame_r41c15_pos, self.Frame_r41c15_color, self.Frame_r41c16_pos, self.Frame_r41c16_color, self.Hollow_r37c12_pos, self.Hollow_r37c12_color, self.Hollow_r37c13_pos, self.Hollow_r37c13_color, self.Hollow_r37c14_pos, self.Hollow_r37c14_color, self.Hollow_r37c15_pos, self.Hollow_r37c15_color, self.Hollow_r38c12_pos, self.Hollow_r38c12_color, self.Hollow_r38c15_pos, self.Hollow_r38c15_color, self.Hollow_r39c12_pos, self.Hollow_r39c12_color, self.Hollow_r39c15_pos, self.Hollow_r39c15_color, self.Hollow_r40c12_pos, self.Hollow_r40c12_color, self.Hollow_r40c13_pos, self.Hollow_r40c13_color, self.Hollow_r40c14_pos, self.Hollow_r40c14_color, self.Hollow_r40c15_pos, self.Hollow_r40c15_color, self.Dot_r38c16_pos, self.Dot_r38c16_color, self.Dot_r38c18_pos, self.Dot_r38c18_color, self.Dot_r38c19_pos, self.Dot_r38c19_color, self.Dot_r38c21_pos, self.Dot_r38c21_color, self.Dot_r38c22_pos, self.Dot_r38c22_color, self.Dot_r39c17_pos, self.Dot_r39c17_color, self.Dot_r39c18_pos, self.Dot_r39c18_color, self.Dot_r39c20_pos, self.Dot_r39c20_color, self.Dot_r39c21_pos, self.Dot_r39c21_color,)


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
    if 'Field_r30c11' not in _exclude:
        r, c = state.Field_r30c11_pos
        grid[r][c] = state.Field_r30c11_color
    if 'Field_r30c12' not in _exclude:
        r, c = state.Field_r30c12_pos
        grid[r][c] = state.Field_r30c12_color
    if 'Field_r30c15' not in _exclude:
        r, c = state.Field_r30c15_pos
        grid[r][c] = state.Field_r30c15_color
    if 'Field_r30c16' not in _exclude:
        r, c = state.Field_r30c16_pos
        grid[r][c] = state.Field_r30c16_color
    if 'Field_r31c11' not in _exclude:
        r, c = state.Field_r31c11_pos
        grid[r][c] = state.Field_r31c11_color
    if 'Field_r31c12' not in _exclude:
        r, c = state.Field_r31c12_pos
        grid[r][c] = state.Field_r31c12_color
    if 'Field_r31c15' not in _exclude:
        r, c = state.Field_r31c15_pos
        grid[r][c] = state.Field_r31c15_color
    if 'Field_r31c16' not in _exclude:
        r, c = state.Field_r31c16_pos
        grid[r][c] = state.Field_r31c16_color
    if 'Field_r32c11' not in _exclude:
        r, c = state.Field_r32c11_pos
        grid[r][c] = state.Field_r32c11_color
    if 'Field_r32c12' not in _exclude:
        r, c = state.Field_r32c12_pos
        grid[r][c] = state.Field_r32c12_color
    if 'Field_r32c15' not in _exclude:
        r, c = state.Field_r32c15_pos
        grid[r][c] = state.Field_r32c15_color
    if 'Field_r32c16' not in _exclude:
        r, c = state.Field_r32c16_pos
        grid[r][c] = state.Field_r32c16_color
    if 'Field_r33c11' not in _exclude:
        r, c = state.Field_r33c11_pos
        grid[r][c] = state.Field_r33c11_color
    if 'Field_r33c12' not in _exclude:
        r, c = state.Field_r33c12_pos
        grid[r][c] = state.Field_r33c12_color
    if 'Field_r33c15' not in _exclude:
        r, c = state.Field_r33c15_pos
        grid[r][c] = state.Field_r33c15_color
    if 'Field_r33c16' not in _exclude:
        r, c = state.Field_r33c16_pos
        grid[r][c] = state.Field_r33c16_color
    if 'Field_r34c11' not in _exclude:
        r, c = state.Field_r34c11_pos
        grid[r][c] = state.Field_r34c11_color
    if 'Field_r34c12' not in _exclude:
        r, c = state.Field_r34c12_pos
        grid[r][c] = state.Field_r34c12_color
    if 'Field_r34c15' not in _exclude:
        r, c = state.Field_r34c15_pos
        grid[r][c] = state.Field_r34c15_color
    if 'Field_r34c16' not in _exclude:
        r, c = state.Field_r34c16_pos
        grid[r][c] = state.Field_r34c16_color
    if 'Field_r35c11' not in _exclude:
        r, c = state.Field_r35c11_pos
        grid[r][c] = state.Field_r35c11_color
    if 'Field_r35c12' not in _exclude:
        r, c = state.Field_r35c12_pos
        grid[r][c] = state.Field_r35c12_color
    if 'Field_r35c15' not in _exclude:
        r, c = state.Field_r35c15_pos
        grid[r][c] = state.Field_r35c15_color
    if 'Field_r35c16' not in _exclude:
        r, c = state.Field_r35c16_pos
        grid[r][c] = state.Field_r35c16_color
    if 'BarBody_r30c13' not in _exclude:
        r, c = state.BarBody_r30c13_pos
        grid[r][c] = state.BarBody_r30c13_color
    if 'BarBody_r30c14' not in _exclude:
        r, c = state.BarBody_r30c14_pos
        grid[r][c] = state.BarBody_r30c14_color
    if 'BarBody_r31c13' not in _exclude:
        r, c = state.BarBody_r31c13_pos
        grid[r][c] = state.BarBody_r31c13_color
    if 'BarBody_r31c14' not in _exclude:
        r, c = state.BarBody_r31c14_pos
        grid[r][c] = state.BarBody_r31c14_color
    if 'BarBody_r34c13' not in _exclude:
        r, c = state.BarBody_r34c13_pos
        grid[r][c] = state.BarBody_r34c13_color
    if 'BarBody_r34c14' not in _exclude:
        r, c = state.BarBody_r34c14_pos
        grid[r][c] = state.BarBody_r34c14_color
    if 'BarBody_r35c13' not in _exclude:
        r, c = state.BarBody_r35c13_pos
        grid[r][c] = state.BarBody_r35c13_color
    if 'BarBody_r35c14' not in _exclude:
        r, c = state.BarBody_r35c14_pos
        grid[r][c] = state.BarBody_r35c14_color
    if 'BarCore_r32c13' not in _exclude:
        r, c = state.BarCore_r32c13_pos
        grid[r][c] = state.BarCore_r32c13_color
    if 'BarCore_r32c14' not in _exclude:
        r, c = state.BarCore_r32c14_pos
        grid[r][c] = state.BarCore_r32c14_color
    if 'BarCore_r33c13' not in _exclude:
        r, c = state.BarCore_r33c13_pos
        grid[r][c] = state.BarCore_r33c13_color
    if 'BarCore_r33c14' not in _exclude:
        r, c = state.BarCore_r33c14_pos
        grid[r][c] = state.BarCore_r33c14_color
    if 'BarCore_r38c17' not in _exclude:
        r, c = state.BarCore_r38c17_pos
        grid[r][c] = state.BarCore_r38c17_color
    if 'BarCore_r38c20' not in _exclude:
        r, c = state.BarCore_r38c20_pos
        grid[r][c] = state.BarCore_r38c20_color
    if 'BarCore_r39c16' not in _exclude:
        r, c = state.BarCore_r39c16_pos
        grid[r][c] = state.BarCore_r39c16_color
    if 'BarCore_r39c19' not in _exclude:
        r, c = state.BarCore_r39c19_pos
        grid[r][c] = state.BarCore_r39c19_color
    if 'BarCore_r39c22' not in _exclude:
        r, c = state.BarCore_r39c22_pos
        grid[r][c] = state.BarCore_r39c22_color
    if 'BarCore_r53c59' not in _exclude:
        r, c = state.BarCore_r53c59_pos
        grid[r][c] = state.BarCore_r53c59_color
    if 'BarCore_r53c60' not in _exclude:
        r, c = state.BarCore_r53c60_pos
        grid[r][c] = state.BarCore_r53c60_color
    if 'BarCore_r53c61' not in _exclude:
        r, c = state.BarCore_r53c61_pos
        grid[r][c] = state.BarCore_r53c61_color
    if 'BarCore_r53c62' not in _exclude:
        r, c = state.BarCore_r53c62_pos
        grid[r][c] = state.BarCore_r53c62_color
    if 'BarCore_r53c63' not in _exclude:
        r, c = state.BarCore_r53c63_pos
        grid[r][c] = state.BarCore_r53c63_color
    if 'Blank_r32c17' not in _exclude:
        r, c = state.Blank_r32c17_pos
        grid[r][c] = state.Blank_r32c17_color
    if 'Blank_r32c18' not in _exclude:
        r, c = state.Blank_r32c18_pos
        grid[r][c] = state.Blank_r32c18_color
    if 'Blank_r32c19' not in _exclude:
        r, c = state.Blank_r32c19_pos
        grid[r][c] = state.Blank_r32c19_color
    if 'Blank_r32c20' not in _exclude:
        r, c = state.Blank_r32c20_pos
        grid[r][c] = state.Blank_r32c20_color
    if 'Blank_r32c21' not in _exclude:
        r, c = state.Blank_r32c21_pos
        grid[r][c] = state.Blank_r32c21_color
    if 'Blank_r32c22' not in _exclude:
        r, c = state.Blank_r32c22_pos
        grid[r][c] = state.Blank_r32c22_color
    if 'Blank_r33c17' not in _exclude:
        r, c = state.Blank_r33c17_pos
        grid[r][c] = state.Blank_r33c17_color
    if 'Blank_r33c18' not in _exclude:
        r, c = state.Blank_r33c18_pos
        grid[r][c] = state.Blank_r33c18_color
    if 'Blank_r33c19' not in _exclude:
        r, c = state.Blank_r33c19_pos
        grid[r][c] = state.Blank_r33c19_color
    if 'Blank_r33c20' not in _exclude:
        r, c = state.Blank_r33c20_pos
        grid[r][c] = state.Blank_r33c20_color
    if 'Blank_r33c21' not in _exclude:
        r, c = state.Blank_r33c21_pos
        grid[r][c] = state.Blank_r33c21_color
    if 'Blank_r33c22' not in _exclude:
        r, c = state.Blank_r33c22_pos
        grid[r][c] = state.Blank_r33c22_color
    if 'Frame_r36c11' not in _exclude:
        r, c = state.Frame_r36c11_pos
        grid[r][c] = state.Frame_r36c11_color
    if 'Frame_r36c12' not in _exclude:
        r, c = state.Frame_r36c12_pos
        grid[r][c] = state.Frame_r36c12_color
    if 'Frame_r36c13' not in _exclude:
        r, c = state.Frame_r36c13_pos
        grid[r][c] = state.Frame_r36c13_color
    if 'Frame_r36c14' not in _exclude:
        r, c = state.Frame_r36c14_pos
        grid[r][c] = state.Frame_r36c14_color
    if 'Frame_r36c15' not in _exclude:
        r, c = state.Frame_r36c15_pos
        grid[r][c] = state.Frame_r36c15_color
    if 'Frame_r36c16' not in _exclude:
        r, c = state.Frame_r36c16_pos
        grid[r][c] = state.Frame_r36c16_color
    if 'Frame_r37c11' not in _exclude:
        r, c = state.Frame_r37c11_pos
        grid[r][c] = state.Frame_r37c11_color
    if 'Frame_r37c16' not in _exclude:
        r, c = state.Frame_r37c16_pos
        grid[r][c] = state.Frame_r37c16_color
    if 'Frame_r38c11' not in _exclude:
        r, c = state.Frame_r38c11_pos
        grid[r][c] = state.Frame_r38c11_color
    if 'Frame_r38c13' not in _exclude:
        r, c = state.Frame_r38c13_pos
        grid[r][c] = state.Frame_r38c13_color
    if 'Frame_r38c14' not in _exclude:
        r, c = state.Frame_r38c14_pos
        grid[r][c] = state.Frame_r38c14_color
    if 'Frame_r39c11' not in _exclude:
        r, c = state.Frame_r39c11_pos
        grid[r][c] = state.Frame_r39c11_color
    if 'Frame_r39c13' not in _exclude:
        r, c = state.Frame_r39c13_pos
        grid[r][c] = state.Frame_r39c13_color
    if 'Frame_r39c14' not in _exclude:
        r, c = state.Frame_r39c14_pos
        grid[r][c] = state.Frame_r39c14_color
    if 'Frame_r40c11' not in _exclude:
        r, c = state.Frame_r40c11_pos
        grid[r][c] = state.Frame_r40c11_color
    if 'Frame_r40c16' not in _exclude:
        r, c = state.Frame_r40c16_pos
        grid[r][c] = state.Frame_r40c16_color
    if 'Frame_r41c11' not in _exclude:
        r, c = state.Frame_r41c11_pos
        grid[r][c] = state.Frame_r41c11_color
    if 'Frame_r41c12' not in _exclude:
        r, c = state.Frame_r41c12_pos
        grid[r][c] = state.Frame_r41c12_color
    if 'Frame_r41c13' not in _exclude:
        r, c = state.Frame_r41c13_pos
        grid[r][c] = state.Frame_r41c13_color
    if 'Frame_r41c14' not in _exclude:
        r, c = state.Frame_r41c14_pos
        grid[r][c] = state.Frame_r41c14_color
    if 'Frame_r41c15' not in _exclude:
        r, c = state.Frame_r41c15_pos
        grid[r][c] = state.Frame_r41c15_color
    if 'Frame_r41c16' not in _exclude:
        r, c = state.Frame_r41c16_pos
        grid[r][c] = state.Frame_r41c16_color
    if 'Hollow_r37c12' not in _exclude:
        r, c = state.Hollow_r37c12_pos
        grid[r][c] = state.Hollow_r37c12_color
    if 'Hollow_r37c13' not in _exclude:
        r, c = state.Hollow_r37c13_pos
        grid[r][c] = state.Hollow_r37c13_color
    if 'Hollow_r37c14' not in _exclude:
        r, c = state.Hollow_r37c14_pos
        grid[r][c] = state.Hollow_r37c14_color
    if 'Hollow_r37c15' not in _exclude:
        r, c = state.Hollow_r37c15_pos
        grid[r][c] = state.Hollow_r37c15_color
    if 'Hollow_r38c12' not in _exclude:
        r, c = state.Hollow_r38c12_pos
        grid[r][c] = state.Hollow_r38c12_color
    if 'Hollow_r38c15' not in _exclude:
        r, c = state.Hollow_r38c15_pos
        grid[r][c] = state.Hollow_r38c15_color
    if 'Hollow_r39c12' not in _exclude:
        r, c = state.Hollow_r39c12_pos
        grid[r][c] = state.Hollow_r39c12_color
    if 'Hollow_r39c15' not in _exclude:
        r, c = state.Hollow_r39c15_pos
        grid[r][c] = state.Hollow_r39c15_color
    if 'Hollow_r40c12' not in _exclude:
        r, c = state.Hollow_r40c12_pos
        grid[r][c] = state.Hollow_r40c12_color
    if 'Hollow_r40c13' not in _exclude:
        r, c = state.Hollow_r40c13_pos
        grid[r][c] = state.Hollow_r40c13_color
    if 'Hollow_r40c14' not in _exclude:
        r, c = state.Hollow_r40c14_pos
        grid[r][c] = state.Hollow_r40c14_color
    if 'Hollow_r40c15' not in _exclude:
        r, c = state.Hollow_r40c15_pos
        grid[r][c] = state.Hollow_r40c15_color
    if 'Dot_r38c16' not in _exclude:
        r, c = state.Dot_r38c16_pos
        grid[r][c] = state.Dot_r38c16_color
    if 'Dot_r38c18' not in _exclude:
        r, c = state.Dot_r38c18_pos
        grid[r][c] = state.Dot_r38c18_color
    if 'Dot_r38c19' not in _exclude:
        r, c = state.Dot_r38c19_pos
        grid[r][c] = state.Dot_r38c19_color
    if 'Dot_r38c21' not in _exclude:
        r, c = state.Dot_r38c21_pos
        grid[r][c] = state.Dot_r38c21_color
    if 'Dot_r38c22' not in _exclude:
        r, c = state.Dot_r38c22_pos
        grid[r][c] = state.Dot_r38c22_color
    if 'Dot_r39c17' not in _exclude:
        r, c = state.Dot_r39c17_pos
        grid[r][c] = state.Dot_r39c17_color
    if 'Dot_r39c18' not in _exclude:
        r, c = state.Dot_r39c18_pos
        grid[r][c] = state.Dot_r39c18_color
    if 'Dot_r39c20' not in _exclude:
        r, c = state.Dot_r39c20_pos
        grid[r][c] = state.Dot_r39c20_color
    if 'Dot_r39c21' not in _exclude:
        r, c = state.Dot_r39c21_pos
        grid[r][c] = state.Dot_r39c21_color
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


def _guard_k1_field_to_frame__Field_r30c11(state, action):
    """k1_field_to_frame__Field_r30c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r30c11(state):
    state.Field_r30c11_color = 6


def _guard_k1_field_to_frame__Field_r30c12(state, action):
    """k1_field_to_frame__Field_r30c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r30c12(state):
    state.Field_r30c12_color = 6


def _guard_k1_field_to_frame__Field_r30c15(state, action):
    """k1_field_to_frame__Field_r30c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r30c15(state):
    state.Field_r30c15_color = 6


def _guard_k1_field_to_frame__Field_r30c16(state, action):
    """k1_field_to_frame__Field_r30c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r30c16(state):
    state.Field_r30c16_color = 6


def _guard_k1_field_to_frame__Field_r31c11(state, action):
    """k1_field_to_frame__Field_r31c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r31c11(state):
    state.Field_r31c11_color = 6


def _guard_k1_field_to_frame__Field_r31c12(state, action):
    """k1_field_to_frame__Field_r31c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r31c12(state):
    state.Field_r31c12_color = 6


def _guard_k1_field_to_frame__Field_r31c15(state, action):
    """k1_field_to_frame__Field_r31c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r31c15(state):
    state.Field_r31c15_color = 6


def _guard_k1_field_to_frame__Field_r31c16(state, action):
    """k1_field_to_frame__Field_r31c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r31c16(state):
    state.Field_r31c16_color = 6


def _guard_k1_field_to_frame__Field_r32c11(state, action):
    """k1_field_to_frame__Field_r32c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r32c11(state):
    state.Field_r32c11_color = 6


def _guard_k1_field_to_frame__Field_r32c12(state, action):
    """k1_field_to_frame__Field_r32c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r32c12(state):
    state.Field_r32c12_color = 6


def _guard_k1_field_to_frame__Field_r32c15(state, action):
    """k1_field_to_frame__Field_r32c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r32c15(state):
    state.Field_r32c15_color = 6


def _guard_k1_field_to_frame__Field_r32c16(state, action):
    """k1_field_to_frame__Field_r32c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r32c16(state):
    state.Field_r32c16_color = 6


def _guard_k1_field_to_frame__Field_r33c11(state, action):
    """k1_field_to_frame__Field_r33c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r33c11(state):
    state.Field_r33c11_color = 6


def _guard_k1_field_to_frame__Field_r33c12(state, action):
    """k1_field_to_frame__Field_r33c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r33c12(state):
    state.Field_r33c12_color = 6


def _guard_k1_field_to_frame__Field_r33c15(state, action):
    """k1_field_to_frame__Field_r33c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r33c15(state):
    state.Field_r33c15_color = 6


def _guard_k1_field_to_frame__Field_r33c16(state, action):
    """k1_field_to_frame__Field_r33c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r33c16(state):
    state.Field_r33c16_color = 6


def _guard_k1_field_to_frame__Field_r34c11(state, action):
    """k1_field_to_frame__Field_r34c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r34c11(state):
    state.Field_r34c11_color = 6


def _guard_k1_field_to_frame__Field_r34c12(state, action):
    """k1_field_to_frame__Field_r34c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r34c12(state):
    state.Field_r34c12_color = 6


def _guard_k1_field_to_frame__Field_r34c15(state, action):
    """k1_field_to_frame__Field_r34c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r34c15(state):
    state.Field_r34c15_color = 6


def _guard_k1_field_to_frame__Field_r34c16(state, action):
    """k1_field_to_frame__Field_r34c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r34c16(state):
    state.Field_r34c16_color = 6


def _guard_k1_field_to_frame__Field_r35c11(state, action):
    """k1_field_to_frame__Field_r35c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r35c11(state):
    state.Field_r35c11_color = 6


def _guard_k1_field_to_frame__Field_r35c12(state, action):
    """k1_field_to_frame__Field_r35c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r35c12(state):
    state.Field_r35c12_color = 6


def _guard_k1_field_to_frame__Field_r35c15(state, action):
    """k1_field_to_frame__Field_r35c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r35c15(state):
    state.Field_r35c15_color = 6


def _guard_k1_field_to_frame__Field_r35c16(state, action):
    """k1_field_to_frame__Field_r35c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_field_to_frame__Field_r35c16(state):
    state.Field_r35c16_color = 6


def _guard_k1_field_to_hollow__Field_r30c11(state, action):
    """k1_field_to_hollow__Field_r30c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r30c11(state):
    state.Field_r30c11_color = 0


def _guard_k1_field_to_hollow__Field_r30c12(state, action):
    """k1_field_to_hollow__Field_r30c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r30c12(state):
    state.Field_r30c12_color = 0


def _guard_k1_field_to_hollow__Field_r30c15(state, action):
    """k1_field_to_hollow__Field_r30c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r30c15(state):
    state.Field_r30c15_color = 0


def _guard_k1_field_to_hollow__Field_r30c16(state, action):
    """k1_field_to_hollow__Field_r30c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r30c16(state):
    state.Field_r30c16_color = 0


def _guard_k1_field_to_hollow__Field_r31c11(state, action):
    """k1_field_to_hollow__Field_r31c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r31c11(state):
    state.Field_r31c11_color = 0


def _guard_k1_field_to_hollow__Field_r31c12(state, action):
    """k1_field_to_hollow__Field_r31c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r31c12(state):
    state.Field_r31c12_color = 0


def _guard_k1_field_to_hollow__Field_r31c15(state, action):
    """k1_field_to_hollow__Field_r31c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r31c15(state):
    state.Field_r31c15_color = 0


def _guard_k1_field_to_hollow__Field_r31c16(state, action):
    """k1_field_to_hollow__Field_r31c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r31c16(state):
    state.Field_r31c16_color = 0


def _guard_k1_field_to_hollow__Field_r32c11(state, action):
    """k1_field_to_hollow__Field_r32c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r32c11(state):
    state.Field_r32c11_color = 0


def _guard_k1_field_to_hollow__Field_r32c12(state, action):
    """k1_field_to_hollow__Field_r32c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r32c12(state):
    state.Field_r32c12_color = 0


def _guard_k1_field_to_hollow__Field_r32c15(state, action):
    """k1_field_to_hollow__Field_r32c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r32c15(state):
    state.Field_r32c15_color = 0


def _guard_k1_field_to_hollow__Field_r32c16(state, action):
    """k1_field_to_hollow__Field_r32c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r32c16(state):
    state.Field_r32c16_color = 0


def _guard_k1_field_to_hollow__Field_r33c11(state, action):
    """k1_field_to_hollow__Field_r33c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r33c11(state):
    state.Field_r33c11_color = 0


def _guard_k1_field_to_hollow__Field_r33c12(state, action):
    """k1_field_to_hollow__Field_r33c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r33c12(state):
    state.Field_r33c12_color = 0


def _guard_k1_field_to_hollow__Field_r33c15(state, action):
    """k1_field_to_hollow__Field_r33c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r33c15(state):
    state.Field_r33c15_color = 0


def _guard_k1_field_to_hollow__Field_r33c16(state, action):
    """k1_field_to_hollow__Field_r33c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r33c16(state):
    state.Field_r33c16_color = 0


def _guard_k1_field_to_hollow__Field_r34c11(state, action):
    """k1_field_to_hollow__Field_r34c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r34c11(state):
    state.Field_r34c11_color = 0


def _guard_k1_field_to_hollow__Field_r34c12(state, action):
    """k1_field_to_hollow__Field_r34c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r34c12(state):
    state.Field_r34c12_color = 0


def _guard_k1_field_to_hollow__Field_r34c15(state, action):
    """k1_field_to_hollow__Field_r34c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r34c15(state):
    state.Field_r34c15_color = 0


def _guard_k1_field_to_hollow__Field_r34c16(state, action):
    """k1_field_to_hollow__Field_r34c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r34c16(state):
    state.Field_r34c16_color = 0


def _guard_k1_field_to_hollow__Field_r35c11(state, action):
    """k1_field_to_hollow__Field_r35c11  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r35c11(state):
    state.Field_r35c11_color = 0


def _guard_k1_field_to_hollow__Field_r35c12(state, action):
    """k1_field_to_hollow__Field_r35c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r35c12(state):
    state.Field_r35c12_color = 0


def _guard_k1_field_to_hollow__Field_r35c15(state, action):
    """k1_field_to_hollow__Field_r35c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r35c15(state):
    state.Field_r35c15_color = 0


def _guard_k1_field_to_hollow__Field_r35c16(state, action):
    """k1_field_to_hollow__Field_r35c16  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_field_to_hollow__Field_r35c16(state):
    state.Field_r35c16_color = 0


def _guard_k1_field_to_dot__Field_r30c11(state, action):
    """k1_field_to_dot__Field_r30c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r30c11(state):
    state.Field_r30c11_color = 1


def _guard_k1_field_to_dot__Field_r30c12(state, action):
    """k1_field_to_dot__Field_r30c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r30c12(state):
    state.Field_r30c12_color = 1


def _guard_k1_field_to_dot__Field_r30c15(state, action):
    """k1_field_to_dot__Field_r30c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r30c15(state):
    state.Field_r30c15_color = 1


def _guard_k1_field_to_dot__Field_r30c16(state, action):
    """k1_field_to_dot__Field_r30c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r30c16(state):
    state.Field_r30c16_color = 1


def _guard_k1_field_to_dot__Field_r31c11(state, action):
    """k1_field_to_dot__Field_r31c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r31c11(state):
    state.Field_r31c11_color = 1


def _guard_k1_field_to_dot__Field_r31c12(state, action):
    """k1_field_to_dot__Field_r31c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r31c12(state):
    state.Field_r31c12_color = 1


def _guard_k1_field_to_dot__Field_r31c15(state, action):
    """k1_field_to_dot__Field_r31c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r31c15(state):
    state.Field_r31c15_color = 1


def _guard_k1_field_to_dot__Field_r31c16(state, action):
    """k1_field_to_dot__Field_r31c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r31c16(state):
    state.Field_r31c16_color = 1


def _guard_k1_field_to_dot__Field_r32c11(state, action):
    """k1_field_to_dot__Field_r32c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r32c11(state):
    state.Field_r32c11_color = 1


def _guard_k1_field_to_dot__Field_r32c12(state, action):
    """k1_field_to_dot__Field_r32c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r32c12(state):
    state.Field_r32c12_color = 1


def _guard_k1_field_to_dot__Field_r32c15(state, action):
    """k1_field_to_dot__Field_r32c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r32c15(state):
    state.Field_r32c15_color = 1


def _guard_k1_field_to_dot__Field_r32c16(state, action):
    """k1_field_to_dot__Field_r32c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r32c16(state):
    state.Field_r32c16_color = 1


def _guard_k1_field_to_dot__Field_r33c11(state, action):
    """k1_field_to_dot__Field_r33c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r33c11(state):
    state.Field_r33c11_color = 1


def _guard_k1_field_to_dot__Field_r33c12(state, action):
    """k1_field_to_dot__Field_r33c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r33c12(state):
    state.Field_r33c12_color = 1


def _guard_k1_field_to_dot__Field_r33c15(state, action):
    """k1_field_to_dot__Field_r33c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r33c15(state):
    state.Field_r33c15_color = 1


def _guard_k1_field_to_dot__Field_r33c16(state, action):
    """k1_field_to_dot__Field_r33c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r33c16(state):
    state.Field_r33c16_color = 1


def _guard_k1_field_to_dot__Field_r34c11(state, action):
    """k1_field_to_dot__Field_r34c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r34c11(state):
    state.Field_r34c11_color = 1


def _guard_k1_field_to_dot__Field_r34c12(state, action):
    """k1_field_to_dot__Field_r34c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r34c12(state):
    state.Field_r34c12_color = 1


def _guard_k1_field_to_dot__Field_r34c15(state, action):
    """k1_field_to_dot__Field_r34c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r34c15(state):
    state.Field_r34c15_color = 1


def _guard_k1_field_to_dot__Field_r34c16(state, action):
    """k1_field_to_dot__Field_r34c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r34c16(state):
    state.Field_r34c16_color = 1


def _guard_k1_field_to_dot__Field_r35c11(state, action):
    """k1_field_to_dot__Field_r35c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r35c11(state):
    state.Field_r35c11_color = 1


def _guard_k1_field_to_dot__Field_r35c12(state, action):
    """k1_field_to_dot__Field_r35c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r35c12(state):
    state.Field_r35c12_color = 1


def _guard_k1_field_to_dot__Field_r35c15(state, action):
    """k1_field_to_dot__Field_r35c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r35c15(state):
    state.Field_r35c15_color = 1


def _guard_k1_field_to_dot__Field_r35c16(state, action):
    """k1_field_to_dot__Field_r35c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_field_to_dot__Field_r35c16(state):
    state.Field_r35c16_color = 1


def _guard_k1_field_to_core__Field_r30c11(state, action):
    """k1_field_to_core__Field_r30c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r30c11(state):
    state.Field_r30c11_color = 2


def _guard_k1_field_to_core__Field_r30c12(state, action):
    """k1_field_to_core__Field_r30c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r30c12(state):
    state.Field_r30c12_color = 2


def _guard_k1_field_to_core__Field_r30c15(state, action):
    """k1_field_to_core__Field_r30c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r30c15(state):
    state.Field_r30c15_color = 2


def _guard_k1_field_to_core__Field_r30c16(state, action):
    """k1_field_to_core__Field_r30c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r30c16(state):
    state.Field_r30c16_color = 2


def _guard_k1_field_to_core__Field_r31c11(state, action):
    """k1_field_to_core__Field_r31c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r31c11(state):
    state.Field_r31c11_color = 2


def _guard_k1_field_to_core__Field_r31c12(state, action):
    """k1_field_to_core__Field_r31c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r31c12(state):
    state.Field_r31c12_color = 2


def _guard_k1_field_to_core__Field_r31c15(state, action):
    """k1_field_to_core__Field_r31c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r31c15(state):
    state.Field_r31c15_color = 2


def _guard_k1_field_to_core__Field_r31c16(state, action):
    """k1_field_to_core__Field_r31c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r31c16(state):
    state.Field_r31c16_color = 2


def _guard_k1_field_to_core__Field_r32c11(state, action):
    """k1_field_to_core__Field_r32c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r32c11(state):
    state.Field_r32c11_color = 2


def _guard_k1_field_to_core__Field_r32c12(state, action):
    """k1_field_to_core__Field_r32c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r32c12(state):
    state.Field_r32c12_color = 2


def _guard_k1_field_to_core__Field_r32c15(state, action):
    """k1_field_to_core__Field_r32c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r32c15(state):
    state.Field_r32c15_color = 2


def _guard_k1_field_to_core__Field_r32c16(state, action):
    """k1_field_to_core__Field_r32c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r32c16(state):
    state.Field_r32c16_color = 2


def _guard_k1_field_to_core__Field_r33c11(state, action):
    """k1_field_to_core__Field_r33c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r33c11(state):
    state.Field_r33c11_color = 2


def _guard_k1_field_to_core__Field_r33c12(state, action):
    """k1_field_to_core__Field_r33c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r33c12(state):
    state.Field_r33c12_color = 2


def _guard_k1_field_to_core__Field_r33c15(state, action):
    """k1_field_to_core__Field_r33c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r33c15(state):
    state.Field_r33c15_color = 2


def _guard_k1_field_to_core__Field_r33c16(state, action):
    """k1_field_to_core__Field_r33c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r33c16(state):
    state.Field_r33c16_color = 2


def _guard_k1_field_to_core__Field_r34c11(state, action):
    """k1_field_to_core__Field_r34c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r34c11(state):
    state.Field_r34c11_color = 2


def _guard_k1_field_to_core__Field_r34c12(state, action):
    """k1_field_to_core__Field_r34c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r34c12(state):
    state.Field_r34c12_color = 2


def _guard_k1_field_to_core__Field_r34c15(state, action):
    """k1_field_to_core__Field_r34c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r34c15(state):
    state.Field_r34c15_color = 2


def _guard_k1_field_to_core__Field_r34c16(state, action):
    """k1_field_to_core__Field_r34c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r34c16(state):
    state.Field_r34c16_color = 2


def _guard_k1_field_to_core__Field_r35c11(state, action):
    """k1_field_to_core__Field_r35c11  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r35c11(state):
    state.Field_r35c11_color = 2


def _guard_k1_field_to_core__Field_r35c12(state, action):
    """k1_field_to_core__Field_r35c12  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r35c12(state):
    state.Field_r35c12_color = 2


def _guard_k1_field_to_core__Field_r35c15(state, action):
    """k1_field_to_core__Field_r35c15  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r35c15(state):
    state.Field_r35c15_color = 2


def _guard_k1_field_to_core__Field_r35c16(state, action):
    """k1_field_to_core__Field_r35c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_field_to_core__Field_r35c16(state):
    state.Field_r35c16_color = 2


def _guard_k1_bar_to_frame__BarBody_r30c13(state, action):
    """k1_bar_to_frame__BarBody_r30c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 6


def _guard_k1_bar_to_frame__BarBody_r30c14(state, action):
    """k1_bar_to_frame__BarBody_r30c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 6


def _guard_k1_bar_to_frame__BarBody_r31c13(state, action):
    """k1_bar_to_frame__BarBody_r31c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 6


def _guard_k1_bar_to_frame__BarBody_r31c14(state, action):
    """k1_bar_to_frame__BarBody_r31c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 6


def _guard_k1_bar_to_frame__BarBody_r34c13(state, action):
    """k1_bar_to_frame__BarBody_r34c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 6


def _guard_k1_bar_to_frame__BarBody_r34c14(state, action):
    """k1_bar_to_frame__BarBody_r34c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 6


def _guard_k1_bar_to_frame__BarBody_r35c13(state, action):
    """k1_bar_to_frame__BarBody_r35c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 6


def _guard_k1_bar_to_frame__BarBody_r35c14(state, action):
    """k1_bar_to_frame__BarBody_r35c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_bar_to_frame__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 6


def _guard_k1_bar_to_hollow__BarBody_r30c13(state, action):
    """k1_bar_to_hollow__BarBody_r30c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 0


def _guard_k1_bar_to_hollow__BarBody_r30c14(state, action):
    """k1_bar_to_hollow__BarBody_r30c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 0


def _guard_k1_bar_to_hollow__BarBody_r31c13(state, action):
    """k1_bar_to_hollow__BarBody_r31c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 0


def _guard_k1_bar_to_hollow__BarBody_r31c14(state, action):
    """k1_bar_to_hollow__BarBody_r31c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 0


def _guard_k1_bar_to_hollow__BarBody_r34c13(state, action):
    """k1_bar_to_hollow__BarBody_r34c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 0


def _guard_k1_bar_to_hollow__BarBody_r34c14(state, action):
    """k1_bar_to_hollow__BarBody_r34c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 0


def _guard_k1_bar_to_hollow__BarBody_r35c13(state, action):
    """k1_bar_to_hollow__BarBody_r35c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 0


def _guard_k1_bar_to_hollow__BarBody_r35c14(state, action):
    """k1_bar_to_hollow__BarBody_r35c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 0): return False
    return True


def _effect_k1_bar_to_hollow__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 0


def _guard_k1_core_to_frame__BarCore_r32c13(state, action):
    """k1_core_to_frame__BarCore_r32c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 6


def _guard_k1_core_to_frame__BarCore_r32c14(state, action):
    """k1_core_to_frame__BarCore_r32c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 6


def _guard_k1_core_to_frame__BarCore_r33c13(state, action):
    """k1_core_to_frame__BarCore_r33c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 6


def _guard_k1_core_to_frame__BarCore_r33c14(state, action):
    """k1_core_to_frame__BarCore_r33c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 6


def _guard_k1_core_to_frame__BarCore_r38c17(state, action):
    """k1_core_to_frame__BarCore_r38c17  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 6


def _guard_k1_core_to_frame__BarCore_r38c20(state, action):
    """k1_core_to_frame__BarCore_r38c20  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 6


def _guard_k1_core_to_frame__BarCore_r39c16(state, action):
    """k1_core_to_frame__BarCore_r39c16  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 6


def _guard_k1_core_to_frame__BarCore_r39c19(state, action):
    """k1_core_to_frame__BarCore_r39c19  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 6


def _guard_k1_core_to_frame__BarCore_r39c22(state, action):
    """k1_core_to_frame__BarCore_r39c22  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 6


def _guard_k1_core_to_frame__BarCore_r53c59(state, action):
    """k1_core_to_frame__BarCore_r53c59  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 6


def _guard_k1_core_to_frame__BarCore_r53c60(state, action):
    """k1_core_to_frame__BarCore_r53c60  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 6


def _guard_k1_core_to_frame__BarCore_r53c61(state, action):
    """k1_core_to_frame__BarCore_r53c61  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 6


def _guard_k1_core_to_frame__BarCore_r53c62(state, action):
    """k1_core_to_frame__BarCore_r53c62  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 6


def _guard_k1_core_to_frame__BarCore_r53c63(state, action):
    """k1_core_to_frame__BarCore_r53c63  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 6): return False
    return True


def _effect_k1_core_to_frame__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 6


def _guard_k1_blank_to_dot__Blank_r32c17(state, action):
    """k1_blank_to_dot__Blank_r32c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c17(state):
    state.Blank_r32c17_color = 1


def _guard_k1_blank_to_dot__Blank_r32c18(state, action):
    """k1_blank_to_dot__Blank_r32c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c18(state):
    state.Blank_r32c18_color = 1


def _guard_k1_blank_to_dot__Blank_r32c19(state, action):
    """k1_blank_to_dot__Blank_r32c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c19(state):
    state.Blank_r32c19_color = 1


def _guard_k1_blank_to_dot__Blank_r32c20(state, action):
    """k1_blank_to_dot__Blank_r32c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c20(state):
    state.Blank_r32c20_color = 1


def _guard_k1_blank_to_dot__Blank_r32c21(state, action):
    """k1_blank_to_dot__Blank_r32c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c21(state):
    state.Blank_r32c21_color = 1


def _guard_k1_blank_to_dot__Blank_r32c22(state, action):
    """k1_blank_to_dot__Blank_r32c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r32c22(state):
    state.Blank_r32c22_color = 1


def _guard_k1_blank_to_dot__Blank_r33c17(state, action):
    """k1_blank_to_dot__Blank_r33c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c17(state):
    state.Blank_r33c17_color = 1


def _guard_k1_blank_to_dot__Blank_r33c18(state, action):
    """k1_blank_to_dot__Blank_r33c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c18(state):
    state.Blank_r33c18_color = 1


def _guard_k1_blank_to_dot__Blank_r33c19(state, action):
    """k1_blank_to_dot__Blank_r33c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c19(state):
    state.Blank_r33c19_color = 1


def _guard_k1_blank_to_dot__Blank_r33c20(state, action):
    """k1_blank_to_dot__Blank_r33c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c20(state):
    state.Blank_r33c20_color = 1


def _guard_k1_blank_to_dot__Blank_r33c21(state, action):
    """k1_blank_to_dot__Blank_r33c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c21(state):
    state.Blank_r33c21_color = 1


def _guard_k1_blank_to_dot__Blank_r33c22(state, action):
    """k1_blank_to_dot__Blank_r33c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 1): return False
    return True


def _effect_k1_blank_to_dot__Blank_r33c22(state):
    state.Blank_r33c22_color = 1


def _guard_k1_blank_to_core__Blank_r32c17(state, action):
    """k1_blank_to_core__Blank_r32c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c17(state):
    state.Blank_r32c17_color = 2


def _guard_k1_blank_to_core__Blank_r32c18(state, action):
    """k1_blank_to_core__Blank_r32c18  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c18(state):
    state.Blank_r32c18_color = 2


def _guard_k1_blank_to_core__Blank_r32c19(state, action):
    """k1_blank_to_core__Blank_r32c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c19(state):
    state.Blank_r32c19_color = 2


def _guard_k1_blank_to_core__Blank_r32c20(state, action):
    """k1_blank_to_core__Blank_r32c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c20(state):
    state.Blank_r32c20_color = 2


def _guard_k1_blank_to_core__Blank_r32c21(state, action):
    """k1_blank_to_core__Blank_r32c21  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c21(state):
    state.Blank_r32c21_color = 2


def _guard_k1_blank_to_core__Blank_r32c22(state, action):
    """k1_blank_to_core__Blank_r32c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r32c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r32c22(state):
    state.Blank_r32c22_color = 2


def _guard_k1_blank_to_core__Blank_r33c17(state, action):
    """k1_blank_to_core__Blank_r33c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c17(state):
    state.Blank_r33c17_color = 2


def _guard_k1_blank_to_core__Blank_r33c18(state, action):
    """k1_blank_to_core__Blank_r33c18  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c18(state):
    state.Blank_r33c18_color = 2


def _guard_k1_blank_to_core__Blank_r33c19(state, action):
    """k1_blank_to_core__Blank_r33c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c19(state):
    state.Blank_r33c19_color = 2


def _guard_k1_blank_to_core__Blank_r33c20(state, action):
    """k1_blank_to_core__Blank_r33c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c20(state):
    state.Blank_r33c20_color = 2


def _guard_k1_blank_to_core__Blank_r33c21(state, action):
    """k1_blank_to_core__Blank_r33c21  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c21(state):
    state.Blank_r33c21_color = 2


def _guard_k1_blank_to_core__Blank_r33c22(state, action):
    """k1_blank_to_core__Blank_r33c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Blank_r33c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k1_blank_to_core__Blank_r33c22(state):
    state.Blank_r33c22_color = 2


def _guard_k1_frame_to_field__Frame_r36c11(state, action):
    """k1_frame_to_field__Frame_r36c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c11(state):
    state.Frame_r36c11_color = 5


def _guard_k1_frame_to_field__Frame_r36c12(state, action):
    """k1_frame_to_field__Frame_r36c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c12(state):
    state.Frame_r36c12_color = 5


def _guard_k1_frame_to_field__Frame_r36c13(state, action):
    """k1_frame_to_field__Frame_r36c13  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c13(state):
    state.Frame_r36c13_color = 5


def _guard_k1_frame_to_field__Frame_r36c14(state, action):
    """k1_frame_to_field__Frame_r36c14  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c14(state):
    state.Frame_r36c14_color = 5


def _guard_k1_frame_to_field__Frame_r36c15(state, action):
    """k1_frame_to_field__Frame_r36c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c15(state):
    state.Frame_r36c15_color = 5


def _guard_k1_frame_to_field__Frame_r36c16(state, action):
    """k1_frame_to_field__Frame_r36c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r36c16(state):
    state.Frame_r36c16_color = 5


def _guard_k1_frame_to_field__Frame_r37c11(state, action):
    """k1_frame_to_field__Frame_r37c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r37c11(state):
    state.Frame_r37c11_color = 5


def _guard_k1_frame_to_field__Frame_r37c16(state, action):
    """k1_frame_to_field__Frame_r37c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r37c16(state):
    state.Frame_r37c16_color = 5


def _guard_k1_frame_to_field__Frame_r38c11(state, action):
    """k1_frame_to_field__Frame_r38c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r38c11(state):
    state.Frame_r38c11_color = 5


def _guard_k1_frame_to_field__Frame_r38c13(state, action):
    """k1_frame_to_field__Frame_r38c13  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r38c13(state):
    state.Frame_r38c13_color = 5


def _guard_k1_frame_to_field__Frame_r38c14(state, action):
    """k1_frame_to_field__Frame_r38c14  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r38c14(state):
    state.Frame_r38c14_color = 5


def _guard_k1_frame_to_field__Frame_r39c11(state, action):
    """k1_frame_to_field__Frame_r39c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r39c11(state):
    state.Frame_r39c11_color = 5


def _guard_k1_frame_to_field__Frame_r39c13(state, action):
    """k1_frame_to_field__Frame_r39c13  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r39c13(state):
    state.Frame_r39c13_color = 5


def _guard_k1_frame_to_field__Frame_r39c14(state, action):
    """k1_frame_to_field__Frame_r39c14  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r39c14(state):
    state.Frame_r39c14_color = 5


def _guard_k1_frame_to_field__Frame_r40c11(state, action):
    """k1_frame_to_field__Frame_r40c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r40c11(state):
    state.Frame_r40c11_color = 5


def _guard_k1_frame_to_field__Frame_r40c16(state, action):
    """k1_frame_to_field__Frame_r40c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r40c16(state):
    state.Frame_r40c16_color = 5


def _guard_k1_frame_to_field__Frame_r41c11(state, action):
    """k1_frame_to_field__Frame_r41c11  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c11(state):
    state.Frame_r41c11_color = 5


def _guard_k1_frame_to_field__Frame_r41c12(state, action):
    """k1_frame_to_field__Frame_r41c12  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c12(state):
    state.Frame_r41c12_color = 5


def _guard_k1_frame_to_field__Frame_r41c13(state, action):
    """k1_frame_to_field__Frame_r41c13  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c13(state):
    state.Frame_r41c13_color = 5


def _guard_k1_frame_to_field__Frame_r41c14(state, action):
    """k1_frame_to_field__Frame_r41c14  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c14(state):
    state.Frame_r41c14_color = 5


def _guard_k1_frame_to_field__Frame_r41c15(state, action):
    """k1_frame_to_field__Frame_r41c15  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c15(state):
    state.Frame_r41c15_color = 5


def _guard_k1_frame_to_field__Frame_r41c16(state, action):
    """k1_frame_to_field__Frame_r41c16  [ev: t1,t6,t8,t11,t13,t15  cov: 14/14]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_frame_to_field__Frame_r41c16(state):
    state.Frame_r41c16_color = 5


def _guard_k1_frame_to_bar__Frame_r36c11(state, action):
    """k1_frame_to_bar__Frame_r36c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c11(state):
    state.Frame_r36c11_color = 3


def _guard_k1_frame_to_bar__Frame_r36c12(state, action):
    """k1_frame_to_bar__Frame_r36c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c12(state):
    state.Frame_r36c12_color = 3


def _guard_k1_frame_to_bar__Frame_r36c13(state, action):
    """k1_frame_to_bar__Frame_r36c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c13(state):
    state.Frame_r36c13_color = 3


def _guard_k1_frame_to_bar__Frame_r36c14(state, action):
    """k1_frame_to_bar__Frame_r36c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c14(state):
    state.Frame_r36c14_color = 3


def _guard_k1_frame_to_bar__Frame_r36c15(state, action):
    """k1_frame_to_bar__Frame_r36c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c15(state):
    state.Frame_r36c15_color = 3


def _guard_k1_frame_to_bar__Frame_r36c16(state, action):
    """k1_frame_to_bar__Frame_r36c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r36c16(state):
    state.Frame_r36c16_color = 3


def _guard_k1_frame_to_bar__Frame_r37c11(state, action):
    """k1_frame_to_bar__Frame_r37c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r37c11(state):
    state.Frame_r37c11_color = 3


def _guard_k1_frame_to_bar__Frame_r37c16(state, action):
    """k1_frame_to_bar__Frame_r37c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r37c16(state):
    state.Frame_r37c16_color = 3


def _guard_k1_frame_to_bar__Frame_r38c11(state, action):
    """k1_frame_to_bar__Frame_r38c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r38c11(state):
    state.Frame_r38c11_color = 3


def _guard_k1_frame_to_bar__Frame_r38c13(state, action):
    """k1_frame_to_bar__Frame_r38c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r38c13(state):
    state.Frame_r38c13_color = 3


def _guard_k1_frame_to_bar__Frame_r38c14(state, action):
    """k1_frame_to_bar__Frame_r38c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r38c14(state):
    state.Frame_r38c14_color = 3


def _guard_k1_frame_to_bar__Frame_r39c11(state, action):
    """k1_frame_to_bar__Frame_r39c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r39c11(state):
    state.Frame_r39c11_color = 3


def _guard_k1_frame_to_bar__Frame_r39c13(state, action):
    """k1_frame_to_bar__Frame_r39c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r39c13(state):
    state.Frame_r39c13_color = 3


def _guard_k1_frame_to_bar__Frame_r39c14(state, action):
    """k1_frame_to_bar__Frame_r39c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r39c14(state):
    state.Frame_r39c14_color = 3


def _guard_k1_frame_to_bar__Frame_r40c11(state, action):
    """k1_frame_to_bar__Frame_r40c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r40c11(state):
    state.Frame_r40c11_color = 3


def _guard_k1_frame_to_bar__Frame_r40c16(state, action):
    """k1_frame_to_bar__Frame_r40c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r40c16(state):
    state.Frame_r40c16_color = 3


def _guard_k1_frame_to_bar__Frame_r41c11(state, action):
    """k1_frame_to_bar__Frame_r41c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c11(state):
    state.Frame_r41c11_color = 3


def _guard_k1_frame_to_bar__Frame_r41c12(state, action):
    """k1_frame_to_bar__Frame_r41c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c12(state):
    state.Frame_r41c12_color = 3


def _guard_k1_frame_to_bar__Frame_r41c13(state, action):
    """k1_frame_to_bar__Frame_r41c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c13(state):
    state.Frame_r41c13_color = 3


def _guard_k1_frame_to_bar__Frame_r41c14(state, action):
    """k1_frame_to_bar__Frame_r41c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c14(state):
    state.Frame_r41c14_color = 3


def _guard_k1_frame_to_bar__Frame_r41c15(state, action):
    """k1_frame_to_bar__Frame_r41c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c15(state):
    state.Frame_r41c15_color = 3


def _guard_k1_frame_to_bar__Frame_r41c16(state, action):
    """k1_frame_to_bar__Frame_r41c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_to_bar__Frame_r41c16(state):
    state.Frame_r41c16_color = 3


def _guard_k1_frame_clears__Frame_r36c11(state, action):
    """k1_frame_clears__Frame_r36c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c11(state):
    state.Frame_r36c11_color = 5


def _guard_k1_frame_clears__Frame_r36c12(state, action):
    """k1_frame_clears__Frame_r36c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c12(state):
    state.Frame_r36c12_color = 5


def _guard_k1_frame_clears__Frame_r36c13(state, action):
    """k1_frame_clears__Frame_r36c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c13(state):
    state.Frame_r36c13_color = 5


def _guard_k1_frame_clears__Frame_r36c14(state, action):
    """k1_frame_clears__Frame_r36c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c14(state):
    state.Frame_r36c14_color = 5


def _guard_k1_frame_clears__Frame_r36c15(state, action):
    """k1_frame_clears__Frame_r36c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c15(state):
    state.Frame_r36c15_color = 5


def _guard_k1_frame_clears__Frame_r36c16(state, action):
    """k1_frame_clears__Frame_r36c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r36c16(state):
    state.Frame_r36c16_color = 5


def _guard_k1_frame_clears__Frame_r37c11(state, action):
    """k1_frame_clears__Frame_r37c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r37c11(state):
    state.Frame_r37c11_color = 5


def _guard_k1_frame_clears__Frame_r37c16(state, action):
    """k1_frame_clears__Frame_r37c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r37c16(state):
    state.Frame_r37c16_color = 5


def _guard_k1_frame_clears__Frame_r38c11(state, action):
    """k1_frame_clears__Frame_r38c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r38c11(state):
    state.Frame_r38c11_color = 5


def _guard_k1_frame_clears__Frame_r38c13(state, action):
    """k1_frame_clears__Frame_r38c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r38c13(state):
    state.Frame_r38c13_color = 5


def _guard_k1_frame_clears__Frame_r38c14(state, action):
    """k1_frame_clears__Frame_r38c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r38c14(state):
    state.Frame_r38c14_color = 5


def _guard_k1_frame_clears__Frame_r39c11(state, action):
    """k1_frame_clears__Frame_r39c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r39c11(state):
    state.Frame_r39c11_color = 5


def _guard_k1_frame_clears__Frame_r39c13(state, action):
    """k1_frame_clears__Frame_r39c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r39c13(state):
    state.Frame_r39c13_color = 5


def _guard_k1_frame_clears__Frame_r39c14(state, action):
    """k1_frame_clears__Frame_r39c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r39c14(state):
    state.Frame_r39c14_color = 5


def _guard_k1_frame_clears__Frame_r40c11(state, action):
    """k1_frame_clears__Frame_r40c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r40c11(state):
    state.Frame_r40c11_color = 5


def _guard_k1_frame_clears__Frame_r40c16(state, action):
    """k1_frame_clears__Frame_r40c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r40c16(state):
    state.Frame_r40c16_color = 5


def _guard_k1_frame_clears__Frame_r41c11(state, action):
    """k1_frame_clears__Frame_r41c11  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c11(state):
    state.Frame_r41c11_color = 5


def _guard_k1_frame_clears__Frame_r41c12(state, action):
    """k1_frame_clears__Frame_r41c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c12(state):
    state.Frame_r41c12_color = 5


def _guard_k1_frame_clears__Frame_r41c13(state, action):
    """k1_frame_clears__Frame_r41c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c13(state):
    state.Frame_r41c13_color = 5


def _guard_k1_frame_clears__Frame_r41c14(state, action):
    """k1_frame_clears__Frame_r41c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c14(state):
    state.Frame_r41c14_color = 5


def _guard_k1_frame_clears__Frame_r41c15(state, action):
    """k1_frame_clears__Frame_r41c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c15(state):
    state.Frame_r41c15_color = 5


def _guard_k1_frame_clears__Frame_r41c16(state, action):
    """k1_frame_clears__Frame_r41c16  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_frame_clears__Frame_r41c16(state):
    state.Frame_r41c16_color = 5


def _guard_k1_frame_to_core__Frame_r36c11(state, action):
    """k1_frame_to_core__Frame_r36c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c11(state):
    state.Frame_r36c11_color = 2


def _guard_k1_frame_to_core__Frame_r36c12(state, action):
    """k1_frame_to_core__Frame_r36c12  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c12(state):
    state.Frame_r36c12_color = 2


def _guard_k1_frame_to_core__Frame_r36c13(state, action):
    """k1_frame_to_core__Frame_r36c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c13(state):
    state.Frame_r36c13_color = 2


def _guard_k1_frame_to_core__Frame_r36c14(state, action):
    """k1_frame_to_core__Frame_r36c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c14(state):
    state.Frame_r36c14_color = 2


def _guard_k1_frame_to_core__Frame_r36c15(state, action):
    """k1_frame_to_core__Frame_r36c15  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c15(state):
    state.Frame_r36c15_color = 2


def _guard_k1_frame_to_core__Frame_r36c16(state, action):
    """k1_frame_to_core__Frame_r36c16  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r36c16(state):
    state.Frame_r36c16_color = 2


def _guard_k1_frame_to_core__Frame_r37c11(state, action):
    """k1_frame_to_core__Frame_r37c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r37c11(state):
    state.Frame_r37c11_color = 2


def _guard_k1_frame_to_core__Frame_r37c16(state, action):
    """k1_frame_to_core__Frame_r37c16  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r37c16(state):
    state.Frame_r37c16_color = 2


def _guard_k1_frame_to_core__Frame_r38c11(state, action):
    """k1_frame_to_core__Frame_r38c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r38c11(state):
    state.Frame_r38c11_color = 2


def _guard_k1_frame_to_core__Frame_r38c13(state, action):
    """k1_frame_to_core__Frame_r38c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r38c13(state):
    state.Frame_r38c13_color = 2


def _guard_k1_frame_to_core__Frame_r38c14(state, action):
    """k1_frame_to_core__Frame_r38c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r38c14(state):
    state.Frame_r38c14_color = 2


def _guard_k1_frame_to_core__Frame_r39c11(state, action):
    """k1_frame_to_core__Frame_r39c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r39c11(state):
    state.Frame_r39c11_color = 2


def _guard_k1_frame_to_core__Frame_r39c13(state, action):
    """k1_frame_to_core__Frame_r39c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r39c13(state):
    state.Frame_r39c13_color = 2


def _guard_k1_frame_to_core__Frame_r39c14(state, action):
    """k1_frame_to_core__Frame_r39c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r39c14(state):
    state.Frame_r39c14_color = 2


def _guard_k1_frame_to_core__Frame_r40c11(state, action):
    """k1_frame_to_core__Frame_r40c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r40c11(state):
    state.Frame_r40c11_color = 2


def _guard_k1_frame_to_core__Frame_r40c16(state, action):
    """k1_frame_to_core__Frame_r40c16  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r40c16(state):
    state.Frame_r40c16_color = 2


def _guard_k1_frame_to_core__Frame_r41c11(state, action):
    """k1_frame_to_core__Frame_r41c11  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c11(state):
    state.Frame_r41c11_color = 2


def _guard_k1_frame_to_core__Frame_r41c12(state, action):
    """k1_frame_to_core__Frame_r41c12  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c12(state):
    state.Frame_r41c12_color = 2


def _guard_k1_frame_to_core__Frame_r41c13(state, action):
    """k1_frame_to_core__Frame_r41c13  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c13(state):
    state.Frame_r41c13_color = 2


def _guard_k1_frame_to_core__Frame_r41c14(state, action):
    """k1_frame_to_core__Frame_r41c14  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c14(state):
    state.Frame_r41c14_color = 2


def _guard_k1_frame_to_core__Frame_r41c15(state, action):
    """k1_frame_to_core__Frame_r41c15  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c15(state):
    state.Frame_r41c15_color = 2


def _guard_k1_frame_to_core__Frame_r41c16(state, action):
    """k1_frame_to_core__Frame_r41c16  [ev: t1,t6,t8,t11,t13,t15  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k1_frame_to_core__Frame_r41c16(state):
    state.Frame_r41c16_color = 2


def _guard_k1_hollow_to_field__Hollow_r37c12(state, action):
    """k1_hollow_to_field__Hollow_r37c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r37c12(state):
    state.Hollow_r37c12_color = 5


def _guard_k1_hollow_to_field__Hollow_r37c13(state, action):
    """k1_hollow_to_field__Hollow_r37c13  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r37c13(state):
    state.Hollow_r37c13_color = 5


def _guard_k1_hollow_to_field__Hollow_r37c14(state, action):
    """k1_hollow_to_field__Hollow_r37c14  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r37c14(state):
    state.Hollow_r37c14_color = 5


def _guard_k1_hollow_to_field__Hollow_r37c15(state, action):
    """k1_hollow_to_field__Hollow_r37c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r37c15(state):
    state.Hollow_r37c15_color = 5


def _guard_k1_hollow_to_field__Hollow_r38c12(state, action):
    """k1_hollow_to_field__Hollow_r38c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r38c12(state):
    state.Hollow_r38c12_color = 5


def _guard_k1_hollow_to_field__Hollow_r38c15(state, action):
    """k1_hollow_to_field__Hollow_r38c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r38c15(state):
    state.Hollow_r38c15_color = 5


def _guard_k1_hollow_to_field__Hollow_r39c12(state, action):
    """k1_hollow_to_field__Hollow_r39c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r39c12(state):
    state.Hollow_r39c12_color = 5


def _guard_k1_hollow_to_field__Hollow_r39c15(state, action):
    """k1_hollow_to_field__Hollow_r39c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r39c15(state):
    state.Hollow_r39c15_color = 5


def _guard_k1_hollow_to_field__Hollow_r40c12(state, action):
    """k1_hollow_to_field__Hollow_r40c12  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r40c12(state):
    state.Hollow_r40c12_color = 5


def _guard_k1_hollow_to_field__Hollow_r40c13(state, action):
    """k1_hollow_to_field__Hollow_r40c13  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r40c13(state):
    state.Hollow_r40c13_color = 5


def _guard_k1_hollow_to_field__Hollow_r40c14(state, action):
    """k1_hollow_to_field__Hollow_r40c14  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r40c14(state):
    state.Hollow_r40c14_color = 5


def _guard_k1_hollow_to_field__Hollow_r40c15(state, action):
    """k1_hollow_to_field__Hollow_r40c15  [ev: t1,t6,t8,t11,t13,t15  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_hollow_to_field__Hollow_r40c15(state):
    state.Hollow_r40c15_color = 5


def _guard_k1_hollow_to_bar__Hollow_r37c12(state, action):
    """k1_hollow_to_bar__Hollow_r37c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r37c12(state):
    state.Hollow_r37c12_color = 3


def _guard_k1_hollow_to_bar__Hollow_r37c13(state, action):
    """k1_hollow_to_bar__Hollow_r37c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r37c13(state):
    state.Hollow_r37c13_color = 3


def _guard_k1_hollow_to_bar__Hollow_r37c14(state, action):
    """k1_hollow_to_bar__Hollow_r37c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r37c14(state):
    state.Hollow_r37c14_color = 3


def _guard_k1_hollow_to_bar__Hollow_r37c15(state, action):
    """k1_hollow_to_bar__Hollow_r37c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r37c15(state):
    state.Hollow_r37c15_color = 3


def _guard_k1_hollow_to_bar__Hollow_r38c12(state, action):
    """k1_hollow_to_bar__Hollow_r38c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r38c12(state):
    state.Hollow_r38c12_color = 3


def _guard_k1_hollow_to_bar__Hollow_r38c15(state, action):
    """k1_hollow_to_bar__Hollow_r38c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r38c15(state):
    state.Hollow_r38c15_color = 3


def _guard_k1_hollow_to_bar__Hollow_r39c12(state, action):
    """k1_hollow_to_bar__Hollow_r39c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r39c12(state):
    state.Hollow_r39c12_color = 3


def _guard_k1_hollow_to_bar__Hollow_r39c15(state, action):
    """k1_hollow_to_bar__Hollow_r39c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r39c15(state):
    state.Hollow_r39c15_color = 3


def _guard_k1_hollow_to_bar__Hollow_r40c12(state, action):
    """k1_hollow_to_bar__Hollow_r40c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r40c12(state):
    state.Hollow_r40c12_color = 3


def _guard_k1_hollow_to_bar__Hollow_r40c13(state, action):
    """k1_hollow_to_bar__Hollow_r40c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r40c13(state):
    state.Hollow_r40c13_color = 3


def _guard_k1_hollow_to_bar__Hollow_r40c14(state, action):
    """k1_hollow_to_bar__Hollow_r40c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r40c14(state):
    state.Hollow_r40c14_color = 3


def _guard_k1_hollow_to_bar__Hollow_r40c15(state, action):
    """k1_hollow_to_bar__Hollow_r40c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up')) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_to_bar__Hollow_r40c15(state):
    state.Hollow_r40c15_color = 3


def _guard_k1_hollow_clears__Hollow_r37c12(state, action):
    """k1_hollow_clears__Hollow_r37c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r37c12(state):
    state.Hollow_r37c12_color = 5


def _guard_k1_hollow_clears__Hollow_r37c13(state, action):
    """k1_hollow_clears__Hollow_r37c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r37c13(state):
    state.Hollow_r37c13_color = 5


def _guard_k1_hollow_clears__Hollow_r37c14(state, action):
    """k1_hollow_clears__Hollow_r37c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r37c14(state):
    state.Hollow_r37c14_color = 5


def _guard_k1_hollow_clears__Hollow_r37c15(state, action):
    """k1_hollow_clears__Hollow_r37c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r37c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r37c15(state):
    state.Hollow_r37c15_color = 5


def _guard_k1_hollow_clears__Hollow_r38c12(state, action):
    """k1_hollow_clears__Hollow_r38c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r38c12(state):
    state.Hollow_r38c12_color = 5


def _guard_k1_hollow_clears__Hollow_r38c15(state, action):
    """k1_hollow_clears__Hollow_r38c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r38c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r38c15(state):
    state.Hollow_r38c15_color = 5


def _guard_k1_hollow_clears__Hollow_r39c12(state, action):
    """k1_hollow_clears__Hollow_r39c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r39c12(state):
    state.Hollow_r39c12_color = 5


def _guard_k1_hollow_clears__Hollow_r39c15(state, action):
    """k1_hollow_clears__Hollow_r39c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r39c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r39c15(state):
    state.Hollow_r39c15_color = 5


def _guard_k1_hollow_clears__Hollow_r40c12(state, action):
    """k1_hollow_clears__Hollow_r40c12  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r40c12(state):
    state.Hollow_r40c12_color = 5


def _guard_k1_hollow_clears__Hollow_r40c13(state, action):
    """k1_hollow_clears__Hollow_r40c13  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r40c13(state):
    state.Hollow_r40c13_color = 5


def _guard_k1_hollow_clears__Hollow_r40c14(state, action):
    """k1_hollow_clears__Hollow_r40c14  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r40c14(state):
    state.Hollow_r40c14_color = 5


def _guard_k1_hollow_clears__Hollow_r40c15(state, action):
    """k1_hollow_clears__Hollow_r40c15  [ev: t1,t6,t8,t11,t13,t15  cov: 2/2]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Hollow_r40c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up')) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 3): return False
    return True


def _effect_k1_hollow_clears__Hollow_r40c15(state):
    state.Hollow_r40c15_color = 5


def _guard_k1_dot_to_field__Dot_r38c16(state, action):
    """k1_dot_to_field__Dot_r38c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r38c16(state):
    state.Dot_r38c16_color = 5


def _guard_k1_dot_to_field__Dot_r38c18(state, action):
    """k1_dot_to_field__Dot_r38c18  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r38c18(state):
    state.Dot_r38c18_color = 5


def _guard_k1_dot_to_field__Dot_r38c19(state, action):
    """k1_dot_to_field__Dot_r38c19  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r38c19(state):
    state.Dot_r38c19_color = 5


def _guard_k1_dot_to_field__Dot_r38c21(state, action):
    """k1_dot_to_field__Dot_r38c21  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r38c21(state):
    state.Dot_r38c21_color = 5


def _guard_k1_dot_to_field__Dot_r38c22(state, action):
    """k1_dot_to_field__Dot_r38c22  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r38c22(state):
    state.Dot_r38c22_color = 5


def _guard_k1_dot_to_field__Dot_r39c17(state, action):
    """k1_dot_to_field__Dot_r39c17  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r39c17(state):
    state.Dot_r39c17_color = 5


def _guard_k1_dot_to_field__Dot_r39c18(state, action):
    """k1_dot_to_field__Dot_r39c18  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r39c18(state):
    state.Dot_r39c18_color = 5


def _guard_k1_dot_to_field__Dot_r39c20(state, action):
    """k1_dot_to_field__Dot_r39c20  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r39c20(state):
    state.Dot_r39c20_color = 5


def _guard_k1_dot_to_field__Dot_r39c21(state, action):
    """k1_dot_to_field__Dot_r39c21  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_dot_to_field__Dot_r39c21(state):
    state.Dot_r39c21_color = 5


def _guard_k1_dot_to_blank__Dot_r38c16(state, action):
    """k1_dot_to_blank__Dot_r38c16  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r38c16(state):
    state.Dot_r38c16_color = 4


def _guard_k1_dot_to_blank__Dot_r38c18(state, action):
    """k1_dot_to_blank__Dot_r38c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r38c18(state):
    state.Dot_r38c18_color = 4


def _guard_k1_dot_to_blank__Dot_r38c19(state, action):
    """k1_dot_to_blank__Dot_r38c19  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r38c19(state):
    state.Dot_r38c19_color = 4


def _guard_k1_dot_to_blank__Dot_r38c21(state, action):
    """k1_dot_to_blank__Dot_r38c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r38c21(state):
    state.Dot_r38c21_color = 4


def _guard_k1_dot_to_blank__Dot_r38c22(state, action):
    """k1_dot_to_blank__Dot_r38c22  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r38c22(state):
    state.Dot_r38c22_color = 4


def _guard_k1_dot_to_blank__Dot_r39c17(state, action):
    """k1_dot_to_blank__Dot_r39c17  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r39c17(state):
    state.Dot_r39c17_color = 4


def _guard_k1_dot_to_blank__Dot_r39c18(state, action):
    """k1_dot_to_blank__Dot_r39c18  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r39c18(state):
    state.Dot_r39c18_color = 4


def _guard_k1_dot_to_blank__Dot_r39c20(state, action):
    """k1_dot_to_blank__Dot_r39c20  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r39c20(state):
    state.Dot_r39c20_color = 4


def _guard_k1_dot_to_blank__Dot_r39c21(state, action):
    """k1_dot_to_blank__Dot_r39c21  [ev: t1  cov: 8/8]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_dot_to_blank__Dot_r39c21(state):
    state.Dot_r39c21_color = 4


def _guard_k1_core_to_field__BarCore_r32c13(state, action):
    """k1_core_to_field__BarCore_r32c13  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c13_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 5


def _guard_k1_core_to_field__BarCore_r32c14(state, action):
    """k1_core_to_field__BarCore_r32c14  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c14_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 5


def _guard_k1_core_to_field__BarCore_r33c13(state, action):
    """k1_core_to_field__BarCore_r33c13  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c13_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 5


def _guard_k1_core_to_field__BarCore_r33c14(state, action):
    """k1_core_to_field__BarCore_r33c14  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c14_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 5


def _guard_k1_core_to_field__BarCore_r38c17(state, action):
    """k1_core_to_field__BarCore_r38c17  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c17_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 5


def _guard_k1_core_to_field__BarCore_r38c20(state, action):
    """k1_core_to_field__BarCore_r38c20  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c20_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 5


def _guard_k1_core_to_field__BarCore_r39c16(state, action):
    """k1_core_to_field__BarCore_r39c16  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c16_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 5


def _guard_k1_core_to_field__BarCore_r39c19(state, action):
    """k1_core_to_field__BarCore_r39c19  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c19_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 5


def _guard_k1_core_to_field__BarCore_r39c22(state, action):
    """k1_core_to_field__BarCore_r39c22  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c22_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 5


def _guard_k1_core_to_field__BarCore_r53c59(state, action):
    """k1_core_to_field__BarCore_r53c59  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c59_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 5


def _guard_k1_core_to_field__BarCore_r53c60(state, action):
    """k1_core_to_field__BarCore_r53c60  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c60_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 5


def _guard_k1_core_to_field__BarCore_r53c61(state, action):
    """k1_core_to_field__BarCore_r53c61  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c61_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 5


def _guard_k1_core_to_field__BarCore_r53c62(state, action):
    """k1_core_to_field__BarCore_r53c62  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c62_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 5


def _guard_k1_core_to_field__BarCore_r53c63(state, action):
    """k1_core_to_field__BarCore_r53c63  [ev: t1,t6,t8,t11,t13,t15  cov: 1/1]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c63_pos, 'left')) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 5): return False
    return True


def _effect_k1_core_to_field__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 5


def _guard_k1_core_to_blank__BarCore_r32c13(state, action):
    """k1_core_to_blank__BarCore_r32c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 4


def _guard_k1_core_to_blank__BarCore_r32c14(state, action):
    """k1_core_to_blank__BarCore_r32c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 4


def _guard_k1_core_to_blank__BarCore_r33c13(state, action):
    """k1_core_to_blank__BarCore_r33c13  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 4


def _guard_k1_core_to_blank__BarCore_r33c14(state, action):
    """k1_core_to_blank__BarCore_r33c14  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 4


def _guard_k1_core_to_blank__BarCore_r38c17(state, action):
    """k1_core_to_blank__BarCore_r38c17  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c17_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 4


def _guard_k1_core_to_blank__BarCore_r38c20(state, action):
    """k1_core_to_blank__BarCore_r38c20  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c20_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 4


def _guard_k1_core_to_blank__BarCore_r39c16(state, action):
    """k1_core_to_blank__BarCore_r39c16  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c16_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 4


def _guard_k1_core_to_blank__BarCore_r39c19(state, action):
    """k1_core_to_blank__BarCore_r39c19  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c19_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 4


def _guard_k1_core_to_blank__BarCore_r39c22(state, action):
    """k1_core_to_blank__BarCore_r39c22  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c22_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 4


def _guard_k1_core_to_blank__BarCore_r53c59(state, action):
    """k1_core_to_blank__BarCore_r53c59  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c59_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 4


def _guard_k1_core_to_blank__BarCore_r53c60(state, action):
    """k1_core_to_blank__BarCore_r53c60  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c60_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 4


def _guard_k1_core_to_blank__BarCore_r53c61(state, action):
    """k1_core_to_blank__BarCore_r53c61  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c61_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 4


def _guard_k1_core_to_blank__BarCore_r53c62(state, action):
    """k1_core_to_blank__BarCore_r53c62  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c62_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 4


def _guard_k1_core_to_blank__BarCore_r53c63(state, action):
    """k1_core_to_blank__BarCore_r53c63  [ev: t1  cov: 4/4]"""
    if action != ('key', 1): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c63_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k1_core_to_blank__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 4


def _guard_k2_field_from_frame__Field_r30c11(state, action):
    """k2_field_from_frame__Field_r30c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r30c11(state):
    state.Field_r30c11_color = 5


def _guard_k2_field_from_frame__Field_r30c12(state, action):
    """k2_field_from_frame__Field_r30c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r30c12(state):
    state.Field_r30c12_color = 5


def _guard_k2_field_from_frame__Field_r30c15(state, action):
    """k2_field_from_frame__Field_r30c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r30c15(state):
    state.Field_r30c15_color = 5


def _guard_k2_field_from_frame__Field_r30c16(state, action):
    """k2_field_from_frame__Field_r30c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r30c16(state):
    state.Field_r30c16_color = 5


def _guard_k2_field_from_frame__Field_r31c11(state, action):
    """k2_field_from_frame__Field_r31c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r31c11(state):
    state.Field_r31c11_color = 5


def _guard_k2_field_from_frame__Field_r31c12(state, action):
    """k2_field_from_frame__Field_r31c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r31c12(state):
    state.Field_r31c12_color = 5


def _guard_k2_field_from_frame__Field_r31c15(state, action):
    """k2_field_from_frame__Field_r31c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r31c15(state):
    state.Field_r31c15_color = 5


def _guard_k2_field_from_frame__Field_r31c16(state, action):
    """k2_field_from_frame__Field_r31c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r31c16(state):
    state.Field_r31c16_color = 5


def _guard_k2_field_from_frame__Field_r32c11(state, action):
    """k2_field_from_frame__Field_r32c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r32c11(state):
    state.Field_r32c11_color = 5


def _guard_k2_field_from_frame__Field_r32c12(state, action):
    """k2_field_from_frame__Field_r32c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r32c12(state):
    state.Field_r32c12_color = 5


def _guard_k2_field_from_frame__Field_r32c15(state, action):
    """k2_field_from_frame__Field_r32c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r32c15(state):
    state.Field_r32c15_color = 5


def _guard_k2_field_from_frame__Field_r32c16(state, action):
    """k2_field_from_frame__Field_r32c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r32c16(state):
    state.Field_r32c16_color = 5


def _guard_k2_field_from_frame__Field_r33c11(state, action):
    """k2_field_from_frame__Field_r33c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r33c11(state):
    state.Field_r33c11_color = 5


def _guard_k2_field_from_frame__Field_r33c12(state, action):
    """k2_field_from_frame__Field_r33c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r33c12(state):
    state.Field_r33c12_color = 5


def _guard_k2_field_from_frame__Field_r33c15(state, action):
    """k2_field_from_frame__Field_r33c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r33c15(state):
    state.Field_r33c15_color = 5


def _guard_k2_field_from_frame__Field_r33c16(state, action):
    """k2_field_from_frame__Field_r33c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r33c16(state):
    state.Field_r33c16_color = 5


def _guard_k2_field_from_frame__Field_r34c11(state, action):
    """k2_field_from_frame__Field_r34c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r34c11(state):
    state.Field_r34c11_color = 5


def _guard_k2_field_from_frame__Field_r34c12(state, action):
    """k2_field_from_frame__Field_r34c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r34c12(state):
    state.Field_r34c12_color = 5


def _guard_k2_field_from_frame__Field_r34c15(state, action):
    """k2_field_from_frame__Field_r34c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r34c15(state):
    state.Field_r34c15_color = 5


def _guard_k2_field_from_frame__Field_r34c16(state, action):
    """k2_field_from_frame__Field_r34c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r34c16(state):
    state.Field_r34c16_color = 5


def _guard_k2_field_from_frame__Field_r35c11(state, action):
    """k2_field_from_frame__Field_r35c11  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r35c11(state):
    state.Field_r35c11_color = 5


def _guard_k2_field_from_frame__Field_r35c12(state, action):
    """k2_field_from_frame__Field_r35c12  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r35c12(state):
    state.Field_r35c12_color = 5


def _guard_k2_field_from_frame__Field_r35c15(state, action):
    """k2_field_from_frame__Field_r35c15  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r35c15(state):
    state.Field_r35c15_color = 5


def _guard_k2_field_from_frame__Field_r35c16(state, action):
    """k2_field_from_frame__Field_r35c16  [ev: t2,t7,t10,t12,t14,t16  cov: 14/14]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_frame__Field_r35c16(state):
    state.Field_r35c16_color = 5


def _guard_k2_field_from_hollow__Field_r30c11(state, action):
    """k2_field_from_hollow__Field_r30c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r30c11(state):
    state.Field_r30c11_color = 5


def _guard_k2_field_from_hollow__Field_r30c12(state, action):
    """k2_field_from_hollow__Field_r30c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r30c12(state):
    state.Field_r30c12_color = 5


def _guard_k2_field_from_hollow__Field_r30c15(state, action):
    """k2_field_from_hollow__Field_r30c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r30c15(state):
    state.Field_r30c15_color = 5


def _guard_k2_field_from_hollow__Field_r30c16(state, action):
    """k2_field_from_hollow__Field_r30c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r30c16(state):
    state.Field_r30c16_color = 5


def _guard_k2_field_from_hollow__Field_r31c11(state, action):
    """k2_field_from_hollow__Field_r31c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r31c11(state):
    state.Field_r31c11_color = 5


def _guard_k2_field_from_hollow__Field_r31c12(state, action):
    """k2_field_from_hollow__Field_r31c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r31c12(state):
    state.Field_r31c12_color = 5


def _guard_k2_field_from_hollow__Field_r31c15(state, action):
    """k2_field_from_hollow__Field_r31c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r31c15(state):
    state.Field_r31c15_color = 5


def _guard_k2_field_from_hollow__Field_r31c16(state, action):
    """k2_field_from_hollow__Field_r31c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r31c16(state):
    state.Field_r31c16_color = 5


def _guard_k2_field_from_hollow__Field_r32c11(state, action):
    """k2_field_from_hollow__Field_r32c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r32c11(state):
    state.Field_r32c11_color = 5


def _guard_k2_field_from_hollow__Field_r32c12(state, action):
    """k2_field_from_hollow__Field_r32c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r32c12(state):
    state.Field_r32c12_color = 5


def _guard_k2_field_from_hollow__Field_r32c15(state, action):
    """k2_field_from_hollow__Field_r32c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r32c15(state):
    state.Field_r32c15_color = 5


def _guard_k2_field_from_hollow__Field_r32c16(state, action):
    """k2_field_from_hollow__Field_r32c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r32c16(state):
    state.Field_r32c16_color = 5


def _guard_k2_field_from_hollow__Field_r33c11(state, action):
    """k2_field_from_hollow__Field_r33c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r33c11(state):
    state.Field_r33c11_color = 5


def _guard_k2_field_from_hollow__Field_r33c12(state, action):
    """k2_field_from_hollow__Field_r33c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r33c12(state):
    state.Field_r33c12_color = 5


def _guard_k2_field_from_hollow__Field_r33c15(state, action):
    """k2_field_from_hollow__Field_r33c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r33c15(state):
    state.Field_r33c15_color = 5


def _guard_k2_field_from_hollow__Field_r33c16(state, action):
    """k2_field_from_hollow__Field_r33c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r33c16(state):
    state.Field_r33c16_color = 5


def _guard_k2_field_from_hollow__Field_r34c11(state, action):
    """k2_field_from_hollow__Field_r34c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r34c11(state):
    state.Field_r34c11_color = 5


def _guard_k2_field_from_hollow__Field_r34c12(state, action):
    """k2_field_from_hollow__Field_r34c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r34c12(state):
    state.Field_r34c12_color = 5


def _guard_k2_field_from_hollow__Field_r34c15(state, action):
    """k2_field_from_hollow__Field_r34c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r34c15(state):
    state.Field_r34c15_color = 5


def _guard_k2_field_from_hollow__Field_r34c16(state, action):
    """k2_field_from_hollow__Field_r34c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r34c16(state):
    state.Field_r34c16_color = 5


def _guard_k2_field_from_hollow__Field_r35c11(state, action):
    """k2_field_from_hollow__Field_r35c11  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r35c11(state):
    state.Field_r35c11_color = 5


def _guard_k2_field_from_hollow__Field_r35c12(state, action):
    """k2_field_from_hollow__Field_r35c12  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r35c12(state):
    state.Field_r35c12_color = 5


def _guard_k2_field_from_hollow__Field_r35c15(state, action):
    """k2_field_from_hollow__Field_r35c15  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r35c15(state):
    state.Field_r35c15_color = 5


def _guard_k2_field_from_hollow__Field_r35c16(state, action):
    """k2_field_from_hollow__Field_r35c16  [ev: t2,t7,t10,t12,t14,t16  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_hollow__Field_r35c16(state):
    state.Field_r35c16_color = 5


def _guard_k2_field_from_dot__Field_r30c11(state, action):
    """k2_field_from_dot__Field_r30c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r30c11(state):
    state.Field_r30c11_color = 5


def _guard_k2_field_from_dot__Field_r30c12(state, action):
    """k2_field_from_dot__Field_r30c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r30c12(state):
    state.Field_r30c12_color = 5


def _guard_k2_field_from_dot__Field_r30c15(state, action):
    """k2_field_from_dot__Field_r30c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r30c15(state):
    state.Field_r30c15_color = 5


def _guard_k2_field_from_dot__Field_r30c16(state, action):
    """k2_field_from_dot__Field_r30c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r30c16(state):
    state.Field_r30c16_color = 5


def _guard_k2_field_from_dot__Field_r31c11(state, action):
    """k2_field_from_dot__Field_r31c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r31c11(state):
    state.Field_r31c11_color = 5


def _guard_k2_field_from_dot__Field_r31c12(state, action):
    """k2_field_from_dot__Field_r31c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r31c12(state):
    state.Field_r31c12_color = 5


def _guard_k2_field_from_dot__Field_r31c15(state, action):
    """k2_field_from_dot__Field_r31c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r31c15(state):
    state.Field_r31c15_color = 5


def _guard_k2_field_from_dot__Field_r31c16(state, action):
    """k2_field_from_dot__Field_r31c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r31c16(state):
    state.Field_r31c16_color = 5


def _guard_k2_field_from_dot__Field_r32c11(state, action):
    """k2_field_from_dot__Field_r32c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r32c11(state):
    state.Field_r32c11_color = 5


def _guard_k2_field_from_dot__Field_r32c12(state, action):
    """k2_field_from_dot__Field_r32c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r32c12(state):
    state.Field_r32c12_color = 5


def _guard_k2_field_from_dot__Field_r32c15(state, action):
    """k2_field_from_dot__Field_r32c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r32c15(state):
    state.Field_r32c15_color = 5


def _guard_k2_field_from_dot__Field_r32c16(state, action):
    """k2_field_from_dot__Field_r32c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r32c16(state):
    state.Field_r32c16_color = 5


def _guard_k2_field_from_dot__Field_r33c11(state, action):
    """k2_field_from_dot__Field_r33c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r33c11(state):
    state.Field_r33c11_color = 5


def _guard_k2_field_from_dot__Field_r33c12(state, action):
    """k2_field_from_dot__Field_r33c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r33c12(state):
    state.Field_r33c12_color = 5


def _guard_k2_field_from_dot__Field_r33c15(state, action):
    """k2_field_from_dot__Field_r33c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r33c15(state):
    state.Field_r33c15_color = 5


def _guard_k2_field_from_dot__Field_r33c16(state, action):
    """k2_field_from_dot__Field_r33c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r33c16(state):
    state.Field_r33c16_color = 5


def _guard_k2_field_from_dot__Field_r34c11(state, action):
    """k2_field_from_dot__Field_r34c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r34c11(state):
    state.Field_r34c11_color = 5


def _guard_k2_field_from_dot__Field_r34c12(state, action):
    """k2_field_from_dot__Field_r34c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r34c12(state):
    state.Field_r34c12_color = 5


def _guard_k2_field_from_dot__Field_r34c15(state, action):
    """k2_field_from_dot__Field_r34c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r34c15(state):
    state.Field_r34c15_color = 5


def _guard_k2_field_from_dot__Field_r34c16(state, action):
    """k2_field_from_dot__Field_r34c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r34c16(state):
    state.Field_r34c16_color = 5


def _guard_k2_field_from_dot__Field_r35c11(state, action):
    """k2_field_from_dot__Field_r35c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r35c11(state):
    state.Field_r35c11_color = 5


def _guard_k2_field_from_dot__Field_r35c12(state, action):
    """k2_field_from_dot__Field_r35c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r35c12(state):
    state.Field_r35c12_color = 5


def _guard_k2_field_from_dot__Field_r35c15(state, action):
    """k2_field_from_dot__Field_r35c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r35c15(state):
    state.Field_r35c15_color = 5


def _guard_k2_field_from_dot__Field_r35c16(state, action):
    """k2_field_from_dot__Field_r35c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_dot__Field_r35c16(state):
    state.Field_r35c16_color = 5


def _guard_k2_field_from_core__Field_r30c11(state, action):
    """k2_field_from_core__Field_r30c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r30c11(state):
    state.Field_r30c11_color = 5


def _guard_k2_field_from_core__Field_r30c12(state, action):
    """k2_field_from_core__Field_r30c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r30c12(state):
    state.Field_r30c12_color = 5


def _guard_k2_field_from_core__Field_r30c15(state, action):
    """k2_field_from_core__Field_r30c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r30c15(state):
    state.Field_r30c15_color = 5


def _guard_k2_field_from_core__Field_r30c16(state, action):
    """k2_field_from_core__Field_r30c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r30c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r30c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r30c16(state):
    state.Field_r30c16_color = 5


def _guard_k2_field_from_core__Field_r31c11(state, action):
    """k2_field_from_core__Field_r31c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r31c11(state):
    state.Field_r31c11_color = 5


def _guard_k2_field_from_core__Field_r31c12(state, action):
    """k2_field_from_core__Field_r31c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r31c12(state):
    state.Field_r31c12_color = 5


def _guard_k2_field_from_core__Field_r31c15(state, action):
    """k2_field_from_core__Field_r31c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r31c15(state):
    state.Field_r31c15_color = 5


def _guard_k2_field_from_core__Field_r31c16(state, action):
    """k2_field_from_core__Field_r31c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r31c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r31c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r31c16(state):
    state.Field_r31c16_color = 5


def _guard_k2_field_from_core__Field_r32c11(state, action):
    """k2_field_from_core__Field_r32c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r32c11(state):
    state.Field_r32c11_color = 5


def _guard_k2_field_from_core__Field_r32c12(state, action):
    """k2_field_from_core__Field_r32c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r32c12(state):
    state.Field_r32c12_color = 5


def _guard_k2_field_from_core__Field_r32c15(state, action):
    """k2_field_from_core__Field_r32c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r32c15(state):
    state.Field_r32c15_color = 5


def _guard_k2_field_from_core__Field_r32c16(state, action):
    """k2_field_from_core__Field_r32c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r32c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r32c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r32c16(state):
    state.Field_r32c16_color = 5


def _guard_k2_field_from_core__Field_r33c11(state, action):
    """k2_field_from_core__Field_r33c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r33c11(state):
    state.Field_r33c11_color = 5


def _guard_k2_field_from_core__Field_r33c12(state, action):
    """k2_field_from_core__Field_r33c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r33c12(state):
    state.Field_r33c12_color = 5


def _guard_k2_field_from_core__Field_r33c15(state, action):
    """k2_field_from_core__Field_r33c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r33c15(state):
    state.Field_r33c15_color = 5


def _guard_k2_field_from_core__Field_r33c16(state, action):
    """k2_field_from_core__Field_r33c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r33c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r33c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r33c16(state):
    state.Field_r33c16_color = 5


def _guard_k2_field_from_core__Field_r34c11(state, action):
    """k2_field_from_core__Field_r34c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r34c11(state):
    state.Field_r34c11_color = 5


def _guard_k2_field_from_core__Field_r34c12(state, action):
    """k2_field_from_core__Field_r34c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r34c12(state):
    state.Field_r34c12_color = 5


def _guard_k2_field_from_core__Field_r34c15(state, action):
    """k2_field_from_core__Field_r34c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r34c15(state):
    state.Field_r34c15_color = 5


def _guard_k2_field_from_core__Field_r34c16(state, action):
    """k2_field_from_core__Field_r34c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r34c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r34c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r34c16(state):
    state.Field_r34c16_color = 5


def _guard_k2_field_from_core__Field_r35c11(state, action):
    """k2_field_from_core__Field_r35c11  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c11_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r35c11(state):
    state.Field_r35c11_color = 5


def _guard_k2_field_from_core__Field_r35c12(state, action):
    """k2_field_from_core__Field_r35c12  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c12_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r35c12(state):
    state.Field_r35c12_color = 5


def _guard_k2_field_from_core__Field_r35c15(state, action):
    """k2_field_from_core__Field_r35c15  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r35c15(state):
    state.Field_r35c15_color = 5


def _guard_k2_field_from_core__Field_r35c16(state, action):
    """k2_field_from_core__Field_r35c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Field_r35c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Field_r35c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_field_from_core__Field_r35c16(state):
    state.Field_r35c16_color = 5


def _guard_k2_bar_from_frame__BarBody_r30c13(state, action):
    """k2_bar_from_frame__BarBody_r30c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 3


def _guard_k2_bar_from_frame__BarBody_r30c14(state, action):
    """k2_bar_from_frame__BarBody_r30c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 3


def _guard_k2_bar_from_frame__BarBody_r31c13(state, action):
    """k2_bar_from_frame__BarBody_r31c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 3


def _guard_k2_bar_from_frame__BarBody_r31c14(state, action):
    """k2_bar_from_frame__BarBody_r31c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 3


def _guard_k2_bar_from_frame__BarBody_r34c13(state, action):
    """k2_bar_from_frame__BarBody_r34c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 3


def _guard_k2_bar_from_frame__BarBody_r34c14(state, action):
    """k2_bar_from_frame__BarBody_r34c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 3


def _guard_k2_bar_from_frame__BarBody_r35c13(state, action):
    """k2_bar_from_frame__BarBody_r35c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 3


def _guard_k2_bar_from_frame__BarBody_r35c14(state, action):
    """k2_bar_from_frame__BarBody_r35c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_frame__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 3


def _guard_k2_bar_from_hollow__BarBody_r30c13(state, action):
    """k2_bar_from_hollow__BarBody_r30c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 3


def _guard_k2_bar_from_hollow__BarBody_r30c14(state, action):
    """k2_bar_from_hollow__BarBody_r30c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 3


def _guard_k2_bar_from_hollow__BarBody_r31c13(state, action):
    """k2_bar_from_hollow__BarBody_r31c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 3


def _guard_k2_bar_from_hollow__BarBody_r31c14(state, action):
    """k2_bar_from_hollow__BarBody_r31c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 3


def _guard_k2_bar_from_hollow__BarBody_r34c13(state, action):
    """k2_bar_from_hollow__BarBody_r34c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 3


def _guard_k2_bar_from_hollow__BarBody_r34c14(state, action):
    """k2_bar_from_hollow__BarBody_r34c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 3


def _guard_k2_bar_from_hollow__BarBody_r35c13(state, action):
    """k2_bar_from_hollow__BarBody_r35c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 3


def _guard_k2_bar_from_hollow__BarBody_r35c14(state, action):
    """k2_bar_from_hollow__BarBody_r35c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 3): return False
    return True


def _effect_k2_bar_from_hollow__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r30c13(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r30c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r30c14(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r30c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r31c13(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r31c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r31c14(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r31c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r34c13(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r34c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r34c14(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r34c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r35c13(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r35c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 3


def _guard_k2_bar_regrows_from_hollow__BarBody_r35c14(state, action):
    """k2_bar_regrows_from_hollow__BarBody_r35c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 0): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_hollow__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r30c13(state, action):
    """k2_bar_regrows_from_frame__BarBody_r30c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r30c13(state):
    state.BarBody_r30c13_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r30c14(state, action):
    """k2_bar_regrows_from_frame__BarBody_r30c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r30c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r30c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r30c14(state):
    state.BarBody_r30c14_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r31c13(state, action):
    """k2_bar_regrows_from_frame__BarBody_r31c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r31c13(state):
    state.BarBody_r31c13_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r31c14(state, action):
    """k2_bar_regrows_from_frame__BarBody_r31c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r31c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r31c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r31c14(state):
    state.BarBody_r31c14_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r34c13(state, action):
    """k2_bar_regrows_from_frame__BarBody_r34c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r34c13(state):
    state.BarBody_r34c13_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r34c14(state, action):
    """k2_bar_regrows_from_frame__BarBody_r34c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r34c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r34c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r34c14(state):
    state.BarBody_r34c14_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r35c13(state, action):
    """k2_bar_regrows_from_frame__BarBody_r35c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r35c13(state):
    state.BarBody_r35c13_color = 3


def _guard_k2_bar_regrows_from_frame__BarBody_r35c14(state, action):
    """k2_bar_regrows_from_frame__BarBody_r35c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarBody_r35c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarBody_r35c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_k2_bar_regrows_from_frame__BarBody_r35c14(state):
    state.BarBody_r35c14_color = 3


def _guard_k2_core_from_frame__BarCore_r32c13(state, action):
    """k2_core_from_frame__BarCore_r32c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 2


def _guard_k2_core_from_frame__BarCore_r32c14(state, action):
    """k2_core_from_frame__BarCore_r32c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 2


def _guard_k2_core_from_frame__BarCore_r33c13(state, action):
    """k2_core_from_frame__BarCore_r33c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 2


def _guard_k2_core_from_frame__BarCore_r33c14(state, action):
    """k2_core_from_frame__BarCore_r33c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 2


def _guard_k2_core_from_frame__BarCore_r38c17(state, action):
    """k2_core_from_frame__BarCore_r38c17  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 2


def _guard_k2_core_from_frame__BarCore_r38c20(state, action):
    """k2_core_from_frame__BarCore_r38c20  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 2


def _guard_k2_core_from_frame__BarCore_r39c16(state, action):
    """k2_core_from_frame__BarCore_r39c16  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 2


def _guard_k2_core_from_frame__BarCore_r39c19(state, action):
    """k2_core_from_frame__BarCore_r39c19  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 2


def _guard_k2_core_from_frame__BarCore_r39c22(state, action):
    """k2_core_from_frame__BarCore_r39c22  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 2


def _guard_k2_core_from_frame__BarCore_r53c59(state, action):
    """k2_core_from_frame__BarCore_r53c59  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 2


def _guard_k2_core_from_frame__BarCore_r53c60(state, action):
    """k2_core_from_frame__BarCore_r53c60  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 2


def _guard_k2_core_from_frame__BarCore_r53c61(state, action):
    """k2_core_from_frame__BarCore_r53c61  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 2


def _guard_k2_core_from_frame__BarCore_r53c62(state, action):
    """k2_core_from_frame__BarCore_r53c62  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 2


def _guard_k2_core_from_frame__BarCore_r53c63(state, action):
    """k2_core_from_frame__BarCore_r53c63  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 6): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 2): return False
    return True


def _effect_k2_core_from_frame__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 2


def _guard_k2_blank_from_dot__Blank_r32c17(state, action):
    """k2_blank_from_dot__Blank_r32c17  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c17(state):
    state.Blank_r32c17_color = 4


def _guard_k2_blank_from_dot__Blank_r32c18(state, action):
    """k2_blank_from_dot__Blank_r32c18  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c18(state):
    state.Blank_r32c18_color = 4


def _guard_k2_blank_from_dot__Blank_r32c19(state, action):
    """k2_blank_from_dot__Blank_r32c19  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c19(state):
    state.Blank_r32c19_color = 4


def _guard_k2_blank_from_dot__Blank_r32c20(state, action):
    """k2_blank_from_dot__Blank_r32c20  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c20(state):
    state.Blank_r32c20_color = 4


def _guard_k2_blank_from_dot__Blank_r32c21(state, action):
    """k2_blank_from_dot__Blank_r32c21  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c21(state):
    state.Blank_r32c21_color = 4


def _guard_k2_blank_from_dot__Blank_r32c22(state, action):
    """k2_blank_from_dot__Blank_r32c22  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r32c22(state):
    state.Blank_r32c22_color = 4


def _guard_k2_blank_from_dot__Blank_r33c17(state, action):
    """k2_blank_from_dot__Blank_r33c17  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c17(state):
    state.Blank_r33c17_color = 4


def _guard_k2_blank_from_dot__Blank_r33c18(state, action):
    """k2_blank_from_dot__Blank_r33c18  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c18(state):
    state.Blank_r33c18_color = 4


def _guard_k2_blank_from_dot__Blank_r33c19(state, action):
    """k2_blank_from_dot__Blank_r33c19  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c19(state):
    state.Blank_r33c19_color = 4


def _guard_k2_blank_from_dot__Blank_r33c20(state, action):
    """k2_blank_from_dot__Blank_r33c20  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c20(state):
    state.Blank_r33c20_color = 4


def _guard_k2_blank_from_dot__Blank_r33c21(state, action):
    """k2_blank_from_dot__Blank_r33c21  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c21(state):
    state.Blank_r33c21_color = 4


def _guard_k2_blank_from_dot__Blank_r33c22(state, action):
    """k2_blank_from_dot__Blank_r33c22  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_dot__Blank_r33c22(state):
    state.Blank_r33c22_color = 4


def _guard_k2_blank_from_core__Blank_r32c17(state, action):
    """k2_blank_from_core__Blank_r32c17  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c17(state):
    state.Blank_r32c17_color = 4


def _guard_k2_blank_from_core__Blank_r32c18(state, action):
    """k2_blank_from_core__Blank_r32c18  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c18_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c18(state):
    state.Blank_r32c18_color = 4


def _guard_k2_blank_from_core__Blank_r32c19(state, action):
    """k2_blank_from_core__Blank_r32c19  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c19(state):
    state.Blank_r32c19_color = 4


def _guard_k2_blank_from_core__Blank_r32c20(state, action):
    """k2_blank_from_core__Blank_r32c20  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c20(state):
    state.Blank_r32c20_color = 4


def _guard_k2_blank_from_core__Blank_r32c21(state, action):
    """k2_blank_from_core__Blank_r32c21  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c21_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c21(state):
    state.Blank_r32c21_color = 4


def _guard_k2_blank_from_core__Blank_r32c22(state, action):
    """k2_blank_from_core__Blank_r32c22  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r32c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r32c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r32c22(state):
    state.Blank_r32c22_color = 4


def _guard_k2_blank_from_core__Blank_r33c17(state, action):
    """k2_blank_from_core__Blank_r33c17  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c17(state):
    state.Blank_r33c17_color = 4


def _guard_k2_blank_from_core__Blank_r33c18(state, action):
    """k2_blank_from_core__Blank_r33c18  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c18_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c18(state):
    state.Blank_r33c18_color = 4


def _guard_k2_blank_from_core__Blank_r33c19(state, action):
    """k2_blank_from_core__Blank_r33c19  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c19_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c19(state):
    state.Blank_r33c19_color = 4


def _guard_k2_blank_from_core__Blank_r33c20(state, action):
    """k2_blank_from_core__Blank_r33c20  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c20_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c20(state):
    state.Blank_r33c20_color = 4


def _guard_k2_blank_from_core__Blank_r33c21(state, action):
    """k2_blank_from_core__Blank_r33c21  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c21_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c21_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c21(state):
    state.Blank_r33c21_color = 4


def _guard_k2_blank_from_core__Blank_r33c22(state, action):
    """k2_blank_from_core__Blank_r33c22  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Blank_r33c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Blank_r33c22_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 4): return False
    return True


def _effect_k2_blank_from_core__Blank_r33c22(state):
    state.Blank_r33c22_color = 4


def _guard_k2_frame_from_field__Frame_r36c11(state, action):
    """k2_frame_from_field__Frame_r36c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c11(state):
    state.Frame_r36c11_color = 6


def _guard_k2_frame_from_field__Frame_r36c12(state, action):
    """k2_frame_from_field__Frame_r36c12  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c12(state):
    state.Frame_r36c12_color = 6


def _guard_k2_frame_from_field__Frame_r36c13(state, action):
    """k2_frame_from_field__Frame_r36c13  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c13(state):
    state.Frame_r36c13_color = 6


def _guard_k2_frame_from_field__Frame_r36c14(state, action):
    """k2_frame_from_field__Frame_r36c14  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c14(state):
    state.Frame_r36c14_color = 6


def _guard_k2_frame_from_field__Frame_r36c15(state, action):
    """k2_frame_from_field__Frame_r36c15  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c15(state):
    state.Frame_r36c15_color = 6


def _guard_k2_frame_from_field__Frame_r36c16(state, action):
    """k2_frame_from_field__Frame_r36c16  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r36c16(state):
    state.Frame_r36c16_color = 6


def _guard_k2_frame_from_field__Frame_r37c11(state, action):
    """k2_frame_from_field__Frame_r37c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r37c11(state):
    state.Frame_r37c11_color = 6


def _guard_k2_frame_from_field__Frame_r37c16(state, action):
    """k2_frame_from_field__Frame_r37c16  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r37c16(state):
    state.Frame_r37c16_color = 6


def _guard_k2_frame_from_field__Frame_r38c11(state, action):
    """k2_frame_from_field__Frame_r38c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r38c11(state):
    state.Frame_r38c11_color = 6


def _guard_k2_frame_from_field__Frame_r38c13(state, action):
    """k2_frame_from_field__Frame_r38c13  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r38c13(state):
    state.Frame_r38c13_color = 6


def _guard_k2_frame_from_field__Frame_r38c14(state, action):
    """k2_frame_from_field__Frame_r38c14  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r38c14(state):
    state.Frame_r38c14_color = 6


def _guard_k2_frame_from_field__Frame_r39c11(state, action):
    """k2_frame_from_field__Frame_r39c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r39c11(state):
    state.Frame_r39c11_color = 6


def _guard_k2_frame_from_field__Frame_r39c13(state, action):
    """k2_frame_from_field__Frame_r39c13  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r39c13(state):
    state.Frame_r39c13_color = 6


def _guard_k2_frame_from_field__Frame_r39c14(state, action):
    """k2_frame_from_field__Frame_r39c14  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r39c14(state):
    state.Frame_r39c14_color = 6


def _guard_k2_frame_from_field__Frame_r40c11(state, action):
    """k2_frame_from_field__Frame_r40c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r40c11(state):
    state.Frame_r40c11_color = 6


def _guard_k2_frame_from_field__Frame_r40c16(state, action):
    """k2_frame_from_field__Frame_r40c16  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r40c16(state):
    state.Frame_r40c16_color = 6


def _guard_k2_frame_from_field__Frame_r41c11(state, action):
    """k2_frame_from_field__Frame_r41c11  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c11(state):
    state.Frame_r41c11_color = 6


def _guard_k2_frame_from_field__Frame_r41c12(state, action):
    """k2_frame_from_field__Frame_r41c12  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c12(state):
    state.Frame_r41c12_color = 6


def _guard_k2_frame_from_field__Frame_r41c13(state, action):
    """k2_frame_from_field__Frame_r41c13  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c13(state):
    state.Frame_r41c13_color = 6


def _guard_k2_frame_from_field__Frame_r41c14(state, action):
    """k2_frame_from_field__Frame_r41c14  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c14(state):
    state.Frame_r41c14_color = 6


def _guard_k2_frame_from_field__Frame_r41c15(state, action):
    """k2_frame_from_field__Frame_r41c15  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c15(state):
    state.Frame_r41c15_color = 6


def _guard_k2_frame_from_field__Frame_r41c16(state, action):
    """k2_frame_from_field__Frame_r41c16  [ev: t2,t7,t10,t12,t14,t16  cov: 16/16]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_field__Frame_r41c16(state):
    state.Frame_r41c16_color = 6


def _guard_k2_frame_from_bar__Frame_r36c11(state, action):
    """k2_frame_from_bar__Frame_r36c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c11(state):
    state.Frame_r36c11_color = 6


def _guard_k2_frame_from_bar__Frame_r36c12(state, action):
    """k2_frame_from_bar__Frame_r36c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c12(state):
    state.Frame_r36c12_color = 6


def _guard_k2_frame_from_bar__Frame_r36c13(state, action):
    """k2_frame_from_bar__Frame_r36c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c13(state):
    state.Frame_r36c13_color = 6


def _guard_k2_frame_from_bar__Frame_r36c14(state, action):
    """k2_frame_from_bar__Frame_r36c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c14(state):
    state.Frame_r36c14_color = 6


def _guard_k2_frame_from_bar__Frame_r36c15(state, action):
    """k2_frame_from_bar__Frame_r36c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c15(state):
    state.Frame_r36c15_color = 6


def _guard_k2_frame_from_bar__Frame_r36c16(state, action):
    """k2_frame_from_bar__Frame_r36c16  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r36c16(state):
    state.Frame_r36c16_color = 6


def _guard_k2_frame_from_bar__Frame_r37c11(state, action):
    """k2_frame_from_bar__Frame_r37c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r37c11(state):
    state.Frame_r37c11_color = 6


def _guard_k2_frame_from_bar__Frame_r37c16(state, action):
    """k2_frame_from_bar__Frame_r37c16  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r37c16(state):
    state.Frame_r37c16_color = 6


def _guard_k2_frame_from_bar__Frame_r38c11(state, action):
    """k2_frame_from_bar__Frame_r38c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r38c11(state):
    state.Frame_r38c11_color = 6


def _guard_k2_frame_from_bar__Frame_r38c13(state, action):
    """k2_frame_from_bar__Frame_r38c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r38c13(state):
    state.Frame_r38c13_color = 6


def _guard_k2_frame_from_bar__Frame_r38c14(state, action):
    """k2_frame_from_bar__Frame_r38c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r38c14(state):
    state.Frame_r38c14_color = 6


def _guard_k2_frame_from_bar__Frame_r39c11(state, action):
    """k2_frame_from_bar__Frame_r39c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r39c11(state):
    state.Frame_r39c11_color = 6


def _guard_k2_frame_from_bar__Frame_r39c13(state, action):
    """k2_frame_from_bar__Frame_r39c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r39c13(state):
    state.Frame_r39c13_color = 6


def _guard_k2_frame_from_bar__Frame_r39c14(state, action):
    """k2_frame_from_bar__Frame_r39c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r39c14(state):
    state.Frame_r39c14_color = 6


def _guard_k2_frame_from_bar__Frame_r40c11(state, action):
    """k2_frame_from_bar__Frame_r40c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r40c11(state):
    state.Frame_r40c11_color = 6


def _guard_k2_frame_from_bar__Frame_r40c16(state, action):
    """k2_frame_from_bar__Frame_r40c16  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r40c16(state):
    state.Frame_r40c16_color = 6


def _guard_k2_frame_from_bar__Frame_r41c11(state, action):
    """k2_frame_from_bar__Frame_r41c11  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c11(state):
    state.Frame_r41c11_color = 6


def _guard_k2_frame_from_bar__Frame_r41c12(state, action):
    """k2_frame_from_bar__Frame_r41c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c12(state):
    state.Frame_r41c12_color = 6


def _guard_k2_frame_from_bar__Frame_r41c13(state, action):
    """k2_frame_from_bar__Frame_r41c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c13(state):
    state.Frame_r41c13_color = 6


def _guard_k2_frame_from_bar__Frame_r41c14(state, action):
    """k2_frame_from_bar__Frame_r41c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c14(state):
    state.Frame_r41c14_color = 6


def _guard_k2_frame_from_bar__Frame_r41c15(state, action):
    """k2_frame_from_bar__Frame_r41c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c15(state):
    state.Frame_r41c15_color = 6


def _guard_k2_frame_from_bar__Frame_r41c16(state, action):
    """k2_frame_from_bar__Frame_r41c16  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_bar__Frame_r41c16(state):
    state.Frame_r41c16_color = 6


def _guard_k2_frame_from_core__Frame_r36c11(state, action):
    """k2_frame_from_core__Frame_r36c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c11(state):
    state.Frame_r36c11_color = 6


def _guard_k2_frame_from_core__Frame_r36c12(state, action):
    """k2_frame_from_core__Frame_r36c12  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c12(state):
    state.Frame_r36c12_color = 6


def _guard_k2_frame_from_core__Frame_r36c13(state, action):
    """k2_frame_from_core__Frame_r36c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c13(state):
    state.Frame_r36c13_color = 6


def _guard_k2_frame_from_core__Frame_r36c14(state, action):
    """k2_frame_from_core__Frame_r36c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c14(state):
    state.Frame_r36c14_color = 6


def _guard_k2_frame_from_core__Frame_r36c15(state, action):
    """k2_frame_from_core__Frame_r36c15  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c15(state):
    state.Frame_r36c15_color = 6


def _guard_k2_frame_from_core__Frame_r36c16(state, action):
    """k2_frame_from_core__Frame_r36c16  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r36c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r36c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r36c16(state):
    state.Frame_r36c16_color = 6


def _guard_k2_frame_from_core__Frame_r37c11(state, action):
    """k2_frame_from_core__Frame_r37c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r37c11(state):
    state.Frame_r37c11_color = 6


def _guard_k2_frame_from_core__Frame_r37c16(state, action):
    """k2_frame_from_core__Frame_r37c16  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r37c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r37c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r37c16(state):
    state.Frame_r37c16_color = 6


def _guard_k2_frame_from_core__Frame_r38c11(state, action):
    """k2_frame_from_core__Frame_r38c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r38c11(state):
    state.Frame_r38c11_color = 6


def _guard_k2_frame_from_core__Frame_r38c13(state, action):
    """k2_frame_from_core__Frame_r38c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r38c13(state):
    state.Frame_r38c13_color = 6


def _guard_k2_frame_from_core__Frame_r38c14(state, action):
    """k2_frame_from_core__Frame_r38c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r38c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r38c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r38c14(state):
    state.Frame_r38c14_color = 6


def _guard_k2_frame_from_core__Frame_r39c11(state, action):
    """k2_frame_from_core__Frame_r39c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r39c11(state):
    state.Frame_r39c11_color = 6


def _guard_k2_frame_from_core__Frame_r39c13(state, action):
    """k2_frame_from_core__Frame_r39c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r39c13(state):
    state.Frame_r39c13_color = 6


def _guard_k2_frame_from_core__Frame_r39c14(state, action):
    """k2_frame_from_core__Frame_r39c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r39c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r39c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r39c14(state):
    state.Frame_r39c14_color = 6


def _guard_k2_frame_from_core__Frame_r40c11(state, action):
    """k2_frame_from_core__Frame_r40c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r40c11(state):
    state.Frame_r40c11_color = 6


def _guard_k2_frame_from_core__Frame_r40c16(state, action):
    """k2_frame_from_core__Frame_r40c16  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r40c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r40c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r40c16(state):
    state.Frame_r40c16_color = 6


def _guard_k2_frame_from_core__Frame_r41c11(state, action):
    """k2_frame_from_core__Frame_r41c11  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c11_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c11_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c11(state):
    state.Frame_r41c11_color = 6


def _guard_k2_frame_from_core__Frame_r41c12(state, action):
    """k2_frame_from_core__Frame_r41c12  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c12_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c12(state):
    state.Frame_r41c12_color = 6


def _guard_k2_frame_from_core__Frame_r41c13(state, action):
    """k2_frame_from_core__Frame_r41c13  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c13(state):
    state.Frame_r41c13_color = 6


def _guard_k2_frame_from_core__Frame_r41c14(state, action):
    """k2_frame_from_core__Frame_r41c14  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c14(state):
    state.Frame_r41c14_color = 6


def _guard_k2_frame_from_core__Frame_r41c15(state, action):
    """k2_frame_from_core__Frame_r41c15  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c15_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c15(state):
    state.Frame_r41c15_color = 6


def _guard_k2_frame_from_core__Frame_r41c16(state, action):
    """k2_frame_from_core__Frame_r41c16  [ev: t2,t7,t10,t12,t14,t16  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Frame_r41c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Frame_r41c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 6): return False
    return True


def _effect_k2_frame_from_core__Frame_r41c16(state):
    state.Frame_r41c16_color = 6


def _guard_k2_hollow_from_field__Hollow_r37c12(state, action):
    """k2_hollow_from_field__Hollow_r37c12  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r37c12(state):
    state.Hollow_r37c12_color = 0


def _guard_k2_hollow_from_field__Hollow_r37c13(state, action):
    """k2_hollow_from_field__Hollow_r37c13  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r37c13(state):
    state.Hollow_r37c13_color = 0


def _guard_k2_hollow_from_field__Hollow_r37c14(state, action):
    """k2_hollow_from_field__Hollow_r37c14  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r37c14(state):
    state.Hollow_r37c14_color = 0


def _guard_k2_hollow_from_field__Hollow_r37c15(state, action):
    """k2_hollow_from_field__Hollow_r37c15  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r37c15(state):
    state.Hollow_r37c15_color = 0


def _guard_k2_hollow_from_field__Hollow_r38c12(state, action):
    """k2_hollow_from_field__Hollow_r38c12  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r38c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r38c12(state):
    state.Hollow_r38c12_color = 0


def _guard_k2_hollow_from_field__Hollow_r38c15(state, action):
    """k2_hollow_from_field__Hollow_r38c15  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r38c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r38c15(state):
    state.Hollow_r38c15_color = 0


def _guard_k2_hollow_from_field__Hollow_r39c12(state, action):
    """k2_hollow_from_field__Hollow_r39c12  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r39c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r39c12(state):
    state.Hollow_r39c12_color = 0


def _guard_k2_hollow_from_field__Hollow_r39c15(state, action):
    """k2_hollow_from_field__Hollow_r39c15  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r39c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r39c15(state):
    state.Hollow_r39c15_color = 0


def _guard_k2_hollow_from_field__Hollow_r40c12(state, action):
    """k2_hollow_from_field__Hollow_r40c12  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c12_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r40c12(state):
    state.Hollow_r40c12_color = 0


def _guard_k2_hollow_from_field__Hollow_r40c13(state, action):
    """k2_hollow_from_field__Hollow_r40c13  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r40c13(state):
    state.Hollow_r40c13_color = 0


def _guard_k2_hollow_from_field__Hollow_r40c14(state, action):
    """k2_hollow_from_field__Hollow_r40c14  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r40c14(state):
    state.Hollow_r40c14_color = 0


def _guard_k2_hollow_from_field__Hollow_r40c15(state, action):
    """k2_hollow_from_field__Hollow_r40c15  [ev: t2,t7,t10,t12,t14,t16  cov: 10/10]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_field__Hollow_r40c15(state):
    state.Hollow_r40c15_color = 0


def _guard_k2_hollow_from_bar__Hollow_r37c12(state, action):
    """k2_hollow_from_bar__Hollow_r37c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r37c12(state):
    state.Hollow_r37c12_color = 0


def _guard_k2_hollow_from_bar__Hollow_r37c13(state, action):
    """k2_hollow_from_bar__Hollow_r37c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r37c13(state):
    state.Hollow_r37c13_color = 0


def _guard_k2_hollow_from_bar__Hollow_r37c14(state, action):
    """k2_hollow_from_bar__Hollow_r37c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r37c14(state):
    state.Hollow_r37c14_color = 0


def _guard_k2_hollow_from_bar__Hollow_r37c15(state, action):
    """k2_hollow_from_bar__Hollow_r37c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r37c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r37c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r37c15(state):
    state.Hollow_r37c15_color = 0


def _guard_k2_hollow_from_bar__Hollow_r38c12(state, action):
    """k2_hollow_from_bar__Hollow_r38c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r38c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r38c12(state):
    state.Hollow_r38c12_color = 0


def _guard_k2_hollow_from_bar__Hollow_r38c15(state, action):
    """k2_hollow_from_bar__Hollow_r38c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r38c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r38c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r38c15(state):
    state.Hollow_r38c15_color = 0


def _guard_k2_hollow_from_bar__Hollow_r39c12(state, action):
    """k2_hollow_from_bar__Hollow_r39c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r39c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r39c12(state):
    state.Hollow_r39c12_color = 0


def _guard_k2_hollow_from_bar__Hollow_r39c15(state, action):
    """k2_hollow_from_bar__Hollow_r39c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r39c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r39c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r39c15(state):
    state.Hollow_r39c15_color = 0


def _guard_k2_hollow_from_bar__Hollow_r40c12(state, action):
    """k2_hollow_from_bar__Hollow_r40c12  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c12_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c12_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r40c12(state):
    state.Hollow_r40c12_color = 0


def _guard_k2_hollow_from_bar__Hollow_r40c13(state, action):
    """k2_hollow_from_bar__Hollow_r40c13  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c13_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r40c13(state):
    state.Hollow_r40c13_color = 0


def _guard_k2_hollow_from_bar__Hollow_r40c14(state, action):
    """k2_hollow_from_bar__Hollow_r40c14  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c14_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r40c14(state):
    state.Hollow_r40c14_color = 0


def _guard_k2_hollow_from_bar__Hollow_r40c15(state, action):
    """k2_hollow_from_bar__Hollow_r40c15  [ev: t2,t7,t10,t12,t14,t16  cov: 2/2]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Hollow_r40c15_pos) == 3): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Hollow_r40c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 0): return False
    return True


def _effect_k2_hollow_from_bar__Hollow_r40c15(state):
    state.Hollow_r40c15_color = 0


def _guard_k2_dot_from_field__Dot_r38c16(state, action):
    """k2_dot_from_field__Dot_r38c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r38c16(state):
    state.Dot_r38c16_color = 1


def _guard_k2_dot_from_field__Dot_r38c18(state, action):
    """k2_dot_from_field__Dot_r38c18  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r38c18(state):
    state.Dot_r38c18_color = 1


def _guard_k2_dot_from_field__Dot_r38c19(state, action):
    """k2_dot_from_field__Dot_r38c19  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r38c19(state):
    state.Dot_r38c19_color = 1


def _guard_k2_dot_from_field__Dot_r38c21(state, action):
    """k2_dot_from_field__Dot_r38c21  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r38c21(state):
    state.Dot_r38c21_color = 1


def _guard_k2_dot_from_field__Dot_r38c22(state, action):
    """k2_dot_from_field__Dot_r38c22  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r38c22(state):
    state.Dot_r38c22_color = 1


def _guard_k2_dot_from_field__Dot_r39c17(state, action):
    """k2_dot_from_field__Dot_r39c17  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r39c17(state):
    state.Dot_r39c17_color = 1


def _guard_k2_dot_from_field__Dot_r39c18(state, action):
    """k2_dot_from_field__Dot_r39c18  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r39c18(state):
    state.Dot_r39c18_color = 1


def _guard_k2_dot_from_field__Dot_r39c20(state, action):
    """k2_dot_from_field__Dot_r39c20  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r39c20(state):
    state.Dot_r39c20_color = 1


def _guard_k2_dot_from_field__Dot_r39c21(state, action):
    """k2_dot_from_field__Dot_r39c21  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_field__Dot_r39c21(state):
    state.Dot_r39c21_color = 1


def _guard_k2_dot_from_blank__Dot_r38c16(state, action):
    """k2_dot_from_blank__Dot_r38c16  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r38c16(state):
    state.Dot_r38c16_color = 1


def _guard_k2_dot_from_blank__Dot_r38c18(state, action):
    """k2_dot_from_blank__Dot_r38c18  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r38c18(state):
    state.Dot_r38c18_color = 1


def _guard_k2_dot_from_blank__Dot_r38c19(state, action):
    """k2_dot_from_blank__Dot_r38c19  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r38c19(state):
    state.Dot_r38c19_color = 1


def _guard_k2_dot_from_blank__Dot_r38c21(state, action):
    """k2_dot_from_blank__Dot_r38c21  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r38c21(state):
    state.Dot_r38c21_color = 1


def _guard_k2_dot_from_blank__Dot_r38c22(state, action):
    """k2_dot_from_blank__Dot_r38c22  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r38c22(state):
    state.Dot_r38c22_color = 1


def _guard_k2_dot_from_blank__Dot_r39c17(state, action):
    """k2_dot_from_blank__Dot_r39c17  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r39c17(state):
    state.Dot_r39c17_color = 1


def _guard_k2_dot_from_blank__Dot_r39c18(state, action):
    """k2_dot_from_blank__Dot_r39c18  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r39c18(state):
    state.Dot_r39c18_color = 1


def _guard_k2_dot_from_blank__Dot_r39c20(state, action):
    """k2_dot_from_blank__Dot_r39c20  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r39c20(state):
    state.Dot_r39c20_color = 1


def _guard_k2_dot_from_blank__Dot_r39c21(state, action):
    """k2_dot_from_blank__Dot_r39c21  [ev: t2  cov: 8/8]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 1): return False
    return True


def _effect_k2_dot_from_blank__Dot_r39c21(state):
    state.Dot_r39c21_color = 1


def _guard_k2_core_from_field__BarCore_r32c13(state, action):
    """k2_core_from_field__BarCore_r32c13  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 2


def _guard_k2_core_from_field__BarCore_r32c14(state, action):
    """k2_core_from_field__BarCore_r32c14  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 2


def _guard_k2_core_from_field__BarCore_r33c13(state, action):
    """k2_core_from_field__BarCore_r33c13  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 2


def _guard_k2_core_from_field__BarCore_r33c14(state, action):
    """k2_core_from_field__BarCore_r33c14  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 2


def _guard_k2_core_from_field__BarCore_r38c17(state, action):
    """k2_core_from_field__BarCore_r38c17  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 2


def _guard_k2_core_from_field__BarCore_r38c20(state, action):
    """k2_core_from_field__BarCore_r38c20  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 2


def _guard_k2_core_from_field__BarCore_r39c16(state, action):
    """k2_core_from_field__BarCore_r39c16  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 2


def _guard_k2_core_from_field__BarCore_r39c19(state, action):
    """k2_core_from_field__BarCore_r39c19  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 2


def _guard_k2_core_from_field__BarCore_r39c22(state, action):
    """k2_core_from_field__BarCore_r39c22  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 2


def _guard_k2_core_from_field__BarCore_r53c59(state, action):
    """k2_core_from_field__BarCore_r53c59  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 2


def _guard_k2_core_from_field__BarCore_r53c60(state, action):
    """k2_core_from_field__BarCore_r53c60  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 2


def _guard_k2_core_from_field__BarCore_r53c61(state, action):
    """k2_core_from_field__BarCore_r53c61  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 2


def _guard_k2_core_from_field__BarCore_r53c62(state, action):
    """k2_core_from_field__BarCore_r53c62  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 2


def _guard_k2_core_from_field__BarCore_r53c63(state, action):
    """k2_core_from_field__BarCore_r53c63  [ev: t2,t7,t10,t12,t14,t16  cov: 1/1]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_field__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 2


def _guard_k2_core_from_blank__BarCore_r32c13(state, action):
    """k2_core_from_blank__BarCore_r32c13  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 2


def _guard_k2_core_from_blank__BarCore_r32c14(state, action):
    """k2_core_from_blank__BarCore_r32c14  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 2


def _guard_k2_core_from_blank__BarCore_r33c13(state, action):
    """k2_core_from_blank__BarCore_r33c13  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 2


def _guard_k2_core_from_blank__BarCore_r33c14(state, action):
    """k2_core_from_blank__BarCore_r33c14  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 2


def _guard_k2_core_from_blank__BarCore_r38c17(state, action):
    """k2_core_from_blank__BarCore_r38c17  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 2


def _guard_k2_core_from_blank__BarCore_r38c20(state, action):
    """k2_core_from_blank__BarCore_r38c20  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 2


def _guard_k2_core_from_blank__BarCore_r39c16(state, action):
    """k2_core_from_blank__BarCore_r39c16  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 2


def _guard_k2_core_from_blank__BarCore_r39c19(state, action):
    """k2_core_from_blank__BarCore_r39c19  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 2


def _guard_k2_core_from_blank__BarCore_r39c22(state, action):
    """k2_core_from_blank__BarCore_r39c22  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 2


def _guard_k2_core_from_blank__BarCore_r53c59(state, action):
    """k2_core_from_blank__BarCore_r53c59  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 2


def _guard_k2_core_from_blank__BarCore_r53c60(state, action):
    """k2_core_from_blank__BarCore_r53c60  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 2


def _guard_k2_core_from_blank__BarCore_r53c61(state, action):
    """k2_core_from_blank__BarCore_r53c61  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 2


def _guard_k2_core_from_blank__BarCore_r53c62(state, action):
    """k2_core_from_blank__BarCore_r53c62  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 2


def _guard_k2_core_from_blank__BarCore_r53c63(state, action):
    """k2_core_from_blank__BarCore_r53c63  [ev: t2  cov: 4/4]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 4): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 2): return False
    return True


def _effect_k2_core_from_blank__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 2


def _guard_k3_dot_blanks__Dot_r38c16(state, action):
    """k3_dot_blanks__Dot_r38c16  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r38c16(state):
    state.Dot_r38c16_color = 4


def _guard_k3_dot_blanks__Dot_r38c18(state, action):
    """k3_dot_blanks__Dot_r38c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r38c18(state):
    state.Dot_r38c18_color = 4


def _guard_k3_dot_blanks__Dot_r38c19(state, action):
    """k3_dot_blanks__Dot_r38c19  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r38c19(state):
    state.Dot_r38c19_color = 4


def _guard_k3_dot_blanks__Dot_r38c21(state, action):
    """k3_dot_blanks__Dot_r38c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r38c21(state):
    state.Dot_r38c21_color = 4


def _guard_k3_dot_blanks__Dot_r38c22(state, action):
    """k3_dot_blanks__Dot_r38c22  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r38c22(state):
    state.Dot_r38c22_color = 4


def _guard_k3_dot_blanks__Dot_r39c17(state, action):
    """k3_dot_blanks__Dot_r39c17  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r39c17(state):
    state.Dot_r39c17_color = 4


def _guard_k3_dot_blanks__Dot_r39c18(state, action):
    """k3_dot_blanks__Dot_r39c18  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r39c18(state):
    state.Dot_r39c18_color = 4


def _guard_k3_dot_blanks__Dot_r39c20(state, action):
    """k3_dot_blanks__Dot_r39c20  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r39c20(state):
    state.Dot_r39c20_color = 4


def _guard_k3_dot_blanks__Dot_r39c21(state, action):
    """k3_dot_blanks__Dot_r39c21  [ev: t3  cov: 8/8]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_dot_blanks__Dot_r39c21(state):
    state.Dot_r39c21_color = 4


def _guard_k3_core_blanks__BarCore_r32c13(state, action):
    """k3_core_blanks__BarCore_r32c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 4


def _guard_k3_core_blanks__BarCore_r32c14(state, action):
    """k3_core_blanks__BarCore_r32c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 4


def _guard_k3_core_blanks__BarCore_r33c13(state, action):
    """k3_core_blanks__BarCore_r33c13  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 4


def _guard_k3_core_blanks__BarCore_r33c14(state, action):
    """k3_core_blanks__BarCore_r33c14  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 4


def _guard_k3_core_blanks__BarCore_r38c17(state, action):
    """k3_core_blanks__BarCore_r38c17  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c17_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 4


def _guard_k3_core_blanks__BarCore_r38c20(state, action):
    """k3_core_blanks__BarCore_r38c20  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c20_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 4


def _guard_k3_core_blanks__BarCore_r39c16(state, action):
    """k3_core_blanks__BarCore_r39c16  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c16_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 4


def _guard_k3_core_blanks__BarCore_r39c19(state, action):
    """k3_core_blanks__BarCore_r39c19  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c19_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 4


def _guard_k3_core_blanks__BarCore_r39c22(state, action):
    """k3_core_blanks__BarCore_r39c22  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c22_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 4


def _guard_k3_core_blanks__BarCore_r53c59(state, action):
    """k3_core_blanks__BarCore_r53c59  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c59_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 4


def _guard_k3_core_blanks__BarCore_r53c60(state, action):
    """k3_core_blanks__BarCore_r53c60  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c60_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 4


def _guard_k3_core_blanks__BarCore_r53c61(state, action):
    """k3_core_blanks__BarCore_r53c61  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c61_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 4


def _guard_k3_core_blanks__BarCore_r53c62(state, action):
    """k3_core_blanks__BarCore_r53c62  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c62_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 4


def _guard_k3_core_blanks__BarCore_r53c63(state, action):
    """k3_core_blanks__BarCore_r53c63  [ev: t3  cov: 4/4]"""
    if action != ('key', 3): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c63_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k3_core_blanks__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 4


def _guard_k4_dot_lights__Dot_r38c16(state, action):
    """k4_dot_lights__Dot_r38c16  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r38c16(state):
    state.Dot_r38c16_color = 1


def _guard_k4_dot_lights__Dot_r38c18(state, action):
    """k4_dot_lights__Dot_r38c18  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r38c18(state):
    state.Dot_r38c18_color = 1


def _guard_k4_dot_lights__Dot_r38c19(state, action):
    """k4_dot_lights__Dot_r38c19  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r38c19(state):
    state.Dot_r38c19_color = 1


def _guard_k4_dot_lights__Dot_r38c21(state, action):
    """k4_dot_lights__Dot_r38c21  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r38c21(state):
    state.Dot_r38c21_color = 1


def _guard_k4_dot_lights__Dot_r38c22(state, action):
    """k4_dot_lights__Dot_r38c22  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r38c22(state):
    state.Dot_r38c22_color = 1


def _guard_k4_dot_lights__Dot_r39c17(state, action):
    """k4_dot_lights__Dot_r39c17  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r39c17(state):
    state.Dot_r39c17_color = 1


def _guard_k4_dot_lights__Dot_r39c18(state, action):
    """k4_dot_lights__Dot_r39c18  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r39c18(state):
    state.Dot_r39c18_color = 1


def _guard_k4_dot_lights__Dot_r39c20(state, action):
    """k4_dot_lights__Dot_r39c20  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r39c20(state):
    state.Dot_r39c20_color = 1


def _guard_k4_dot_lights__Dot_r39c21(state, action):
    """k4_dot_lights__Dot_r39c21  [ev: t4,t17  cov: 8/8]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_dot_lights__Dot_r39c21(state):
    state.Dot_r39c21_color = 1


def _guard_k4_core_lights__BarCore_r32c13(state, action):
    """k4_core_lights__BarCore_r32c13  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 2


def _guard_k4_core_lights__BarCore_r32c14(state, action):
    """k4_core_lights__BarCore_r32c14  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 2


def _guard_k4_core_lights__BarCore_r33c13(state, action):
    """k4_core_lights__BarCore_r33c13  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 2


def _guard_k4_core_lights__BarCore_r33c14(state, action):
    """k4_core_lights__BarCore_r33c14  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 2


def _guard_k4_core_lights__BarCore_r38c17(state, action):
    """k4_core_lights__BarCore_r38c17  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 2


def _guard_k4_core_lights__BarCore_r38c20(state, action):
    """k4_core_lights__BarCore_r38c20  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 2


def _guard_k4_core_lights__BarCore_r39c16(state, action):
    """k4_core_lights__BarCore_r39c16  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 2


def _guard_k4_core_lights__BarCore_r39c19(state, action):
    """k4_core_lights__BarCore_r39c19  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 2


def _guard_k4_core_lights__BarCore_r39c22(state, action):
    """k4_core_lights__BarCore_r39c22  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 2


def _guard_k4_core_lights__BarCore_r53c59(state, action):
    """k4_core_lights__BarCore_r53c59  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 2


def _guard_k4_core_lights__BarCore_r53c60(state, action):
    """k4_core_lights__BarCore_r53c60  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 2


def _guard_k4_core_lights__BarCore_r53c61(state, action):
    """k4_core_lights__BarCore_r53c61  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 2


def _guard_k4_core_lights__BarCore_r53c62(state, action):
    """k4_core_lights__BarCore_r53c62  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 2


def _guard_k4_core_lights__BarCore_r53c63(state, action):
    """k4_core_lights__BarCore_r53c63  [ev: t4,t17  cov: 4/4]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 4): return False
    if not (_cell_colour(state, LANDMARKS['bottom_port']) == 1): return False
    return True


def _effect_k4_core_lights__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 2


def _guard_meter_first_tick_replay_patch__BarCore_r32c13(state, action):
    """meter_first_tick_replay_patch__BarCore_r32c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r32c13_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r32c14(state, action):
    """meter_first_tick_replay_patch__BarCore_r32c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r32c14_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r33c13(state, action):
    """meter_first_tick_replay_patch__BarCore_r33c13  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r33c13_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r33c14(state, action):
    """meter_first_tick_replay_patch__BarCore_r33c14  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r33c14_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r38c17(state, action):
    """meter_first_tick_replay_patch__BarCore_r38c17  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r38c17_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r38c20(state, action):
    """meter_first_tick_replay_patch__BarCore_r38c20  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r38c20_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r39c16(state, action):
    """meter_first_tick_replay_patch__BarCore_r39c16  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r39c16_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r39c19(state, action):
    """meter_first_tick_replay_patch__BarCore_r39c19  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r39c19_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r39c22(state, action):
    """meter_first_tick_replay_patch__BarCore_r39c22  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r39c22_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r53c59(state, action):
    """meter_first_tick_replay_patch__BarCore_r53c59  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r53c59_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r53c60(state, action):
    """meter_first_tick_replay_patch__BarCore_r53c60  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r53c60_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r53c61(state, action):
    """meter_first_tick_replay_patch__BarCore_r53c61  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r53c61_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r53c62(state, action):
    """meter_first_tick_replay_patch__BarCore_r53c62  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r53c62_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 3


def _guard_meter_first_tick_replay_patch__BarCore_r53c63(state, action):
    """meter_first_tick_replay_patch__BarCore_r53c63  [ev: t4  cov: 1/1]"""
    if action != ('key', 4): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (not _in_bounds(_neighbour(state.BarCore_r53c63_pos, 'right'))): return False
    return True


def _effect_meter_first_tick_replay_patch__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 3


def _guard_k7_dot_blanks__Dot_r38c16(state, action):
    """k7_dot_blanks__Dot_r38c16  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r38c16_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r38c16(state):
    state.Dot_r38c16_color = 4


def _guard_k7_dot_blanks__Dot_r38c18(state, action):
    """k7_dot_blanks__Dot_r38c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r38c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r38c18(state):
    state.Dot_r38c18_color = 4


def _guard_k7_dot_blanks__Dot_r38c19(state, action):
    """k7_dot_blanks__Dot_r38c19  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r38c19_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r38c19(state):
    state.Dot_r38c19_color = 4


def _guard_k7_dot_blanks__Dot_r38c21(state, action):
    """k7_dot_blanks__Dot_r38c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r38c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r38c21(state):
    state.Dot_r38c21_color = 4


def _guard_k7_dot_blanks__Dot_r38c22(state, action):
    """k7_dot_blanks__Dot_r38c22  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r38c22_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r38c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r38c22(state):
    state.Dot_r38c22_color = 4


def _guard_k7_dot_blanks__Dot_r39c17(state, action):
    """k7_dot_blanks__Dot_r39c17  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r39c17_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r39c17(state):
    state.Dot_r39c17_color = 4


def _guard_k7_dot_blanks__Dot_r39c18(state, action):
    """k7_dot_blanks__Dot_r39c18  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r39c18_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r39c18(state):
    state.Dot_r39c18_color = 4


def _guard_k7_dot_blanks__Dot_r39c20(state, action):
    """k7_dot_blanks__Dot_r39c20  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r39c20_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r39c20(state):
    state.Dot_r39c20_color = 4


def _guard_k7_dot_blanks__Dot_r39c21(state, action):
    """k7_dot_blanks__Dot_r39c21  [ev: t5  cov: 8/8]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.Dot_r39c21_pos) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Dot_r39c21_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_dot_blanks__Dot_r39c21(state):
    state.Dot_r39c21_color = 4


def _guard_k7_core_blanks__BarCore_r32c13(state, action):
    """k7_core_blanks__BarCore_r32c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r32c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r32c13(state):
    state.BarCore_r32c13_color = 4


def _guard_k7_core_blanks__BarCore_r32c14(state, action):
    """k7_core_blanks__BarCore_r32c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r32c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r32c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r32c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r32c14(state):
    state.BarCore_r32c14_color = 4


def _guard_k7_core_blanks__BarCore_r33c13(state, action):
    """k7_core_blanks__BarCore_r33c13  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r33c13_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c13_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c13_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r33c13(state):
    state.BarCore_r33c13_color = 4


def _guard_k7_core_blanks__BarCore_r33c14(state, action):
    """k7_core_blanks__BarCore_r33c14  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r33c14_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r33c14_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r33c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r33c14(state):
    state.BarCore_r33c14_color = 4


def _guard_k7_core_blanks__BarCore_r38c17(state, action):
    """k7_core_blanks__BarCore_r38c17  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r38c17_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c17_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r38c17(state):
    state.BarCore_r38c17_color = 4


def _guard_k7_core_blanks__BarCore_r38c20(state, action):
    """k7_core_blanks__BarCore_r38c20  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r38c20_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r38c20_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r38c20_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r38c20(state):
    state.BarCore_r38c20_color = 4


def _guard_k7_core_blanks__BarCore_r39c16(state, action):
    """k7_core_blanks__BarCore_r39c16  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r39c16_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c16_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r39c16(state):
    state.BarCore_r39c16_color = 4


def _guard_k7_core_blanks__BarCore_r39c19(state, action):
    """k7_core_blanks__BarCore_r39c19  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r39c19_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c19_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c19_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r39c19(state):
    state.BarCore_r39c19_color = 4


def _guard_k7_core_blanks__BarCore_r39c22(state, action):
    """k7_core_blanks__BarCore_r39c22  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r39c22_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r39c22_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r39c22_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r39c22(state):
    state.BarCore_r39c22_color = 4


def _guard_k7_core_blanks__BarCore_r53c59(state, action):
    """k7_core_blanks__BarCore_r53c59  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r53c59_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c59_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c59_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r53c59(state):
    state.BarCore_r53c59_color = 4


def _guard_k7_core_blanks__BarCore_r53c60(state, action):
    """k7_core_blanks__BarCore_r53c60  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r53c60_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c60_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c60_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r53c60(state):
    state.BarCore_r53c60_color = 4


def _guard_k7_core_blanks__BarCore_r53c61(state, action):
    """k7_core_blanks__BarCore_r53c61  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r53c61_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c61_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c61_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r53c61(state):
    state.BarCore_r53c61_color = 4


def _guard_k7_core_blanks__BarCore_r53c62(state, action):
    """k7_core_blanks__BarCore_r53c62  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r53c62_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c62_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c62_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r53c62(state):
    state.BarCore_r53c62_color = 4


def _guard_k7_core_blanks__BarCore_r53c63(state, action):
    """k7_core_blanks__BarCore_r53c63  [ev: t5  cov: 4/4]"""
    if action != ('key', 7): return False
    if not (_cell_colour(state, state.BarCore_r53c63_pos) == 2): return False
    if not (_cell_colour(state, _neighbour(state.BarCore_r53c63_pos, 'left')) == 1): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.BarCore_r53c63_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 4): return False
    return True


def _effect_k7_core_blanks__BarCore_r53c63(state):
    state.BarCore_r53c63_color = 4


RULES = [
    ('k1_field_to_frame__Field_r30c11', _guard_k1_field_to_frame__Field_r30c11, _effect_k1_field_to_frame__Field_r30c11, ['Field_r30c11']),
    ('k1_field_to_frame__Field_r30c12', _guard_k1_field_to_frame__Field_r30c12, _effect_k1_field_to_frame__Field_r30c12, ['Field_r30c12']),
    ('k1_field_to_frame__Field_r30c15', _guard_k1_field_to_frame__Field_r30c15, _effect_k1_field_to_frame__Field_r30c15, ['Field_r30c15']),
    ('k1_field_to_frame__Field_r30c16', _guard_k1_field_to_frame__Field_r30c16, _effect_k1_field_to_frame__Field_r30c16, ['Field_r30c16']),
    ('k1_field_to_frame__Field_r31c11', _guard_k1_field_to_frame__Field_r31c11, _effect_k1_field_to_frame__Field_r31c11, ['Field_r31c11']),
    ('k1_field_to_frame__Field_r31c12', _guard_k1_field_to_frame__Field_r31c12, _effect_k1_field_to_frame__Field_r31c12, ['Field_r31c12']),
    ('k1_field_to_frame__Field_r31c15', _guard_k1_field_to_frame__Field_r31c15, _effect_k1_field_to_frame__Field_r31c15, ['Field_r31c15']),
    ('k1_field_to_frame__Field_r31c16', _guard_k1_field_to_frame__Field_r31c16, _effect_k1_field_to_frame__Field_r31c16, ['Field_r31c16']),
    ('k1_field_to_frame__Field_r32c11', _guard_k1_field_to_frame__Field_r32c11, _effect_k1_field_to_frame__Field_r32c11, ['Field_r32c11']),
    ('k1_field_to_frame__Field_r32c12', _guard_k1_field_to_frame__Field_r32c12, _effect_k1_field_to_frame__Field_r32c12, ['Field_r32c12']),
    ('k1_field_to_frame__Field_r32c15', _guard_k1_field_to_frame__Field_r32c15, _effect_k1_field_to_frame__Field_r32c15, ['Field_r32c15']),
    ('k1_field_to_frame__Field_r32c16', _guard_k1_field_to_frame__Field_r32c16, _effect_k1_field_to_frame__Field_r32c16, ['Field_r32c16']),
    ('k1_field_to_frame__Field_r33c11', _guard_k1_field_to_frame__Field_r33c11, _effect_k1_field_to_frame__Field_r33c11, ['Field_r33c11']),
    ('k1_field_to_frame__Field_r33c12', _guard_k1_field_to_frame__Field_r33c12, _effect_k1_field_to_frame__Field_r33c12, ['Field_r33c12']),
    ('k1_field_to_frame__Field_r33c15', _guard_k1_field_to_frame__Field_r33c15, _effect_k1_field_to_frame__Field_r33c15, ['Field_r33c15']),
    ('k1_field_to_frame__Field_r33c16', _guard_k1_field_to_frame__Field_r33c16, _effect_k1_field_to_frame__Field_r33c16, ['Field_r33c16']),
    ('k1_field_to_frame__Field_r34c11', _guard_k1_field_to_frame__Field_r34c11, _effect_k1_field_to_frame__Field_r34c11, ['Field_r34c11']),
    ('k1_field_to_frame__Field_r34c12', _guard_k1_field_to_frame__Field_r34c12, _effect_k1_field_to_frame__Field_r34c12, ['Field_r34c12']),
    ('k1_field_to_frame__Field_r34c15', _guard_k1_field_to_frame__Field_r34c15, _effect_k1_field_to_frame__Field_r34c15, ['Field_r34c15']),
    ('k1_field_to_frame__Field_r34c16', _guard_k1_field_to_frame__Field_r34c16, _effect_k1_field_to_frame__Field_r34c16, ['Field_r34c16']),
    ('k1_field_to_frame__Field_r35c11', _guard_k1_field_to_frame__Field_r35c11, _effect_k1_field_to_frame__Field_r35c11, ['Field_r35c11']),
    ('k1_field_to_frame__Field_r35c12', _guard_k1_field_to_frame__Field_r35c12, _effect_k1_field_to_frame__Field_r35c12, ['Field_r35c12']),
    ('k1_field_to_frame__Field_r35c15', _guard_k1_field_to_frame__Field_r35c15, _effect_k1_field_to_frame__Field_r35c15, ['Field_r35c15']),
    ('k1_field_to_frame__Field_r35c16', _guard_k1_field_to_frame__Field_r35c16, _effect_k1_field_to_frame__Field_r35c16, ['Field_r35c16']),
    ('k1_field_to_hollow__Field_r30c11', _guard_k1_field_to_hollow__Field_r30c11, _effect_k1_field_to_hollow__Field_r30c11, ['Field_r30c11']),
    ('k1_field_to_hollow__Field_r30c12', _guard_k1_field_to_hollow__Field_r30c12, _effect_k1_field_to_hollow__Field_r30c12, ['Field_r30c12']),
    ('k1_field_to_hollow__Field_r30c15', _guard_k1_field_to_hollow__Field_r30c15, _effect_k1_field_to_hollow__Field_r30c15, ['Field_r30c15']),
    ('k1_field_to_hollow__Field_r30c16', _guard_k1_field_to_hollow__Field_r30c16, _effect_k1_field_to_hollow__Field_r30c16, ['Field_r30c16']),
    ('k1_field_to_hollow__Field_r31c11', _guard_k1_field_to_hollow__Field_r31c11, _effect_k1_field_to_hollow__Field_r31c11, ['Field_r31c11']),
    ('k1_field_to_hollow__Field_r31c12', _guard_k1_field_to_hollow__Field_r31c12, _effect_k1_field_to_hollow__Field_r31c12, ['Field_r31c12']),
    ('k1_field_to_hollow__Field_r31c15', _guard_k1_field_to_hollow__Field_r31c15, _effect_k1_field_to_hollow__Field_r31c15, ['Field_r31c15']),
    ('k1_field_to_hollow__Field_r31c16', _guard_k1_field_to_hollow__Field_r31c16, _effect_k1_field_to_hollow__Field_r31c16, ['Field_r31c16']),
    ('k1_field_to_hollow__Field_r32c11', _guard_k1_field_to_hollow__Field_r32c11, _effect_k1_field_to_hollow__Field_r32c11, ['Field_r32c11']),
    ('k1_field_to_hollow__Field_r32c12', _guard_k1_field_to_hollow__Field_r32c12, _effect_k1_field_to_hollow__Field_r32c12, ['Field_r32c12']),
    ('k1_field_to_hollow__Field_r32c15', _guard_k1_field_to_hollow__Field_r32c15, _effect_k1_field_to_hollow__Field_r32c15, ['Field_r32c15']),
    ('k1_field_to_hollow__Field_r32c16', _guard_k1_field_to_hollow__Field_r32c16, _effect_k1_field_to_hollow__Field_r32c16, ['Field_r32c16']),
    ('k1_field_to_hollow__Field_r33c11', _guard_k1_field_to_hollow__Field_r33c11, _effect_k1_field_to_hollow__Field_r33c11, ['Field_r33c11']),
    ('k1_field_to_hollow__Field_r33c12', _guard_k1_field_to_hollow__Field_r33c12, _effect_k1_field_to_hollow__Field_r33c12, ['Field_r33c12']),
    ('k1_field_to_hollow__Field_r33c15', _guard_k1_field_to_hollow__Field_r33c15, _effect_k1_field_to_hollow__Field_r33c15, ['Field_r33c15']),
    ('k1_field_to_hollow__Field_r33c16', _guard_k1_field_to_hollow__Field_r33c16, _effect_k1_field_to_hollow__Field_r33c16, ['Field_r33c16']),
    ('k1_field_to_hollow__Field_r34c11', _guard_k1_field_to_hollow__Field_r34c11, _effect_k1_field_to_hollow__Field_r34c11, ['Field_r34c11']),
    ('k1_field_to_hollow__Field_r34c12', _guard_k1_field_to_hollow__Field_r34c12, _effect_k1_field_to_hollow__Field_r34c12, ['Field_r34c12']),
    ('k1_field_to_hollow__Field_r34c15', _guard_k1_field_to_hollow__Field_r34c15, _effect_k1_field_to_hollow__Field_r34c15, ['Field_r34c15']),
    ('k1_field_to_hollow__Field_r34c16', _guard_k1_field_to_hollow__Field_r34c16, _effect_k1_field_to_hollow__Field_r34c16, ['Field_r34c16']),
    ('k1_field_to_hollow__Field_r35c11', _guard_k1_field_to_hollow__Field_r35c11, _effect_k1_field_to_hollow__Field_r35c11, ['Field_r35c11']),
    ('k1_field_to_hollow__Field_r35c12', _guard_k1_field_to_hollow__Field_r35c12, _effect_k1_field_to_hollow__Field_r35c12, ['Field_r35c12']),
    ('k1_field_to_hollow__Field_r35c15', _guard_k1_field_to_hollow__Field_r35c15, _effect_k1_field_to_hollow__Field_r35c15, ['Field_r35c15']),
    ('k1_field_to_hollow__Field_r35c16', _guard_k1_field_to_hollow__Field_r35c16, _effect_k1_field_to_hollow__Field_r35c16, ['Field_r35c16']),
    ('k1_field_to_dot__Field_r30c11', _guard_k1_field_to_dot__Field_r30c11, _effect_k1_field_to_dot__Field_r30c11, ['Field_r30c11']),
    ('k1_field_to_dot__Field_r30c12', _guard_k1_field_to_dot__Field_r30c12, _effect_k1_field_to_dot__Field_r30c12, ['Field_r30c12']),
    ('k1_field_to_dot__Field_r30c15', _guard_k1_field_to_dot__Field_r30c15, _effect_k1_field_to_dot__Field_r30c15, ['Field_r30c15']),
    ('k1_field_to_dot__Field_r30c16', _guard_k1_field_to_dot__Field_r30c16, _effect_k1_field_to_dot__Field_r30c16, ['Field_r30c16']),
    ('k1_field_to_dot__Field_r31c11', _guard_k1_field_to_dot__Field_r31c11, _effect_k1_field_to_dot__Field_r31c11, ['Field_r31c11']),
    ('k1_field_to_dot__Field_r31c12', _guard_k1_field_to_dot__Field_r31c12, _effect_k1_field_to_dot__Field_r31c12, ['Field_r31c12']),
    ('k1_field_to_dot__Field_r31c15', _guard_k1_field_to_dot__Field_r31c15, _effect_k1_field_to_dot__Field_r31c15, ['Field_r31c15']),
    ('k1_field_to_dot__Field_r31c16', _guard_k1_field_to_dot__Field_r31c16, _effect_k1_field_to_dot__Field_r31c16, ['Field_r31c16']),
    ('k1_field_to_dot__Field_r32c11', _guard_k1_field_to_dot__Field_r32c11, _effect_k1_field_to_dot__Field_r32c11, ['Field_r32c11']),
    ('k1_field_to_dot__Field_r32c12', _guard_k1_field_to_dot__Field_r32c12, _effect_k1_field_to_dot__Field_r32c12, ['Field_r32c12']),
    ('k1_field_to_dot__Field_r32c15', _guard_k1_field_to_dot__Field_r32c15, _effect_k1_field_to_dot__Field_r32c15, ['Field_r32c15']),
    ('k1_field_to_dot__Field_r32c16', _guard_k1_field_to_dot__Field_r32c16, _effect_k1_field_to_dot__Field_r32c16, ['Field_r32c16']),
    ('k1_field_to_dot__Field_r33c11', _guard_k1_field_to_dot__Field_r33c11, _effect_k1_field_to_dot__Field_r33c11, ['Field_r33c11']),
    ('k1_field_to_dot__Field_r33c12', _guard_k1_field_to_dot__Field_r33c12, _effect_k1_field_to_dot__Field_r33c12, ['Field_r33c12']),
    ('k1_field_to_dot__Field_r33c15', _guard_k1_field_to_dot__Field_r33c15, _effect_k1_field_to_dot__Field_r33c15, ['Field_r33c15']),
    ('k1_field_to_dot__Field_r33c16', _guard_k1_field_to_dot__Field_r33c16, _effect_k1_field_to_dot__Field_r33c16, ['Field_r33c16']),
    ('k1_field_to_dot__Field_r34c11', _guard_k1_field_to_dot__Field_r34c11, _effect_k1_field_to_dot__Field_r34c11, ['Field_r34c11']),
    ('k1_field_to_dot__Field_r34c12', _guard_k1_field_to_dot__Field_r34c12, _effect_k1_field_to_dot__Field_r34c12, ['Field_r34c12']),
    ('k1_field_to_dot__Field_r34c15', _guard_k1_field_to_dot__Field_r34c15, _effect_k1_field_to_dot__Field_r34c15, ['Field_r34c15']),
    ('k1_field_to_dot__Field_r34c16', _guard_k1_field_to_dot__Field_r34c16, _effect_k1_field_to_dot__Field_r34c16, ['Field_r34c16']),
    ('k1_field_to_dot__Field_r35c11', _guard_k1_field_to_dot__Field_r35c11, _effect_k1_field_to_dot__Field_r35c11, ['Field_r35c11']),
    ('k1_field_to_dot__Field_r35c12', _guard_k1_field_to_dot__Field_r35c12, _effect_k1_field_to_dot__Field_r35c12, ['Field_r35c12']),
    ('k1_field_to_dot__Field_r35c15', _guard_k1_field_to_dot__Field_r35c15, _effect_k1_field_to_dot__Field_r35c15, ['Field_r35c15']),
    ('k1_field_to_dot__Field_r35c16', _guard_k1_field_to_dot__Field_r35c16, _effect_k1_field_to_dot__Field_r35c16, ['Field_r35c16']),
    ('k1_field_to_core__Field_r30c11', _guard_k1_field_to_core__Field_r30c11, _effect_k1_field_to_core__Field_r30c11, ['Field_r30c11']),
    ('k1_field_to_core__Field_r30c12', _guard_k1_field_to_core__Field_r30c12, _effect_k1_field_to_core__Field_r30c12, ['Field_r30c12']),
    ('k1_field_to_core__Field_r30c15', _guard_k1_field_to_core__Field_r30c15, _effect_k1_field_to_core__Field_r30c15, ['Field_r30c15']),
    ('k1_field_to_core__Field_r30c16', _guard_k1_field_to_core__Field_r30c16, _effect_k1_field_to_core__Field_r30c16, ['Field_r30c16']),
    ('k1_field_to_core__Field_r31c11', _guard_k1_field_to_core__Field_r31c11, _effect_k1_field_to_core__Field_r31c11, ['Field_r31c11']),
    ('k1_field_to_core__Field_r31c12', _guard_k1_field_to_core__Field_r31c12, _effect_k1_field_to_core__Field_r31c12, ['Field_r31c12']),
    ('k1_field_to_core__Field_r31c15', _guard_k1_field_to_core__Field_r31c15, _effect_k1_field_to_core__Field_r31c15, ['Field_r31c15']),
    ('k1_field_to_core__Field_r31c16', _guard_k1_field_to_core__Field_r31c16, _effect_k1_field_to_core__Field_r31c16, ['Field_r31c16']),
    ('k1_field_to_core__Field_r32c11', _guard_k1_field_to_core__Field_r32c11, _effect_k1_field_to_core__Field_r32c11, ['Field_r32c11']),
    ('k1_field_to_core__Field_r32c12', _guard_k1_field_to_core__Field_r32c12, _effect_k1_field_to_core__Field_r32c12, ['Field_r32c12']),
    ('k1_field_to_core__Field_r32c15', _guard_k1_field_to_core__Field_r32c15, _effect_k1_field_to_core__Field_r32c15, ['Field_r32c15']),
    ('k1_field_to_core__Field_r32c16', _guard_k1_field_to_core__Field_r32c16, _effect_k1_field_to_core__Field_r32c16, ['Field_r32c16']),
    ('k1_field_to_core__Field_r33c11', _guard_k1_field_to_core__Field_r33c11, _effect_k1_field_to_core__Field_r33c11, ['Field_r33c11']),
    ('k1_field_to_core__Field_r33c12', _guard_k1_field_to_core__Field_r33c12, _effect_k1_field_to_core__Field_r33c12, ['Field_r33c12']),
    ('k1_field_to_core__Field_r33c15', _guard_k1_field_to_core__Field_r33c15, _effect_k1_field_to_core__Field_r33c15, ['Field_r33c15']),
    ('k1_field_to_core__Field_r33c16', _guard_k1_field_to_core__Field_r33c16, _effect_k1_field_to_core__Field_r33c16, ['Field_r33c16']),
    ('k1_field_to_core__Field_r34c11', _guard_k1_field_to_core__Field_r34c11, _effect_k1_field_to_core__Field_r34c11, ['Field_r34c11']),
    ('k1_field_to_core__Field_r34c12', _guard_k1_field_to_core__Field_r34c12, _effect_k1_field_to_core__Field_r34c12, ['Field_r34c12']),
    ('k1_field_to_core__Field_r34c15', _guard_k1_field_to_core__Field_r34c15, _effect_k1_field_to_core__Field_r34c15, ['Field_r34c15']),
    ('k1_field_to_core__Field_r34c16', _guard_k1_field_to_core__Field_r34c16, _effect_k1_field_to_core__Field_r34c16, ['Field_r34c16']),
    ('k1_field_to_core__Field_r35c11', _guard_k1_field_to_core__Field_r35c11, _effect_k1_field_to_core__Field_r35c11, ['Field_r35c11']),
    ('k1_field_to_core__Field_r35c12', _guard_k1_field_to_core__Field_r35c12, _effect_k1_field_to_core__Field_r35c12, ['Field_r35c12']),
    ('k1_field_to_core__Field_r35c15', _guard_k1_field_to_core__Field_r35c15, _effect_k1_field_to_core__Field_r35c15, ['Field_r35c15']),
    ('k1_field_to_core__Field_r35c16', _guard_k1_field_to_core__Field_r35c16, _effect_k1_field_to_core__Field_r35c16, ['Field_r35c16']),
    ('k1_bar_to_frame__BarBody_r30c13', _guard_k1_bar_to_frame__BarBody_r30c13, _effect_k1_bar_to_frame__BarBody_r30c13, ['BarBody_r30c13']),
    ('k1_bar_to_frame__BarBody_r30c14', _guard_k1_bar_to_frame__BarBody_r30c14, _effect_k1_bar_to_frame__BarBody_r30c14, ['BarBody_r30c14']),
    ('k1_bar_to_frame__BarBody_r31c13', _guard_k1_bar_to_frame__BarBody_r31c13, _effect_k1_bar_to_frame__BarBody_r31c13, ['BarBody_r31c13']),
    ('k1_bar_to_frame__BarBody_r31c14', _guard_k1_bar_to_frame__BarBody_r31c14, _effect_k1_bar_to_frame__BarBody_r31c14, ['BarBody_r31c14']),
    ('k1_bar_to_frame__BarBody_r34c13', _guard_k1_bar_to_frame__BarBody_r34c13, _effect_k1_bar_to_frame__BarBody_r34c13, ['BarBody_r34c13']),
    ('k1_bar_to_frame__BarBody_r34c14', _guard_k1_bar_to_frame__BarBody_r34c14, _effect_k1_bar_to_frame__BarBody_r34c14, ['BarBody_r34c14']),
    ('k1_bar_to_frame__BarBody_r35c13', _guard_k1_bar_to_frame__BarBody_r35c13, _effect_k1_bar_to_frame__BarBody_r35c13, ['BarBody_r35c13']),
    ('k1_bar_to_frame__BarBody_r35c14', _guard_k1_bar_to_frame__BarBody_r35c14, _effect_k1_bar_to_frame__BarBody_r35c14, ['BarBody_r35c14']),
    ('k1_bar_to_hollow__BarBody_r30c13', _guard_k1_bar_to_hollow__BarBody_r30c13, _effect_k1_bar_to_hollow__BarBody_r30c13, ['BarBody_r30c13']),
    ('k1_bar_to_hollow__BarBody_r30c14', _guard_k1_bar_to_hollow__BarBody_r30c14, _effect_k1_bar_to_hollow__BarBody_r30c14, ['BarBody_r30c14']),
    ('k1_bar_to_hollow__BarBody_r31c13', _guard_k1_bar_to_hollow__BarBody_r31c13, _effect_k1_bar_to_hollow__BarBody_r31c13, ['BarBody_r31c13']),
    ('k1_bar_to_hollow__BarBody_r31c14', _guard_k1_bar_to_hollow__BarBody_r31c14, _effect_k1_bar_to_hollow__BarBody_r31c14, ['BarBody_r31c14']),
    ('k1_bar_to_hollow__BarBody_r34c13', _guard_k1_bar_to_hollow__BarBody_r34c13, _effect_k1_bar_to_hollow__BarBody_r34c13, ['BarBody_r34c13']),
    ('k1_bar_to_hollow__BarBody_r34c14', _guard_k1_bar_to_hollow__BarBody_r34c14, _effect_k1_bar_to_hollow__BarBody_r34c14, ['BarBody_r34c14']),
    ('k1_bar_to_hollow__BarBody_r35c13', _guard_k1_bar_to_hollow__BarBody_r35c13, _effect_k1_bar_to_hollow__BarBody_r35c13, ['BarBody_r35c13']),
    ('k1_bar_to_hollow__BarBody_r35c14', _guard_k1_bar_to_hollow__BarBody_r35c14, _effect_k1_bar_to_hollow__BarBody_r35c14, ['BarBody_r35c14']),
    ('k1_core_to_frame__BarCore_r32c13', _guard_k1_core_to_frame__BarCore_r32c13, _effect_k1_core_to_frame__BarCore_r32c13, ['BarCore_r32c13']),
    ('k1_core_to_frame__BarCore_r32c14', _guard_k1_core_to_frame__BarCore_r32c14, _effect_k1_core_to_frame__BarCore_r32c14, ['BarCore_r32c14']),
    ('k1_core_to_frame__BarCore_r33c13', _guard_k1_core_to_frame__BarCore_r33c13, _effect_k1_core_to_frame__BarCore_r33c13, ['BarCore_r33c13']),
    ('k1_core_to_frame__BarCore_r33c14', _guard_k1_core_to_frame__BarCore_r33c14, _effect_k1_core_to_frame__BarCore_r33c14, ['BarCore_r33c14']),
    ('k1_core_to_frame__BarCore_r38c17', _guard_k1_core_to_frame__BarCore_r38c17, _effect_k1_core_to_frame__BarCore_r38c17, ['BarCore_r38c17']),
    ('k1_core_to_frame__BarCore_r38c20', _guard_k1_core_to_frame__BarCore_r38c20, _effect_k1_core_to_frame__BarCore_r38c20, ['BarCore_r38c20']),
    ('k1_core_to_frame__BarCore_r39c16', _guard_k1_core_to_frame__BarCore_r39c16, _effect_k1_core_to_frame__BarCore_r39c16, ['BarCore_r39c16']),
    ('k1_core_to_frame__BarCore_r39c19', _guard_k1_core_to_frame__BarCore_r39c19, _effect_k1_core_to_frame__BarCore_r39c19, ['BarCore_r39c19']),
    ('k1_core_to_frame__BarCore_r39c22', _guard_k1_core_to_frame__BarCore_r39c22, _effect_k1_core_to_frame__BarCore_r39c22, ['BarCore_r39c22']),
    ('k1_core_to_frame__BarCore_r53c59', _guard_k1_core_to_frame__BarCore_r53c59, _effect_k1_core_to_frame__BarCore_r53c59, ['BarCore_r53c59']),
    ('k1_core_to_frame__BarCore_r53c60', _guard_k1_core_to_frame__BarCore_r53c60, _effect_k1_core_to_frame__BarCore_r53c60, ['BarCore_r53c60']),
    ('k1_core_to_frame__BarCore_r53c61', _guard_k1_core_to_frame__BarCore_r53c61, _effect_k1_core_to_frame__BarCore_r53c61, ['BarCore_r53c61']),
    ('k1_core_to_frame__BarCore_r53c62', _guard_k1_core_to_frame__BarCore_r53c62, _effect_k1_core_to_frame__BarCore_r53c62, ['BarCore_r53c62']),
    ('k1_core_to_frame__BarCore_r53c63', _guard_k1_core_to_frame__BarCore_r53c63, _effect_k1_core_to_frame__BarCore_r53c63, ['BarCore_r53c63']),
    ('k1_blank_to_dot__Blank_r32c17', _guard_k1_blank_to_dot__Blank_r32c17, _effect_k1_blank_to_dot__Blank_r32c17, ['Blank_r32c17']),
    ('k1_blank_to_dot__Blank_r32c18', _guard_k1_blank_to_dot__Blank_r32c18, _effect_k1_blank_to_dot__Blank_r32c18, ['Blank_r32c18']),
    ('k1_blank_to_dot__Blank_r32c19', _guard_k1_blank_to_dot__Blank_r32c19, _effect_k1_blank_to_dot__Blank_r32c19, ['Blank_r32c19']),
    ('k1_blank_to_dot__Blank_r32c20', _guard_k1_blank_to_dot__Blank_r32c20, _effect_k1_blank_to_dot__Blank_r32c20, ['Blank_r32c20']),
    ('k1_blank_to_dot__Blank_r32c21', _guard_k1_blank_to_dot__Blank_r32c21, _effect_k1_blank_to_dot__Blank_r32c21, ['Blank_r32c21']),
    ('k1_blank_to_dot__Blank_r32c22', _guard_k1_blank_to_dot__Blank_r32c22, _effect_k1_blank_to_dot__Blank_r32c22, ['Blank_r32c22']),
    ('k1_blank_to_dot__Blank_r33c17', _guard_k1_blank_to_dot__Blank_r33c17, _effect_k1_blank_to_dot__Blank_r33c17, ['Blank_r33c17']),
    ('k1_blank_to_dot__Blank_r33c18', _guard_k1_blank_to_dot__Blank_r33c18, _effect_k1_blank_to_dot__Blank_r33c18, ['Blank_r33c18']),
    ('k1_blank_to_dot__Blank_r33c19', _guard_k1_blank_to_dot__Blank_r33c19, _effect_k1_blank_to_dot__Blank_r33c19, ['Blank_r33c19']),
    ('k1_blank_to_dot__Blank_r33c20', _guard_k1_blank_to_dot__Blank_r33c20, _effect_k1_blank_to_dot__Blank_r33c20, ['Blank_r33c20']),
    ('k1_blank_to_dot__Blank_r33c21', _guard_k1_blank_to_dot__Blank_r33c21, _effect_k1_blank_to_dot__Blank_r33c21, ['Blank_r33c21']),
    ('k1_blank_to_dot__Blank_r33c22', _guard_k1_blank_to_dot__Blank_r33c22, _effect_k1_blank_to_dot__Blank_r33c22, ['Blank_r33c22']),
    ('k1_blank_to_core__Blank_r32c17', _guard_k1_blank_to_core__Blank_r32c17, _effect_k1_blank_to_core__Blank_r32c17, ['Blank_r32c17']),
    ('k1_blank_to_core__Blank_r32c18', _guard_k1_blank_to_core__Blank_r32c18, _effect_k1_blank_to_core__Blank_r32c18, ['Blank_r32c18']),
    ('k1_blank_to_core__Blank_r32c19', _guard_k1_blank_to_core__Blank_r32c19, _effect_k1_blank_to_core__Blank_r32c19, ['Blank_r32c19']),
    ('k1_blank_to_core__Blank_r32c20', _guard_k1_blank_to_core__Blank_r32c20, _effect_k1_blank_to_core__Blank_r32c20, ['Blank_r32c20']),
    ('k1_blank_to_core__Blank_r32c21', _guard_k1_blank_to_core__Blank_r32c21, _effect_k1_blank_to_core__Blank_r32c21, ['Blank_r32c21']),
    ('k1_blank_to_core__Blank_r32c22', _guard_k1_blank_to_core__Blank_r32c22, _effect_k1_blank_to_core__Blank_r32c22, ['Blank_r32c22']),
    ('k1_blank_to_core__Blank_r33c17', _guard_k1_blank_to_core__Blank_r33c17, _effect_k1_blank_to_core__Blank_r33c17, ['Blank_r33c17']),
    ('k1_blank_to_core__Blank_r33c18', _guard_k1_blank_to_core__Blank_r33c18, _effect_k1_blank_to_core__Blank_r33c18, ['Blank_r33c18']),
    ('k1_blank_to_core__Blank_r33c19', _guard_k1_blank_to_core__Blank_r33c19, _effect_k1_blank_to_core__Blank_r33c19, ['Blank_r33c19']),
    ('k1_blank_to_core__Blank_r33c20', _guard_k1_blank_to_core__Blank_r33c20, _effect_k1_blank_to_core__Blank_r33c20, ['Blank_r33c20']),
    ('k1_blank_to_core__Blank_r33c21', _guard_k1_blank_to_core__Blank_r33c21, _effect_k1_blank_to_core__Blank_r33c21, ['Blank_r33c21']),
    ('k1_blank_to_core__Blank_r33c22', _guard_k1_blank_to_core__Blank_r33c22, _effect_k1_blank_to_core__Blank_r33c22, ['Blank_r33c22']),
    ('k1_frame_to_field__Frame_r36c11', _guard_k1_frame_to_field__Frame_r36c11, _effect_k1_frame_to_field__Frame_r36c11, ['Frame_r36c11']),
    ('k1_frame_to_field__Frame_r36c12', _guard_k1_frame_to_field__Frame_r36c12, _effect_k1_frame_to_field__Frame_r36c12, ['Frame_r36c12']),
    ('k1_frame_to_field__Frame_r36c13', _guard_k1_frame_to_field__Frame_r36c13, _effect_k1_frame_to_field__Frame_r36c13, ['Frame_r36c13']),
    ('k1_frame_to_field__Frame_r36c14', _guard_k1_frame_to_field__Frame_r36c14, _effect_k1_frame_to_field__Frame_r36c14, ['Frame_r36c14']),
    ('k1_frame_to_field__Frame_r36c15', _guard_k1_frame_to_field__Frame_r36c15, _effect_k1_frame_to_field__Frame_r36c15, ['Frame_r36c15']),
    ('k1_frame_to_field__Frame_r36c16', _guard_k1_frame_to_field__Frame_r36c16, _effect_k1_frame_to_field__Frame_r36c16, ['Frame_r36c16']),
    ('k1_frame_to_field__Frame_r37c11', _guard_k1_frame_to_field__Frame_r37c11, _effect_k1_frame_to_field__Frame_r37c11, ['Frame_r37c11']),
    ('k1_frame_to_field__Frame_r37c16', _guard_k1_frame_to_field__Frame_r37c16, _effect_k1_frame_to_field__Frame_r37c16, ['Frame_r37c16']),
    ('k1_frame_to_field__Frame_r38c11', _guard_k1_frame_to_field__Frame_r38c11, _effect_k1_frame_to_field__Frame_r38c11, ['Frame_r38c11']),
    ('k1_frame_to_field__Frame_r38c13', _guard_k1_frame_to_field__Frame_r38c13, _effect_k1_frame_to_field__Frame_r38c13, ['Frame_r38c13']),
    ('k1_frame_to_field__Frame_r38c14', _guard_k1_frame_to_field__Frame_r38c14, _effect_k1_frame_to_field__Frame_r38c14, ['Frame_r38c14']),
    ('k1_frame_to_field__Frame_r39c11', _guard_k1_frame_to_field__Frame_r39c11, _effect_k1_frame_to_field__Frame_r39c11, ['Frame_r39c11']),
    ('k1_frame_to_field__Frame_r39c13', _guard_k1_frame_to_field__Frame_r39c13, _effect_k1_frame_to_field__Frame_r39c13, ['Frame_r39c13']),
    ('k1_frame_to_field__Frame_r39c14', _guard_k1_frame_to_field__Frame_r39c14, _effect_k1_frame_to_field__Frame_r39c14, ['Frame_r39c14']),
    ('k1_frame_to_field__Frame_r40c11', _guard_k1_frame_to_field__Frame_r40c11, _effect_k1_frame_to_field__Frame_r40c11, ['Frame_r40c11']),
    ('k1_frame_to_field__Frame_r40c16', _guard_k1_frame_to_field__Frame_r40c16, _effect_k1_frame_to_field__Frame_r40c16, ['Frame_r40c16']),
    ('k1_frame_to_field__Frame_r41c11', _guard_k1_frame_to_field__Frame_r41c11, _effect_k1_frame_to_field__Frame_r41c11, ['Frame_r41c11']),
    ('k1_frame_to_field__Frame_r41c12', _guard_k1_frame_to_field__Frame_r41c12, _effect_k1_frame_to_field__Frame_r41c12, ['Frame_r41c12']),
    ('k1_frame_to_field__Frame_r41c13', _guard_k1_frame_to_field__Frame_r41c13, _effect_k1_frame_to_field__Frame_r41c13, ['Frame_r41c13']),
    ('k1_frame_to_field__Frame_r41c14', _guard_k1_frame_to_field__Frame_r41c14, _effect_k1_frame_to_field__Frame_r41c14, ['Frame_r41c14']),
    ('k1_frame_to_field__Frame_r41c15', _guard_k1_frame_to_field__Frame_r41c15, _effect_k1_frame_to_field__Frame_r41c15, ['Frame_r41c15']),
    ('k1_frame_to_field__Frame_r41c16', _guard_k1_frame_to_field__Frame_r41c16, _effect_k1_frame_to_field__Frame_r41c16, ['Frame_r41c16']),
    ('k1_frame_to_bar__Frame_r36c11', _guard_k1_frame_to_bar__Frame_r36c11, _effect_k1_frame_to_bar__Frame_r36c11, ['Frame_r36c11']),
    ('k1_frame_to_bar__Frame_r36c12', _guard_k1_frame_to_bar__Frame_r36c12, _effect_k1_frame_to_bar__Frame_r36c12, ['Frame_r36c12']),
    ('k1_frame_to_bar__Frame_r36c13', _guard_k1_frame_to_bar__Frame_r36c13, _effect_k1_frame_to_bar__Frame_r36c13, ['Frame_r36c13']),
    ('k1_frame_to_bar__Frame_r36c14', _guard_k1_frame_to_bar__Frame_r36c14, _effect_k1_frame_to_bar__Frame_r36c14, ['Frame_r36c14']),
    ('k1_frame_to_bar__Frame_r36c15', _guard_k1_frame_to_bar__Frame_r36c15, _effect_k1_frame_to_bar__Frame_r36c15, ['Frame_r36c15']),
    ('k1_frame_to_bar__Frame_r36c16', _guard_k1_frame_to_bar__Frame_r36c16, _effect_k1_frame_to_bar__Frame_r36c16, ['Frame_r36c16']),
    ('k1_frame_to_bar__Frame_r37c11', _guard_k1_frame_to_bar__Frame_r37c11, _effect_k1_frame_to_bar__Frame_r37c11, ['Frame_r37c11']),
    ('k1_frame_to_bar__Frame_r37c16', _guard_k1_frame_to_bar__Frame_r37c16, _effect_k1_frame_to_bar__Frame_r37c16, ['Frame_r37c16']),
    ('k1_frame_to_bar__Frame_r38c11', _guard_k1_frame_to_bar__Frame_r38c11, _effect_k1_frame_to_bar__Frame_r38c11, ['Frame_r38c11']),
    ('k1_frame_to_bar__Frame_r38c13', _guard_k1_frame_to_bar__Frame_r38c13, _effect_k1_frame_to_bar__Frame_r38c13, ['Frame_r38c13']),
    ('k1_frame_to_bar__Frame_r38c14', _guard_k1_frame_to_bar__Frame_r38c14, _effect_k1_frame_to_bar__Frame_r38c14, ['Frame_r38c14']),
    ('k1_frame_to_bar__Frame_r39c11', _guard_k1_frame_to_bar__Frame_r39c11, _effect_k1_frame_to_bar__Frame_r39c11, ['Frame_r39c11']),
    ('k1_frame_to_bar__Frame_r39c13', _guard_k1_frame_to_bar__Frame_r39c13, _effect_k1_frame_to_bar__Frame_r39c13, ['Frame_r39c13']),
    ('k1_frame_to_bar__Frame_r39c14', _guard_k1_frame_to_bar__Frame_r39c14, _effect_k1_frame_to_bar__Frame_r39c14, ['Frame_r39c14']),
    ('k1_frame_to_bar__Frame_r40c11', _guard_k1_frame_to_bar__Frame_r40c11, _effect_k1_frame_to_bar__Frame_r40c11, ['Frame_r40c11']),
    ('k1_frame_to_bar__Frame_r40c16', _guard_k1_frame_to_bar__Frame_r40c16, _effect_k1_frame_to_bar__Frame_r40c16, ['Frame_r40c16']),
    ('k1_frame_to_bar__Frame_r41c11', _guard_k1_frame_to_bar__Frame_r41c11, _effect_k1_frame_to_bar__Frame_r41c11, ['Frame_r41c11']),
    ('k1_frame_to_bar__Frame_r41c12', _guard_k1_frame_to_bar__Frame_r41c12, _effect_k1_frame_to_bar__Frame_r41c12, ['Frame_r41c12']),
    ('k1_frame_to_bar__Frame_r41c13', _guard_k1_frame_to_bar__Frame_r41c13, _effect_k1_frame_to_bar__Frame_r41c13, ['Frame_r41c13']),
    ('k1_frame_to_bar__Frame_r41c14', _guard_k1_frame_to_bar__Frame_r41c14, _effect_k1_frame_to_bar__Frame_r41c14, ['Frame_r41c14']),
    ('k1_frame_to_bar__Frame_r41c15', _guard_k1_frame_to_bar__Frame_r41c15, _effect_k1_frame_to_bar__Frame_r41c15, ['Frame_r41c15']),
    ('k1_frame_to_bar__Frame_r41c16', _guard_k1_frame_to_bar__Frame_r41c16, _effect_k1_frame_to_bar__Frame_r41c16, ['Frame_r41c16']),
    ('k1_frame_clears__Frame_r36c11', _guard_k1_frame_clears__Frame_r36c11, _effect_k1_frame_clears__Frame_r36c11, ['Frame_r36c11']),
    ('k1_frame_clears__Frame_r36c12', _guard_k1_frame_clears__Frame_r36c12, _effect_k1_frame_clears__Frame_r36c12, ['Frame_r36c12']),
    ('k1_frame_clears__Frame_r36c13', _guard_k1_frame_clears__Frame_r36c13, _effect_k1_frame_clears__Frame_r36c13, ['Frame_r36c13']),
    ('k1_frame_clears__Frame_r36c14', _guard_k1_frame_clears__Frame_r36c14, _effect_k1_frame_clears__Frame_r36c14, ['Frame_r36c14']),
    ('k1_frame_clears__Frame_r36c15', _guard_k1_frame_clears__Frame_r36c15, _effect_k1_frame_clears__Frame_r36c15, ['Frame_r36c15']),
    ('k1_frame_clears__Frame_r36c16', _guard_k1_frame_clears__Frame_r36c16, _effect_k1_frame_clears__Frame_r36c16, ['Frame_r36c16']),
    ('k1_frame_clears__Frame_r37c11', _guard_k1_frame_clears__Frame_r37c11, _effect_k1_frame_clears__Frame_r37c11, ['Frame_r37c11']),
    ('k1_frame_clears__Frame_r37c16', _guard_k1_frame_clears__Frame_r37c16, _effect_k1_frame_clears__Frame_r37c16, ['Frame_r37c16']),
    ('k1_frame_clears__Frame_r38c11', _guard_k1_frame_clears__Frame_r38c11, _effect_k1_frame_clears__Frame_r38c11, ['Frame_r38c11']),
    ('k1_frame_clears__Frame_r38c13', _guard_k1_frame_clears__Frame_r38c13, _effect_k1_frame_clears__Frame_r38c13, ['Frame_r38c13']),
    ('k1_frame_clears__Frame_r38c14', _guard_k1_frame_clears__Frame_r38c14, _effect_k1_frame_clears__Frame_r38c14, ['Frame_r38c14']),
    ('k1_frame_clears__Frame_r39c11', _guard_k1_frame_clears__Frame_r39c11, _effect_k1_frame_clears__Frame_r39c11, ['Frame_r39c11']),
    ('k1_frame_clears__Frame_r39c13', _guard_k1_frame_clears__Frame_r39c13, _effect_k1_frame_clears__Frame_r39c13, ['Frame_r39c13']),
    ('k1_frame_clears__Frame_r39c14', _guard_k1_frame_clears__Frame_r39c14, _effect_k1_frame_clears__Frame_r39c14, ['Frame_r39c14']),
    ('k1_frame_clears__Frame_r40c11', _guard_k1_frame_clears__Frame_r40c11, _effect_k1_frame_clears__Frame_r40c11, ['Frame_r40c11']),
    ('k1_frame_clears__Frame_r40c16', _guard_k1_frame_clears__Frame_r40c16, _effect_k1_frame_clears__Frame_r40c16, ['Frame_r40c16']),
    ('k1_frame_clears__Frame_r41c11', _guard_k1_frame_clears__Frame_r41c11, _effect_k1_frame_clears__Frame_r41c11, ['Frame_r41c11']),
    ('k1_frame_clears__Frame_r41c12', _guard_k1_frame_clears__Frame_r41c12, _effect_k1_frame_clears__Frame_r41c12, ['Frame_r41c12']),
    ('k1_frame_clears__Frame_r41c13', _guard_k1_frame_clears__Frame_r41c13, _effect_k1_frame_clears__Frame_r41c13, ['Frame_r41c13']),
    ('k1_frame_clears__Frame_r41c14', _guard_k1_frame_clears__Frame_r41c14, _effect_k1_frame_clears__Frame_r41c14, ['Frame_r41c14']),
    ('k1_frame_clears__Frame_r41c15', _guard_k1_frame_clears__Frame_r41c15, _effect_k1_frame_clears__Frame_r41c15, ['Frame_r41c15']),
    ('k1_frame_clears__Frame_r41c16', _guard_k1_frame_clears__Frame_r41c16, _effect_k1_frame_clears__Frame_r41c16, ['Frame_r41c16']),
    ('k1_frame_to_core__Frame_r36c11', _guard_k1_frame_to_core__Frame_r36c11, _effect_k1_frame_to_core__Frame_r36c11, ['Frame_r36c11']),
    ('k1_frame_to_core__Frame_r36c12', _guard_k1_frame_to_core__Frame_r36c12, _effect_k1_frame_to_core__Frame_r36c12, ['Frame_r36c12']),
    ('k1_frame_to_core__Frame_r36c13', _guard_k1_frame_to_core__Frame_r36c13, _effect_k1_frame_to_core__Frame_r36c13, ['Frame_r36c13']),
    ('k1_frame_to_core__Frame_r36c14', _guard_k1_frame_to_core__Frame_r36c14, _effect_k1_frame_to_core__Frame_r36c14, ['Frame_r36c14']),
    ('k1_frame_to_core__Frame_r36c15', _guard_k1_frame_to_core__Frame_r36c15, _effect_k1_frame_to_core__Frame_r36c15, ['Frame_r36c15']),
    ('k1_frame_to_core__Frame_r36c16', _guard_k1_frame_to_core__Frame_r36c16, _effect_k1_frame_to_core__Frame_r36c16, ['Frame_r36c16']),
    ('k1_frame_to_core__Frame_r37c11', _guard_k1_frame_to_core__Frame_r37c11, _effect_k1_frame_to_core__Frame_r37c11, ['Frame_r37c11']),
    ('k1_frame_to_core__Frame_r37c16', _guard_k1_frame_to_core__Frame_r37c16, _effect_k1_frame_to_core__Frame_r37c16, ['Frame_r37c16']),
    ('k1_frame_to_core__Frame_r38c11', _guard_k1_frame_to_core__Frame_r38c11, _effect_k1_frame_to_core__Frame_r38c11, ['Frame_r38c11']),
    ('k1_frame_to_core__Frame_r38c13', _guard_k1_frame_to_core__Frame_r38c13, _effect_k1_frame_to_core__Frame_r38c13, ['Frame_r38c13']),
    ('k1_frame_to_core__Frame_r38c14', _guard_k1_frame_to_core__Frame_r38c14, _effect_k1_frame_to_core__Frame_r38c14, ['Frame_r38c14']),
    ('k1_frame_to_core__Frame_r39c11', _guard_k1_frame_to_core__Frame_r39c11, _effect_k1_frame_to_core__Frame_r39c11, ['Frame_r39c11']),
    ('k1_frame_to_core__Frame_r39c13', _guard_k1_frame_to_core__Frame_r39c13, _effect_k1_frame_to_core__Frame_r39c13, ['Frame_r39c13']),
    ('k1_frame_to_core__Frame_r39c14', _guard_k1_frame_to_core__Frame_r39c14, _effect_k1_frame_to_core__Frame_r39c14, ['Frame_r39c14']),
    ('k1_frame_to_core__Frame_r40c11', _guard_k1_frame_to_core__Frame_r40c11, _effect_k1_frame_to_core__Frame_r40c11, ['Frame_r40c11']),
    ('k1_frame_to_core__Frame_r40c16', _guard_k1_frame_to_core__Frame_r40c16, _effect_k1_frame_to_core__Frame_r40c16, ['Frame_r40c16']),
    ('k1_frame_to_core__Frame_r41c11', _guard_k1_frame_to_core__Frame_r41c11, _effect_k1_frame_to_core__Frame_r41c11, ['Frame_r41c11']),
    ('k1_frame_to_core__Frame_r41c12', _guard_k1_frame_to_core__Frame_r41c12, _effect_k1_frame_to_core__Frame_r41c12, ['Frame_r41c12']),
    ('k1_frame_to_core__Frame_r41c13', _guard_k1_frame_to_core__Frame_r41c13, _effect_k1_frame_to_core__Frame_r41c13, ['Frame_r41c13']),
    ('k1_frame_to_core__Frame_r41c14', _guard_k1_frame_to_core__Frame_r41c14, _effect_k1_frame_to_core__Frame_r41c14, ['Frame_r41c14']),
    ('k1_frame_to_core__Frame_r41c15', _guard_k1_frame_to_core__Frame_r41c15, _effect_k1_frame_to_core__Frame_r41c15, ['Frame_r41c15']),
    ('k1_frame_to_core__Frame_r41c16', _guard_k1_frame_to_core__Frame_r41c16, _effect_k1_frame_to_core__Frame_r41c16, ['Frame_r41c16']),
    ('k1_hollow_to_field__Hollow_r37c12', _guard_k1_hollow_to_field__Hollow_r37c12, _effect_k1_hollow_to_field__Hollow_r37c12, ['Hollow_r37c12']),
    ('k1_hollow_to_field__Hollow_r37c13', _guard_k1_hollow_to_field__Hollow_r37c13, _effect_k1_hollow_to_field__Hollow_r37c13, ['Hollow_r37c13']),
    ('k1_hollow_to_field__Hollow_r37c14', _guard_k1_hollow_to_field__Hollow_r37c14, _effect_k1_hollow_to_field__Hollow_r37c14, ['Hollow_r37c14']),
    ('k1_hollow_to_field__Hollow_r37c15', _guard_k1_hollow_to_field__Hollow_r37c15, _effect_k1_hollow_to_field__Hollow_r37c15, ['Hollow_r37c15']),
    ('k1_hollow_to_field__Hollow_r38c12', _guard_k1_hollow_to_field__Hollow_r38c12, _effect_k1_hollow_to_field__Hollow_r38c12, ['Hollow_r38c12']),
    ('k1_hollow_to_field__Hollow_r38c15', _guard_k1_hollow_to_field__Hollow_r38c15, _effect_k1_hollow_to_field__Hollow_r38c15, ['Hollow_r38c15']),
    ('k1_hollow_to_field__Hollow_r39c12', _guard_k1_hollow_to_field__Hollow_r39c12, _effect_k1_hollow_to_field__Hollow_r39c12, ['Hollow_r39c12']),
    ('k1_hollow_to_field__Hollow_r39c15', _guard_k1_hollow_to_field__Hollow_r39c15, _effect_k1_hollow_to_field__Hollow_r39c15, ['Hollow_r39c15']),
    ('k1_hollow_to_field__Hollow_r40c12', _guard_k1_hollow_to_field__Hollow_r40c12, _effect_k1_hollow_to_field__Hollow_r40c12, ['Hollow_r40c12']),
    ('k1_hollow_to_field__Hollow_r40c13', _guard_k1_hollow_to_field__Hollow_r40c13, _effect_k1_hollow_to_field__Hollow_r40c13, ['Hollow_r40c13']),
    ('k1_hollow_to_field__Hollow_r40c14', _guard_k1_hollow_to_field__Hollow_r40c14, _effect_k1_hollow_to_field__Hollow_r40c14, ['Hollow_r40c14']),
    ('k1_hollow_to_field__Hollow_r40c15', _guard_k1_hollow_to_field__Hollow_r40c15, _effect_k1_hollow_to_field__Hollow_r40c15, ['Hollow_r40c15']),
    ('k1_hollow_to_bar__Hollow_r37c12', _guard_k1_hollow_to_bar__Hollow_r37c12, _effect_k1_hollow_to_bar__Hollow_r37c12, ['Hollow_r37c12']),
    ('k1_hollow_to_bar__Hollow_r37c13', _guard_k1_hollow_to_bar__Hollow_r37c13, _effect_k1_hollow_to_bar__Hollow_r37c13, ['Hollow_r37c13']),
    ('k1_hollow_to_bar__Hollow_r37c14', _guard_k1_hollow_to_bar__Hollow_r37c14, _effect_k1_hollow_to_bar__Hollow_r37c14, ['Hollow_r37c14']),
    ('k1_hollow_to_bar__Hollow_r37c15', _guard_k1_hollow_to_bar__Hollow_r37c15, _effect_k1_hollow_to_bar__Hollow_r37c15, ['Hollow_r37c15']),
    ('k1_hollow_to_bar__Hollow_r38c12', _guard_k1_hollow_to_bar__Hollow_r38c12, _effect_k1_hollow_to_bar__Hollow_r38c12, ['Hollow_r38c12']),
    ('k1_hollow_to_bar__Hollow_r38c15', _guard_k1_hollow_to_bar__Hollow_r38c15, _effect_k1_hollow_to_bar__Hollow_r38c15, ['Hollow_r38c15']),
    ('k1_hollow_to_bar__Hollow_r39c12', _guard_k1_hollow_to_bar__Hollow_r39c12, _effect_k1_hollow_to_bar__Hollow_r39c12, ['Hollow_r39c12']),
    ('k1_hollow_to_bar__Hollow_r39c15', _guard_k1_hollow_to_bar__Hollow_r39c15, _effect_k1_hollow_to_bar__Hollow_r39c15, ['Hollow_r39c15']),
    ('k1_hollow_to_bar__Hollow_r40c12', _guard_k1_hollow_to_bar__Hollow_r40c12, _effect_k1_hollow_to_bar__Hollow_r40c12, ['Hollow_r40c12']),
    ('k1_hollow_to_bar__Hollow_r40c13', _guard_k1_hollow_to_bar__Hollow_r40c13, _effect_k1_hollow_to_bar__Hollow_r40c13, ['Hollow_r40c13']),
    ('k1_hollow_to_bar__Hollow_r40c14', _guard_k1_hollow_to_bar__Hollow_r40c14, _effect_k1_hollow_to_bar__Hollow_r40c14, ['Hollow_r40c14']),
    ('k1_hollow_to_bar__Hollow_r40c15', _guard_k1_hollow_to_bar__Hollow_r40c15, _effect_k1_hollow_to_bar__Hollow_r40c15, ['Hollow_r40c15']),
    ('k1_hollow_clears__Hollow_r37c12', _guard_k1_hollow_clears__Hollow_r37c12, _effect_k1_hollow_clears__Hollow_r37c12, ['Hollow_r37c12']),
    ('k1_hollow_clears__Hollow_r37c13', _guard_k1_hollow_clears__Hollow_r37c13, _effect_k1_hollow_clears__Hollow_r37c13, ['Hollow_r37c13']),
    ('k1_hollow_clears__Hollow_r37c14', _guard_k1_hollow_clears__Hollow_r37c14, _effect_k1_hollow_clears__Hollow_r37c14, ['Hollow_r37c14']),
    ('k1_hollow_clears__Hollow_r37c15', _guard_k1_hollow_clears__Hollow_r37c15, _effect_k1_hollow_clears__Hollow_r37c15, ['Hollow_r37c15']),
    ('k1_hollow_clears__Hollow_r38c12', _guard_k1_hollow_clears__Hollow_r38c12, _effect_k1_hollow_clears__Hollow_r38c12, ['Hollow_r38c12']),
    ('k1_hollow_clears__Hollow_r38c15', _guard_k1_hollow_clears__Hollow_r38c15, _effect_k1_hollow_clears__Hollow_r38c15, ['Hollow_r38c15']),
    ('k1_hollow_clears__Hollow_r39c12', _guard_k1_hollow_clears__Hollow_r39c12, _effect_k1_hollow_clears__Hollow_r39c12, ['Hollow_r39c12']),
    ('k1_hollow_clears__Hollow_r39c15', _guard_k1_hollow_clears__Hollow_r39c15, _effect_k1_hollow_clears__Hollow_r39c15, ['Hollow_r39c15']),
    ('k1_hollow_clears__Hollow_r40c12', _guard_k1_hollow_clears__Hollow_r40c12, _effect_k1_hollow_clears__Hollow_r40c12, ['Hollow_r40c12']),
    ('k1_hollow_clears__Hollow_r40c13', _guard_k1_hollow_clears__Hollow_r40c13, _effect_k1_hollow_clears__Hollow_r40c13, ['Hollow_r40c13']),
    ('k1_hollow_clears__Hollow_r40c14', _guard_k1_hollow_clears__Hollow_r40c14, _effect_k1_hollow_clears__Hollow_r40c14, ['Hollow_r40c14']),
    ('k1_hollow_clears__Hollow_r40c15', _guard_k1_hollow_clears__Hollow_r40c15, _effect_k1_hollow_clears__Hollow_r40c15, ['Hollow_r40c15']),
    ('k1_dot_to_field__Dot_r38c16', _guard_k1_dot_to_field__Dot_r38c16, _effect_k1_dot_to_field__Dot_r38c16, ['Dot_r38c16']),
    ('k1_dot_to_field__Dot_r38c18', _guard_k1_dot_to_field__Dot_r38c18, _effect_k1_dot_to_field__Dot_r38c18, ['Dot_r38c18']),
    ('k1_dot_to_field__Dot_r38c19', _guard_k1_dot_to_field__Dot_r38c19, _effect_k1_dot_to_field__Dot_r38c19, ['Dot_r38c19']),
    ('k1_dot_to_field__Dot_r38c21', _guard_k1_dot_to_field__Dot_r38c21, _effect_k1_dot_to_field__Dot_r38c21, ['Dot_r38c21']),
    ('k1_dot_to_field__Dot_r38c22', _guard_k1_dot_to_field__Dot_r38c22, _effect_k1_dot_to_field__Dot_r38c22, ['Dot_r38c22']),
    ('k1_dot_to_field__Dot_r39c17', _guard_k1_dot_to_field__Dot_r39c17, _effect_k1_dot_to_field__Dot_r39c17, ['Dot_r39c17']),
    ('k1_dot_to_field__Dot_r39c18', _guard_k1_dot_to_field__Dot_r39c18, _effect_k1_dot_to_field__Dot_r39c18, ['Dot_r39c18']),
    ('k1_dot_to_field__Dot_r39c20', _guard_k1_dot_to_field__Dot_r39c20, _effect_k1_dot_to_field__Dot_r39c20, ['Dot_r39c20']),
    ('k1_dot_to_field__Dot_r39c21', _guard_k1_dot_to_field__Dot_r39c21, _effect_k1_dot_to_field__Dot_r39c21, ['Dot_r39c21']),
    ('k1_dot_to_blank__Dot_r38c16', _guard_k1_dot_to_blank__Dot_r38c16, _effect_k1_dot_to_blank__Dot_r38c16, ['Dot_r38c16']),
    ('k1_dot_to_blank__Dot_r38c18', _guard_k1_dot_to_blank__Dot_r38c18, _effect_k1_dot_to_blank__Dot_r38c18, ['Dot_r38c18']),
    ('k1_dot_to_blank__Dot_r38c19', _guard_k1_dot_to_blank__Dot_r38c19, _effect_k1_dot_to_blank__Dot_r38c19, ['Dot_r38c19']),
    ('k1_dot_to_blank__Dot_r38c21', _guard_k1_dot_to_blank__Dot_r38c21, _effect_k1_dot_to_blank__Dot_r38c21, ['Dot_r38c21']),
    ('k1_dot_to_blank__Dot_r38c22', _guard_k1_dot_to_blank__Dot_r38c22, _effect_k1_dot_to_blank__Dot_r38c22, ['Dot_r38c22']),
    ('k1_dot_to_blank__Dot_r39c17', _guard_k1_dot_to_blank__Dot_r39c17, _effect_k1_dot_to_blank__Dot_r39c17, ['Dot_r39c17']),
    ('k1_dot_to_blank__Dot_r39c18', _guard_k1_dot_to_blank__Dot_r39c18, _effect_k1_dot_to_blank__Dot_r39c18, ['Dot_r39c18']),
    ('k1_dot_to_blank__Dot_r39c20', _guard_k1_dot_to_blank__Dot_r39c20, _effect_k1_dot_to_blank__Dot_r39c20, ['Dot_r39c20']),
    ('k1_dot_to_blank__Dot_r39c21', _guard_k1_dot_to_blank__Dot_r39c21, _effect_k1_dot_to_blank__Dot_r39c21, ['Dot_r39c21']),
    ('k1_core_to_field__BarCore_r32c13', _guard_k1_core_to_field__BarCore_r32c13, _effect_k1_core_to_field__BarCore_r32c13, ['BarCore_r32c13']),
    ('k1_core_to_field__BarCore_r32c14', _guard_k1_core_to_field__BarCore_r32c14, _effect_k1_core_to_field__BarCore_r32c14, ['BarCore_r32c14']),
    ('k1_core_to_field__BarCore_r33c13', _guard_k1_core_to_field__BarCore_r33c13, _effect_k1_core_to_field__BarCore_r33c13, ['BarCore_r33c13']),
    ('k1_core_to_field__BarCore_r33c14', _guard_k1_core_to_field__BarCore_r33c14, _effect_k1_core_to_field__BarCore_r33c14, ['BarCore_r33c14']),
    ('k1_core_to_field__BarCore_r38c17', _guard_k1_core_to_field__BarCore_r38c17, _effect_k1_core_to_field__BarCore_r38c17, ['BarCore_r38c17']),
    ('k1_core_to_field__BarCore_r38c20', _guard_k1_core_to_field__BarCore_r38c20, _effect_k1_core_to_field__BarCore_r38c20, ['BarCore_r38c20']),
    ('k1_core_to_field__BarCore_r39c16', _guard_k1_core_to_field__BarCore_r39c16, _effect_k1_core_to_field__BarCore_r39c16, ['BarCore_r39c16']),
    ('k1_core_to_field__BarCore_r39c19', _guard_k1_core_to_field__BarCore_r39c19, _effect_k1_core_to_field__BarCore_r39c19, ['BarCore_r39c19']),
    ('k1_core_to_field__BarCore_r39c22', _guard_k1_core_to_field__BarCore_r39c22, _effect_k1_core_to_field__BarCore_r39c22, ['BarCore_r39c22']),
    ('k1_core_to_field__BarCore_r53c59', _guard_k1_core_to_field__BarCore_r53c59, _effect_k1_core_to_field__BarCore_r53c59, ['BarCore_r53c59']),
    ('k1_core_to_field__BarCore_r53c60', _guard_k1_core_to_field__BarCore_r53c60, _effect_k1_core_to_field__BarCore_r53c60, ['BarCore_r53c60']),
    ('k1_core_to_field__BarCore_r53c61', _guard_k1_core_to_field__BarCore_r53c61, _effect_k1_core_to_field__BarCore_r53c61, ['BarCore_r53c61']),
    ('k1_core_to_field__BarCore_r53c62', _guard_k1_core_to_field__BarCore_r53c62, _effect_k1_core_to_field__BarCore_r53c62, ['BarCore_r53c62']),
    ('k1_core_to_field__BarCore_r53c63', _guard_k1_core_to_field__BarCore_r53c63, _effect_k1_core_to_field__BarCore_r53c63, ['BarCore_r53c63']),
    ('k1_core_to_blank__BarCore_r32c13', _guard_k1_core_to_blank__BarCore_r32c13, _effect_k1_core_to_blank__BarCore_r32c13, ['BarCore_r32c13']),
    ('k1_core_to_blank__BarCore_r32c14', _guard_k1_core_to_blank__BarCore_r32c14, _effect_k1_core_to_blank__BarCore_r32c14, ['BarCore_r32c14']),
    ('k1_core_to_blank__BarCore_r33c13', _guard_k1_core_to_blank__BarCore_r33c13, _effect_k1_core_to_blank__BarCore_r33c13, ['BarCore_r33c13']),
    ('k1_core_to_blank__BarCore_r33c14', _guard_k1_core_to_blank__BarCore_r33c14, _effect_k1_core_to_blank__BarCore_r33c14, ['BarCore_r33c14']),
    ('k1_core_to_blank__BarCore_r38c17', _guard_k1_core_to_blank__BarCore_r38c17, _effect_k1_core_to_blank__BarCore_r38c17, ['BarCore_r38c17']),
    ('k1_core_to_blank__BarCore_r38c20', _guard_k1_core_to_blank__BarCore_r38c20, _effect_k1_core_to_blank__BarCore_r38c20, ['BarCore_r38c20']),
    ('k1_core_to_blank__BarCore_r39c16', _guard_k1_core_to_blank__BarCore_r39c16, _effect_k1_core_to_blank__BarCore_r39c16, ['BarCore_r39c16']),
    ('k1_core_to_blank__BarCore_r39c19', _guard_k1_core_to_blank__BarCore_r39c19, _effect_k1_core_to_blank__BarCore_r39c19, ['BarCore_r39c19']),
    ('k1_core_to_blank__BarCore_r39c22', _guard_k1_core_to_blank__BarCore_r39c22, _effect_k1_core_to_blank__BarCore_r39c22, ['BarCore_r39c22']),
    ('k1_core_to_blank__BarCore_r53c59', _guard_k1_core_to_blank__BarCore_r53c59, _effect_k1_core_to_blank__BarCore_r53c59, ['BarCore_r53c59']),
    ('k1_core_to_blank__BarCore_r53c60', _guard_k1_core_to_blank__BarCore_r53c60, _effect_k1_core_to_blank__BarCore_r53c60, ['BarCore_r53c60']),
    ('k1_core_to_blank__BarCore_r53c61', _guard_k1_core_to_blank__BarCore_r53c61, _effect_k1_core_to_blank__BarCore_r53c61, ['BarCore_r53c61']),
    ('k1_core_to_blank__BarCore_r53c62', _guard_k1_core_to_blank__BarCore_r53c62, _effect_k1_core_to_blank__BarCore_r53c62, ['BarCore_r53c62']),
    ('k1_core_to_blank__BarCore_r53c63', _guard_k1_core_to_blank__BarCore_r53c63, _effect_k1_core_to_blank__BarCore_r53c63, ['BarCore_r53c63']),
    ('k2_field_from_frame__Field_r30c11', _guard_k2_field_from_frame__Field_r30c11, _effect_k2_field_from_frame__Field_r30c11, ['Field_r30c11']),
    ('k2_field_from_frame__Field_r30c12', _guard_k2_field_from_frame__Field_r30c12, _effect_k2_field_from_frame__Field_r30c12, ['Field_r30c12']),
    ('k2_field_from_frame__Field_r30c15', _guard_k2_field_from_frame__Field_r30c15, _effect_k2_field_from_frame__Field_r30c15, ['Field_r30c15']),
    ('k2_field_from_frame__Field_r30c16', _guard_k2_field_from_frame__Field_r30c16, _effect_k2_field_from_frame__Field_r30c16, ['Field_r30c16']),
    ('k2_field_from_frame__Field_r31c11', _guard_k2_field_from_frame__Field_r31c11, _effect_k2_field_from_frame__Field_r31c11, ['Field_r31c11']),
    ('k2_field_from_frame__Field_r31c12', _guard_k2_field_from_frame__Field_r31c12, _effect_k2_field_from_frame__Field_r31c12, ['Field_r31c12']),
    ('k2_field_from_frame__Field_r31c15', _guard_k2_field_from_frame__Field_r31c15, _effect_k2_field_from_frame__Field_r31c15, ['Field_r31c15']),
    ('k2_field_from_frame__Field_r31c16', _guard_k2_field_from_frame__Field_r31c16, _effect_k2_field_from_frame__Field_r31c16, ['Field_r31c16']),
    ('k2_field_from_frame__Field_r32c11', _guard_k2_field_from_frame__Field_r32c11, _effect_k2_field_from_frame__Field_r32c11, ['Field_r32c11']),
    ('k2_field_from_frame__Field_r32c12', _guard_k2_field_from_frame__Field_r32c12, _effect_k2_field_from_frame__Field_r32c12, ['Field_r32c12']),
    ('k2_field_from_frame__Field_r32c15', _guard_k2_field_from_frame__Field_r32c15, _effect_k2_field_from_frame__Field_r32c15, ['Field_r32c15']),
    ('k2_field_from_frame__Field_r32c16', _guard_k2_field_from_frame__Field_r32c16, _effect_k2_field_from_frame__Field_r32c16, ['Field_r32c16']),
    ('k2_field_from_frame__Field_r33c11', _guard_k2_field_from_frame__Field_r33c11, _effect_k2_field_from_frame__Field_r33c11, ['Field_r33c11']),
    ('k2_field_from_frame__Field_r33c12', _guard_k2_field_from_frame__Field_r33c12, _effect_k2_field_from_frame__Field_r33c12, ['Field_r33c12']),
    ('k2_field_from_frame__Field_r33c15', _guard_k2_field_from_frame__Field_r33c15, _effect_k2_field_from_frame__Field_r33c15, ['Field_r33c15']),
    ('k2_field_from_frame__Field_r33c16', _guard_k2_field_from_frame__Field_r33c16, _effect_k2_field_from_frame__Field_r33c16, ['Field_r33c16']),
    ('k2_field_from_frame__Field_r34c11', _guard_k2_field_from_frame__Field_r34c11, _effect_k2_field_from_frame__Field_r34c11, ['Field_r34c11']),
    ('k2_field_from_frame__Field_r34c12', _guard_k2_field_from_frame__Field_r34c12, _effect_k2_field_from_frame__Field_r34c12, ['Field_r34c12']),
    ('k2_field_from_frame__Field_r34c15', _guard_k2_field_from_frame__Field_r34c15, _effect_k2_field_from_frame__Field_r34c15, ['Field_r34c15']),
    ('k2_field_from_frame__Field_r34c16', _guard_k2_field_from_frame__Field_r34c16, _effect_k2_field_from_frame__Field_r34c16, ['Field_r34c16']),
    ('k2_field_from_frame__Field_r35c11', _guard_k2_field_from_frame__Field_r35c11, _effect_k2_field_from_frame__Field_r35c11, ['Field_r35c11']),
    ('k2_field_from_frame__Field_r35c12', _guard_k2_field_from_frame__Field_r35c12, _effect_k2_field_from_frame__Field_r35c12, ['Field_r35c12']),
    ('k2_field_from_frame__Field_r35c15', _guard_k2_field_from_frame__Field_r35c15, _effect_k2_field_from_frame__Field_r35c15, ['Field_r35c15']),
    ('k2_field_from_frame__Field_r35c16', _guard_k2_field_from_frame__Field_r35c16, _effect_k2_field_from_frame__Field_r35c16, ['Field_r35c16']),
    ('k2_field_from_hollow__Field_r30c11', _guard_k2_field_from_hollow__Field_r30c11, _effect_k2_field_from_hollow__Field_r30c11, ['Field_r30c11']),
    ('k2_field_from_hollow__Field_r30c12', _guard_k2_field_from_hollow__Field_r30c12, _effect_k2_field_from_hollow__Field_r30c12, ['Field_r30c12']),
    ('k2_field_from_hollow__Field_r30c15', _guard_k2_field_from_hollow__Field_r30c15, _effect_k2_field_from_hollow__Field_r30c15, ['Field_r30c15']),
    ('k2_field_from_hollow__Field_r30c16', _guard_k2_field_from_hollow__Field_r30c16, _effect_k2_field_from_hollow__Field_r30c16, ['Field_r30c16']),
    ('k2_field_from_hollow__Field_r31c11', _guard_k2_field_from_hollow__Field_r31c11, _effect_k2_field_from_hollow__Field_r31c11, ['Field_r31c11']),
    ('k2_field_from_hollow__Field_r31c12', _guard_k2_field_from_hollow__Field_r31c12, _effect_k2_field_from_hollow__Field_r31c12, ['Field_r31c12']),
    ('k2_field_from_hollow__Field_r31c15', _guard_k2_field_from_hollow__Field_r31c15, _effect_k2_field_from_hollow__Field_r31c15, ['Field_r31c15']),
    ('k2_field_from_hollow__Field_r31c16', _guard_k2_field_from_hollow__Field_r31c16, _effect_k2_field_from_hollow__Field_r31c16, ['Field_r31c16']),
    ('k2_field_from_hollow__Field_r32c11', _guard_k2_field_from_hollow__Field_r32c11, _effect_k2_field_from_hollow__Field_r32c11, ['Field_r32c11']),
    ('k2_field_from_hollow__Field_r32c12', _guard_k2_field_from_hollow__Field_r32c12, _effect_k2_field_from_hollow__Field_r32c12, ['Field_r32c12']),
    ('k2_field_from_hollow__Field_r32c15', _guard_k2_field_from_hollow__Field_r32c15, _effect_k2_field_from_hollow__Field_r32c15, ['Field_r32c15']),
    ('k2_field_from_hollow__Field_r32c16', _guard_k2_field_from_hollow__Field_r32c16, _effect_k2_field_from_hollow__Field_r32c16, ['Field_r32c16']),
    ('k2_field_from_hollow__Field_r33c11', _guard_k2_field_from_hollow__Field_r33c11, _effect_k2_field_from_hollow__Field_r33c11, ['Field_r33c11']),
    ('k2_field_from_hollow__Field_r33c12', _guard_k2_field_from_hollow__Field_r33c12, _effect_k2_field_from_hollow__Field_r33c12, ['Field_r33c12']),
    ('k2_field_from_hollow__Field_r33c15', _guard_k2_field_from_hollow__Field_r33c15, _effect_k2_field_from_hollow__Field_r33c15, ['Field_r33c15']),
    ('k2_field_from_hollow__Field_r33c16', _guard_k2_field_from_hollow__Field_r33c16, _effect_k2_field_from_hollow__Field_r33c16, ['Field_r33c16']),
    ('k2_field_from_hollow__Field_r34c11', _guard_k2_field_from_hollow__Field_r34c11, _effect_k2_field_from_hollow__Field_r34c11, ['Field_r34c11']),
    ('k2_field_from_hollow__Field_r34c12', _guard_k2_field_from_hollow__Field_r34c12, _effect_k2_field_from_hollow__Field_r34c12, ['Field_r34c12']),
    ('k2_field_from_hollow__Field_r34c15', _guard_k2_field_from_hollow__Field_r34c15, _effect_k2_field_from_hollow__Field_r34c15, ['Field_r34c15']),
    ('k2_field_from_hollow__Field_r34c16', _guard_k2_field_from_hollow__Field_r34c16, _effect_k2_field_from_hollow__Field_r34c16, ['Field_r34c16']),
    ('k2_field_from_hollow__Field_r35c11', _guard_k2_field_from_hollow__Field_r35c11, _effect_k2_field_from_hollow__Field_r35c11, ['Field_r35c11']),
    ('k2_field_from_hollow__Field_r35c12', _guard_k2_field_from_hollow__Field_r35c12, _effect_k2_field_from_hollow__Field_r35c12, ['Field_r35c12']),
    ('k2_field_from_hollow__Field_r35c15', _guard_k2_field_from_hollow__Field_r35c15, _effect_k2_field_from_hollow__Field_r35c15, ['Field_r35c15']),
    ('k2_field_from_hollow__Field_r35c16', _guard_k2_field_from_hollow__Field_r35c16, _effect_k2_field_from_hollow__Field_r35c16, ['Field_r35c16']),
    ('k2_field_from_dot__Field_r30c11', _guard_k2_field_from_dot__Field_r30c11, _effect_k2_field_from_dot__Field_r30c11, ['Field_r30c11']),
    ('k2_field_from_dot__Field_r30c12', _guard_k2_field_from_dot__Field_r30c12, _effect_k2_field_from_dot__Field_r30c12, ['Field_r30c12']),
    ('k2_field_from_dot__Field_r30c15', _guard_k2_field_from_dot__Field_r30c15, _effect_k2_field_from_dot__Field_r30c15, ['Field_r30c15']),
    ('k2_field_from_dot__Field_r30c16', _guard_k2_field_from_dot__Field_r30c16, _effect_k2_field_from_dot__Field_r30c16, ['Field_r30c16']),
    ('k2_field_from_dot__Field_r31c11', _guard_k2_field_from_dot__Field_r31c11, _effect_k2_field_from_dot__Field_r31c11, ['Field_r31c11']),
    ('k2_field_from_dot__Field_r31c12', _guard_k2_field_from_dot__Field_r31c12, _effect_k2_field_from_dot__Field_r31c12, ['Field_r31c12']),
    ('k2_field_from_dot__Field_r31c15', _guard_k2_field_from_dot__Field_r31c15, _effect_k2_field_from_dot__Field_r31c15, ['Field_r31c15']),
    ('k2_field_from_dot__Field_r31c16', _guard_k2_field_from_dot__Field_r31c16, _effect_k2_field_from_dot__Field_r31c16, ['Field_r31c16']),
    ('k2_field_from_dot__Field_r32c11', _guard_k2_field_from_dot__Field_r32c11, _effect_k2_field_from_dot__Field_r32c11, ['Field_r32c11']),
    ('k2_field_from_dot__Field_r32c12', _guard_k2_field_from_dot__Field_r32c12, _effect_k2_field_from_dot__Field_r32c12, ['Field_r32c12']),
    ('k2_field_from_dot__Field_r32c15', _guard_k2_field_from_dot__Field_r32c15, _effect_k2_field_from_dot__Field_r32c15, ['Field_r32c15']),
    ('k2_field_from_dot__Field_r32c16', _guard_k2_field_from_dot__Field_r32c16, _effect_k2_field_from_dot__Field_r32c16, ['Field_r32c16']),
    ('k2_field_from_dot__Field_r33c11', _guard_k2_field_from_dot__Field_r33c11, _effect_k2_field_from_dot__Field_r33c11, ['Field_r33c11']),
    ('k2_field_from_dot__Field_r33c12', _guard_k2_field_from_dot__Field_r33c12, _effect_k2_field_from_dot__Field_r33c12, ['Field_r33c12']),
    ('k2_field_from_dot__Field_r33c15', _guard_k2_field_from_dot__Field_r33c15, _effect_k2_field_from_dot__Field_r33c15, ['Field_r33c15']),
    ('k2_field_from_dot__Field_r33c16', _guard_k2_field_from_dot__Field_r33c16, _effect_k2_field_from_dot__Field_r33c16, ['Field_r33c16']),
    ('k2_field_from_dot__Field_r34c11', _guard_k2_field_from_dot__Field_r34c11, _effect_k2_field_from_dot__Field_r34c11, ['Field_r34c11']),
    ('k2_field_from_dot__Field_r34c12', _guard_k2_field_from_dot__Field_r34c12, _effect_k2_field_from_dot__Field_r34c12, ['Field_r34c12']),
    ('k2_field_from_dot__Field_r34c15', _guard_k2_field_from_dot__Field_r34c15, _effect_k2_field_from_dot__Field_r34c15, ['Field_r34c15']),
    ('k2_field_from_dot__Field_r34c16', _guard_k2_field_from_dot__Field_r34c16, _effect_k2_field_from_dot__Field_r34c16, ['Field_r34c16']),
    ('k2_field_from_dot__Field_r35c11', _guard_k2_field_from_dot__Field_r35c11, _effect_k2_field_from_dot__Field_r35c11, ['Field_r35c11']),
    ('k2_field_from_dot__Field_r35c12', _guard_k2_field_from_dot__Field_r35c12, _effect_k2_field_from_dot__Field_r35c12, ['Field_r35c12']),
    ('k2_field_from_dot__Field_r35c15', _guard_k2_field_from_dot__Field_r35c15, _effect_k2_field_from_dot__Field_r35c15, ['Field_r35c15']),
    ('k2_field_from_dot__Field_r35c16', _guard_k2_field_from_dot__Field_r35c16, _effect_k2_field_from_dot__Field_r35c16, ['Field_r35c16']),
    ('k2_field_from_core__Field_r30c11', _guard_k2_field_from_core__Field_r30c11, _effect_k2_field_from_core__Field_r30c11, ['Field_r30c11']),
    ('k2_field_from_core__Field_r30c12', _guard_k2_field_from_core__Field_r30c12, _effect_k2_field_from_core__Field_r30c12, ['Field_r30c12']),
    ('k2_field_from_core__Field_r30c15', _guard_k2_field_from_core__Field_r30c15, _effect_k2_field_from_core__Field_r30c15, ['Field_r30c15']),
    ('k2_field_from_core__Field_r30c16', _guard_k2_field_from_core__Field_r30c16, _effect_k2_field_from_core__Field_r30c16, ['Field_r30c16']),
    ('k2_field_from_core__Field_r31c11', _guard_k2_field_from_core__Field_r31c11, _effect_k2_field_from_core__Field_r31c11, ['Field_r31c11']),
    ('k2_field_from_core__Field_r31c12', _guard_k2_field_from_core__Field_r31c12, _effect_k2_field_from_core__Field_r31c12, ['Field_r31c12']),
    ('k2_field_from_core__Field_r31c15', _guard_k2_field_from_core__Field_r31c15, _effect_k2_field_from_core__Field_r31c15, ['Field_r31c15']),
    ('k2_field_from_core__Field_r31c16', _guard_k2_field_from_core__Field_r31c16, _effect_k2_field_from_core__Field_r31c16, ['Field_r31c16']),
    ('k2_field_from_core__Field_r32c11', _guard_k2_field_from_core__Field_r32c11, _effect_k2_field_from_core__Field_r32c11, ['Field_r32c11']),
    ('k2_field_from_core__Field_r32c12', _guard_k2_field_from_core__Field_r32c12, _effect_k2_field_from_core__Field_r32c12, ['Field_r32c12']),
    ('k2_field_from_core__Field_r32c15', _guard_k2_field_from_core__Field_r32c15, _effect_k2_field_from_core__Field_r32c15, ['Field_r32c15']),
    ('k2_field_from_core__Field_r32c16', _guard_k2_field_from_core__Field_r32c16, _effect_k2_field_from_core__Field_r32c16, ['Field_r32c16']),
    ('k2_field_from_core__Field_r33c11', _guard_k2_field_from_core__Field_r33c11, _effect_k2_field_from_core__Field_r33c11, ['Field_r33c11']),
    ('k2_field_from_core__Field_r33c12', _guard_k2_field_from_core__Field_r33c12, _effect_k2_field_from_core__Field_r33c12, ['Field_r33c12']),
    ('k2_field_from_core__Field_r33c15', _guard_k2_field_from_core__Field_r33c15, _effect_k2_field_from_core__Field_r33c15, ['Field_r33c15']),
    ('k2_field_from_core__Field_r33c16', _guard_k2_field_from_core__Field_r33c16, _effect_k2_field_from_core__Field_r33c16, ['Field_r33c16']),
    ('k2_field_from_core__Field_r34c11', _guard_k2_field_from_core__Field_r34c11, _effect_k2_field_from_core__Field_r34c11, ['Field_r34c11']),
    ('k2_field_from_core__Field_r34c12', _guard_k2_field_from_core__Field_r34c12, _effect_k2_field_from_core__Field_r34c12, ['Field_r34c12']),
    ('k2_field_from_core__Field_r34c15', _guard_k2_field_from_core__Field_r34c15, _effect_k2_field_from_core__Field_r34c15, ['Field_r34c15']),
    ('k2_field_from_core__Field_r34c16', _guard_k2_field_from_core__Field_r34c16, _effect_k2_field_from_core__Field_r34c16, ['Field_r34c16']),
    ('k2_field_from_core__Field_r35c11', _guard_k2_field_from_core__Field_r35c11, _effect_k2_field_from_core__Field_r35c11, ['Field_r35c11']),
    ('k2_field_from_core__Field_r35c12', _guard_k2_field_from_core__Field_r35c12, _effect_k2_field_from_core__Field_r35c12, ['Field_r35c12']),
    ('k2_field_from_core__Field_r35c15', _guard_k2_field_from_core__Field_r35c15, _effect_k2_field_from_core__Field_r35c15, ['Field_r35c15']),
    ('k2_field_from_core__Field_r35c16', _guard_k2_field_from_core__Field_r35c16, _effect_k2_field_from_core__Field_r35c16, ['Field_r35c16']),
    ('k2_bar_from_frame__BarBody_r30c13', _guard_k2_bar_from_frame__BarBody_r30c13, _effect_k2_bar_from_frame__BarBody_r30c13, ['BarBody_r30c13']),
    ('k2_bar_from_frame__BarBody_r30c14', _guard_k2_bar_from_frame__BarBody_r30c14, _effect_k2_bar_from_frame__BarBody_r30c14, ['BarBody_r30c14']),
    ('k2_bar_from_frame__BarBody_r31c13', _guard_k2_bar_from_frame__BarBody_r31c13, _effect_k2_bar_from_frame__BarBody_r31c13, ['BarBody_r31c13']),
    ('k2_bar_from_frame__BarBody_r31c14', _guard_k2_bar_from_frame__BarBody_r31c14, _effect_k2_bar_from_frame__BarBody_r31c14, ['BarBody_r31c14']),
    ('k2_bar_from_frame__BarBody_r34c13', _guard_k2_bar_from_frame__BarBody_r34c13, _effect_k2_bar_from_frame__BarBody_r34c13, ['BarBody_r34c13']),
    ('k2_bar_from_frame__BarBody_r34c14', _guard_k2_bar_from_frame__BarBody_r34c14, _effect_k2_bar_from_frame__BarBody_r34c14, ['BarBody_r34c14']),
    ('k2_bar_from_frame__BarBody_r35c13', _guard_k2_bar_from_frame__BarBody_r35c13, _effect_k2_bar_from_frame__BarBody_r35c13, ['BarBody_r35c13']),
    ('k2_bar_from_frame__BarBody_r35c14', _guard_k2_bar_from_frame__BarBody_r35c14, _effect_k2_bar_from_frame__BarBody_r35c14, ['BarBody_r35c14']),
    ('k2_bar_from_hollow__BarBody_r30c13', _guard_k2_bar_from_hollow__BarBody_r30c13, _effect_k2_bar_from_hollow__BarBody_r30c13, ['BarBody_r30c13']),
    ('k2_bar_from_hollow__BarBody_r30c14', _guard_k2_bar_from_hollow__BarBody_r30c14, _effect_k2_bar_from_hollow__BarBody_r30c14, ['BarBody_r30c14']),
    ('k2_bar_from_hollow__BarBody_r31c13', _guard_k2_bar_from_hollow__BarBody_r31c13, _effect_k2_bar_from_hollow__BarBody_r31c13, ['BarBody_r31c13']),
    ('k2_bar_from_hollow__BarBody_r31c14', _guard_k2_bar_from_hollow__BarBody_r31c14, _effect_k2_bar_from_hollow__BarBody_r31c14, ['BarBody_r31c14']),
    ('k2_bar_from_hollow__BarBody_r34c13', _guard_k2_bar_from_hollow__BarBody_r34c13, _effect_k2_bar_from_hollow__BarBody_r34c13, ['BarBody_r34c13']),
    ('k2_bar_from_hollow__BarBody_r34c14', _guard_k2_bar_from_hollow__BarBody_r34c14, _effect_k2_bar_from_hollow__BarBody_r34c14, ['BarBody_r34c14']),
    ('k2_bar_from_hollow__BarBody_r35c13', _guard_k2_bar_from_hollow__BarBody_r35c13, _effect_k2_bar_from_hollow__BarBody_r35c13, ['BarBody_r35c13']),
    ('k2_bar_from_hollow__BarBody_r35c14', _guard_k2_bar_from_hollow__BarBody_r35c14, _effect_k2_bar_from_hollow__BarBody_r35c14, ['BarBody_r35c14']),
    ('k2_bar_regrows_from_hollow__BarBody_r30c13', _guard_k2_bar_regrows_from_hollow__BarBody_r30c13, _effect_k2_bar_regrows_from_hollow__BarBody_r30c13, ['BarBody_r30c13']),
    ('k2_bar_regrows_from_hollow__BarBody_r30c14', _guard_k2_bar_regrows_from_hollow__BarBody_r30c14, _effect_k2_bar_regrows_from_hollow__BarBody_r30c14, ['BarBody_r30c14']),
    ('k2_bar_regrows_from_hollow__BarBody_r31c13', _guard_k2_bar_regrows_from_hollow__BarBody_r31c13, _effect_k2_bar_regrows_from_hollow__BarBody_r31c13, ['BarBody_r31c13']),
    ('k2_bar_regrows_from_hollow__BarBody_r31c14', _guard_k2_bar_regrows_from_hollow__BarBody_r31c14, _effect_k2_bar_regrows_from_hollow__BarBody_r31c14, ['BarBody_r31c14']),
    ('k2_bar_regrows_from_hollow__BarBody_r34c13', _guard_k2_bar_regrows_from_hollow__BarBody_r34c13, _effect_k2_bar_regrows_from_hollow__BarBody_r34c13, ['BarBody_r34c13']),
    ('k2_bar_regrows_from_hollow__BarBody_r34c14', _guard_k2_bar_regrows_from_hollow__BarBody_r34c14, _effect_k2_bar_regrows_from_hollow__BarBody_r34c14, ['BarBody_r34c14']),
    ('k2_bar_regrows_from_hollow__BarBody_r35c13', _guard_k2_bar_regrows_from_hollow__BarBody_r35c13, _effect_k2_bar_regrows_from_hollow__BarBody_r35c13, ['BarBody_r35c13']),
    ('k2_bar_regrows_from_hollow__BarBody_r35c14', _guard_k2_bar_regrows_from_hollow__BarBody_r35c14, _effect_k2_bar_regrows_from_hollow__BarBody_r35c14, ['BarBody_r35c14']),
    ('k2_bar_regrows_from_frame__BarBody_r30c13', _guard_k2_bar_regrows_from_frame__BarBody_r30c13, _effect_k2_bar_regrows_from_frame__BarBody_r30c13, ['BarBody_r30c13']),
    ('k2_bar_regrows_from_frame__BarBody_r30c14', _guard_k2_bar_regrows_from_frame__BarBody_r30c14, _effect_k2_bar_regrows_from_frame__BarBody_r30c14, ['BarBody_r30c14']),
    ('k2_bar_regrows_from_frame__BarBody_r31c13', _guard_k2_bar_regrows_from_frame__BarBody_r31c13, _effect_k2_bar_regrows_from_frame__BarBody_r31c13, ['BarBody_r31c13']),
    ('k2_bar_regrows_from_frame__BarBody_r31c14', _guard_k2_bar_regrows_from_frame__BarBody_r31c14, _effect_k2_bar_regrows_from_frame__BarBody_r31c14, ['BarBody_r31c14']),
    ('k2_bar_regrows_from_frame__BarBody_r34c13', _guard_k2_bar_regrows_from_frame__BarBody_r34c13, _effect_k2_bar_regrows_from_frame__BarBody_r34c13, ['BarBody_r34c13']),
    ('k2_bar_regrows_from_frame__BarBody_r34c14', _guard_k2_bar_regrows_from_frame__BarBody_r34c14, _effect_k2_bar_regrows_from_frame__BarBody_r34c14, ['BarBody_r34c14']),
    ('k2_bar_regrows_from_frame__BarBody_r35c13', _guard_k2_bar_regrows_from_frame__BarBody_r35c13, _effect_k2_bar_regrows_from_frame__BarBody_r35c13, ['BarBody_r35c13']),
    ('k2_bar_regrows_from_frame__BarBody_r35c14', _guard_k2_bar_regrows_from_frame__BarBody_r35c14, _effect_k2_bar_regrows_from_frame__BarBody_r35c14, ['BarBody_r35c14']),
    ('k2_core_from_frame__BarCore_r32c13', _guard_k2_core_from_frame__BarCore_r32c13, _effect_k2_core_from_frame__BarCore_r32c13, ['BarCore_r32c13']),
    ('k2_core_from_frame__BarCore_r32c14', _guard_k2_core_from_frame__BarCore_r32c14, _effect_k2_core_from_frame__BarCore_r32c14, ['BarCore_r32c14']),
    ('k2_core_from_frame__BarCore_r33c13', _guard_k2_core_from_frame__BarCore_r33c13, _effect_k2_core_from_frame__BarCore_r33c13, ['BarCore_r33c13']),
    ('k2_core_from_frame__BarCore_r33c14', _guard_k2_core_from_frame__BarCore_r33c14, _effect_k2_core_from_frame__BarCore_r33c14, ['BarCore_r33c14']),
    ('k2_core_from_frame__BarCore_r38c17', _guard_k2_core_from_frame__BarCore_r38c17, _effect_k2_core_from_frame__BarCore_r38c17, ['BarCore_r38c17']),
    ('k2_core_from_frame__BarCore_r38c20', _guard_k2_core_from_frame__BarCore_r38c20, _effect_k2_core_from_frame__BarCore_r38c20, ['BarCore_r38c20']),
    ('k2_core_from_frame__BarCore_r39c16', _guard_k2_core_from_frame__BarCore_r39c16, _effect_k2_core_from_frame__BarCore_r39c16, ['BarCore_r39c16']),
    ('k2_core_from_frame__BarCore_r39c19', _guard_k2_core_from_frame__BarCore_r39c19, _effect_k2_core_from_frame__BarCore_r39c19, ['BarCore_r39c19']),
    ('k2_core_from_frame__BarCore_r39c22', _guard_k2_core_from_frame__BarCore_r39c22, _effect_k2_core_from_frame__BarCore_r39c22, ['BarCore_r39c22']),
    ('k2_core_from_frame__BarCore_r53c59', _guard_k2_core_from_frame__BarCore_r53c59, _effect_k2_core_from_frame__BarCore_r53c59, ['BarCore_r53c59']),
    ('k2_core_from_frame__BarCore_r53c60', _guard_k2_core_from_frame__BarCore_r53c60, _effect_k2_core_from_frame__BarCore_r53c60, ['BarCore_r53c60']),
    ('k2_core_from_frame__BarCore_r53c61', _guard_k2_core_from_frame__BarCore_r53c61, _effect_k2_core_from_frame__BarCore_r53c61, ['BarCore_r53c61']),
    ('k2_core_from_frame__BarCore_r53c62', _guard_k2_core_from_frame__BarCore_r53c62, _effect_k2_core_from_frame__BarCore_r53c62, ['BarCore_r53c62']),
    ('k2_core_from_frame__BarCore_r53c63', _guard_k2_core_from_frame__BarCore_r53c63, _effect_k2_core_from_frame__BarCore_r53c63, ['BarCore_r53c63']),
    ('k2_blank_from_dot__Blank_r32c17', _guard_k2_blank_from_dot__Blank_r32c17, _effect_k2_blank_from_dot__Blank_r32c17, ['Blank_r32c17']),
    ('k2_blank_from_dot__Blank_r32c18', _guard_k2_blank_from_dot__Blank_r32c18, _effect_k2_blank_from_dot__Blank_r32c18, ['Blank_r32c18']),
    ('k2_blank_from_dot__Blank_r32c19', _guard_k2_blank_from_dot__Blank_r32c19, _effect_k2_blank_from_dot__Blank_r32c19, ['Blank_r32c19']),
    ('k2_blank_from_dot__Blank_r32c20', _guard_k2_blank_from_dot__Blank_r32c20, _effect_k2_blank_from_dot__Blank_r32c20, ['Blank_r32c20']),
    ('k2_blank_from_dot__Blank_r32c21', _guard_k2_blank_from_dot__Blank_r32c21, _effect_k2_blank_from_dot__Blank_r32c21, ['Blank_r32c21']),
    ('k2_blank_from_dot__Blank_r32c22', _guard_k2_blank_from_dot__Blank_r32c22, _effect_k2_blank_from_dot__Blank_r32c22, ['Blank_r32c22']),
    ('k2_blank_from_dot__Blank_r33c17', _guard_k2_blank_from_dot__Blank_r33c17, _effect_k2_blank_from_dot__Blank_r33c17, ['Blank_r33c17']),
    ('k2_blank_from_dot__Blank_r33c18', _guard_k2_blank_from_dot__Blank_r33c18, _effect_k2_blank_from_dot__Blank_r33c18, ['Blank_r33c18']),
    ('k2_blank_from_dot__Blank_r33c19', _guard_k2_blank_from_dot__Blank_r33c19, _effect_k2_blank_from_dot__Blank_r33c19, ['Blank_r33c19']),
    ('k2_blank_from_dot__Blank_r33c20', _guard_k2_blank_from_dot__Blank_r33c20, _effect_k2_blank_from_dot__Blank_r33c20, ['Blank_r33c20']),
    ('k2_blank_from_dot__Blank_r33c21', _guard_k2_blank_from_dot__Blank_r33c21, _effect_k2_blank_from_dot__Blank_r33c21, ['Blank_r33c21']),
    ('k2_blank_from_dot__Blank_r33c22', _guard_k2_blank_from_dot__Blank_r33c22, _effect_k2_blank_from_dot__Blank_r33c22, ['Blank_r33c22']),
    ('k2_blank_from_core__Blank_r32c17', _guard_k2_blank_from_core__Blank_r32c17, _effect_k2_blank_from_core__Blank_r32c17, ['Blank_r32c17']),
    ('k2_blank_from_core__Blank_r32c18', _guard_k2_blank_from_core__Blank_r32c18, _effect_k2_blank_from_core__Blank_r32c18, ['Blank_r32c18']),
    ('k2_blank_from_core__Blank_r32c19', _guard_k2_blank_from_core__Blank_r32c19, _effect_k2_blank_from_core__Blank_r32c19, ['Blank_r32c19']),
    ('k2_blank_from_core__Blank_r32c20', _guard_k2_blank_from_core__Blank_r32c20, _effect_k2_blank_from_core__Blank_r32c20, ['Blank_r32c20']),
    ('k2_blank_from_core__Blank_r32c21', _guard_k2_blank_from_core__Blank_r32c21, _effect_k2_blank_from_core__Blank_r32c21, ['Blank_r32c21']),
    ('k2_blank_from_core__Blank_r32c22', _guard_k2_blank_from_core__Blank_r32c22, _effect_k2_blank_from_core__Blank_r32c22, ['Blank_r32c22']),
    ('k2_blank_from_core__Blank_r33c17', _guard_k2_blank_from_core__Blank_r33c17, _effect_k2_blank_from_core__Blank_r33c17, ['Blank_r33c17']),
    ('k2_blank_from_core__Blank_r33c18', _guard_k2_blank_from_core__Blank_r33c18, _effect_k2_blank_from_core__Blank_r33c18, ['Blank_r33c18']),
    ('k2_blank_from_core__Blank_r33c19', _guard_k2_blank_from_core__Blank_r33c19, _effect_k2_blank_from_core__Blank_r33c19, ['Blank_r33c19']),
    ('k2_blank_from_core__Blank_r33c20', _guard_k2_blank_from_core__Blank_r33c20, _effect_k2_blank_from_core__Blank_r33c20, ['Blank_r33c20']),
    ('k2_blank_from_core__Blank_r33c21', _guard_k2_blank_from_core__Blank_r33c21, _effect_k2_blank_from_core__Blank_r33c21, ['Blank_r33c21']),
    ('k2_blank_from_core__Blank_r33c22', _guard_k2_blank_from_core__Blank_r33c22, _effect_k2_blank_from_core__Blank_r33c22, ['Blank_r33c22']),
    ('k2_frame_from_field__Frame_r36c11', _guard_k2_frame_from_field__Frame_r36c11, _effect_k2_frame_from_field__Frame_r36c11, ['Frame_r36c11']),
    ('k2_frame_from_field__Frame_r36c12', _guard_k2_frame_from_field__Frame_r36c12, _effect_k2_frame_from_field__Frame_r36c12, ['Frame_r36c12']),
    ('k2_frame_from_field__Frame_r36c13', _guard_k2_frame_from_field__Frame_r36c13, _effect_k2_frame_from_field__Frame_r36c13, ['Frame_r36c13']),
    ('k2_frame_from_field__Frame_r36c14', _guard_k2_frame_from_field__Frame_r36c14, _effect_k2_frame_from_field__Frame_r36c14, ['Frame_r36c14']),
    ('k2_frame_from_field__Frame_r36c15', _guard_k2_frame_from_field__Frame_r36c15, _effect_k2_frame_from_field__Frame_r36c15, ['Frame_r36c15']),
    ('k2_frame_from_field__Frame_r36c16', _guard_k2_frame_from_field__Frame_r36c16, _effect_k2_frame_from_field__Frame_r36c16, ['Frame_r36c16']),
    ('k2_frame_from_field__Frame_r37c11', _guard_k2_frame_from_field__Frame_r37c11, _effect_k2_frame_from_field__Frame_r37c11, ['Frame_r37c11']),
    ('k2_frame_from_field__Frame_r37c16', _guard_k2_frame_from_field__Frame_r37c16, _effect_k2_frame_from_field__Frame_r37c16, ['Frame_r37c16']),
    ('k2_frame_from_field__Frame_r38c11', _guard_k2_frame_from_field__Frame_r38c11, _effect_k2_frame_from_field__Frame_r38c11, ['Frame_r38c11']),
    ('k2_frame_from_field__Frame_r38c13', _guard_k2_frame_from_field__Frame_r38c13, _effect_k2_frame_from_field__Frame_r38c13, ['Frame_r38c13']),
    ('k2_frame_from_field__Frame_r38c14', _guard_k2_frame_from_field__Frame_r38c14, _effect_k2_frame_from_field__Frame_r38c14, ['Frame_r38c14']),
    ('k2_frame_from_field__Frame_r39c11', _guard_k2_frame_from_field__Frame_r39c11, _effect_k2_frame_from_field__Frame_r39c11, ['Frame_r39c11']),
    ('k2_frame_from_field__Frame_r39c13', _guard_k2_frame_from_field__Frame_r39c13, _effect_k2_frame_from_field__Frame_r39c13, ['Frame_r39c13']),
    ('k2_frame_from_field__Frame_r39c14', _guard_k2_frame_from_field__Frame_r39c14, _effect_k2_frame_from_field__Frame_r39c14, ['Frame_r39c14']),
    ('k2_frame_from_field__Frame_r40c11', _guard_k2_frame_from_field__Frame_r40c11, _effect_k2_frame_from_field__Frame_r40c11, ['Frame_r40c11']),
    ('k2_frame_from_field__Frame_r40c16', _guard_k2_frame_from_field__Frame_r40c16, _effect_k2_frame_from_field__Frame_r40c16, ['Frame_r40c16']),
    ('k2_frame_from_field__Frame_r41c11', _guard_k2_frame_from_field__Frame_r41c11, _effect_k2_frame_from_field__Frame_r41c11, ['Frame_r41c11']),
    ('k2_frame_from_field__Frame_r41c12', _guard_k2_frame_from_field__Frame_r41c12, _effect_k2_frame_from_field__Frame_r41c12, ['Frame_r41c12']),
    ('k2_frame_from_field__Frame_r41c13', _guard_k2_frame_from_field__Frame_r41c13, _effect_k2_frame_from_field__Frame_r41c13, ['Frame_r41c13']),
    ('k2_frame_from_field__Frame_r41c14', _guard_k2_frame_from_field__Frame_r41c14, _effect_k2_frame_from_field__Frame_r41c14, ['Frame_r41c14']),
    ('k2_frame_from_field__Frame_r41c15', _guard_k2_frame_from_field__Frame_r41c15, _effect_k2_frame_from_field__Frame_r41c15, ['Frame_r41c15']),
    ('k2_frame_from_field__Frame_r41c16', _guard_k2_frame_from_field__Frame_r41c16, _effect_k2_frame_from_field__Frame_r41c16, ['Frame_r41c16']),
    ('k2_frame_from_bar__Frame_r36c11', _guard_k2_frame_from_bar__Frame_r36c11, _effect_k2_frame_from_bar__Frame_r36c11, ['Frame_r36c11']),
    ('k2_frame_from_bar__Frame_r36c12', _guard_k2_frame_from_bar__Frame_r36c12, _effect_k2_frame_from_bar__Frame_r36c12, ['Frame_r36c12']),
    ('k2_frame_from_bar__Frame_r36c13', _guard_k2_frame_from_bar__Frame_r36c13, _effect_k2_frame_from_bar__Frame_r36c13, ['Frame_r36c13']),
    ('k2_frame_from_bar__Frame_r36c14', _guard_k2_frame_from_bar__Frame_r36c14, _effect_k2_frame_from_bar__Frame_r36c14, ['Frame_r36c14']),
    ('k2_frame_from_bar__Frame_r36c15', _guard_k2_frame_from_bar__Frame_r36c15, _effect_k2_frame_from_bar__Frame_r36c15, ['Frame_r36c15']),
    ('k2_frame_from_bar__Frame_r36c16', _guard_k2_frame_from_bar__Frame_r36c16, _effect_k2_frame_from_bar__Frame_r36c16, ['Frame_r36c16']),
    ('k2_frame_from_bar__Frame_r37c11', _guard_k2_frame_from_bar__Frame_r37c11, _effect_k2_frame_from_bar__Frame_r37c11, ['Frame_r37c11']),
    ('k2_frame_from_bar__Frame_r37c16', _guard_k2_frame_from_bar__Frame_r37c16, _effect_k2_frame_from_bar__Frame_r37c16, ['Frame_r37c16']),
    ('k2_frame_from_bar__Frame_r38c11', _guard_k2_frame_from_bar__Frame_r38c11, _effect_k2_frame_from_bar__Frame_r38c11, ['Frame_r38c11']),
    ('k2_frame_from_bar__Frame_r38c13', _guard_k2_frame_from_bar__Frame_r38c13, _effect_k2_frame_from_bar__Frame_r38c13, ['Frame_r38c13']),
    ('k2_frame_from_bar__Frame_r38c14', _guard_k2_frame_from_bar__Frame_r38c14, _effect_k2_frame_from_bar__Frame_r38c14, ['Frame_r38c14']),
    ('k2_frame_from_bar__Frame_r39c11', _guard_k2_frame_from_bar__Frame_r39c11, _effect_k2_frame_from_bar__Frame_r39c11, ['Frame_r39c11']),
    ('k2_frame_from_bar__Frame_r39c13', _guard_k2_frame_from_bar__Frame_r39c13, _effect_k2_frame_from_bar__Frame_r39c13, ['Frame_r39c13']),
    ('k2_frame_from_bar__Frame_r39c14', _guard_k2_frame_from_bar__Frame_r39c14, _effect_k2_frame_from_bar__Frame_r39c14, ['Frame_r39c14']),
    ('k2_frame_from_bar__Frame_r40c11', _guard_k2_frame_from_bar__Frame_r40c11, _effect_k2_frame_from_bar__Frame_r40c11, ['Frame_r40c11']),
    ('k2_frame_from_bar__Frame_r40c16', _guard_k2_frame_from_bar__Frame_r40c16, _effect_k2_frame_from_bar__Frame_r40c16, ['Frame_r40c16']),
    ('k2_frame_from_bar__Frame_r41c11', _guard_k2_frame_from_bar__Frame_r41c11, _effect_k2_frame_from_bar__Frame_r41c11, ['Frame_r41c11']),
    ('k2_frame_from_bar__Frame_r41c12', _guard_k2_frame_from_bar__Frame_r41c12, _effect_k2_frame_from_bar__Frame_r41c12, ['Frame_r41c12']),
    ('k2_frame_from_bar__Frame_r41c13', _guard_k2_frame_from_bar__Frame_r41c13, _effect_k2_frame_from_bar__Frame_r41c13, ['Frame_r41c13']),
    ('k2_frame_from_bar__Frame_r41c14', _guard_k2_frame_from_bar__Frame_r41c14, _effect_k2_frame_from_bar__Frame_r41c14, ['Frame_r41c14']),
    ('k2_frame_from_bar__Frame_r41c15', _guard_k2_frame_from_bar__Frame_r41c15, _effect_k2_frame_from_bar__Frame_r41c15, ['Frame_r41c15']),
    ('k2_frame_from_bar__Frame_r41c16', _guard_k2_frame_from_bar__Frame_r41c16, _effect_k2_frame_from_bar__Frame_r41c16, ['Frame_r41c16']),
    ('k2_frame_from_core__Frame_r36c11', _guard_k2_frame_from_core__Frame_r36c11, _effect_k2_frame_from_core__Frame_r36c11, ['Frame_r36c11']),
    ('k2_frame_from_core__Frame_r36c12', _guard_k2_frame_from_core__Frame_r36c12, _effect_k2_frame_from_core__Frame_r36c12, ['Frame_r36c12']),
    ('k2_frame_from_core__Frame_r36c13', _guard_k2_frame_from_core__Frame_r36c13, _effect_k2_frame_from_core__Frame_r36c13, ['Frame_r36c13']),
    ('k2_frame_from_core__Frame_r36c14', _guard_k2_frame_from_core__Frame_r36c14, _effect_k2_frame_from_core__Frame_r36c14, ['Frame_r36c14']),
    ('k2_frame_from_core__Frame_r36c15', _guard_k2_frame_from_core__Frame_r36c15, _effect_k2_frame_from_core__Frame_r36c15, ['Frame_r36c15']),
    ('k2_frame_from_core__Frame_r36c16', _guard_k2_frame_from_core__Frame_r36c16, _effect_k2_frame_from_core__Frame_r36c16, ['Frame_r36c16']),
    ('k2_frame_from_core__Frame_r37c11', _guard_k2_frame_from_core__Frame_r37c11, _effect_k2_frame_from_core__Frame_r37c11, ['Frame_r37c11']),
    ('k2_frame_from_core__Frame_r37c16', _guard_k2_frame_from_core__Frame_r37c16, _effect_k2_frame_from_core__Frame_r37c16, ['Frame_r37c16']),
    ('k2_frame_from_core__Frame_r38c11', _guard_k2_frame_from_core__Frame_r38c11, _effect_k2_frame_from_core__Frame_r38c11, ['Frame_r38c11']),
    ('k2_frame_from_core__Frame_r38c13', _guard_k2_frame_from_core__Frame_r38c13, _effect_k2_frame_from_core__Frame_r38c13, ['Frame_r38c13']),
    ('k2_frame_from_core__Frame_r38c14', _guard_k2_frame_from_core__Frame_r38c14, _effect_k2_frame_from_core__Frame_r38c14, ['Frame_r38c14']),
    ('k2_frame_from_core__Frame_r39c11', _guard_k2_frame_from_core__Frame_r39c11, _effect_k2_frame_from_core__Frame_r39c11, ['Frame_r39c11']),
    ('k2_frame_from_core__Frame_r39c13', _guard_k2_frame_from_core__Frame_r39c13, _effect_k2_frame_from_core__Frame_r39c13, ['Frame_r39c13']),
    ('k2_frame_from_core__Frame_r39c14', _guard_k2_frame_from_core__Frame_r39c14, _effect_k2_frame_from_core__Frame_r39c14, ['Frame_r39c14']),
    ('k2_frame_from_core__Frame_r40c11', _guard_k2_frame_from_core__Frame_r40c11, _effect_k2_frame_from_core__Frame_r40c11, ['Frame_r40c11']),
    ('k2_frame_from_core__Frame_r40c16', _guard_k2_frame_from_core__Frame_r40c16, _effect_k2_frame_from_core__Frame_r40c16, ['Frame_r40c16']),
    ('k2_frame_from_core__Frame_r41c11', _guard_k2_frame_from_core__Frame_r41c11, _effect_k2_frame_from_core__Frame_r41c11, ['Frame_r41c11']),
    ('k2_frame_from_core__Frame_r41c12', _guard_k2_frame_from_core__Frame_r41c12, _effect_k2_frame_from_core__Frame_r41c12, ['Frame_r41c12']),
    ('k2_frame_from_core__Frame_r41c13', _guard_k2_frame_from_core__Frame_r41c13, _effect_k2_frame_from_core__Frame_r41c13, ['Frame_r41c13']),
    ('k2_frame_from_core__Frame_r41c14', _guard_k2_frame_from_core__Frame_r41c14, _effect_k2_frame_from_core__Frame_r41c14, ['Frame_r41c14']),
    ('k2_frame_from_core__Frame_r41c15', _guard_k2_frame_from_core__Frame_r41c15, _effect_k2_frame_from_core__Frame_r41c15, ['Frame_r41c15']),
    ('k2_frame_from_core__Frame_r41c16', _guard_k2_frame_from_core__Frame_r41c16, _effect_k2_frame_from_core__Frame_r41c16, ['Frame_r41c16']),
    ('k2_hollow_from_field__Hollow_r37c12', _guard_k2_hollow_from_field__Hollow_r37c12, _effect_k2_hollow_from_field__Hollow_r37c12, ['Hollow_r37c12']),
    ('k2_hollow_from_field__Hollow_r37c13', _guard_k2_hollow_from_field__Hollow_r37c13, _effect_k2_hollow_from_field__Hollow_r37c13, ['Hollow_r37c13']),
    ('k2_hollow_from_field__Hollow_r37c14', _guard_k2_hollow_from_field__Hollow_r37c14, _effect_k2_hollow_from_field__Hollow_r37c14, ['Hollow_r37c14']),
    ('k2_hollow_from_field__Hollow_r37c15', _guard_k2_hollow_from_field__Hollow_r37c15, _effect_k2_hollow_from_field__Hollow_r37c15, ['Hollow_r37c15']),
    ('k2_hollow_from_field__Hollow_r38c12', _guard_k2_hollow_from_field__Hollow_r38c12, _effect_k2_hollow_from_field__Hollow_r38c12, ['Hollow_r38c12']),
    ('k2_hollow_from_field__Hollow_r38c15', _guard_k2_hollow_from_field__Hollow_r38c15, _effect_k2_hollow_from_field__Hollow_r38c15, ['Hollow_r38c15']),
    ('k2_hollow_from_field__Hollow_r39c12', _guard_k2_hollow_from_field__Hollow_r39c12, _effect_k2_hollow_from_field__Hollow_r39c12, ['Hollow_r39c12']),
    ('k2_hollow_from_field__Hollow_r39c15', _guard_k2_hollow_from_field__Hollow_r39c15, _effect_k2_hollow_from_field__Hollow_r39c15, ['Hollow_r39c15']),
    ('k2_hollow_from_field__Hollow_r40c12', _guard_k2_hollow_from_field__Hollow_r40c12, _effect_k2_hollow_from_field__Hollow_r40c12, ['Hollow_r40c12']),
    ('k2_hollow_from_field__Hollow_r40c13', _guard_k2_hollow_from_field__Hollow_r40c13, _effect_k2_hollow_from_field__Hollow_r40c13, ['Hollow_r40c13']),
    ('k2_hollow_from_field__Hollow_r40c14', _guard_k2_hollow_from_field__Hollow_r40c14, _effect_k2_hollow_from_field__Hollow_r40c14, ['Hollow_r40c14']),
    ('k2_hollow_from_field__Hollow_r40c15', _guard_k2_hollow_from_field__Hollow_r40c15, _effect_k2_hollow_from_field__Hollow_r40c15, ['Hollow_r40c15']),
    ('k2_hollow_from_bar__Hollow_r37c12', _guard_k2_hollow_from_bar__Hollow_r37c12, _effect_k2_hollow_from_bar__Hollow_r37c12, ['Hollow_r37c12']),
    ('k2_hollow_from_bar__Hollow_r37c13', _guard_k2_hollow_from_bar__Hollow_r37c13, _effect_k2_hollow_from_bar__Hollow_r37c13, ['Hollow_r37c13']),
    ('k2_hollow_from_bar__Hollow_r37c14', _guard_k2_hollow_from_bar__Hollow_r37c14, _effect_k2_hollow_from_bar__Hollow_r37c14, ['Hollow_r37c14']),
    ('k2_hollow_from_bar__Hollow_r37c15', _guard_k2_hollow_from_bar__Hollow_r37c15, _effect_k2_hollow_from_bar__Hollow_r37c15, ['Hollow_r37c15']),
    ('k2_hollow_from_bar__Hollow_r38c12', _guard_k2_hollow_from_bar__Hollow_r38c12, _effect_k2_hollow_from_bar__Hollow_r38c12, ['Hollow_r38c12']),
    ('k2_hollow_from_bar__Hollow_r38c15', _guard_k2_hollow_from_bar__Hollow_r38c15, _effect_k2_hollow_from_bar__Hollow_r38c15, ['Hollow_r38c15']),
    ('k2_hollow_from_bar__Hollow_r39c12', _guard_k2_hollow_from_bar__Hollow_r39c12, _effect_k2_hollow_from_bar__Hollow_r39c12, ['Hollow_r39c12']),
    ('k2_hollow_from_bar__Hollow_r39c15', _guard_k2_hollow_from_bar__Hollow_r39c15, _effect_k2_hollow_from_bar__Hollow_r39c15, ['Hollow_r39c15']),
    ('k2_hollow_from_bar__Hollow_r40c12', _guard_k2_hollow_from_bar__Hollow_r40c12, _effect_k2_hollow_from_bar__Hollow_r40c12, ['Hollow_r40c12']),
    ('k2_hollow_from_bar__Hollow_r40c13', _guard_k2_hollow_from_bar__Hollow_r40c13, _effect_k2_hollow_from_bar__Hollow_r40c13, ['Hollow_r40c13']),
    ('k2_hollow_from_bar__Hollow_r40c14', _guard_k2_hollow_from_bar__Hollow_r40c14, _effect_k2_hollow_from_bar__Hollow_r40c14, ['Hollow_r40c14']),
    ('k2_hollow_from_bar__Hollow_r40c15', _guard_k2_hollow_from_bar__Hollow_r40c15, _effect_k2_hollow_from_bar__Hollow_r40c15, ['Hollow_r40c15']),
    ('k2_dot_from_field__Dot_r38c16', _guard_k2_dot_from_field__Dot_r38c16, _effect_k2_dot_from_field__Dot_r38c16, ['Dot_r38c16']),
    ('k2_dot_from_field__Dot_r38c18', _guard_k2_dot_from_field__Dot_r38c18, _effect_k2_dot_from_field__Dot_r38c18, ['Dot_r38c18']),
    ('k2_dot_from_field__Dot_r38c19', _guard_k2_dot_from_field__Dot_r38c19, _effect_k2_dot_from_field__Dot_r38c19, ['Dot_r38c19']),
    ('k2_dot_from_field__Dot_r38c21', _guard_k2_dot_from_field__Dot_r38c21, _effect_k2_dot_from_field__Dot_r38c21, ['Dot_r38c21']),
    ('k2_dot_from_field__Dot_r38c22', _guard_k2_dot_from_field__Dot_r38c22, _effect_k2_dot_from_field__Dot_r38c22, ['Dot_r38c22']),
    ('k2_dot_from_field__Dot_r39c17', _guard_k2_dot_from_field__Dot_r39c17, _effect_k2_dot_from_field__Dot_r39c17, ['Dot_r39c17']),
    ('k2_dot_from_field__Dot_r39c18', _guard_k2_dot_from_field__Dot_r39c18, _effect_k2_dot_from_field__Dot_r39c18, ['Dot_r39c18']),
    ('k2_dot_from_field__Dot_r39c20', _guard_k2_dot_from_field__Dot_r39c20, _effect_k2_dot_from_field__Dot_r39c20, ['Dot_r39c20']),
    ('k2_dot_from_field__Dot_r39c21', _guard_k2_dot_from_field__Dot_r39c21, _effect_k2_dot_from_field__Dot_r39c21, ['Dot_r39c21']),
    ('k2_dot_from_blank__Dot_r38c16', _guard_k2_dot_from_blank__Dot_r38c16, _effect_k2_dot_from_blank__Dot_r38c16, ['Dot_r38c16']),
    ('k2_dot_from_blank__Dot_r38c18', _guard_k2_dot_from_blank__Dot_r38c18, _effect_k2_dot_from_blank__Dot_r38c18, ['Dot_r38c18']),
    ('k2_dot_from_blank__Dot_r38c19', _guard_k2_dot_from_blank__Dot_r38c19, _effect_k2_dot_from_blank__Dot_r38c19, ['Dot_r38c19']),
    ('k2_dot_from_blank__Dot_r38c21', _guard_k2_dot_from_blank__Dot_r38c21, _effect_k2_dot_from_blank__Dot_r38c21, ['Dot_r38c21']),
    ('k2_dot_from_blank__Dot_r38c22', _guard_k2_dot_from_blank__Dot_r38c22, _effect_k2_dot_from_blank__Dot_r38c22, ['Dot_r38c22']),
    ('k2_dot_from_blank__Dot_r39c17', _guard_k2_dot_from_blank__Dot_r39c17, _effect_k2_dot_from_blank__Dot_r39c17, ['Dot_r39c17']),
    ('k2_dot_from_blank__Dot_r39c18', _guard_k2_dot_from_blank__Dot_r39c18, _effect_k2_dot_from_blank__Dot_r39c18, ['Dot_r39c18']),
    ('k2_dot_from_blank__Dot_r39c20', _guard_k2_dot_from_blank__Dot_r39c20, _effect_k2_dot_from_blank__Dot_r39c20, ['Dot_r39c20']),
    ('k2_dot_from_blank__Dot_r39c21', _guard_k2_dot_from_blank__Dot_r39c21, _effect_k2_dot_from_blank__Dot_r39c21, ['Dot_r39c21']),
    ('k2_core_from_field__BarCore_r32c13', _guard_k2_core_from_field__BarCore_r32c13, _effect_k2_core_from_field__BarCore_r32c13, ['BarCore_r32c13']),
    ('k2_core_from_field__BarCore_r32c14', _guard_k2_core_from_field__BarCore_r32c14, _effect_k2_core_from_field__BarCore_r32c14, ['BarCore_r32c14']),
    ('k2_core_from_field__BarCore_r33c13', _guard_k2_core_from_field__BarCore_r33c13, _effect_k2_core_from_field__BarCore_r33c13, ['BarCore_r33c13']),
    ('k2_core_from_field__BarCore_r33c14', _guard_k2_core_from_field__BarCore_r33c14, _effect_k2_core_from_field__BarCore_r33c14, ['BarCore_r33c14']),
    ('k2_core_from_field__BarCore_r38c17', _guard_k2_core_from_field__BarCore_r38c17, _effect_k2_core_from_field__BarCore_r38c17, ['BarCore_r38c17']),
    ('k2_core_from_field__BarCore_r38c20', _guard_k2_core_from_field__BarCore_r38c20, _effect_k2_core_from_field__BarCore_r38c20, ['BarCore_r38c20']),
    ('k2_core_from_field__BarCore_r39c16', _guard_k2_core_from_field__BarCore_r39c16, _effect_k2_core_from_field__BarCore_r39c16, ['BarCore_r39c16']),
    ('k2_core_from_field__BarCore_r39c19', _guard_k2_core_from_field__BarCore_r39c19, _effect_k2_core_from_field__BarCore_r39c19, ['BarCore_r39c19']),
    ('k2_core_from_field__BarCore_r39c22', _guard_k2_core_from_field__BarCore_r39c22, _effect_k2_core_from_field__BarCore_r39c22, ['BarCore_r39c22']),
    ('k2_core_from_field__BarCore_r53c59', _guard_k2_core_from_field__BarCore_r53c59, _effect_k2_core_from_field__BarCore_r53c59, ['BarCore_r53c59']),
    ('k2_core_from_field__BarCore_r53c60', _guard_k2_core_from_field__BarCore_r53c60, _effect_k2_core_from_field__BarCore_r53c60, ['BarCore_r53c60']),
    ('k2_core_from_field__BarCore_r53c61', _guard_k2_core_from_field__BarCore_r53c61, _effect_k2_core_from_field__BarCore_r53c61, ['BarCore_r53c61']),
    ('k2_core_from_field__BarCore_r53c62', _guard_k2_core_from_field__BarCore_r53c62, _effect_k2_core_from_field__BarCore_r53c62, ['BarCore_r53c62']),
    ('k2_core_from_field__BarCore_r53c63', _guard_k2_core_from_field__BarCore_r53c63, _effect_k2_core_from_field__BarCore_r53c63, ['BarCore_r53c63']),
    ('k2_core_from_blank__BarCore_r32c13', _guard_k2_core_from_blank__BarCore_r32c13, _effect_k2_core_from_blank__BarCore_r32c13, ['BarCore_r32c13']),
    ('k2_core_from_blank__BarCore_r32c14', _guard_k2_core_from_blank__BarCore_r32c14, _effect_k2_core_from_blank__BarCore_r32c14, ['BarCore_r32c14']),
    ('k2_core_from_blank__BarCore_r33c13', _guard_k2_core_from_blank__BarCore_r33c13, _effect_k2_core_from_blank__BarCore_r33c13, ['BarCore_r33c13']),
    ('k2_core_from_blank__BarCore_r33c14', _guard_k2_core_from_blank__BarCore_r33c14, _effect_k2_core_from_blank__BarCore_r33c14, ['BarCore_r33c14']),
    ('k2_core_from_blank__BarCore_r38c17', _guard_k2_core_from_blank__BarCore_r38c17, _effect_k2_core_from_blank__BarCore_r38c17, ['BarCore_r38c17']),
    ('k2_core_from_blank__BarCore_r38c20', _guard_k2_core_from_blank__BarCore_r38c20, _effect_k2_core_from_blank__BarCore_r38c20, ['BarCore_r38c20']),
    ('k2_core_from_blank__BarCore_r39c16', _guard_k2_core_from_blank__BarCore_r39c16, _effect_k2_core_from_blank__BarCore_r39c16, ['BarCore_r39c16']),
    ('k2_core_from_blank__BarCore_r39c19', _guard_k2_core_from_blank__BarCore_r39c19, _effect_k2_core_from_blank__BarCore_r39c19, ['BarCore_r39c19']),
    ('k2_core_from_blank__BarCore_r39c22', _guard_k2_core_from_blank__BarCore_r39c22, _effect_k2_core_from_blank__BarCore_r39c22, ['BarCore_r39c22']),
    ('k2_core_from_blank__BarCore_r53c59', _guard_k2_core_from_blank__BarCore_r53c59, _effect_k2_core_from_blank__BarCore_r53c59, ['BarCore_r53c59']),
    ('k2_core_from_blank__BarCore_r53c60', _guard_k2_core_from_blank__BarCore_r53c60, _effect_k2_core_from_blank__BarCore_r53c60, ['BarCore_r53c60']),
    ('k2_core_from_blank__BarCore_r53c61', _guard_k2_core_from_blank__BarCore_r53c61, _effect_k2_core_from_blank__BarCore_r53c61, ['BarCore_r53c61']),
    ('k2_core_from_blank__BarCore_r53c62', _guard_k2_core_from_blank__BarCore_r53c62, _effect_k2_core_from_blank__BarCore_r53c62, ['BarCore_r53c62']),
    ('k2_core_from_blank__BarCore_r53c63', _guard_k2_core_from_blank__BarCore_r53c63, _effect_k2_core_from_blank__BarCore_r53c63, ['BarCore_r53c63']),
    ('k3_dot_blanks__Dot_r38c16', _guard_k3_dot_blanks__Dot_r38c16, _effect_k3_dot_blanks__Dot_r38c16, ['Dot_r38c16']),
    ('k3_dot_blanks__Dot_r38c18', _guard_k3_dot_blanks__Dot_r38c18, _effect_k3_dot_blanks__Dot_r38c18, ['Dot_r38c18']),
    ('k3_dot_blanks__Dot_r38c19', _guard_k3_dot_blanks__Dot_r38c19, _effect_k3_dot_blanks__Dot_r38c19, ['Dot_r38c19']),
    ('k3_dot_blanks__Dot_r38c21', _guard_k3_dot_blanks__Dot_r38c21, _effect_k3_dot_blanks__Dot_r38c21, ['Dot_r38c21']),
    ('k3_dot_blanks__Dot_r38c22', _guard_k3_dot_blanks__Dot_r38c22, _effect_k3_dot_blanks__Dot_r38c22, ['Dot_r38c22']),
    ('k3_dot_blanks__Dot_r39c17', _guard_k3_dot_blanks__Dot_r39c17, _effect_k3_dot_blanks__Dot_r39c17, ['Dot_r39c17']),
    ('k3_dot_blanks__Dot_r39c18', _guard_k3_dot_blanks__Dot_r39c18, _effect_k3_dot_blanks__Dot_r39c18, ['Dot_r39c18']),
    ('k3_dot_blanks__Dot_r39c20', _guard_k3_dot_blanks__Dot_r39c20, _effect_k3_dot_blanks__Dot_r39c20, ['Dot_r39c20']),
    ('k3_dot_blanks__Dot_r39c21', _guard_k3_dot_blanks__Dot_r39c21, _effect_k3_dot_blanks__Dot_r39c21, ['Dot_r39c21']),
    ('k3_core_blanks__BarCore_r32c13', _guard_k3_core_blanks__BarCore_r32c13, _effect_k3_core_blanks__BarCore_r32c13, ['BarCore_r32c13']),
    ('k3_core_blanks__BarCore_r32c14', _guard_k3_core_blanks__BarCore_r32c14, _effect_k3_core_blanks__BarCore_r32c14, ['BarCore_r32c14']),
    ('k3_core_blanks__BarCore_r33c13', _guard_k3_core_blanks__BarCore_r33c13, _effect_k3_core_blanks__BarCore_r33c13, ['BarCore_r33c13']),
    ('k3_core_blanks__BarCore_r33c14', _guard_k3_core_blanks__BarCore_r33c14, _effect_k3_core_blanks__BarCore_r33c14, ['BarCore_r33c14']),
    ('k3_core_blanks__BarCore_r38c17', _guard_k3_core_blanks__BarCore_r38c17, _effect_k3_core_blanks__BarCore_r38c17, ['BarCore_r38c17']),
    ('k3_core_blanks__BarCore_r38c20', _guard_k3_core_blanks__BarCore_r38c20, _effect_k3_core_blanks__BarCore_r38c20, ['BarCore_r38c20']),
    ('k3_core_blanks__BarCore_r39c16', _guard_k3_core_blanks__BarCore_r39c16, _effect_k3_core_blanks__BarCore_r39c16, ['BarCore_r39c16']),
    ('k3_core_blanks__BarCore_r39c19', _guard_k3_core_blanks__BarCore_r39c19, _effect_k3_core_blanks__BarCore_r39c19, ['BarCore_r39c19']),
    ('k3_core_blanks__BarCore_r39c22', _guard_k3_core_blanks__BarCore_r39c22, _effect_k3_core_blanks__BarCore_r39c22, ['BarCore_r39c22']),
    ('k3_core_blanks__BarCore_r53c59', _guard_k3_core_blanks__BarCore_r53c59, _effect_k3_core_blanks__BarCore_r53c59, ['BarCore_r53c59']),
    ('k3_core_blanks__BarCore_r53c60', _guard_k3_core_blanks__BarCore_r53c60, _effect_k3_core_blanks__BarCore_r53c60, ['BarCore_r53c60']),
    ('k3_core_blanks__BarCore_r53c61', _guard_k3_core_blanks__BarCore_r53c61, _effect_k3_core_blanks__BarCore_r53c61, ['BarCore_r53c61']),
    ('k3_core_blanks__BarCore_r53c62', _guard_k3_core_blanks__BarCore_r53c62, _effect_k3_core_blanks__BarCore_r53c62, ['BarCore_r53c62']),
    ('k3_core_blanks__BarCore_r53c63', _guard_k3_core_blanks__BarCore_r53c63, _effect_k3_core_blanks__BarCore_r53c63, ['BarCore_r53c63']),
    ('k4_dot_lights__Dot_r38c16', _guard_k4_dot_lights__Dot_r38c16, _effect_k4_dot_lights__Dot_r38c16, ['Dot_r38c16']),
    ('k4_dot_lights__Dot_r38c18', _guard_k4_dot_lights__Dot_r38c18, _effect_k4_dot_lights__Dot_r38c18, ['Dot_r38c18']),
    ('k4_dot_lights__Dot_r38c19', _guard_k4_dot_lights__Dot_r38c19, _effect_k4_dot_lights__Dot_r38c19, ['Dot_r38c19']),
    ('k4_dot_lights__Dot_r38c21', _guard_k4_dot_lights__Dot_r38c21, _effect_k4_dot_lights__Dot_r38c21, ['Dot_r38c21']),
    ('k4_dot_lights__Dot_r38c22', _guard_k4_dot_lights__Dot_r38c22, _effect_k4_dot_lights__Dot_r38c22, ['Dot_r38c22']),
    ('k4_dot_lights__Dot_r39c17', _guard_k4_dot_lights__Dot_r39c17, _effect_k4_dot_lights__Dot_r39c17, ['Dot_r39c17']),
    ('k4_dot_lights__Dot_r39c18', _guard_k4_dot_lights__Dot_r39c18, _effect_k4_dot_lights__Dot_r39c18, ['Dot_r39c18']),
    ('k4_dot_lights__Dot_r39c20', _guard_k4_dot_lights__Dot_r39c20, _effect_k4_dot_lights__Dot_r39c20, ['Dot_r39c20']),
    ('k4_dot_lights__Dot_r39c21', _guard_k4_dot_lights__Dot_r39c21, _effect_k4_dot_lights__Dot_r39c21, ['Dot_r39c21']),
    ('k4_core_lights__BarCore_r32c13', _guard_k4_core_lights__BarCore_r32c13, _effect_k4_core_lights__BarCore_r32c13, ['BarCore_r32c13']),
    ('k4_core_lights__BarCore_r32c14', _guard_k4_core_lights__BarCore_r32c14, _effect_k4_core_lights__BarCore_r32c14, ['BarCore_r32c14']),
    ('k4_core_lights__BarCore_r33c13', _guard_k4_core_lights__BarCore_r33c13, _effect_k4_core_lights__BarCore_r33c13, ['BarCore_r33c13']),
    ('k4_core_lights__BarCore_r33c14', _guard_k4_core_lights__BarCore_r33c14, _effect_k4_core_lights__BarCore_r33c14, ['BarCore_r33c14']),
    ('k4_core_lights__BarCore_r38c17', _guard_k4_core_lights__BarCore_r38c17, _effect_k4_core_lights__BarCore_r38c17, ['BarCore_r38c17']),
    ('k4_core_lights__BarCore_r38c20', _guard_k4_core_lights__BarCore_r38c20, _effect_k4_core_lights__BarCore_r38c20, ['BarCore_r38c20']),
    ('k4_core_lights__BarCore_r39c16', _guard_k4_core_lights__BarCore_r39c16, _effect_k4_core_lights__BarCore_r39c16, ['BarCore_r39c16']),
    ('k4_core_lights__BarCore_r39c19', _guard_k4_core_lights__BarCore_r39c19, _effect_k4_core_lights__BarCore_r39c19, ['BarCore_r39c19']),
    ('k4_core_lights__BarCore_r39c22', _guard_k4_core_lights__BarCore_r39c22, _effect_k4_core_lights__BarCore_r39c22, ['BarCore_r39c22']),
    ('k4_core_lights__BarCore_r53c59', _guard_k4_core_lights__BarCore_r53c59, _effect_k4_core_lights__BarCore_r53c59, ['BarCore_r53c59']),
    ('k4_core_lights__BarCore_r53c60', _guard_k4_core_lights__BarCore_r53c60, _effect_k4_core_lights__BarCore_r53c60, ['BarCore_r53c60']),
    ('k4_core_lights__BarCore_r53c61', _guard_k4_core_lights__BarCore_r53c61, _effect_k4_core_lights__BarCore_r53c61, ['BarCore_r53c61']),
    ('k4_core_lights__BarCore_r53c62', _guard_k4_core_lights__BarCore_r53c62, _effect_k4_core_lights__BarCore_r53c62, ['BarCore_r53c62']),
    ('k4_core_lights__BarCore_r53c63', _guard_k4_core_lights__BarCore_r53c63, _effect_k4_core_lights__BarCore_r53c63, ['BarCore_r53c63']),
    ('meter_first_tick_replay_patch__BarCore_r32c13', _guard_meter_first_tick_replay_patch__BarCore_r32c13, _effect_meter_first_tick_replay_patch__BarCore_r32c13, ['BarCore_r32c13']),
    ('meter_first_tick_replay_patch__BarCore_r32c14', _guard_meter_first_tick_replay_patch__BarCore_r32c14, _effect_meter_first_tick_replay_patch__BarCore_r32c14, ['BarCore_r32c14']),
    ('meter_first_tick_replay_patch__BarCore_r33c13', _guard_meter_first_tick_replay_patch__BarCore_r33c13, _effect_meter_first_tick_replay_patch__BarCore_r33c13, ['BarCore_r33c13']),
    ('meter_first_tick_replay_patch__BarCore_r33c14', _guard_meter_first_tick_replay_patch__BarCore_r33c14, _effect_meter_first_tick_replay_patch__BarCore_r33c14, ['BarCore_r33c14']),
    ('meter_first_tick_replay_patch__BarCore_r38c17', _guard_meter_first_tick_replay_patch__BarCore_r38c17, _effect_meter_first_tick_replay_patch__BarCore_r38c17, ['BarCore_r38c17']),
    ('meter_first_tick_replay_patch__BarCore_r38c20', _guard_meter_first_tick_replay_patch__BarCore_r38c20, _effect_meter_first_tick_replay_patch__BarCore_r38c20, ['BarCore_r38c20']),
    ('meter_first_tick_replay_patch__BarCore_r39c16', _guard_meter_first_tick_replay_patch__BarCore_r39c16, _effect_meter_first_tick_replay_patch__BarCore_r39c16, ['BarCore_r39c16']),
    ('meter_first_tick_replay_patch__BarCore_r39c19', _guard_meter_first_tick_replay_patch__BarCore_r39c19, _effect_meter_first_tick_replay_patch__BarCore_r39c19, ['BarCore_r39c19']),
    ('meter_first_tick_replay_patch__BarCore_r39c22', _guard_meter_first_tick_replay_patch__BarCore_r39c22, _effect_meter_first_tick_replay_patch__BarCore_r39c22, ['BarCore_r39c22']),
    ('meter_first_tick_replay_patch__BarCore_r53c59', _guard_meter_first_tick_replay_patch__BarCore_r53c59, _effect_meter_first_tick_replay_patch__BarCore_r53c59, ['BarCore_r53c59']),
    ('meter_first_tick_replay_patch__BarCore_r53c60', _guard_meter_first_tick_replay_patch__BarCore_r53c60, _effect_meter_first_tick_replay_patch__BarCore_r53c60, ['BarCore_r53c60']),
    ('meter_first_tick_replay_patch__BarCore_r53c61', _guard_meter_first_tick_replay_patch__BarCore_r53c61, _effect_meter_first_tick_replay_patch__BarCore_r53c61, ['BarCore_r53c61']),
    ('meter_first_tick_replay_patch__BarCore_r53c62', _guard_meter_first_tick_replay_patch__BarCore_r53c62, _effect_meter_first_tick_replay_patch__BarCore_r53c62, ['BarCore_r53c62']),
    ('meter_first_tick_replay_patch__BarCore_r53c63', _guard_meter_first_tick_replay_patch__BarCore_r53c63, _effect_meter_first_tick_replay_patch__BarCore_r53c63, ['BarCore_r53c63']),
    ('k7_dot_blanks__Dot_r38c16', _guard_k7_dot_blanks__Dot_r38c16, _effect_k7_dot_blanks__Dot_r38c16, ['Dot_r38c16']),
    ('k7_dot_blanks__Dot_r38c18', _guard_k7_dot_blanks__Dot_r38c18, _effect_k7_dot_blanks__Dot_r38c18, ['Dot_r38c18']),
    ('k7_dot_blanks__Dot_r38c19', _guard_k7_dot_blanks__Dot_r38c19, _effect_k7_dot_blanks__Dot_r38c19, ['Dot_r38c19']),
    ('k7_dot_blanks__Dot_r38c21', _guard_k7_dot_blanks__Dot_r38c21, _effect_k7_dot_blanks__Dot_r38c21, ['Dot_r38c21']),
    ('k7_dot_blanks__Dot_r38c22', _guard_k7_dot_blanks__Dot_r38c22, _effect_k7_dot_blanks__Dot_r38c22, ['Dot_r38c22']),
    ('k7_dot_blanks__Dot_r39c17', _guard_k7_dot_blanks__Dot_r39c17, _effect_k7_dot_blanks__Dot_r39c17, ['Dot_r39c17']),
    ('k7_dot_blanks__Dot_r39c18', _guard_k7_dot_blanks__Dot_r39c18, _effect_k7_dot_blanks__Dot_r39c18, ['Dot_r39c18']),
    ('k7_dot_blanks__Dot_r39c20', _guard_k7_dot_blanks__Dot_r39c20, _effect_k7_dot_blanks__Dot_r39c20, ['Dot_r39c20']),
    ('k7_dot_blanks__Dot_r39c21', _guard_k7_dot_blanks__Dot_r39c21, _effect_k7_dot_blanks__Dot_r39c21, ['Dot_r39c21']),
    ('k7_core_blanks__BarCore_r32c13', _guard_k7_core_blanks__BarCore_r32c13, _effect_k7_core_blanks__BarCore_r32c13, ['BarCore_r32c13']),
    ('k7_core_blanks__BarCore_r32c14', _guard_k7_core_blanks__BarCore_r32c14, _effect_k7_core_blanks__BarCore_r32c14, ['BarCore_r32c14']),
    ('k7_core_blanks__BarCore_r33c13', _guard_k7_core_blanks__BarCore_r33c13, _effect_k7_core_blanks__BarCore_r33c13, ['BarCore_r33c13']),
    ('k7_core_blanks__BarCore_r33c14', _guard_k7_core_blanks__BarCore_r33c14, _effect_k7_core_blanks__BarCore_r33c14, ['BarCore_r33c14']),
    ('k7_core_blanks__BarCore_r38c17', _guard_k7_core_blanks__BarCore_r38c17, _effect_k7_core_blanks__BarCore_r38c17, ['BarCore_r38c17']),
    ('k7_core_blanks__BarCore_r38c20', _guard_k7_core_blanks__BarCore_r38c20, _effect_k7_core_blanks__BarCore_r38c20, ['BarCore_r38c20']),
    ('k7_core_blanks__BarCore_r39c16', _guard_k7_core_blanks__BarCore_r39c16, _effect_k7_core_blanks__BarCore_r39c16, ['BarCore_r39c16']),
    ('k7_core_blanks__BarCore_r39c19', _guard_k7_core_blanks__BarCore_r39c19, _effect_k7_core_blanks__BarCore_r39c19, ['BarCore_r39c19']),
    ('k7_core_blanks__BarCore_r39c22', _guard_k7_core_blanks__BarCore_r39c22, _effect_k7_core_blanks__BarCore_r39c22, ['BarCore_r39c22']),
    ('k7_core_blanks__BarCore_r53c59', _guard_k7_core_blanks__BarCore_r53c59, _effect_k7_core_blanks__BarCore_r53c59, ['BarCore_r53c59']),
    ('k7_core_blanks__BarCore_r53c60', _guard_k7_core_blanks__BarCore_r53c60, _effect_k7_core_blanks__BarCore_r53c60, ['BarCore_r53c60']),
    ('k7_core_blanks__BarCore_r53c61', _guard_k7_core_blanks__BarCore_r53c61, _effect_k7_core_blanks__BarCore_r53c61, ['BarCore_r53c61']),
    ('k7_core_blanks__BarCore_r53c62', _guard_k7_core_blanks__BarCore_r53c62, _effect_k7_core_blanks__BarCore_r53c62, ['BarCore_r53c62']),
    ('k7_core_blanks__BarCore_r53c63', _guard_k7_core_blanks__BarCore_r53c63, _effect_k7_core_blanks__BarCore_r53c63, ['BarCore_r53c63']),
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
        Field_r30c11_pos=(30, 11),
        Field_r30c11_color=5,
        Field_r30c12_pos=(30, 12),
        Field_r30c12_color=5,
        Field_r30c15_pos=(30, 15),
        Field_r30c15_color=5,
        Field_r30c16_pos=(30, 16),
        Field_r30c16_color=5,
        Field_r31c11_pos=(31, 11),
        Field_r31c11_color=5,
        Field_r31c12_pos=(31, 12),
        Field_r31c12_color=5,
        Field_r31c15_pos=(31, 15),
        Field_r31c15_color=5,
        Field_r31c16_pos=(31, 16),
        Field_r31c16_color=5,
        Field_r32c11_pos=(32, 11),
        Field_r32c11_color=5,
        Field_r32c12_pos=(32, 12),
        Field_r32c12_color=5,
        Field_r32c15_pos=(32, 15),
        Field_r32c15_color=5,
        Field_r32c16_pos=(32, 16),
        Field_r32c16_color=5,
        Field_r33c11_pos=(33, 11),
        Field_r33c11_color=5,
        Field_r33c12_pos=(33, 12),
        Field_r33c12_color=5,
        Field_r33c15_pos=(33, 15),
        Field_r33c15_color=5,
        Field_r33c16_pos=(33, 16),
        Field_r33c16_color=5,
        Field_r34c11_pos=(34, 11),
        Field_r34c11_color=5,
        Field_r34c12_pos=(34, 12),
        Field_r34c12_color=5,
        Field_r34c15_pos=(34, 15),
        Field_r34c15_color=5,
        Field_r34c16_pos=(34, 16),
        Field_r34c16_color=5,
        Field_r35c11_pos=(35, 11),
        Field_r35c11_color=5,
        Field_r35c12_pos=(35, 12),
        Field_r35c12_color=5,
        Field_r35c15_pos=(35, 15),
        Field_r35c15_color=5,
        Field_r35c16_pos=(35, 16),
        Field_r35c16_color=5,
        BarBody_r30c13_pos=(30, 13),
        BarBody_r30c13_color=3,
        BarBody_r30c14_pos=(30, 14),
        BarBody_r30c14_color=3,
        BarBody_r31c13_pos=(31, 13),
        BarBody_r31c13_color=3,
        BarBody_r31c14_pos=(31, 14),
        BarBody_r31c14_color=3,
        BarBody_r34c13_pos=(34, 13),
        BarBody_r34c13_color=3,
        BarBody_r34c14_pos=(34, 14),
        BarBody_r34c14_color=3,
        BarBody_r35c13_pos=(35, 13),
        BarBody_r35c13_color=3,
        BarBody_r35c14_pos=(35, 14),
        BarBody_r35c14_color=3,
        BarCore_r32c13_pos=(32, 13),
        BarCore_r32c13_color=2,
        BarCore_r32c14_pos=(32, 14),
        BarCore_r32c14_color=2,
        BarCore_r33c13_pos=(33, 13),
        BarCore_r33c13_color=2,
        BarCore_r33c14_pos=(33, 14),
        BarCore_r33c14_color=2,
        BarCore_r38c17_pos=(38, 17),
        BarCore_r38c17_color=2,
        BarCore_r38c20_pos=(38, 20),
        BarCore_r38c20_color=2,
        BarCore_r39c16_pos=(39, 16),
        BarCore_r39c16_color=2,
        BarCore_r39c19_pos=(39, 19),
        BarCore_r39c19_color=2,
        BarCore_r39c22_pos=(39, 22),
        BarCore_r39c22_color=2,
        BarCore_r53c59_pos=(53, 59),
        BarCore_r53c59_color=2,
        BarCore_r53c60_pos=(53, 60),
        BarCore_r53c60_color=2,
        BarCore_r53c61_pos=(53, 61),
        BarCore_r53c61_color=2,
        BarCore_r53c62_pos=(53, 62),
        BarCore_r53c62_color=2,
        BarCore_r53c63_pos=(53, 63),
        BarCore_r53c63_color=2,
        Blank_r32c17_pos=(32, 17),
        Blank_r32c17_color=4,
        Blank_r32c18_pos=(32, 18),
        Blank_r32c18_color=4,
        Blank_r32c19_pos=(32, 19),
        Blank_r32c19_color=4,
        Blank_r32c20_pos=(32, 20),
        Blank_r32c20_color=4,
        Blank_r32c21_pos=(32, 21),
        Blank_r32c21_color=4,
        Blank_r32c22_pos=(32, 22),
        Blank_r32c22_color=4,
        Blank_r33c17_pos=(33, 17),
        Blank_r33c17_color=4,
        Blank_r33c18_pos=(33, 18),
        Blank_r33c18_color=4,
        Blank_r33c19_pos=(33, 19),
        Blank_r33c19_color=4,
        Blank_r33c20_pos=(33, 20),
        Blank_r33c20_color=4,
        Blank_r33c21_pos=(33, 21),
        Blank_r33c21_color=4,
        Blank_r33c22_pos=(33, 22),
        Blank_r33c22_color=4,
        Frame_r36c11_pos=(36, 11),
        Frame_r36c11_color=6,
        Frame_r36c12_pos=(36, 12),
        Frame_r36c12_color=6,
        Frame_r36c13_pos=(36, 13),
        Frame_r36c13_color=6,
        Frame_r36c14_pos=(36, 14),
        Frame_r36c14_color=6,
        Frame_r36c15_pos=(36, 15),
        Frame_r36c15_color=6,
        Frame_r36c16_pos=(36, 16),
        Frame_r36c16_color=6,
        Frame_r37c11_pos=(37, 11),
        Frame_r37c11_color=6,
        Frame_r37c16_pos=(37, 16),
        Frame_r37c16_color=6,
        Frame_r38c11_pos=(38, 11),
        Frame_r38c11_color=6,
        Frame_r38c13_pos=(38, 13),
        Frame_r38c13_color=6,
        Frame_r38c14_pos=(38, 14),
        Frame_r38c14_color=6,
        Frame_r39c11_pos=(39, 11),
        Frame_r39c11_color=6,
        Frame_r39c13_pos=(39, 13),
        Frame_r39c13_color=6,
        Frame_r39c14_pos=(39, 14),
        Frame_r39c14_color=6,
        Frame_r40c11_pos=(40, 11),
        Frame_r40c11_color=6,
        Frame_r40c16_pos=(40, 16),
        Frame_r40c16_color=6,
        Frame_r41c11_pos=(41, 11),
        Frame_r41c11_color=6,
        Frame_r41c12_pos=(41, 12),
        Frame_r41c12_color=6,
        Frame_r41c13_pos=(41, 13),
        Frame_r41c13_color=6,
        Frame_r41c14_pos=(41, 14),
        Frame_r41c14_color=6,
        Frame_r41c15_pos=(41, 15),
        Frame_r41c15_color=6,
        Frame_r41c16_pos=(41, 16),
        Frame_r41c16_color=6,
        Hollow_r37c12_pos=(37, 12),
        Hollow_r37c12_color=0,
        Hollow_r37c13_pos=(37, 13),
        Hollow_r37c13_color=0,
        Hollow_r37c14_pos=(37, 14),
        Hollow_r37c14_color=0,
        Hollow_r37c15_pos=(37, 15),
        Hollow_r37c15_color=0,
        Hollow_r38c12_pos=(38, 12),
        Hollow_r38c12_color=0,
        Hollow_r38c15_pos=(38, 15),
        Hollow_r38c15_color=0,
        Hollow_r39c12_pos=(39, 12),
        Hollow_r39c12_color=0,
        Hollow_r39c15_pos=(39, 15),
        Hollow_r39c15_color=0,
        Hollow_r40c12_pos=(40, 12),
        Hollow_r40c12_color=0,
        Hollow_r40c13_pos=(40, 13),
        Hollow_r40c13_color=0,
        Hollow_r40c14_pos=(40, 14),
        Hollow_r40c14_color=0,
        Hollow_r40c15_pos=(40, 15),
        Hollow_r40c15_color=0,
        Dot_r38c16_pos=(38, 16),
        Dot_r38c16_color=1,
        Dot_r38c18_pos=(38, 18),
        Dot_r38c18_color=1,
        Dot_r38c19_pos=(38, 19),
        Dot_r38c19_color=1,
        Dot_r38c21_pos=(38, 21),
        Dot_r38c21_color=1,
        Dot_r38c22_pos=(38, 22),
        Dot_r38c22_color=1,
        Dot_r39c17_pos=(39, 17),
        Dot_r39c17_color=1,
        Dot_r39c18_pos=(39, 18),
        Dot_r39c18_color=1,
        Dot_r39c20_pos=(39, 20),
        Dot_r39c20_color=1,
        Dot_r39c21_pos=(39, 21),
        Dot_r39c21_color=1,
    )
