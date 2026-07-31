"""The freeze record: what BATTERY_V1.md pins, and how to check it still holds.

`Theoria.md:368` requires the metric battery to enter Phase 4 as a hashed item
on the freeze list — 指标电池 v1(定义与代码、逐指标方向预测). This module is the
executable half of that: `BATTERY_V1.md` carries the digests, and `verify()`
recomputes them and refuses on disagreement.

Six things are pinned, and they are pinned for different reasons:

* **code** — every file whose edit can move a published number. A change here
  without a new freeze version means the numbers in `REPORT_V2.md` were produced
  by an instrument that no longer exists.
* **docs** — `docs.py` and the two documents it renders. `METRICS.md` is read by
  humans as a statement of what the instrument *is*, so it is gated, not merely
  recorded — even though part of it is derived from a reading (see `readings`).
* **suite** — all of `battery/tests`. The suite is half the gate: `verify.py`
  runs the freeze check *and* pytest, and a suite that can be edited freely can
  be made to stop objecting. Freezing it costs a version bump per new test; that
  is the intended price.
* **freeze** — this module and `verify.py`, so that quietly relaxing the check
  shows up in a diff like any other edit.
* **prereg** — `PREDICTIONS.md`, append-only. Two checks, because the two ways of
  breaking it are not the same offence: the frozen prefix must stay
  byte-identical (editing a prediction after the fact is forbidden outright),
  and the whole-file digest must match (appending after the freeze is legal work
  that needs a new freeze version, not a silent extension).
* **cut** — the pile cut's canonical digest. `arc-recon/data/piles.json` lives
  outside this territory and is a *contract*, not a reading: `CLAUDE.md`
  publishes its digest and changing it after play has begun is an incident. The
  file's own `sha256` field is self-referential and verifies a doctored cut
  happily, so the expected value is pinned here, in a frozen file.

What is deliberately **recorded but not gated**: `readings` — the seven
artefacts. The battery is a passive instrument and Phase 4 exists to point it at
inputs it has never read, so failing on changed artefacts would fail by
construction on the first sealed-pile recompute. `verify.py` reports drift and
still exits 0. The inputs themselves are recorded in BATTERY_V1.md §6.1 and are
not digested here at all, for the same reason.

Hashing is sha256 over the bytes with CRLF normalised to LF, following
`proxy/scoring/__init__.py:64`. `battery/.gitattributes` pins LF for everything
in this territory, so inside `battery/` the two agree; normalising anyway is what
keeps the record reproducible on a clone configured differently.
"""

import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RECORD = os.path.join(HERE, "BATTERY_V1.md")

FREEZE_VERSION = "BATTERY_V1"


class FreezeDriftError(Exception):
    """Raised when the tree no longer matches the freeze record."""


def sha256_file(path):
    """Digest one file, newlines normalised to LF.

    The freeze is about the code, not about how a checkout transported it.
    """
    with open(path, "rb") as fh:
        blob = fh.read().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def sha256_prefix(path, nbytes):
    """Digest the first `nbytes` bytes of a file, newlines normalised to LF.

    Normalisation happens before the cut, so the byte count is an LF count and
    does not shift when a file is checked out with CRLF.
    """
    with open(path, "rb") as fh:
        blob = fh.read().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(blob[:nbytes]).hexdigest(), len(blob)


# --- the frozen file set -------------------------------------------------
#
# Membership is itself part of the freeze: `unlisted()` walks battery/ and fails
# on any file — not just any `.py` — that no bucket and no exclusion covers. A
# thirty-ninth metric, a new `conftest.py`, and an edited `pytest.ini` are all
# ways to move a published number, and only a whole-tree walk sees all three.

