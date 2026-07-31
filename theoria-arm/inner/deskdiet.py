"""The desk's diet: what it is shown, and what it is asked to write back.

Why this module exists
----------------------
`Theoria.md` 1.6 makes the bill an instrument: 每回合花费 ≈ 模型此刻还剩多少不懂,
so the curve should be front-heavy and fall towards zero as the theory converges.
It also names the shape of the failure, at line 59: **Schema 每回合重读全帧、上下文
越滚越大,曲线平坦、处处付全价——它的账单什么都读不出来**.  Today's live legs
had exactly that curve.  r3 spent $13.44 over 8 desk calls at $1.68 +- 0.14 with
no trend; l1 spent $12.25 over 9 at $1.36 +- 0.20, also with no trend.

`armtools/prompt_census.py` measured why, off the archived transcripts, before
anything here was written.  Three facts came back, and this module is shaped by
all three rather than by the suspicion we started with:

1. **Nothing was reused.**  `cache_read_input_tokens` is 0 on 21 of the 22
   archived desk calls, and the prompt's stable prefix ends after the preamble
   and the grammar card -- 10 828 chars, ~11% -- because the very next section
   (`## What has been observed`) changes every call.  Full price everywhere, as
   line 59 predicts.

2. **The context does roll bigger** -- r3's prompt went 74 613 -> 101 632 chars,
   +36% over eight calls -- **but not because the world is re-read.**  The
   evidence sections are already windowed (`render_window` clips to the box that
   ever changed) and already capped, and they are only 24% of the prompt.  54.6%
   of what the desk is shown is *the desk's own previous output*, handed back:
   the manual grew 32 958 -> 51 253 chars inside one leg.

3. **The input side is not where the money is.**  Regressing `cli_cost_usd` on
   the archived usage blocks over all 22 calls gives $10.42/Mtok for cache
   creation and $25.24/Mtok for output (r2 = 0.99983; the 2.42 ratio between
   them is list pricing's 75:30 to within the fit's error).  On those rates the
   **output side carries 73.1% of the desk bill** and everything sent to the
   desk carries 26.9%.

So a diet that only trims the prompt can address at most about a quarter of the
bill, and this module says so in code rather than in a hopeful commit message:
it has two independent knobs, one per side, and the one that matters is the
output contract.

The two knobs
-------------
`evidence_delta` -- send what changed since the previous desk call instead of
re-rendering the whole engine report and the whole command history.  Bounded
win: the engine block is pinned at its 14 000-char truncation cap on every
single call in every leg, and the command list is re-rendered from t0.

`theory_patch` -- ask for an edit to the manual instead of the whole manual.
Today's `OUTPUT_CONTRACT` says "the whole of theory.dsl, not a diff", which
makes the output bill grow with the manual's *size* rather than with what is
still unknown: precisely the inversion `Theoria.md` 1.6 forbids.  A converged
theory should cost a few hundred tokens to leave alone, not fifty thousand to
retype.

**Both default to off.**  `DeskDiet.FULL` reproduces today's prompt byte for
byte -- `tests/test_desk_diet.py::test_full_mode_is_byte_identical_to_today`
is the check, and it compares against the prompt builder with no diet object at
all, not against a re-implementation.

Failing closed
--------------
A patch is a load-bearing edit to the only artefact the whole system predicts
from, applied by a program to text a model wrote.  So every op must name an
anchor that occurs **exactly once**: zero matches is a refusal, two matches is a
refusal, and one bad op refuses the whole patch rather than applying the good
half.  A refused patch is fed back through the repair loop that already exists
for compile errors, and the last repair attempt reverts to demanding the whole
book -- so the worst case is today's behaviour plus one call, not a lost round.

None of these refusals is theoretical: `tests/test_desk_diet.py` drives each one
and asserts the reason, because a check that has never been seen to say no has
not been shown to check anything.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

#: Applied ops, in the order `apply_patch` tries them.
OPS = ("replace", "insert_after", "delete")


class PatchRefused(ValueError):
    """A patch that will not be applied, carrying the reason the desk is told."""

    def __init__(self, reason: str, detail: Dict[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


# --------------------------------------------------------------------- config
class DeskDiet:
    """Which knobs are on, plus the carry-over the delta knob needs.

    Config is set once; `state` is what one leg accumulates so call N can be
    expressed against call N-1.  They live on one object because the alternative
    -- threading two parameters through `theorize.run`, `inner/loop.py` and
    `harness/run.py` -- doubles the wiring for no gain, and because a diet whose
    state was dropped would silently degrade to full mode while still claiming
    to be on.  `state_is_fresh()` exists so a caller can tell the two apart.
    """

    __slots__ = ("evidence_delta", "theory_patch", "state")

    def __init__(self, *, evidence_delta: bool = False,
                 theory_patch: bool = False) -> None:
        self.evidence_delta = bool(evidence_delta)
        self.theory_patch = bool(theory_patch)
        self.state: Dict[str, Any] = {}

    # -- naming ------------------------------------------------------------
    @property
    def on(self) -> bool:
        return self.evidence_delta or self.theory_patch

    @property
    def name(self) -> str:
        if not self.on:
            return "full"
        if self.evidence_delta and self.theory_patch:
            return "diet"
        return "evidence" if self.evidence_delta else "patch"

    def as_json(self) -> Dict[str, Any]:
        return {"mode": self.name, "evidence_delta": self.evidence_delta,
                "theory_patch": self.theory_patch}

    def state_is_fresh(self) -> bool:
        return not self.state

    def __repr__(self) -> str:                                   # pragma: no cover
        return "DeskDiet(%s)" % self.name

    # -- parsing -----------------------------------------------------------
    @classmethod
    def parse(cls, spec: Optional[str]) -> "DeskDiet":
        """`full` (default) / `evidence` / `patch` / `diet`.

        An unknown spec raises.  Defaulting an unrecognised mode to `full`
        would turn a typo in a launch command into a leg that silently measured
        the wrong arm -- the run would look fine and the finding would be void.
        """
        text = (spec or "full").strip().lower()
        table = {
            "full": cls(),
            "off": cls(),
            "evidence": cls(evidence_delta=True),
            "patch": cls(theory_patch=True),
            "diet": cls(evidence_delta=True, theory_patch=True),
            "on": cls(evidence_delta=True, theory_patch=True),
        }
        if text not in table:
            raise ValueError(
                "unknown desk diet %r; one of %s"
                % (spec, ", ".join(sorted(table))))
        return table[text]


#: The object every call site gets when no diet was configured.  A module-level
#: singleton would be shared mutable state across legs, so this is a factory.
def full() -> DeskDiet:
    return DeskDiet()


# ---------------------------------------------------------------- the contract
#: Appended to `OUTPUT_CONTRACT` when `theory_patch` is on AND a manual already
#: exists.  A cold desk with no manual has nothing to patch and gets today's
#: contract unchanged -- the first manual is written whole, once.
PATCH_CONTRACT = """
# Writing the manual: send the EDIT, not the book

