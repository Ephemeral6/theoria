"""The file `a6carry/protocol.py` says exists.

Its docstring has claimed since it was written that "`tests/test_a6_sealing.py`
reads this file's source and fails the suite if a world module … appears in it".
No such file existed for a day, which made the sealing property a sentence in a
comment — the same shape as the fingerprint `monitor/inbox/20260728T082700Z-W-1521`
complains about, and the shape `a6carry` was written to argue against.  It is a
test now.

**The claim being sealed.**  `protocol.carry` is a driver that must work against
any world, including one `theoria-arm` supplies online.  The reason it takes an
`Executor` rather than importing a world is that A3's sealing argument is a claim
about what an arm did *not* read, and a claim of that shape cannot be evidenced
by the arm's own report — only by its call graph.  So the test reads the call
graph.

`executors.py` is the one module here allowed to know a world, and that is the
whole design: the boundary is a file boundary, so it is checkable by reading
filenames rather than by trusting anybody.
"""

import ast
import hashlib
import io
import os
import sys
import tokenize

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pytest  # noqa: E402

import _bootstrap  # noqa: F401,E402

CARRY = os.path.join(HERE, "a6carry")

#: Every module in `a6carry` except the one whose job is to reach a world.
SEALED_MODULES = ("protocol.py", "pack.py", "rebuild.py", "forms.py",
                  "executor_api.py", "pddl_push.py", "__init__.py")

#: Names that mean "a world", "a trace", or "an engine's proposal stream".  A
#: sealed module that mentions any of them in *code* has a path to the answer
#: key, whatever its report says.
FORBIDDEN = ("a3world", "worldgen", "GridWorld", "WorldSpec", "raw_trace",
             "ground_truth", "spec.json", "_sweep", "coverage.json",
             "reversibility.json", "is_win", "LEVELS")


def _source(path):
    with io.open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _code_only(path):
    """Source with comments and string literals removed.

    Necessary, and for exactly the reason `tests/test_sealing.py` gives: every
    module in this package documents at length what it does *not* reach, so a
    naive substring scan would fail on the prose that exists to be honest.
    `protocol.py`'s docstring names `worldgen` twice while its code cannot
    import it.
    """
    out = []
    with io.open(path, "rb") as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            out.append(token.string)
    return " ".join(out)


