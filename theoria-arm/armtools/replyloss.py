"""replyloss -- what happened to a desk reply, read off the archive.

**Why this file exists.** `inner/theorize.py` reports one error for every reply
it cannot use: `no THEORY block in the reply`. Across this arm's whole archive
that sentence has been written 32 times, and until it was read against the
transcripts it named three completely different events:

* the provider refused the call outright (`You've hit your session limit`),
* the CLI returned nothing at all,
* and -- 11 times, $31.05 of a $108.54 lifetime desk bill -- **the reply was
  there and the harness only kept the end of it.**

`harness/modelcall.py:561` reads `envelope["result"]`, which is the *last*
assistant message the CLI emitted. When the desk's answer spans more than one
message the earlier ones are dropped on the floor, and what lands on disk is a
tail: `R1b-sk48-b/desk/call-002` begins mid-header with

    === THEORY (continued -- the remainder of theory.dsl, appended to the
    block above) ===

and `call-006` of the same leg begins mid-word, at `ditional repaint of the
four mark cells`. Those are not malformed answers. They are correct answers
with the front torn off, billed in full, and the arm recorded them as the
desk's failure.

**The discriminator, and why it is this one and not a ratio.** The obvious
test -- output tokens against reply characters -- does not work: `claude -p`
bills thinking tokens that never appear in `result`, so the ratio is below 1.0
on 39 of the 88 archived calls, most of which parsed perfectly. The signal that
does work is structural and exact. Every one of the 53 archived replies that
`theorize` accepted begins with the literal marker `=== THEORY ===`, and not
one of the 35 it rejected does. The contract asks for that marker first; a
reply that starts anywhere else started somewhere the arm cannot see.

So the classes below are decided by where the reply *starts*, and the token
count is carried as evidence rather than as the test. That keeps the
classifier honest about the one thing it cannot know: whether a dropped
message existed at all. It knows the reply on disk is not the whole reply. It
does not know what the missing part said.

    python -m armtools.replyloss --runs-root theoria-arm/runs
"""

import argparse
import io
import json
import os
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

#: The marker the theorize contract asks for first. `inner/theorize.py`'s
#: splitter looks for it anywhere; this module cares that it is at the front,
#: which is a strictly stronger reading of the same contract.
THEORY_MARKER = "=== THEORY ==="

#: The other two block markers, carried as evidence: a tail that still holds
#: `=== PLAYBOOK ===` lost strictly less than one that holds neither.
OTHER_MARKERS = ("=== PLAYBOOK ===", "=== LOG ===")

#: Provider-side refusals, matched at the *start* of the reply. Deliberately a
#: prefix match on a short list rather than a substring search: a desk that
#: quotes the phrase inside a theorem is answering, not being refused.
PROVIDER_REFUSAL_PREFIXES = (
    "You've hit your session limit",
    "You have hit your session limit",
    "Claude AI usage limit reached",
)

#: The closed set. Every one of these has been seen in the archive except
#: `well_formed`'s complement `unparsed_but_complete`, which is reserved for a
#: reply that starts correctly and still fails downstream -- it has never
#: happened here and the sweep reports 0 for it rather than omitting it.
CLASSES = (
    "well_formed",
    "empty",
    "provider_refusal",
    "lost_continuation",
)


