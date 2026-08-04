"""What a desk call delivered, against what it cost.

`prompt_census` answers *what the desk was shown*.  This module answers the
other half -- *what the desk gave back* -- because the two R2b legs of
2026-08-01 disagreed by 3.5x in cost per action while the cheaper leg was
shown the **larger** prompt, and no census of the input can explain that.

The three measurements
----------------------
**1. Where the money actually is.**  The bill is not the prompt.  Every
`model_call` row carries three billable token counts (cache write, cache read,
output) and the CLI's own `costUSD`; `price_fit` recovers the per-million rate
of each by least squares over a leg's calls and reports the worst residual, so
a decomposition nobody checked does not get to call itself a measurement.  On
the R2b pair the output term carries 58-79% of every call.

**2. Whether the reply was usable at all.**  `inner.theorize`'s output contract
demands exactly three blocks -- `=== THEORY ===`, `=== PLAYBOOK ===`,
`=== LOG ===` -- and the arm refuses a reply that omits the first with
"the reply carried no === THEORY === block".  `blocks_in_reply` reads the
archived transcript and says which blocks arrived.  A reply that is missing
THEORY is not a partial success: the manual does not change, the compiler has
nothing new to refuse, and the next call is handed a **byte-identical** prompt.
The money is spent and the leg does not move.

**3. Whether the manual is being compressed.**  `Theoria.md` 1.8 and
`inner.theorize`'s rule 3 say a concept earns its place by making the manual
SHORTER.  `manual_trajectory` reads `books/snapshots/rev*-after-theorize/` and
reports the size after every theorize, plus the plain arithmetic of whether the
book ended smaller than the seed it carried.  This is a report, not a gate:
growth can be honest when the world got bigger.  It is written down so the
question stops being answered from memory.

Nothing here calls a model or the network.  It reads `desk/*.md`,
`desk_log.json`, `ledger.jsonl` and `books/snapshots/`.

    python -m armtools.desk_yield runs/<leg> [runs/<leg> ...]
    python -m armtools.desk_yield --json runs/<leg>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: The three blocks `inner.theorize.OUTPUT_CONTRACT` demands, in its order.
BLOCKS: Tuple[str, ...] = ("THEORY", "PLAYBOOK", "LOG")

#: The block whose absence makes the whole call void.  `inner.books` stores the
#: manual only from a THEORY block; without one the books are untouched.
REQUIRED_BLOCK = "THEORY"

_BLOCK = re.compile(r"^=== (THEORY|PLAYBOOK|LOG) ===\s*$", re.MULTILINE)
_REPLY_FENCE = "\n## reply\n"
#: The prompt as `ModelDesk._write_transcript` fences it.  Taking everything
#: before "## reply" instead would fold in the transcript's own header, which
#: names the call -- so two byte-identical prompts would compare unequal and
#: the retry loop this module exists to find would be invisible.
_PROMPT_FENCE = re.compile(r"\n## prompt\n\n```\n(.*?)\n```\n\n## reply\n", re.DOTALL)
_CALL_NAME = re.compile(r"^call-(\d+)-")

#: Chars per output token, used ONLY to split a reply's tokens from the
#: thinking tokens billed alongside it.  It is a stated constant, not a
#: measurement, and every field derived from it carries `_est` in its name.
#: 3.7 is the conventional English figure; the conclusions below survive
#: anything in 3.0-4.5 because the gap they describe is a factor of ten.
CHARS_PER_OUTPUT_TOKEN_EST = 3.7


class YieldError(RuntimeError):
    pass


# ----------------------------------------------------------------- the reply
def split_transcript(path: str) -> Tuple[str, str]:
    """Return `(prompt, reply)` from an archived `desk/call-*.md`.

    `ModelDesk._write_transcript` writes the prompt between a "## prompt" fence
    and a "## reply" fence.  The prompt is taken from inside the fence, exactly
    as `prompt_census` takes it, so two calls sent the same prompt compare
    equal; the reply is everything after the fence, without requiring it to be
    fenced too -- a truncated transcript still has a readable reply, and
    refusing to read one would hide exactly the calls worth looking at.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    at = text.find(_REPLY_FENCE)
    if at < 0:
        raise YieldError("no reply fence in %s" % os.path.basename(path))
    fenced = _PROMPT_FENCE.search(text)
    prompt = fenced.group(1) if fenced else text[:at]
    return prompt, text[at + len(_REPLY_FENCE):]


