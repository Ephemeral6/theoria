"""theorize -- the desk. The only place a concept enters the world.

`Theoria.md` 1.10(b), rule 1: engines propose, the LLM adjudicates; only the
LLM writes into the two books. Rule 2: the LLM changes the *language*, the
engines fit inside it. So this module does exactly three things:

1. dispatch -- hand the frames to the engines (`world/adapt.py`), which append
   to `candidates.jsonl` and never adjudicate anything;
2. adjudicate -- put the candidate stream, the board, the diffs, the current
   books and the surprises that fired in front of one model call, and take back
   two books and a verdict log;
3. recompile -- run the four generators, and if the manual will not compile,
   hand the compiler's own refusal back to the desk. A manual that does not
   compile is a manual that contradicts itself, and Theoria.md says that alarm
   is free.

The desk sees the candidate stream, the frames and the books. It does not see
`Theoria.md`, this repository, the pile cut, the other arms' traces or its own
source -- `ModelDesk` starts the CLI in an empty directory outside the repo for
exactly that reason (baseline-arms D-009). What it knows about the framework is
what this prompt tells it.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from world import adapt
from world.frames import FrameStore, describe_diff, render_window

from . import deskdiet
from .grammar_card import CARD

#: How many extra calls the desk gets to repair a manual that will not compile.
#: More than this and the right conclusion is that the world does not fit the
#: DSL -- which is a finding, not a budget problem.
REPAIR_ROUNDS = 2

BLOCK = re.compile(r"===\s*(THEORY|PLAYBOOK|LOG)\s*===\s*\n+```(?:\w+)?\n(.*?)```",
                   re.DOTALL)


class TheorizeResult(dict):
    pass


# ------------------------------------------------------------------ evidence
#: How many *new* command rows the delta brief renders before it elides.  Only
#: consulted when `evidence_delta` is on; the full brief keeps `max_steps`.
DELTA_MAX_NEW_STEPS = 40


def evidence_brief(store: FrameStore, engines: Dict[str, Any],
                   candidates_path: str, *, max_steps: int = 30,
                   diet: Optional["deskdiet.DeskDiet"] = None) -> str:
    """Everything the desk is allowed to see, rendered once.

    With no `diet`, or a diet with `evidence_delta` off, this returns exactly
    the text it has always returned -- the two delta branches below are the only
    additions and both are behind that flag.  `tests/test_desk_diet.py` compares
    the two paths byte for byte on the same store rather than trusting the
    reading.
    """
    delta = bool(diet is not None and diet.evidence_delta)
    state = diet.state if diet is not None else {}
    summary = store.summary()
    window = engines.get("window") or {}
    box = window.get("box")
    lines: List[str] = []

    lines.append("## What has been observed")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(summary, indent=1, sort_keys=True))
    lines.append("```")
    lines.append("")

    grid = store.current
    if grid is not None:
        lines.append("## The current frame")
        lines.append("")
        lines.append("Each cell is one hex digit 0-f standing for a colour. "
                     "Row numbers on the left, column numbers on top.")
        if box:
            lines.append("")
            lines.append("Only the cells that have EVER changed are shown "
                         "(rows %d-%d, cols %d-%d); everything outside this box "
                         "has held one colour for the whole history and is "
                         "board by definition." % tuple(box))
        lines.append("")
        lines.append("```")
        lines.append(render_window(grid, tuple(box) if box else None))
        lines.append("```")
        lines.append("")

    lines.append("## Every command, and what changed")
    lines.append("")
    lines.append("`t` indexes the state sequence. `frames` is how many grids "
                 "one command returned -- more than one means the world took "
                 "several internal steps for a single action.")
    lines.append("")
    grids = store.grids
    labelled = [s for s in store.steps if s.grid is not None]
    if delta:
        rows, _note = deskdiet.command_lines(
            store, since=int(state.get("labelled_shown", 0)),
            max_new=DELTA_MAX_NEW_STEPS, render_line=_command_row)
        lines.extend(rows)
    else:
        for t, step in enumerate(labelled[:max_steps]):
            before = grids[t - 1] if t > 0 else None
            lines.append(_command_row(t, step, grids[t - 1] if t > 0 else None))
        if len(labelled) > max_steps:
            lines.append("- ... %d more" % (len(labelled) - max_steps))
    lines.append("")

    lines.append("## What the engines proposed")
    lines.append("")
    lines.append("These are PROPOSALS. Nothing here is accepted until you "
                 "accept it, and an engine cannot name anything -- `obj0` is "
                 "the best it can do.")
    lines.append("")
    stripped = adapt.strip_internals(engines)
    if delta:
        shown, note = deskdiet.engine_delta(stripped, state.get("engines"))
        if not note["first_call"]:
            lines.append("Only the reports that CHANGED since the previous call "
                         "are printed. Unchanged, and still standing exactly as "
                         "you last read them: %s. Reported by no engine this "
                         "sweep: %s."
                         % (", ".join(note["unchanged"]) or "none",
                            ", ".join(note["gone"]) or "none"))
            lines.append("")
    else:
        shown = stripped
    lines.append("```json")
    lines.append(json.dumps(shown, indent=1,
                            sort_keys=True, default=str)[:14000])
    lines.append("```")
    lines.append("")
    lines.append("The full proposal stream is %d rows in `candidates.jsonl`."
                 % _count_lines(candidates_path))
    return "\n".join(lines)


def _command_row(t: int, step: Any, before: Any) -> str:
    """One row of the command table.

    Lifted out of the loop verbatim so the full brief and the delta brief
    cannot drift into rendering the same step two different ways -- which would
    make a before/after comparison of the two modes measure the formatting
    rather than the diet.
    """
    return ("- t%-3d %-9s frames=%-3d state=%-12s %s"
            % (t, step.action, step.n_frames, step.state,
               describe_diff(before, step.grid)))


def _count_lines(path: str) -> int:
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


# -------------------------------------------------------------------- prompt
PREAMBLE = """You are the theorize desk of a world-modelling framework called
Theoria. You are playing an ARC-AGI-3 game you have never seen, through a
64x64 grid of colour codes, by maintaining an explicit written theory of it.

