"""The exchange format, checked by something that does not know the producer.

`tests/test_interop.py` checks the certificate documents with
`certificate_export.verify()` -- the producer's own module, iterating the
producer's own witness list. `tests/test_recheck.py` checks the *weights*, but
it gets them by hand-transcription into `recheck/cases/*.cert.json`, and
`recheck` refuses an `obligations` key at load, so it never reads the exchange
document at all. Between the two, nothing in this rig had ever loaded a file
from `interop/certificates/` and adjudicated it as an outsider would.

That is what this file does, and the sharpest test in it is
`test_the_omission_forgery_passes_the_producer_and_fails_the_reader`: a
certificate whose weights break the invariant, with the two witnesses that would
have shown it deleted and every remaining field made internally consistent. It
passes `certificate_export.verify()` -- which is not a bug in that function but
the gap its own docstring, `DECISIONS.md` D-035 and `interop/README.md` all name
-- and `interop/pagoda_reader.py` rejects it, because the reader grounds the
move relation instead of reading it.
"""

import copy
import json
import os
import subprocess
import sys

import pytest

from engines.lp_potential.potential import solve_certificate
from interop import certificate_export as ce
from interop import export_certificates
from interop import pagoda_reader
from interop import peg1d

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.dirname(HERE)
REPO = os.path.dirname(RIG)
CERT_DIR = os.path.join(RIG, "interop", "certificates")
READER = os.path.join(RIG, "interop", "pagoda_reader.py")

COMMITTED = sorted(
    os.path.join(CERT_DIR, name)
    for name in os.listdir(CERT_DIR) if name.endswith(".json")
)


@pytest.fixture(scope="module")
def document():
    """The 5-cell case, straight from the engine -- not read off disk.

    The round trip has to start at the producer or it is not a round trip.
    """
    goals = ["01000"]
    graph = peg1d.build_graph(5, "11011", goal_states=goals)
    certificate = solve_certificate(graph, "11011", goal_states=goals,
                                    bound=export_certificates.BOUND)
    assert certificate is not None
    return ce.build(certificate, graph, claim_name="unsolvable_11011_to_01000")


# ------------------------------------------------------------------ round trip

def test_the_committed_certificates_rebuild_byte_for_byte():
    """The artefacts on disk are reproducible from the engine that proved them.

    Before this, no script in the tree produced `interop/certificates/*.json`;
    the only record of a regeneration was a prose line in another run's
    manifest. An exchange artefact nobody can rebuild is an exchange artefact
    nobody can audit.
    """
    assert export_certificates.regenerate(check_only=True) == []


def test_round_trip_engine_to_file_to_independent_reader(tmp_path, document):
    """Engine -> export -> disk -> a reader that imports none of the above."""
    path = ce.write(document, str(tmp_path / "cert.json"))
    reloaded = pagoda_reader.load(path)
    assert reloaded == document
    assert pagoda_reader.check(reloaded) == []


@pytest.mark.parametrize("path", COMMITTED, ids=os.path.basename)
def test_every_committed_certificate_is_accepted(path):
    assert pagoda_reader.check(pagoda_reader.load(path)) == []


@pytest.mark.parametrize("path", COMMITTED, ids=os.path.basename)
def test_exhaustive_search_agrees_with_every_accepted_certificate(path):
    """The second opinion, on boards small enough to settle by enumeration.

    A valid pagoda implies unreachability, so this can never strengthen an
    accepted certificate -- it can only catch a bug in the reader. `recheck`
    carries the same cross-check for the same reason.
    """
    document = pagoda_reader.load(path)
    opinion = pagoda_reader.second_opinion(document)
    assert opinion is not None
    assert opinion["goal_reachable"] is False


# ----------------------------------------------------------- the independence

FORBIDDEN_IMPORTS = ("engines", "interop", "recheck", "common", "fixtures",
                     "tools", "numpy", "scipy")


