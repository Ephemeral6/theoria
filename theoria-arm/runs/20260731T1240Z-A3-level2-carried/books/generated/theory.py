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
LANDMARKS = {'gate_center': (0, 0), 'knob_center': (0, 0), 'socket_center': (0, 0), 'spawn_center': (0, 0)}
BACKGROUND = 0
N_POS = None
GRID = (64, 64)
BOARD = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 8, 8, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 8, 8, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 8, 8, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 5, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 8, 8, 8, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 8, 8, 8, 8, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 8, 8, 8, 8, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 8, 8, 8, 8, 8, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 9, 9, 9, 9, 9, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 5, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 9, 9, 9, 9, 9, 9, 9, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 0, 0],
]
ACTIONS = [('key', 2), ('key', 5)]


@dataclass
class State:
    """One field per instance per observation the word table names."""
    Glyph9_r1c1_pos: object = (1, 1)
    Glyph9_r1c1_color: object = 9
    Glyph9_r1c2_pos: object = (1, 2)
    Glyph9_r1c2_color: object = 9
    Glyph9_r1c3_pos: object = (1, 3)
    Glyph9_r1c3_color: object = 9
    Glyph9_r2c1_pos: object = (2, 1)
    Glyph9_r2c1_color: object = 9
    Glyph9_r2c3_pos: object = (2, 3)
    Glyph9_r2c3_color: object = 9
    Glyph9_r3c1_pos: object = (3, 1)
    Glyph9_r3c1_color: object = 9
    Glyph9_r3c2_pos: object = (3, 2)
    Glyph9_r3c2_color: object = 9
    Glyph9_r3c3_pos: object = (3, 3)
    Glyph9_r3c3_color: object = 9
    Glyph9_r5c1_pos: object = (5, 1)
    Glyph9_r5c1_color: object = 9
    Glyph9_r5c2_pos: object = (5, 2)
    Glyph9_r5c2_color: object = 9
    Glyph9_r5c3_pos: object = (5, 3)
    Glyph9_r5c3_color: object = 9
    Glyph9_r8c14_pos: object = (8, 14)
    Glyph9_r8c14_color: object = 9
    Glyph9_r8c15_pos: object = (8, 15)
    Glyph9_r8c15_color: object = 9
    Glyph9_r8c16_pos: object = (8, 16)
    Glyph9_r8c16_color: object = 9
    Glyph9_r8c17_pos: object = (8, 17)
    Glyph9_r8c17_color: object = 9
    Glyph9_r8c18_pos: object = (8, 18)
    Glyph9_r8c18_color: object = 9
    Glyph9_r9c14_pos: object = (9, 14)
    Glyph9_r9c14_color: object = 9
    Glyph9_r9c15_pos: object = (9, 15)
    Glyph9_r9c15_color: object = 9
    Glyph9_r9c16_pos: object = (9, 16)
    Glyph9_r9c16_color: object = 9
    Glyph9_r9c17_pos: object = (9, 17)
    Glyph9_r9c17_color: object = 9
    Glyph9_r9c18_pos: object = (9, 18)
    Glyph9_r9c18_color: object = 9
    Glyph9_r10c14_pos: object = (10, 14)
    Glyph9_r10c14_color: object = 9
    Glyph9_r10c15_pos: object = (10, 15)
    Glyph9_r10c15_color: object = 9
    Glyph9_r10c17_pos: object = (10, 17)
    Glyph9_r10c17_color: object = 9
    Glyph9_r10c18_pos: object = (10, 18)
    Glyph9_r10c18_color: object = 9
    Glyph9_r11c14_pos: object = (11, 14)
    Glyph9_r11c14_color: object = 9
    Glyph9_r11c15_pos: object = (11, 15)
    Glyph9_r11c15_color: object = 9
    Glyph9_r11c16_pos: object = (11, 16)
    Glyph9_r11c16_color: object = 9
    Glyph9_r11c17_pos: object = (11, 17)
    Glyph9_r11c17_color: object = 9
    Glyph9_r11c18_pos: object = (11, 18)
    Glyph9_r11c18_color: object = 9
    Glyph9_r12c14_pos: object = (12, 14)
    Glyph9_r12c14_color: object = 9
    Glyph9_r12c15_pos: object = (12, 15)
    Glyph9_r12c15_color: object = 9
    Glyph9_r12c16_pos: object = (12, 16)
    Glyph9_r12c16_color: object = 9
    Glyph9_r12c17_pos: object = (12, 17)
    Glyph9_r12c17_color: object = 9
    Glyph9_r12c18_pos: object = (12, 18)
    Glyph9_r12c18_color: object = 9
    Glyph9_r63c62_pos: object = (63, 62)
    Glyph9_r63c62_color: object = 9
    Glyph9_r63c63_pos: object = (63, 63)
    Glyph9_r63c63_color: object = 9
    Vacated_r14c14_pos: object = (14, 14)
    Vacated_r14c14_color: object = 5
    Vacated_r14c15_pos: object = (14, 15)
    Vacated_r14c15_color: object = 5
    Vacated_r14c16_pos: object = (14, 16)
    Vacated_r14c16_color: object = 5
    Vacated_r14c17_pos: object = (14, 17)
    Vacated_r14c17_color: object = 5
    Vacated_r14c18_pos: object = (14, 18)
    Vacated_r14c18_color: object = 5
    Vacated_r15c14_pos: object = (15, 14)
    Vacated_r15c14_color: object = 5
    Vacated_r15c15_pos: object = (15, 15)
    Vacated_r15c15_color: object = 5
    Vacated_r15c16_pos: object = (15, 16)
    Vacated_r15c16_color: object = 5
    Vacated_r15c17_pos: object = (15, 17)
    Vacated_r15c17_color: object = 5
    Vacated_r15c18_pos: object = (15, 18)
    Vacated_r15c18_color: object = 5
    Vacated_r16c14_pos: object = (16, 14)
    Vacated_r16c14_color: object = 5
    Vacated_r16c15_pos: object = (16, 15)
    Vacated_r16c15_color: object = 5
    Vacated_r16c17_pos: object = (16, 17)
    Vacated_r16c17_color: object = 5
    Vacated_r16c18_pos: object = (16, 18)
    Vacated_r16c18_color: object = 5
    Vacated_r17c14_pos: object = (17, 14)
    Vacated_r17c14_color: object = 5
    Vacated_r17c15_pos: object = (17, 15)
    Vacated_r17c15_color: object = 5
    Vacated_r17c16_pos: object = (17, 16)
    Vacated_r17c16_color: object = 5
    Vacated_r17c17_pos: object = (17, 17)
    Vacated_r17c17_color: object = 5
    Vacated_r17c18_pos: object = (17, 18)
    Vacated_r17c18_color: object = 5
    Vacated_r18c14_pos: object = (18, 14)
    Vacated_r18c14_color: object = 5
    Vacated_r18c15_pos: object = (18, 15)
    Vacated_r18c15_color: object = 5
    Vacated_r18c16_pos: object = (18, 16)
    Vacated_r18c16_color: object = 5
    Vacated_r18c17_pos: object = (18, 17)
    Vacated_r18c17_color: object = 5
    Vacated_r18c18_pos: object = (18, 18)
    Vacated_r18c18_color: object = 5
    Spent_r1c5_pos: object = (1, 5)
    Spent_r1c5_color: object = 1
    Spent_r1c6_pos: object = (1, 6)
    Spent_r1c6_color: object = 1
    Spent_r1c7_pos: object = (1, 7)
    Spent_r1c7_color: object = 1
    Spent_r2c5_pos: object = (2, 5)
    Spent_r2c5_color: object = 1
    Spent_r2c6_pos: object = (2, 6)
    Spent_r2c6_color: object = 1
    Spent_r2c7_pos: object = (2, 7)
    Spent_r2c7_color: object = 1
    Spent_r3c5_pos: object = (3, 5)
    Spent_r3c5_color: object = 1
    Spent_r3c6_pos: object = (3, 6)
    Spent_r3c6_color: object = 1
    Spent_r3c7_pos: object = (3, 7)
    Spent_r3c7_color: object = 1

    def copy(self):
        return replace(self)

    def key(self):
        return (self.Glyph9_r1c1_pos, self.Glyph9_r1c1_color, self.Glyph9_r1c2_pos, self.Glyph9_r1c2_color, self.Glyph9_r1c3_pos, self.Glyph9_r1c3_color, self.Glyph9_r2c1_pos, self.Glyph9_r2c1_color, self.Glyph9_r2c3_pos, self.Glyph9_r2c3_color, self.Glyph9_r3c1_pos, self.Glyph9_r3c1_color, self.Glyph9_r3c2_pos, self.Glyph9_r3c2_color, self.Glyph9_r3c3_pos, self.Glyph9_r3c3_color, self.Glyph9_r5c1_pos, self.Glyph9_r5c1_color, self.Glyph9_r5c2_pos, self.Glyph9_r5c2_color, self.Glyph9_r5c3_pos, self.Glyph9_r5c3_color, self.Glyph9_r8c14_pos, self.Glyph9_r8c14_color, self.Glyph9_r8c15_pos, self.Glyph9_r8c15_color, self.Glyph9_r8c16_pos, self.Glyph9_r8c16_color, self.Glyph9_r8c17_pos, self.Glyph9_r8c17_color, self.Glyph9_r8c18_pos, self.Glyph9_r8c18_color, self.Glyph9_r9c14_pos, self.Glyph9_r9c14_color, self.Glyph9_r9c15_pos, self.Glyph9_r9c15_color, self.Glyph9_r9c16_pos, self.Glyph9_r9c16_color, self.Glyph9_r9c17_pos, self.Glyph9_r9c17_color, self.Glyph9_r9c18_pos, self.Glyph9_r9c18_color, self.Glyph9_r10c14_pos, self.Glyph9_r10c14_color, self.Glyph9_r10c15_pos, self.Glyph9_r10c15_color, self.Glyph9_r10c17_pos, self.Glyph9_r10c17_color, self.Glyph9_r10c18_pos, self.Glyph9_r10c18_color, self.Glyph9_r11c14_pos, self.Glyph9_r11c14_color, self.Glyph9_r11c15_pos, self.Glyph9_r11c15_color, self.Glyph9_r11c16_pos, self.Glyph9_r11c16_color, self.Glyph9_r11c17_pos, self.Glyph9_r11c17_color, self.Glyph9_r11c18_pos, self.Glyph9_r11c18_color, self.Glyph9_r12c14_pos, self.Glyph9_r12c14_color, self.Glyph9_r12c15_pos, self.Glyph9_r12c15_color, self.Glyph9_r12c16_pos, self.Glyph9_r12c16_color, self.Glyph9_r12c17_pos, self.Glyph9_r12c17_color, self.Glyph9_r12c18_pos, self.Glyph9_r12c18_color, self.Glyph9_r63c62_pos, self.Glyph9_r63c62_color, self.Glyph9_r63c63_pos, self.Glyph9_r63c63_color, self.Vacated_r14c14_pos, self.Vacated_r14c14_color, self.Vacated_r14c15_pos, self.Vacated_r14c15_color, self.Vacated_r14c16_pos, self.Vacated_r14c16_color, self.Vacated_r14c17_pos, self.Vacated_r14c17_color, self.Vacated_r14c18_pos, self.Vacated_r14c18_color, self.Vacated_r15c14_pos, self.Vacated_r15c14_color, self.Vacated_r15c15_pos, self.Vacated_r15c15_color, self.Vacated_r15c16_pos, self.Vacated_r15c16_color, self.Vacated_r15c17_pos, self.Vacated_r15c17_color, self.Vacated_r15c18_pos, self.Vacated_r15c18_color, self.Vacated_r16c14_pos, self.Vacated_r16c14_color, self.Vacated_r16c15_pos, self.Vacated_r16c15_color, self.Vacated_r16c17_pos, self.Vacated_r16c17_color, self.Vacated_r16c18_pos, self.Vacated_r16c18_color, self.Vacated_r17c14_pos, self.Vacated_r17c14_color, self.Vacated_r17c15_pos, self.Vacated_r17c15_color, self.Vacated_r17c16_pos, self.Vacated_r17c16_color, self.Vacated_r17c17_pos, self.Vacated_r17c17_color, self.Vacated_r17c18_pos, self.Vacated_r17c18_color, self.Vacated_r18c14_pos, self.Vacated_r18c14_color, self.Vacated_r18c15_pos, self.Vacated_r18c15_color, self.Vacated_r18c16_pos, self.Vacated_r18c16_color, self.Vacated_r18c17_pos, self.Vacated_r18c17_color, self.Vacated_r18c18_pos, self.Vacated_r18c18_color, self.Spent_r1c5_pos, self.Spent_r1c5_color, self.Spent_r1c6_pos, self.Spent_r1c6_color, self.Spent_r1c7_pos, self.Spent_r1c7_color, self.Spent_r2c5_pos, self.Spent_r2c5_color, self.Spent_r2c6_pos, self.Spent_r2c6_color, self.Spent_r2c7_pos, self.Spent_r2c7_color, self.Spent_r3c5_pos, self.Spent_r3c5_color, self.Spent_r3c6_pos, self.Spent_r3c6_color, self.Spent_r3c7_pos, self.Spent_r3c7_color,)


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
    if 'Glyph9_r1c1' not in _exclude:
        r, c = state.Glyph9_r1c1_pos
        grid[r][c] = state.Glyph9_r1c1_color
    if 'Glyph9_r1c2' not in _exclude:
        r, c = state.Glyph9_r1c2_pos
        grid[r][c] = state.Glyph9_r1c2_color
    if 'Glyph9_r1c3' not in _exclude:
        r, c = state.Glyph9_r1c3_pos
        grid[r][c] = state.Glyph9_r1c3_color
    if 'Glyph9_r2c1' not in _exclude:
        r, c = state.Glyph9_r2c1_pos
        grid[r][c] = state.Glyph9_r2c1_color
    if 'Glyph9_r2c3' not in _exclude:
        r, c = state.Glyph9_r2c3_pos
        grid[r][c] = state.Glyph9_r2c3_color
    if 'Glyph9_r3c1' not in _exclude:
        r, c = state.Glyph9_r3c1_pos
        grid[r][c] = state.Glyph9_r3c1_color
    if 'Glyph9_r3c2' not in _exclude:
        r, c = state.Glyph9_r3c2_pos
        grid[r][c] = state.Glyph9_r3c2_color
    if 'Glyph9_r3c3' not in _exclude:
        r, c = state.Glyph9_r3c3_pos
        grid[r][c] = state.Glyph9_r3c3_color
    if 'Glyph9_r5c1' not in _exclude:
        r, c = state.Glyph9_r5c1_pos
        grid[r][c] = state.Glyph9_r5c1_color
    if 'Glyph9_r5c2' not in _exclude:
        r, c = state.Glyph9_r5c2_pos
        grid[r][c] = state.Glyph9_r5c2_color
    if 'Glyph9_r5c3' not in _exclude:
        r, c = state.Glyph9_r5c3_pos
        grid[r][c] = state.Glyph9_r5c3_color
    if 'Glyph9_r8c14' not in _exclude:
        r, c = state.Glyph9_r8c14_pos
        grid[r][c] = state.Glyph9_r8c14_color
    if 'Glyph9_r8c15' not in _exclude:
        r, c = state.Glyph9_r8c15_pos
        grid[r][c] = state.Glyph9_r8c15_color
    if 'Glyph9_r8c16' not in _exclude:
        r, c = state.Glyph9_r8c16_pos
        grid[r][c] = state.Glyph9_r8c16_color
    if 'Glyph9_r8c17' not in _exclude:
        r, c = state.Glyph9_r8c17_pos
        grid[r][c] = state.Glyph9_r8c17_color
    if 'Glyph9_r8c18' not in _exclude:
        r, c = state.Glyph9_r8c18_pos
        grid[r][c] = state.Glyph9_r8c18_color
    if 'Glyph9_r9c14' not in _exclude:
        r, c = state.Glyph9_r9c14_pos
        grid[r][c] = state.Glyph9_r9c14_color
    if 'Glyph9_r9c15' not in _exclude:
        r, c = state.Glyph9_r9c15_pos
        grid[r][c] = state.Glyph9_r9c15_color
    if 'Glyph9_r9c16' not in _exclude:
        r, c = state.Glyph9_r9c16_pos
        grid[r][c] = state.Glyph9_r9c16_color
    if 'Glyph9_r9c17' not in _exclude:
        r, c = state.Glyph9_r9c17_pos
        grid[r][c] = state.Glyph9_r9c17_color
    if 'Glyph9_r9c18' not in _exclude:
        r, c = state.Glyph9_r9c18_pos
        grid[r][c] = state.Glyph9_r9c18_color
    if 'Glyph9_r10c14' not in _exclude:
        r, c = state.Glyph9_r10c14_pos
        grid[r][c] = state.Glyph9_r10c14_color
    if 'Glyph9_r10c15' not in _exclude:
        r, c = state.Glyph9_r10c15_pos
        grid[r][c] = state.Glyph9_r10c15_color
    if 'Glyph9_r10c17' not in _exclude:
        r, c = state.Glyph9_r10c17_pos
        grid[r][c] = state.Glyph9_r10c17_color
    if 'Glyph9_r10c18' not in _exclude:
        r, c = state.Glyph9_r10c18_pos
        grid[r][c] = state.Glyph9_r10c18_color
    if 'Glyph9_r11c14' not in _exclude:
        r, c = state.Glyph9_r11c14_pos
        grid[r][c] = state.Glyph9_r11c14_color
    if 'Glyph9_r11c15' not in _exclude:
        r, c = state.Glyph9_r11c15_pos
        grid[r][c] = state.Glyph9_r11c15_color
    if 'Glyph9_r11c16' not in _exclude:
        r, c = state.Glyph9_r11c16_pos
        grid[r][c] = state.Glyph9_r11c16_color
    if 'Glyph9_r11c17' not in _exclude:
        r, c = state.Glyph9_r11c17_pos
        grid[r][c] = state.Glyph9_r11c17_color
    if 'Glyph9_r11c18' not in _exclude:
        r, c = state.Glyph9_r11c18_pos
        grid[r][c] = state.Glyph9_r11c18_color
    if 'Glyph9_r12c14' not in _exclude:
        r, c = state.Glyph9_r12c14_pos
        grid[r][c] = state.Glyph9_r12c14_color
    if 'Glyph9_r12c15' not in _exclude:
        r, c = state.Glyph9_r12c15_pos
        grid[r][c] = state.Glyph9_r12c15_color
    if 'Glyph9_r12c16' not in _exclude:
        r, c = state.Glyph9_r12c16_pos
        grid[r][c] = state.Glyph9_r12c16_color
    if 'Glyph9_r12c17' not in _exclude:
        r, c = state.Glyph9_r12c17_pos
        grid[r][c] = state.Glyph9_r12c17_color
    if 'Glyph9_r12c18' not in _exclude:
        r, c = state.Glyph9_r12c18_pos
        grid[r][c] = state.Glyph9_r12c18_color
    if 'Glyph9_r63c62' not in _exclude:
        r, c = state.Glyph9_r63c62_pos
        grid[r][c] = state.Glyph9_r63c62_color
    if 'Glyph9_r63c63' not in _exclude:
        r, c = state.Glyph9_r63c63_pos
        grid[r][c] = state.Glyph9_r63c63_color
    if 'Vacated_r14c14' not in _exclude:
        r, c = state.Vacated_r14c14_pos
        grid[r][c] = state.Vacated_r14c14_color
    if 'Vacated_r14c15' not in _exclude:
        r, c = state.Vacated_r14c15_pos
        grid[r][c] = state.Vacated_r14c15_color
    if 'Vacated_r14c16' not in _exclude:
        r, c = state.Vacated_r14c16_pos
        grid[r][c] = state.Vacated_r14c16_color
    if 'Vacated_r14c17' not in _exclude:
        r, c = state.Vacated_r14c17_pos
        grid[r][c] = state.Vacated_r14c17_color
    if 'Vacated_r14c18' not in _exclude:
        r, c = state.Vacated_r14c18_pos
        grid[r][c] = state.Vacated_r14c18_color
    if 'Vacated_r15c14' not in _exclude:
        r, c = state.Vacated_r15c14_pos
        grid[r][c] = state.Vacated_r15c14_color
    if 'Vacated_r15c15' not in _exclude:
        r, c = state.Vacated_r15c15_pos
        grid[r][c] = state.Vacated_r15c15_color
    if 'Vacated_r15c16' not in _exclude:
        r, c = state.Vacated_r15c16_pos
        grid[r][c] = state.Vacated_r15c16_color
    if 'Vacated_r15c17' not in _exclude:
        r, c = state.Vacated_r15c17_pos
        grid[r][c] = state.Vacated_r15c17_color
    if 'Vacated_r15c18' not in _exclude:
        r, c = state.Vacated_r15c18_pos
        grid[r][c] = state.Vacated_r15c18_color
    if 'Vacated_r16c14' not in _exclude:
        r, c = state.Vacated_r16c14_pos
        grid[r][c] = state.Vacated_r16c14_color
    if 'Vacated_r16c15' not in _exclude:
        r, c = state.Vacated_r16c15_pos
        grid[r][c] = state.Vacated_r16c15_color
    if 'Vacated_r16c17' not in _exclude:
        r, c = state.Vacated_r16c17_pos
        grid[r][c] = state.Vacated_r16c17_color
    if 'Vacated_r16c18' not in _exclude:
        r, c = state.Vacated_r16c18_pos
        grid[r][c] = state.Vacated_r16c18_color
    if 'Vacated_r17c14' not in _exclude:
        r, c = state.Vacated_r17c14_pos
        grid[r][c] = state.Vacated_r17c14_color
    if 'Vacated_r17c15' not in _exclude:
        r, c = state.Vacated_r17c15_pos
        grid[r][c] = state.Vacated_r17c15_color
    if 'Vacated_r17c16' not in _exclude:
        r, c = state.Vacated_r17c16_pos
        grid[r][c] = state.Vacated_r17c16_color
    if 'Vacated_r17c17' not in _exclude:
        r, c = state.Vacated_r17c17_pos
        grid[r][c] = state.Vacated_r17c17_color
    if 'Vacated_r17c18' not in _exclude:
        r, c = state.Vacated_r17c18_pos
        grid[r][c] = state.Vacated_r17c18_color
    if 'Vacated_r18c14' not in _exclude:
        r, c = state.Vacated_r18c14_pos
        grid[r][c] = state.Vacated_r18c14_color
    if 'Vacated_r18c15' not in _exclude:
        r, c = state.Vacated_r18c15_pos
        grid[r][c] = state.Vacated_r18c15_color
    if 'Vacated_r18c16' not in _exclude:
        r, c = state.Vacated_r18c16_pos
        grid[r][c] = state.Vacated_r18c16_color
    if 'Vacated_r18c17' not in _exclude:
        r, c = state.Vacated_r18c17_pos
        grid[r][c] = state.Vacated_r18c17_color
    if 'Vacated_r18c18' not in _exclude:
        r, c = state.Vacated_r18c18_pos
        grid[r][c] = state.Vacated_r18c18_color
    if 'Spent_r1c5' not in _exclude:
        r, c = state.Spent_r1c5_pos
        grid[r][c] = state.Spent_r1c5_color
    if 'Spent_r1c6' not in _exclude:
        r, c = state.Spent_r1c6_pos
        grid[r][c] = state.Spent_r1c6_color
    if 'Spent_r1c7' not in _exclude:
        r, c = state.Spent_r1c7_pos
        grid[r][c] = state.Spent_r1c7_color
    if 'Spent_r2c5' not in _exclude:
        r, c = state.Spent_r2c5_pos
        grid[r][c] = state.Spent_r2c5_color
    if 'Spent_r2c6' not in _exclude:
        r, c = state.Spent_r2c6_pos
        grid[r][c] = state.Spent_r2c6_color
    if 'Spent_r2c7' not in _exclude:
        r, c = state.Spent_r2c7_pos
        grid[r][c] = state.Spent_r2c7_color
    if 'Spent_r3c5' not in _exclude:
        r, c = state.Spent_r3c5_pos
        grid[r][c] = state.Spent_r3c5_color
    if 'Spent_r3c6' not in _exclude:
        r, c = state.Spent_r3c6_pos
        grid[r][c] = state.Spent_r3c6_color
    if 'Spent_r3c7' not in _exclude:
        r, c = state.Spent_r3c7_pos
        grid[r][c] = state.Spent_r3c7_color
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


