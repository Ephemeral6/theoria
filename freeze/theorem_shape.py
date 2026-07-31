#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""freeze/theorem_shape.py — what a Lean theorem PROVES, read off its statement.

Why this module exists (F1, exam → freeze, 2026-08-01)
------------------------------------------------------
`u3.classify_theorem` used to be a prefix matcher over theorem NAMES.  A name
is a label the arm picks freely, so keying the frozen criterion (c) on it made
E1 a naming-convention detector:

  * `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify/
    Deadlock_corner.lean` compiles, reports an EMPTY axiom set on all nine
    theorems, and carries its own two witnesses (`pat_witness`,
    `level_is_winnable`).  `STATS_RULES.md:123` names it as the paradigm of
    what U3 means.  Its theorems are called `dead`, `pat_no_goal`, … — no
    prefix matched, so every one read `kind=unknown`, failed (c) closed, and
    the development was labelled **`vacuous`**.
  * exam reduced it to one fixture pair: the same manual with `inv_*` renamed
    to `frobnicate_*`.  One attained, one was `vacuous`.

The criterion, and the argument for it
--------------------------------------
STATS_RULES §1.2.1 defines non-vacuity **按断言的种类** — by the kind of
ASSERTION.  Its three rows are written as `theorem unsolvable …`,
`invariant …`, `prune …`, which reads like a naming convention but is not one:
the rows are distinguished by what the assertion says, and the frozen table's
own sub-checks are all statements about the *content* (「不变量在初始态成立」,
「每个目标态都被排除」, 「存在至少一个良构状态满足该模式」).

So the kind is decided by the **shape of the statement over the development's
own declarations**, and by nothing else:

  ┌ conclusion is a NEGATIVE claim `G e = false` / `¬ G e` about a declared
  │ predicate G, under a hypothesis in a declared `Prop`-valued inductive
  │ RELATION whose last argument is the conclusion's state:
  │   · the relation's start point is internally anchored (unary relation, e.g.
  │     `Reachable s`) or is a declared state CONSTANT (`ReachFrom s0 s`)
  │       → `unsolvable`  — "from the initial state, no goal is reachable"
  │   · the start point is universally quantified AND carries positive
  │     hypotheses `P start = true`
  │       → `prune`  — conditional unsolvability: "from ANY state matching this
  │         pattern, no goal is reachable".  This is exactly the distinction
  │         `CONTRACTS/deadlock_certificate_v0.1.md` insists on: 「本份证书对
  │         `s₀` 一个字都不说」 — the certificate says nothing about s₀, and it
  │         is the free start state plus the pattern hypothesis that makes it
  │         conditional.  The pattern is READ OFF the theorem: it is the set of
  │         predicates positively hypothesised at the start state.
  ├ conclusion contains `∃`            → `witness`     (a supporting obligation)
  ├ conclusion is a POSITIVE claim `P e = true` / `P e` whose argument mentions
  │ a universally quantified variable  → `invariant`   (a conserved property)
  ├ conclusion is a claim about a CLOSED expression (no bound variables)
  │                                    → `point_claim` (one state, not a law)
  └ anything else                      → `unclassified`

`unclassified` is a statement about THIS ADJUDICATOR, not about the manual.
It is the second half of exam's ask: `vacuous` accuses a manual of having
proved a tautology; `unclassified` confesses that E1 does not know what kind of
assertion this is.  They demand different actions and only one of them is an
accusation, so they may not share a word.

What a name is still allowed to do
----------------------------------
`name_hint()` survives and is reported alongside every verdict, because a
disagreement between the hint and the shape is worth seeing.  It never enters
a decision: nothing in `u3.judge_nonvacuity` reads it.

Residuals, stated rather than hidden
------------------------------------
* The parser handles the fragment the repo's generators actually emit
  (`∀`-prefixed, `→`-chained, `∧`-conjoined statements over `Bool`- or
  `Prop`-valued unary predicates).  A statement outside that fragment reads
  `unclassified` — it fails CLOSED, it does not pass open.
* A `prune` theorem whose pattern conjunction is `{wf, Pat}` is checked against
  co-theorems that mention a SUBSET of those predicates.  A subset is a
  stronger claim (fewer hypotheses), so this direction is sound.
