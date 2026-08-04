"""desk_discard -- every desk reply the arm paid for and did not use, by class.

**Why this file exists.** R2b found that 74% of the sk48 leg's spend bought
replies the arm threw away, and `armtools/replyloss.py` then found the shape of
the throwing-away: `envelope["result"]` is the CLI's *last* assistant message,
so a reply that spanned more than one message reached the arm as a tail. Both
findings are true and neither is actionable on its own, because "discarded" is
not one event. Across this archive it is five, with five different owners:

* the **transport** dropped the front of the reply (`harness/modelcall.py`),
* the **parser** refused a block whose marker carried a parenthetical
  (`inner/theorize.py:BLOCK`),
* the **beat** discarded a complete PLAYBOOK and a 19-to-31-entry LOG because
  the THEORY block was missing (`inner/theorize.py:run`),
* the **repair loop** re-sent a byte-identical prompt after a failure whose
  cause was not in the prompt,
* and the **provider** refused outright, which is not a defect at all.

A single switch cannot fix five defects, and a single number cannot price them.
This module puts each call in exactly one class, with the money and the evidence
that decided it.

**The discriminator for transport loss is arithmetic, not text.** `replyloss`
decides on where the reply *starts*, which is right for a human reading a
transcript and wrong for a guard: it cannot see a dropped message whose
successor happens to begin at the marker. The arm's own records can. The CLI
reports `usage.output_tokens` for the whole call and `usage.iterations[-1]` for
the last message only; their difference is what the earlier messages generated,
and on all 103 archived calls that difference is either zero or an exact
multiple of the model's own reported `maxOutputTokens` (64,000). Two calls that
`replyloss` reads as `well_formed` dropped a message by this test -- they are
tails that happened to resume at `=== THEORY ===`.

So: `messages_dropped` is the fact, and the reply text says what survived it.

    python -m armtools.desk_discard --runs-root theoria-arm/runs
"""

import argparse
import io
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from armtools import replyloss
# One definition, used by the transport as the call goes out and by this sweep
# afterwards. A forensic module with its own copy of the rule is a module that
# will eventually disagree with the thing it audits.
from harness.replywholeness import (MAX_OUTPUT_TOKENS_FALLBACK,  # noqa: F401
                                    messages_dropped)

#: The strict contract marker, as `inner/theorize.py` writes it.
STRICT_BLOCK = re.compile(
    r"===\s*(THEORY|PLAYBOOK|LOG)\s*===\s*\n+```(?:\w+)?\n(.*?)```", re.DOTALL)

#: The same three names, allowing the parenthetical the desk actually writes
#: when it continues a block across messages:
#: `=== THEORY (continued -- the remainder of theory.dsl, appended above) ===`.
#: `[^=\n]*` keeps the tolerance to one line and stops it swallowing the `===`.
TOLERANT_BLOCK = re.compile(
    r"===\s*(THEORY|PLAYBOOK|LOG)\b([^=\n]*)===\s*\n+```(?:\w+)?\n(.*?)```",
    re.DOTALL)

#: A qualified marker is not the whole book. `=== THEORY (continued ...) ===`
#: names a fragment, and writing a fragment into `theory.dsl` as though it were
#: the manual would be worse than refusing it -- the compile would pass on half
#: a world. Detected so the beat can say the true thing instead.
CONTINUATION_HINT = re.compile(r"\bcontinu(?:ed|ation|ing)\b", re.I)

#: The closed set. Ordered from most to least recoverable; `classify` returns
#: the first that applies, so the order is the precedence.
CLASSES = (
    "used",                      # the arm wrote the books from this reply
    "truncated_theory_fragment", # THEORY arrived, but as a continuation
    "blocks_discarded",          # PLAYBOOK and/or LOG survived and were dropped
    "transport_total_loss",      # nothing usable reached the arm
    "provider_refusal",          # the desk never ran
    "empty",                     # the CLI returned nothing
)

#: Which file owns the repair for each class. This is the whole point of the
#: module: a reply discarded by a retry loop is a loop defect, a reply that
#: cannot be parsed is a parser defect, and a reply the arm never reads is a
#: design defect. They are not the same and must not be fixed by one switch.
OWNER = {
    "used": None,
    "truncated_theory_fragment": "inner/theorize.py (parser + beat)",
    "blocks_discarded": "inner/theorize.py (beat)",
    "transport_total_loss": "harness/modelcall.py (transport)",
    "provider_refusal": None,
    "empty": None,
}


