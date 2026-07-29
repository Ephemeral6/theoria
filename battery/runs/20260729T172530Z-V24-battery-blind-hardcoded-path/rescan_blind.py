"""Re-run the V9 blinding and re-perform the scan that certified it.

V24 clause 2: "重跑一次致盲流程并确认产物与既有结论一致".  The blinded trees were
never committed and no manifest recorded a digest of them -- the V9 MANIFEST's 24
entries do not include `make_blind.py`, let alone its output -- so there is no
byte comparison to make against 2026-07-29.  What there is, is a set of *recorded
claims about the material*, and those are checkable.

Two scans, because the recorded conclusion is really two claims about two
different objects, and running one scan over both is how the first draft of this
file produced a false positive:

  **Scan A, the blinded tree** -- what the six attackers were handed.  It must
  not contain the vocabulary that only exists after the attacks: the `unsound(`
  defence helper, the defence names, the summariser's `V9-P*` predictions, tier
  knowledge, or the prose register.  BLINDING.md §3.8 and REPORT.md §9(d) record
  these as zero-hit.

  **Scan B, the attackers' submissions** -- `attacks/a1.py`..`a6.py`.  REPORT.md
  §9(d) records that the 118 constructed `Run`s are uniformly `arm="attacker"`,
  `source="v9"`, with no adapter name, `game_id`, `campaign`, `pile` or `model`.
  That is a claim about the *values the attackers wrote*, not about the field
  names -- `model.py` necessarily exposes `campaign: Optional[str]`, because it
  is the data model, and an attacker who cannot see the fields cannot construct
  a Run at all.

  BLINDING.md §3.7 is the positive control: K2's `thin()` string contains
  `39960` and "3 adversarial gaps" verbatim, it is not on the NEUTRALISE list,
  and it reached attacker a5.  A rebuild *missing* the registered leak is not
  the tree the attackers saw either, so the tree is pinned from both sides.

Also performs the follow-up BLINDING.md:77 asked the next round to do: sweep the
surviving string literals by "does it contain a number" rather than by
recollection, since the K2 leak was a datum embedded in a defence criterion.

Run from the repo root:

    python battery/runs/<this-dir>/rescan_blind.py

Exit 0 iff the rebuild at the pinned ref reproduces every recorded claim.
"""
import ast
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from battery.audit.v9 import make_blind as mb   # noqa: E402

# The branch tip the old hardcoded SRC path resolved to.  Kept so the report can
# quantify what the drift would have leaked.
WORKTREE_HEAD = "0d586b6f99615fd87375d14441e0cc290fed8086"

ATTACKS = os.path.join(ROOT, "battery", "audit", "v9", "attacks")

# Scan A -- must not appear in the blinded tree.  Each of these exists only in
# material written after the attacks, or in material never given to attackers.
TREE_FORBIDDEN = {
    r"unsound\(": "the defence helper, added by 520dc5dd after the attacks",
    r"\bV9-P\d": "the summariser's directional predictions (PREREG_V9 §4)",
    r"\bD[123]\b": "the defence names, written after the attacks",
    r"main table": "tier knowledge -- which metrics are load-bearing",
    r"reference layer": "tier knowledge -- which metrics are load-bearing",
    r"gaming\.py|GAMING_REGISTER": "the prose how-to-game / defence register",
    r"how_to_game": "the prose how-to-game / defence register",
    r"a0-spike|bare_cc": "repo proper nouns",
}

# Scan B -- must not appear as a *value* in the attackers' submissions.
# REPORT.md §9(d): the constructed Runs carry no provenance of the real corpus.
SUBMISSION_FORBIDDEN = {
    r"\bunsound\b": "the defence helper the attackers could not have known",
    r"\bV9-P\d": "the summariser's predictions",
    r"a0-spike|bare_cc|baseline-arms": "repo proper nouns",
}
SUBMISSION_RUN_FIELDS = ["game_id", "campaign", "pile", "model"]

# BLINDING.md §3.7, registered and expected to still be present.
REGISTERED_LEAK = ["39960", "3 adversarial gaps"]