* Definition names (`I`, `Goal`, `Pat`) are never assumed.  Every predicate is
  read out of the statement being judged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Atom", "Theorem", "Development", "parse_development",
    "INVARIANT_KIND", "UNSOLVABLE_KIND", "PRUNE_KIND", "POINT_KIND",
    "WITNESS_KIND", "UNCLASSIFIED_KIND", "KINDS_WITH_A_C_CHECK",
    "name_hint", "strip_comments",
]

# ------------------------------------------------------------------ kinds

INVARIANT_KIND = "invariant"
UNSOLVABLE_KIND = "unsolvable"
PRUNE_KIND = "prune"
POINT_KIND = "point_claim"
WITNESS_KIND = "witness"
UNCLASSIFIED_KIND = "unclassified"

#: The kinds §1.2.1 writes a non-vacuity requirement for.  Every other kind is
#: reported honestly as unchecked; none of them attains.
KINDS_WITH_A_C_CHECK = frozenset({INVARIANT_KIND, UNSOLVABLE_KIND, PRUNE_KIND})


# --------------------------------------------------------------- tokenising

_OPEN = {"(": ")", "{": "}", "[": "]", "⟨": "⟩", "⦃": "⦄"}
_CLOSE = {v: k for k, v in _OPEN.items()}

_BLOCK_COMMENT = re.compile(r"/-.*?-/", re.S)


def strip_comments(src: str) -> str:
    """Remove Lean block and line comments.  Doc comments are comments."""
    src = _BLOCK_COMMENT.sub(" ", src)
    out: List[str] = []
    for line in src.splitlines():
        idx = line.find("--")
        while idx != -1:
            if idx == 0 or line[idx - 1] in " \t(":
                line = line[:idx]
                break
            idx = line.find("--", idx + 1)
        out.append(line)
    return "\n".join(out)


def _match_bracket(text: str, i: int) -> int:
    """Index of the bracket closing the one at `i` (or len(text) - 1)."""
    depth = 0
    for j in range(i, len(text)):
        ch = text[j]
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
            if depth == 0:
                return j
    return len(text) - 1


def _find_top(text: str, needles: Sequence[str], start: int = 0) -> Tuple[int, str]:
    depth = 0
    i = start
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif depth == 0:
            for nd in needles:
                if text.startswith(nd, i):
                    return i, nd
        i += 1
    return -1, ""


def _split_top(text: str, needles: Sequence[str]) -> List[str]:
    parts: List[str] = []
    rest = text
    while True:
        idx, nd = _find_top(rest, needles)
        if idx < 0:
            parts.append(rest)
            return parts
        parts.append(rest[:idx])
        rest = rest[idx + len(nd):]


#: A top-level `=` that is not part of `==`, `!=`, `<=`, `>=`, `=>`, `:=`.
def _find_top_eq(text: str) -> int:
    depth = 0
    for i, ch in enumerate(text):
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            depth -= 1
        elif ch == "=" and depth == 0:
            prev = text[i - 1] if i else " "
            nxt = text[i + 1] if i + 1 < len(text) else " "
            if prev in "=!<>:≠" or nxt in "=>":
                continue
            return i
    return -1


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_'.!?]*")


def _idents(text: str) -> Set[str]:
    return {m.group(0).split(".")[0] for m in _IDENT.finditer(text)}


def _head(text: str) -> Optional[str]:
    t = text.strip()
    m = _IDENT.match(t)
    if not m or m.start() != 0:
        return None
    return m.group(0)


# ------------------------------------------------------------------- atoms

@dataclass(frozen=True)
class Atom:
    """`P e = true` / `P e = false` / `P e` / `¬ P e`, for a declared `P`."""
    pred: str
    arg: str
    polarity: str          # "pos" | "neg"

    def as_dict(self) -> Dict[str, str]:
        return {"pred": self.pred, "arg": self.arg.strip(), "polarity": self.polarity}


_TRUE_LITERALS = {"true", "True"}
_FALSE_LITERALS = {"false", "False"}


