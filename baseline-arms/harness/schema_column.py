"""The main table's middle column, recomputed and guarded.

`Theoria.md:271` carries one row this repository has never been able to
produce:

    | Schema(复现口径) | 98.98%(上游)/ ⟨复现值⟩ | ~10⁸(实测 2.04–3.41 亿) | world_model.py(重放级) |

Three cells, three different epistemic states, and until now they were treated
as one thing:

* **the score cell** -- `98.98%` is upstream's number over 25 games;
  `⟨复现值⟩` is a placeholder that can never be filled, because the harness was
  never released (`SCHEMA_LOCATE.md` §2.2).
* **the cache-read cell** -- `~10⁸(实测 2.04–3.41 亿)` says 实测, *measured*.
  No measurement of it exists anywhere in this repository.  This module is the
  first one, and it does not reproduce the stated interval.
* **the deliverable cell** -- `world_model.py(重放级)` is a fact about the
  released artefacts and is true on the 4 development-pile games we hold.

Two entry points, and they fail in opposite directions on purpose.

``measure_cache_reads`` reads the gitignored upstream payload and returns
per-run token aggregates.  It never returns, prints or stores a frame, an
action, a transcript line or a world-model source byte (`battery/DECISIONS.md`
D-B-020).  Aggregates only.

``check_text`` is the guard: it refuses any text that fills ⟨复现值⟩ or calls
the upstream material a reproduction.  A guard that has never been seen to say
no has not been shown to check anything, so `tests/test_schema_column.py`
drives it with fabricated violations and requires a refusal for each.

**Deduplication is the whole measurement.** A Claude Code session log records
each assistant message's `usage` block once at the top level and again inside
`usage.iterations[*]`.  Summing every `cache_read_input_tokens` key found by a
naive tree walk double-counts, and it double-counts by a factor that varies per
run (3.5x on sk48, 4.6x on g50t) -- so the error is not a constant anybody
would notice as a constant.  Both conventions are reported here, because
"which convention produces 2.04–3.41 亿" is a question a reader should be able
to ask and answer, and the answer turns out to be *neither*.

    cd baseline-arms && python -m harness.schema_column measure
    cd baseline-arms && python -m harness.schema_column check <path>...
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterator, List, Optional, Tuple

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ROOT = os.path.join(TRACK, "schema_traces")
ROOT_ENV = "THEORIA_SCHEMA_TRACES"

#: The upstream collections, and whether their session log records token usage
#: at all.  `False` is not a defect to route around: the Codex rollout log has
#: no token fields, and a zero there would be a fabrication.
COLLECTIONS: Tuple[Tuple[str, bool], ...] = (
    ("claude_fable_opus", True),
    ("gpt_5_6_sol", False),
)

#: `Theoria.md:271`, verbatim, as an interval in tokens.  Recorded so the
#: mismatch is a computation rather than an assertion.
TABLE_CLAIM = (204_000_000, 341_000_000)


def resolve_root(root: Optional[str] = None) -> str:
    """Explicit argument, then the environment, then the repo-relative default.

    The payload is gitignored, and **a linked git worktree does not contain
    it** -- ignored files are not checked out.  An agent on a branch therefore
    sees `baseline-arms/` fully populated except for this directory, and a
    reader that silently found nothing would report a clean zero.  Whichever
    path answers is returned so the caller can record it.
    """
    return root or os.environ.get(ROOT_ENV) or DEFAULT_ROOT


def _iter_runs(root: str) -> Iterator[Tuple[str, str, str]]:
    for collection, _ in COLLECTIONS:
        base = os.path.join(root, collection)
        if not os.path.isdir(base):
            continue
        for run in sorted(os.listdir(base)):
            path = os.path.join(base, run)
            if os.path.isdir(path):
                yield collection, run, path


def _naive_walk(obj: Any, out: List[Dict[str, Any]]) -> None:
    """Every dict anywhere carrying `cache_read_input_tokens`.

    This is the wrong convention.  It is computed anyway, because the point of
    the exercise is to find out whether *any* convention yields the published
    interval.
    """
    if isinstance(obj, dict):
        if "cache_read_input_tokens" in obj:
            out.append(obj)
        for value in obj.values():
            _naive_walk(value, out)
    elif isinstance(obj, list):
        for value in obj:
            _naive_walk(value, out)


def measure_run(run_dir: str) -> Dict[str, Any]:
    """Token aggregates for one upstream run directory.

    Returns counts only.  Nothing derived from message content, tool arguments
    or world-model source leaves this function.
    """
    sessions = os.path.join(run_dir, "sessions")
    deduped: Dict[str, Dict[str, Any]] = {}
    naive: List[Dict[str, Any]] = []
    if os.path.isdir(sessions):
        for name in sorted(os.listdir(sessions)):
            if not name.endswith(".jsonl"):
                continue
            with open(os.path.join(sessions, name), encoding="utf-8",
                      errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    _naive_walk(record, naive)
                    if record.get("type") != "assistant":
                        continue
                    message = record.get("message") or {}
                    usage = message.get("usage")
                    if not isinstance(usage, dict):
                        continue
                    # Message id first; `uuid` only as a fallback, so a log
                    # that omits ids degrades to per-record rather than to
                    # collapsing every message into one bucket.
                    key = message.get("id") or record.get("uuid") or str(len(deduped))
                    deduped[key] = usage

    def total(blocks, field: str) -> int:
        return sum(int(block.get(field) or 0) for block in blocks)

    values = list(deduped.values())
    return {
        "assistant_messages": len(values),
        "usage_records_naive": len(naive),
        "cache_read_tokens": total(values, "cache_read_input_tokens"),
        "cache_read_tokens_naive": total(naive, "cache_read_input_tokens"),
        "cache_creation_tokens": total(values, "cache_creation_input_tokens"),
        "input_tokens": total(values, "input_tokens"),
        "output_tokens": total(values, "output_tokens"),
        "env_steps": _count_steps(run_dir),
    }


def _count_steps(run_dir: str) -> Optional[int]:
    """Lines in `events.jsonl`, as a coarse action-budget proxy.

    `None` rather than 0 when the file is absent: an unmeasured count is not a
    count of zero, which is the same rule `proxy/cost.py` applies to dollars.
    """
    path = os.path.join(run_dir, "events.jsonl")
    if not os.path.exists(path):
        return None
    count = 0
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def measure_cache_reads(root: Optional[str] = None) -> Dict[str, Any]:
    """The middle column's cache-read cell, recomputed over what we hold."""
    root = resolve_root(root)
    runs: Dict[str, Dict[str, Any]] = {}
    for collection, run, path in _iter_runs(root):
        entry = measure_run(path)
        entry["collection"] = collection
        runs["%s/%s" % (collection, run)] = entry

    with_usage = [entry for entry in runs.values() if entry["assistant_messages"]]
    reads = sorted(entry["cache_read_tokens"] for entry in with_usage)
    naive_reads = sorted(entry["cache_read_tokens_naive"] for entry in with_usage)
    low, high = TABLE_CLAIM
    return {
        "root": root,
        "runs": runs,
        "n_runs": len(runs),
        "n_runs_with_token_usage": len(with_usage),
        "cache_read_range": [reads[0], reads[-1]] if reads else None,
        "cache_read_range_naive": ([naive_reads[0], naive_reads[-1]]
                                   if naive_reads else None),
        "table_claim_tokens": list(TABLE_CLAIM),
        "table_claim_reproduced": bool(
            reads and low <= reads[0] and reads[-1] <= high),
        "table_claim_reproduced_naive": bool(
            naive_reads and low <= naive_reads[0] and naive_reads[-1] <= high),
    }