def _guard_key2_body_leaves__Glyph9_r1c1(state, action):
    """key2_body_leaves__Glyph9_r1c1  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r1c1_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r1c1_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r1c1(state):
    state.Glyph9_r1c1_color = 5


def _guard_key2_body_leaves__Glyph9_r1c2(state, action):
    """key2_body_leaves__Glyph9_r1c2  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r1c2_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r1c2_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r1c2(state):
    state.Glyph9_r1c2_color = 5


def _guard_key2_body_leaves__Glyph9_r1c3(state, action):
    """key2_body_leaves__Glyph9_r1c3  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r1c3_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r1c3_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r1c3(state):
    state.Glyph9_r1c3_color = 5


def _guard_key2_body_leaves__Glyph9_r2c1(state, action):
    """key2_body_leaves__Glyph9_r2c1  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r2c1_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r2c1_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r2c1(state):
    state.Glyph9_r2c1_color = 5


def _guard_key2_body_leaves__Glyph9_r2c3(state, action):
    """key2_body_leaves__Glyph9_r2c3  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r2c3_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r2c3_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r2c3(state):
    state.Glyph9_r2c3_color = 5


def _guard_key2_body_leaves__Glyph9_r3c1(state, action):
    """key2_body_leaves__Glyph9_r3c1  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r3c1_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r3c1_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r3c1(state):
    state.Glyph9_r3c1_color = 5


