"""C1 -- mutation table for V25's code, patched **inside a named function**.

Supersedes V21's `a10_mutation_test.py` for anything touching the token check.
Not because a10 was wrong, but because of what it did when the source moved
under it, which is the finding this file exists to prevent recurring:

V21 taught a10 to notice a patch whose text no longer matches (`STALE`), after
one such mutation spent a whole pass testing nothing while printing a blank row.
Running the same a10 against V25's source turned up the harder half of the same
defect. Mutation `P: token-level floor comparison weakened to >=` patches the
literal line

    "        if rate > tolerance and rate > floor + 1e-9:"

which V25 moved out of `_token_hits_within` -- but an identical line now exists
inside `token_fire_probability`, the *null* enumeration. So the patch applies,
cleanly, to the wrong function; a10 reports `P ... 0/20` in a perfectly ordinary
looking row; and the thing the row names was never mutated at all.

**A patch that does not apply is visible. A patch that applies somewhere else is
not.** Text substitution has no notion of location, so this harness takes the
function name with the patch and refuses to apply it outside that function's
source span.

Run serially -- never alongside `pytest exam/tests`. V21 lost an afternoon to a
byte-identical-spec failure that was two processes writing one `.verify/`.
"""
import os
import re
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)

SRC = os.path.join(REPO, "exam", "leakage.py")

#: (label, function, [(before, after), ...])
MUTATIONS = [
    ("V1: fire probability always 0 (every red looks unimpeachable)",
     "token_fire_probability",
     [("    return hits / total", "    return 0.0 * hits / max(total, 1)")]),
    ("V2: fire probability always 1 (every red looks like noise)",
     "token_fire_probability",
     [("    return hits / total", "    return 1.0")]),
    ("V3: null ignores the tolerance, so p counts every improvement",
     "token_fire_probability",
     [("        if rate > tolerance and rate > floor + 1e-9:",
       "        if rate > floor + 1e-9:")]),
    ("V4: null ignores the floor",
     "token_fire_probability",
     [("        if rate > tolerance and rate > floor + 1e-9:",
       "        if rate > tolerance:")]),
    ("V5: k=n and k=0 treated as testable",
     "token_fire_probability",
     [("    if n == 0 or not 0 < k < n:", "    if n == 0:")]),
    ("V6: complement no longer folded -- a cut counted twice",
     "_partition_key",
     [("    return min(tuple(sorted(held)),\n"
       "               tuple(sorted(universe - held)))",
       "    return tuple(sorted(held))")]),
    ("V7: familywise reduced to the single worst cut",
     "_token_hits_within",
     [("    survives = 1.0\n"
       "    for p_fire in cuts.values():\n"
       "        survives *= (1.0 - p_fire)\n"
       "    familywise = 1.0 - survives",
       "    familywise = max(cuts.values()) if cuts else 0.0")]),
    ("V8: multiplicity counted per token instead of per cut",
     "_token_hits_within",
     [("    cuts: Dict[Tuple[str, ...], float] = {}\n"
       "    for _token, _holders, held, _rate, p_fire in scored:\n"
       "        cuts.setdefault(_partition_key(held, universe), p_fire)",
       "    cuts: Dict[Tuple[str, ...], float] = {}\n"
       "    for _i, (_token, _holders, held, _rate, p_fire) "
       "in enumerate(scored):\n"
       "        cuts[(str(_i),)] = p_fire")]),
    ("V9: the correction becomes a suppressor (the ruling reversed)",
     "_token_hits_within",
     [("        findings.append({\n"
       "            \"field\": field_name,\n"
       "            \"token\": token,",
       "        if familywise >= ALPHA:\n"
       "            continue\n"
       "        findings.append({\n"
       "            \"field\": field_name,\n"
       "            \"token\": token,")]),
    ("V10: weak_evidence always False",
     "_token_hits_within",
     [("            \"weak_evidence\": familywise >= ALPHA,",
       "            \"weak_evidence\": False,")]),
    ("V11: p_fire dropped from the finding",
     "_token_hits_within",
     [("            \"p_fire\": round(p_fire, 6),\n"
       "            \"p_fire_familywise\": round(familywise, 6),\n"
       "            \"cuts_tried\": len(cuts),", "")]),
    ("V12: the single-holder guard removed (what V25 was asked to do)",
     "_token_hits_within",
     [("        if len(holders) < 2 or len(holders) == n:",
       "        if len(holders) == n:")]),
    ("V13: single-holder coverage miscounts (reports zero gap)",
     "single_holder_coverage",
     [("    singles = sorted(t for t, h in carriers.items() if len(h) == 1)",
       "    singles = []")]),
    ("V14: the coverage record never reaches the report",
     "_metadata_hits_within",
     [("        if coverage[\"single_holder\"]:", "        if False:")]),
    ("V15: token declines silently dropped instead of recorded",
     "_metadata_hits_within",
     [("        declined.extend(token_declined)", "        pass")]),
]

