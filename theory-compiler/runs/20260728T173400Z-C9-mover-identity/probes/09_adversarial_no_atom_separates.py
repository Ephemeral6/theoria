"""Probe 09 -- adversarial test of the claim that `a0_relational_v1` cannot
separate the failing group of `t2-lock-fragile`.

The claim under attack:

    No atom in `a0_relational_v1` is true on all 23 positives of the group
    track=obj1 action=RIGHT effect=('none',0,0,None) and false at transition 31.

This probe rebuilds the *pipeline's own* inputs -- same reader, same board, same
background, same segmenter choice, same `build_transitions`, same
`build_vocabulary` call as `multi_miner.mine` makes -- reuses `multi_miner`'s own
grouping code so the group tested is the group that failed, then:

  1. enumerates every atom (the vocabulary is already closed under negation) and
     checks "true on all positives AND false at t=31";
  2. names the five that come closest;
  3. explains, atom by atom, why `tcolor(RIGHT)==2`, `at(1,2)`, `present(obj1)`
     and every `count(...)` atom fails;
  4. exhaustively checks every *pair* (conjunction), because CEGIS builds
     conjunctions -- if a pair works the failure is a search bug, not an
     expressivity gap.

Read-only: prints, writes nothing.

    python theory-compiler/runs/20260728T173400Z-C9-mover-identity/probes/09_adversarial_no_atom_separates.py
"""

import hashlib
import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(RUN, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "cold-start-a0"))
sys.path.insert(0, os.path.join(ROOT, "engine-rig"))

import _bootstrap  # noqa: F401,E402

from engines.cegis_miner.atoms import atom_order_key  # noqa: E402

from pipeline import atoms_a0, multi_miner, segment_operators  # noqa: E402
from pipeline.atoms_a0 import atom_masks, build_vocabulary, frame_count  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

WORLD = "t2-lock-fragile"
TRACE = os.path.join(ROOT, "worldgen", "out", "worlds", WORLD, "raw_trace.jsonl")

TARGET_TRACK = "obj1"
TARGET_ACTION = "RIGHT"
TARGET_EFFECT_KEY = ("none", 0, 0, None)
CEX = 31