def blocks_in_reply(reply: str) -> List[str]:
    """The contract blocks present, in the order they appear, duplicates kept.

    Duplicates are kept because they happen and they matter: one R2b call
    emitted `THEORY` four times, which is a different defect from emitting it
    once, and a `set` would have erased it.
    """
    return [m.group(1) for m in _BLOCK.finditer(reply)]


def delivered(reply: str) -> Dict[str, Any]:
    names = blocks_in_reply(reply)
    unique = sorted(set(names))
    return {
        "blocks": names,
        "blocks_unique": unique,
        "has_required": REQUIRED_BLOCK in unique,
        "missing": [b for b in BLOCKS if b not in unique],
        "duplicated": sorted({b for b in names if names.count(b) > 1}),
        "reply_chars": len(reply),
    }


# ----------------------------------------------------------------- the price
def price_fit(rows: Sequence[Tuple[int, int, int, float]]) -> Dict[str, Any]:
    """Recover `$/Mtok` for (cache_write, cache_read, output) by least squares.

    `rows` is [(cache_creation, cache_read, output, usd)].  Three unknowns need
    at least three calls, and returns `None` below that rather than a rate
    invented from two.  `max_abs_residual_usd` is reported next to the rates:
    a decomposition whose residual is a large fraction of a call's bill is not
    a decomposition, and the caller is given the number to judge that with.

    Implemented with the normal equations and a small Gaussian elimination so
    the module has no numpy import -- it is read by people auditing a bill, and
    a dependency is one more thing that can differ between two machines.
    """
    usable = [r for r in rows if isinstance(r[3], (int, float))]
    if len(usable) < 3:
        return {"ok": False, "reason": "need >=3 priced calls", "n": len(usable)}
    xs = [[r[0] / 1e6, r[1] / 1e6, r[2] / 1e6] for r in usable]
    ys = [float(r[3]) for r in usable]
    n = 3
    ata = [[sum(x[i] * x[j] for x in xs) for j in range(n)] for i in range(n)]
    atb = [sum(x[i] * y for x, y in zip(xs, ys)) for i in range(n)]
    coef = _solve(ata, atb)
    if coef is None:
        return {"ok": False, "reason": "singular: the three token counts are "
                                       "collinear across these calls",
                "n": len(usable)}
    resid = [abs(sum(c * v for c, v in zip(coef, x)) - y) for x, y in zip(xs, ys)]
    mean_usd = sum(ys) / len(ys)
    names = ("cache_write", "cache_read", "output")
    rates = dict(zip(names, coef))
    # A negative $/Mtok is not a discount; it is the fit saying that term is
    # not identified by these calls.  On the R2b pair only 4 of 15 calls read
    # any cache at all, and those four are also the longest, so the cache_read
    # column carries almost no independent variation and its coefficient
    # absorbs whatever the other two miss.  Named here rather than rounded to
    # zero: a rate that came out impossible is a fact about the data, and the
    # two terms that DO have variation (which is where 100% of the finding
    # lives) are unaffected by it.
    unidentified = sorted(k for k, v in rates.items() if v < 0)
    nonzero = {k: sum(1 for x in xs if x[i] > 0) for i, k in enumerate(names)}
    return {
        "ok": True,
        "n": len(usable),
        "usd_per_mtok": rates,
        "calls_with_nonzero_tokens": nonzero,
        "unidentified_terms": unidentified,
        "max_abs_residual_usd": max(resid),
        "max_residual_share_of_mean_bill": (max(resid) / mean_usd) if mean_usd else None,
    }


def _solve(a: List[List[float]], b: List[float]) -> Optional[List[float]]:
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-15:
            return None
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r == col:
                continue
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


# ------------------------------------------------------------ the manual size
_REV = re.compile(r"^rev(\d+)-(.+)$")