TESTS = ["exam/tests/test_leakage_tokens.py",
         "exam/tests/test_leakage_multiplicity.py"]


def function_span(src, name):
    """The source span of `def <name>(`, up to the next top-level definition."""
    m = re.search(r"^def %s\(" % re.escape(name), src, re.M)
    if not m:
        raise KeyError("no function %r in %s" % (name, SRC))
    start = m.start()
    nxt = re.search(r"^(def |#: |[A-Z_]+ = )", src[m.end():], re.M)
    end = m.end() + nxt.start() if nxt else len(src)
    return start, end


def apply_mutation(src, func, pairs):
    """Substitute only within `func`'s span. Refuse anything else."""
    start, end = function_span(src, func)
    body = src[start:end]
    for before, after in pairs:
        if before not in body:
            elsewhere = before in src
            return None, ("PATCH DID NOT APPLY inside %s()%s" % (
                func, " -- but it DOES match elsewhere in the file, which is "
                      "exactly the retarget this harness exists to refuse"
                      if elsewhere else ""))
        if body.count(before) > 1:
            return None, "PATCH IS AMBIGUOUS inside %s() (%d matches)" % (
                func, body.count(before))
        body = body.replace(before, after, 1)
    return src[:start] + body + src[end:], None


def run_tests():
    """Run the pinning tests in a FRESH interpreter; return the names that failed.

    Subprocess, not `pytest.main`, and the difference is the whole harness. The
    first version of this file ran the tests in-process and reported all fifteen
    mutations unpinned -- because `exam.leakage` was already in `sys.modules`,
    so rewriting the file on disk changed nothing the tests could see. Fifteen
    rows of "caught by 0 tests", every one of them false, and the table looked
    exactly like a table reporting a catastrophe. A harness that cannot tell
    "nothing caught this" from "nothing was mutated" is the defect it is meant
    to detect, wearing the detector's clothes.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header",
         "-p", "no:cacheprovider", "--tb=no", "-rf"]
        + [os.path.join(REPO, t) for t in TESTS],
        cwd=REPO, capture_output=True, text=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1"))
    failed = sorted(set(re.findall(r"^FAILED .*::(\w+)", proc.stdout, re.M)))
    if proc.returncode != 0 and not failed:
        failed = sorted(set(re.findall(r"^ERROR .*::(\w+)", proc.stdout, re.M)))             or ["<collection error or crash>"]
    return failed, proc.returncode


def main():
    original = open(SRC, encoding="utf-8").read()
    baseline_failed, code = run_tests()
    if baseline_failed:
        print("BASELINE IS RED, mutation results would be meaningless: %s"
              % baseline_failed)
        return 2
    print("baseline: all pinning tests pass\n")

    rows, stale, unpinned = [], [], []
    try:
        for label, func, pairs in MUTATIONS:
            mutated, err = apply_mutation(original, func, pairs)
            if err:
                rows.append((label, None, err))
                stale.append(label.split(":")[0])
                continue
            open(SRC, "w", encoding="utf-8").write(mutated)
            try:
                failed, _code = run_tests()
            except Exception:
                traceback.print_exc()
                failed = ["<crashed>"]
            finally:
                open(SRC, "w", encoding="utf-8").write(original)
            rows.append((label, failed, None))
            if not failed:
                unpinned.append(label.split(":")[0])
    finally:
        open(SRC, "w", encoding="utf-8").write(original)

    print("\n" + "=" * 78)
    print("== mutation table (function-scoped)")
    print("=" * 78)
    for label, failed, err in rows:
        if err:
            print("  %-62s %s" % (label[:62], err))
        else:
            print("  %-62s caught by %d test(s)%s"
                  % (label[:62], len(failed),
                     "" if failed else "   <-- UNPINNED"))
            for name in sorted(failed)[:3]:
                print("        %s" % name)
    print()
    if stale:
        print("STALE  (patch did not apply where it claims to): %s"
              % ", ".join(stale))
    if unpinned:
        print("UNPINNED (no test caught these): %s" % ", ".join(unpinned))
    if not stale and not unpinned:
        print("OK: %d mutations, every one caught by at least one test."
              % len(MUTATIONS))
    return 1 if (stale or unpinned) else 0


if __name__ == "__main__":
    raise SystemExit(main())