def blocks(reply: str, *, tolerant: bool) -> Dict[str, str]:
    """The three contract blocks found in `reply`, strictly or tolerantly."""
    if not tolerant:
        return {n: b for n, b in STRICT_BLOCK.findall(reply or "")}
    return {n: b for n, _q, b in TOLERANT_BLOCK.findall(reply or "")}


def qualifiers(reply: str) -> Dict[str, str]:
    """What each marker carried between its name and the closing `===`.

    Empty string for a bare `=== THEORY ===`. This is the evidence that
    separates a whole book from a continuation of one, and it is reported
    rather than acted on so a reader can check the reading.
    """
    return {n: (q or "").strip() for n, q, _b in TOLERANT_BLOCK.findall(reply or "")}


def classify(reply: str, usage: Dict[str, Any], *,
             cap: Optional[int] = None,
             cost_usd: Optional[float] = None) -> Dict[str, Any]:
    """One desk call, in exactly one class, with the evidence that decided it."""
    dropped, why_dropped = messages_dropped(usage, cap)
    strict = blocks(reply, tolerant=False)
    tol = blocks(reply, tolerant=True)
    quals = qualifiers(reply)
    stripped = (reply or "").strip()

    out: Dict[str, Any] = {
        "messages_dropped": dropped,
        "why_messages_dropped": why_dropped,
        "blocks_strict": sorted(strict),
        "blocks_tolerant": sorted(tol),
        "marker_qualifiers": {k: v for k, v in quals.items() if v},
        "log_entries": _log_len(strict.get("LOG") or tol.get("LOG")),
        "chars": len(reply or ""),
    }
    if cost_usd is not None:
        out["cost_usd"] = cost_usd

    if not stripped:
        out["verdict"] = "empty"
        out["why"] = ("the CLI returned nothing. There is no reply to have "
                      "discarded -- this is a failed call, not a wasted one.")
    elif any(stripped.startswith(p)
             for p in replyloss.PROVIDER_REFUSAL_PREFIXES):
        out["verdict"] = "provider_refusal"
        out["why"] = ("the reply is the provider's own refusal text. The desk "
                      "never ran, so nothing was thrown away and (on this "
                      "archive) nothing was billed.")
    elif "THEORY" in strict:
        out["verdict"] = "used"
        out["why"] = ("a bare `=== THEORY ===` block reached the arm, so the "
                      "beat wrote the books from this reply.")
        if dropped:
            out["why"] += (" It still dropped %d earlier message(s): the tail "
                           "happened to resume at the marker, which is luck, "
                           "not correctness." % dropped)
    elif "THEORY" in tol:
        out["verdict"] = "truncated_theory_fragment"
        out["why"] = ("the reply carries a THEORY block whose marker is "
                      "qualified (%r), which the beat's `BLOCK` regex refuses. "
                      "The fragment is real but it is NOT the whole manual, so "
                      "the honest repair is to name the truncation, not to "
                      "write the fragment into theory.dsl."
                      % quals.get("THEORY", ""))
    elif strict or tol:
        out["verdict"] = "blocks_discarded"
        out["why"] = ("the reply carries %s and %d adjudication(s), all of "
                      "which the beat discarded because the THEORY block was "
                      "absent. The contract asks for three blocks and the beat "
                      "treats them as one."
                      % (" and ".join(sorted(tol)) or "no block",
                         out["log_entries"] or 0))
    else:
        out["verdict"] = "transport_total_loss"
        out["why"] = ("no contract block survived. Whatever the desk wrote, "
                      "the arm received a fragment with no usable structure.")

    out["owner"] = OWNER[out["verdict"]]
    return out


def _log_len(raw: Optional[str]) -> Optional[int]:
    if not raw or not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
    except ValueError:
        return None
    return len(parsed) if isinstance(parsed, list) else None


# ------------------------------------------------------------------ the sweep
def _caps_from_ledger(leg_dir: str) -> Dict[int, int]:
    """`maxOutputTokens` per call, out of the CLI envelope the ledger kept.

    The desk log does not carry it. Reading it here rather than assuming 64000
    is what lets a row say whether its ceiling was measured or guessed.
    """
    path = os.path.join(leg_dir, "ledger.jsonl")
    caps: Dict[int, int] = {}
    if not os.path.isfile(path):
        return caps
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or '"model_call"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            request = record.get("request") or {}
            idx = request.get("invocation_idx")
            usage = ((record.get("response") or {}).get("modelUsage") or {})
            model = request.get("model")
            cap = (usage.get(model) or {}).get("maxOutputTokens")
            if isinstance(idx, int) and isinstance(cap, int):
                caps[idx] = cap
    return caps