def manual_trajectory(run_dir: str) -> Dict[str, Any]:
    """Manual and playbook size at every archived revision.

    `Theoria.md` 1.8 / `inner.theorize` rule 3: a concept earns its place by
    making the manual shorter.  This reports the sizes and the plain
    subtraction; it does not rule.  `after_theorize` is the sequence that
    matters -- the `before-theorize` snapshots are copies of the previous
    `after`, and counting both would double every plateau.
    """
    snaps = os.path.join(run_dir, "books", "snapshots")
    if not os.path.isdir(snaps):
        return {"revisions": [], "reason": "no books/snapshots in this leg"}
    revs: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(snaps)):
        m = _REV.match(name)
        if not m:
            continue
        entry: Dict[str, Any] = {"rev": int(m.group(1)), "phase": m.group(2)}
        for book in ("theory", "playbook"):
            path = os.path.join(snaps, name, book + ".dsl")
            entry[book + "_chars"] = (os.path.getsize(path)
                                      if os.path.exists(path) else None)
        revs.append(entry)
    revs.sort(key=lambda e: e["rev"])

    carried = next((r for r in revs if r["phase"] == "carried"), None)
    after = [r for r in revs if r["phase"] == "after-theorize"]
    sizes = [r["theory_chars"] for r in after if r["theory_chars"] is not None]
    out: Dict[str, Any] = {
        "revisions": revs,
        "after_theorize_theory_chars": sizes,
        "carried_theory_chars": carried["theory_chars"] if carried else None,
        "theorize_writes": len(sizes),
    }
    if sizes and carried and carried["theory_chars"]:
        seed = carried["theory_chars"]
        out["final_vs_carried_chars"] = sizes[-1] - seed
        out["final_vs_carried_ratio"] = sizes[-1] / seed
        out["ended_shorter_than_carried"] = sizes[-1] < seed
    if len(sizes) >= 2:
        out["monotone_growth_after_first_write"] = all(
            b >= a for a, b in zip(sizes[1:], sizes[2:])) if len(sizes) > 2 else None
        out["net_growth_after_first_write_chars"] = sizes[-1] - sizes[0]
        out["frozen_tail_writes"] = _frozen_tail(sizes)
    return out


def _frozen_tail(sizes: Sequence[int]) -> int:
    """How many trailing theorize writes left the manual exactly the same size.

    Same size is not the same bytes, so this is evidence and not proof -- but a
    desk that rewrote a 32 kB manual to the byte-count it already had, three
    times running, is the signature worth surfacing.
    """
    n = 0
    for a, b in zip(reversed(sizes), list(reversed(sizes))[1:]):
        if a == b:
            n += 1
        else:
            break
    return n


# ------------------------------------------------------------------- one leg
def _read_ledger_calls(run_dir: str) -> Dict[int, Dict[str, Any]]:
    """`num_turns`/`stop_reason`/per-model usage, keyed by 1-based call number.

    `desk_log.json` is the arm's own record and is authoritative for the bill.
    The ledger carries what the arm did not copy across -- how many turns the
    CLI took, and which side models it charged -- so a call that looks like one
    turn but billed two output budgets can be told apart from one that did not.
    """
    path = os.path.join(run_dir, "ledger.jsonl")
    out: Dict[int, Dict[str, Any]] = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("event") != "model_call":
                continue
            idx = row.get("call_idx")
            if not isinstance(idx, int):
                continue
            resp = row.get("response") or {}
            usage = (resp.get("modelUsage") or {})
            main = max(usage.items(), key=lambda kv: kv[1].get("outputTokens", 0),
                       default=(None, {}))
            out[idx + 1] = {
                "num_turns": resp.get("num_turns"),
                "stop_reason": resp.get("stop_reason"),
                "subtype": resp.get("subtype"),
                "max_output_tokens": main[1].get("maxOutputTokens"),
                "side_models": sorted(k for k in usage if k != main[0]),
            }
    return out