def _guard_key2_body_leaves__Glyph9_r3c2(state, action):
    """key2_body_leaves__Glyph9_r3c2  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r3c2_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r3c2_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r3c2(state):
    state.Glyph9_r3c2_color = 5


def _guard_key2_body_leaves__Glyph9_r3c3(state, action):
    """key2_body_leaves__Glyph9_r3c3  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r3c3_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r3c3_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r3c3(state):
    state.Glyph9_r3c3_color = 5


def _guard_key2_body_leaves__Glyph9_r5c1(state, action):
    """key2_body_leaves__Glyph9_r5c1  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r5c1_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r5c1_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r5c1(state):
    state.Glyph9_r5c1_color = 5


def _guard_key2_body_leaves__Glyph9_r5c2(state, action):
    """key2_body_leaves__Glyph9_r5c2  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r5c2_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r5c2_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r5c2(state):
    state.Glyph9_r5c2_color = 5


def _guard_key2_body_leaves__Glyph9_r5c3(state, action):
    """key2_body_leaves__Glyph9_r5c3  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r5c3_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r5c3_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r5c3(state):
    state.Glyph9_r5c3_color = 5


def _guard_key2_body_leaves__Glyph9_r8c14(state, action):
    """key2_body_leaves__Glyph9_r8c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r8c14_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r8c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r8c14(state):
    state.Glyph9_r8c14_color = 5


def _guard_key2_body_leaves__Glyph9_r8c15(state, action):
    """key2_body_leaves__Glyph9_r8c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r8c15_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r8c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r8c15(state):
    state.Glyph9_r8c15_color = 5


def _guard_key2_body_leaves__Glyph9_r8c16(state, action):
    """key2_body_leaves__Glyph9_r8c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r8c16_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r8c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r8c16(state):
    state.Glyph9_r8c16_color = 5


def _guard_key2_body_leaves__Glyph9_r8c17(state, action):
    """key2_body_leaves__Glyph9_r8c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r8c17_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r8c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r8c17(state):
    state.Glyph9_r8c17_color = 5


def _guard_key2_body_leaves__Glyph9_r8c18(state, action):
    """key2_body_leaves__Glyph9_r8c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r8c18_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r8c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r8c18(state):
    state.Glyph9_r8c18_color = 5


def _guard_key2_body_leaves__Glyph9_r9c14(state, action):
    """key2_body_leaves__Glyph9_r9c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r9c14_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r9c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r9c14(state):
    state.Glyph9_r9c14_color = 5


def _guard_key2_body_leaves__Glyph9_r9c15(state, action):
    """key2_body_leaves__Glyph9_r9c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r9c15_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r9c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r9c15(state):
    state.Glyph9_r9c15_color = 5


def _guard_key2_body_leaves__Glyph9_r9c16(state, action):
    """key2_body_leaves__Glyph9_r9c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r9c16_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r9c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r9c16(state):
    state.Glyph9_r9c16_color = 5


def _guard_key2_body_leaves__Glyph9_r9c17(state, action):
    """key2_body_leaves__Glyph9_r9c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r9c17_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r9c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r9c17(state):
    state.Glyph9_r9c17_color = 5


def _guard_key2_body_leaves__Glyph9_r9c18(state, action):
    """key2_body_leaves__Glyph9_r9c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r9c18_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r9c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r9c18(state):
    state.Glyph9_r9c18_color = 5


def _guard_key2_body_leaves__Glyph9_r10c14(state, action):
    """key2_body_leaves__Glyph9_r10c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r10c14_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r10c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r10c14(state):
    state.Glyph9_r10c14_color = 5


def _guard_key2_body_leaves__Glyph9_r10c15(state, action):
    """key2_body_leaves__Glyph9_r10c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r10c15_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r10c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r10c15(state):
    state.Glyph9_r10c15_color = 5


def _guard_key2_body_leaves__Glyph9_r10c17(state, action):
    """key2_body_leaves__Glyph9_r10c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r10c17_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r10c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r10c17(state):
    state.Glyph9_r10c17_color = 5


def _guard_key2_body_leaves__Glyph9_r10c18(state, action):
    """key2_body_leaves__Glyph9_r10c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r10c18_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r10c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r10c18(state):
    state.Glyph9_r10c18_color = 5


def _guard_key2_body_leaves__Glyph9_r11c14(state, action):
    """key2_body_leaves__Glyph9_r11c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r11c14_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r11c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r11c14(state):
    state.Glyph9_r11c14_color = 5


def _guard_key2_body_leaves__Glyph9_r11c15(state, action):
    """key2_body_leaves__Glyph9_r11c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r11c15_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r11c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r11c15(state):
    state.Glyph9_r11c15_color = 5


def _guard_key2_body_leaves__Glyph9_r11c16(state, action):
    """key2_body_leaves__Glyph9_r11c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r11c16_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r11c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r11c16(state):
    state.Glyph9_r11c16_color = 5


def _guard_key2_body_leaves__Glyph9_r11c17(state, action):
    """key2_body_leaves__Glyph9_r11c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r11c17_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r11c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r11c17(state):
    state.Glyph9_r11c17_color = 5


def _guard_key2_body_leaves__Glyph9_r11c18(state, action):
    """key2_body_leaves__Glyph9_r11c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r11c18_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r11c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r11c18(state):
    state.Glyph9_r11c18_color = 5