A manual already exists above, and you are being paid for what is still unknown,
not for retyping what is already settled. So instead of the `=== THEORY ===`
block, reply with:

=== THEORY-PATCH ===
```json
[
  {"op": "replace",
   "find": "<text that occurs EXACTLY ONCE in the manual above, verbatim>",
   "with": "<what it becomes>"},
  {"op": "insert_after",
   "find": "<text that occurs EXACTLY ONCE, verbatim>",
   "with": "<text inserted directly after it>"},
  {"op": "delete",
   "find": "<text that occurs EXACTLY ONCE, verbatim>"}
]
```

Rules, and they are checked by a program before anything downstream runs:

* `find` must match the manual **exactly**, including indentation and comments,
  and must occur **exactly once**. Zero matches or two matches refuses the WHOLE
  patch -- not just that op -- and you will be called again to redo it. Quote
  more surrounding text to make an anchor unique; that is cheaper than a retry.
* Ops apply in order, each against the manual as the previous ops left it.
* An empty list `[]` is a legitimate answer: it says the surprises do not move
  the manual. Say why in the LOG -- constraint 6 makes an explicit refusal an
  answer, but an unexplained one is not.
* If the change is structural enough that patching is dishonest -- the
  vocabulary is being re-cut, most rules are being rewritten -- emit a full
  `=== THEORY ===` block instead. That is always allowed and is never wrong,
  only expensive. Do not fake a small patch for a large change.