def yield_leg(run_dir: str) -> Dict[str, Any]:
    """Per-call delivery and cost for one leg, plus the leg's rollup."""
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
                "reason": "no desk/ transcripts in this leg",
                "per_call": [], "totals": None,
                "manual": manual_trajectory(run_dir)}

    by_call: Dict[int, str] = {}
    for name in sorted(os.listdir(desk_dir)):
        if not name.endswith(".md"):
            continue
        m = _CALL_NAME.match(name)
        if m:
            by_call[int(m.group(1))] = os.path.join(desk_dir, name)

    log_by_call = {e.get("call"): e for e in entries if isinstance(e, dict)}
    ledger_by_call = _read_ledger_calls(run_dir)

    per_call: List[Dict[str, Any]] = []
    price_rows: List[Tuple[int, int, int, float]] = []
    prev_prompt: Optional[str] = None
    for call in sorted(by_call):
        prompt, reply = split_transcript(by_call[call])
        got = delivered(reply)
        entry = log_by_call.get(call) or {}
        usage = entry.get("usage") or {}
        cc = usage.get("cache_creation_input_tokens")
        cr = usage.get("cache_read_input_tokens")
        ot = usage.get("output_tokens")
        usd = entry.get("cli_cost_usd")
        if all(isinstance(v, int) for v in (cc, cr, ot)) and isinstance(usd, (int, float)):
            price_rows.append((cc, cr, ot, usd))
        reply_tokens_est = got["reply_chars"] / CHARS_PER_OUTPUT_TOKEN_EST
        row: Dict[str, Any] = {
            "call": call,
            "transcript": os.path.basename(by_call[call]),
            "label": entry.get("label"),
            "step_idx": entry.get("step_idx"),
            "actions_at_call": entry.get("actions_at_call"),
            "usd": usd,
            "elapsed_s": (entry.get("elapsed_ms") / 1000.0
                          if isinstance(entry.get("elapsed_ms"), int) else None),
            "cache_creation_input_tokens": cc,
            "cache_read_input_tokens": cr,
            "output_tokens": ot,
            "prompt_chars": len(prompt),
            "prompt_identical_to_previous": (prev_prompt == prompt) if prev_prompt is not None else None,
            "delivered": got,
            "reply_tokens_est": reply_tokens_est,
            "unreplied_output_tokens_est": (ot - reply_tokens_est) if isinstance(ot, int) else None,
            "unreplied_output_share_est": ((ot - reply_tokens_est) / ot
                                           if isinstance(ot, int) and ot else None),
            "output_tokens_per_second": (ot / (entry["elapsed_ms"] / 1000.0)
                                         if isinstance(ot, int)
                                         and isinstance(entry.get("elapsed_ms"), int)
                                         and entry["elapsed_ms"] else None),
            "void": not got["has_required"],
        }
        row.update({"ledger_" + k: v for k, v in (ledger_by_call.get(call) or {}).items()})
        per_call.append(row)
        prev_prompt = prompt

    fit = price_fit(price_rows)
    return {"run": os.path.basename(run_dir), "calls": len(per_call),
            "per_call": per_call, "price_fit": fit,
            "manual": manual_trajectory(run_dir),
            "totals": _totals(run_dir, per_call, fit)}