def rule(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ------------------------------------------------------------ 1. rebuild inputs

rule("1. rebuilding the pipeline's own inputs (engines_stage.run_stage order)")

frames, actions, wins = read_trace(TRACE)
board = extract_board(frames)
background = background_color(board, frames)
layer = object_layer(frames, board, background=background)
operator, seg, operator_report = segment_operators.choose_operator(
    layer, background=background
)
track_ids = [t.track_id for t in seg.tracks]
mover = multi_miner.mover_track(seg)
transitions = multi_miner.build_transitions(
    frames, layer, actions, seg, background=background
)

# exactly as multi_miner.mine does it
observations = [t.obs for t in transitions]
acts = [t.action for t in transitions]
vocabulary = build_vocabulary(observations, list(track_ids))
masks = atom_masks(vocabulary, observations, acts)
universe = (1 << len(transitions)) - 1

print("frames            :", len(frames))
print("transitions       :", len(transitions))
print("background        :", background)
print("segment operator  :", operator)
print("tracks            :", track_ids)
print("mover             :", mover)
print("vocabulary size   :", len(vocabulary), "(includes negations)")
print("distinct atoms    :", len({a.name for a in vocabulary}))
print("atom kinds        :", sorted({a.kind for a in vocabulary}))

# The vocabulary is a moving target -- `atoms_a0.py` is under concurrent edit --
# so the run labels *which* vocabulary it tested.  A verdict here is only about
# the file whose digest is printed.
_src = os.path.join(ROOT, "cold-start-a0", "pipeline", "atoms_a0.py")
with open(_src, "rb") as _fh:
    _blob = _fh.read()
print("atoms_a0.py       : %d bytes  sha256=%s"
      % (len(_blob), hashlib.sha256(_blob).hexdigest()[:16]))


# ------------------------------------------------- 2. reproduce the exact group

rule("2. reproducing the failing group with multi_miner's own grouping")

groups = {}
for transition in transitions:
    key = (transition.action, transition.effects[TARGET_TRACK].key())
    groups.setdefault(key, []).append(transition)

print("groups for track=%s (multi_miner.mine grouping):" % TARGET_TRACK)
for key in sorted(groups, key=lambda k: (k[0], str(k[1]))):
    print("   %-6s %-28s n=%d  %s" % (
        key[0], str(key[1]), len(groups[key]),
        [t.index for t in groups[key]][:12],
    ))

target_key = (TARGET_ACTION, TARGET_EFFECT_KEY)
members = groups[target_key]
pos_idx = sorted(t.index for t in members)
positives = 0
for t in members:
    positives |= 1 << t.index
negatives = universe & ~positives

print()
print("TARGET group      :", target_key)
print("positives (%d)     : %s" % (len(pos_idx), pos_idx))
print("t=%d in positives : %s" % (CEX, CEX in pos_idx))

tr31 = next(t for t in transitions if t.index == CEX)
print()
print("transition %d      : action=%s" % (CEX, tr31.action))
print("   effects        :", {k: v.key() for k, v in sorted(tr31.effects.items())})
print("   mover_anchor   :", tr31.obs.mover_anchor)
print("   anchors        :", dict(sorted(tr31.obs.anchors.items())))
print("   colors         :", dict(sorted(tr31.obs.colors.items())))
print("   frame at t=%d:" % CEX)
for row in tr31.obs.frame:
    print("      " + "".join(str(v) for v in row))

# what CEGIS actually reaches first
consistent = [a for a in masks if positives & ~masks[a] == 0]
print()
print("atoms true on every positive (CEGIS 'consistent') :", len(consistent))
guard_mask = universe
first_cex = None
counter = guard_mask & negatives
if counter:
    first_cex = (counter & -counter).bit_length() - 1
print("first counterexample the empty guard admits       :", first_cex)


# ------------------------------------------------- 3. every atom and its negation

rule("3. single-atom separation: true on all %d positives AND false at t=%d"
     % (len(pos_idx), CEX))


def violated_positives(atom):
    """Positive indices where `atom` is false."""
    m = masks[atom]
    return [i for i in pos_idx if not (m >> i) & 1]


def true_at(atom, i):
    return bool((masks[atom] >> i) & 1)


seen = set()
atoms = []
for a in vocabulary:
    if a.name in seen:
        continue
    seen.add(a.name)
    atoms.append(a)

# The vocabulary is closed under negation by construction; assert it, and add
# any missing negation so "every atom AND its negation" is literally true.
added_negations = 0
for a in list(atoms):
    neg = a.negate()
    if neg.name not in seen:
        seen.add(neg.name)
        atoms.append(neg)
        added_negations += 1
        if neg not in masks:
            masks[neg] = universe & ~masks[a]
print("atoms enumerated  : %d  (negations added to close the set: %d)"
      % (len(atoms), added_negations))

separators = [
    a for a in atoms
    if not violated_positives(a) and not true_at(a, CEX)
]
print()
print(">>> SEPARATING SINGLE ATOMS : %d" % len(separators))
for a in sorted(separators, key=atom_order_key):
    print("      %s   cost=%d" % (a.name, a.cost))
if not separators:
    print("      (none -- the claim survives the single-atom attack)")

scored = sorted(
    atoms,
    key=lambda a: (len(violated_positives(a)), true_at(a, CEX), a.cost, a.name),
)
print()
print("five closest atoms (fewest positives violated, then false-at-%d first):" % CEX)
print("   %-26s %-9s %-11s %s" % ("atom", "#viol", "false@%d" % CEX, "first violated positive"))
for a in scored[:5]:
    viol = violated_positives(a)
    print("   %-26s %-9d %-11s %s" % (
        a.name, len(viol), (not true_at(a, CEX)),
        viol[0] if viol else "-",
    ))

print()
print("of the %d atoms false at t=%d, the fewest positives any violates: %s" % (
    sum(1 for a in atoms if not true_at(a, CEX)), CEX,
    min((len(violated_positives(a)) for a in atoms if not true_at(a, CEX)),
        default=None),
))
print("closest atoms that ARE false at t=%d:" % CEX)
false_at_cex = sorted(
    (a for a in atoms if not true_at(a, CEX)),
    key=lambda a: (len(violated_positives(a)), a.cost, a.name),
)
for a in false_at_cex[:5]:
    viol = violated_positives(a)
    print("   %-26s violates %d positive(s): %s" % (
        a.name, len(viol), viol[:8] + (["..."] if len(viol) > 8 else []),
    ))


# ------------------------------------------------------------ 4. the why-table

rule("4. why each named atom fails")

named = ["tcolor(RIGHT)==2", "at(1,2)", "present(obj1)"]
by_name = {a.name: a for a in atoms}
count_atoms = [a for a in atoms if a.kind == "count" and not a.negated]
count_names = [a.name for a in count_atoms]
targets = named + count_names

print("count atoms in the vocabulary: %s" % (count_names or "(none)"))
print()
for name in targets:
    atom = by_name.get(name)
    if atom is None:
        print("%-22s NOT IN VOCABULARY" % name)
        continue
    viol = violated_positives(atom)
    at31 = true_at(atom, CEX)
    if viol:
        i = viol[0]
        why = "FALSE at positive t=%d (violates %d/%d positives)" % (
            i, len(viol), len(pos_idx))
    else:
        why = "true on ALL %d positives" % len(pos_idx)
    verdict = ("also TRUE at t=%d -> cannot exclude it" % CEX) if at31 else (
        "FALSE at t=%d" % CEX)
    print("%-22s %-52s %s" % (name, why, verdict))
    if atom.kind == "count":
        colour, threshold = atom.arg
        vals = [frame_count(transitions[i].obs.frame, colour) for i in pos_idx]
        print("   %s  count(%d) over positives: min=%d max=%d   at t=%d: %d"
              % (" " * 19, colour, min(vals), max(vals), CEX,
                 frame_count(tr31.obs.frame, colour)))
    if atom.kind in ("tcolor",) and viol:
        i = viol[0]
        obs = transitions[i].obs
        cells = atoms_a0.strip_cells(obs.mover_anchor, atom.arg[0], obs.mover_shape)
        vals = [obs.frame[r][c] if obs.in_bounds((r, c)) else None for r, c in cells]
        print("   %s  at t=%d strip(%s)=%s cells=%s (wanted all %d)"
              % (" " * 19, i, atom.arg[0], vals, cells, atom.arg[1]))
        o31 = tr31.obs
        c31 = atoms_a0.strip_cells(o31.mover_anchor, atom.arg[0], o31.mover_shape)
        v31 = [o31.frame[r][c] if o31.in_bounds((r, c)) else None for r, c in c31]
        print("   %s  at t=%d strip(%s)=%s cells=%s"
              % (" " * 19, CEX, atom.arg[0], v31, c31))
    if atom.kind == "at":
        anch = [transitions[i].obs.mover_anchor for i in pos_idx]
        print("   %s  mover anchors over positives: %s"
              % (" " * 19, sorted(set(anch))))
        print("   %s  mover anchor at t=%d: %s"
              % (" " * 19, CEX, tr31.obs.mover_anchor))
    if atom.kind == "present":
        print("   %s  anchor of %s at t=%d: %s"
              % (" " * 19, atom.arg, CEX, tr31.obs.anchors.get(atom.arg)))

# The negations too -- a negation is an atom in this vocabulary.
print()
print("negations of the same atoms:")
for name in targets:
    atom = by_name.get(name)
    if atom is None:
        continue
    neg = by_name.get("!" + name)
    if neg is None:
        continue
    viol = violated_positives(neg)
    print("%-22s violates %d/%d positives; at t=%d: %s" % (
        neg.name, len(viol), len(pos_idx), CEX,
        "TRUE" if true_at(neg, CEX) else "FALSE"))


# ------------------------------------------------------- 5. pairs (conjunctions)

rule("5. exhaustive pair search: (atom_i AND atom_j) over the whole vocabulary")

print("note: a conjunction is true on all positives iff BOTH conjuncts are, and")
print("      false at t=%d iff at least one conjunct is -- so a working pair" % CEX)
print("      REQUIRES a working single atom.  Checked exhaustively anyway.")
print()

pos_consistent = [a for a in atoms if not violated_positives(a)]
print("atoms true on every positive : %d" % len(pos_consistent))
print("of those, false at t=%d       : %d"
      % (CEX, sum(1 for a in pos_consistent if not true_at(a, CEX))))

found_pair = None
checked = 0
for a, b in itertools.combinations(sorted(atoms, key=lambda x: x.name), 2):
    checked += 1
    m = masks[a] & masks[b]
    if positives & ~m:
        continue                      # not true on all positives
    if (m >> CEX) & 1:
        continue                      # still admits t=31
    found_pair = (a, b)
    break

print("pairs checked                : %d" % checked)
if found_pair is None:
    print(">>> NO PAIR separates the group from t=%d" % CEX)
else:
    print(">>> PAIR FOUND: %s AND %s" % (found_pair[0].name, found_pair[1].name))

# And the stronger question CEGIS actually faces: can ANY conjunction of any
# size do it?  Same argument -- the intersection of the positive-consistent
# atoms is the strongest conjunction available.
strongest = universe
for a in pos_consistent:
    strongest &= masks[a]
print()
print("strongest conjunction available (AND of every positive-consistent atom):")
print("   admits t=%d : %s" % (CEX, bool((strongest >> CEX) & 1)))
leaked = [i for i in range(len(transitions)) if ((strongest & negatives) >> i) & 1]
print("   admits %d transitions outside the group: %s"
      % (len(leaked), leaked[:20]))


# ------------------------------------- 6. what the missing atom would have to be

rule("6. the shape of the missing atom (diagnostic, not part of the claim)")

print("t=%d and its nearest positives, side by side:" % CEX)
print("   %-5s %-8s %-9s %-14s %-9s %s"
      % ("t", "anchor", "strip val", "occupant", "obj1 eff", "in group"))


def occupant(obs):
    cells = atoms_a0.strip_cells(obs.mover_anchor, TARGET_ACTION, obs.mover_shape)
    if not all(obs.in_bounds(c) for c in cells):
        return "(out of bounds)"
    who = [k for k, a in sorted(obs.anchors.items())
           if a is not None and tuple(a) == tuple(cells[0])]
    return ",".join(who) or "(empty)"


def strip_vals(obs):
    cells = atoms_a0.strip_cells(obs.mover_anchor, TARGET_ACTION, obs.mover_shape)
    return [obs.frame[r][c] if obs.in_bounds((r, c)) else None for r, c in cells]


for i in [CEX] + pos_idx:
    t = transitions[i]
    print("   %-5d %-8s %-9s %-14s %-9s %s"
          % (i, t.obs.mover_anchor, strip_vals(t.obs), occupant(t.obs),
             t.effects[TARGET_TRACK].key()[0], i in pos_idx))

# A hypothetical relational atom: "the track occupying the mover's target strip
# is T".  Not in `a0_relational_v1`; evaluated here only to show what the
# vocabulary would need in order to separate the group.
print()
print("hypothetical atom `facing(T)` -- the track on the mover's target cell:")
for tid in track_ids:
    viol = [i for i in pos_idx if occupant(transitions[i].obs).split(",")[0] == tid]
    at31 = occupant(tr31.obs).split(",")[0] == tid
    print("   facing(%s): true on %d/%d positives; at t=%d: %s%s"
          % (tid, len(viol), len(pos_idx), CEX, at31,
             "   <-- SEPARATES" if not viol and at31 else ""))


# ------------------------------------------------------------------- 7. verdict

rule("7. verdict")

print("single-atom claim : %s  (%d separating atoms found)"
      % ("REFUTED" if separators else "CONFIRMED", len(separators)))
print("pair claim        : %s"
      % ("REFUTED" if found_pair else "CONFIRMED"))
print("any-size conjunction: %s"
      % ("REFUTED" if not ((strongest >> CEX) & 1) else "CONFIRMED"))