# Strips %-conversion machinery, so `'%d turns'` reads as carrying no digit
# while `'39960 exhaustive cases'` still does.
FORMAT_SPEC = re.compile(r"%[-#0 +]*\d*(?:\.\d+)?[a-zA-Z%]")
# A bare metric id -- 'E1', 'K12', 'P4'.  Allowed by construction: the attacker
# is told which metric is which.
METRIC_ID = re.compile(r"^[EKMPX]\d{1,2}$")


def literals(text):
    """Every string constant in `text`, via ast rather than a regex.

    The regex version of this spanned adjacent quotes and reported literals
    that do not exist.
    """
    out = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.add(node.value)
    return out


def scan(texts, patterns):
    """{pattern: [where xN]} for every pattern that matches anywhere."""
    hits = {}
    for pat in patterns:
        rx = re.compile(pat)
        for name, text in sorted(texts.items()):
            n = len(rx.findall(text))
            if n:
                hits.setdefault(pat, []).append("%s x%d" % (name, n))
    return hits


def main():
    repo = mb.repo_root(ROOT)
    sha, tree = mb.contents_at(mb.BLIND_REF, repo)
    # `files` counts what is written; `files_read` counts what is read from the
    # ref.  The two package shims are written empty, so drift is measured
    # against the second -- 5 of 10, not 5 of 12.
    report = {"pinned_ref": mb.BLIND_REF, "pinned_commit": sha,
              "python": "%d.%d" % sys.version_info[:2], "files": len(tree),
              "files_read": len(mb.COPY) + len(mb.PROTOCOL)}
    bad = []

    # --- determinism -------------------------------------------------------
    sha2, tree2 = mb.contents_at(mb.BLIND_REF, repo)
    report["deterministic"] = (tree == tree2 and sha == sha2)
    if not report["deterministic"]:
        bad.append("rebuild is not byte-identical to itself")

    # --- Scan A: the blinded tree ------------------------------------------
    a = scan(tree, TREE_FORBIDDEN)
    report["scan_a_violations"] = a
    if a:
        bad.append("blinded tree carries post-attack vocabulary: %s"
                   % ", ".join(sorted(a)))

    # --- positive control ---------------------------------------------------
    whole = "\n".join(tree[r] for r in sorted(tree))
    present = {s: whole.count(s) for s in REGISTERED_LEAK}
    report["registered_leak_present"] = present
    for s, n in present.items():
        if n == 0:
            bad.append("registered leak %r (BLINDING.md §3.7) is absent -- this "
                       "is not the tree the attackers saw" % s)

    # --- Scan B: the attackers' submissions ---------------------------------
    subs = {}
    for name in sorted(os.listdir(ATTACKS)):
        if re.fullmatch(r"a[1-6]\.py", name):
            with io.open(os.path.join(ATTACKS, name), encoding="utf-8") as fh:
                subs[name] = fh.read()
    report["submissions"] = sorted(subs)
    b = scan(subs, SUBMISSION_FORBIDDEN)
    report["scan_b_violations"] = b
    if b:
        bad.append("attacker submissions carry outside knowledge: %s"
                   % ", ".join(sorted(b)))

    runs, arms, sources, provenance = 0, set(), set(), {}
    for name, text in sorted(subs.items()):
        for node in ast.walk(ast.parse(text)):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "Run"):
                continue
            runs += 1
            for kw in node.keywords:
                if kw.arg == "arm" and isinstance(kw.value, ast.Constant):
                    arms.add(kw.value.value)
                if kw.arg == "source" and isinstance(kw.value, ast.Constant):
                    sources.add(kw.value.value)
                if kw.arg in SUBMISSION_RUN_FIELDS:
                    v = getattr(kw.value, "value", "<expr>")
                    if v is not None:
                        provenance.setdefault(kw.arg, []).append(
                            "%s=%r in %s" % (kw.arg, v, name))
    report["constructed_runs"] = runs
    report["run_arms"] = sorted(arms)
    report["run_sources"] = sorted(sources)
    report["run_provenance_fields_set"] = provenance
    if arms - {"attacker"}:
        bad.append("constructed Runs use arms other than 'attacker': %s" % sorted(arms))
    if sources - {"v9"}:
        bad.append("constructed Runs use sources other than 'v9': %s" % sorted(sources))
    if provenance:
        bad.append("constructed Runs carry real-corpus provenance: %s" % provenance)

    # --- what the old hardcoded path would have built instead ---------------
    try:
        head_sha, head_tree = mb.contents_at(WORKTREE_HEAD, repo)
    except mb.BlindingError:
        report["drift"] = "worktree HEAD unreachable in this clone; not measured"
    else:
        differing = sorted(r for r in tree if tree[r] != head_tree[r])
        leaked = {}
        for pat in TREE_FORBIDDEN:
            rx = re.compile(pat)
            n = sum(len(rx.findall(head_tree[r])) - len(rx.findall(tree[r]))
                    for r in differing)
            if n > 0:
                leaked[pat] = n
        report["drift"] = {"worktree_head": head_sha,
                           "files_differing": differing,
                           "would_have_leaked": leaked}
        if not differing:
            bad.append("expected the branch tip to differ from the pinned ref; "
                       "it does not -- re-check the provenance in FINDINGS.md")

    # --- BLINDING.md:77 follow-up: literals carrying digits -----------------
    digits = {}
    for rel, text in sorted(tree.items()):
        found = sorted(s for s in literals(text)
                       if any(ch.isdigit() for ch in FORMAT_SPEC.sub("", s))
                       and not METRIC_ID.match(s))
        if found:
            digits[rel] = found
    report["literals_with_digits"] = digits

    out = os.path.join(HERE, "rescan_blind.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")

    for line in _render(report, bad):
        print(line)
    print("wrote", os.path.relpath(out, ROOT).replace(os.sep, "/"))
    return 1 if bad else 0