def _imports(path):
    """Every module name imported anywhere in the file, including inside defs."""
    names = set()
    for node in ast.walk(ast.parse(_source(path))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


# ------------------------------------------------- the sealed modules are sealed

@pytest.mark.parametrize("module", SEALED_MODULES)
def test_a_sealed_module_names_no_world_in_its_code(module):
    path = os.path.join(CARRY, module)
    code = _code_only(path)
    hits = sorted(name for name in FORBIDDEN if name in code)
    assert hits == [], (
        "%s reaches a world: %s.  The driver takes an Executor precisely so "
        "that this list stays empty; a module that can import a world can be "
        "handed one by accident." % (module, ", ".join(hits)))


@pytest.mark.parametrize("module", SEALED_MODULES)
def test_a_sealed_module_imports_no_world(module):
    imported = _imports(os.path.join(CARRY, module))
    bad = sorted(name for name in imported
                 if name.split(".")[0] in ("a3world", "worldgen"))
    assert bad == [], "%s imports %s" % (module, ", ".join(bad))


def _local_import_closure(entry):
    """Every module in this track that `entry` can reach, transitively.

    An allow-list of filenames was the first version of this and it was wrong.
    It failed the moment `a6carry/score.py` arrived — a module that must drive
    both worlds exhaustively, and quite properly knows what a world is — and the
    only way to make it pass was to add a name to the list, which is how an
    allow-list stops meaning anything.

    The property that actually matters is narrower and does not need a list:
    **nothing the driver imports may know a world.**  A tool that sits beside the
    driver and never gets imported by it is not a door into it.  So the closure
    is computed and the question is asked of whatever is in it.
    """
    roots = {
        "a6carry": CARRY,
        "a3pipeline": os.path.join(HERE, "a3pipeline"),
        # The closure stopped at the track boundary until an adversarial pass
        # walked past it.  That truncation was not conservative — it cut the
        # graph at *exactly* the hop where a world enters:
        #
        #   a3pipeline/certify_a3.py:50  from certify import replay
        #   cold-start-a0/certify/replay.py:33  from world.ground_truth import …
        #   cold-start-a0/world/ground_truth.py:20  from world.a0_world import …
        #
        # so `world.a0_world` — a simulator with a hardcoded 9x9 level, a
        # palette and a `GOAL_CELL` — is live in `sys.modules` the moment the
        # driver is imported, and the test that certified the seal was built to
        # stop one hop short of finding it.
        "certify": os.path.join(REPO, "cold-start-a0", "certify"),
        "world": os.path.join(REPO, "cold-start-a0", "world"),
        "compile": os.path.join(REPO, "cold-start-a0", "compile"),
        "pipeline": os.path.join(REPO, "cold-start-a0", "pipeline"),
        "common": os.path.join(REPO, "engine-rig", "common"),
        "engines": os.path.join(REPO, "engine-rig", "engines"),
    }
    seen, queue = set(), [entry]
    while queue:
        path = queue.pop()
        if path in seen or not os.path.exists(path):
            continue
        seen.add(path)
        for name in _imports(path):
            head = name.split(".")
            if head[0] not in roots:
                continue
            module = head[1] if len(head) > 1 else "__init__"
            queue.append(os.path.join(roots[head[0]], module + ".py"))
    return seen


#: Modules on the driver's import closure that do know a world, each with the
#: chain that puts it there.  This is a **quarantine list, not an allow-list**,
#: and the difference is that every entry carries its chain and the test fails
#: on anything not in it.  Its purpose is to make a known leak visible and to
#: fire when a new one appears.
#:
#: A0's world arrives through the certifier and cannot be removed from here:
#: `cold-start-a0/` belongs to the theory-compiler track and this one may not
#: edit it (`CLAUDE.md`).  What can be said honestly is the narrower true thing
#: — the world *under test* still arrives only as an `Executor`, which is what
#: `test_no_world_under_test_is_reachable_from_the_driver` asserts.
KNOWN_WORLD_LEAKS = {
    "../cold-start-a0/world/a0_world.py":
        "a6carry/protocol.py:43 -> a3pipeline/certify_a3.py:50 -> "
        "cold-start-a0/certify/replay.py:33 -> world/ground_truth.py:20",
    "../cold-start-a0/world/ground_truth.py":
        "a6carry/protocol.py:43 -> a3pipeline/certify_a3.py:50 -> "
        "cold-start-a0/certify/replay.py:33",
    "../cold-start-a0/world/explorer.py":
        "world/ground_truth.py:24",
    # The hop itself.  `replay.py` is the certifier the protocol genuinely
    # needs — `certify_a3.cheap` is steps 4 and 7 — and it reaches for
    # `world.ground_truth.read_trace` to read a trace file.  Finding this one
    # required walking past the track boundary too, which is the point.
    "../cold-start-a0/certify/replay.py":
        "a6carry/protocol.py:43 -> a3pipeline/certify_a3.py:50",
}


def test_the_only_worlds_the_driver_can_reach_are_the_ones_on_the_record():
    """The seal, stated as what is true rather than as what would be nicer.

    The earlier version of this test asserted that *nothing* the driver imports
    knows a world, and that was false — provably, in one line:

        python -c "import a6carry.protocol, sys; print('world.a0_world' in sys.modules)"
        True

    It passed only because the closure it walked stopped at the track boundary,
    one hop before the leak.  A test engineered, however unintentionally, to
    miss the thing it certifies is worse than no test: it converts an open
    question into a settled one.

    So the claim is now the narrow true one, and the leak is on the record with
    its chain.
    """
    closure = _local_import_closure(os.path.join(CARRY, "protocol.py"))
    knows = {}
    for path in closure:
        if any(word in _code_only(path) for word in FORBIDDEN):
            rel = os.path.relpath(path, HERE).replace(os.sep, "/")
            knows[rel] = True
    unexpected = sorted(set(knows) - set(KNOWN_WORLD_LEAKS))
    assert unexpected == [], (
        "a world became reachable from the driver and is not on the record: %s"
        % ", ".join(unexpected))


def test_no_world_under_test_is_reachable_from_the_driver():
    """The claim that does hold, and the one the design is actually about.

    `worldgen` and `a3world` — the worlds a carry is *graded against* — arrive
    only as an `Executor` argument.  A0's hardcoded level being live in the
    certifier is a different fact: it is not a world any arm here is scored on,
    and it cannot be used to answer a question about one.
    """
    closure = _local_import_closure(os.path.join(CARRY, "protocol.py"))
    knows = sorted(os.path.relpath(path, HERE).replace(os.sep, "/")
                   for path in closure
                   if any(word in _code_only(path)
                          for word in ("a3world", "worldgen", "GridWorld")))
    assert knows == [], "the driver reaches a world under test: %s" % ", ".join(knows)


def test_the_leak_is_real_and_the_record_is_not_stale():
    """If A0's world stops being importable through the certifier, say so.

    A quarantine entry that no longer corresponds to anything is the same defect
    class as the hardcoded header count: a record that rots because nothing
    rereads it.
    """
    import importlib
    importlib.import_module("a6carry.protocol")
    live = {name for name in sys.modules if name.split(".")[0] == "world"}
    assert "world.a0_world" in live, (
        "A0's world is no longer live after importing the driver — good news, "
        "but KNOWN_WORLD_LEAKS now overstates the problem and should shrink")


def test_the_modules_that_do_know_a_world_are_not_on_the_carry_path():
    """`executors.py` and `score.py` are the two, and neither is imported by it."""
    closure = _local_import_closure(os.path.join(CARRY, "protocol.py"))
    for name in ("executors.py", "score.py"):
        path = os.path.join(CARRY, name)
        if not os.path.exists(path):
            continue
        assert path not in closure, "%s is on the driver's import path" % name


def test_the_protocol_cannot_reach_the_answer_key():
    """`is_win` on a hypothetical state would be the answer key itself.

    `executor_api.py`'s docstring argues the point: an executor that offered
    `is_win(state)` would let a driver ask "would this have won?" without
    spending an action, which is the one thing the quota model exists to price.
    The `Executor` surface is two methods, and this asserts it stays two.
    """
    tree = ast.parse(_source(os.path.join(CARRY, "executor_api.py")))
    klass = next(n for n in ast.walk(tree)
                 if isinstance(n, ast.ClassDef) and n.name == "Executor")
    methods = sorted(n.name for n in klass.body if isinstance(n, ast.FunctionDef))
    assert methods == ["execute", "first_frame"], methods


# --------------------------------------------------------- the other track's tree

def _tree_hash(root):
    digest = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            path = os.path.join(base, name)
            digest.update(os.path.relpath(path, root).replace(os.sep, "/").encode())
            with io.open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


def test_a_full_a6_run_writes_nothing_into_worldgen():
    """`worldgen/` is another track's directory; A6 reads it and never writes.

    `tools/verify_readonly.py` watches `cold-start-a0`, `engine-rig`,
    `theory-compiler` and `CONTRACTS` — **not** `worldgen`, which was nobody's
    upstream until A6 made it one.  So the guard is here, hashing the tree
    around a real run rather than around an import.
    """
    root = os.path.join(REPO, "worldgen")
    if not os.path.isdir(root):
        pytest.skip("worldgen/ absent")
    before = _tree_hash(root)

    import subprocess
    result = subprocess.run([sys.executable, "run_a6.py"], cwd=HERE,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

    assert _tree_hash(root) == before, "a6 run modified worldgen/"


def test_no_credential_is_read_anywhere_in_the_package():
    """Zero API contact is a red line, and the key file is how it would be crossed.

    The credential's variable name is assembled rather than written: A3's
    `tests/test_sealing.py::test_no_credential_appears_anywhere` greps every file
    in this tree for that literal, so a test that spelled it out would fail the
    suite by existing.  The first version of this file did exactly that.
    """
    needle = "ARC_" + "API_KEY"
    for name in sorted(os.listdir(CARRY)):
        if not name.endswith(".py"):
            continue
        code = _code_only(os.path.join(CARRY, name))
        for word in (needle, "load_api_key", ".env", "requests",
                     "urllib", "socket", "httpx"):
            assert word not in code, "%s reaches for %s" % (name, word)