CODE = [
    # registry and the shapes every metric reads
    "battery/__init__.py",
    "battery/model.py",
    "battery/metrics/__init__.py",
    # the 38 metric bodies
    "battery/metrics/economy.py",
    "battery/metrics/epistemic.py",
    "battery/metrics/exploration.py",
    "battery/metrics/mechanism.py",
    "battery/metrics/planning.py",
    # adapters decide what a Run contains, hence every value
    "battery/adapters/__init__.py",
    "battery/adapters/a0.py",
    "battery/adapters/a0_spike.py",
    "battery/adapters/a2.py",
    "battery/adapters/ledger_jsonl.py",
    "battery/adapters/schema_traces.py",
    "battery/adapters/theoria_live.py",
    # guardrail and driver
    "battery/guard.py",
    "battery/run_battery.py",
    # the four processes
    "battery/audit/__init__.py",
    "battery/audit/contrast.py",
    "battery/audit/discriminate.py",
    "battery/audit/gaming.py",
    "battery/audit/redundancy.py",
    "battery/audit/live_arm.py",
    "battery/audit/live_economy.py",
    "battery/audit/live_tiers.py",
    "battery/audit/stats.py",
    # the threat-model split and the E2L candidate: both publish numbers and
    # both can move a verdict, so they are frozen like any other audit code.
    "battery/audit/threat.py",
    "battery/audit/frontload.py",
    "battery/audit/validation.py",
    # exploits are not documentation: tier_of() prefers a demonstrated
    # verdict over the prose register, so editing one moves a metric
    # between the main table and reference.
    "battery/audit/exploits/__init__.py",
    "battery/audit/exploits/economy.py",
    "battery/audit/exploits/exploration_planning.py",
    "battery/audit/exploits/mechanism_epistemic.py",
    # not Python, and load-bearing: without it core.autocrlf re-materialises
    # this tree with CRLF and every digest above goes stale silently.
    "battery/.gitattributes",
    # also not Python, also load-bearing: it is the pytest rootdir config, so
    # one `addopts` line can deselect any test that would have objected.
    "battery/pytest.ini",
    # what git refuses to see is part of what the tree is: an ignore line can
    # hide a file from every reviewer while the interpreter still imports it.
    "battery/.gitignore",
    # the V9 adversarial audit: its code decides the audit's published verdict,
    # and BLIND_DIGESTS.json is the pin the blinding check verifies against.
    "battery/audit/v9/BLIND_DIGESTS.json",
    "battery/audit/v9/__init__.py",
    "battery/audit/v9/attack.py",
    "battery/audit/v9/check.py",
    "battery/audit/v9/make_blind.py",
    "battery/audit/v9/mutants.py",
    "battery/audit/v9/prereg.py",
    "battery/audit/v9/run.py",
    "battery/audit/v9/verdict.py",
    "battery/audit/v9/attacks/__init__.py",
    "battery/audit/v9/attacks/a1.py",
    "battery/audit/v9/attacks/a2.py",
    "battery/audit/v9/attacks/a3.py",
    "battery/audit/v9/attacks/a4.py",
    "battery/audit/v9/attacks/a5.py",
    "battery/audit/v9/attacks/a6.py",
    "battery/audit/v9/attacks/a7_review.py",
]

DOCS = [
    "battery/docs.py",              # renders the two below
    "battery/METRICS.md",
    "battery/audit/REDUNDANCY.md",
]

SUITE = [
    "battery/tests/__init__.py",
    "battery/tests/fixtures/ledger_fixture.jsonl",
    "battery/tests/make_fixture.py",
    "battery/tests/test_adapter_a0_spike.py",
    "battery/tests/test_adapter_a2.py",
    "battery/tests/test_adapter_schema_traces.py",
    "battery/tests/test_adapters.py",
    "battery/tests/test_determinism.py",
    "battery/tests/test_discriminate_arms.py",
    "battery/tests/test_docs.py",
    "battery/tests/test_exploits_economy.py",
    "battery/tests/test_exploits_exploration_planning.py",
    "battery/tests/test_exploits_mechanism_epistemic.py",
    "battery/tests/test_freeze.py",
    "battery/tests/test_guard.py",
    "battery/tests/test_live_economy.py",
    "battery/tests/test_live_tiers.py",
    "battery/tests/test_metrics.py",
    "battery/tests/test_theoria_live.py",
    "battery/tests/test_threat_and_frontload.py",
    "battery/tests/test_v9_blinding.py",
    "battery/tests/test_v9_defences.py",
    "battery/tests/test_v9_prereg.py",
    "battery/tests/test_v9_verdict_rule.py",
    "battery/tests/test_verify_separation_claim.py",
]

FREEZE = [
    "battery/freeze.py",
    "battery/verify.py",
]