def sweep_leg(leg_dir: str) -> Dict[str, Any]:
    """Every archived desk call in one leg, classified and priced."""
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
        out["counts"] = dict.fromkeys(CLASSES, 0)
        out["usd"] = dict.fromkeys(CLASSES, 0.0)
        return out

    index = replyloss._desk_log_index(leg_dir)
    caps = _caps_from_ledger(leg_dir)
    prompts: Dict[int, str] = {}

    for name in sorted(os.listdir(desk)):
        if not name.endswith(".md"):
            continue
        path = os.path.join(desk, name)
        body = replyloss.read_transcript(path)
        if body is None:
            continue
        call = replyloss._call_no(name)
        entry = index.get(call) or {}
        cap = caps.get(call)
        row = classify(body, entry.get("usage") or {}, cap=cap,
                       cost_usd=entry.get("cli_cost_usd"))
        row["call"] = call
        row["transcript"] = name
        row["label"] = entry.get("label")
        row["cap"] = cap or MAX_OUTPUT_TOKENS_FALLBACK
        row["cap_source"] = "ledger" if cap else "fallback"
        prompt = read_prompt(path)
        if prompt is not None:
            prompts[call] = prompt
        out["calls"].append(row)

    _mark_identical_reasks(out["calls"], prompts)

    out["counts"] = {c: sum(1 for r in out["calls"] if r["verdict"] == c)
                     for c in CLASSES}
    out["usd"] = {c: round(sum(r.get("cost_usd") or 0.0 for r in out["calls"]
                               if r["verdict"] == c), 6) for c in CLASSES}
    out["usd_total"] = round(sum(r.get("cost_usd") or 0.0
                                 for r in out["calls"]), 6)
    out["identical_reask_usd"] = round(
        sum(r.get("cost_usd") or 0.0 for r in out["calls"]
            if r.get("identical_reask")), 6)
    return out


def read_prompt(path: str) -> Optional[str]:
    """The prompt body out of one `desk/call-NNN-*.md`, or `None`.

    The prompt is needed for one question only: did the repair loop pay for the
    same question twice? Answering it needs the bytes, not a hash of them,
    because the transcripts are the only surviving copy.
    """
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.find("\n## prompt\n")
    if start < 0:
        return None
    end = text.find("\n## reply\n", start)
    body = text[start + len("\n## prompt\n"):end if end > 0 else len(text)]
    return replyloss._strip_transcript_fence(body)


def _mark_identical_reasks(calls: List[Dict[str, Any]],
                           prompts: Dict[int, str]) -> None:
    """Flag a call whose prompt is byte-identical to the call before it.

    This is the loop defect, and it is separate from the class: a call can be
    both `blocks_discarded` and an identical re-ask. `inner/theorize.py`'s
    repair path builds `compile_errors` from a *constant* string when the
    failure is "no THEORY block", so attempt 2 and attempt 3 of the same beat
    send the same bytes and buy the same answer twice.
    """
    for row in calls:
        row["identical_reask"] = False
        prev = prompts.get((row.get("call") or 0) - 1)
        here = prompts.get(row.get("call"))
        if prev is not None and here is not None and prev == here:
            row["identical_reask"] = True
            row["why_identical_reask"] = (
                "the prompt is byte-identical to call %d's. The previous "
                "attempt failed, and the arm paid again to ask exactly the "
                "same question -- so whatever caused the failure, this call "
                "could not have addressed it."
                % ((row.get("call") or 0) - 1))


