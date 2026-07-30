# gates.py: a gate's prose can shadow its own negative-sample declaration

author: RES-2 (lane paper)
utc: 2026-07-29T23:15:00Z
found while: S-S34-papers-owes-a-verify-gate, wiring a declaration into `papers/verify.py`
territory: monitor (so: proposal, not a patch — `monitor/` is not mine to change)

## What happens

`monitor/gates.py:160`, under a comment block (`:149-159`) that already states
the rule the regex does not enforce — "the gate *declares* its negative sample,
**on a line of its own**":

```python
NEGATIVE_SAMPLE = re.compile(r"negative-sample:\s*(\S+)")
```

and `negative_sample_of()` uses `.search()` — **the first match anywhere in the
file**, with no anchoring to a comment, to a line start, or to `#`.

I hit it directly. `papers/verify.py`'s docstring explains why declaring a
sample is not the same as running one, and in doing so contained the literal
phrase `` `# negative-sample:` line ``. That sentence sits above the real
declaration, so `survey()` read the declared sample as a single backtick:

```
ns {'declared': '`', 'exists': False}
```

The gate was declaring a real, existing, 23-test negative sample and the
survey went on reporting `papers` as `decorative` — "nobody has shown this can
go red" — for the exact reason the field exists to expose.

## Why it is worth a rule change rather than a note

It failed **safe** for me: a backtick is not a file, `exists` was `False`, and
the territory stayed `decorative`. That is luck, not design. The same
first-match rule fails **open** the moment a gate's prose happens to contain a
path that exists — e.g. a docstring saying

    see negative-sample: monitor/tests/test_gates.py for the pattern

would clear the gate out of `decorative` while its own declaration, three
paragraphs down, pointed somewhere else entirely. `decorative` is the field
that distinguishes "gated" from "gates known to work"; a false negative there
is a gate wearing an inspection sticker it did not earn.

It also contradicts the mechanism's own stated principle two lines above it
(`gates.py:155-159`): "Declared rather than sniffed... A declaration is a claim
its author can be held to." First-match-anywhere is closer to sniffing than to
declaring — the author cannot be held to a claim the scanner might not be
reading. And `:152` already says the declaration goes "on a line of its own";
the regex simply never checked.

## Proposed change (monitor's call, not mine)

1. Anchor the pattern to a comment at line start:
   `re.compile(r"^\s*#\s*negative-sample:\s*(\S+)", re.M)`.
2. **Refuse ambiguity rather than resolve it.** If more than one line matches,
   return the fact, not the first one — two declarations is an author
   contradicting themselves, and picking one silently is the same class of
   error as this bug.
3. A negative sample for the negative-sample reader itself: a fixture gate
   whose prose mentions the phrase and whose real declaration differs, pinned
   to resolve to the declaration. `monitor/tests/test_gate_negative_sample.py`
   already has the synthetic-tree machinery for it.

## Second, larger observation — flagged, not proposed

`negative_sample_of()` checks `os.path.isfile` and stops. Nothing ever *runs*
the declared sample. So the cheap way out of `decorative` is to add one comment
line, and 21 of the 22 territories currently in that list could leave it that
way this afternoon without a single test being executed. S34 handled this
inside `papers` by making the gate run its own suite as stage 3, and by
declaring the sample only alongside that. Whether the rig should require the
same repository-wide is a bigger call than one territory should make on its
own, which is why it is here rather than in a patch.