# Recorded, reported on drift, and deliberately NOT gated. See module docstring.
# `artifacts_live/` is in here too: the live-tier companion is a reading of the
# live code, and verify.py's rung 6 is what gates it (against a recompute, not
# against this record) — gating it here as well would demand a freeze version
# per legitimate regeneration.
READINGS = [
    "battery/artifacts/arm_contrast.json",
    "battery/artifacts/capability_spectrum.json",
    "battery/artifacts/discrimination.json",
    "battery/artifacts/discrimination_arms.json",
    "battery/artifacts/gaming_audit.json",
    "battery/artifacts/redundancy.json",
    "battery/artifacts/validation_material.json",
    "battery/artifacts_live/gaming_audit.live.json",
    "battery/artifacts_live/live_arm_readings.json",
    "battery/artifacts_live/live_economy.json",
    "battery/artifacts_live/threat_model.json",
    "battery/artifacts_live/frontload_e2l.json",
]

PREREG = "battery/PREDICTIONS.md"

# The pile cut: outside this territory, gated anyway because it is a contract.
CUT = "arc-recon/data/piles.json"
CUT_DIGEST = "3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a"

# Narrative, and uncovered on purpose. Listed one by one rather than matched by
# pattern, so that a new document under battery/ trips the walk and gets a
# deliberate decision instead of a silent pass.
NARRATIVE = [
    "battery/BATTERY_V1.md",        # the record does not hash itself
    "battery/BLINDING.md",
    "battery/PREREG_V9.md",         # its integrity is test_v9_prereg.py's job
    "battery/PREREG_E2L.md",        # ancestry is the proof; see its §0
    "battery/audit/v9/REPORT.md",
    "battery/DECISIONS.md",
    "battery/INPUT_FORMAT.md",
    "battery/README.md",
    "battery/REPORT_V0.md",
    "battery/REPORT_V1.md",
    "battery/REPORT_V2.md",
    "battery/STATUS.md",
]

# Directories the walk does not enter, each with the reason it cannot hide code
# that moves a published number.
SKIP_DIRS = {
    "__pycache__": "untracked build output",
    ".pytest_cache": "untracked build output",
    "runs": "run records, including this freeze's own manifest",
}

BUCKETS = (("code", CODE), ("docs", DOCS), ("suite", SUITE),
           ("freeze", FREEZE), ("readings", READINGS))
GATED = ("code", "docs", "suite", "freeze")


def fingerprint(bucket, root=ROOT):
    """Digest a bucket, sorted by path. Missing files raise rather than vanish."""
    out = {}
    for rel in sorted(bucket):
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.exists(path):
            raise FreezeDriftError(
                "%s is in the freeze record but not on disk. A frozen file that "
                "can disappear silently is not frozen." % rel)
        out[rel] = sha256_file(path)
    return out


def unlisted(root=ROOT):
    """Files under battery/ that no bucket and no exclusion covers.

    Walks every file, not only `*.py`: `pytest.ini` is the pytest rootdir config
    and can deselect any test that would have objected, which makes it as
    load-bearing as a metric body.
    """
    listed = set(NARRATIVE) | {PREREG}
    for _name, bucket in BUCKETS:
        listed |= set(bucket)
    out = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, "battery")):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, name),
                                  root).replace(os.sep, "/")
            if rel not in listed:
                out.append(rel)
    return out


# --- reading the record --------------------------------------------------

_DIGEST = re.compile(r"^(sha256:[0-9a-f]{64})\s\s(\S+)$", re.M)
_FENCE = r"```freeze:%s\n(.*?)```"


def _block(text, name):
    """Pull exactly one fenced ```freeze:<name> block out of the record.

    `re.search` would take the first of several and ignore the rest, which is a
    silent way to have a second block nobody checks.
    """
    found = re.findall(_FENCE % re.escape(name), text, re.S)
    if not found:
        raise FreezeDriftError(
            "BATTERY_V1.md has no `freeze:%s` block. The record cannot be "
            "checked against a tree it does not describe." % name)
    if len(found) > 1:
        raise FreezeDriftError(
            "BATTERY_V1.md has %d `freeze:%s` blocks. Only one can be the "
            "record; the others would be checked by nothing."
            % (len(found), name))
    return found[0]


