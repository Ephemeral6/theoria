"""What the desk is shown, section by section, and what of it is a repeat.

`Theoria.md` 1.6 says the bill should shrink as the theory converges.  Across
today's four live legs it did not: r3 spent $13.44 over 8 desk calls, a flat
~$1.68 each, with no downward trend.  Before changing anything, this module
answers the prior question -- *what is in the prompt* -- because a bill that is
flat by construction cannot be fixed by making the theory better.

Two readings, one segmentation
------------------------------
`census(prompt)` cuts a prompt into the sections `inner.theorize.build_prompt`
concatenates, using that function's own literal headings as anchors and
scanning them **in build order** from a moving offset.  Splitting on `^## `
would be wrong: the grammar card contains six `##` headings of its own, and the
manual the desk writes is arbitrary text that may contain anything.  Anchors in
order, found from the previous section's start, is the only cut that survives
both.

`census_leg(run_dir)` replays that over a leg's archived `desk/*.md`
transcripts, which carry the prompt verbatim (`ModelDesk._write_transcript`
writes it between a "## prompt" fence and a "## reply" fence), and pairs each
call with its `desk_log.json` usage block.  Nothing here calls a model or the
network; it reads files.

Tokens: measured, not guessed
-----------------------------
There is no tokenizer offline, so this does not pretend to one.  The ledger's
`cache_creation_input_tokens` is the true billed input size of the whole
request -- CLI system prompt and tool definitions included -- so a leg with two
or more calls of differing length pins down both unknowns by least squares:

    billed_tokens = chars_per_token^-1 * chars_in + fixed_overhead

The fit's slope converts section *chars* to section *tokens*; the intercept is
everything the arm does not control (the CLI's own preamble).  `r2` is reported
next to every fit, because a fit nobody checked is a guess with error bars
drawn on.  A leg whose calls are all the same length gets `null`, not a number.

The repeat measure
------------------
`cache_read_input_tokens` in the usage block is the direct evidence of what the
provider reused between calls.  Independently of it, `repeat_vs_previous`
compares each section against the same section of the previous call: identical
bytes mean the desk was shown that section again for the second (or eighth)
time.  The two numbers answer different questions -- what was billed as new,
and what was semantically new -- and the gap between them is the finding.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

#: The sections `inner.theorize.build_prompt` emits, in the order it emits
#: them, each with the literal text that opens it.  `optional` sections are
#: absent on a cold first call (no manual yet) or on a healthy one (no compiler
#: refusal).  `kind` classifies the section for the composition rollup:
#:
#:   boilerplate -- fixed text, identical on every call of every leg forever
#:   evidence    -- what the world did
#:   books       -- what the desk itself wrote last time, handed back to it
#:   feedback    -- why it is being called again
#:
#: The classification is the whole point of the census: `Theoria.md`:344 calls
#: 调度失误 a failure class, and a prompt that is mostly boilerplate plus a
#: re-read of the whole world is that failure in prompt form.
SECTIONS: Tuple[Tuple[str, str, str, bool], ...] = (
    ("preamble",        "You are the theorize desk", "boilerplate", False),
    ("grammar_card",    "\n# theory.dsl -- the exact grammar the compiler accepts",
                                                    "boilerplate", False),
    ("obs_summary",     "\n## What has been observed", "evidence", False),
    ("current_frame",   "\n## The current frame",     "evidence", True),
    ("command_diffs",   "\n## Every command, and what changed", "evidence", False),
    ("engine_proposals", "\n## What the engines proposed", "evidence", False),
    ("manual",          "\n## The manual as it stands", "books", True),
    ("playbook",        "\n## The playbook as it stands", "books", True),
    ("surprises",       "\n## Why you are being called: the surprises that fired",
                                                    "feedback", True),
    ("certify",         "\n## What certify said about the manual you have now",
                                                    "feedback", True),
    ("compile_errors",  "\n## The compiler refused your last manual",
                                                    "feedback", True),
    ("output_contract", "\n# What to reply",         "boilerplate", False),
    # Only present when `inner.deskdiet`'s `theory_patch` knob is on. It is
    # boilerplate like the other two contracts -- fixed text, same every call --
    # and it is listed separately so a diet leg's composition can be compared
    # against a full leg's without the extra contract hiding inside
    # `output_contract` and reading as growth that never happened.
    ("patch_contract",  "\n# Writing the manual: send the EDIT, not the book",
                                                    "boilerplate", True),
)

KINDS = ("boilerplate", "evidence", "books", "feedback")

_TRANSCRIPT = re.compile(r"\n## prompt\n\n```\n(.*?)\n```\n\n## reply\n", re.DOTALL)
_CALL_NAME = re.compile(r"^call-(\d+)-")


class CensusError(RuntimeError):
    pass


# ------------------------------------------------------------------ one prompt
def census(prompt: str) -> Dict[str, Any]:
    """Cut one prompt into sections.  Total chars are conserved exactly.

    Anything before the first anchor lands in `_prologue` and anything the
    anchors do not claim lands in the section that opened it, so
    `sum(sections[*].chars) == len(prompt)` always.  A segmentation that
    silently loses bytes would understate whatever it lost.
    """
    if prompt is None:
        raise CensusError("no prompt")
    found: List[Tuple[str, str, int]] = []
    offset = 0
    for name, anchor, kind, _optional in SECTIONS:
        at = prompt.find(anchor, offset)
        if at < 0:
            continue
        found.append((name, kind, at))
        offset = at + len(anchor)

    sections: List[Dict[str, Any]] = []
    if found and found[0][2] > 0:
        sections.append({"section": "_prologue", "kind": "boilerplate",
                         "start": 0, "chars": found[0][2],
                         "text": prompt[:found[0][2]]})
    elif not found:
        raise CensusError("no build_prompt anchor found; not a desk prompt")

    for i, (name, kind, at) in enumerate(found):
        end = found[i + 1][2] if i + 1 < len(found) else len(prompt)
        sections.append({"section": name, "kind": kind, "start": at,
                         "chars": end - at, "text": prompt[at:end]})

    total = len(prompt)
    if sum(s["chars"] for s in sections) != total:
        raise CensusError("segmentation lost bytes")
    for s in sections:
        s["share"] = (s["chars"] / total) if total else 0.0
    return {"total_chars": total, "sections": sections,
            "by_kind": _rollup(sections, total),
            "present": [s["section"] for s in sections]}


def _rollup(sections: List[Dict[str, Any]], total: int) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for kind in KINDS:
        chars = sum(s["chars"] for s in sections if s["kind"] == kind)
        out[kind] = {"chars": chars, "share": (chars / total) if total else 0.0}
    return out


# ------------------------------------------------------ repeat across a leg
def repeat_vs_previous(this: Dict[str, Any],
                       prev: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """How much of this prompt the desk has already been shown, byte for byte.

    Per section: `identical` means the previous call carried the same section
    with the same bytes.  `common_prefix` is how far the two agree from the
    start, which is what a prefix cache can reuse and is therefore the number
    that matters for the bill -- a section that grew by appending is fully
    cacheable up to the append point; a section that was rewritten in the
    middle is not.
    """
    if prev is None:
        return {"first_call": True, "repeated_chars": 0, "repeated_share": 0.0,
                "prefix_chars": 0, "prefix_share": 0.0, "sections": {}}
    prev_by_name = {s["section"]: s for s in prev["sections"]}
    detail: Dict[str, Any] = {}
    repeated = 0
    for s in this["sections"]:
        old = prev_by_name.get(s["section"])
        if old is None:
            detail[s["section"]] = {"identical": False, "common_prefix": 0,
                                    "chars": s["chars"], "was_absent": True}
            continue
        same = old["text"] == s["text"]
        pre = _common_prefix(old["text"], s["text"])
        if same:
            repeated += s["chars"]
        detail[s["section"]] = {"identical": same, "common_prefix": pre,
                                "chars": s["chars"], "was_absent": False}

    whole_prefix = _common_prefix(prev.get("_prompt", ""), this.get("_prompt", ""))
    total = this["total_chars"]
    return {"first_call": False,
            "repeated_chars": repeated,
            "repeated_share": (repeated / total) if total else 0.0,
            "prefix_chars": whole_prefix,
            "prefix_share": (whole_prefix / total) if total else 0.0,
            "sections": detail}


def _common_prefix(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


# ------------------------------------------------------------ token calibration
def fit_tokens(points: List[Tuple[int, int]]) -> Dict[str, Any]:
    """Least squares `billed_tokens = slope*chars + intercept`, with r2.

    `points` is [(chars_in, cache_creation_input_tokens)].  Fewer than two
    distinct x values makes the fit undetermined, and that returns `None`
    rather than a slope invented from one point.
    """
    xs = [float(x) for x, _ in points]
    ys = [float(y) for _, y in points]
    n = len(xs)
    if n < 2 or len(set(xs)) < 2:
        return {"ok": False, "reason": "need >=2 calls of differing length",
                "n": n, "slope": None, "intercept": None, "r2": None}
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot else None
    return {"ok": True, "n": n, "slope_tokens_per_char": slope,
            "intercept_tokens": intercept,
            "chars_per_token": (1.0 / slope) if slope else None,
            "r2": r2}


def fit_tokens_paired(by_leg: Dict[str, List[Tuple[int, int]]],
                      *, min_delta_chars: int = 500) -> Dict[str, Any]:
    """Chars-per-token from WITHIN-leg differences, which kills the intercept.

    Pooling every leg's calls into one regression is wrong and the r2 says so:
    each leg carries its own fixed CLI overhead (system prompt, tool table,
    whichever model), so a pooled fit spends its slope explaining differences
    between legs rather than within them.  Differencing adjacent calls of the
    same leg removes that term exactly:

        (t2 - t1) = slope * (c2 - c1)

    The estimate is the **median** of those ratios, not the mean, because one
    call whose reply was truncated or retried would otherwise drag it.  The
    spread is reported next to it -- a median with no spread is a point estimate
    pretending to be a measurement.  Pairs whose char difference is small are
    dropped: dividing two noisy small numbers is how a ratio estimator goes
    wrong.
    """
    ratios: List[float] = []
    used_legs: List[str] = []
    for leg, points in sorted(by_leg.items()):
        ordered = list(points)
        legs_ratios = 0
        for (c1, t1), (c2, t2) in zip(ordered, ordered[1:]):
            if abs(c2 - c1) < min_delta_chars:
                continue
            ratios.append((t2 - t1) / float(c2 - c1))
            legs_ratios += 1
        if legs_ratios:
            used_legs.append(leg)
    if len(ratios) < 3:
        return {"ok": False, "reason": "need >=3 usable adjacent pairs",
                "pairs": len(ratios)}
    ratios.sort()
    n = len(ratios)
    median = (ratios[n // 2] if n % 2 else 0.5 * (ratios[n // 2 - 1] + ratios[n // 2]))
    lo = ratios[max(0, int(0.25 * (n - 1)))]
    hi = ratios[min(n - 1, int(round(0.75 * (n - 1))))]
    return {"ok": True, "pairs": n, "legs": used_legs,
            "slope_tokens_per_char": median,
            "chars_per_token": (1.0 / median) if median else None,
            "iqr_tokens_per_char": [lo, hi],
            "chars_per_token_iqr": [(1.0 / hi) if hi else None,
                                    (1.0 / lo) if lo else None]}


# ---------------------------------------------------------------- a whole leg
def read_transcript_prompt(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    match = _TRANSCRIPT.search(text)
    if not match:
        raise CensusError("no prompt fence in %s" % os.path.basename(path))
    return match.group(1)


def census_leg(run_dir: str) -> Dict[str, Any]:
    """Census every archived desk call of one leg.

    A leg with no `desk/` directory is not an error -- the mock legs and the
    aborted ones have none -- it reports `calls: 0` and says so.  An empty
    result is not silently a pass anywhere in this repo, so the caller gets the
    count and decides.
    """
    desk_dir = os.path.join(run_dir, "desk")
    log_path = os.path.join(run_dir, "desk_log.json")
    entries: List[Dict[str, Any]] = []
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as fh:
            loaded = json.load(fh)
        if isinstance(loaded, list):
            entries = loaded

    if not os.path.isdir(desk_dir):
        return {"run": os.path.basename(run_dir), "calls": 0,
                "reason": "no desk/ transcripts in this leg", "per_call": [],
                "fit": fit_tokens([]), "totals": None}

    names = sorted(n for n in os.listdir(desk_dir) if n.endswith(".md"))
    by_call = {}
    for name in names:
        m = _CALL_NAME.match(name)
        if m:
            by_call[int(m.group(1))] = os.path.join(desk_dir, name)

    log_by_call = {e.get("call"): e for e in entries if isinstance(e, dict)}

    per_call: List[Dict[str, Any]] = []
    prev: Optional[Dict[str, Any]] = None
    points: List[Tuple[int, int]] = []
    for call in sorted(by_call):
        prompt = read_transcript_prompt(by_call[call])
        cen = census(prompt)
        cen["_prompt"] = prompt
        rep = repeat_vs_previous(cen, prev)
        entry = log_by_call.get(call) or {}
        usage = entry.get("usage") or {}
        cc = usage.get("cache_creation_input_tokens")
        cr = usage.get("cache_read_input_tokens")
        if isinstance(cc, int) and cc > 0:
            points.append((len(prompt), cc))
        per_call.append({
            "call": call,
            "transcript": os.path.basename(by_call[call]),
            "chars_in": len(prompt),
            "cost_usd": entry.get("cli_cost_usd"),
            "cache_creation_input_tokens": cc,
            "cache_read_input_tokens": cr,
            "output_tokens": usage.get("output_tokens"),
            "by_kind": cen["by_kind"],
            "sections": [{k: s[k] for k in ("section", "kind", "chars", "share")}
                         for s in cen["sections"]],
            "repeat_vs_previous": rep,
        })
        prev = cen

    fit = fit_tokens(points)
    return {"run": os.path.basename(run_dir), "calls": len(per_call),
            "per_call": per_call, "fit": fit,
            "totals": _leg_totals(per_call, fit)}


def _leg_totals(per_call: List[Dict[str, Any]], fit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not per_call:
        return None
    chars = sum(c["chars_in"] for c in per_call)
    costs = [c["cost_usd"] for c in per_call if isinstance(c["cost_usd"], (int, float))]
    reads = [c["cache_read_input_tokens"] for c in per_call
             if isinstance(c["cache_read_input_tokens"], int)]
    out: Dict[str, Any] = {
        "calls": len(per_call),
        "chars_in": chars,
        "cost_usd": round(sum(costs), 6) if costs else None,
        "cost_per_call_usd": round(sum(costs) / len(costs), 6) if costs else None,
        "cache_read_total_tokens": sum(reads) if reads else (0 if reads == [] else None),
        "by_kind_chars": {k: sum(c["by_kind"][k]["chars"] for c in per_call)
                          for k in KINDS},
    }
    out["by_kind_share"] = {k: (v / chars if chars else 0.0)
                            for k, v in out["by_kind_chars"].items()}
    repeated = sum(c["repeat_vs_previous"]["repeated_chars"] for c in per_call)
    prefix = sum(c["repeat_vs_previous"]["prefix_chars"] for c in per_call)
    out["repeated_chars"] = repeated
    out["repeated_share"] = (repeated / chars) if chars else 0.0
    out["prefix_chars"] = prefix
    out["prefix_share"] = (prefix / chars) if chars else 0.0
    if fit.get("ok"):
        slope = fit["slope_tokens_per_char"]
        out["est_tokens_by_kind"] = {k: int(round(slope * v))
                                     for k, v in out["by_kind_chars"].items()}
        out["est_repeated_tokens"] = int(round(slope * repeated))
        out["est_prefix_tokens"] = int(round(slope * prefix))
    return out


def census_runs(runs_dir: str, names: Optional[List[str]] = None) -> Dict[str, Any]:
    if names is None:
        names = sorted(n for n in os.listdir(runs_dir)
                       if os.path.isdir(os.path.join(runs_dir, n)))
    legs = [census_leg(os.path.join(runs_dir, n)) for n in names]
    return {"legs": legs,
            "legs_with_desk": sum(1 for l in legs if l["calls"] > 0)}


# ------------------------------------------------------------------------ cli
def _format(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    for leg in report["legs"]:
        if not leg["calls"]:
            continue
        lines.append("=== %s  (%d desk calls) ===" % (leg["run"], leg["calls"]))
        t = leg["totals"]
        fit = leg["fit"]
        if fit.get("ok"):
            lines.append("  fit: %.4f chars/token, +%d fixed tokens, r2=%.4f"
                         % (fit["chars_per_token"], round(fit["intercept_tokens"]),
                            fit["r2"]))
        else:
            lines.append("  fit: unavailable (%s)" % fit.get("reason"))
        lines.append("  cost $%.2f over %d calls ($%.2f/call); cache_read total %s tokens"
                     % (t["cost_usd"] or 0.0, t["calls"], t["cost_per_call_usd"] or 0.0,
                        t["cache_read_total_tokens"]))
        lines.append("  composition (chars, all calls):")
        for kind in KINDS:
            lines.append("    %-12s %9d  %5.1f%%"
                         % (kind, t["by_kind_chars"][kind],
                            100 * t["by_kind_share"][kind]))
        lines.append("  verbatim-identical to previous call: %d chars (%.1f%%)"
                     % (t["repeated_chars"], 100 * t["repeated_share"]))
        lines.append("  shared prefix with previous call:    %d chars (%.1f%%)"
                     % (t["prefix_chars"], 100 * t["prefix_share"]))
        lines.append("  per call:")
        lines.append("    call  chars_in  cc_tokens  cr_tokens   $  repeat%  prefix%")
        for c in leg["per_call"]:
            r = c["repeat_vs_previous"]
            lines.append("    %4d  %8d  %9s  %9s  %5s  %6.1f  %6.1f"
                         % (c["call"], c["chars_in"],
                            c["cache_creation_input_tokens"],
                            c["cache_read_input_tokens"],
                            ("%.2f" % c["cost_usd"]) if c["cost_usd"] is not None else "-",
                            100 * r["repeated_share"], 100 * r["prefix_share"]))
        lines.append("  per-section chars, first call -> last call:")
        first = {s["section"]: s for s in leg["per_call"][0]["sections"]}
        last = {s["section"]: s for s in leg["per_call"][-1]["sections"]}
        for name in [s[0] for s in SECTIONS] + ["_prologue"]:
            if name not in first and name not in last:
                continue
            f = first.get(name, {}).get("chars", 0)
            l = last.get(name, {}).get("chars", 0)
            lines.append("    %-17s %8d -> %8d   (%+d)" % (name, f, l, l - f))
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", default=None, help="runs/ directory")
    ap.add_argument("--leg", action="append", default=None,
                    help="leg directory name; repeatable; default = all")
    ap.add_argument("--json", dest="as_json", action="store_true")
    ap.add_argument("--out", default=None, help="write the JSON report here")
    args = ap.parse_args(argv)

    runs = args.runs
    if runs is None:
        here = os.path.dirname(os.path.abspath(__file__))
        runs = os.path.join(os.path.dirname(here), "runs")
    report = census_runs(runs, args.leg)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(_strip_text(report), fh, indent=1, sort_keys=True)
            fh.write("\n")
    if args.as_json:
        print(json.dumps(_strip_text(report), indent=1, sort_keys=True))
    else:
        print(_format(report))
    return 0


def _strip_text(obj: Any) -> Any:
    """The report is an artefact; the prompts themselves are already on disk in
    `desk/`.  Carrying 100 KB of prompt text into a JSON report would make it
    unreadable and would duplicate the transcript for no gain."""
    if isinstance(obj, dict):
        return {k: _strip_text(v) for k, v in obj.items() if k != "_prompt"}
    if isinstance(obj, list):
        return [_strip_text(v) for v in obj]
    return obj


if __name__ == "__main__":
    raise SystemExit(main())