Your job is NOT to pick a good move. Your job is to write two books, and the
books are the only thing that predicts anything:

  theory.dsl   -- the manual: what this world IS. Vocabulary, rules, winning
                  condition, laws. It compiles to an executable predictor, and
                  that predictor is the whole system's only predictor. If it is
                  wrong, everything downstream is wrong; there is no side door.
  playbook.dsl -- the playbook: how to WIN. Ordering, pruning, heuristics,
                  decomposition. Never a stored solution.

Six rules bind you, and they are not style advice:

1. ONLY you write these two books. Search engines put proposals in a candidate
   box; every one of them is a proposal, not a fact. You accept, reject, or
   carry it as pending, and you say why.
2. NO ENTRY WITHOUT EVIDENCE. Every rule carries the transitions that witness
   it and its coverage. A rule you believe but cannot witness does not go in
   the manual -- it goes in `laws:` as a `theorem ... [probe: pending]`, which
   is a promise to test it, not a claim that it holds.
3. NO ENTRY WITHOUT GAIN. A concept earns its place by making the manual
   shorter than writing out the pixels it explains. When a concept fails this
   test but is still needed (because some pixel would otherwise be
   unexplained), admit it AND SAY SO -- that conflict is worth more than a
   tidy manual.
4. FULL-FRAME RESPONSIBILITY. Every pixel of every frame belongs either to the
   board (cells that never vary) or to some object you declared. A pixel your
   manual cannot draw is a defect in the manual, and it will be caught: your
   manual is re-drawn onto every observed frame and compared cell by cell.
5. TRANSITIONS ARE UNAMBIGUOUS. For any state and action, exactly one
   successor. Two rules that can both fire on the same object in the same
   transition is an error, not a preference.
6. WHAT YOU DO NOT KNOW, YOU SAY. This world has been observed for a few dozen
   actions. The honest manual is small, and names its own gaps. A manual that
   over-claims will be refuted by the very next frame and cost a whole round
   to repair; a manual that under-claims just stays small.

You will be given: what has been observed, the current frame, the diff of every
command, and what the engines proposed. If a manual and a playbook already
exist you will be given those too, together with the surprises that brought you
back here -- those surprises are the reason you are being paid, and each one
must be answered by a change or by an explicit refusal to change.
"""

OUTPUT_CONTRACT = """
# What to reply

Reply with EXACTLY three blocks, in this order, and nothing else outside them.

=== THEORY ===
```
<the whole of theory.dsl, not a diff>
```

=== PLAYBOOK ===
```
<the whole of playbook.dsl, not a diff. If you have nothing defensible to say
yet, emit only comment lines -- an empty playbook is honest, an invented one is
not.>
```

=== LOG ===
```json
[
  {"id": "O-01", "subject": "obj0 (colour 6)", "verdict": "accept",
   "as": "Cart", "why": "one sentence of reasoning a reader could check
   against the candidate stream alone"},
  {"id": "R-01", "subject": "obj0_step_UP", "verdict": "probe-pending",
   "why": "..."}
]
```

