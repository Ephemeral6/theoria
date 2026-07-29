"""Say the same world in more words, or fewer, and hold the state space still.

Axis A varies |S| on the peg family, and on that family it *cannot* do anything
else: peg-N has n predicates and exactly 2^n states, so "how many states" and
"how many predicates" are the same number wearing two hats.  Every row of axis A
is therefore mute on the question this module exists to ask -- **when IC3 slows
down, is it paying for the states or for the predicates?**

The only way to ask that is to change one and pin the other.  This module pins
the state space *exactly* -- same states, same labelled edges, same initial
state, same bad set, same answer -- and changes only how many booleans are spent
saying it.  Three schemes, all of them things a person writing a manual actually
does:

    binary      the fewest booleans that can tell |S| states apart, and
                nothing else: bit i of the state's index.  The floor.
                                                          m = ceil(log2 |S|)
    native      the variables the world came with.                     m = n
    dual(k)     the first k variables are *also* declared under a second
                name for their negation -- `free_pos3` beside `pos3`.
                A modeller who writes both `occupied(i)` and `free(i)`
                has done exactly this.                             m = n + k
    onehot      one predicate per state: `is_01111111`.  The manual
                that names every situation instead of describing it. m = |S|

`binary` is the axis's other direction and it matters as much as the padding
ones.  On the peg family it is nothing new -- peg-N spends n booleans on 2^n
states, which is already the floor -- but a `worldgen` world one-hots the agent's
position over seventeen floor cells, so its native encoding sits far above the
floor and can be *compressed*.  Both directions are asked because a ladder that
only ever adds predicates cannot distinguish "IC3 pays for predicates" from "IC3
pays for the particular predicates a padding scheme adds".

A re-encoding is a *bijection on states*, so it changes no fact about the world.
`0111` still cannot reach `0100` whatever alphabet the question is asked in, and
IC3's *answer* -- an invariant exists, or the goal is genuinely reachable -- is
invariant with it.

**The recorded verdict is a weaker thing than the answer, and an adversarial
pass caught this module overclaiming it.**  IC3 converges at a different frame
under different vocabularies -- on peg-6 the same problem converges at frame 7
under `native` and frame 3 under `onehot` -- so `max_levels` binds differently
per encoding, and a rung can report `level-cap` for a reason that is about the
alphabet rather than about the world.  With the ladder's `max_levels = 64`
nothing on it comes near binding (the deepest convergence measured is frame 20),
but the caveat is not conditional on that: any table that tightens the cap must
read `converged_at_frame` alongside the verdict, and `IC3_BOUNDS.md` carries the
column for this reason.

What is emphatically *not* invariant is the invariant itself: a clause set over
`dual` vocabulary is a different object from a clause set over `native`
vocabulary, and comparing their `n_clauses` directly would be comparing two
languages.  The quantity that *is* comparable across
every rung is the **set of states the invariant holds on** -- `n_satisfying` out
of `|S|` -- because that is a fact about the world rather than about the
alphabet.  Read the ladder on coverage and wall clock; read clause counts only
within one scheme.

**Definitions, not functions.**  Each new predicate is declared as a small piece
of data rather than as a closure:

    ("var", j, sense)   this bit is variable j of the native state, negated
                        when `sense` is False
    ("state", i)        this bit is "the state is exactly `order[i]`"
    ("bit", i)          this bit is bit i of the state's index in `order`

That costs a little machinery and buys one thing that matters and one that
sounds better than it is.  What it really buys is that the inverse can be
written *separately* -- `Recoding.decode` reads the declarations the other way
round rather than searching for the state whose `encode` matches, which is what
lets `recoding_mismatches` compare two translations instead of one twice.  What
it does not buy, despite an earlier draft of this paragraph claiming it, is
crossing the process boundary: only `PredicateSpec` is serialised onto the
child's command line, and the child rebuilds the recoding from `recoding_for`.
`as_json` is a description for the artefact, not a wire format, and it has no
inverse.

The declarative form does also make **desugaring** decidable by inspection: a
scheme all of whose definitions are `("var", j, sense)` can have any clause over
its vocabulary rewritten back into the native vocabulary, literal for literal,
which is what lets a `dual` rung's certificate be handed to the independent
rechecker that only speaks peg.  A scheme with a `("state", i)` definition
cannot, and says so rather than pretending -- see `Recoding.desugars`.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

from engines.ic3_pdr.system import Clause, Literal, State, System, clause_key

BINARY = "binary"
NATIVE = "native"
DUAL = "dual"
ONEHOT = "onehot"

SCHEMES = (BINARY, NATIVE, DUAL, ONEHOT)

# A definition is ("var", index, sense) or ("state", index).
Definition = Tuple[Any, ...]


class RecodingError(Exception):
    """The re-encoding is not a bijection, or was asked for something it is not.

    Raised rather than warned, for the reason `AnchorDrift` is: a re-encoding
    that is not a bijection is measuring a different world, and every number
    taken under it would be a number about that other world.
    """


# --------------------------------------------------------------- the recoding

@dataclass(frozen=True)
class Recoding:
    """How to say one system's states in a different set of booleans."""

    scheme: str
    k: int
    variables: Tuple[str, ...]
    native_variables: Tuple[str, ...]
    definitions: Tuple[Definition, ...]
    # `onehot` and `binary` need it; the two `var`-only schemes leave it empty.
    order: Tuple[State, ...] = ()
    # Position lookup for `order`, built once.  Out of `compare` and `repr`
    # because it is derived from `order` and carries no information of its own;
    # a `Recoding` is still hashable and still compares on what it declares.
    _ordinals: Dict[State, int] = field(
        default_factory=dict, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_ordinals",
            {state: index for index, state in enumerate(self.order)})

    # ------------------------------------------------------------- properties

    @property
    def label(self) -> str:
        if self.scheme == DUAL:
            return "dual+%d" % self.k
        return self.scheme

    @property
    def n_variables(self) -> int:
        return len(self.variables)

    def desugars(self) -> bool:
        """Can a clause over this vocabulary be rewritten in the native one?

        True exactly when every predicate is a native variable or its negation.
        `onehot` names states, not variables, so a clause over it says nothing
        that survives the translation and this returns False -- which is the
        honest answer and the reason the recheck column on those rows reads
        `not available` instead of a tick.
        """
        return all(kind == "var" for kind, *_ in self.definitions)

    # --------------------------------------------------------------- encoding

    def encode(self, state: State) -> State:
        """The state, said in this vocabulary.

        The state's index is looked up once, not once per definition: `onehot`
        on a 1024-state world has 1024 definitions, and asking each of them
        independently where the state sits would turn a linear encode into a
        quadratic one and put the cost of *this module* into a column that is
        supposed to be measuring IC3.
        """
        index = self._index_of(state) if self.order else -1
        bits: List[bool] = []
        for definition in self.definitions:
            if definition[0] == "var":
                _, position, sense = definition
                bits.append(state[position] if sense else not state[position])
            elif definition[0] == "bit":
                _, position = definition
                bits.append(bool((index >> position) & 1))
            else:
                _, position = definition
                bits.append(index == position)
        return tuple(bits)

    def decode(self, bits: State) -> State:
        """The native state a code stands for -- the inverse, written out.

        Deliberately *not* implemented as "search `order` for the state whose
        `encode` gives these bits".  That would make the gate below a check that
        `encode` equals itself, which is the failure `recheck/README.md` opens by
        naming: two transcriptions or none.  This one reads the declarations the
        other way round -- `("var", j, sense)` says which bit carries native
        variable j and with which polarity, `("bit", i)` and `("state", i)` say
        how to recover the ordinal -- so a wrong `encode` and a wrong `decode`
        would have to be wrong in matching ways to agree.

        The independence is real but bounded, and the bound is worth stating:
        both directions read the same `definitions`, so this catches an error in
        *evaluating* a declaration and not an error in *choosing* one.  A scheme
        that declared the wrong thing would be self-consistently wrong, and the
        checks on |S| and on the edge relation are what stand behind that.
        """
        if len(bits) != len(self.definitions):
            raise RecodingError(
                "%d bits, the recoding declares %d predicates"
                % (len(bits), len(self.definitions)))

        sources: Dict[int, Tuple[int, bool]] = {}
        ordinal: Optional[int] = None
        for position, definition in enumerate(self.definitions):
            if definition[0] == "var":
                _, native_index, sense = definition
                sources.setdefault(native_index, (position, sense))
            elif definition[0] == "bit":
                _, weight = definition
                ordinal = (ordinal or 0) | ((1 << weight) if bits[position] else 0)
            elif bits[position]:
                if ordinal is not None:
                    raise RecodingError(
                        "two one-hot predicates are set at once, so this code "
                        "names two states: %r" % (bits,))
                ordinal = definition[1]

        if sources:
            if len(sources) != len(self.native_variables):
                raise RecodingError(
                    "the recoding carries %d of the world's %d variables, so a "
                    "code cannot be read back into a state"
                    % (len(sources), len(self.native_variables)))
            return tuple(
                bits[position] if sense else not bits[position]
                for position, sense in
                (sources[j] for j in range(len(self.native_variables)))
            )
        if ordinal is None or not 0 <= ordinal < len(self.order):
            raise RecodingError(
                "the code %r names no state in the declared order" % (bits,))
        return self.order[ordinal]

    def _index_of(self, state: State) -> int:
        """Where `state` sits in the declared order."""
        ordinal = self._ordinals.get(state)
        if ordinal is None:
            raise RecodingError(
                "state %r is not in the declared order, so it has no index to "
                "encode -- the recoding was built for a different system"
                % (state,)
            )
        return ordinal

    # -------------------------------------------------------------- desugaring

    def desugar_literal(self, literal: Literal) -> Literal:
        """One literal of this vocabulary, said in the native one.

        `free_pos3` is true exactly when `pos3` is false, so the literal
        `(free_pos3, True)` *is* the literal `(pos3, False)` -- the same
        half-plane, renamed.  Nothing is lost and nothing is approximated.
        """
        index, value = literal
        if not 0 <= index < len(self.definitions):
            raise RecodingError(
                "literal %r names predicate %d and this recoding declares %d; a "
                "negative index would wrap silently onto the last one"
                % ((index, value), index, len(self.definitions))
            )
        kind = self.definitions[index][0]
        if kind != "var":
            raise RecodingError(
                "predicate %r is defined as %r -- it names a state or an index "
                "bit rather than a world variable, so it has no native literal "
                "to be rewritten into" % (self.variables[index], kind)
            )
        _, native_index, sense = self.definitions[index]
        return (native_index, value if sense else not value)

    def as_json(self) -> Dict[str, Any]:
        return {
            "scheme": self.scheme,
            "label": self.label,
            "k": self.k,
            "n_variables": self.n_variables,
            "n_native_variables": len(self.native_variables),
            "desugars": self.desugars(),
            "variables": list(self.variables),
        }