def sweep(runs_root: str) -> Dict[str, Any]:
    """Every leg under `runs_root`, including the clean ones."""
    legs: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(runs_root)):
        path = os.path.join(runs_root, name)
        if not os.path.isdir(path) or not os.path.isdir(os.path.join(path, "desk")):
            continue
        legs.append(sweep_leg(path))

    counts = {c: sum(leg["counts"][c] for leg in legs) for c in CLASSES}
    usd = {c: round(sum(leg["usd"][c] for leg in legs), 6) for c in CLASSES}
    usd_total = round(sum(leg["usd_total"] for leg in legs), 6)
    dropped = [r for leg in legs for r in leg["calls"]
               if (r.get("messages_dropped") or 0) > 0]
    unknown = [r for leg in legs for r in leg["calls"]
               if r.get("messages_dropped") is None]

    return {
        "legs": legs,
        "legs_with_transcripts": len(legs),
        "calls": sum(len(leg["calls"]) for leg in legs),
        "counts": counts,
        "usd": usd,
        "usd_total": usd_total,
        "owners": {c: OWNER[c] for c in CLASSES},
        "transport": {
            "calls_that_dropped_a_message": len(dropped),
            "usd": round(sum(r.get("cost_usd") or 0.0 for r in dropped), 6),
            "calls_with_unknown_wholeness": len(unknown),
            "note": ("`calls_with_unknown_wholeness` counts calls whose usage "
                     "carries no per-message `iterations`. They are not "
                     "counted as whole and not counted as truncated."),
        },
        "identical_reask": {
            "calls": sum(1 for leg in legs for r in leg["calls"]
                         if r.get("identical_reask")),
            "usd": round(sum(leg["identical_reask_usd"] for leg in legs), 6),
        },
        "reading": _reading(counts, usd, usd_total),
    }


def _reading(counts: Dict[str, int], usd: Dict[str, float],
             usd_total: float) -> str:
    if not usd_total:
        return ("no priced desk call was found, so nothing was classified. "
                "This is an absence, not a clean sweep.")
    discarded = sum(usd[c] for c in ("truncated_theory_fragment",
                                     "blocks_discarded", "transport_total_loss"))
    return (
        "$%.4f of a $%.4f desk bill bought a reply the arm did not use, %.1f%% "
        "of the whole. It is not one defect: $%.4f is a reply whose PLAYBOOK "
        "and LOG survived and were discarded for want of a THEORY block (a "
        "beat defect, %d calls), $%.4f is a THEORY block the parser refused "
        "for its marker (a parser defect, %d calls), and $%.4f reached the arm "
        "with no usable structure at all (a transport defect, %d calls). The "
        "%d provider refusals are not in that total and were not billed."
        % (discarded, usd_total, 100.0 * discarded / usd_total,
           usd["blocks_discarded"], counts["blocks_discarded"],
           usd["truncated_theory_fragment"], counts["truncated_theory_fragment"],
           usd["transport_total_loss"], counts["transport_total_loss"],
           counts["provider_refusal"]))


# ----------------------------------------------------------------- the replay
class _ReplayBooks:
    """The smallest thing `_salvage` can write to.

    A stand-in, not a mock of `inner.books.Books`: the replay must not touch a
    real book directory, and the only two facts `_salvage` needs are whether a
    manual already exists and where the playbook goes. Kept here rather than in
    the test so the reported number and the tested number come from one path.
    """

    def __init__(self, theory: str = "") -> None:
        self.theory = theory
        self.playbook = ""
        self.writes = 0

    def write(self, theory: str = "", playbook: str = "") -> None:
        self.theory = theory
        self.playbook = playbook
        self.writes += 1