`verdict` is one of: accept, reject, entailed, probe-pending.
Use `id` prefixes O- for objects, R- for rules, L- for laws, P- for probes,
E- for a thing the DSL cannot express (say what you wanted and what you wrote
instead).
"""


def build_prompt(store: FrameStore, engines: Dict[str, Any], books,
                 candidates_path: str, surprises: List[Any],
                 compile_errors: Optional[Dict[str, Any]] = None,
                 certify_report: Optional[Dict[str, Any]] = None,
                 diet: Optional["deskdiet.DeskDiet"] = None,
                 allow_patch: bool = True) -> str:
    """The prompt, and the only place the diet can change what the desk sees.

    `allow_patch` is the caller's veto: the beat turns it off on the final
    repair attempt so a desk that cannot produce a usable patch is asked for the
    whole book rather than being sent round the loop until the budget runs out.
    A diet with `theory_patch` off ignores it.
    """
    parts = [PREAMBLE, "", CARD, "",
             evidence_brief(store, engines, candidates_path, diet=diet)]

    theory = books.theory.strip()
    if theory:
        parts += ["", "## The manual as it stands", "", "```", theory, "```"]
        playbook = books.playbook.strip()
        if playbook:
            parts += ["", "## The playbook as it stands", "", "```",
                      playbook, "```"]

    if surprises:
        parts += ["", "## Why you are being called: the surprises that fired", ""]
        for item in surprises:
            parts.append("### %s (%s family -> %s)" % (item.kind, item.family,
                                                       item.book))
            parts.append("")
            parts.append(item.detail)
            if item.payload:
                parts.append("")
                parts.append("```json")
                parts.append(json.dumps(item.payload, indent=1, sort_keys=True,
                                        default=str)[:4000])
                parts.append("```")
            parts.append("")

    if certify_report:
        parts += ["", "## What certify said about the manual you have now", "",
                  "```json",
                  json.dumps(_certify_digest(certify_report), indent=1,
                             sort_keys=True, default=str)[:6000],
                  "```"]

    if compile_errors:
        parts += ["", "## The compiler refused your last manual", "",
                  "This is not a style complaint. The manual did not compile, "
                  "so it has no executable form and nothing downstream can run. "
                  "Fix the named clause; do not work around it by deleting the "
                  "content unless the content really is inexpressible, in which "
                  "case say so with an `E-` entry in the log.", "",
                  "```json",
                  json.dumps(compile_errors, indent=1, sort_keys=True)[:4000],
                  "```"]

    parts += ["", OUTPUT_CONTRACT]
    # The patch contract goes last, and only when there is something to patch.
    # A cold desk writes its first manual whole -- there is no anchor to quote
    # against an empty book, and asking for one would spend a repair round
    # learning that.
    if (diet is not None and diet.theory_patch and allow_patch
            and books.theory.strip()):
        parts += ["", deskdiet.PATCH_CONTRACT]
    return "\n".join(parts)


def _certify_digest(report: Dict[str, Any]) -> Dict[str, Any]:
    cheap = (report.get("cheap") or {}).get("checks") or {}
    return {
        "responsibility": {k: v for k, v in (cheap.get("responsibility") or {}).items()
                           if k != "first_cells"},
        "replay": {k: v for k, v in (cheap.get("replay") or {}).items()
                   if k != "first_divergence"},
        "first_divergence": (cheap.get("replay") or {}).get("first_divergence"),
        "unambiguous": cheap.get("unambiguous"),
        "proof_layer_available": report.get("proof_layer_available"),
        "expensive": {k: v for k, v in (report.get("expensive") or {}).items()
                      if k in ("available", "detail", "state_estimate", "ok")},
    }


# --------------------------------------------------------------------- reply
def parse_reply(text: str) -> Dict[str, Any]:
    blocks = {name: body for name, body in BLOCK.findall(text or "")}
    log: List[Dict[str, Any]] = []
    raw_log = blocks.get("LOG", "").strip()
    if raw_log:
        try:
            parsed = json.loads(raw_log)
            if isinstance(parsed, list):
                log = parsed
        except json.JSONDecodeError:
            log = [{"id": "?", "verdict": "unparsed", "why": raw_log[:2000]}]
    return {"theory": blocks.get("THEORY", "").strip(),
            "playbook": blocks.get("PLAYBOOK", "").strip(),
            "log": log,
            "blocks_found": sorted(blocks)}


# ---------------------------------------------------------------------- beat
def run(desk, books, store: FrameStore, candidates_path: str, *,
        surprises: Optional[List[Any]] = None,
        certify_report: Optional[Dict[str, Any]] = None,
        objects_hint: Optional[List[Dict[str, Any]]] = None,
        step_idx: Optional[int] = None,
        engines: Optional[Dict[str, Any]] = None,
        diet: Optional["deskdiet.DeskDiet"] = None) -> TheorizeResult:
    """One theorize beat: dispatch, adjudicate, recompile.

    `diet` defaults to `DeskDiet()`, which is `full` -- every knob off and the
    prompt byte-identical to the one this arm has always sent.  See
    `inner/deskdiet.py` for what the knobs do and the measurement that chose
    them.
    """
    diet = diet if diet is not None else deskdiet.full()
    result = TheorizeResult(calls=0, rounds=[], log=[], compiled=None)
    result["diet"] = diet.as_json()

    # 1. dispatch. Zero model calls; deterministic given the same frames.
    if engines is None:
        engines = adapt.run_engines(store, candidates_path)
    result["engines"] = adapt.strip_internals(engines)

    before = books.snapshot("before-theorize")
    result["snapshot_before"] = before

    compile_errors: Optional[Dict[str, Any]] = None
    patch_refusal: Optional[deskdiet.PatchRefused] = None
    census: List[Dict[str, Any]] = []
    result["prompt_census"] = census

    for attempt in range(REPAIR_ROUNDS + 1):
        # The last repair attempt always asks for the whole book. A desk that
        # has failed to produce an applicable patch twice is not going to on the
        # third try, and the round is worth more than the tokens.
        allow_patch = diet.theory_patch and attempt < REPAIR_ROUNDS
        if patch_refusal is not None:
            # Built here, not where the refusal was raised, because what the
            # desk should do next depends on whether it is still being offered
            # the patch contract. Telling it to "send a corrected patch" on the
            # very attempt that withdrew the contract would buy a refusal with a
            # paid call.
            compile_errors = {
                "patch_refused": patch_refusal.reason,
                "detail": patch_refusal.detail,
                "note": ("the manual is UNCHANGED. Send a corrected patch, or "
                         "the whole THEORY block."
                         if allow_patch else
                         "the manual is UNCHANGED, and the patch contract is "
                         "withdrawn for this attempt: send the whole THEORY "
                         "block."),
            }
            patch_refusal = None
        prompt = build_prompt(store, engines, books, candidates_path,
                              surprises or [], compile_errors, certify_report,
                              diet=diet, allow_patch=allow_patch)
        census.append(_census(prompt, attempt + 1, allow_patch))
        reply = desk.call(prompt, beat="theorize", step_idx=step_idx,
                          label="round%d" % (attempt + 1))
        result["calls"] += 1
        parsed = parse_reply(reply)
        round_entry: Dict[str, Any] = {"attempt": attempt + 1,
                                       "blocks": parsed["blocks_found"],
                                       "log_entries": len(parsed["log"])}

        theory_text = parsed["theory"]

        # 2a. the patch path. Only when the diet asked for one, the desk did not
        # override with a whole book, and there is a manual to anchor against.
        if not theory_text and allow_patch and books.theory.strip():
            try:
                ops = deskdiet.parse_patch(reply)
                if ops is None:
                    raise deskdiet.PatchRefused(
                        "the reply carried neither a === THEORY === block nor a "
                        "=== THEORY-PATCH === block; send one of them",
                        {"blocks": parsed["blocks_found"]})
                theory_text, patch_report = deskdiet.apply_patch(books.theory, ops)
                round_entry["patch"] = patch_report
            except deskdiet.PatchRefused as exc:
                round_entry["patch_refused"] = exc.reason
                round_entry["patch_detail"] = exc.detail
                result["rounds"].append(round_entry)
                patch_refusal = exc
                continue

        if not theory_text:
            round_entry["error"] = "no THEORY block in the reply"
            result["rounds"].append(round_entry)
            compile_errors = {"reply": "the reply carried no === THEORY === "
                                       "block; emit all three blocks"}
            continue

        books.write(theory=theory_text,
                    playbook=parsed["playbook"] or "# nothing defensible yet\n")
        result["log"] = parsed["log"]

        # The level instance is computed, never written by the desk. Read off
        # `theory_text`, not `parsed["theory"]` -- under the patch contract the
        # second is empty and the manual that matters is the patched one, so
        # reading the reply here would locate zero objects and hand certify an
        # empty level while the compile stayed green.
        objects = objects_hint or _objects_from_theory(theory_text)
        landmarks = _landmarks_from_theory(theory_text)
        try:
            from .books import problem_from_frames                # noqa: PLC0415
            books.write_problem(problem_from_frames(store, objects,
                                                    landmarks=landmarks))
            round_entry["objects_located"] = len(objects)
            round_entry["landmarks"] = {k: v for k, v in landmarks.items()}
        except Exception as exc:                                  # noqa: BLE001
            round_entry["problem_error"] = "%s: %s" % (type(exc).__name__, exc)

        compiled = books.compile_all()
        round_entry["compile_ok"] = bool(compiled.get("ok"))
        round_entry["compile_errors"] = compiled.get("errors")
        result["rounds"].append(round_entry)
        result["compiled"] = adapt.strip_internals(compiled)
        result["_compiled"] = compiled

        if compiled.get("ok"):
            break
        compile_errors = compiled.get("errors")

    # The delta baseline advances once per BEAT, not once per attempt: a repair
    # call is the same question asked again, and diffing it against the attempt
    # that just failed would show the desk an empty evidence section on the call
    # where it most needs the evidence.
    if diet.evidence_delta:
        diet.state["labelled_shown"] = sum(
            1 for s in store.steps if s.grid is not None)
        diet.state["engines"] = result["engines"]

    result["snapshot_after"] = books.snapshot("after-theorize")
    result["ok"] = bool((result.get("_compiled") or {}).get("ok"))
    return result


def _census(prompt: str, attempt: int, patch_asked: bool) -> Dict[str, Any]:
    """Record what this prompt was made of, on every call, live.

    The forensic pass that motivated the diet had to reconstruct this from
    archived transcripts.  Recording it as the call goes out means the next
    person asking "where did the money go" reads a number instead of writing a
    parser -- and it is the measurement this change is judged by, so it is not
    optional instrumentation.  A census that raises must not cost a desk call,
    so the failure is recorded rather than propagated.
    """
    entry: Dict[str, Any] = {"attempt": attempt, "chars": len(prompt),
                             "patch_contract": bool(patch_asked)}
    try:
        from armtools import prompt_census                      # noqa: PLC0415
        report = prompt_census.census(prompt)
        entry["by_kind"] = {k: v["chars"] for k, v in report["by_kind"].items()}
        entry["sections"] = {s["section"]: s["chars"] for s in report["sections"]}
    except Exception as exc:                                    # noqa: BLE001
        entry["census_error"] = "%s: %s" % (type(exc).__name__, exc)
    return entry


OBJECT_DECL = re.compile(r"^\s*object\s+(\w+)\s*\{([^}]*)\}", re.M)
LANDMARK_DECL = re.compile(r"^\s*landmark\s+(\w+)\s*(.*)$", re.M)
CELL_HINT = re.compile(r"arc-cell\s*[:=]\s*\(?\s*(\d+)\s*,\s*(\d+)\s*\)?")


def _landmarks_from_theory(text: str) -> Dict[str, Any]:
    """Where each declared landmark sits, from `# arc-cell: (r, c)`.

    A landmark is level data by definition (the domain/problem split), so the
    manual names it and the level places it. There is nowhere in the DSL to
    write the coordinates -- that is the point -- so the desk supplies them in a
    comment on the declaration line and this reads them back out. A landmark
    with no hint is still declared, and lands at the origin with the fact
    recorded, because the alternative is a compile error naming a level file the
    desk never sees.
    """
    out: Dict[str, Any] = {}
    for match in LANDMARK_DECL.finditer(text or ""):
        hint = CELL_HINT.search(match.group(2) or "")
        out[match.group(1)] = ((int(hint.group(1)), int(hint.group(2)))
                               if hint else None)
    return out


def _objects_from_theory(text: str) -> List[Dict[str, Any]]:
    """Which objects the manual declares, and which colour it says each is.

    The colour is read from an `# arc-colour: <n>` comment on the declaration
    line, because the DSL has no place to put a literal colour in the word
    table and the level instance needs one to locate the object in the frame.
    A declaration without it is located by nothing and enters the level as
    absent -- which certify will notice.
    """
    out = []
    for match in OBJECT_DECL.finditer(text or ""):
        name = match.group(1)
        line_end = text.find("\n", match.end())
        tail = text[match.end():line_end if line_end > 0 else len(text)]
        colour = None
        hint = re.search(r"arc-colou?r\s*[:=]\s*(\d+)", tail)
        if hint:
            colour = int(hint.group(1))
        # `arc-instances: all` spreads one declaration over every dynamic cell
        # of that colour, as one instance each of the same type -- the only way
        # an object with extent can be drawn, because the generated `render`
        # paints one cell per instance. See `books.problem_from_frames`.
        spread = re.search(r"arc-instances\s*[:=]\s*(all|one)\b", tail)
        out.append({"name": name, "type": name, "color": colour,
                    "instances": (spread.group(1) if spread else "one")})
    return out
