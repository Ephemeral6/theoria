"""The `semantics:` section — A0's local dialect, and a proposal for v0.2.

`A0_REPORT.md` §4 names the worst hole in `dsl_grammar_v0.1`: **the most
important semantic fact about `step` is not in the DSL at all.** The frame
axiom — *if no rule fires for an object, that object is unchanged* — lived in a
comment at the top of `theory.dsl` and was hard-coded three times, once per
backend. A second reader compiling `theory.dsl` alone would get a different
world, which is precisely what the handover test is supposed to punish.

`/CONTRACTS/dsl_grammar_v0.1.md` is frozen and owned by the compiler track, so
this is **not** an edit to the contract. It is a dialect implemented here, used
here, and written up as a formal extension request in
`proposals/dsl_grammar_v0.2_semantics.md`.

## The section

```
semantics:
  frame persist                     # persist | reset
  conflict exclusive                # exclusive | priority: r1 > r2 > ...
  cascade single_frame              # single_frame | multi_frame
```

Three statements, three closed value sets, no free text. Each closes a hole the
A0 sprint actually fell into:

| statement | closes | why it is a per-world fact and not a framework constant |
|---|---|---|
| `frame` | E-03 | a world *could* reset unmentioned objects; sokoban does not, a cellular automaton does |
| `conflict` | constraint 9 | the contract offers two discharge routes — provable disjointness, or an explicit total priority — and the manual has to say which it is claiming |
| `cascade` | Theoria 1.8's open question | whether one action yields one frame or a sequence is exactly what 1.8 defers to the trace, and it is a property of the world, not of the framework |

`cascade single_frame` carries a second commitment that cost this sprint a real
bug: **every guard is read against the pre-state, and all effects apply
simultaneously.** Sequential application let `press_left` recolour the Button and
`door_opens_left` then find colour 8 and silently not fire. Naming the semantics
is what makes that a violation rather than an implementation detail.

## Compatibility, stated rather than hoped

The v0.1 parser skips lines it does not recognise, so a manual carrying this
section still parses there — **silently, and to a different world**. That is the
hazard, not the feature. This module therefore *requires* the section: a manual
without it is rejected here rather than compiled under an assumed default. The
proposal asks the compiler track to make it mandatory in v0.2 for the same
reason.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

FRAME_VALUES = ("persist", "reset")
CASCADE_VALUES = ("single_frame", "multi_frame")


class SemanticsError(Exception):
    """The `semantics:` section is missing, malformed, or claims something
    this backend does not implement.  Never defaulted, never guessed."""


@dataclass
class Semantics:
    frame: str
    conflict: str                                  # "exclusive" | "priority"
    cascade: str
    priority: List[str] = field(default_factory=list)

    @property
    def simultaneous(self) -> bool:
        return self.cascade == "single_frame"

    def as_json(self) -> Dict[str, object]:
        out = {"frame": self.frame, "conflict": self.conflict,
               "cascade": self.cascade}
        if self.priority:
            out["priority"] = list(self.priority)
        return out

    def rendering(self) -> List[str]:
        """Deterministic natural language, for theory.md.  No LLM."""
        lines = []
        if self.frame == "persist":
            lines.append("If no rule applies to an object in a turn, that object "
                         "is exactly as it was.")
        else:
            lines.append("If no rule applies to an object in a turn, that object "
                         "returns to its starting condition.")
        if self.conflict == "exclusive":
            lines.append("At most one rule may apply to any one object in any one "
                         "turn; the rules are written so that this cannot fail.")
        else:
            lines.append("If several rules apply to one object, the earlier one in "
                         "this order wins: " + " > ".join(self.priority) + ".")
        if self.cascade == "single_frame":
            lines.append("One action produces one new situation. Every rule reads "
                         "the situation as it was before the action, and all of "
                         "their effects happen together.")
        else:
            lines.append("One action may produce a run of situations, each rule "
                         "reacting to the one before it, until nothing more "
                         "changes.")
        return lines


def _from_upstream(text: str) -> Optional[Semantics]:
    """Use the compiler track's own parser once it has one.

    The `theory-compiler` track adopted this proposal mid-sprint: its parser now
    has a `semantics:` section with the same three statements and the same
    refusal to default. Same pattern as `mdl_segmenter`'s `split_by_color` — when
    upstream grows the feature, delegate to it and keep the local implementation
    as the fallback, so this directory still runs against the version tagged at
    `theory-compiler`'s M8.

    Returns `None` when upstream has no such section, so the local parser runs.
    A rejection from upstream is **not** a reason to fall back — that is an
    answer — but it is re-raised as this module's own `SemanticsError`, because
    a caller should not have to know which of the two implementations replied.
    """
    try:
        from theory_compiler.parser import theory_parser as _tp
    except ImportError:
        return None
    upstream_error = getattr(_tp, "SemanticsError", None)
    if upstream_error is None:
        return None
    try:
        section = getattr(_tp.parse_theory(text), "semantics", None)
    except upstream_error as exc:
        raise SemanticsError(str(exc)) from exc
    if section is None:
        return None
    return Semantics(
        frame=getattr(section, "frame"),
        conflict=getattr(section, "conflict"),
        cascade=getattr(section, "cascade"),
        priority=list(getattr(section, "priority", []) or []),
    )


def parse_semantics(text: str) -> Semantics:
    """Read the `semantics:` section out of a theory.dsl source."""
    upstream = _from_upstream(text)
    if upstream is not None:
        return upstream

    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("semantics:"):
            start = i + 1
            break
    if start is None:
        raise SemanticsError(
            "theory.dsl has no `semantics:` section. The frame axiom, the "
            "conflict policy and the cascade semantics are facts about the world "
            "and must be in the manual; this backend will not assume them. "
            "See proposals/dsl_grammar_v0.2_semantics.md."
        )

    frame = conflict = cascade = None
    priority: List[str] = []
    for line in lines[start:]:
        if line.strip() and not line[0].isspace():
            break                                   # next top-level section
        body = line.strip()
        if not body or body.startswith("#"):
            continue
        body = body.split("#", 1)[0].strip()
        if body.startswith("frame "):
            frame = body[len("frame "):].strip()
            if frame not in FRAME_VALUES:
                raise SemanticsError("frame must be one of %r, got %r"
                                     % (list(FRAME_VALUES), frame))
        elif body.startswith("conflict "):
            rest = body[len("conflict "):].strip()
            if rest == "exclusive":
                conflict = "exclusive"
            elif rest.startswith("priority:"):
                conflict = "priority"
                priority = [p.strip() for p in
                            re.split(r">", rest[len("priority:"):]) if p.strip()]
                if len(priority) < 2:
                    raise SemanticsError(
                        "conflict priority needs a total order of at least two "
                        "rules, got %r" % (priority,))
            else:
                raise SemanticsError(
                    "conflict must be `exclusive` or `priority: r1 > r2 ...`, "
                    "got %r" % rest)
        elif body.startswith("cascade "):
            cascade = body[len("cascade "):].strip()
            if cascade not in CASCADE_VALUES:
                raise SemanticsError("cascade must be one of %r, got %r"
                                     % (list(CASCADE_VALUES), cascade))
        else:
            raise SemanticsError("unknown statement in `semantics:`: %r" % body)

    missing = [name for name, value in
               (("frame", frame), ("conflict", conflict), ("cascade", cascade))
               if value is None]
    if missing:
        raise SemanticsError("`semantics:` is missing %s" % ", ".join(missing))
    return Semantics(frame=frame, conflict=conflict, cascade=cascade,
                     priority=priority)


def check_backend_support(semantics: Semantics) -> None:
    """Raise on anything the A0 backends do not implement.

    Following `fd_adapter`'s rule: outside the supported subset is an error, not
    a silent approximation.
    """
    if semantics.frame != "persist":
        raise SemanticsError("this backend implements `frame persist` only; "
                             "`%s` would need a different step" % semantics.frame)
    if semantics.cascade != "single_frame":
        raise SemanticsError(
            "this backend implements `cascade single_frame` only. "
            "`multi_frame` means one action yields a frame *sequence*, which "
            "changes the shape of step, of the replay comparison and of the PDDL "
            "encoding — see Theoria 1.8's cascade question.")
    if semantics.conflict != "exclusive":
        raise SemanticsError(
            "this backend implements `conflict exclusive` only; a declared "
            "priority order would have to be compiled into the rule dispatch")