def replay(runs_root: str) -> Dict[str, Any]:
    """Push every archived reply back through the repaired paths.

    Zero API calls, zero spend: the transcripts are the material. What this can
    and cannot show, stated before the numbers:

    * It **can** show what the repaired parser and the repaired beat would have
      kept out of replies already on disk. That is a fact about bytes.
    * It **cannot** show what the repaired *loop* would have bought, because a
      different prompt gets a different reply and there is no reply on disk for
      a prompt that was never sent. The identical re-asks are reported as spend
      that would not have been made, which is a floor on the loop's value and
      not an estimate of it.
    * It **cannot** show anything about the transport repair at all. The front
      of a truncated reply is not in the envelope, in the ledger, or in the
      transcript. `transport_total_loss` stays lost under replay; only a live
      call over a different transport recovers it, and none was made.
    """
    from inner import theorize                                # noqa: PLC0415

    sweep_report = sweep(runs_root)
    kept = {"log_entries": 0, "playbooks": 0, "usd_touched": 0.0}
    unrecoverable = {"usd": 0.0, "calls": 0}
    rows: List[Dict[str, Any]] = []

    for leg in sweep_report["legs"]:
        legdir = os.path.join(runs_root, leg["leg"])
        for row in leg["calls"]:
            if row["verdict"] not in ("blocks_discarded",
                                      "truncated_theory_fragment",
                                      "transport_total_loss"):
                continue
            body = replyloss.read_transcript(
                os.path.join(legdir, "desk", row["transcript"]))
            parsed = theorize.parse_reply(body or "")
            # A manual is assumed present: every one of these calls is a repair
            # or a later beat on a leg that had already written books, which is
            # what the archive shows. `_salvage` refuses to write a playbook
            # against an empty manual, and that refusal is the conservative
            # direction here.
            books = _ReplayBooks(theory="# carried manual (replay stand-in)\n")
            salvaged = theorize._salvage(books, parsed)
            complaint = theorize._missing_theory(
                parsed, row.get("messages_dropped"), allow_patch=False)
            usd = row.get("cost_usd") or 0.0
            recovered = bool(salvaged["salvaged_log_entries"]
                             or salvaged["salvaged_playbook"])
            if recovered:
                kept["log_entries"] += salvaged["salvaged_log_entries"]
                kept["playbooks"] += int(salvaged["salvaged_playbook"])
                kept["usd_touched"] += usd
            else:
                unrecoverable["usd"] += usd
                unrecoverable["calls"] += 1
            rows.append({
                "leg": leg["leg"], "call": row["call"], "cost_usd": usd,
                "verdict": row["verdict"],
                "salvaged_log_entries": salvaged["salvaged_log_entries"],
                "salvaged_playbook": salvaged["salvaged_playbook"],
                "complaint_names_truncation": "transport_truncation" in complaint,
                "complaint_is_the_old_constant":
                    complaint.get("reply") == ("the reply carried no === THEORY "
                                               "=== block; emit all three blocks"),
            })

    kept["usd_touched"] = round(kept["usd_touched"], 6)
    unrecoverable["usd"] = round(unrecoverable["usd"], 6)
    discarded_usd = sum(sweep_report["usd"][c] for c in
                        ("blocks_discarded", "truncated_theory_fragment",
                         "transport_total_loss"))
    return {
        "rows": rows,
        "discarded_usd": round(discarded_usd, 6),
        "kept": kept,
        "unrecoverable_by_replay": unrecoverable,
        "recovered_share_of_discarded": (round(kept["usd_touched"] / discarded_usd, 4)
                                         if discarded_usd else None),
        "identical_reask_usd_not_spent":
            sweep_report["identical_reask"]["usd"],
        "complaints_that_now_name_the_truncation":
            sum(1 for r in rows if r["complaint_names_truncation"]),
        "complaints_still_the_old_constant":
            sum(1 for r in rows if r["complaint_is_the_old_constant"]),
        "caveat": ("`recovered_share_of_discarded` is the share of discarded "
                   "spend whose reply carried something the repaired beat "
                   "keeps -- adjudications and a playbook. It is NOT a claim "
                   "that the manual was recovered: no manual was. The "
                   "transport repair is not exercised here at all."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--replay", action="store_true",
                    help="push archived replies through the repaired paths")
    ap.add_argument("--runs-root", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs"))
    ap.add_argument("--out", default=None, help="write the sweep as JSON here")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.replay:
        out = replay(args.runs_root)
        if args.out:
            with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(out, fh, indent=1, sort_keys=True)
                fh.write("\n")
        if not args.quiet:
            for r in out["rows"]:
                print("%-30s call %-3s $%7.4f %-26s log=%-4s playbook=%-5s "
                      "truncation_named=%s"
                      % (r["leg"][:30], r["call"], r["cost_usd"], r["verdict"],
                         r["salvaged_log_entries"], r["salvaged_playbook"],
                         r["complaint_names_truncation"]))
            print()
            print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                             indent=1, sort_keys=True))
        return 0

    report = sweep(args.runs_root)
    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=1, sort_keys=True)
            fh.write("\n")
    if not args.quiet:
        for leg in report["legs"]:
            rows = [r for r in leg["calls"]
                    if r["verdict"] not in ("used", "provider_refusal")
                    or (r.get("messages_dropped") or 0) > 0
                    or r.get("identical_reask")]
            if not rows:
                continue
            print(leg["leg"])
            for r in rows:
                print("    call %-3s $%7.4f  drop=%-4s %-26s %s%s"
                      % (r["call"], r.get("cost_usd") or 0.0,
                         r["messages_dropped"], r["verdict"],
                         ",".join(r["blocks_tolerant"]) or "-",
                         "  [identical re-ask]" if r.get("identical_reask") else ""))
        print()
        print(json.dumps({"counts": report["counts"], "usd": report["usd"]},
                         indent=1, sort_keys=True))
        print(json.dumps(report["identical_reask"], sort_keys=True))
        print()
        print(report["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