# ------------------------------------------------------------ the three schemes

def native_recoding(system: System) -> Recoding:
    """The identity.  On the ladder so that the k=0 rung is measured through the
    same code path as every other one, rather than being the one row that took a
    shortcut and is therefore not comparable with its neighbours."""
    return Recoding(
        scheme=NATIVE,
        k=0,
        variables=tuple(system.variables),
        native_variables=tuple(system.variables),
        definitions=tuple(("var", j, True) for j in range(len(system.variables))),
    )


def dual_recoding(system: System, k: int) -> Recoding:
    """The native variables, plus a second name for the negation of the first k.

    `k = 0` is the identity and is allowed: it makes `dual` a family with the
    native encoding as its own first member, so a ladder over k needs no special
    case at its foot.
    """
    n = len(system.variables)
    if not 0 <= k <= n:
        raise RecodingError(
            "dual(%d) on a %d-variable system: k must be between 0 and n. Past n "
            "the extra predicates would be duplicates of ones already declared, "
            "and a ladder rung whose two predicates are literally the same "
            "column measures duplication, not predicate count." % (k, n)
        )
    return Recoding(
        scheme=DUAL,
        k=k,
        variables=tuple(system.variables)
                  + tuple("free_%s" % system.variables[j] for j in range(k)),
        native_variables=tuple(system.variables),
        definitions=tuple(("var", j, True) for j in range(n))
                    + tuple(("var", j, False) for j in range(k)),
    )