# --------------------------------------------------------------------------
# The guard.
# --------------------------------------------------------------------------

#: A filled reproduction cell, in the shapes it would plausibly be written.
#: The bracket forms are the placeholder itself with a number substituted; the
#: prose forms are the claim made in words.
_FILLED_CELL = re.compile(
    r"(复现值\s*[:：=]\s*[0-9]|"
    r"⟨\s*复现值\s*[:：=]\s*[0-9]|"
    r"复现口径\s*[)）]?\s*\|\s*[0-9.]+\s*%\s*[(（]?\s*上游\s*[)）]?\s*/\s*[0-9]|"
    r"(?:our|we\s+\w+\s+a)\s+reproduction\s+score\s+(?:of\s+)?[0-9]|"
    r"reproduction\s+score\s*[:=]\s*[0-9])")

#: Calling the ingested upstream ledger a reproduction *of ours*.  The phrase
#: "not a reproduction" must not trip this, which is what the negative
#: lookbehind on 不/not is for.
_CALLED_REPRO = re.compile(
    r"((?<!not )(?<!never )we\s+reproduced\s+Schema|"
    r"(?<!不)(?<!未)复现了\s*Schema|"
    r"our\s+Schema\s+reproduction|"
    r"Schema\s+复现臂(?!\s*不存在))")


def check_text(text: str, label: str = "<text>") -> List[Dict[str, str]]:
    """Findings for one document.  Empty list means the text is clean.

    Deliberately narrow.  A guard that flags every occurrence of the word
    "Schema" would be switched off within a week, and a guard that is switched
    off checks nothing.
    """
    findings: List[Dict[str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern, rule in ((_FILLED_CELL, "filled-repro-cell"),
                              (_CALLED_REPRO, "upstream-called-reproduction")):
            match = pattern.search(line)
            if match:
                findings.append({
                    "file": label,
                    "line": str(line_no),
                    "rule": rule,
                    "match": match.group(0)[:80],
                })
    return findings


def check_paths(paths: List[str]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as exc:
            findings.append({"file": path, "line": "0", "rule": "unreadable",
                             "match": str(exc)[:80]})
            continue
        findings.extend(check_text(text, label=path))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    measure = sub.add_parser("measure", help="recompute the cache-read cell")
    measure.add_argument("--root", default=None)

    check = sub.add_parser("check", help="refuse a filled reproduction cell")
    check.add_argument("paths", nargs="+")

    args = parser.parse_args(argv)

    if args.cmd == "measure":
        report = measure_cache_reads(args.root)
        if not os.path.isdir(report["root"]):
            print("REFUSED: no payload at %s (set %s)"
                  % (report["root"], ROOT_ENV), file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    findings = check_paths(args.paths)
    for finding in findings:
        print("%(file)s:%(line)s: %(rule)s: %(match)s" % finding)
    print("checked %d file(s), %d finding(s)" % (len(args.paths), len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