def _parse_atom(text: str, defs: Set[str]) -> Optional[Atom]:
    t = text.strip()
    neg = False
    while True:
        t = t.strip()
        if t.startswith("¬"):
            neg = not neg
            t = t[1:]
            continue
        if t.startswith("(") and _match_bracket(t, 0) == len(t) - 1:
            t = t[1:-1]
            continue
        break
    if not t:
        return None
    # A disjunction / iff / arrow is not an atom.
    if _find_top(t, ["∨", "↔", "→", "->"])[0] >= 0:
        return None
    eq = _find_top_eq(t)
    if eq >= 0:
        lhs, rhs = t[:eq].strip(), t[eq + 1:].strip()
        if rhs in _TRUE_LITERALS:
            pol = "neg" if neg else "pos"
        elif rhs in _FALSE_LITERALS:
            pol = "pos" if neg else "neg"
        else:
            return None
        head = _head(lhs)
        if head is None or head not in defs:
            return None
        return Atom(head, lhs[len(head):].strip(), pol)
    head = _head(t)
    if head is None or head not in defs:
        return None
    arg = t[len(head):].strip()
    if not arg:
        return None
    return Atom(head, arg, "neg" if neg else "pos")


def _atoms(text: str, defs: Set[str]) -> List[Atom]:
    """Conjuncts of `text` that are atoms.  Non-atomic conjuncts are dropped —
    they are recorded nowhere because they carry no (c) content, and dropping
    them can only make a check harder to pass."""
    out: List[Atom] = []
    for part in _split_top(text, ["∧"]):
        a = _parse_atom(part, defs)
        if a is not None:
            out.append(a)
    return out


# ---------------------------------------------------------------- theorems

@dataclass
class Theorem:
    name: str
    statement: str
    quantified: Set[str] = field(default_factory=set)
    hypotheses: List[str] = field(default_factory=list)
    conclusion: str = ""
    hyp_atoms: List[Atom] = field(default_factory=list)
    concl_atoms: List[Atom] = field(default_factory=list)
    relation_hyps: List[Tuple[str, List[str]]] = field(default_factory=list)
    has_exists: bool = False
    kind: str = UNCLASSIFIED_KIND
    basis: Dict[str, Any] = field(default_factory=dict)

    def mentions_bound(self, expr: str) -> bool:
        return bool(_idents(expr) & self.quantified)


def _parse_binder_group(inner: str, types: Set[str]) -> Tuple[List[str], Optional[str], bool]:
    """`s : St` → (["s"], "St", is_value).  `h : I s` → (["h"], "I s", False)."""
    idx, _ = _find_top(inner, [":"])
    if idx < 0:
        return [t for t in inner.split() if t], None, True
    names = [t for t in inner[:idx].split() if t]
    ty = inner[idx + 1:].strip()
    return names, ty, (ty in types)


def _split_signature(sig: str, types: Set[str]) -> Tuple[List[str], List[str], str]:
    """Split `(s : St) (h : I s) : concl` into value binders, hypotheses, concl."""
    values: List[str] = []
    hyps: List[str] = []
    i, n = 0, len(sig)
    while i < n:
        ch = sig[i]
        if ch.isspace():
            i += 1
            continue
        if ch == ":":
            return values, hyps, sig[i + 1:]
        if ch in _OPEN:
            j = _match_bracket(sig, i)
            names, ty, is_value = _parse_binder_group(sig[i + 1:j], types)
            if is_value:
                values.extend(names)
            elif ty:
                hyps.append(ty)
            i = j + 1
            continue
        m = _IDENT.match(sig, i)
        i = m.end() if m else i + 1
    return values, hyps, ""


def _strip_foralls(statement: str, types: Set[str]) -> Tuple[List[str], str]:
    """Consume leading `∀ <binders>,` groups, returning the bound value names."""
    names: List[str] = []
    s = statement.strip()
    while s.startswith("∀"):
        body = s[1:]
        idx, _ = _find_top(body, [","])
        if idx < 0:
            break
        head, s = body[:idx], body[idx + 1:].strip()
        rest = head.strip()
        consumed = False
        while rest:
            rest = rest.strip()
            if not rest:
                break
            if rest[0] in _OPEN:
                j = _match_bracket(rest, 0)
                bnames, _ty, is_value = _parse_binder_group(rest[1:j], types)
                if is_value:
                    names.extend(bnames)
                rest = rest[j + 1:]
                consumed = True
                continue
            bnames, _ty, is_value = _parse_binder_group(rest, types)
            if is_value:
                names.extend(bnames)
            rest = ""
            consumed = True
        if not consumed:
            break
    return names, s