def _digests(block, name):
    """Parse `sha256:<hex>  <path>` lines, refusing a repeated path.

    A dict comprehension would let a second line for the same path overwrite the
    first, silently, in sorted position where it reads as a copy-paste artefact.
    """
    out = {}
    for digest, path in _DIGEST.findall(block):
        if path in out:
            raise FreezeDriftError(
                "%s appears twice in the `freeze:%s` block, with %s and %s. A "
                "repeated path means one of the two digests is checked by "
                "nothing." % (path, name, out[path], digest))
        out[path] = digest
    if not out:
        raise FreezeDriftError(
            "the `freeze:%s` block registers no digest." % name)
    return out


def read_record(path=RECORD):
    """Parse BATTERY_V1.md. The document is the record; there is no second copy."""
    if not os.path.exists(path):
        raise FreezeDriftError("no freeze record at %s" % path)
    # Normalised on read for the same reason the digests are: a record that
    # stops parsing because a checkout used CRLF would look like drift.
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    rec = {}
    for name, _bucket in BUCKETS:
        rec[name] = _digests(_block(text, name), name)

    prereg = _block(text, "prereg")
    reg = _digests(prereg, "prereg")
    if len(reg) != 1:
        raise FreezeDriftError(
            "the `freeze:prereg` block registers %d files; it must register "
            "exactly one." % len(reg))
    nbytes = re.findall(r"^prefix-bytes:\s*(\d+)\s*$", prereg, re.M)
    pdig = re.findall(r"^prefix-sha256:\s*(sha256:[0-9a-f]{64})\s*$", prereg, re.M)
    if len(nbytes) != 1 or len(pdig) != 1:
        raise FreezeDriftError(
            "the `freeze:prereg` block has %d prefix-bytes and %d prefix-sha256 "
            "lines; it must have exactly one of each, or the append-only check "
            "cannot run." % (len(nbytes), len(pdig)))
    path_, digest_ = list(reg.items())[0]
    rec["prereg"] = {"path": path_, "sha256": digest_,
                     "prefix_bytes": int(nbytes[0]), "prefix_sha256": pdig[0]}

    cut = re.findall(r"^cut-sha256:\s*([0-9a-f]{64})\s*$", text, re.M)
    if len(cut) != 1:
        raise FreezeDriftError(
            "BATTERY_V1.md has %d `cut-sha256:` lines; it must have exactly "
            "one." % len(cut))
    rec["cut"] = cut[0]
    return rec


# --- the check -----------------------------------------------------------

def _compare(name, bucket, want, root, fails):
    try:
        got = fingerprint(bucket, root)
    except FreezeDriftError as exc:
        fails.append(str(exc))
        return {}
    if len(want) != len(bucket):
        fails.append(
            "the `freeze:%s` block registers %d files but battery/freeze.py "
            "lists %d. The record and the code disagree about how much is "
            "frozen." % (name, len(want), len(bucket)))
    for rel in sorted(set(want) | set(got)):
        if rel not in want:
            fails.append(
                "%s is hashed by battery/freeze.py but absent from the "
                "`freeze:%s` block in BATTERY_V1.md — the record and the code "
                "disagree about what is frozen." % (rel, name))
        elif rel not in got:
            fails.append(
                "%s is in the `freeze:%s` block but battery/freeze.py no longer "
                "hashes it." % (rel, name))
    return got


def readings_drift(root=ROOT, record_path=RECORD):
    """Artefacts that no longer match the record. Reported, never fatal."""
    rec = read_record(record_path)
    want = rec["readings"]
    out = []
    for rel in sorted(READINGS):
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.exists(path):
            out.append(rel + " (missing)")
        elif sha256_file(path) != want.get(rel):
            out.append(rel)
    return out