def binary_recoding(system: System) -> Recoding:
    """The floor: ceil(log2 |S|) booleans, and no meaning attached to any of them.

    This is the only scheme that can spend *fewer* predicates than the world was
    handed in, and it is the sharpest test on the ladder, because it strips out
    exactly the thing a predicate is for.  `b3` is not "the door is open" or
    "position 3 holds a peg"; it is the fourth bit of an index, and a clause over
    it says nothing a reader can adjudicate.  If IC3 gets faster here, then what
    the extra predicates were buying was not speed -- it was the certificate.
    """
    order = tuple(system.states)
    width = floor_width(len(order))
    return Recoding(
        scheme=BINARY,
        k=0,
        variables=tuple("b%d" % i for i in range(width)),
        native_variables=tuple(system.variables),
        definitions=tuple(("bit", i) for i in range(width)),
        order=order,
    )


def onehot_recoding(system: System) -> Recoding:
    """One predicate per state.  The extreme of the axis, and a real modelling
    style: a manual that lists situations rather than describing them.

    |S| does not move -- the same states are still the only states -- but the
    predicate count jumps from n to 2^n on the peg family, which is the widest
    single step this axis can take without touching the world.
    """
    order = tuple(system.states)
    return Recoding(
        scheme=ONEHOT,
        k=0,
        variables=tuple("is_%s" % system.render_state(s) for s in order),
        native_variables=tuple(system.variables),
        definitions=tuple(("state", i) for i in range(len(order))),
        order=order,
    )