def test_the_reader_imports_nothing_from_this_rig():
    """Independence as a property of the text, not of a docstring.

    Both the strip and the deferred-import ban are load-bearing: an adversarial
    pass built a backdoored copy whose `import engines` sat one level indented
    inside `check()`, and the first version of this test -- which matched on the
    unstripped line -- never saw it.
    """
    with open(READER, encoding="utf-8") as handle:
        source = handle.read()
    lines = source.splitlines()
    imports = [line.strip() for line in lines
               if line.strip().startswith(("import ", "from "))]
    assert imports, "no import lines found; did the file move?"
    for line in imports:
        module = line.split()[1].split(".")[0]
        assert module not in FORBIDDEN_IMPORTS, \
            "%r makes the reader a client of the producer" % line
    body = source.split('"""', 2)[2]
    for dodge in ("importlib", "__import__"):
        assert dodge not in body, \
            "%s can import at run time, which the line scan cannot see" % dodge


def test_the_reader_names_the_producer_fields_it_refuses_to_read():
    """The refusal is a list, so deleting a name is a deliberate act.

    Counted quote-agnostically: the same adversarial pass reached a producer
    field as `document['obligations']`, which a double-quoted-only count misses.
    """
    with open(READER, encoding="utf-8") as handle:
        body = handle.read().split('"""', 2)[2]
    for field in pagoda_reader.PRODUCER_OPINION:
        mentions = body.count('"%s"' % field) + body.count("'%s'" % field)
        assert mentions == 1, \
            "%r is read somewhere below the docstring" % field


