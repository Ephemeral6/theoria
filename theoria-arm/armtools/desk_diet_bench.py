"""Before and after, offline: the same campaign run at each diet setting.

No model call, no network, no key, no quota.  The desk is a scripted double and
the world is synthetic, which is the only honest way to compare prompt
economics without spending: the two arms must differ **only** in how the same
work is encoded, and a live desk cannot be held to that.

What is controlled, and why it matters
--------------------------------------
Every arm plays the same rounds against the same growing `FrameStore` and the
same engine reports, and makes the **same semantic change to the manual each
round** -- one rule's worth of text, appended in the same place.  `full` says
that change by retyping the whole manual, because that is what today's
`OUTPUT_CONTRACT` demands ("the whole of theory.dsl, not a diff").  `patch` says
it as one anchored op.  So the manual after round N is byte-identical across
arms, and the bench asserts that before it reports anything -- otherwise the
comparison would be measuring two different theories, and the cheaper one would
be cheaper for the wrong reason.

What the numbers are, and what they are not
-------------------------------------------
Prompt chars and reply chars are **measured** here -- they are what the real
`inner.theorize.build_prompt` produced for the real beat.

Dollars are **estimated**, and the estimate is derived from this arm's own
archive rather than from a price list: `armtools.prompt_census.fit_tokens`
converts chars to billed tokens off the archived legs' `usage` blocks, and the
per-Mtok rates come from regressing `cli_cost_usd` on those same blocks.  Both
fits are reported with their r2 next to every dollar figure.  If the archive is
not there, this refuses to print a dollar rather than reaching for a constant --
a benchmark that invents its own prices is a benchmark that proves whatever it
was written to prove.

The load-bearing caveat, stated in the artefact and not only here
----------------------------------------------------------------
The output-side saving is **conditional**.  It is what happens *if* a live desk
answers the patch contract with a patch.  This bench cannot establish that it
will; only a live leg can, and the arm is offline.  What this bench does
establish is the input-side saving (fully measured), the mechanical correctness
of the patch path (the manuals match byte for byte), and the *size* of the prize
if the behavioural assumption holds.  The report carries
`output_saving_is_conditional: true` for exactly this reason.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import prompt_census                    # noqa: E402
from inner import deskdiet, theorize                  # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402
from world.frames import FrameStore, Step             # noqa: E402

ARMS = ("full", "evidence", "patch", "diet")

#: The fixture's dimensions, taken from the census of the live legs rather than
#: chosen. A bench whose synthetic manual is 1 500 chars measures a world where
#: the prompt is 73% boilerplate and the patch contract costs more than it
#: saves -- which is true of that world and of no leg this arm has ever run.
#:
#:   MANUAL_START_CHARS  r3's manual at its first desk call (`census`, section
#:                       `manual`, call 1): 32 958 chars.
#:   ROUND_GROWTH_CHARS  r3's manual grew 32 958 -> 51 253 over its seven later
#:                       calls: +2 613 chars per round.
#:
#: Both are overridable on the command line, and the report records the values
#: it ran at, because a benchmark whose fixture is invisible is a benchmark that
#: cannot be argued with.
MANUAL_START_CHARS = 32958
ROUND_GROWTH_CHARS = 2613

_FILLER = ("# %s -- carried pending: the candidate stream offers obj%d as a\n"
           "# mover with coverage %d/%d, which is below the bar constraint 2\n"
           "# sets, so it stays out of `rules:` and is recorded here instead.\n")


def _comment_block(tag: str, chars: int, salt: int = 0) -> str:
    """A block of valid manual text of about `chars` characters.

    Comment lines, because the bench measures the ENCODING of a change and not
    its content: a generated rule that failed to compile would send every arm
    into the repair loop and the bench would be measuring that instead.
    """
    out: List[str] = []
    size = 0
    i = 0
    while size < chars:
        piece = _FILLER % ("%s-%03d" % (tag, i), salt + i, (i % 7) + 1, (i % 7) + 4)
        out.append(piece)
        size += len(piece)
        i += 1
    return "".join(out)


def _round_text(i: int, growth: int = ROUND_GROWTH_CHARS) -> str:
    return "\n" + _comment_block("round%02d" % i, growth, salt=100 * (i + 1))


def _grid(n, mark):
    g = [[0] * n for _ in range(n)]
    g[mark[0]][mark[1]] = 6
    return g


def _engines(round_idx: int) -> Dict[str, Any]:
    """Engine reports that mostly repeat, which is what the archive shows.

    `mdl_segmenter` and `zero_space` are byte-identical every round; only
    `cegis_miner` moves. That is the shape the delta knob is aimed at, and it is
    modelled rather than assumed: in every archived leg the engine block sat at
    its 14 000-char truncation cap on every single call.
    """
    return {
        "window": {"box": [0, 7, 0, 7]},
        "mdl_segmenter": {"objects": [{"id": "obj0", "color": 6,
                                       "cells": [[r, 0] for r in range(8)],
                                       "compress": 2125}]},
        "zero_space": {"invariants": ["count(obj0) = 1", "sum(color) = 6"]},
        "cegis_miner": {"rules": [{"id": "r%02d" % i,
                                   "guard": "act=key(%d) and free(above(obj0))" % (i % 4),
                                   "coverage": "%d/%d" % (i + 1, i + 3)}
                                  for i in range(round_idx + 1)]},
    }


class _ScriptedDesk:
    """Answers each prompt in the way the arm's contract asks for.

    It reads the prompt to decide, exactly as a live desk would: if the patch
    contract is present it patches, otherwise it sends the whole book. So the
    bench cannot accidentally credit the patch arm for a saving the contract
    never asked for.
    """

    def __init__(self, target_theory_at_round, base_theory, growth):
        self.target = target_theory_at_round
        self.base = base_theory
        self.growth = growth
        self.round = 0
        self.prompts: List[str] = []
        self.replies: List[str] = []

    def call(self, prompt, *, beat, step_idx=None, label=None):
        self.prompts.append(prompt)
        patching = deskdiet.PATCH_CONTRACT.splitlines()[1] in prompt
        new_text = _round_text(self.round, self.growth)
        if patching:
            anchor = self.target(self.round - 1) if self.round else self.base
            tail = _unique_tail(anchor)
            reply = ("=== THEORY-PATCH ===\n```json\n%s\n```\n\n"
                     "=== PLAYBOOK ===\n```\n%s```\n\n=== LOG ===\n```json\n%s\n```\n"
                     % (json.dumps([{"op": "insert_after", "find": tail,
                                     "with": new_text}]),
                        _playbook(self.round), _log(self.round)))
        else:
            reply = ("=== THEORY ===\n```\n%s\n```\n\n=== PLAYBOOK ===\n```\n%s"
                     "```\n\n=== LOG ===\n```json\n%s\n```\n"
                     % (self.target(self.round), _playbook(self.round),
                        _log(self.round)))
        self.replies.append(reply)
        return reply


def _unique_tail(text: str, *, max_lines: int = 12) -> str:
    """The shortest whole-line suffix of `text` that occurs exactly once.

    This is what the patch contract tells the desk to do -- "quote more
    surrounding text so it occurs once" -- and the scripted desk does it rather
    than being handed a magic anchor, so the bench measures a desk that follows
    the contract and not a fixture that was built to pass.

    The first draft of this bench took a fixed 120-char tail and every round was
    refused as ambiguous, 23 matches deep, because the filler repeats. That was
    the guard working; it is left recorded here because it is the only reason
    anyone would believe the guard fires outside its own unit test.
    """
    lines = text.splitlines(keepends=True)
    for n in range(1, min(max_lines, len(lines)) + 1):
        tail = "".join(lines[-n:])
        if text.count(tail) == 1:
            return tail
    raise RuntimeError("no unique whole-line tail within %d lines" % max_lines)


def _playbook(i: int) -> str:
    return "# ordering, revision %d\n" % i + "".join(
        "# try key(%d) before key(%d) when the mover is blocked\n" % (a, a + 1)
        for a in range(i + 1))


def _log(i: int) -> str:
    return json.dumps([{"id": "R-%02d" % i, "subject": "obj0_step",
                        "verdict": "probe-pending",
                        "why": "coverage %d/%d is below the bar" % (i + 1, i + 3)}])


# ----------------------------------------------------------------- one arm
def run_arm(spec: str, rounds: int, workdir: str, *,
            manual_start: int = MANUAL_START_CHARS,
            growth: int = ROUND_GROWTH_CHARS) -> Dict[str, Any]:
    diet = deskdiet.DeskDiet.parse(spec)
    root = os.path.join(workdir, spec)
    os.makedirs(root, exist_ok=True)
    base = WORKED_EXAMPLE + "\n" + _comment_block(
        "carried", max(0, manual_start - len(WORKED_EXAMPLE)))
    books = Books(os.path.join(root, "books"))
    books.write(theory=base, playbook="# nothing defensible yet\n")

    cands = os.path.join(root, "candidates.jsonl")
    with open(cands, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('{"kind": "object", "status": "candidate"}\n' * 12)

    targets: List[str] = []

    def target(i: int) -> str:
        return targets[i]

    text = base
    for i in range(rounds):
        text = text + _round_text(i, growth)
        targets.append(text)

    desk = _ScriptedDesk(target, base, growth)
    store = FrameStore()
    store.add(Step(0, "RESET", [_grid(8, (0, 0))], state="NOT_FINISHED"))

    calls: List[Dict[str, Any]] = []
    for i in range(rounds):
        desk.round = i
        for k in range(4):                       # four commands between beats
            t = len(store.steps)
            store.add(Step(t, "ACTION%d" % (1 + k), [_grid(8, (t % 8, k))],
                           state="NOT_FINISHED"))
        n_before = len(desk.prompts)
        result = theorize.run(desk, books, store, cands,
                              engines=_engines(i), diet=diet)
        for j in range(n_before, len(desk.prompts)):
            cen = prompt_census.census(desk.prompts[j])
            calls.append({
                "round": i, "attempt": j - n_before + 1,
                "prompt_chars": len(desk.prompts[j]),
                "reply_chars": len(desk.replies[j]),
                "by_kind": {k: v["chars"] for k, v in cen["by_kind"].items()},
                "sections": {s["section"]: s["chars"] for s in cen["sections"]},
            })
        if not result["ok"]:
            raise RuntimeError("%s: round %d did not compile: %r"
                               % (spec, i, result["rounds"][-1].get("compile_errors")))

    return {"arm": spec, "diet": diet.as_json(), "rounds": rounds,
            "calls": calls,
            "final_theory": books.theory,
            "prompt_chars": sum(c["prompt_chars"] for c in calls),
            "reply_chars": sum(c["reply_chars"] for c in calls),
            "model_calls": len(calls)}


# --------------------------------------------------------------- the prices
def archive_rates(runs_dir: str, *, model: str = "claude-opus-5") -> Dict[str, Any]:
    """Chars-per-token and dollars-per-Mtok, fitted from this arm's own legs.

    Two fits:

      chars -> billed input tokens, from `cache_creation_input_tokens`, by
        WITHIN-leg differences (`fit_tokens_paired`) so each leg's fixed CLI
        overhead cancels instead of being explained by the slope;
      (cache_creation, output) tokens -> `cli_cost_usd`, least squares with r2.

    Both are restricted to one model.  Mixing models would fit an average
    price nobody was ever charged, and the archive does carry more than one.

    Not a price list.  A price list would be a claim about a vendor; this is a
    claim about what this arm was actually charged, which is the only quantity
    a before/after can honestly be denominated in.
    """
    by_leg: Dict[str, List[Tuple[int, int]]] = {}
    rows: List[Tuple[float, float, float]] = []
    legs = 0
    models_seen: Dict[str, int] = {}
    for log_path in sorted(glob.glob(os.path.join(runs_dir, "*", "desk_log.json"))):
        run_dir = os.path.dirname(log_path)
        name = os.path.basename(run_dir)
        leg = prompt_census.census_leg(run_dir)
        with open(log_path, encoding="utf-8") as fh:
            try:
                entries = json.load(fh)
            except json.JSONDecodeError:
                entries = []
        if not isinstance(entries, list):
            entries = []
        by_call = {e.get("call"): e for e in entries if isinstance(e, dict)}
        for entry in entries:
            models_seen[str((entry or {}).get("model"))] = \
                models_seen.get(str((entry or {}).get("model")), 0) + 1

        if leg["calls"]:
            legs += 1
            points = []
            for call in leg["per_call"]:
                cc = call["cache_creation_input_tokens"]
                entry = by_call.get(call["call"]) or {}
                if entry.get("model") == model and isinstance(cc, int) and cc > 0:
                    points.append((call["chars_in"], cc))
            if len(points) >= 2:
                by_leg[name] = points

        for entry in entries:
            if (entry or {}).get("model") != model:
                continue
            usage = (entry or {}).get("usage") or {}
            cost = (entry or {}).get("cli_cost_usd")
            cc = usage.get("cache_creation_input_tokens")
            out = usage.get("output_tokens")
            if isinstance(cost, (int, float)) and isinstance(cc, int) \
                    and isinstance(out, int):
                rows.append((float(cc), float(out), float(cost)))

    token_fit = prompt_census.fit_tokens_paired(by_leg)
    if token_fit.get("ok"):
        # The per-call fixed term: what the CLI bills for its own system prompt
        # and tool table, which no diet can touch. Recovered per leg from the
        # paired slope and then taken as a median, because it genuinely differs
        # between legs (2 976 on r3, 2 180 on l1) and one leg's value is not the
        # arm's.
        slope = token_fit["slope_tokens_per_char"]
        fixed_by_leg = {}
        for name, points in sorted(by_leg.items()):
            residuals = sorted(t - slope * c for c, t in points)
            m = len(residuals)
            fixed_by_leg[name] = (residuals[m // 2] if m % 2
                                  else 0.5 * (residuals[m // 2 - 1] + residuals[m // 2]))
        values = sorted(fixed_by_leg.values())
        k = len(values)
        token_fit["fixed_tokens_per_call"] = (
            values[k // 2] if k % 2 else 0.5 * (values[k // 2 - 1] + values[k // 2]))
        token_fit["fixed_tokens_by_leg"] = {n: round(v)
                                            for n, v in fixed_by_leg.items()}
    price = _price_fit(rows)
    return {"model": model, "models_in_archive": models_seen,
            "legs_with_desk_transcripts": legs,
            "legs_used_for_token_fit": sorted(by_leg),
            "priced_calls": len(rows),
            "token_fit": token_fit, "price_fit": price,
            "usable": bool(token_fit.get("ok") and price.get("ok"))}


def _price_fit(rows: List[Tuple[float, float, float]]) -> Dict[str, Any]:
    """cost ~ a*cache_creation + b*output, by normal equations.

    Two unknowns and no intercept, so it needs at least two calls whose token
    mix differs. Solved by hand rather than via numpy so this module has no
    dependency the rest of the arm does not already have.
    """
    if len(rows) < 3:
        return {"ok": False, "reason": "need >=3 priced calls", "n": len(rows)}
    sxx = sum(r[0] * r[0] for r in rows)
    sxy = sum(r[0] * r[1] for r in rows)
    syy = sum(r[1] * r[1] for r in rows)
    sxz = sum(r[0] * r[2] for r in rows)
    syz = sum(r[1] * r[2] for r in rows)
    det = sxx * syy - sxy * sxy
    if abs(det) < 1e-9:
        return {"ok": False, "reason": "token mix is degenerate", "n": len(rows)}
    a = (syy * sxz - sxy * syz) / det
    b = (sxx * syz - sxy * sxz) / det
    zs = [r[2] for r in rows]
    mz = sum(zs) / len(zs)
    ss_tot = sum((z - mz) ** 2 for z in zs)
    ss_res = sum((r[2] - (a * r[0] + b * r[1])) ** 2 for r in rows)
    return {"ok": True, "n": len(rows),
            "usd_per_mtok_cache_creation": a * 1e6,
            "usd_per_mtok_output": b * 1e6,
            "r2": (1.0 - ss_res / ss_tot) if ss_tot else None}


def price_arm(arm: Dict[str, Any], rates: Dict[str, Any]) -> Dict[str, Any]:
    if not rates.get("usable"):
        return {"priced": False,
                "reason": "no usable fit from the archive; refusing to invent "
                          "a price"}
    slope = rates["token_fit"]["slope_tokens_per_char"]
    # The CLI's own system prompt and tool table, billed once per call and
    # identical in every arm. Carried explicitly rather than dropped, because it
    # is the term that makes a per-call saving smaller than a per-char one, and
    # an arm that quietly omitted it would overstate every saving below.
    fixed = rates["token_fit"]["fixed_tokens_per_call"]
    a = rates["price_fit"]["usd_per_mtok_cache_creation"] / 1e6
    b = rates["price_fit"]["usd_per_mtok_output"] / 1e6
    in_tokens = sum(slope * c["prompt_chars"] + fixed for c in arm["calls"])
    out_tokens = sum(slope * c["reply_chars"] for c in arm["calls"])
    return {"priced": True,
            "est_input_tokens": int(round(in_tokens)),
            "est_output_tokens": int(round(out_tokens)),
            "est_input_usd": round(a * in_tokens, 4),
            "est_output_usd": round(b * out_tokens, 4),
            "est_total_usd": round(a * in_tokens + b * out_tokens, 4)}


class ArmsDisagree(RuntimeError):
    """The bench's control failed: two arms ended with different manuals.

    This is not a tolerable warning. Every dollar figure the bench prints is a
    comparison of two encodings of the same work; if the work differs, the
    cheaper arm may simply be the one that wrote less theory, and the whole
    report is void. So it raises rather than annotating.
    """


def arms_disagree(theories: Dict[str, str], baseline_key: str) -> List[str]:
    baseline = theories[baseline_key]
    return sorted(k for k, v in theories.items() if v != baseline)


# ------------------------------------------------------------------ the run
def bench(rounds: int = 6, runs_dir: Optional[str] = None,
          arms: Tuple[str, ...] = ARMS,
          manual_start: int = MANUAL_START_CHARS,
          growth: int = ROUND_GROWTH_CHARS) -> Dict[str, Any]:
    runs_dir = runs_dir or os.path.join(ARM, "runs")
    rates = archive_rates(runs_dir)
    workdir = tempfile.mkdtemp(prefix="desk-diet-bench-")
    try:
        results = {spec: run_arm(spec, rounds, workdir,
                                 manual_start=manual_start, growth=growth)
                   for spec in arms}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    # The control: every arm must have ended with the SAME manual. Without this
    # the cheap arm might simply be the one that wrote less theory.
    theories = {spec: r["final_theory"] for spec, r in results.items()}
    baseline = theories[arms[0]]
    mismatched = arms_disagree(theories, arms[0])
    if mismatched:
        raise ArmsDisagree("arms ended with different manuals: %s" % mismatched)

    base = results[arms[0]]
    report: Dict[str, Any] = {
        "rounds": rounds,
        "fixture": {"manual_start_chars": manual_start,
                    "round_growth_chars": growth,
                    "calibrated_from":
                        "runs/20260731T1430Z-A3-level2-carried-r3, census "
                        "section `manual`: 32958 chars at call 1, +2613/call "
                        "over its seven later calls"},
        "arms": [],
        "final_theory_chars": len(baseline),
        "final_theory_sha_prefix": _sha(baseline)[:16],
        "all_arms_agree_on_the_manual": True,
        "rates": rates,
        "output_saving_is_conditional": True,
        "conditional_note":
            "The output-side figure is what happens IF a live desk answers the "
            "patch contract with a patch. This bench cannot establish that it "
            "will; it establishes the input-side saving, that the patch path "
            "reproduces the manual byte for byte, and the size of the prize.",
    }
    for spec in arms:
        arm = results[spec]
        priced = price_arm(arm, rates)
        row: Dict[str, Any] = {
            "arm": spec, "diet": arm["diet"],
            "model_calls": arm["model_calls"],
            "prompt_chars": arm["prompt_chars"],
            "reply_chars": arm["reply_chars"],
            "prompt_chars_vs_full": arm["prompt_chars"] - base["prompt_chars"],
            "reply_chars_vs_full": arm["reply_chars"] - base["reply_chars"],
            "by_kind_chars": {k: sum(c["by_kind"][k] for c in arm["calls"])
                              for k in prompt_census.KINDS},
            "per_call_prompt_chars": [c["prompt_chars"] for c in arm["calls"]],
            "per_call_reply_chars": [c["reply_chars"] for c in arm["calls"]],
        }
        row.update(priced)
        if priced.get("priced") and spec != arms[0]:
            base_priced = price_arm(base, rates)
            row["est_total_usd_vs_full"] = round(
                priced["est_total_usd"] - base_priced["est_total_usd"], 4)
            row["est_saving_pct"] = round(
                100.0 * (base_priced["est_total_usd"] - priced["est_total_usd"])
                / base_priced["est_total_usd"], 2)
        report["arms"].append(row)
    return report


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def format_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("desk-diet bench -- %d rounds, offline, scripted desk"
                 % report["rounds"])
    rates = report["rates"]
    if rates.get("usable"):
        tf, pf = rates["token_fit"], rates["price_fit"]
        lines.append("rates fitted from %d archived %s desk calls in %d legs:"
                     % (pf["n"], rates["model"],
                        rates["legs_with_desk_transcripts"]))
        lines.append("  %.4f chars/token (IQR %.4f-%.4f) from %d within-leg "
                     "pairs, +%d fixed tokens/call"
                     % (tf["chars_per_token"], tf["chars_per_token_iqr"][0],
                        tf["chars_per_token_iqr"][1], tf["pairs"],
                        round(tf["fixed_tokens_per_call"])))
        lines.append("  $%.2f/Mtok cache-creation, $%.2f/Mtok output, r2=%.5f"
                     % (pf["usd_per_mtok_cache_creation"],
                        pf["usd_per_mtok_output"], pf["r2"]))
    else:
        lines.append("rates: UNAVAILABLE -- no dollar figures will be printed")
    lines.append("all arms ended with the same manual: %s (%d chars, sha %s)"
                 % (report["all_arms_agree_on_the_manual"],
                    report["final_theory_chars"],
                    report["final_theory_sha_prefix"]))
    lines.append("")
    lines.append("  arm       calls   prompt_ch    reply_ch   est_in$  est_out$   est_$   vs full")
    for row in report["arms"]:
        lines.append("  %-9s %5d  %10d  %10d  %8s  %8s  %6s  %8s"
                     % (row["arm"], row["model_calls"], row["prompt_chars"],
                        row["reply_chars"],
                        ("%.3f" % row["est_input_usd"]) if row.get("priced") else "-",
                        ("%.3f" % row["est_output_usd"]) if row.get("priced") else "-",
                        ("%.3f" % row["est_total_usd"]) if row.get("priced") else "-",
                        ("%+.1f%%" % -row["est_saving_pct"])
                        if row.get("est_saving_pct") is not None else "baseline"))
    lines.append("")
    lines.append("prompt composition (chars over the whole campaign):")
    lines.append("  arm        boilerplate    evidence       books    feedback")
    for row in report["arms"]:
        k = row["by_kind_chars"]
        lines.append("  %-9s %12d %11d %11d %11d"
                     % (row["arm"], k["boilerplate"], k["evidence"], k["books"],
                        k["feedback"]))
    lines.append("")
    lines.append("NOTE: the output-side saving is CONDITIONAL. "
                 + report["conditional_note"])
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--manual-start", type=int, default=MANUAL_START_CHARS,
                    help="chars in the carried manual at round 0 (default is "
                         "r3's, measured)")
    ap.add_argument("--growth", type=int, default=ROUND_GROWTH_CHARS,
                    help="chars of new theory per round (default is r3's, "
                         "measured)")
    ap.add_argument("--runs", default=None)
    ap.add_argument("--out", default=None, help="write the JSON report here")
    ap.add_argument("--json", dest="as_json", action="store_true")
    args = ap.parse_args(argv)

    report = bench(rounds=args.rounds, runs_dir=args.runs,
                   manual_start=args.manual_start, growth=args.growth)
    if args.out:
        payload = {k: v for k, v in report.items()}
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=1, sort_keys=True)
            fh.write("\n")
    print(json.dumps(report, indent=1, sort_keys=True) if args.as_json
          else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