def recoding_for(system: System, scheme: str, k: int = 0) -> Recoding:
    if scheme == BINARY:
        return binary_recoding(system)
    if scheme == NATIVE:
        return native_recoding(system)
    if scheme == DUAL:
        return dual_recoding(system, k)
    if scheme == ONEHOT:
        return onehot_recoding(system)
    raise RecodingError("unknown scheme %r; the schemes are %r" % (scheme, SCHEMES))


# ------------------------------------------------------------- the re-encoding

def reencode(system: System, recoding: Recoding) -> System:
    """The same system, said in the recoding's vocabulary.

    Every state is mapped, every labelled edge is mapped, the initial state and
    the bad set are mapped.  `states` is sorted for the same reason the peg
    builder sorts: every loop in the engine walks it, and an unsorted one would
    make the run reproducible only by luck.

    Injectivity is checked here rather than trusted, because a collision would
    silently *merge* two states -- IC3 would then answer a question about a
    smaller world and the row would report its cost as this world's.
    """
    if len(recoding.native_variables) != len(system.variables):
        raise RecodingError(
            "the recoding was built for a %d-variable system and this one has %d"
            % (len(recoding.native_variables), len(system.variables))
        )

    image: Dict[State, State] = {}
    for state in system.states:
        image[state] = recoding.encode(state)
    if len(set(image.values())) != len(system.states):
        raise RecodingError(
            "%s is not injective on this system: %d states collapsed to %d codes"
            % (recoding.label, len(system.states), len(set(image.values())))
        )

    # An edge to a state the system does not declare would come out of `image`
    # as a bare KeyError, surface as `engine-refused`, and blame `ic3_pdr` for a
    # malformed input.  Named here instead: it is the adapter's fault or the
    # builder's, and either way the row is void rather than hard.
    stray = sorted(
        {system.render_state(target)
         for state in system.states
         for _, target in system.moves(state)
         if target not in image}
    )
    if stray:
        raise RecodingError(
            "the relation leaves the declared state set: %d edge target(s) are "
            "not states of this system (%s%s). A re-encoding maps states, so "
            "there is nothing to map these to."
            % (len(stray), ", ".join(stray[:4]),
               ", ..." if len(stray) > 4 else "")
        )

    transitions: Dict[State, Tuple[Tuple[str, State], ...]] = {}
    for state in system.states:
        moves = system.moves(state)
        if moves:
            transitions[image[state]] = tuple(
                sorted((label, image[target]) for label, target in moves)
            )

    return System(
        name="%s/%s" % (system.name, recoding.label),
        variables=recoding.variables,
        states=tuple(sorted(image[s] for s in system.states)),
        init=tuple(image[s] for s in system.init),
        bad=tuple(sorted(image[s] for s in system.bad)),
        transitions=transitions,
    )


# ------------------------------------------------------------------- the gate