def _guard_key2_body_leaves__Glyph9_r12c14(state, action):
    """key2_body_leaves__Glyph9_r12c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r12c14_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r12c14_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r12c14(state):
    state.Glyph9_r12c14_color = 5


def _guard_key2_body_leaves__Glyph9_r12c15(state, action):
    """key2_body_leaves__Glyph9_r12c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r12c15_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r12c15_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r12c15(state):
    state.Glyph9_r12c15_color = 5


def _guard_key2_body_leaves__Glyph9_r12c16(state, action):
    """key2_body_leaves__Glyph9_r12c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r12c16_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r12c16_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r12c16(state):
    state.Glyph9_r12c16_color = 5


def _guard_key2_body_leaves__Glyph9_r12c17(state, action):
    """key2_body_leaves__Glyph9_r12c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r12c17_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r12c17_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r12c17(state):
    state.Glyph9_r12c17_color = 5


def _guard_key2_body_leaves__Glyph9_r12c18(state, action):
    """key2_body_leaves__Glyph9_r12c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r12c18_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r12c18_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r12c18(state):
    state.Glyph9_r12c18_color = 5


def _guard_key2_body_leaves__Glyph9_r63c62(state, action):
    """key2_body_leaves__Glyph9_r63c62  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r63c62_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r63c62_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r63c62(state):
    state.Glyph9_r63c62_color = 5


def _guard_key2_body_leaves__Glyph9_r63c63(state, action):
    """key2_body_leaves__Glyph9_r63c63  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Glyph9_r63c63_pos) == 9): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Glyph9_r63c63_pos, 'down'), 'down'), 'down'), 'down'), 'down'), 'down')) == 5): return False
    return True


def _effect_key2_body_leaves__Glyph9_r63c63(state):
    state.Glyph9_r63c63_color = 5


def _guard_key2_body_arrives__Vacated_r14c14(state, action):
    """key2_body_arrives__Vacated_r14c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r14c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r14c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r14c14(state):
    state.Vacated_r14c14_color = 9


def _guard_key2_body_arrives__Vacated_r14c15(state, action):
    """key2_body_arrives__Vacated_r14c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r14c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r14c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r14c15(state):
    state.Vacated_r14c15_color = 9


def _guard_key2_body_arrives__Vacated_r14c16(state, action):
    """key2_body_arrives__Vacated_r14c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r14c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r14c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r14c16(state):
    state.Vacated_r14c16_color = 9


def _guard_key2_body_arrives__Vacated_r14c17(state, action):
    """key2_body_arrives__Vacated_r14c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r14c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r14c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r14c17(state):
    state.Vacated_r14c17_color = 9


def _guard_key2_body_arrives__Vacated_r14c18(state, action):
    """key2_body_arrives__Vacated_r14c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r14c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r14c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r14c18(state):
    state.Vacated_r14c18_color = 9


def _guard_key2_body_arrives__Vacated_r15c14(state, action):
    """key2_body_arrives__Vacated_r15c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r15c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r15c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r15c14(state):
    state.Vacated_r15c14_color = 9


def _guard_key2_body_arrives__Vacated_r15c15(state, action):
    """key2_body_arrives__Vacated_r15c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r15c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r15c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r15c15(state):
    state.Vacated_r15c15_color = 9


def _guard_key2_body_arrives__Vacated_r15c16(state, action):
    """key2_body_arrives__Vacated_r15c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r15c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r15c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r15c16(state):
    state.Vacated_r15c16_color = 9


def _guard_key2_body_arrives__Vacated_r15c17(state, action):
    """key2_body_arrives__Vacated_r15c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r15c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r15c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r15c17(state):
    state.Vacated_r15c17_color = 9


def _guard_key2_body_arrives__Vacated_r15c18(state, action):
    """key2_body_arrives__Vacated_r15c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r15c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r15c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r15c18(state):
    state.Vacated_r15c18_color = 9


def _guard_key2_body_arrives__Vacated_r16c14(state, action):
    """key2_body_arrives__Vacated_r16c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r16c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r16c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r16c14(state):
    state.Vacated_r16c14_color = 9


def _guard_key2_body_arrives__Vacated_r16c15(state, action):
    """key2_body_arrives__Vacated_r16c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r16c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r16c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r16c15(state):
    state.Vacated_r16c15_color = 9


def _guard_key2_body_arrives__Vacated_r16c17(state, action):
    """key2_body_arrives__Vacated_r16c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r16c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r16c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r16c17(state):
    state.Vacated_r16c17_color = 9


def _guard_key2_body_arrives__Vacated_r16c18(state, action):
    """key2_body_arrives__Vacated_r16c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r16c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r16c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r16c18(state):
    state.Vacated_r16c18_color = 9


def _guard_key2_body_arrives__Vacated_r17c14(state, action):
    """key2_body_arrives__Vacated_r17c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r17c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r17c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r17c14(state):
    state.Vacated_r17c14_color = 9


def _guard_key2_body_arrives__Vacated_r17c15(state, action):
    """key2_body_arrives__Vacated_r17c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r17c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r17c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r17c15(state):
    state.Vacated_r17c15_color = 9


def _guard_key2_body_arrives__Vacated_r17c16(state, action):
    """key2_body_arrives__Vacated_r17c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r17c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r17c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r17c16(state):
    state.Vacated_r17c16_color = 9


def _guard_key2_body_arrives__Vacated_r17c17(state, action):
    """key2_body_arrives__Vacated_r17c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r17c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r17c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r17c17(state):
    state.Vacated_r17c17_color = 9


def _guard_key2_body_arrives__Vacated_r17c18(state, action):
    """key2_body_arrives__Vacated_r17c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r17c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r17c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r17c18(state):
    state.Vacated_r17c18_color = 9


def _guard_key2_body_arrives__Vacated_r18c14(state, action):
    """key2_body_arrives__Vacated_r18c14  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r18c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r18c14_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r18c14(state):
    state.Vacated_r18c14_color = 9


def _guard_key2_body_arrives__Vacated_r18c15(state, action):
    """key2_body_arrives__Vacated_r18c15  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r18c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r18c15_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r18c15(state):
    state.Vacated_r18c15_color = 9


def _guard_key2_body_arrives__Vacated_r18c16(state, action):
    """key2_body_arrives__Vacated_r18c16  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r18c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r18c16_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r18c16(state):
    state.Vacated_r18c16_color = 9


def _guard_key2_body_arrives__Vacated_r18c17(state, action):
    """key2_body_arrives__Vacated_r18c17  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r18c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r18c17_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r18c17(state):
    state.Vacated_r18c17_color = 9


def _guard_key2_body_arrives__Vacated_r18c18(state, action):
    """key2_body_arrives__Vacated_r18c18  [ev: t2,t7  cov: 48/48]"""
    if action != ('key', 2): return False
    if not (_cell_colour(state, state.Vacated_r18c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(_neighbour(_neighbour(_neighbour(_neighbour(_neighbour(state.Vacated_r18c18_pos, 'up'), 'up'), 'up'), 'up'), 'up'), 'up')) == 9): return False
    return True


def _effect_key2_body_arrives__Vacated_r18c18(state):
    state.Vacated_r18c18_color = 9


def _guard_key5_body_clears__Vacated_r14c14(state, action):
    """key5_body_clears__Vacated_r14c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r14c14_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r14c14(state):
    state.Vacated_r14c14_color = 5


def _guard_key5_body_clears__Vacated_r14c15(state, action):
    """key5_body_clears__Vacated_r14c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r14c15_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r14c15(state):
    state.Vacated_r14c15_color = 5


def _guard_key5_body_clears__Vacated_r14c16(state, action):
    """key5_body_clears__Vacated_r14c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r14c16_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r14c16(state):
    state.Vacated_r14c16_color = 5


def _guard_key5_body_clears__Vacated_r14c17(state, action):
    """key5_body_clears__Vacated_r14c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r14c17_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r14c17(state):
    state.Vacated_r14c17_color = 5


def _guard_key5_body_clears__Vacated_r14c18(state, action):
    """key5_body_clears__Vacated_r14c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r14c18_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r14c18(state):
    state.Vacated_r14c18_color = 5


def _guard_key5_body_clears__Vacated_r15c14(state, action):
    """key5_body_clears__Vacated_r15c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r15c14_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r15c14(state):
    state.Vacated_r15c14_color = 5


def _guard_key5_body_clears__Vacated_r15c15(state, action):
    """key5_body_clears__Vacated_r15c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r15c15_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r15c15(state):
    state.Vacated_r15c15_color = 5


def _guard_key5_body_clears__Vacated_r15c16(state, action):
    """key5_body_clears__Vacated_r15c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r15c16_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r15c16(state):
    state.Vacated_r15c16_color = 5


def _guard_key5_body_clears__Vacated_r15c17(state, action):
    """key5_body_clears__Vacated_r15c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r15c17_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r15c17(state):
    state.Vacated_r15c17_color = 5


def _guard_key5_body_clears__Vacated_r15c18(state, action):
    """key5_body_clears__Vacated_r15c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r15c18_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r15c18(state):
    state.Vacated_r15c18_color = 5


def _guard_key5_body_clears__Vacated_r16c14(state, action):
    """key5_body_clears__Vacated_r16c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r16c14_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r16c14(state):
    state.Vacated_r16c14_color = 5


def _guard_key5_body_clears__Vacated_r16c15(state, action):
    """key5_body_clears__Vacated_r16c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r16c15_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r16c15(state):
    state.Vacated_r16c15_color = 5


def _guard_key5_body_clears__Vacated_r16c17(state, action):
    """key5_body_clears__Vacated_r16c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r16c17_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r16c17(state):
    state.Vacated_r16c17_color = 5


def _guard_key5_body_clears__Vacated_r16c18(state, action):
    """key5_body_clears__Vacated_r16c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r16c18_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r16c18(state):
    state.Vacated_r16c18_color = 5


def _guard_key5_body_clears__Vacated_r17c14(state, action):
    """key5_body_clears__Vacated_r17c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r17c14_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r17c14(state):
    state.Vacated_r17c14_color = 5


def _guard_key5_body_clears__Vacated_r17c15(state, action):
    """key5_body_clears__Vacated_r17c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r17c15_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r17c15(state):
    state.Vacated_r17c15_color = 5


def _guard_key5_body_clears__Vacated_r17c16(state, action):
    """key5_body_clears__Vacated_r17c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r17c16_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r17c16(state):
    state.Vacated_r17c16_color = 5


def _guard_key5_body_clears__Vacated_r17c17(state, action):
    """key5_body_clears__Vacated_r17c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r17c17_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r17c17(state):
    state.Vacated_r17c17_color = 5