The `=== PLAYBOOK ===` and `=== LOG ===` blocks are unchanged: send the whole
playbook, and the whole log.
"""

PATCH_BLOCK = re.compile(
    r"===\s*THEORY-PATCH\s*===\s*\n+```(?:\w+)?\n(.*?)```", re.DOTALL)


def parse_patch(text: str) -> Optional[List[Dict[str, Any]]]:
    """The ops in a reply, or None if the reply carried no patch block.

    A patch block that is present but unreadable raises `PatchRefused` -- it is
    an answer that failed, which is different from an answer that was not
    given, and only the first should cost a repair round.
    """
    match = PATCH_BLOCK.search(text or "")
    if not match:
        return None
    body = match.group(1).strip()
    if not body:
        raise PatchRefused("the THEORY-PATCH block was empty; send `[]` to mean "
                           "'no change', or send the ops", {"body": ""})
    try:
        ops = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PatchRefused("the THEORY-PATCH block is not valid JSON: %s" % exc,
                           {"body": body[:500]}) from None
    if not isinstance(ops, list):
        raise PatchRefused("the THEORY-PATCH block must be a JSON list of ops, "
                           "got %s" % type(ops).__name__, {"body": body[:500]})
    return ops


def apply_patch(theory: str, ops: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """Apply anchored ops to a manual, or refuse the lot.

    Refusal is total by design.  Half-applying a patch leaves the manual in a
    state neither the desk nor the compiler asked for, and the desk's next call
    would be anchored against text that no longer says what it saw.  Better one
    named refusal than a manual nobody wrote.
    """
    if not isinstance(ops, list):
        raise PatchRefused("ops must be a list", {})
    text = theory
    applied: List[Dict[str, Any]] = []
    for i, op in enumerate(ops):
        if not isinstance(op, dict):
            raise PatchRefused("op %d is not an object" % i, {"index": i})
        kind = op.get("op")
        if kind not in OPS:
            raise PatchRefused(
                "op %d has unknown `op` %r; one of %s"
                % (i, kind, ", ".join(OPS)), {"index": i, "op": kind})
        find = op.get("find")
        if not isinstance(find, str) or not find:
            raise PatchRefused("op %d has no `find` anchor" % i, {"index": i})
        count = text.count(find)
        if count == 0:
            raise PatchRefused(
                "op %d: the `find` anchor does not occur in the manual. Quote "
                "it verbatim, including indentation and comments." % i,
                {"index": i, "matches": 0, "find": find[:200]})
        if count > 1:
            raise PatchRefused(
                "op %d: the `find` anchor occurs %d times and is therefore "
                "ambiguous. Quote more surrounding text so it occurs once."
                % (i, count),
                {"index": i, "matches": count, "find": find[:200]})

        if kind == "delete":
            new = text.replace(find, "", 1)
        else:
            with_ = op.get("with")
            if not isinstance(with_, str):
                raise PatchRefused(
                    "op %d (%s) has no `with` text" % (i, kind),
                    {"index": i, "op": kind})
            new = (text.replace(find, with_, 1) if kind == "replace"
                   else text.replace(find, find + with_, 1))
        applied.append({"index": i, "op": kind, "find_chars": len(find),
                        "delta_chars": len(new) - len(text)})
        text = new

    report = {"ops": len(ops), "applied": applied,
              "before_chars": len(theory), "after_chars": len(text),
              "delta_chars": len(text) - len(theory),
              "patch_chars": sum(len(json.dumps(o)) for o in ops)}
    return text, report


# ------------------------------------------------------------- evidence delta
def command_lines(store, *, since: int, max_new: int,
                  render_line) -> Tuple[List[str], Dict[str, Any]]:
    """The command rows to show, in delta form.

    `since` is how many labelled steps the desk was shown last time.  Rows for
    those are replaced by one rollup line; everything after them is rendered in
    full, newest included -- which today's `[:max_steps]` head-slice does not
    do once a level runs past 30 steps.  That is a widening, not a trim, and it
    is deliberate: the surprise that triggered this call lives in the newest
    rows, and paying to re-read the oldest thirty while never seeing the newest
    is the 调度失误 of `Theoria.md`:344 in prompt form.
    """
    labelled = [s for s in store.steps if s.grid is not None]
    grids = store.grids
    lines: List[str] = []
    n = len(labelled)
    start = max(0, min(since, n))
    if start:
        lines.append("- t0-t%d  %d earlier commands, already shown in full on "
                     "the previous call and unchanged since." % (start - 1, start))
    shown = labelled[start:]
    dropped = 0
    if len(shown) > max_new:
        dropped = len(shown) - max_new
        shown = shown[-max_new:]
        start += dropped
    for offset, step in enumerate(shown):
        t = start + offset
        before = grids[t - 1] if t > 0 else None
        lines.append(render_line(t, step, before))
    if dropped:
        lines.append("- ... %d commands between the rollup and these were "
                     "elided by the per-call cap." % dropped)
    return lines, {"labelled": n, "rolled_up": max(0, min(since, n)),
                   "rendered": len(shown), "elided": dropped}


def engine_delta(current: Dict[str, Any],
                 previous: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Which top-level engine reports changed since the desk last saw them.

    The engine block is a JSON dump of every engine's report and it is pinned at
    its 14 000-char truncation cap on **every call of every archived leg** --
    14 241 chars of the prompt, identical in size and largely in content, eight
    times over.  Most of it is the same proposals re-offered.

    Keys are compared by their serialised form because that is exactly what the
    desk was shown: if the bytes are the same, the desk has already read them.
    The unchanged keys are *named* in the brief, not silently dropped -- the
    desk must be able to tell "this engine said nothing new" from "this engine
    was not run", and those have opposite meanings for a `probe: pending`.
    """
    if previous is None:
        return dict(current), {"first_call": True, "changed": sorted(current),
                               "unchanged": [], "gone": []}
    changed: Dict[str, Any] = {}
    unchanged: List[str] = []
    for key, value in current.items():
        old = previous.get(key, _MISSING)
        if old is not _MISSING and _same(old, value):
            unchanged.append(key)
        else:
            changed[key] = value
    gone = sorted(k for k in previous if k not in current)
    return changed, {"first_call": False, "changed": sorted(changed),
                     "unchanged": sorted(unchanged), "gone": gone}


_MISSING = object()


def _same(a: Any, b: Any) -> bool:
    try:
        return (json.dumps(a, sort_keys=True, default=str)
                == json.dumps(b, sort_keys=True, default=str))
    except (TypeError, ValueError):                              # pragma: no cover
        return False