def recoding_mismatches(original: System, recoded: System,
                        recoding: Recoding, limit: int = 8) -> List[str]:
    """Is `recoded` the same world as `original`, only renamed?  Re-derived.

    The same role `harness.transcription_mismatches` plays for the peg adapter,
    and it is worth being exact about how far the parallel goes, because an
    adversarial pass over an earlier version of this function found it running
    five of seven checks through `recoding.encode` -- the very function
    `reencode` had just used -- which could only ever confirm that `encode`
    equals itself.

    It now walks the *recoded* system and reads every state back with
    `Recoding.decode`, the separately written inverse, so the edge check, the
    init check and the bad-set check compare two directions of translation
    rather than one direction twice.  What that does **not** buy is independence
    from the declarations: `encode` and `decode` read the same `definitions`
    tuple, so a scheme that declared the wrong predicate would be
    self-consistently wrong here.  The checks that stand behind *that* are the
    two the docstring puts first -- |S| is unchanged, and the labelled edge
    relation agrees with the original system's -- neither of which any
    declaration can talk its way out of.

    One check is a guard rather than a measurement, and says so: no scheme
    `recoding_for` can build is non-injective (native and dual are the identity
    on the world's own bits, binary and onehot are functions of a state's
    ordinal), so the injectivity branch exists for a scheme someone adds later
    and never fires today.
    """
    problems: List[str] = []

    if tuple(recoded.variables) != tuple(recoding.variables):
        problems.append(
            "vocabulary: the system carries %d variables, the recoding declares %d"
            % (len(recoded.variables), len(recoding.variables))
        )

    if len(recoded.states) != len(original.states):
        problems.append(
            "|S|: %d states after re-encoding, %d before -- this axis holds the "
            "state space FIXED, so any movement here voids the rung"
            % (len(recoded.states), len(original.states))
        )

    if list(recoded.states) != sorted(recoded.states):
        problems.append("states are not sorted, so the run is not reproducible")

    # Read every code back with the inverse, and require the result to be the
    # original state set exactly -- not a subset, not a multiset.
    backward: Dict[State, State] = {}
    for code in recoded.states:
        try:
            state = recoding.decode(code)
        except RecodingError as exc:
            problems.append("%s does not read back into a state: %s"
                            % (recoded.render_state(code), exc))
            if len(problems) >= limit:
                return problems[:limit]
            continue
        backward[code] = state
    if sorted(set(backward.values())) != sorted(original.states):
        problems.append(
            "the codes read back to %d distinct state(s) and the world has %d, "
            "so the re-encoding is not a bijection onto it"
            % (len(set(backward.values())), len(original.states))
        )
        return problems[:limit]

    forward = {state: code for code, state in backward.items()}

    if tuple(recoded.init) != tuple(forward[s] for s in original.init):
        problems.append("init is not the image of the original initial state")
    if tuple(recoded.bad) != tuple(sorted(forward[s] for s in original.bad)):
        problems.append(
            "bad set: %d states after, %d before, and not the image"
            % (len(recoded.bad), len(original.bad))
        )

    for code in recoded.states:
        state = backward[code]
        before = sorted((label, forward[target])
                        for label, target in original.moves(state))
        after = sorted(recoded.moves(code))
        if before != after:
            problems.append(
                "transitions from %s: %d edge(s) after re-encoding, %d before"
                % (original.render_state(state), len(after), len(before))
            )
            if len(problems) >= limit:
                break
    return problems[:limit]


# ------------------------------------------------------------------ desugaring

@dataclass(frozen=True)
class Desugared:
    """A clause set of a recoding's vocabulary, rewritten in the native one."""

    clauses: Tuple[Clause, ...]
    tautologies_dropped: int
    literals_before: int
    literals_after: int

    @property
    def n_clauses(self) -> int:
        return len(self.clauses)

    def as_json(self) -> Dict[str, Any]:
        return {
            "n_clauses": self.n_clauses,
            "n_literals": self.literals_after,
            "literals_before": self.literals_before,
            "tautologies_dropped": self.tautologies_dropped,
        }