def test_the_reader_runs_alone_in_an_empty_directory(tmp_path, document):
    """Copy one file out of the rig and it still adjudicates.

    `-I` is isolated mode: no `PYTHONPATH`, no user site directory. With `cwd`
    set to a directory holding nothing but the reader and a certificate, an
    import of anything in this rig would be an `ImportError`, so a clean exit
    is the structural claim rather than a promise about one.
    """
    lone = tmp_path / "pagoda_reader.py"
    lone.write_bytes(open(READER, "rb").read())
    cert = tmp_path / "cert.json"
    cert.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")

    done = subprocess.run(
        [sys.executable, "-I", "pagoda_reader.py", "cert.json"],
        cwd=str(tmp_path), capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert "ACCEPTED" in done.stdout

    forged = json.loads(cert.read_text(encoding="utf-8"))
    forged["weights_integer"][2] += 5
    forged.pop("weights_rational")
    cert.write_text(json.dumps(forged, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", "pagoda_reader.py", "cert.json"],
        cwd=str(tmp_path), capture_output=True, text=True)
    assert done.returncode == 1
    assert "REJECTED" in done.stdout


def test_the_cli_separates_a_refusal_from_a_misuse(tmp_path):
    done = subprocess.run([sys.executable, READER], capture_output=True,
                          text=True)
    assert done.returncode == 2, "a usage error must not read as a rejection"


@pytest.mark.parametrize("content", [
    "[1, 2, 3]",                                    # a top-level array
    '{"schema": "lp_potential/pagoda_certificate@1"',   # truncated JSON
    "",                                             # empty file
], ids=["array", "truncated", "empty"])
def test_a_malformed_file_is_not_reported_as_a_refuted_certificate(tmp_path,
                                                                   content):
    """Exit 2, not 1. A crash is a statement about the checker, not the claim.

    Before this, `main` ran the reachability cross-check on documents `check`
    had already condemned, so a file missing `initial_state` raised `KeyError`
    and Python's own exit status 1 -- byte-identical, to a caller reading only
    the exit code, with "this certificate is refuted".
    """
    bad = tmp_path / "bad.json"
    bad.write_text(content, encoding="utf-8")
    done = subprocess.run([sys.executable, READER, str(bad)],
                          capture_output=True, text=True)
    assert done.returncode == 2, done.stdout + done.stderr
    assert "REJECTED" not in done.stdout


def test_a_document_missing_its_fields_is_refused_without_a_traceback(tmp_path):
    """The same hazard from the library side: `check` returns, never raises."""
    for document in ({"schema": pagoda_reader.SCHEMA, "n_pos": 5},
                     {"schema": pagoda_reader.SCHEMA, "n_pos": 5,
                      "initial_state": "110", "goal_states": ["01000"],
                      "weights_integer": [1, 1, 1, 1, 1],
                      "initial_potential": 0},
                     [1, 2, 3], None, "not a document"):
        assert pagoda_reader.check(document)


# ---------------------------------------------------------- negative samples

def test_a_tampered_weight_is_rejected(document):
    forged = copy.deepcopy(document)
    forged["weights_integer"][2] += 5
    reasons = pagoda_reader.check(forged)
    assert reasons
    assert any("inv_closed" in reason for reason in reasons)


def test_a_lowered_bound_is_rejected(document):
    """`initial_potential` is the declared bound, so lowering it must bite.

    `certificate_export.build` writes the bound *as* potential(initial), which
    makes the producer's own `inv_init` read "x <= x" -- its docstring says so.
    Reading the field as a declaration rather than recomputing it is what turns
    that obligation back into a check.
    """
    forged = copy.deepcopy(document)
    forged["initial_potential"] -= 1
    reasons = pagoda_reader.check(forged)
    assert any("inv_init" in reason for reason in reasons)


def test_a_goal_that_no_longer_breaks_the_invariant_is_rejected(document):
    forged = copy.deepcopy(document)
    forged["goal_states"] = ["10000"]
    reasons = pagoda_reader.check(forged)
    assert any("goal_break" in reason for reason in reasons)


def test_a_goal_whose_potential_equals_the_bound_is_rejected(document):
    """The boundary, pinned. `>` and `>=` are one character apart and not alike.

    An adversarial pass mutated `goal_break` from `value <= bound` to
    `value < bound` and the suite stayed green, because every negative sample
    used a goal strictly under the bound. That mutant is not cosmetic: it issues
    thousands of accepted-but-reachable documents, the worst found being a
    6-cell board whose goal is four jumps away with potential exactly equal to
    the bound. A goal state that merely ties the bound is still admitted by
    `I(s) := potential(s) <= b`, so it proves nothing.
    """
    forged = copy.deepcopy(document)
    weights = forged["weights_integer"]
    bound = forged["initial_potential"]
    tied = [state for state in ("01000", "00100", "10000", "00010", "00001")
            if pagoda_reader.potential(weights, state) == bound]
    assert tied, "no single-peg state ties the bound; pick another board"
    forged["goal_states"] = [tied[0]]
    reasons = pagoda_reader.check(forged)
    assert any("goal_break" in reason for reason in reasons), \
        "a goal whose potential equals the bound was accepted"


def test_a_foreign_schema_is_rejected_without_guessing(document):
    forged = copy.deepcopy(document)
    forged["schema"] = "ic3_pdr/inductive_invariant_certificate@1"
    reasons = pagoda_reader.check(forged)
    assert len(reasons) == 1 and "schema" in reasons[0]


def test_a_truncated_weight_vector_is_rejected_before_any_arithmetic(document):
    """A short vector must not be scored as zeros in the missing cells."""
    forged = copy.deepcopy(document)
    forged["weights_integer"] = forged["weights_integer"][:-1]
    reasons = pagoda_reader.check(forged)
    assert any("weights_integer" in reason for reason in reasons)


def test_a_certificate_against_no_goals_is_rejected(document):
    forged = copy.deepcopy(document)
    forged["goal_states"] = []
    assert any("proves nothing" in reason
               for reason in pagoda_reader.check(forged))


def test_rationals_that_disagree_with_the_integers_are_rejected(document):
    """The forger who edits one weight vector and forgets the other."""
    forged = copy.deepcopy(document)
    forged["weights_integer"] = [w * 2 for w in forged["weights_integer"]]
    forged["weights_integer"][0] += 1
    assert any("weights_rational" in reason or "multiple" in reason
               for reason in pagoda_reader.check(forged))


def test_a_legal_certificate_still_passes_after_all_of_that(document):
    """The control. A checker that rejects everything rejects nothing."""
    assert pagoda_reader.check(copy.deepcopy(document)) == []


# --------------------------------------------------------- the omission forgery

def omission_forgery(document):
    """A certificate that breaks the invariant with the evidence deleted.

    `w[2]` goes from 0 to -1. Two of the six jumps then raise the potential --
    `jump(1,2,3)` and `jump(3,2,1)`, both by 1 -- and both witnesses are
    removed. Everything else is made to agree: the remaining four witnesses are
    recomputed, `n_checked` and `checked_over` are corrected to say four, and
    `weights_rational` is edited to match, so the document is internally
    consistent and self-consistently wrong.

    The bound is untouched because it does not move: potential(11011) is
    w0+w1+w3+w4, and `w[2]` is not in it. Nor does the goal: potential(01000)
    is w1. So `inv_init` and `goal_break` both still hold, and the only broken
    obligation is the one whose evidence was deleted.
    """
    forged = copy.deepcopy(document)
    forged["weights_integer"][2] = -1
    forged["weights_rational"][2] = "-1"
    weights = forged["weights_integer"]

    kept = []
    for witness in forged["obligations"]["inv_closed"]["witnesses"]:
        src, over, dst = witness["positions"]
        delta = weights[dst] - weights[src] - weights[over]
        if delta > 0:
            continue
        witness.update({"w_src": weights[src], "w_over": weights[over],
                        "w_dst": weights[dst], "delta": delta, "holds": True})
        kept.append(witness)
    forged["obligations"]["inv_closed"].update({
        "witnesses": kept,
        "n_checked": len(kept),
        "checked_over": "the %d move instances this document lists" % len(kept),
    })
    return forged


def test_the_omission_forgery_passes_the_producer_and_fails_the_reader(document):
    """The whole reason this reader exists, as one assertion pair."""
    forged = omission_forgery(document)

    assert len(forged["obligations"]["inv_closed"]["witnesses"]) == 4
    assert len(document["obligations"]["inv_closed"]["witnesses"]) == 6
    # The producer's verifier iterates the document's own list, so deleting an
    # entry deletes the check. This is the documented gap, pinned here so that
    # closing it later shows up as a failing test rather than as silence.
    assert ce.verify(forged) == []

    reasons = pagoda_reader.check(forged)
    assert reasons, "the reader accepted a document with a broken invariant"
    raised = sorted(reason for reason in reasons if "inv_closed" in reason)
    assert len(raised) == 2
    assert "jump(1,2,3)" in raised[0] and "raises the potential by 1" in raised[0]
    assert "jump(3,2,1)" in raised[1]


def test_the_forgery_is_not_caught_by_the_obligations_block_being_short(document):
    """Rule out the cheap explanation: the reader never opens that block.

    If the rejection came from noticing four witnesses where six were expected,
    it would be reading the producer's account again -- and a forger who padded
    the list back to six would walk through. Deleting the block entirely must
    change nothing.
    """
    forged = omission_forgery(document)
    stripped = copy.deepcopy(forged)
    stripped.pop("obligations")
    stripped.pop("verified")
    stripped.pop("conclusion")
    assert pagoda_reader.check(stripped) == pagoda_reader.check(forged)

    honest = copy.deepcopy(document)
    honest.pop("obligations")
    honest.pop("verified")
    honest.pop("conclusion")
    assert pagoda_reader.check(honest) == []


# ------------------------------------------- the forgery that certifies a lie

#: An omission forgery whose *conclusion* is false, not merely unproven.
#: Weights `[-4, -4, 4, 0, 4]` on the same 5-cell board: only `jump(0,1,2)`
#: raises the potential, and it raises it by 12. Delete that one witness and the
#: producer's verifier sees five well-behaved moves. But `jump(0,1,2)` is legal
#: in `11011` and lands exactly on the goal -- `00111` is one jump away.
LIE = {
    "schema": "lp_potential/pagoda_certificate@1",
    "claim": "unsolvable_11011_to_00111",
    "conclusion": "no goal state is reachable from 11011",
    "produced_by": "engine-rig/engines/lp_potential",
    "n_pos": 5,
    "initial_state": "11011",
    "goal_states": ["00111"],
    "weights_integer": [-4, -4, 4, 0, 4],
    "initial_potential": -4,
    "verified": True,
}


def test_the_producer_certifies_a_falsehood_and_the_reader_refuses_it():
    """The strong form of the argument, found by attacking the weak one.

    `test_the_omission_forgery_...` shows the reader catching a broken proof of
    a claim that happens to be *true* -- `01000` really is unreachable from
    `11011`. That understates what is at stake. Here the omitted move is the
    move that reaches the goal, so `certificate_export.verify()` returns clean
    on a document whose headline conclusion is false, and the gap it leaves is
    not "an unproven true claim" but a certified falsehood.
    """
    weights = LIE["weights_integer"]
    witnesses = []
    for src, over, dst in pagoda_reader.jump_moves(5):
        delta = weights[dst] - weights[src] - weights[over]
        if delta > 0:
            continue                       # the forger deletes exactly this one
        witnesses.append({
            "move": "jump(%d,%d,%d)" % (src, over, dst),
            "positions": [src, over, dst], "w_src": weights[src],
            "w_over": weights[over], "w_dst": weights[dst],
            "delta": delta, "holds": True})
    forged = dict(LIE)
    forged["obligations"] = {
        "inv_init": {"statement": "potential(initial) <= -4", "value": -4,
                     "holds": True},
        "inv_closed": {
            "statement": "every legal move has delta <= 0",
            "checked_over": "the %d move instances this document lists"
                            % len(witnesses),
            "n_checked": len(witnesses), "witnesses": witnesses,
            "holds": True},
        "goal_break": {
            "statement": "every goal state has potential > -4",
            "witnesses": [{"goal_state": "00111", "potential": 8,
                           "exceeds_initial_by": 12, "holds": True}],
            "holds": True},
    }
    assert len(witnesses) == 5, "expected exactly one raising move"

    # The producer's verifier: clean.
    assert ce.verify(forged) == []

    # The world: the goal is one jump from the start.
    assert "00111" in peg1d.reachable_from("11011")
    opinion = pagoda_reader.second_opinion(forged)
    assert opinion["goal_reachable"] is True

    # The reader: refused, naming the move that was deleted.
    reasons = pagoda_reader.check(forged)
    assert len(reasons) == 1
    assert "jump(0,1,2) raises the potential by 12" in reasons[0]


def test_the_second_opinion_tracks_real_reachability():
    """Pin the cross-check itself; an unexercised cross-check checks nothing.

    Both a stubbed `second_opinion` that always answers `False` and one that
    never searches at all used to survive the whole suite, because every
    assertion in it ran on certificates whose goals are unreachable.
    """
    for start in ("11011", "1110", "11111", "10101"):
        n = len(start)
        expected = set(peg1d.reachable_from(start))
        document = {"n_pos": n, "initial_state": start,
                    "goal_states": sorted(expected)[:1]}
        opinion = pagoda_reader.second_opinion(document)
        assert opinion["n_reachable"] == len(expected)
        assert opinion["goal_reachable"] is True
    assert pagoda_reader.second_opinion({"n_pos": 10 ** 6}) is None


# ------------------------------------------------------------------ the anchor

CONSUMER = os.path.join(REPO, "theory-compiler", "src", "theory_compiler",
                        "certificate.py")


def test_the_consumer_side_names_the_schema_we_stamp():
    """The far half of the bridge, pinned by this rig's own suite.

    Read-only, and the same move `recheck/anchors.py` already makes on that
    track's tree (D-030: it reads there and writes nothing). Until now the only
    thing asserting the bridge was consumed was `monitor/scan.py`'s probe; a
    handshake that only the monitor checks is a handshake neither track notices
    breaking.
    """
    if not os.path.exists(CONSUMER):
        pytest.skip("theory-compiler tree not present")
    with open(CONSUMER, encoding="utf-8") as handle:
        source = handle.read()
    assert 'SCHEMA = "%s"' % pagoda_reader.SCHEMA in source, \
        "the consumer no longer pins the schema id this rig stamps"