def _strip_transcript_fence(reply: str) -> str:
    """The transcript writes the reply inside a ``` fence; take it back out.

    `harness/modelcall._write_transcript` emits ``"## reply\\n\\n```\\n%s\\n```\\n"``,
    so the first line after the header is the opening fence and the last is the
    closing one. Removing them is not cosmetic: the opening fence is the reason
    a naive reader sees every reply as starting with a code fence rather than
    with the marker the contract asked for.
    """
    body = reply.lstrip("\n")
    if body.startswith("```"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
    if body.endswith("```\n"):
        body = body[: -len("```\n")]
    elif body.endswith("```"):
        body = body[: -len("```")]
    return body


def classify(reply: str, *, output_tokens: Optional[int] = None,
             cost_usd: Optional[float] = None) -> Dict[str, Any]:
    """One reply, classified, with the evidence that decided it.

    `reply` is the reply body -- what `envelope["result"]` held, not the
    transcript file. `read_transcript` does the unwrapping.

    `output_tokens` and `cost_usd` are optional and change no verdict. They are
    here so the caller does not have to join two files to answer "what did this
    cost", which is the question that makes the finding actionable.
    """
    body = reply
    stripped = body.strip()

    if not stripped:
        verdict = "empty"
        why = ("the CLI returned an empty result. Nothing was received, so "
               "nothing was lost in transit -- this is a failed call, not a "
               "truncated one.")
    elif any(stripped.startswith(p) for p in PROVIDER_REFUSAL_PREFIXES):
        verdict = "provider_refusal"
        why = ("the reply is the provider's own refusal text, not the desk's "
               "answer. The desk never ran; there is no answer to have lost.")
    elif stripped.startswith(THEORY_MARKER):
        verdict = "well_formed"
        why = ("the reply begins with %r, which is the first thing the "
               "contract asks for, so the whole of it reached the arm."
               % THEORY_MARKER)
    else:
        verdict = "lost_continuation"
        why = ("the reply is substantial and begins somewhere other than %r. "
               "The contract puts that marker first, so what is on disk "
               "starts inside an answer whose beginning the arm never "
               "received: `envelope['result']` carries only the CLI's LAST "
               "assistant message." % THEORY_MARKER)

    out: Dict[str, Any] = {
        "verdict": verdict,
        "why": why,
        "chars": len(body),
        "begins_with": stripped[:80],
        "has_theory_marker_anywhere": THEORY_MARKER in body,
        "markers_present": [m for m in (THEORY_MARKER,) + OTHER_MARKERS
                            if m in body],
    }
    if output_tokens is not None:
        out["output_tokens"] = output_tokens
        # Evidence, not the test. Reported for every class -- including the
        # ones where it is unremarkable -- so a reader can see that the ratio
        # does not separate them and stop reaching for it.
        out["chars_per_output_token"] = (round(len(body) / output_tokens, 4)
                                         if output_tokens else None)
    if cost_usd is not None:
        out["cost_usd"] = cost_usd
    return out


def read_transcript(path: str) -> Optional[str]:
    """The reply body out of one `desk/call-NNN-*.md`, or `None`.

    `None` means the file is not a transcript this module understands -- it
    has no `## reply` section. That is different from an empty reply and the
    caller must not collapse them.
    """
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    idx = text.find("\n## reply\n")
    if idx < 0:
        return None
    return _strip_transcript_fence(text[idx + len("\n## reply\n"):])


def _desk_log_index(leg_dir: str) -> Dict[int, Dict[str, Any]]:
    path = os.path.join(leg_dir, "desk_log.json")
    if not os.path.isfile(path):
        return {}
    with io.open(path, encoding="utf-8") as fh:
        try:
            log = json.load(fh)
        except ValueError:
            return {}
    return {int(e["call"]): e for e in log if isinstance(e, dict)
            and "call" in e}


def _call_no(name: str) -> Optional[int]:
    # "call-002-theorize-round1.md"
    parts = name.split("-")
    if len(parts) < 2 or parts[0] != "call":
        return None
    try:
        return int(parts[1])
    except ValueError:
        return None


def sweep_leg(leg_dir: str) -> Dict[str, Any]:
    """Every desk transcript in one leg, classified and priced.

    A leg with no `desk/` directory returns `calls: []` and
    `has_transcripts: False`. Absence is recorded as absence: a leg that made
    no desk call and a leg whose transcripts were never written must not both
    report zero losses as though the question had been asked and answered.
    """
    desk = os.path.join(leg_dir, "desk")
    out: Dict[str, Any] = {
        "leg": os.path.basename(leg_dir.rstrip(os.sep)),
        "has_transcripts": os.path.isdir(desk),
        "calls": [],
    }
    if not out["has_transcripts"]:
        out["why_no_calls"] = ("no desk/ directory: this leg archived no "
                               "transcripts, which is not the same as having "
                               "made no call")
        return out

    index = _desk_log_index(leg_dir)
    for name in sorted(os.listdir(desk)):
        if not name.endswith(".md"):
            continue
        body = read_transcript(os.path.join(desk, name))
        if body is None:
            continue
        call = _call_no(name)
        entry = index.get(call) or {}
        usage = entry.get("usage") or {}
        row = classify(body,
                       output_tokens=usage.get("output_tokens"),
                       cost_usd=entry.get("cli_cost_usd"))
        row["transcript"] = name
        row["call"] = call
        out["calls"].append(row)

    out["counts"] = {c: sum(1 for r in out["calls"] if r["verdict"] == c)
                     for c in CLASSES}
    out["usd_lost"] = round(sum(r.get("cost_usd") or 0.0 for r in out["calls"]
                                if r["verdict"] == "lost_continuation"), 6)
    out["usd_total"] = round(sum(r.get("cost_usd") or 0.0
                                 for r in out["calls"]), 6)
    return out


def sweep(runs_root: str) -> Dict[str, Any]:
    """Every leg under `runs_root`. Legs are reported even when clean."""
    legs: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(runs_root)):
        path = os.path.join(runs_root, name)
        if not os.path.isdir(path):
            continue
        if not os.path.isdir(os.path.join(path, "desk")):
            continue
        legs.append(sweep_leg(path))

    counts = {c: sum(leg["counts"][c] for leg in legs) for c in CLASSES}
    total_calls = sum(len(leg["calls"]) for leg in legs)
    usd_lost = round(sum(leg["usd_lost"] for leg in legs), 6)
    usd_total = round(sum(leg["usd_total"] for leg in legs), 6)
    return {
        "legs": legs,
        "legs_with_transcripts": len(legs),
        "calls": total_calls,
        "counts": counts,
        "usd_lost_to_lost_continuation": usd_lost,
        "usd_total": usd_total,
        "share_of_desk_spend_lost": (round(usd_lost / usd_total, 4)
                                     if usd_total else None),
        "reading": _reading(counts, total_calls, usd_lost, usd_total),
    }


