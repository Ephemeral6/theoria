"""CONTRACTS' completion gate — does the frozen spec still agree with its code?

    cd CONTRACTS && python verify.py

This territory is prose, so the obvious reading is that there is nothing to
check and it stays UNGATED forever. That reading is wrong in one specific way:
a frozen contract has an **executable form**, and the interesting question is
not whether the prose is well written but whether the two still say the same
thing.

`candidates_schema.md` declares a record shape. `engine-rig/tools/
validate_candidates.py` enforces one. Nothing has ever compared them. If they
drift, every stream in the repository passes a validator that is checking a
contract nobody agreed to -- and the failure is silent, because the validator
keeps returning success against its own idea of the rules.

## Three rungs

  1. **the spec parses** -- every contract file that declares a JSON example
     yields a readable object;
  2. **spec and enforcement agree** -- the key set in `candidates_schema.md`
     equals `validate_candidates.REQUIRED_KEYS`, and the `status` constant the
     prose fixes is the one the code fixes;
  3. **the executable form actually runs** -- the validator is fed the tracked
     reference stream and must accept it, and then fed a deliberately broken
     record and must reject it.

Rung 3's second half is the part worth insisting on. A validator that accepts
everything passes rung 3's first half perfectly, and this repository has met
that shape often enough to stop trusting a checker it has only seen say yes.
"""

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE_RIG = os.path.join(ROOT, "engine-rig")

#: The frozen schema and the module that enforces it.
SCHEMA = os.path.join(HERE, "candidates_schema.md")

#: Floors. A territory of seven contract documents that suddenly parses two is
#: not a simplification, it is a loss.
MIN_CONTRACT_FILES = 5
MIN_REFERENCE_ROWS = 10


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def first_json_block(path):
    """The first fenced JSON object in a Markdown file, as a dict.

    The schema is written as an annotated example rather than as JSON Schema,
    so the placeholder values are prose. Only the *keys* are read here, which
    is all rung 2 compares.
    """
    text = open(path, encoding="utf-8").read()
    # Fenced or bare. `candidates_schema.md` writes its example as a plain
    # brace block with no fence at all, and the first version of this parser
    # required ```json -- so it reported "the frozen shape cannot be compared
    # to anything" about a file that states the shape perfectly clearly. A
    # checker that cannot read its subject must say so, which it did, but the
    # right fix is to read the subject as it is rather than as I assumed.
    m = re.search(r"^\{\s*$(.*?)^\}\s*$", text, re.S | re.M)
    if not m:
        m = re.search(r"```(?:json|jsonc)?\s*\n\{(.*?)\n\}\s*\n```", text, re.S)
    if not m:
        return None
    keys = re.findall(r'^\s*"([A-Za-z_][A-Za-z0-9_]*)"\s*:', m.group(1), re.M)
    return keys or None


def rung_spec_parses(problems):
    print("[1/3] the contract documents")
    files = sorted(f for f in os.listdir(HERE) if f.endswith(".md"))
    if len(files) < MIN_CONTRACT_FILES:
        fail(problems, "only %d contract document(s), floor is %d -- a "
                       "territory that suddenly holds fewer contracts has lost "
                       "some, not simplified" % (len(files), MIN_CONTRACT_FILES))
        return None
    keys = first_json_block(SCHEMA)
    if not keys:
        fail(problems, "candidates_schema.md declares no readable JSON example "
                       "-- the frozen shape cannot be compared to anything")
        return None
    print("   ok    %d contract document(s); candidates_schema declares %d keys"
          % (len(files), len(keys)))
    return set(keys)


def rung_spec_matches_code(problems, spec_keys):
    print("[2/3] the spec and its executable form say the same thing")
    sys.path.insert(0, ENGINE_RIG)
    try:
        from tools import validate_candidates as vc
    except Exception as exc:
        fail(problems, "cannot import the executable form: %s" % exc)
        return
    code_keys = set(getattr(vc, "REQUIRED_KEYS", ()) or ())
    if not code_keys:
        fail(problems, "validate_candidates declares no REQUIRED_KEYS -- there "
                       "is nothing enforcing the frozen shape")
        return
    only_spec = sorted(spec_keys - code_keys)
    only_code = sorted(code_keys - spec_keys)
    if only_spec or only_code:
        fail(problems, "the frozen schema and the validator disagree. "
                       "only in the spec: %s; only in the code: %s. One of "
                       "them is enforcing a contract nobody agreed to."
             % (only_spec or "-", only_code or "-"))
        return
    text = open(SCHEMA, encoding="utf-8").read()
    if '"candidate"' not in text:
        fail(problems, "the schema no longer fixes status to \"candidate\"")
        return
    print("   ok    %d keys, identical on both sides; status pinned in both"
          % len(code_keys))


def rung_the_validator_really_validates(problems):
    print("[3/3] the executable form accepts the real stream and rejects a "
          "broken one")
    ref = os.path.join(ENGINE_RIG, "artifacts", "candidates.jsonl")
    if not os.path.exists(ref):
        fail(problems, "no reference stream at engine-rig/artifacts/"
                       "candidates.jsonl to validate against")
        return
    rows = [json.loads(l) for l in open(ref, encoding="utf-8") if l.strip()]
    if len(rows) < MIN_REFERENCE_ROWS:
        fail(problems, "the reference stream holds %d row(s), floor is %d -- "
                       "an almost-empty stream validates trivially"
             % (len(rows), MIN_REFERENCE_ROWS))
        return

    r = subprocess.run([sys.executable, "-m", "tools.validate_candidates", ref],
                       cwd=ENGINE_RIG, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        fail(problems, "the validator rejects the tracked reference stream\n%s"
             % (r.stdout + r.stderr)[-2000:])
        return

    # The negative control. A validator that accepts everything satisfies the
    # half above perfectly, and a checker this repository has only ever seen
    # say yes has not been observed to check anything.
    scratch = tempfile.mkdtemp(prefix="contracts-verify-")
    try:
        broken = copy.deepcopy(rows[0])
        broken["status"] = "adjudicated"      # engines never adjudicate
        path = os.path.join(scratch, "broken.jsonl")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(broken, sort_keys=True) + "\n")
        r = subprocess.run([sys.executable, "-m", "tools.validate_candidates",
                            path], cwd=ENGINE_RIG, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            fail(problems, "the validator ACCEPTED a record whose status is "
                           "'adjudicated'. The contract's central rule -- "
                           "engines propose, they never adjudicate -- is not "
                           "being enforced by the thing that enforces it.")
            return
    finally:
        import shutil
        shutil.rmtree(scratch, ignore_errors=True)

    print("   ok    %d reference rows accepted; a forged status is rejected"
          % len(rows))


def main():
    argparse.ArgumentParser().parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    problems = []
    spec_keys = rung_spec_parses(problems)
    if spec_keys:
        rung_spec_matches_code(problems, spec_keys)
    rung_the_validator_really_validates(problems)
    print()
    if problems:
        print("CONTRACTS: RED (%d problem(s))" % len(problems))
        return 1
    print("CONTRACTS: green -- the frozen spec and its executable form agree, "
          "and the validator has been seen to say no")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