def desugar(recoding: Recoding, clauses: Sequence[Clause]) -> Desugared:
    """Rewrite a clause set into the native vocabulary, meaning preserved.

    Two things can shrink and neither changes what the formula says.  A clause
    that mentions both `pos3` and `free_pos3` becomes one mentioning both
    polarities of `pos3`: it is true of every state, so it is dropped.  And two
    literals that were distinct names for the same half-plane collapse into one,
    which is why `literals_after` can be smaller than `literals_before` with no
    state changing sides.

    **Both counters read zero on every row this repo has produced, and that is
    structural rather than lucky.**  An adversarial pass established why: every
    clause IC3 learns is a subset of a negated cube, a negated cube contains at
    most one polarity of each native variable, and where a `dual` cube carries
    both `(j, not v)` and its `free` twin `pdr.generalise` drops one of them
    before returning -- the smaller clause is trivially still relative-inductive.
    So `tautologies_dropped` and the `before`/`after` gap are a guard against a
    *different* producer feeding this function, not a measurement of this one,
    and a reader should not take the zeroes as evidence that the certificates
    are tight.  They are evidence of nothing at all.

    The result is exact, not an approximation: a state satisfies the original
    clause set over the recoded vocabulary if and only if its native
    counterpart satisfies this one.  `axis_predicates` does not take that on
    trust either -- it re-counts both sides with the engine's own checker and
    reports a finding if the two numbers differ.
    """
    if not recoding.desugars():
        raise RecodingError(
            "%s names states rather than variables, so its clauses have no "
            "native form. A rung under it has no certificate the peg rechecker "
            "can read, and must say so rather than be scored." % recoding.label
        )

    out: List[Clause] = []
    dropped = 0
    literals_before = 0
    literals_after = 0
    for clause in clauses:
        literals_before += len(clause)
        rewritten = {recoding.desugar_literal(literal) for literal in clause}
        variables_seen: Dict[int, bool] = {}
        tautological = False
        for index, value in rewritten:
            if variables_seen.get(index, value) != value:
                tautological = True
                break
            variables_seen[index] = value
        if tautological:
            dropped += 1
            continue
        literals_after += len(rewritten)
        out.append(frozenset(rewritten))

    ordered = tuple(sorted(set(out), key=clause_key))
    # Deduplication can also drop a clause: two clauses of the recoded
    # vocabulary can be the same clause once renamed.  Recount rather than
    # carry the pre-dedup sum, which would overstate the certificate.
    literals_after = sum(len(clause) for clause in ordered)
    return Desugared(
        clauses=ordered,
        tautologies_dropped=dropped,
        literals_before=literals_before,
        literals_after=literals_after,
    )


# ------------------------------------------------------------------- reporting

def floor_width(n_states: int) -> int:
    """The fewest booleans that can tell `n_states` states apart.

    `(n-1).bit_length()` rather than `ceil(log2 n)`: the float form is off by
    one at `2^e + 1` for large e, and while no world here is remotely that big,
    a width that is silently wrong is a bad thing for the two callers that must
    agree -- `binary_recoding`, which spends it, and `encoding_slack`, which
    measures against it.  Both go through this function so they cannot drift.

    One state needs no bits to distinguish and one bit to write down; the
    minimum is 1, which is what `binary_recoding` emits.
    """
    return max(1, (max(n_states, 1) - 1).bit_length())


def encoding_slack(n_variables: int, n_states: int) -> int:
    """Predicates spent above the information-theoretic floor.

    `floor_width(|S|)` booleans are enough to name |S| states.  Anything above
    that is what a modeller chose to spend: `binary` and `native` peg-N both sit
    at zero, `dual(k)` at k, `onehot` at |S| - floor_width(|S|).

    An adversarial pass refuted the rationale this carried when it was written
    -- it claimed to be "the number that does not depend on how big the world
    is", which `onehot` falsifies immediately, since its slack is |S| minus a
    logarithm and is therefore almost entirely world size.  The column is kept
    because "how far above the floor" is the honest description of what the
    ladder varies, and it is read that way in `IC3_BOUNDS.md`: within a block,
    where |S| does not move, slack is exactly the padding; across blocks it is
    not comparable, and the document takes no ratio across blocks.

    It is also not a substitute for the `encoding` column: `binary` and `native`
    both read 0 on the peg family, and they are the two rungs whose timings
    differ most.
    """
    return n_variables - floor_width(n_states)
