"""
Playbook DSL parser — hand-rolled.
Parses playbook.dsl text into PlaybookAST.
Enforces anti-cheat: rejects literal action sequences.
"""

import re
from typing import Optional

from .ast_nodes import (
    PlaybookAST, OrderStmt, PruneStmt, HeuristicStmt, PreferStmt,
)


class PlaybookParseError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


# Patterns that look like literal action sequences
ACTION_SEQ_PATTERNS = [
    # "solution: action, action, action"
    re.compile(r'\b(solution|sequence|steps|moves|path)\s*:', re.IGNORECASE),
    # Comma-separated list of direction-like words (3+ items)
    re.compile(
        r'\b(UP|DOWN|LEFT|RIGHT|NORTH|SOUTH|EAST|WEST|jump\(\d)'
        r'(\s*,\s*(UP|DOWN|LEFT|RIGHT|NORTH|SOUTH|EAST|WEST|jump\(\d)){2,}',
        re.IGNORECASE
    ),
]


def _check_anti_cheat(line: str, lineno: int):
    """Reject lines containing literal action sequences."""
    for pat in ACTION_SEQ_PATTERNS:
        if pat.search(line):
            raise PlaybookParseError(
                f"Literal action sequence detected (anti-cheat violation): {line.strip()!r}",
                lineno,
            )


class PlaybookParser:
    """Parse playbook.dsl text into PlaybookAST."""

    def __init__(self, text: str):
        self.lines = text.splitlines()
        self.pos = 0

    def parse(self) -> PlaybookAST:
        ast = PlaybookAST()
        while self.pos < len(self.lines):
            line = self.lines[self.pos].strip()
            lineno = self.pos + 1

            if not line or line.startswith("#"):
                self.pos += 1
                continue

            # Anti-cheat check on every non-comment line
            _check_anti_cheat(line, lineno)

            if line.startswith("order "):
                ast.statements.append(self._parse_order(line))
            elif line.startswith("prune "):
                ast.statements.append(self._parse_prune(line))
            elif line.startswith("heuristic "):
                ast.statements.append(self._parse_heuristic(line))
            elif line.startswith("prefer "):
                ast.statements.append(self._parse_prefer(line))
            else:
                # Unknown line — could be anti-cheat trigger
                _check_anti_cheat(line, lineno)
                raise PlaybookParseError(
                    f"Unrecognized playbook statement: {line!r}", lineno
                )

            self.pos += 1
        return ast

    def _parse_order(self, line: str) -> OrderStmt:
        # order <landmark-name> [proof: lean|none]
        m = re.match(r'order\s+(\S+)\s*(?:\[proof:\s*(\w+)\])?\s*$', line)
        if not m:
            raise PlaybookParseError(f"Invalid order statement: {line!r}", self.pos + 1)
        return OrderStmt(landmark=m.group(1), proof=m.group(2))

    def _parse_prune(self, line: str) -> PruneStmt:
        # prune <condition> => dead [proof: lean|none]
        # Also accept ⇒
        m = re.match(r'prune\s+(.+?)\s*(?:=>|⇒)\s*dead\s*(?:\[proof:\s*(\w+)\])?\s*$', line)
        if not m:
            raise PlaybookParseError(f"Invalid prune statement: {line!r}", self.pos + 1)
        return PruneStmt(condition=m.group(1).strip(), proof=m.group(2))

    def _parse_heuristic(self, line: str) -> HeuristicStmt:
        # heuristic <name>(<params>) [admissible: lean|none]
        m = re.match(r'heuristic\s+(\w+)\(([^)]*)\)\s*(?:\[admissible:\s*(\w+)\])?\s*$', line)
        if not m:
            raise PlaybookParseError(f"Invalid heuristic statement: {line!r}", self.pos + 1)
        name = m.group(1)
        params = [p.strip() for p in m.group(2).split(",") if p.strip()]
        return HeuristicStmt(name=name, params=params, admissible=m.group(3))

    def _parse_prefer(self, line: str) -> PreferStmt:
        # prefer <name> [ev: k/n]
        m = re.match(r'prefer\s+(\S+)\s*(?:\[ev:\s*(\d+/\d+)\])?\s*$', line)
        if not m:
            raise PlaybookParseError(f"Invalid prefer statement: {line!r}", self.pos + 1)
        return PreferStmt(name=m.group(1), evidence=m.group(2))


def parse_playbook(text: str) -> PlaybookAST:
    """Parse playbook.dsl text into a PlaybookAST."""
    parser = PlaybookParser(text)
    return parser.parse()