def _render(report, bad):
    yield "V9 blinding re-run"
    yield "  pinned ref       %s" % report["pinned_commit"][:12]
    yield "  files rebuilt    %d written (%d read from the ref, 2 empty shims)" % (
        report["files"], report["files_read"])
    yield "  deterministic    %s" % ("yes" if report["deterministic"] else "NO")
    yield "  scan A (tree)    %s" % ("clean -- no post-attack vocabulary"
                                     if not report["scan_a_violations"]
                                     else "VIOLATED %s" % report["scan_a_violations"])
    yield "  scan B (attacks) %d Run(s) in %d submission(s); arms=%s sources=%s; %s" % (
        report["constructed_runs"], len(report["submissions"]),
        report["run_arms"], report["run_sources"],
        "clean" if not report["scan_b_violations"] and not report["run_provenance_fields_set"]
        else "VIOLATED")
    yield "  registered leak  %s" % ", ".join(
        "%s x%d" % (s, n) for s, n in sorted(report["registered_leak_present"].items()))
    d = report["drift"]
    if isinstance(d, dict):
        yield "  drift vs the old hardcoded path:"
        yield "    %d of %d files read from the ref would have differed" % (
            len(d["files_differing"]), report["files_read"])
        for rel in d["files_differing"]:
            yield "      %s" % rel
        yield "    it would have leaked: %s" % (
            ", ".join("%s x%d" % kv for kv in sorted(d["would_have_leaked"].items()))
            or "none")
    else:
        yield "  drift            %s" % d
    yield "  literals carrying a datum (BLINDING.md:77 follow-up):"
    for rel, ss in sorted(report["literals_with_digits"].items()):
        for s in ss:
            yield "      %-16s %s" % (rel.rsplit("/", 1)[-1],
                                      s if len(s) < 96 else s[:93] + "...")
    yield ""
    if bad:
        for b in bad:
            yield "FAIL: %s" % b
    else:
        yield "green -- the rebuild reproduces every recorded claim about the blind"


if __name__ == "__main__":
    sys.exit(main())
