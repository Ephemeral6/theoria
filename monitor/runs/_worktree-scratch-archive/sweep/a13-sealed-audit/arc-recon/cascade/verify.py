"""P-20 accounting check -- every action has a request, a response and a frame hash.

    python -m cascade.verify --run-dir <dir>          (exit 1 on any failure)

This is the stop-hook. It exists because the failure this repository keeps
paying for is not a wrong number, it is a *record that cannot be checked*:
INC-003's precheck could not fail, INC-006a's derivation fell open, INC-009's
redactor leaked through itself. So the run's own files are audited against each
other rather than believed.

Seven assertions, each of which can actually fail:

  A1 every step in `steps.<game>.jsonl` names a request that is in the ledger
  A2 every such request has a recorded response with the step's status
  A3 the frame hashes in the step are RECOMPUTED from the ledger's stored frames
     and must match -- a step cannot assert a hash the ledger does not support
  A4 sequence completeness: 1 + len(spec sequence) steps, or a recorded early
     stop whose last step carries an error
  A5 budget: executed actions per game <= 7 and in total <= 30
  A6 secret hygiene: no ledger entry carries a cookie VALUE (INC-008), the API
     key never appears in any run file, and `X-API-Key` is redacted everywhere
  A7 the sealed pile is absent from every request body

A3 is the load-bearing one. A summary that agrees with itself proves nothing
(PARTNER_SYNC, proxy's security note: 账本自洽 != 账本可信); a summary whose
hashes are re-derived from the raw bodies at least cannot drift from them.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ARC_RECON = os.path.dirname(HERE)
sys.path.insert(0, ARC_RECON)

from client import load_api_key                            # noqa: E402
from precheck import hash_frames                           # noqa: E402
from cascade import spec                                   # noqa: E402
from cascade.probe import hash_one, resolve_env            # noqa: E402
import sealed as sealed_mod                                # noqa: E402


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def sealed_ids() -> List[str]:
    """The sealed pile, from the one module that owns the question (A13).

    This used to open `piles.json` itself, which made it the third independent
    implementation of "is this id sealed" in `arc-recon/`. The three had drifted:
    A7 below compared full ids only, so the bare stem `probe.py` puts in every
    scorecard's `tags` was invisible to it, and `contamination.py` could not see
    it either because it only looked inside `request_body["game_id"]`.
    """
    return sealed_mod.sealed_pile()


def audited_ledgers(run_dir: str) -> List[str]:
    """Every `ledger.*.jsonl` under the run directory, discovered not named.

    A13: `verify()` builds filenames from `spec.SEQUENCES` -- the four
    development games -- so `ledger.<sealed-id>.jsonl` dropped into a run
    directory was never `os.path.exists`-ed, never opened, and contributed
    nothing to `checked`. The sealed check cannot be the one check that only
    looks where it expects the answer to be no.

    `os.walk`, not `os.listdir`: an adversarial pass pointed out that the first
    version of this was one level deep while `redact_ledger.all_ledgers` -- the
    routine whose discipline it claimed to copy -- recurses, so a shard
    subdirectory was still invisible.
    """
    out: List[str] = []
    for root, _dirs, names in os.walk(run_dir):
        if "__pycache__" in root:
            continue
        for name in names:
            if name.startswith("ledger.") and name.endswith(".jsonl"):
                out.append(os.path.join(root, name))
    return sorted(out)


def run_file_names(run_dir: str) -> List[str]:
    """Every file under the run directory, for the name check.

    Naming *any* run file after a sealed game is the thing the cut forbids --
    `steps.<sealed>.jsonl` and `summary.<sealed>.json` say it as loudly as a
    ledger does, and the first version of this checked only ledger names.
    """
    out: List[str] = []
    for root, _dirs, names in os.walk(run_dir):
        if "__pycache__" in root:
            continue
        out.extend(os.path.join(root, name) for name in names)
    return sorted(out)


def read_jsonl_lenient(path: str):
    """`read_jsonl`, but a bad line is a finding rather than a traceback.

    `read_jsonl` lets `JSONDecodeError` and `PermissionError` escape, so one
    corrupt byte in a discovered ledger aborted `verify()` with no verdict and
    no JSON output at all. A sealed audit that cannot read a file must say so,
    which is the same rule `contamination.py` follows.
    """
    records, problems = [], []
    try:
        raw = open(path, encoding="utf-8").read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [], ["%s: %s: %s" % (os.path.basename(path),
                                    type(exc).__name__, exc)]
    for i, line in enumerate(raw, 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError as exc:
            problems.append("%s line %d does not parse (%s), so it has not been "
                            "audited" % (os.path.basename(path), i, exc))
    return records, problems


def undiscovered_ledger_failures(run_dir: str,
                                 sealed: List[str] = None) -> Dict[str, Any]:
    """A7b -- every ledger in the run directory, not only the named ones.

    A13: `verify()` builds its filenames from `spec.SEQUENCES`, the four
    development games, so a file called `ledger.<sealed-id>.jsonl` sitting
    beside them was never `os.path.exists`-ed, never opened, and contributed
    nothing to `checked`. A7 then reported PASS over a directory it had not
    finished reading -- the sealed check being the one check that only looked
    where it expected the answer to be no.

    Every file *name* under the directory is checked, not only the ledgers':
    `steps.<sealed>.jsonl` and `summary.<sealed>.json` say the forbidden thing
    as loudly as a ledger does, and a run that produced no records for it is not
    thereby innocent.

    Separated from `verify()` so it can be tested: `verify()` loads the API key
    for its secret sweep, and a check about sealed games should not require a
    credential to exercise.
    """
    sealed = sealed if sealed is not None else sealed_ids()
    failures: List[str] = []
    # Only the ledgers `verify()` ACTUALLY read. It skips a game whose
    # `steps.<game>.jsonl` is absent, so building this from `spec.SEQUENCES`
    # unconditionally excluded exactly those files from A7b as well -- a
    # ledger named after a dev game, with no steps file, was audited by
    # neither. An adversarial pass built that case on the shape of the real
    # `-p20-followup` run directory, which holds one game of four.
    expected = {os.path.join(run_dir, "ledger.%s.jsonl" % game)
                for game in spec.SEQUENCES
                if os.path.exists(os.path.join(run_dir, "steps.%s.jsonl" % game))}
    undiscovered = 0
    entries_read = 0
    for path in run_file_names(run_dir):
        name = os.path.basename(path)
        for sealed_id, why in sealed_mod.hits(name, sealed).items():
            failures.append("A7b %s: run file is named after sealed game %s (%s)"
                            % (name, sealed_id, why))
    for path in audited_ledgers(run_dir):
        name = os.path.basename(path)
        if path in expected:
            continue                     # already read, entry by entry, by verify()
        undiscovered += 1
        records, problems = read_jsonl_lenient(path)
        failures.extend("A7b %s" % p for p in problems)
        for entry in records:
            entries_read += 1
            for sealed_id, why in sealed_mod.hits_in_any(
                    [entry.get("request_body"), entry.get("url"),
                     entry.get("final_url")], sealed).items():
                failures.append(
                    "A7b %s: sealed game %s appears in a request (%s), in a "
                    "ledger no game sequence names" % (name, sealed_id, why))
    return {"failures": failures, "undiscovered": undiscovered,
            "entries_read": entries_read}


def note_prefix(game: str, step: Dict[str, Any]) -> str:
    if step["action"] == "RESET":
        return "p20 RESET %s attempt" % game
    return "p20 %s #%d %s attempt" % (step["action"], step["seq"] - 1, game)


def verify(run_dir: str) -> int:
    failures: List[str] = []
    checked = {"steps": 0, "games": 0, "ledger_entries": 0, "actions": 0}
    sealed = sealed_ids()
    key = load_api_key(resolve_env())

    for game in sorted(spec.SEQUENCES):
        steps_path = os.path.join(run_dir, "steps.%s.jsonl" % game)
        ledger_path = os.path.join(run_dir, "ledger.%s.jsonl" % game)
        if not os.path.exists(steps_path):
            # A run directory need not hold every game -- the follow-up run is
            # tn36 only. `verify.sh` refuses a directory with no steps at all,
            # so "nothing to check" still cannot be reported as a pass.
            continue
        steps = read_jsonl(steps_path)
        ledger = read_jsonl(ledger_path)
        if not steps:
            failures.append("A4 %s: %s exists but is empty" % (game, steps_path))
            continue
        checked["games"] += 1
        checked["ledger_entries"] += len(ledger)

        for step in steps:
            checked["steps"] += 1
            prefix = note_prefix(game, step)
            entries = [e for e in ledger if str(e.get("note", "")).startswith(prefix)]
            if not entries:                                             # A1
                failures.append("A1 %s seq=%s: no ledger request for %r"
                                % (game, step["seq"], prefix))
                continue
            last = entries[-1]
            body = last.get("request_body") or {}
            if body.get("game_id") != game:                             # A1
                failures.append("A1 %s seq=%s: request game_id %r != %r"
                                % (game, step["seq"], body.get("game_id"), game))
            if last.get("status") != step.get("http_status"):           # A2
                failures.append("A2 %s seq=%s: ledger status %s != step status %s"
                                % (game, step["seq"], last.get("status"),
                                   step.get("http_status")))
            if step.get("attempts") != len(entries):                    # A2
                failures.append("A2 %s seq=%s: %d ledger attempts != recorded %s"
                                % (game, step["seq"], len(entries), step.get("attempts")))

            response = last.get("response_body")
            frames = response.get("frame") if isinstance(response, dict) else None
            if step.get("frame_hashes") is None:
                if isinstance(frames, list):                            # A3
                    failures.append("A3 %s seq=%s: step has no hashes but the "
                                    "ledger response carries %d frames"
                                    % (game, step["seq"], len(frames)))
                continue
            if not isinstance(frames, list):                            # A3
                failures.append("A3 %s seq=%s: step claims %d frame hashes, the "
                                "ledger response has no frame list"
                                % (game, step["seq"], len(step["frame_hashes"])))
                continue
            if [hash_one(f) for f in frames] != step["frame_hashes"]:   # A3
                failures.append("A3 %s seq=%s: per-frame hashes do not recompute "
                                "from the ledger" % (game, step["seq"]))
            if hash_frames(frames) != step.get("batch_hash"):           # A3
                failures.append("A3 %s seq=%s: batch hash does not recompute "
                                "from the ledger" % (game, step["seq"]))
            if len(frames) != step.get("n_frames"):                     # A3
                failures.append("A3 %s seq=%s: n_frames %s != %d frames in the "
                                "ledger" % (game, step["seq"], step.get("n_frames"),
                                            len(frames)))

        # Which sequence set this run used is a property of the run, not of the
        # verifier's guess. The summary records it; fall back to `main` only
        # when there is no summary (a run that died before writing one).
        summary_path = os.path.join(run_dir, "summary.%s.json" % game)
        which = "main"
        if os.path.exists(summary_path):
            with open(summary_path, encoding="utf-8") as fh:
                which = json.load(fh).get("set", "main")
        wanted = 1 + len(spec.SETS[which].get(game, []))
        if len(steps) != wanted:                                        # A4
            if steps[-1].get("error") is None:
                failures.append("A4 %s: %d steps, spec wants %d, and the last "
                                "step records no error"
                                % (game, len(steps), wanted))
        executed = sum(1 for s in steps
                       if s["action"] != "RESET" and s.get("http_status") == 200)
        checked["actions"] += executed
        if executed > spec.BUDGET_PER_GAME:                             # A5
            failures.append("A5 %s: %d executed actions > cap %d"
                            % (game, executed, spec.BUDGET_PER_GAME))

        for entry in ledger:                                            # A6
            names = entry.get("set_cookie_names") or []
            for name in names:
                if "=" in str(name) or len(str(name)) > 64:
                    failures.append("A6 %s: cookie field looks like a value: %r"
                                    % (game, str(name)[:40]))
            headers = entry.get("request_headers") or {}
            if headers.get("X-API-Key") not in (None, "<redacted>"):
                failures.append("A6 %s: X-API-Key not redacted in the ledger" % game)
            # A7 -- one criterion, shared with contamination.py. Was: a full-id
            # substring of `json.dumps(request_body or {})`, which missed a bare
            # stem, missed the URL entirely, and turned a body of `None` into
            # `{}` so that a GET passed without being looked at.
            for sealed_id, why in sealed_mod.hits_in_any(
                    [entry.get("request_body"), entry.get("url"),
                     entry.get("final_url")], sealed).items():
                failures.append("A7 %s: sealed game %s appears in a request (%s)"
                                % (game, sealed_id, why))

    a7b = undiscovered_ledger_failures(run_dir, sealed)
    failures.extend(a7b["failures"])
    checked["undiscovered_ledgers"] = a7b["undiscovered"]
    checked["ledger_entries"] += a7b["entries_read"]

    if checked["actions"] > spec.BUDGET_TOTAL:                          # A5
        failures.append("A5 total: %d executed actions > cap %d"
                        % (checked["actions"], spec.BUDGET_TOTAL))

    # A6 over the WHOLE package, not just the run directory. Everything under
    # cascade/ is committed and Phase 4 publishes every tracked file, so prose
    # is as capable of carrying a secret as a ledger is -- and the prose is the
    # part a human wrote by hand.
    for root, _dirs, names in os.walk(HERE):                            # A6
        if "__pycache__" in root:
            continue
        for name in names:
            path = os.path.join(root, name)
            with open(path, "rb") as fh:
                blob = fh.read()
            if key.encode("utf-8") in blob:
                failures.append("A6 %s: THE API KEY IS IN THIS FILE" % path)
            if re.search(rb"GAMESESSION=[^\"\s;]{4,}", blob):
                failures.append("A6 %s: a GAMESESSION value is in this file" % path)

    print(json.dumps({"run_dir": run_dir, "checked": checked,
                      "failures": failures,
                      "verdict": "PASS" if not failures else "FAIL"},
                     indent=2, ensure_ascii=False))
    return 1 if failures else 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    return verify(os.path.abspath(args.run_dir))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
