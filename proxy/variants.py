"""The variant injection layer: deterministic rewriting at the proxy.

We do not rewrite games. The environment is hosted, so a wrapper cannot touch
the server's internal dynamics, and pretending otherwise would produce variants
whose truth we could not state. The operator library is therefore limited to
the **wrapper-legal set** -- the four things a wrapper provably can do:

    forbid_action / remap_action   the action alphabet the arm may reach
    step_limit                     how many commands the episode allows
    observation_loss               a loss declared at the observation layer
    win_tighten                    a stricter victory test than the server's

That set is small and it is enough: forbidding the only action that crosses a
gap, or declaring a loss on the only cell a path must traverse, constructs an
unsolvable variant whose unsolvability follows from the construction.

**Every variant must carry a constructive justification.** An exam needs ground
truth, and ground truth comes from construction, not from running the variant
and seeing what happened. `Variant.load` refuses a spec without one.

Every rewrite here is a pure function of (spec, session counters, response), so
a variant run replays exactly like an unmodified one.
"""

import glob
import json
import os
from typing import Any, Dict, List, Optional

from .ledger import canonical, sha256
from .paths import VARIANTS_DIR

#: The wrapper-legal set. Nothing outside it can be expressed, by construction.
LEGAL_OPERATORS = ("forbid_action", "remap_action", "step_limit",
                   "observation_loss", "win_tighten")

CLAIMS = ("solvable", "unsolvable", "unchanged")


class VariantSpecError(ValueError):
    pass


def _require(spec: Dict[str, Any], key: str, kind: type, where: str) -> Any:
    if key not in spec:
        raise VariantSpecError("%s: missing required field %r" % (where, key))
    value = spec[key]
    if not isinstance(value, kind):
        raise VariantSpecError(
            "%s: %r must be %s, got %s" % (where, key, kind.__name__, type(value).__name__))
    return value