# ------------------------------------------------------------- development

_DEF_NAME = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_']*)", re.M)
_ABBREV_NAME = re.compile(r"^\s*abbrev\s+([A-Za-z_][A-Za-z0-9_']*)", re.M)
_STRUCT_NAME = re.compile(r"^\s*structure\s+([A-Za-z_][A-Za-z0-9_']*)", re.M)
_INDUCTIVE = re.compile(
    r"^\s*inductive\s+([A-Za-z_][A-Za-z0-9_']*)(.*?)(?:\bwhere\b|\n\s*\|)", re.M | re.S)
_THM_HEAD = re.compile(r"^\s*(?:theorem|lemma)\s+([A-Za-z_][A-Za-z0-9_'!?]*)", re.M)


@dataclass
class Development:
    defs: Set[str] = field(default_factory=set)
    types: Set[str] = field(default_factory=set)
    relations: Dict[str, int] = field(default_factory=dict)
    constants: Set[str] = field(default_factory=set)
    theorems: Dict[str, Theorem] = field(default_factory=dict)
    parsed: bool = False

    def by_kind(self, kind: str) -> List[Theorem]:
        return [t for t in self.theorems.values() if t.kind == kind]


def _relation_arity(header: str) -> int:
    idx, _ = _find_top(header, [":"])
    binders = header[:idx] if idx >= 0 else header
    tail = header[idx + 1:] if idx >= 0 else ""
    n = 0
    rest = binders.strip()
    while rest.startswith("(") or rest.startswith("{"):
        j = _match_bracket(rest, 0)
        names, _ty, is_value = _parse_binder_group(rest[1:j], set())
        n += len(names)
        rest = rest[j + 1:].strip()
    if tail:
        n += max(0, len(_split_top(tail, ["→", "->"])) - 1)
    return n


def parse_development(src: Optional[str]) -> Development:
    """Parse a Lean development into declarations and classified theorems."""
    dev = Development()
    if not src:
        return dev
    text = strip_comments(src)
    dev.parsed = True
    dev.defs = set(_DEF_NAME.findall(text)) | set(_ABBREV_NAME.findall(text))
    dev.types = set(_STRUCT_NAME.findall(text))
    for m in _INDUCTIVE.finditer(text):
        name, header = m.group(1), m.group(2)
        if re.search(r"\bProp\b", header):
            dev.relations[name] = _relation_arity(header)
        else:
            dev.types.add(name)
    for m in re.finditer(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_']*)\s*:\s*([A-Za-z_][\w.']*)\s*:=",
                         text, re.M):
        if m.group(2) in dev.types:
            dev.constants.add(m.group(1))

    for m in _THM_HEAD.finditer(text):
        name = m.group(1)
        idx, _ = _find_top(text, [":="], m.end())
        if idx < 0:
            continue
        sig = text[m.end():idx]
        values, binder_hyps, statement = _split_signature(sig, dev.types)
        forall_names, body = _strip_foralls(statement, dev.types)
        parts = _split_top(body, ["→", "->"])
        hyps = binder_hyps + [p for p in parts[:-1] if p.strip()]
        concl = parts[-1] if parts else ""
        thm = Theorem(
            name=name,
            statement=" ".join(statement.split()),
            quantified=set(values) | set(forall_names),
            hypotheses=[" ".join(h.split()) for h in hyps],
            conclusion=" ".join(concl.split()),
            has_exists="∃" in concl,
        )
        thm.hyp_atoms = [a for h in hyps for a in _atoms(h, dev.defs)]
        thm.concl_atoms = _atoms(concl, dev.defs)
        for h in hyps:
            head = _head(h)
            if head and head in dev.relations:
                args = [p for p in h.strip()[len(head):].split() if p]
                thm.relation_hyps.append((head, args))
        dev.theorems[name] = thm

    for thm in dev.theorems.values():
        thm.kind, thm.basis = _classify(thm, dev)
    return dev


