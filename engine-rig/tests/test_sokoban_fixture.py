"""Fixture D: the geometry the deadlock and probe tests reason about is real."""

import os
from collections import deque

import pytest

from engines.fd_adapter import search as fd_search
from engines.fd_adapter.pddl import (
    ground_actions,
    parse_domain,
    parse_problem,
    static_predicates,
)
from fixtures import sokoban


@pytest.fixture(scope="module")
def domain():
    with open(sokoban.DOMAIN_PATH, "r", encoding="utf-8") as fh:
        return parse_domain(fh.read())


def problem_of(level):
    with open(level.path, "r", encoding="utf-8") as fh:
        return parse_problem(fh.read())


# ------------------------------------------------------------ reproducibility

def test_regenerating_the_fixture_is_byte_identical(tmp_path):
    before = {}
    for path in [sokoban.DOMAIN_PATH] + [level.path for level in sokoban.LEVELS]:
        with open(path, "rb") as fh:
            before[path] = fh.read()
    sokoban.write()
    for path, content in before.items():
        with open(path, "rb") as fh:
            assert fh.read() == content, path


def test_the_files_are_lf_only():
    """The rig pins LF; a CRLF fixture would break byte-stability elsewhere."""
    for path in [sokoban.DOMAIN_PATH] + [level.path for level in sokoban.LEVELS]:
        with open(path, "rb") as fh:
            assert b"\r\n" not in fh.read(), path


# ------------------------------------------------------------------ geometry

def test_the_open_board_has_four_dead_corners_and_no_goal_sits_in_one():
    corners = sokoban.OPEN4.corners()
    assert [sokoban.OPEN4.cell_name(c) for c in corners] == ["c11", "c14", "c41", "c44"]
    assert not set(corners) & set(sokoban.OPEN4.goal_cells())
    assert not set(corners) & set(sokoban.OPEN4FAR.goal_cells())


def test_the_ring_is_a_one_wide_corridor():
    """Every ring cell has at most two floor neighbours -- that is what "1-wide"
    means, and it is why a box in it can never be turned."""
    for cell in sokoban.RING.floors():
        neighbours = [
            sokoban.RING.neighbour(cell, d) for d in sokoban.DIRECTIONS
        ]
        assert sum(1 for n in neighbours if n is not None) <= 2


def test_adjacency_is_static_so_grounding_can_prune_on_it(domain):
    assert "adj" in static_predicates(domain)
    assert "at" not in static_predicates(domain)
    assert "clear" not in static_predicates(domain)


# -------------------------------------------------------------- the instances

def test_the_easy_level_has_the_hand_derived_optimum(domain):
    """6, argued in engines/deadlock_carver/README.md and not read off the search.

    Two boxes need one push each (2); the player starts 3 moves from the nearest
    pushing cell and 1 move separates the two pushing cells once the first push
    lands it on the box's old square: 3 + 1 + 1 + 1 = 6.
    """
    result = fd_search.search(domain, problem_of(sokoban.OPEN4))
    assert result.length == sokoban.OPEN4.optimum == 6


def test_the_ring_goal_is_one_push(domain):
    result = fd_search.search(domain, problem_of(sokoban.RING))
    assert result.length == sokoban.RING.optimum == 1


def test_a_box_can_never_leave_row_one_of_the_ring(domain):
    """The claim `ringstuck` and the p_side probe both rest on, by exhaustion."""
    problem = problem_of(sokoban.RING)
    actions, start, _ = fd_search.strip_static(
        domain, problem, ground_actions(domain, problem)
    )
    seen = {start}
    queue = deque([start])
    box_cells = set()
    while queue:
        state = queue.popleft()
        for atom in state:
            if atom[0] == "at":
                box_cells.add(atom[2])
        for action in actions:
            if not fd_search.applicable(action, state):
                continue
            nxt = fd_search.successor(action, state)
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    assert box_cells == {"c11", "c12", "c13", "c14"}
    assert "c31" not in box_cells          # the p_side / ringstuck configuration


def test_the_stuck_instance_really_has_no_plan(domain):
    result = fd_search.search(domain, problem_of(sokoban.RING_STUCK))
    assert result.plan is None