def _totals(run_dir: str, per_call: List[Dict[str, Any]],
            fit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not per_call:
        return None
    costs = [c["usd"] for c in per_call if isinstance(c["usd"], (int, float))]
    void = [c for c in per_call if c["void"]]
    void_usd = sum(c["usd"] for c in void if isinstance(c["usd"], (int, float)))
    total_usd = sum(costs)
    out_tokens = sum(c["output_tokens"] for c in per_call
                     if isinstance(c["output_tokens"], int))
    in_tokens = sum((c["cache_creation_input_tokens"] or 0)
                    + (c["cache_read_input_tokens"] or 0) for c in per_call)
    out: Dict[str, Any] = {
        "calls": len(per_call),
        "usd": round(total_usd, 6),
        "usd_per_call": round(total_usd / len(per_call), 6),
        "void_calls": len(void),
        "void_call_numbers": [c["call"] for c in void],
        "void_usd": round(void_usd, 6),
        "void_share_of_spend": (void_usd / total_usd) if total_usd else None,
        "productive_calls": len(per_call) - len(void),
        # Two different questions, and conflating them is how sk48 reads as
        # three times dearer to theorise than it is.
        #   usd_per_productive_call -- the leg's WHOLE spend divided by the
        #     calls that moved the books.  What a unit of progress cost.
        #   mean_usd_of_productive_calls -- the mean bill of those calls alone.
        #     What theorising this game actually costs when it works.
        # On sk48 they are $10.15 and $2.69: the gap IS the defect.
        "usd_per_productive_call": (round((total_usd) / (len(per_call) - len(void)), 6)
                                    if len(per_call) > len(void) else None),
        "mean_usd_of_productive_calls": (
            round(sum(c["usd"] for c in per_call
                      if not c["void"] and isinstance(c["usd"], (int, float)))
                  / (len(per_call) - len(void)), 6)
            if len(per_call) > len(void) else None),
        "output_tokens": out_tokens,
        "input_tokens": in_tokens,
        "output_to_input_token_ratio": (out_tokens / in_tokens) if in_tokens else None,
        "repeated_prompts": [c["call"] for c in per_call
                             if c["prompt_identical_to_previous"]],
        "elapsed_s": round(sum(c["elapsed_s"] for c in per_call
                               if isinstance(c["elapsed_s"], (int, float))), 1),
    }
    if fit.get("ok"):
        rate = fit["usd_per_mtok"]["output"]
        out["usd_attributable_to_output"] = round(rate * out_tokens / 1e6, 6)
        out["output_share_of_bill"] = ((rate * out_tokens / 1e6) / total_usd
                                       if total_usd else None)

    shape = os.path.join(run_dir, "bill_shape.json")
    if os.path.exists(shape):
        with open(shape, encoding="utf-8") as fh:
            totals = (json.load(fh) or {}).get("totals") or {}
        actions = totals.get("actions_billed")
        out["actions_billed"] = actions
        out["usd_per_billed_action"] = totals.get("usd_per_billed_action")
        if isinstance(actions, int) and actions:
            productive = len(per_call) - len(void)
            out["actions_per_productive_call"] = actions / productive if productive else None
    return out


# ------------------------------------------------------------------ the CLI
def _fmt(v: Any, spec: str = "") -> str:
    if v is None:
        return "--"
    try:
        return format(v, spec)
    except (TypeError, ValueError):
        return str(v)


def render(report: Dict[str, Any]) -> str:
    lines: List[str] = ["== %s  (%d desk calls)" % (report["run"], report["calls"])]
    if not report["per_call"]:
        lines.append("   %s" % report.get("reason", "nothing to report"))
        return "\n".join(lines)
    lines.append("   %-3s %-7s %5s %6s %6s %9s %8s %7s  %s"
                 % ("#", "label", "step", "usd", "min", "out_tok", "reply_ch",
                    "same?", "blocks"))
    for c in report["per_call"]:
        lines.append("   %-3d %-7s %5s %6s %6s %9s %8d %7s  %s%s"
                     % (c["call"], c["label"] or "", _fmt(c["step_idx"]),
                        _fmt(c["usd"], "6.2f"),
                        _fmt((c["elapsed_s"] or 0) / 60.0, "6.1f"),
                        _fmt(c["output_tokens"], "9d"),
                        c["delivered"]["reply_chars"],
                        "SAME" if c["prompt_identical_to_previous"] else "",
                        "+".join(c["delivered"]["blocks_unique"]) or "(none)",
                        "   <- VOID: no THEORY" if c["void"] else ""))
    t = report["totals"] or {}
    lines.append("   -- spend $%s over %s calls; %s void ($%s = %s of spend)"
                 % (_fmt(t.get("usd"), ".2f"), t.get("calls"), t.get("void_calls"),
                    _fmt(t.get("void_usd"), ".2f"),
                    _fmt((t.get("void_share_of_spend") or 0) * 100, ".0f") + "%"))
    lines.append("   -- $%s per billed action over %s actions; %s actions per productive call"
                 % (_fmt(t.get("usd_per_billed_action"), ".3f"),
                    t.get("actions_billed"),
                    _fmt(t.get("actions_per_productive_call"), ".2f")))
    fit = report.get("price_fit") or {}
    if fit.get("ok"):
        r = fit["usd_per_mtok"]
        lines.append("   -- implied $/Mtok: cache_write %.2f, cache_read %.2f, output %.2f "
                     "(worst residual $%.4f = %.1f%% of the mean bill)"
                     % (r["cache_write"], r["cache_read"], r["output"],
                        fit["max_abs_residual_usd"],
                        100 * (fit.get("max_residual_share_of_mean_bill") or 0)))
        if fit.get("unidentified_terms"):
            lines.append("      (%s came out negative -- not identified by these "
                         "calls; nonzero in %s of them)"
                         % (", ".join(fit["unidentified_terms"]),
                            ", ".join("%s=%d" % (k, fit["calls_with_nonzero_tokens"][k])
                                      for k in fit["unidentified_terms"])))
        lines.append("   -- output tokens carry %s of the leg's bill"
                     % (_fmt((t.get("output_share_of_bill") or 0) * 100, ".0f") + "%"))
    else:
        lines.append("   -- price fit unavailable: %s" % fit.get("reason"))
    m = report.get("manual") or {}
    if m.get("after_theorize_theory_chars"):
        lines.append("   -- manual after each theorize: %s (carried %s)"
                     % (m["after_theorize_theory_chars"], m.get("carried_theory_chars")))
        lines.append("   -- ended %s than the seed it carried (%+d chars); "
                     "%d trailing writes changed the size not at all"
                     % ("SHORTER" if m.get("ended_shorter_than_carried") else "LONGER",
                        m.get("final_vs_carried_chars") or 0,
                        m.get("frozen_tail_writes") or 0))
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_dir", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    reports = [yield_leg(d) for d in args.run_dir]
    if args.json:
        json.dump(reports, sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for r in reports:
            print(render(r))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