# ------------------------------------------------------------ classification

def _classify(thm: Theorem, dev: Development) -> Tuple[str, Dict[str, Any]]:
    neg = [a for a in thm.concl_atoms if a.polarity == "neg"]

    # 1. unsolvability family: a negative conclusion about a predicate applied
    #    to the far end of a reachability-shaped relation hypothesis.
    for atom in neg:
        target = atom.arg.strip()
        for rel, args in thm.relation_hyps:
            if not args or args[-1] != target:
                continue
            if len(args) < 2:
                return UNSOLVABLE_KIND, {
                    "rule": "negative conclusion about `%s` under the internally "
                            "anchored relation `%s`" % (atom.pred, rel),
                    "goal_pred": atom.pred, "relation": rel, "start": None,
                    "start_anchor": "internal"}
            start = args[0]
            if start in dev.constants:
                return UNSOLVABLE_KIND, {
                    "rule": "negative conclusion about `%s` reachable from the "
                            "declared state constant `%s`" % (atom.pred, start),
                    "goal_pred": atom.pred, "relation": rel, "start": start,
                    "start_anchor": "constant"}
            if start in thm.quantified:
                pattern = sorted({a.pred for a in thm.hyp_atoms
                                  if a.polarity == "pos" and a.arg.strip() == start})
                if pattern:
                    return PRUNE_KIND, {
                        "rule": "negative conclusion about `%s` from ANY state "
                                "matching %s — conditional unsolvability, the "
                                "start state is quantified and constrained"
                                % (atom.pred, pattern),
                        "goal_pred": atom.pred, "relation": rel, "start": start,
                        "start_anchor": "quantified", "pattern_preds": pattern}
                return UNSOLVABLE_KIND, {
                    "rule": "negative conclusion about `%s` from EVERY state — "
                            "unconditional, no pattern hypothesis on `%s`"
                            % (atom.pred, start),
                    "goal_pred": atom.pred, "relation": rel, "start": start,
                    "start_anchor": "quantified-unconstrained"}

    # 2. an existential is a supporting witness, never the main claim.
    if thm.has_exists:
        return WITNESS_KIND, {"rule": "conclusion is an existential — a witness "
                                      "obligation, not a law about the world"}

    # 3. invariant: a positive claim about a predicate at a quantified state.
    for atom in thm.concl_atoms:
        if atom.polarity == "pos" and thm.mentions_bound(atom.arg):
            return INVARIANT_KIND, {
                "rule": "positive conclusion `%s %s` over the quantified state — "
                        "a conserved property" % (atom.pred, atom.arg.strip()),
                "invariant_pred": atom.pred}

    # 4. a claim about one closed expression is a point, not a law.
    for atom in thm.concl_atoms:
        if not thm.mentions_bound(atom.arg):
            return POINT_KIND, {
                "rule": "claim about the closed expression `%s` — one state, "
                        "no §1.2.1 clause covers it" % atom.arg.strip(),
                "pred": atom.pred, "at": atom.arg.strip()}

    return UNCLASSIFIED_KIND, {
        "rule": "statement shape outside the fragment §1.2.1 defines a "
                "non-vacuity requirement for",
        "conclusion": thm.conclusion}


# --------------------------------------------------------------- name hint

_HINT_PREFIXES = (
    (("inv_", "invariant"), INVARIANT_KIND),
    (("unsolvable", "goal_break", "no_goal"), UNSOLVABLE_KIND),
    (("prune", "deadlock", "dead"), PRUNE_KIND),
)


def name_hint(name: str) -> Optional[str]:
    """The old prefix matcher, demoted.  Reported for contrast, never decisive:
    nothing in `u3.judge_nonvacuity` reads this."""
    n = (name or "").lower()
    for prefixes, kind in _HINT_PREFIXES:
        if n.startswith(prefixes) or n in prefixes:
            return kind
    return None