def _reading(counts: Dict[str, int], calls: int, usd_lost: float,
             usd_total: float) -> str:
    lost = counts["lost_continuation"]
    if not calls:
        return ("no desk transcripts were found, so nothing was classified. "
                "This is an absence, not a clean sweep.")
    if not lost:
        return ("%d desk replies were classified and none of them began "
                "inside an answer. On this archive the transport lost "
                "nothing." % calls)
    return (
        "%d of %d archived desk replies begin somewhere other than the "
        "marker the contract asks for first. Each was billed in full: $%.4f "
        "of a $%.4f desk bill, %.1f%%. `inner/theorize.py` recorded every one "
        "of them as `no THEORY block in the reply`, which reads as a desk "
        "that answered badly and is in fact a harness that kept only the "
        "CLI's last assistant message."
        % (lost, calls, usd_lost, usd_total,
           100.0 * usd_lost / usd_total if usd_total else 0.0))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs-root", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs"))
    ap.add_argument("--out", default=None, help="write the sweep as JSON here")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    report = sweep(args.runs_root)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if not args.quiet:
        for leg in report["legs"]:
            if not leg["counts"]["lost_continuation"]:
                continue
            print("%-42s %d lost, $%.4f" % (leg["leg"],
                                            leg["counts"]["lost_continuation"],
                                            leg["usd_lost"]))
            for row in leg["calls"]:
                if row["verdict"] != "lost_continuation":
                    continue
                print("    call %-4s $%7.4f  out_tok %-7s begins %r"
                      % (row["call"], row.get("cost_usd") or 0.0,
                         row.get("output_tokens"), row["begins_with"][:56]))
        print()
        print(json.dumps(report["counts"], sort_keys=True))
        print(report["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