def check(root=ROOT, record_path=RECORD):
    """Recompute everything the record gates. Returns a list of failure strings.

    Empty list means the freeze holds. Artefact drift is not in here by design —
    see `readings_drift`. Each string is written to be read by whoever broke it.
    """
    rec = read_record(record_path)
    fails = []

    for name, bucket in BUCKETS:
        got = _compare(name, bucket, rec[name], root, fails)
        if name not in GATED:
            continue
        for rel, digest in sorted(got.items()):
            if rel in rec[name] and rec[name][rel] != digest:
                fails.append(
                    "%s hashes to %s but %s says %s. A frozen file has been "
                    "edited in place. The numbers published under %s were "
                    "produced by the old file and cannot be compared with "
                    "numbers produced by the new one — register a new freeze "
                    "version (BATTERY_V2.md) instead of editing this one."
                    % (rel, digest, os.path.basename(record_path),
                       rec[name][rel], FREEZE_VERSION))

    for rel in unlisted(root):
        fails.append(
            "%s is under battery/ and no freeze bucket covers it. It can move a "
            "published number, or stop a test from objecting, from outside the "
            "freeze. Put it in a bucket (or in NARRATIVE) in battery/freeze.py "
            "and register it in a new freeze version." % rel)

    cut = os.path.join(root, CUT.replace("/", os.sep))
    if not os.path.exists(cut):
        fails.append("%s is missing; the pile cut cannot be verified." % CUT)
    else:
        try:
            from battery.guard import canonical_digest
            got = canonical_digest(json.load(open(cut, encoding="utf-8")))
        except Exception as exc:                       # unreadable is a failure
            fails.append("%s could not be digested: %s" % (CUT, exc))
            got = None
        if got is not None and got != rec["cut"]:
            fails.append(
                "%s has canonical digest %s but %s pins %s. The pile cut is a "
                "contract, not a reading: CLAUDE.md publishes this digest, and "
                "changing the cut after play has begun is an incident that must "
                "be recorded as one. The file's own sha256 field cannot catch "
                "this — it is rewritten by whoever rewrites the cut."
                % (CUT, got, FREEZE_VERSION, rec["cut"]))

    pre = rec["prereg"]
    path = os.path.join(root, pre["path"].replace("/", os.sep))
    if not os.path.exists(path):
        fails.append("%s is registered by the freeze but missing." % pre["path"])
        return fails
    got_prefix, total = sha256_prefix(path, pre["prefix_bytes"])
    if total < pre["prefix_bytes"]:
        fails.append(
            "%s is %d bytes, shorter than the %d frozen at %s. The "
            "pre-registration has been truncated; it is append-only."
            % (pre["path"], total, pre["prefix_bytes"], FREEZE_VERSION))
    elif got_prefix != pre["prefix_sha256"]:
        fails.append(
            "%s: the first %d bytes no longer hash to %s. A prediction has "
            "been edited after the fact, which is the one thing a "
            "pre-registration exists to prevent (PREDICTIONS.md:5). The "
            "original must stand, wrong, with the correction appended below it."
            % (pre["path"], pre["prefix_bytes"], pre["prefix_sha256"]))
    elif sha256_file(path) != pre["sha256"]:
        fails.append(
            "%s has grown since %s: the frozen prefix is intact, so nothing "
            "was rewritten, but predictions have been appended after the "
            "freeze. That is legitimate work and an illegitimate freeze — a "
            "prediction registered after the instrument was frozen needs a new "
            "freeze version (BATTERY_V2.md) recording when it arrived."
            % (pre["path"], FREEZE_VERSION))
    return fails


def verify(root=ROOT, record_path=RECORD):
    """Raise FreezeDriftError unless the tree matches the record."""
    fails = check(root, record_path)
    if fails:
        raise FreezeDriftError(
            "the battery freeze does not hold (%d):\n  - %s"
            % (len(fails), "\n  - ".join(fails)))
    return True


def render_blocks(root=ROOT):
    """The fenced blocks, as BATTERY_V1.md should carry them.

    Used to author the record and to re-author it for a new freeze version.
    Deliberately not wired to write the file: a freeze that a script can
    refresh in place is not a freeze.
    """
    out = []
    for name, bucket in BUCKETS:
        lines = ["```freeze:%s" % name]
        for rel, digest in sorted(fingerprint(bucket, root).items()):
            lines.append("%s  %s" % (digest, rel))
        lines.append("```")
        out.append("\n".join(lines))
    path = os.path.join(root, PREREG.replace("/", os.sep))
    digest = sha256_file(path)
    _, total = sha256_prefix(path, 0)
    prefix, _ = sha256_prefix(path, total)
    out.append("\n".join([
        "```freeze:prereg",
        "%s  %s" % (digest, PREREG),
        "prefix-bytes: %d" % total,
        "prefix-sha256: %s" % prefix,
        "```",
    ]))
    out.append("cut-sha256: %s" % canonical_cut(root))
    return "\n\n".join(out)


def canonical_cut(root=ROOT):
    from battery.guard import canonical_digest
    path = os.path.join(root, CUT.replace("/", os.sep))
    return canonical_digest(json.load(open(path, encoding="utf-8")))


if __name__ == "__main__":
    print(render_blocks())