def _guard_key5_body_clears__Vacated_r17c18(state, action):
    """key5_body_clears__Vacated_r17c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r17c18_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r17c18(state):
    state.Vacated_r17c18_color = 5


def _guard_key5_body_clears__Vacated_r18c14(state, action):
    """key5_body_clears__Vacated_r18c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r18c14_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r18c14(state):
    state.Vacated_r18c14_color = 5


def _guard_key5_body_clears__Vacated_r18c15(state, action):
    """key5_body_clears__Vacated_r18c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r18c15_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r18c15(state):
    state.Vacated_r18c15_color = 5


def _guard_key5_body_clears__Vacated_r18c16(state, action):
    """key5_body_clears__Vacated_r18c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r18c16_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r18c16(state):
    state.Vacated_r18c16_color = 5


def _guard_key5_body_clears__Vacated_r18c17(state, action):
    """key5_body_clears__Vacated_r18c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r18c17_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r18c17(state):
    state.Vacated_r18c17_color = 5


def _guard_key5_body_clears__Vacated_r18c18(state, action):
    """key5_body_clears__Vacated_r18c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Vacated_r18c18_pos) == 9): return False
    return True


def _effect_key5_body_clears__Vacated_r18c18(state):
    state.Vacated_r18c18_color = 5


def _guard_key5_body_respawns__Glyph9_r1c1(state, action):
    """key5_body_respawns__Glyph9_r1c1  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r1c1_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r1c1_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r1c1(state):
    state.Glyph9_r1c1_color = 9


def _guard_key5_body_respawns__Glyph9_r1c2(state, action):
    """key5_body_respawns__Glyph9_r1c2  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r1c2_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r1c2_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r1c2(state):
    state.Glyph9_r1c2_color = 9


def _guard_key5_body_respawns__Glyph9_r1c3(state, action):
    """key5_body_respawns__Glyph9_r1c3  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r1c3_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r1c3_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r1c3(state):
    state.Glyph9_r1c3_color = 9


def _guard_key5_body_respawns__Glyph9_r2c1(state, action):
    """key5_body_respawns__Glyph9_r2c1  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r2c1_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r2c1_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r2c1(state):
    state.Glyph9_r2c1_color = 9


def _guard_key5_body_respawns__Glyph9_r2c3(state, action):
    """key5_body_respawns__Glyph9_r2c3  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r2c3_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r2c3_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r2c3(state):
    state.Glyph9_r2c3_color = 9


def _guard_key5_body_respawns__Glyph9_r3c1(state, action):
    """key5_body_respawns__Glyph9_r3c1  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r3c1_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r3c1_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r3c1(state):
    state.Glyph9_r3c1_color = 9


def _guard_key5_body_respawns__Glyph9_r3c2(state, action):
    """key5_body_respawns__Glyph9_r3c2  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r3c2_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r3c2_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r3c2(state):
    state.Glyph9_r3c2_color = 9


def _guard_key5_body_respawns__Glyph9_r3c3(state, action):
    """key5_body_respawns__Glyph9_r3c3  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r3c3_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r3c3_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r3c3(state):
    state.Glyph9_r3c3_color = 9


def _guard_key5_body_respawns__Glyph9_r5c1(state, action):
    """key5_body_respawns__Glyph9_r5c1  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r5c1_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r5c1_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r5c1(state):
    state.Glyph9_r5c1_color = 9


def _guard_key5_body_respawns__Glyph9_r5c2(state, action):
    """key5_body_respawns__Glyph9_r5c2  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r5c2_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r5c2_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r5c2(state):
    state.Glyph9_r5c2_color = 9


def _guard_key5_body_respawns__Glyph9_r5c3(state, action):
    """key5_body_respawns__Glyph9_r5c3  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r5c3_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r5c3_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r5c3(state):
    state.Glyph9_r5c3_color = 9


def _guard_key5_body_respawns__Glyph9_r8c14(state, action):
    """key5_body_respawns__Glyph9_r8c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r8c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r8c14_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r8c14(state):
    state.Glyph9_r8c14_color = 9


def _guard_key5_body_respawns__Glyph9_r8c15(state, action):
    """key5_body_respawns__Glyph9_r8c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r8c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r8c15_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r8c15(state):
    state.Glyph9_r8c15_color = 9


def _guard_key5_body_respawns__Glyph9_r8c16(state, action):
    """key5_body_respawns__Glyph9_r8c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r8c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r8c16_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r8c16(state):
    state.Glyph9_r8c16_color = 9


def _guard_key5_body_respawns__Glyph9_r8c17(state, action):
    """key5_body_respawns__Glyph9_r8c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r8c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r8c17_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r8c17(state):
    state.Glyph9_r8c17_color = 9


def _guard_key5_body_respawns__Glyph9_r8c18(state, action):
    """key5_body_respawns__Glyph9_r8c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r8c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r8c18_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r8c18(state):
    state.Glyph9_r8c18_color = 9


def _guard_key5_body_respawns__Glyph9_r9c14(state, action):
    """key5_body_respawns__Glyph9_r9c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r9c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r9c14_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r9c14(state):
    state.Glyph9_r9c14_color = 9


def _guard_key5_body_respawns__Glyph9_r9c15(state, action):
    """key5_body_respawns__Glyph9_r9c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r9c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r9c15_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r9c15(state):
    state.Glyph9_r9c15_color = 9


def _guard_key5_body_respawns__Glyph9_r9c16(state, action):
    """key5_body_respawns__Glyph9_r9c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r9c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r9c16_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r9c16(state):
    state.Glyph9_r9c16_color = 9


def _guard_key5_body_respawns__Glyph9_r9c17(state, action):
    """key5_body_respawns__Glyph9_r9c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r9c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r9c17_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r9c17(state):
    state.Glyph9_r9c17_color = 9


def _guard_key5_body_respawns__Glyph9_r9c18(state, action):
    """key5_body_respawns__Glyph9_r9c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r9c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r9c18_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r9c18(state):
    state.Glyph9_r9c18_color = 9


def _guard_key5_body_respawns__Glyph9_r10c14(state, action):
    """key5_body_respawns__Glyph9_r10c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r10c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r10c14_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r10c14(state):
    state.Glyph9_r10c14_color = 9


def _guard_key5_body_respawns__Glyph9_r10c15(state, action):
    """key5_body_respawns__Glyph9_r10c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r10c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r10c15_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r10c15(state):
    state.Glyph9_r10c15_color = 9


def _guard_key5_body_respawns__Glyph9_r10c17(state, action):
    """key5_body_respawns__Glyph9_r10c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r10c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r10c17_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r10c17(state):
    state.Glyph9_r10c17_color = 9


def _guard_key5_body_respawns__Glyph9_r10c18(state, action):
    """key5_body_respawns__Glyph9_r10c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r10c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r10c18_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r10c18(state):
    state.Glyph9_r10c18_color = 9


def _guard_key5_body_respawns__Glyph9_r11c14(state, action):
    """key5_body_respawns__Glyph9_r11c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r11c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r11c14_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r11c14(state):
    state.Glyph9_r11c14_color = 9


def _guard_key5_body_respawns__Glyph9_r11c15(state, action):
    """key5_body_respawns__Glyph9_r11c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r11c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r11c15_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r11c15(state):
    state.Glyph9_r11c15_color = 9


def _guard_key5_body_respawns__Glyph9_r11c16(state, action):
    """key5_body_respawns__Glyph9_r11c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r11c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r11c16_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r11c16(state):
    state.Glyph9_r11c16_color = 9


def _guard_key5_body_respawns__Glyph9_r11c17(state, action):
    """key5_body_respawns__Glyph9_r11c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r11c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r11c17_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r11c17(state):
    state.Glyph9_r11c17_color = 9


def _guard_key5_body_respawns__Glyph9_r11c18(state, action):
    """key5_body_respawns__Glyph9_r11c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r11c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r11c18_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r11c18(state):
    state.Glyph9_r11c18_color = 9


def _guard_key5_body_respawns__Glyph9_r12c14(state, action):
    """key5_body_respawns__Glyph9_r12c14  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r12c14_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r12c14_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r12c14(state):
    state.Glyph9_r12c14_color = 9


def _guard_key5_body_respawns__Glyph9_r12c15(state, action):
    """key5_body_respawns__Glyph9_r12c15  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r12c15_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r12c15_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r12c15(state):
    state.Glyph9_r12c15_color = 9


def _guard_key5_body_respawns__Glyph9_r12c16(state, action):
    """key5_body_respawns__Glyph9_r12c16  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r12c16_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r12c16_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r12c16(state):
    state.Glyph9_r12c16_color = 9


def _guard_key5_body_respawns__Glyph9_r12c17(state, action):
    """key5_body_respawns__Glyph9_r12c17  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r12c17_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r12c17_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r12c17(state):
    state.Glyph9_r12c17_color = 9


def _guard_key5_body_respawns__Glyph9_r12c18(state, action):
    """key5_body_respawns__Glyph9_r12c18  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r12c18_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r12c18_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r12c18(state):
    state.Glyph9_r12c18_color = 9


def _guard_key5_body_respawns__Glyph9_r63c62(state, action):
    """key5_body_respawns__Glyph9_r63c62  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r63c62_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r63c62_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r63c62(state):
    state.Glyph9_r63c62_color = 9


def _guard_key5_body_respawns__Glyph9_r63c63(state, action):
    """key5_body_respawns__Glyph9_r63c63  [ev: t5  cov: 24/24]"""
    if action != ('key', 5): return False
    if not (_cell_colour(state, state.Glyph9_r63c63_pos) == 5): return False
    if not (_cell_colour(state, _neighbour(state.Glyph9_r63c63_pos, 'up')) == 5): return False
    return True


def _effect_key5_body_respawns__Glyph9_r63c63(state):
    state.Glyph9_r63c63_color = 9