class Variant:
    """A loaded, validated variant spec plus its hash."""

    def __init__(self, spec: Dict[str, Any], source: Optional[str] = None):
        self.spec = spec
        self.source = source
        where = source or spec.get("variant_id", "<spec>")

        self.variant_id = _require(spec, "variant_id", str, where)
        self.base_game = _require(spec, "base_game", str, where)
        self.claim = _require(spec, "claim", str, where)
        if self.claim not in CLAIMS:
            raise VariantSpecError("%s: claim must be one of %s" % (where, list(CLAIMS)))

        justification = _require(spec, "justification", str, where).strip()
        if len(justification) < 40:
            raise VariantSpecError(
                "%s: `justification` must say why the claim follows from the "
                "construction. An exam's ground truth comes from construction, "
                "not from running it." % where)
        self.justification = justification

        self.operators: List[Dict[str, Any]] = _require(spec, "operators", list, where)
        if not self.operators:
            raise VariantSpecError("%s: a variant with no operators is the base game" % where)
        for i, op in enumerate(self.operators):
            if not isinstance(op, dict):
                raise VariantSpecError("%s: operators[%d] is not an object" % (where, i))
            kind = op.get("op")
            if kind not in LEGAL_OPERATORS:
                raise VariantSpecError(
                    "%s: operators[%d] is %r, outside the wrapper-legal set %s. A "
                    "wrapper cannot change server-internal dynamics, so an operator "
                    "outside this set would be a claim we cannot honour."
                    % (where, i, kind, list(LEGAL_OPERATORS)))
            _validate_operator(op, "%s: operators[%d]" % (where, i))

        self.sha256 = sha256(spec)

    def reference(self, applied: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """What goes into an `env_step`'s `variant` field."""
        return {"variant_id": self.variant_id, "spec_sha256": self.sha256,
                "applied": applied}

    def fingerprint(self) -> Dict[str, Any]:
        return {"variant_id": self.variant_id, "spec_sha256": self.sha256,
                "base_game": self.base_game, "claim": self.claim,
                "operators": [op["op"] for op in self.operators],
                "source": os.path.basename(self.source) if self.source else None}

    # -- loading -----------------------------------------------------------
    @classmethod
    def load(cls, path: str) -> "Variant":
        with open(path, encoding="utf-8") as fh:
            return cls(json.load(fh), source=path)

    @classmethod
    def find(cls, variant_id: str, directory: str = VARIANTS_DIR) -> "Variant":
        for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
            variant = cls.load(path)
            if variant.variant_id == variant_id:
                return variant
        raise KeyError("no variant %r in %s" % (variant_id, directory))

    @classmethod
    def load_all(cls, directory: str = VARIANTS_DIR) -> List["Variant"]:
        return [cls.load(p) for p in sorted(glob.glob(os.path.join(directory, "*.json")))]


def _validate_operator(op: Dict[str, Any], where: str) -> None:
    kind = op["op"]
    if kind == "forbid_action":
        _require(op, "action", str, where)
    elif kind == "remap_action":
        _require(op, "from", str, where)
        _require(op, "to", str, where)
    elif kind == "step_limit":
        limit = _require(op, "limit", int, where)
        if limit < 0:
            raise VariantSpecError("%s: limit must be >= 0" % where)
    elif kind == "observation_loss":
        cells = _require(op, "cells", list, where)
        if not cells:
            raise VariantSpecError("%s: observation_loss needs at least one cell" % where)
        for cell in cells:
            if (not isinstance(cell, list) or len(cell) != 2
                    or not all(isinstance(c, int) for c in cell)):
                raise VariantSpecError("%s: each cell must be [row, col]" % where)
        _require(op, "value", int, where)
    elif kind == "win_tighten":
        require = _require(op, "require", dict, where)
        if require.get("kind") != "score_at_least":
            raise VariantSpecError(
                "%s: the only supported win_tighten test is "
                "{'kind':'score_at_least','value':N}" % where)
        _require(require, "value", int, where)


# -- the runtime ------------------------------------------------------------

class Refusal:
    """The variant declines to forward a command, and says what the arm sees
    instead. Refusal is a rewrite too, so it is recorded as one."""

    def __init__(self, body: Dict[str, Any], applied: Dict[str, Any], status: int = 200):
        self.body = body
        self.applied = applied
        self.status = status


class VariantRuntime:
    """Per-session variant state. One per (variant, session).

    Deliberately holds nothing but counters and the last observed body, both of
    which follow from the recorded action sequence -- so replaying the actions
    reproduces the variant's behaviour exactly.
    """

    def __init__(self, variant: Optional[Variant]):
        self.variant = variant
        self.commands = 0          # commands since the last RESET, RESET excluded
        self.last_body: Optional[Dict[str, Any]] = None
        self.dead = False          # a step_limit or observation_loss has fired

    def _ops(self, kind: str):
        if self.variant is None:
            return []
        return [op for op in self.variant.operators if op["op"] == kind]

    # -- outbound ----------------------------------------------------------
    def before(self, action_name: str) -> Any:
        """Returns either a (possibly rewritten) action name to forward, or a
        `Refusal`."""
        if self.variant is None:
            return action_name

        if action_name == "RESET":
            self.commands = 0
            self.dead = False
            return action_name

        if self.dead:
            return Refusal(self._terminal_body("GAME_OVER"),
                           {"op": "episode_already_over",
                            "note": "a variant loss condition fired earlier"})

        for op in self._ops("forbid_action"):
            if op["action"] == action_name:
                return Refusal(
                    self._unchanged_body(),
                    {"op": "forbid_action", "action": action_name,
                     "effect": "not forwarded; the arm observes an unchanged frame"})

        self.commands += 1
        for op in self._ops("step_limit"):
            if self.commands > op["limit"]:
                self.dead = True
                return Refusal(
                    self._terminal_body("GAME_OVER"),
                    {"op": "step_limit", "limit": op["limit"],
                     "commands": self.commands,
                     "effect": "not forwarded; episode declared over"})

        for op in self._ops("remap_action"):
            if op["from"] == action_name:
                return _Remap(op["to"], {"op": "remap_action", "from": action_name,
                                         "to": op["to"]})
        return action_name

    # -- inbound -----------------------------------------------------------
    def after(self, body: Any) -> Any:
        """Rewrite an upstream response. Returns (body, applied_or_None)."""
        if self.variant is None or not isinstance(body, dict):
            self.last_body = body if isinstance(body, dict) else self.last_body
            return body, None

        applied: List[Dict[str, Any]] = []
        frames = body.get("frame")

        for op in self._ops("observation_loss"):
            hit = _cells_hit(frames, op["cells"], op["value"])
            if hit:
                body = dict(body)
                body["state"] = "GAME_OVER"
                self.dead = True
                applied.append({"op": "observation_loss", "cell": list(hit),
                                "value": op["value"],
                                "effect": "state rewritten to GAME_OVER"})

        for op in self._ops("win_tighten"):
            if body.get("state") == "WIN":
                needed = op["require"]["value"]
                have = body.get("score")
                if have is None or have < needed:
                    body = dict(body)
                    body["state"] = "NOT_FINISHED"
                    applied.append({"op": "win_tighten", "require_score": needed,
                                    "score": have,
                                    "effect": "WIN rewritten to NOT_FINISHED"})

        self.last_body = body
        if len(applied) == 0:
            return body, None
        return body, (applied[0] if len(applied) == 1 else {"op": "multiple",
                                                            "applied": applied})

    # -- synthetic bodies --------------------------------------------------
    def _unchanged_body(self) -> Dict[str, Any]:
        if self.last_body is None:
            return {"state": "NOT_FINISHED", "frame": None, "score": None,
                    "variant_note": "forbidden before the first observation"}
        return dict(self.last_body)

    def _terminal_body(self, state: str) -> Dict[str, Any]:
        body = self._unchanged_body()
        body["state"] = state
        return body


class _Remap:
    def __init__(self, action_name: str, applied: Dict[str, Any]):
        self.action_name = action_name
        self.applied = applied


def _cells_hit(frames: Any, cells: List[List[int]], value: int) -> Optional[List[int]]:
    """First listed cell that holds `value` in the last frame of the response.

    The last frame is the observation the arm acts on; intermediate cascade
    frames are transient and declaring a loss on them would make the variant
    depend on animation timing.
    """
    if not isinstance(frames, list) or not frames:
        return None
    grid = frames[-1]
    if not isinstance(grid, list):
        return None
    for row, col in cells:
        try:
            if grid[row][col] == value:
                return [row, col]
        except (IndexError, TypeError):
            continue
    return None