RULES = [
    ('key2_body_leaves__Glyph9_r1c1', _guard_key2_body_leaves__Glyph9_r1c1, _effect_key2_body_leaves__Glyph9_r1c1, ['Glyph9_r1c1']),
    ('key2_body_leaves__Glyph9_r1c2', _guard_key2_body_leaves__Glyph9_r1c2, _effect_key2_body_leaves__Glyph9_r1c2, ['Glyph9_r1c2']),
    ('key2_body_leaves__Glyph9_r1c3', _guard_key2_body_leaves__Glyph9_r1c3, _effect_key2_body_leaves__Glyph9_r1c3, ['Glyph9_r1c3']),
    ('key2_body_leaves__Glyph9_r2c1', _guard_key2_body_leaves__Glyph9_r2c1, _effect_key2_body_leaves__Glyph9_r2c1, ['Glyph9_r2c1']),
    ('key2_body_leaves__Glyph9_r2c3', _guard_key2_body_leaves__Glyph9_r2c3, _effect_key2_body_leaves__Glyph9_r2c3, ['Glyph9_r2c3']),
    ('key2_body_leaves__Glyph9_r3c1', _guard_key2_body_leaves__Glyph9_r3c1, _effect_key2_body_leaves__Glyph9_r3c1, ['Glyph9_r3c1']),
    ('key2_body_leaves__Glyph9_r3c2', _guard_key2_body_leaves__Glyph9_r3c2, _effect_key2_body_leaves__Glyph9_r3c2, ['Glyph9_r3c2']),
    ('key2_body_leaves__Glyph9_r3c3', _guard_key2_body_leaves__Glyph9_r3c3, _effect_key2_body_leaves__Glyph9_r3c3, ['Glyph9_r3c3']),
    ('key2_body_leaves__Glyph9_r5c1', _guard_key2_body_leaves__Glyph9_r5c1, _effect_key2_body_leaves__Glyph9_r5c1, ['Glyph9_r5c1']),
    ('key2_body_leaves__Glyph9_r5c2', _guard_key2_body_leaves__Glyph9_r5c2, _effect_key2_body_leaves__Glyph9_r5c2, ['Glyph9_r5c2']),
    ('key2_body_leaves__Glyph9_r5c3', _guard_key2_body_leaves__Glyph9_r5c3, _effect_key2_body_leaves__Glyph9_r5c3, ['Glyph9_r5c3']),
    ('key2_body_leaves__Glyph9_r8c14', _guard_key2_body_leaves__Glyph9_r8c14, _effect_key2_body_leaves__Glyph9_r8c14, ['Glyph9_r8c14']),
    ('key2_body_leaves__Glyph9_r8c15', _guard_key2_body_leaves__Glyph9_r8c15, _effect_key2_body_leaves__Glyph9_r8c15, ['Glyph9_r8c15']),
    ('key2_body_leaves__Glyph9_r8c16', _guard_key2_body_leaves__Glyph9_r8c16, _effect_key2_body_leaves__Glyph9_r8c16, ['Glyph9_r8c16']),
    ('key2_body_leaves__Glyph9_r8c17', _guard_key2_body_leaves__Glyph9_r8c17, _effect_key2_body_leaves__Glyph9_r8c17, ['Glyph9_r8c17']),
    ('key2_body_leaves__Glyph9_r8c18', _guard_key2_body_leaves__Glyph9_r8c18, _effect_key2_body_leaves__Glyph9_r8c18, ['Glyph9_r8c18']),
    ('key2_body_leaves__Glyph9_r9c14', _guard_key2_body_leaves__Glyph9_r9c14, _effect_key2_body_leaves__Glyph9_r9c14, ['Glyph9_r9c14']),
    ('key2_body_leaves__Glyph9_r9c15', _guard_key2_body_leaves__Glyph9_r9c15, _effect_key2_body_leaves__Glyph9_r9c15, ['Glyph9_r9c15']),
    ('key2_body_leaves__Glyph9_r9c16', _guard_key2_body_leaves__Glyph9_r9c16, _effect_key2_body_leaves__Glyph9_r9c16, ['Glyph9_r9c16']),
    ('key2_body_leaves__Glyph9_r9c17', _guard_key2_body_leaves__Glyph9_r9c17, _effect_key2_body_leaves__Glyph9_r9c17, ['Glyph9_r9c17']),
    ('key2_body_leaves__Glyph9_r9c18', _guard_key2_body_leaves__Glyph9_r9c18, _effect_key2_body_leaves__Glyph9_r9c18, ['Glyph9_r9c18']),
    ('key2_body_leaves__Glyph9_r10c14', _guard_key2_body_leaves__Glyph9_r10c14, _effect_key2_body_leaves__Glyph9_r10c14, ['Glyph9_r10c14']),
    ('key2_body_leaves__Glyph9_r10c15', _guard_key2_body_leaves__Glyph9_r10c15, _effect_key2_body_leaves__Glyph9_r10c15, ['Glyph9_r10c15']),
    ('key2_body_leaves__Glyph9_r10c17', _guard_key2_body_leaves__Glyph9_r10c17, _effect_key2_body_leaves__Glyph9_r10c17, ['Glyph9_r10c17']),
    ('key2_body_leaves__Glyph9_r10c18', _guard_key2_body_leaves__Glyph9_r10c18, _effect_key2_body_leaves__Glyph9_r10c18, ['Glyph9_r10c18']),
    ('key2_body_leaves__Glyph9_r11c14', _guard_key2_body_leaves__Glyph9_r11c14, _effect_key2_body_leaves__Glyph9_r11c14, ['Glyph9_r11c14']),
    ('key2_body_leaves__Glyph9_r11c15', _guard_key2_body_leaves__Glyph9_r11c15, _effect_key2_body_leaves__Glyph9_r11c15, ['Glyph9_r11c15']),
    ('key2_body_leaves__Glyph9_r11c16', _guard_key2_body_leaves__Glyph9_r11c16, _effect_key2_body_leaves__Glyph9_r11c16, ['Glyph9_r11c16']),
    ('key2_body_leaves__Glyph9_r11c17', _guard_key2_body_leaves__Glyph9_r11c17, _effect_key2_body_leaves__Glyph9_r11c17, ['Glyph9_r11c17']),
    ('key2_body_leaves__Glyph9_r11c18', _guard_key2_body_leaves__Glyph9_r11c18, _effect_key2_body_leaves__Glyph9_r11c18, ['Glyph9_r11c18']),
    ('key2_body_leaves__Glyph9_r12c14', _guard_key2_body_leaves__Glyph9_r12c14, _effect_key2_body_leaves__Glyph9_r12c14, ['Glyph9_r12c14']),
    ('key2_body_leaves__Glyph9_r12c15', _guard_key2_body_leaves__Glyph9_r12c15, _effect_key2_body_leaves__Glyph9_r12c15, ['Glyph9_r12c15']),
    ('key2_body_leaves__Glyph9_r12c16', _guard_key2_body_leaves__Glyph9_r12c16, _effect_key2_body_leaves__Glyph9_r12c16, ['Glyph9_r12c16']),
    ('key2_body_leaves__Glyph9_r12c17', _guard_key2_body_leaves__Glyph9_r12c17, _effect_key2_body_leaves__Glyph9_r12c17, ['Glyph9_r12c17']),
    ('key2_body_leaves__Glyph9_r12c18', _guard_key2_body_leaves__Glyph9_r12c18, _effect_key2_body_leaves__Glyph9_r12c18, ['Glyph9_r12c18']),
    ('key2_body_leaves__Glyph9_r63c62', _guard_key2_body_leaves__Glyph9_r63c62, _effect_key2_body_leaves__Glyph9_r63c62, ['Glyph9_r63c62']),
    ('key2_body_leaves__Glyph9_r63c63', _guard_key2_body_leaves__Glyph9_r63c63, _effect_key2_body_leaves__Glyph9_r63c63, ['Glyph9_r63c63']),
    ('key2_body_arrives__Vacated_r14c14', _guard_key2_body_arrives__Vacated_r14c14, _effect_key2_body_arrives__Vacated_r14c14, ['Vacated_r14c14']),
    ('key2_body_arrives__Vacated_r14c15', _guard_key2_body_arrives__Vacated_r14c15, _effect_key2_body_arrives__Vacated_r14c15, ['Vacated_r14c15']),
    ('key2_body_arrives__Vacated_r14c16', _guard_key2_body_arrives__Vacated_r14c16, _effect_key2_body_arrives__Vacated_r14c16, ['Vacated_r14c16']),
    ('key2_body_arrives__Vacated_r14c17', _guard_key2_body_arrives__Vacated_r14c17, _effect_key2_body_arrives__Vacated_r14c17, ['Vacated_r14c17']),
    ('key2_body_arrives__Vacated_r14c18', _guard_key2_body_arrives__Vacated_r14c18, _effect_key2_body_arrives__Vacated_r14c18, ['Vacated_r14c18']),
    ('key2_body_arrives__Vacated_r15c14', _guard_key2_body_arrives__Vacated_r15c14, _effect_key2_body_arrives__Vacated_r15c14, ['Vacated_r15c14']),
    ('key2_body_arrives__Vacated_r15c15', _guard_key2_body_arrives__Vacated_r15c15, _effect_key2_body_arrives__Vacated_r15c15, ['Vacated_r15c15']),
    ('key2_body_arrives__Vacated_r15c16', _guard_key2_body_arrives__Vacated_r15c16, _effect_key2_body_arrives__Vacated_r15c16, ['Vacated_r15c16']),
    ('key2_body_arrives__Vacated_r15c17', _guard_key2_body_arrives__Vacated_r15c17, _effect_key2_body_arrives__Vacated_r15c17, ['Vacated_r15c17']),
    ('key2_body_arrives__Vacated_r15c18', _guard_key2_body_arrives__Vacated_r15c18, _effect_key2_body_arrives__Vacated_r15c18, ['Vacated_r15c18']),
    ('key2_body_arrives__Vacated_r16c14', _guard_key2_body_arrives__Vacated_r16c14, _effect_key2_body_arrives__Vacated_r16c14, ['Vacated_r16c14']),
    ('key2_body_arrives__Vacated_r16c15', _guard_key2_body_arrives__Vacated_r16c15, _effect_key2_body_arrives__Vacated_r16c15, ['Vacated_r16c15']),
    ('key2_body_arrives__Vacated_r16c17', _guard_key2_body_arrives__Vacated_r16c17, _effect_key2_body_arrives__Vacated_r16c17, ['Vacated_r16c17']),
    ('key2_body_arrives__Vacated_r16c18', _guard_key2_body_arrives__Vacated_r16c18, _effect_key2_body_arrives__Vacated_r16c18, ['Vacated_r16c18']),
    ('key2_body_arrives__Vacated_r17c14', _guard_key2_body_arrives__Vacated_r17c14, _effect_key2_body_arrives__Vacated_r17c14, ['Vacated_r17c14']),
    ('key2_body_arrives__Vacated_r17c15', _guard_key2_body_arrives__Vacated_r17c15, _effect_key2_body_arrives__Vacated_r17c15, ['Vacated_r17c15']),
    ('key2_body_arrives__Vacated_r17c16', _guard_key2_body_arrives__Vacated_r17c16, _effect_key2_body_arrives__Vacated_r17c16, ['Vacated_r17c16']),
    ('key2_body_arrives__Vacated_r17c17', _guard_key2_body_arrives__Vacated_r17c17, _effect_key2_body_arrives__Vacated_r17c17, ['Vacated_r17c17']),
    ('key2_body_arrives__Vacated_r17c18', _guard_key2_body_arrives__Vacated_r17c18, _effect_key2_body_arrives__Vacated_r17c18, ['Vacated_r17c18']),
    ('key2_body_arrives__Vacated_r18c14', _guard_key2_body_arrives__Vacated_r18c14, _effect_key2_body_arrives__Vacated_r18c14, ['Vacated_r18c14']),
    ('key2_body_arrives__Vacated_r18c15', _guard_key2_body_arrives__Vacated_r18c15, _effect_key2_body_arrives__Vacated_r18c15, ['Vacated_r18c15']),
    ('key2_body_arrives__Vacated_r18c16', _guard_key2_body_arrives__Vacated_r18c16, _effect_key2_body_arrives__Vacated_r18c16, ['Vacated_r18c16']),
    ('key2_body_arrives__Vacated_r18c17', _guard_key2_body_arrives__Vacated_r18c17, _effect_key2_body_arrives__Vacated_r18c17, ['Vacated_r18c17']),
    ('key2_body_arrives__Vacated_r18c18', _guard_key2_body_arrives__Vacated_r18c18, _effect_key2_body_arrives__Vacated_r18c18, ['Vacated_r18c18']),
    ('key5_body_clears__Vacated_r14c14', _guard_key5_body_clears__Vacated_r14c14, _effect_key5_body_clears__Vacated_r14c14, ['Vacated_r14c14']),
    ('key5_body_clears__Vacated_r14c15', _guard_key5_body_clears__Vacated_r14c15, _effect_key5_body_clears__Vacated_r14c15, ['Vacated_r14c15']),
    ('key5_body_clears__Vacated_r14c16', _guard_key5_body_clears__Vacated_r14c16, _effect_key5_body_clears__Vacated_r14c16, ['Vacated_r14c16']),
    ('key5_body_clears__Vacated_r14c17', _guard_key5_body_clears__Vacated_r14c17, _effect_key5_body_clears__Vacated_r14c17, ['Vacated_r14c17']),
    ('key5_body_clears__Vacated_r14c18', _guard_key5_body_clears__Vacated_r14c18, _effect_key5_body_clears__Vacated_r14c18, ['Vacated_r14c18']),
    ('key5_body_clears__Vacated_r15c14', _guard_key5_body_clears__Vacated_r15c14, _effect_key5_body_clears__Vacated_r15c14, ['Vacated_r15c14']),
    ('key5_body_clears__Vacated_r15c15', _guard_key5_body_clears__Vacated_r15c15, _effect_key5_body_clears__Vacated_r15c15, ['Vacated_r15c15']),
    ('key5_body_clears__Vacated_r15c16', _guard_key5_body_clears__Vacated_r15c16, _effect_key5_body_clears__Vacated_r15c16, ['Vacated_r15c16']),
    ('key5_body_clears__Vacated_r15c17', _guard_key5_body_clears__Vacated_r15c17, _effect_key5_body_clears__Vacated_r15c17, ['Vacated_r15c17']),
    ('key5_body_clears__Vacated_r15c18', _guard_key5_body_clears__Vacated_r15c18, _effect_key5_body_clears__Vacated_r15c18, ['Vacated_r15c18']),
    ('key5_body_clears__Vacated_r16c14', _guard_key5_body_clears__Vacated_r16c14, _effect_key5_body_clears__Vacated_r16c14, ['Vacated_r16c14']),
    ('key5_body_clears__Vacated_r16c15', _guard_key5_body_clears__Vacated_r16c15, _effect_key5_body_clears__Vacated_r16c15, ['Vacated_r16c15']),
    ('key5_body_clears__Vacated_r16c17', _guard_key5_body_clears__Vacated_r16c17, _effect_key5_body_clears__Vacated_r16c17, ['Vacated_r16c17']),
    ('key5_body_clears__Vacated_r16c18', _guard_key5_body_clears__Vacated_r16c18, _effect_key5_body_clears__Vacated_r16c18, ['Vacated_r16c18']),
    ('key5_body_clears__Vacated_r17c14', _guard_key5_body_clears__Vacated_r17c14, _effect_key5_body_clears__Vacated_r17c14, ['Vacated_r17c14']),
    ('key5_body_clears__Vacated_r17c15', _guard_key5_body_clears__Vacated_r17c15, _effect_key5_body_clears__Vacated_r17c15, ['Vacated_r17c15']),
    ('key5_body_clears__Vacated_r17c16', _guard_key5_body_clears__Vacated_r17c16, _effect_key5_body_clears__Vacated_r17c16, ['Vacated_r17c16']),
    ('key5_body_clears__Vacated_r17c17', _guard_key5_body_clears__Vacated_r17c17, _effect_key5_body_clears__Vacated_r17c17, ['Vacated_r17c17']),
    ('key5_body_clears__Vacated_r17c18', _guard_key5_body_clears__Vacated_r17c18, _effect_key5_body_clears__Vacated_r17c18, ['Vacated_r17c18']),
    ('key5_body_clears__Vacated_r18c14', _guard_key5_body_clears__Vacated_r18c14, _effect_key5_body_clears__Vacated_r18c14, ['Vacated_r18c14']),
    ('key5_body_clears__Vacated_r18c15', _guard_key5_body_clears__Vacated_r18c15, _effect_key5_body_clears__Vacated_r18c15, ['Vacated_r18c15']),
    ('key5_body_clears__Vacated_r18c16', _guard_key5_body_clears__Vacated_r18c16, _effect_key5_body_clears__Vacated_r18c16, ['Vacated_r18c16']),
    ('key5_body_clears__Vacated_r18c17', _guard_key5_body_clears__Vacated_r18c17, _effect_key5_body_clears__Vacated_r18c17, ['Vacated_r18c17']),
    ('key5_body_clears__Vacated_r18c18', _guard_key5_body_clears__Vacated_r18c18, _effect_key5_body_clears__Vacated_r18c18, ['Vacated_r18c18']),
    ('key5_body_respawns__Glyph9_r1c1', _guard_key5_body_respawns__Glyph9_r1c1, _effect_key5_body_respawns__Glyph9_r1c1, ['Glyph9_r1c1']),
    ('key5_body_respawns__Glyph9_r1c2', _guard_key5_body_respawns__Glyph9_r1c2, _effect_key5_body_respawns__Glyph9_r1c2, ['Glyph9_r1c2']),
    ('key5_body_respawns__Glyph9_r1c3', _guard_key5_body_respawns__Glyph9_r1c3, _effect_key5_body_respawns__Glyph9_r1c3, ['Glyph9_r1c3']),
    ('key5_body_respawns__Glyph9_r2c1', _guard_key5_body_respawns__Glyph9_r2c1, _effect_key5_body_respawns__Glyph9_r2c1, ['Glyph9_r2c1']),
    ('key5_body_respawns__Glyph9_r2c3', _guard_key5_body_respawns__Glyph9_r2c3, _effect_key5_body_respawns__Glyph9_r2c3, ['Glyph9_r2c3']),
    ('key5_body_respawns__Glyph9_r3c1', _guard_key5_body_respawns__Glyph9_r3c1, _effect_key5_body_respawns__Glyph9_r3c1, ['Glyph9_r3c1']),
    ('key5_body_respawns__Glyph9_r3c2', _guard_key5_body_respawns__Glyph9_r3c2, _effect_key5_body_respawns__Glyph9_r3c2, ['Glyph9_r3c2']),
    ('key5_body_respawns__Glyph9_r3c3', _guard_key5_body_respawns__Glyph9_r3c3, _effect_key5_body_respawns__Glyph9_r3c3, ['Glyph9_r3c3']),
    ('key5_body_respawns__Glyph9_r5c1', _guard_key5_body_respawns__Glyph9_r5c1, _effect_key5_body_respawns__Glyph9_r5c1, ['Glyph9_r5c1']),
    ('key5_body_respawns__Glyph9_r5c2', _guard_key5_body_respawns__Glyph9_r5c2, _effect_key5_body_respawns__Glyph9_r5c2, ['Glyph9_r5c2']),
    ('key5_body_respawns__Glyph9_r5c3', _guard_key5_body_respawns__Glyph9_r5c3, _effect_key5_body_respawns__Glyph9_r5c3, ['Glyph9_r5c3']),
    ('key5_body_respawns__Glyph9_r8c14', _guard_key5_body_respawns__Glyph9_r8c14, _effect_key5_body_respawns__Glyph9_r8c14, ['Glyph9_r8c14']),
    ('key5_body_respawns__Glyph9_r8c15', _guard_key5_body_respawns__Glyph9_r8c15, _effect_key5_body_respawns__Glyph9_r8c15, ['Glyph9_r8c15']),
    ('key5_body_respawns__Glyph9_r8c16', _guard_key5_body_respawns__Glyph9_r8c16, _effect_key5_body_respawns__Glyph9_r8c16, ['Glyph9_r8c16']),
    ('key5_body_respawns__Glyph9_r8c17', _guard_key5_body_respawns__Glyph9_r8c17, _effect_key5_body_respawns__Glyph9_r8c17, ['Glyph9_r8c17']),
    ('key5_body_respawns__Glyph9_r8c18', _guard_key5_body_respawns__Glyph9_r8c18, _effect_key5_body_respawns__Glyph9_r8c18, ['Glyph9_r8c18']),
    ('key5_body_respawns__Glyph9_r9c14', _guard_key5_body_respawns__Glyph9_r9c14, _effect_key5_body_respawns__Glyph9_r9c14, ['Glyph9_r9c14']),
    ('key5_body_respawns__Glyph9_r9c15', _guard_key5_body_respawns__Glyph9_r9c15, _effect_key5_body_respawns__Glyph9_r9c15, ['Glyph9_r9c15']),
    ('key5_body_respawns__Glyph9_r9c16', _guard_key5_body_respawns__Glyph9_r9c16, _effect_key5_body_respawns__Glyph9_r9c16, ['Glyph9_r9c16']),
    ('key5_body_respawns__Glyph9_r9c17', _guard_key5_body_respawns__Glyph9_r9c17, _effect_key5_body_respawns__Glyph9_r9c17, ['Glyph9_r9c17']),
    ('key5_body_respawns__Glyph9_r9c18', _guard_key5_body_respawns__Glyph9_r9c18, _effect_key5_body_respawns__Glyph9_r9c18, ['Glyph9_r9c18']),
    ('key5_body_respawns__Glyph9_r10c14', _guard_key5_body_respawns__Glyph9_r10c14, _effect_key5_body_respawns__Glyph9_r10c14, ['Glyph9_r10c14']),
    ('key5_body_respawns__Glyph9_r10c15', _guard_key5_body_respawns__Glyph9_r10c15, _effect_key5_body_respawns__Glyph9_r10c15, ['Glyph9_r10c15']),
    ('key5_body_respawns__Glyph9_r10c17', _guard_key5_body_respawns__Glyph9_r10c17, _effect_key5_body_respawns__Glyph9_r10c17, ['Glyph9_r10c17']),
    ('key5_body_respawns__Glyph9_r10c18', _guard_key5_body_respawns__Glyph9_r10c18, _effect_key5_body_respawns__Glyph9_r10c18, ['Glyph9_r10c18']),
    ('key5_body_respawns__Glyph9_r11c14', _guard_key5_body_respawns__Glyph9_r11c14, _effect_key5_body_respawns__Glyph9_r11c14, ['Glyph9_r11c14']),
    ('key5_body_respawns__Glyph9_r11c15', _guard_key5_body_respawns__Glyph9_r11c15, _effect_key5_body_respawns__Glyph9_r11c15, ['Glyph9_r11c15']),
    ('key5_body_respawns__Glyph9_r11c16', _guard_key5_body_respawns__Glyph9_r11c16, _effect_key5_body_respawns__Glyph9_r11c16, ['Glyph9_r11c16']),
    ('key5_body_respawns__Glyph9_r11c17', _guard_key5_body_respawns__Glyph9_r11c17, _effect_key5_body_respawns__Glyph9_r11c17, ['Glyph9_r11c17']),
    ('key5_body_respawns__Glyph9_r11c18', _guard_key5_body_respawns__Glyph9_r11c18, _effect_key5_body_respawns__Glyph9_r11c18, ['Glyph9_r11c18']),
    ('key5_body_respawns__Glyph9_r12c14', _guard_key5_body_respawns__Glyph9_r12c14, _effect_key5_body_respawns__Glyph9_r12c14, ['Glyph9_r12c14']),
    ('key5_body_respawns__Glyph9_r12c15', _guard_key5_body_respawns__Glyph9_r12c15, _effect_key5_body_respawns__Glyph9_r12c15, ['Glyph9_r12c15']),
    ('key5_body_respawns__Glyph9_r12c16', _guard_key5_body_respawns__Glyph9_r12c16, _effect_key5_body_respawns__Glyph9_r12c16, ['Glyph9_r12c16']),
    ('key5_body_respawns__Glyph9_r12c17', _guard_key5_body_respawns__Glyph9_r12c17, _effect_key5_body_respawns__Glyph9_r12c17, ['Glyph9_r12c17']),
    ('key5_body_respawns__Glyph9_r12c18', _guard_key5_body_respawns__Glyph9_r12c18, _effect_key5_body_respawns__Glyph9_r12c18, ['Glyph9_r12c18']),
    ('key5_body_respawns__Glyph9_r63c62', _guard_key5_body_respawns__Glyph9_r63c62, _effect_key5_body_respawns__Glyph9_r63c62, ['Glyph9_r63c62']),
    ('key5_body_respawns__Glyph9_r63c63', _guard_key5_body_respawns__Glyph9_r63c63, _effect_key5_body_respawns__Glyph9_r63c63, ['Glyph9_r63c63']),
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
        Glyph9_r1c1_pos=(1, 1),
        Glyph9_r1c1_color=9,
        Glyph9_r1c2_pos=(1, 2),
        Glyph9_r1c2_color=9,
        Glyph9_r1c3_pos=(1, 3),
        Glyph9_r1c3_color=9,
        Glyph9_r2c1_pos=(2, 1),
        Glyph9_r2c1_color=9,
        Glyph9_r2c3_pos=(2, 3),
        Glyph9_r2c3_color=9,
        Glyph9_r3c1_pos=(3, 1),
        Glyph9_r3c1_color=9,
        Glyph9_r3c2_pos=(3, 2),
        Glyph9_r3c2_color=9,
        Glyph9_r3c3_pos=(3, 3),
        Glyph9_r3c3_color=9,
        Glyph9_r5c1_pos=(5, 1),
        Glyph9_r5c1_color=9,
        Glyph9_r5c2_pos=(5, 2),
        Glyph9_r5c2_color=9,
        Glyph9_r5c3_pos=(5, 3),
        Glyph9_r5c3_color=9,
        Glyph9_r8c14_pos=(8, 14),
        Glyph9_r8c14_color=9,
        Glyph9_r8c15_pos=(8, 15),
        Glyph9_r8c15_color=9,
        Glyph9_r8c16_pos=(8, 16),
        Glyph9_r8c16_color=9,
        Glyph9_r8c17_pos=(8, 17),
        Glyph9_r8c17_color=9,
        Glyph9_r8c18_pos=(8, 18),
        Glyph9_r8c18_color=9,
        Glyph9_r9c14_pos=(9, 14),
        Glyph9_r9c14_color=9,
        Glyph9_r9c15_pos=(9, 15),
        Glyph9_r9c15_color=9,
        Glyph9_r9c16_pos=(9, 16),
        Glyph9_r9c16_color=9,
        Glyph9_r9c17_pos=(9, 17),
        Glyph9_r9c17_color=9,
        Glyph9_r9c18_pos=(9, 18),
        Glyph9_r9c18_color=9,
        Glyph9_r10c14_pos=(10, 14),
        Glyph9_r10c14_color=9,
        Glyph9_r10c15_pos=(10, 15),
        Glyph9_r10c15_color=9,
        Glyph9_r10c17_pos=(10, 17),
        Glyph9_r10c17_color=9,
        Glyph9_r10c18_pos=(10, 18),
        Glyph9_r10c18_color=9,
        Glyph9_r11c14_pos=(11, 14),
        Glyph9_r11c14_color=9,
        Glyph9_r11c15_pos=(11, 15),
        Glyph9_r11c15_color=9,
        Glyph9_r11c16_pos=(11, 16),
        Glyph9_r11c16_color=9,
        Glyph9_r11c17_pos=(11, 17),
        Glyph9_r11c17_color=9,
        Glyph9_r11c18_pos=(11, 18),
        Glyph9_r11c18_color=9,
        Glyph9_r12c14_pos=(12, 14),
        Glyph9_r12c14_color=9,
        Glyph9_r12c15_pos=(12, 15),
        Glyph9_r12c15_color=9,
        Glyph9_r12c16_pos=(12, 16),
        Glyph9_r12c16_color=9,
        Glyph9_r12c17_pos=(12, 17),
        Glyph9_r12c17_color=9,
        Glyph9_r12c18_pos=(12, 18),
        Glyph9_r12c18_color=9,
        Glyph9_r63c62_pos=(63, 62),
        Glyph9_r63c62_color=9,
        Glyph9_r63c63_pos=(63, 63),
        Glyph9_r63c63_color=9,
        Vacated_r14c14_pos=(14, 14),
        Vacated_r14c14_color=5,
        Vacated_r14c15_pos=(14, 15),
        Vacated_r14c15_color=5,
        Vacated_r14c16_pos=(14, 16),
        Vacated_r14c16_color=5,
        Vacated_r14c17_pos=(14, 17),
        Vacated_r14c17_color=5,
        Vacated_r14c18_pos=(14, 18),
        Vacated_r14c18_color=5,
        Vacated_r15c14_pos=(15, 14),
        Vacated_r15c14_color=5,
        Vacated_r15c15_pos=(15, 15),
        Vacated_r15c15_color=5,
        Vacated_r15c16_pos=(15, 16),
        Vacated_r15c16_color=5,
        Vacated_r15c17_pos=(15, 17),
        Vacated_r15c17_color=5,
        Vacated_r15c18_pos=(15, 18),
        Vacated_r15c18_color=5,
        Vacated_r16c14_pos=(16, 14),
        Vacated_r16c14_color=5,
        Vacated_r16c15_pos=(16, 15),
        Vacated_r16c15_color=5,
        Vacated_r16c17_pos=(16, 17),
        Vacated_r16c17_color=5,
        Vacated_r16c18_pos=(16, 18),
        Vacated_r16c18_color=5,
        Vacated_r17c14_pos=(17, 14),
        Vacated_r17c14_color=5,
        Vacated_r17c15_pos=(17, 15),
        Vacated_r17c15_color=5,
        Vacated_r17c16_pos=(17, 16),
        Vacated_r17c16_color=5,
        Vacated_r17c17_pos=(17, 17),
        Vacated_r17c17_color=5,
        Vacated_r17c18_pos=(17, 18),
        Vacated_r17c18_color=5,
        Vacated_r18c14_pos=(18, 14),
        Vacated_r18c14_color=5,
        Vacated_r18c15_pos=(18, 15),
        Vacated_r18c15_color=5,
        Vacated_r18c16_pos=(18, 16),
        Vacated_r18c16_color=5,
        Vacated_r18c17_pos=(18, 17),
        Vacated_r18c17_color=5,
        Vacated_r18c18_pos=(18, 18),
        Vacated_r18c18_color=5,
        Spent_r1c5_pos=(1, 5),
        Spent_r1c5_color=1,
        Spent_r1c6_pos=(1, 6),
        Spent_r1c6_color=1,
        Spent_r1c7_pos=(1, 7),
        Spent_r1c7_color=1,
        Spent_r2c5_pos=(2, 5),
        Spent_r2c5_color=1,
        Spent_r2c6_pos=(2, 6),
        Spent_r2c6_color=1,
        Spent_r2c7_pos=(2, 7),
        Spent_r2c7_color=1,
        Spent_r3c5_pos=(3, 5),
        Spent_r3c5_color=1,
        Spent_r3c6_pos=(3, 6),
        Spent_r3c6_color=1,
        Spent_r3c7_pos=(3, 7),
        Spent_r3c7_color=1,
    )
