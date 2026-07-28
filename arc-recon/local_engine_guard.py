"""Fail-closed guard over the local engine: `environment_files/` and the runners that fill it.

WHY THIS EXISTS. `ACCESS_CHECK.md` §8a.1 concluded, correctly, that caching ARC
data locally for our own analysis is *permitted* and needs no permission. That
sentence is about licensing. It says nothing about what lands in the cache, and
the other half of the same finding is in `browser-ops/TERMS.md` §4.2:

  * first run "download the game source", cached in `environment_files/`
    (docs.arcprize.org/arc-prize-2026);
  * `make list-games` -- "Print every game id available";
  * `make play-local` -- "Runs your agent against every game in the dataset";
  * `make verify-local` -- "30-second smoke test on two games" (which two is
    not stated);
  * the swarm runner's `--game` filter: "If not specified, the agent plays all
    available games" (docs.arcprize.org/swarms).

So the first thing anyone does after reading "permitted, no permission needed"
pulls all 25 games' SOURCE onto disk and, by default, plays all 25. By
INC-BA-001's own yardstick source ranks *worse* than trajectories: it hands over
the finished answer to the mechanics. Permission is not containment, and the
containment half has to be executable or it is a note somebody did not read.

WHAT IT REFUSES. The whitelist is positive and the default is deny, in the shape
`baseline-arms/SCHEMA_PATH_A.md` §3 settled on -- and for the reason it gives:
a negative list meets an unforeseen path shape and fails *open*, and failing
open here is not revocable.

  1. A game-playing or game-pulling command with no `--game` selector is
     refused as `deny_default_all`. Defaulting to every game is the documented
     upstream behaviour, so silence is the dangerous case, not the safe one.
  2. A selector token that is not exactly a development-pile full id or its
     4-character prefix is refused -- `deny_sealed` if it names one of the 21,
     `deny_unknown` otherwise. Sealed is tested FIRST, so a command naming both
     piles reads as sealed. A selector flag with an empty or missing value is
     `deny_unknown` too: with last-wins flag semantics `--game=x --game=` is an
     empty filter, i.e. all 25, wearing the costume of a filtered run.
  3. `make play-local`, `make list-games` and `make verify-local` are refused
     outright as `deny_unfiltered`: NO filter argument is documented for any of
     them. `--game` is documented only for the swarm runner. See
     UNFILTERABLE_TARGETS for why `GAME=ar25` does not rescue `play-local`.
  4. Any command, trigger or not, that names a sealed game anywhere is refused,
     case-insensitively. `arc.make("ls20")` is not a `make` target and has no
     `--game` flag; neither does `curl .../tasks/LS20`.
  5. If `data/piles.json` is missing, unreadable, or no longer hashes to the
     value `CLAUDE.md` pins, EVERYTHING is refused. A guard that cannot read
     the cut does not know what it is guarding.

A command line is split into SEGMENTS on `&&`, `||`, `;`, `|`, `&`, newline and
a `#` comment, and each segment is judged on its own; the most severe verdict
wins. Without that, `make play-local GAME=ar25 && make play-local` passes,
because one dev-pile token anywhere on a flattened line satisfies the filter
check for every trigger on it. Quote characters are stripped before splitting --
they carry no meaning here, and leaving them in let `"#"` hide a separator.

The prefix match is boundary-anchored on both sides, so `blobs/9ar25f0e/` does
not read as `ar25` -- the failure SCHEMA_PATH_A §3.1 found the hard way.

WHAT IT DOES NOT DO. It never opens, decodes, prints, or summarises a single
byte of anything under `environment_files/`. `scan` walks NAMES only -- files
and directories both, since an interrupted download leaves a sealed directory
with nothing in it. Downloading is not reading: as long as no model has read
those bytes the sealed discipline holds, and a guard that quoted the file it was
refusing would be the leak.

AND WHAT IT IS NOT. It is a pre-flight, not a sandbox. A process that never
calls it can still run anything; `scan` is the after-the-fact detector for that
case, and it is in `verify.sh` for exactly that reason.

USAGE

    python local_engine_guard.py check -- make play-local                 # exit 2
    python local_engine_guard.py check -- uv run main.py --agent=x        # exit 2
    python local_engine_guard.py check -- uv run main.py --agent=x --game=ar25
    python local_engine_guard.py run   -- <argv...>   # vet, then exec if allowed
    python local_engine_guard.py scan  <dir>...       # names-only sweep of a cache
    python local_engine_guard.py selftest             # offline, no arguments

Exit codes follow the canary's convention so a scheduler can read them:
0 allowed / clean, 2 REFUSED on sealed-pile grounds, 1 the guard itself could
not run (which is also a refusal -- nothing was executed).

Offline by construction: stdlib only, no network, no API key, no import of any
client code.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
PILES_PATH = os.path.join(HERE, "data", "piles.json")

# The value CLAUDE.md pins. It is the hash of the document with its own "sha256"
# key removed (a file cannot contain its own hash), canonicalised the same way
# `baseline-arms/SCHEMA_PATH_A.md` §1.1 recomputed it.
DECLARED_CUT_SHA256 = (
    "3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a"
)

# Verdicts. Exactly one is permissive, which is the point.
ALLOW = "allow"
DENY_SEALED = "deny_sealed"
DENY_UNKNOWN = "deny_unknown"
DENY_DEFAULT_ALL = "deny_default_all"
DENY_UNFILTERED = "deny_unfiltered"

# Most severe first -- used to combine per-segment verdicts.
SEVERITY = {
    DENY_SEALED: 4,
    DENY_UNFILTERED: 3,
    DENY_DEFAULT_ALL: 2,
    DENY_UNKNOWN: 1,
    ALLOW: 0,
}


class LocalEngineRefusal(Exception):
    """Refused: this would touch the sealed pile, or might, and we cannot tell."""


# --------------------------------------------------------------------------
# The cut. Fail-closed: any doubt about piles.json refuses everything.
# --------------------------------------------------------------------------


def cut_digest(doc: Dict[str, Any]) -> str:
    """The declared-hash recipe: drop the self-referential key, canonicalise, sha256."""
    body = {k: v for k, v in doc.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_piles(path: Optional[str] = None) -> Dict[str, Any]:
    # Resolved at call time, not bound as a default: a default argument would
    # freeze the path at import and the guard would keep reading a cut that had
    # since been moved out from under it.
    path = path if path is not None else PILES_PATH
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except OSError as exc:
        raise LocalEngineRefusal(
            "cannot read the pile cut at %s (%s). Refusing every local-engine "
            "path: a guard that cannot read the cut does not know what it is "
            "guarding." % (path, exc)
        )
    except ValueError as exc:
        raise LocalEngineRefusal("the pile cut at %s is not valid JSON (%s)" % (path, exc))

    for key in ("dev_pile", "sealed_pile"):
        if not isinstance(doc.get(key), list) or not doc[key]:
            raise LocalEngineRefusal("the pile cut at %s has no usable %r" % (path, key))

    actual = cut_digest(doc)
    declared = doc.get("sha256")
    if actual != DECLARED_CUT_SHA256 or declared != DECLARED_CUT_SHA256:
        raise LocalEngineRefusal(
            "the pile cut no longer hashes to the value CLAUDE.md pins "
            "(recomputed %s, file declares %s, pinned %s). piles.json rule 3: "
            "any change after a game has been played invalidates the cut and is "
            "an incident. Refusing everything until a human adjudicates."
            % (actual[:16], str(declared)[:16], DECLARED_CUT_SHA256[:16])
        )
    return doc


def _prefix(game_id: str) -> str:
    return game_id.split("-")[0]


def piles_index(doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    doc = doc if doc is not None else load_piles()
    dev = list(doc["dev_pile"])
    sealed = list(doc["sealed_pile"])
    return {
        "dev": dev,
        "sealed": sealed,
        "dev_prefix": {_prefix(g): g for g in dev},
        "sealed_prefix": {_prefix(g): g for g in sealed},
    }


# --------------------------------------------------------------------------
# Name classification -- the only thing that ever looks at a game id.
# --------------------------------------------------------------------------

# Boundary-anchored on both sides. ARC ids are alphanumeric, so the guard
# against `blobs/9ar25f0e/` is "no alphanumeric may abut the prefix". Matching
# is case-insensitive: `tasks/LS20` names a sealed game just as well as
# `tasks/ls20`, and rule 4 is meant to be a catch-all.
_BOUNDARY = "[0-9a-zA-Z]"


def names_game(text: str, game_id: str) -> bool:
    """Does `text` name this game, by full id or by its 4-character prefix?"""
    for token in (game_id, _prefix(game_id)):
        pattern = r"(?<!%s)%s(?!%s)" % (_BOUNDARY, re.escape(token), _BOUNDARY)
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def classify_name(text: str, idx: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Classify an arbitrary string (a path, a CLI token). Sealed is tested first.

    Returns (verdict, detail). Naming nothing is `deny_unknown`, not `allow`:
    the whitelist is positive.
    """
    idx = idx if idx is not None else piles_index()
    for sealed in idx["sealed"]:
        if names_game(text, sealed):
            return DENY_SEALED, sealed
    hits = [g for g in idx["dev"] if names_game(text, g)]
    if hits:
        return ALLOW, ",".join(sorted(hits))
    return DENY_UNKNOWN, "names no game in the cut"


def classify_selector_token(token: Any, idx: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Classify one `--game=` token. Must be an exact dev id or its exact prefix.

    Deliberately stricter than `classify_name`: upstream treats the value as an
    ID *prefix*, so a loose token like `s` would filter to several games at once
    and five of those are sealed. Only the two exact forms are allowed through.
    """
    idx = idx if idx is not None else piles_index()
    if not isinstance(token, str):
        return DENY_UNKNOWN, "selector value %r is not a string" % (token,)
    tok = token.strip().strip("\"'").strip().lower()
    if not tok:
        return DENY_UNKNOWN, (
            "empty selector value. With last-wins flag semantics an empty "
            "--game is no filter at all, i.e. all 25 games"
        )
    if tok in idx["sealed"] or tok in idx["sealed_prefix"]:
        return DENY_SEALED, idx["sealed_prefix"].get(tok, tok)
    if tok in idx["dev"]:
        return ALLOW, tok
    if tok in idx["dev_prefix"]:
        return ALLOW, idx["dev_prefix"][tok]
    return DENY_UNKNOWN, (
        "%r is neither a development-pile id nor its 4-character prefix; "
        "upstream reads it as an ID prefix, which may widen to sealed games" % tok
    )


# --------------------------------------------------------------------------
# Command classification.
# --------------------------------------------------------------------------

# Targets with NO documented filter argument. All three are refused outright.
#
# `play-local` is here on the adversarial review's finding, and the reasoning is
# worth keeping: `GAME=` / `GAMES=` / `-g` are spellings this guard invented.
# The only evidence we hold (browser-ops/TERMS.md §4.2, quoting the docs with
# URLs) documents `--game` for the SWARM RUNNER only, and documents
# `make play-local` as "Runs your agent against every game in the dataset" with
# no argument at all. GNU make accepts an unreferenced variable override in
# silence, so if the Makefile does not consume `GAME`, `make play-local
# GAME=ar25` plays all 25 while looking filtered -- and looking filtered is
# worse than looking dangerous. The same logic that refuses `verify-local` for
# an unnamed pair condemns `play-local` for an unverified variable.
UNFILTERABLE_TARGETS = {
    "play-local": (
        "`make play-local` is documented as \"Runs your agent against every game "
        "in the dataset\" and NO filter argument is documented for it -- `--game` "
        "is documented only for the swarm runner. `GAME=ar25` is a spelling we "
        "invented; make accepts an unreferenced variable silently, so if the "
        "Makefile ignores it this plays all 25 while looking filtered. Use the "
        "swarm runner with an explicit `--game=`, or land the Makefile in the "
        "tree and show it honours a named variable first."
    ),
    "list-games": (
        "`make list-games` is documented as \"Print every game id available\" -- "
        "it enumerates all 25 by design and takes no filter. We already hold the "
        "ids in data/piles.json; read those instead."
    ),
    "verify-local": (
        "`make verify-local` is documented as a \"30-second smoke test on two "
        "games\" and the docs do not say which two. An unnamed pair cannot be "
        "checked against the cut."
    ),
}

_WORD = r"(?<![0-9a-zA-Z_-])%s(?![0-9a-zA-Z_-])"

# Commands that pull game source or play games. Matched per segment,
# case-insensitively. Deliberately generous: a false refusal costs a retype, a
# false allow costs the confirmation set.
_TRIGGERS = (
    (_WORD % "environment_files", "touches the environment_files/ cache"),
    # The target NAME anywhere, not `make\s+<target>`: `make -C agents play-local`
    # and `gmake play-local` are ordinary, and anchoring on `make ` missed both.
    (_WORD % "play-local", "`play-local` runs every game in the dataset"),
    (_WORD % "list-games", "`list-games` enumerates every game"),
    (_WORD % "verify-local", "`verify-local` plays two unnamed games"),
    (r"(?<![0-9a-zA-Z_-])g?make\b[^\n]*?(?<![0-9a-zA-Z_-])play(?![0-9a-zA-Z_-])",
     "a make target that runs the local engine"),
    # The swarm runner. `main.py` ALONE is the trigger: it already denies by
    # default when unfiltered, and requiring `--agent` too meant `uv run main.py`
    # -- the quickstart minus one flag -- sailed through.
    (r"(?<![0-9a-zA-Z_.-])main\.py(?![0-9a-zA-Z])", "the swarm runner defaults to every available game"),
    (r"-m\s+[\w.]*main(?![0-9a-zA-Z_])", "the swarm runner defaults to every available game"),
    (_WORD % r"swarms?\w*", "the swarm runner defaults to every available game"),
    (_WORD % r"swarm[_-]?runner\w*", "the swarm runner defaults to every available game"),
    # The toolkit. `arc_agi` alone never fired for the package's real name,
    # `arc_agi_3`, because the lookahead excluded `_` and digits.
    (r"(?<![0-9a-zA-Z_.-])arc[_-]agi\w*", "the local toolkit downloads game source on first use"),
    (r"(?<![0-9a-zA-Z_.])Arcade\s*\(", "the local toolkit downloads game source on first use"),
    (r"(?<![0-9a-zA-Z_.])arc\.make\s*\(", "arc.make() instantiates a game locally"),
)

# `--game`, `--games`, `-g`, `-a`-style short forms, and Makefile `GAME=`.
_FLAG = re.compile(r"^(?:--games?|-g|GAMES?)(?:=(.*))?$", re.IGNORECASE)
_SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||&|\n")


def _as_text(command: Sequence[Any] | str) -> str:
    if isinstance(command, str):
        return command
    if isinstance(command, (bytes, bytearray)):
        raise LocalEngineRefusal("refusing to classify a bytes command; decode it first")
    try:
        parts = list(command)
    except TypeError:
        raise LocalEngineRefusal("refusing to classify a non-command value %r" % (command,))
    for part in parts:
        if not isinstance(part, str):
            raise LocalEngineRefusal(
                "refusing: command element %r is not a string, so it cannot be "
                "checked against the cut" % (part,)
            )
    return " ".join(parts)


def segments(text: str) -> List[str]:
    """Split a command line into independently-judged segments.

    Quote characters are removed first: they carry no meaning for this guard,
    and leaving them in let `"#"` smuggle a comment marker past the splitter.
    """
    plain = text.replace('"', "").replace("'", "")
    plain = re.split(r"(?:^|\s)#", plain)[0]        # a comment ends the line
    return [seg for seg in _SEGMENT_SPLIT.split(plain) if seg.strip()]


def selector_scan(text: str) -> Dict[str, Any]:
    """Pull every `--game`-ish value out of one segment.

    Returns {"tokens": [...], "malformed": [...]}. A flag with an empty or
    missing value lands in `malformed`, because dropping it silently is how
    `--game=ar25 --game=` came to look like a filtered run.
    """
    words = text.replace('"', "").replace("'", "").split()
    tokens: List[str] = []
    malformed: List[str] = []
    i = 0
    while i < len(words):
        word = words[i]
        match = _FLAG.match(word)
        if not match:
            i += 1
            continue
        inline = match.group(1)
        if inline is not None:
            values = [v for v in inline.split(",")]
            if not any(v.strip() for v in values):
                malformed.append(word)
            tokens.extend(v.strip() for v in values if v.strip())
            i += 1
            continue
        # Spaced form: consume every following non-flag word, not just the
        # first -- an nargs="+" flag's second value was never being classified.
        j = i + 1
        taken = 0
        while j < len(words) and not words[j].startswith("-"):
            tokens.extend(v.strip() for v in words[j].split(",") if v.strip())
            taken += 1
            j += 1
        if taken == 0:
            malformed.append(word)
        i = j
    return {"tokens": tokens, "malformed": malformed}


def selector_tokens(text: str) -> List[str]:
    return selector_scan(text)["tokens"]


def _classify_segment(text: str, idx: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "segment": text.strip(),
        "verdict": ALLOW,
        "reasons": [],
        "triggers": [],
        "selector": [],
    }

    # Rule 4 first: naming a sealed game is fatal whatever the command is.
    for sealed in idx["sealed"]:
        if names_game(text, sealed):
            result["verdict"] = DENY_SEALED
            result["reasons"].append(
                "names sealed game %s. piles.json rule 1: the sealed pile is not "
                "played, inspected, or read about." % sealed
            )
            return result

    triggers = [why for pattern, why in _TRIGGERS if re.search(pattern, text, re.IGNORECASE)]
    result["triggers"] = list(dict.fromkeys(triggers))
    if not result["triggers"]:
        result["reasons"].append("not a local-engine path; this guard has no opinion on it")
        return result

    for target, why in UNFILTERABLE_TARGETS.items():
        if re.search(_WORD % re.escape(target), text, re.IGNORECASE):
            result["verdict"] = DENY_UNFILTERED
            result["reasons"].append(why)
            return result

    scan = selector_scan(text)
    result["selector"] = scan["tokens"]
    if scan["malformed"]:
        result["verdict"] = DENY_UNKNOWN
        result["reasons"].append(
            "selector flag(s) %s carry no value. An empty --game is not a narrow "
            "filter, it is no filter -- all 25 games."
            % ", ".join(repr(m) for m in scan["malformed"])
        )
        return result
    if not scan["tokens"]:
        result["verdict"] = DENY_DEFAULT_ALL
        result["reasons"].append(
            "no --game selector. Upstream documents the default as \"the agent "
            "plays all available games\" / \"every game in the dataset\", so an "
            "unfiltered run is a run over all 25 -- 21 of them sealed. Name the "
            "development-pile games explicitly: %s" % ", ".join(idx["dev"])
        )
        return result

    for token in scan["tokens"]:
        verdict, detail = classify_selector_token(token, idx)
        if verdict != ALLOW:
            result["verdict"] = verdict
            result["reasons"].append("selector token %r: %s" % (token, detail))
            return result

    result["reasons"].append(
        "every selector token resolves inside the development pile: %s"
        % ", ".join(scan["tokens"])
    )
    return result


def classify_command(
    command: Sequence[Any] | str, idx: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Decide whether a command line may run. One permissive verdict, four refusals.

    Each shell segment is judged alone and the most severe verdict wins: one
    dev-pile token must not license the other statements sharing the line.
    """
    idx = idx if idx is not None else piles_index()
    text = _as_text(command)

    parts = segments(text) or [text]
    judged = [_classify_segment(part, idx) for part in parts]
    worst = max(judged, key=lambda r: SEVERITY.get(r["verdict"], 0))

    return {
        "command": text,
        "verdict": worst["verdict"],
        "reasons": worst["reasons"],
        "triggers": worst["triggers"],
        "selector": worst["selector"],
        "segments": judged,
    }


def assert_command_allowed(command: Sequence[Any] | str) -> None:
    """Raise unless the command is filtered down to the development pile."""
    result = classify_command(command)
    if result["verdict"] != ALLOW:
        raise LocalEngineRefusal(
            "REFUSED (%s): %s\n  command: %s"
            % (result["verdict"], "; ".join(result["reasons"]), result["command"])
        )


def assert_local_pull_allowed(game_ids: Optional[Sequence[Any]]) -> List[str]:
    """Programmatic entry point for anything that pulls game source.

    `None` or an empty sequence is the default-all case and is refused: callers
    that mean "all our games" must say which four.
    """
    idx = piles_index()
    # Materialise FIRST. A generator object is always truthy, so `if not
    # game_ids` skipped the refusal for `(g for g in cfg if want(g))` -- the
    # bracket-less twin of a safe list comprehension -- and returned an empty
    # allowlist, i.e. no filter, i.e. all 25. Failing open, invisibly, at the
    # call site.
    if game_ids is None:
        items: List[Any] = []
    elif isinstance(game_ids, str):
        raise LocalEngineRefusal(
            "REFUSED: pass a sequence of game ids, not the single string %r -- a "
            "bare string would be iterated character by character" % game_ids
        )
    else:
        try:
            items = list(game_ids)
        except TypeError:
            raise LocalEngineRefusal("REFUSED: %r is not a sequence of game ids" % (game_ids,))

    if not items:
        raise LocalEngineRefusal(
            "REFUSED (%s): a pull with no game list defaults to all 25. Name the "
            "development-pile games explicitly: %s"
            % (DENY_DEFAULT_ALL, ", ".join(idx["dev"]))
        )
    resolved: List[str] = []
    for token in items:
        verdict, detail = classify_selector_token(token, idx)
        if verdict != ALLOW:
            raise LocalEngineRefusal("REFUSED (%s): %r -- %s" % (verdict, token, detail))
        resolved.append(detail)
    return resolved


# --------------------------------------------------------------------------
# Cache sweep -- names only, never contents.
# --------------------------------------------------------------------------


def scan_paths(names: Sequence[str], idx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Classify a list of path strings. Nothing is opened; this is a name sieve."""
    idx = idx if idx is not None else piles_index()
    entries = []
    counts = {ALLOW: 0, DENY_SEALED: 0, DENY_UNKNOWN: 0}
    for name in names:
        verdict, detail = classify_name(name, idx)
        counts[verdict] = counts.get(verdict, 0) + 1
        entries.append({"path": name, "verdict": verdict, "detail": detail})
    return {
        "entries": entries,
        "counts": counts,
        "clean": counts.get(DENY_SEALED, 0) == 0 and counts.get(DENY_UNKNOWN, 0) == 0,
    }


def scan_dir(root: str, idx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sweep a cache path by name. Never reads a byte of any file.

    Directories are classified as well as files: an interrupted download leaves
    `environment_files/<sealed-id>/` with nothing in it, and a files-only walk
    called that clean.
    """
    if os.path.isfile(root):
        report = scan_paths([os.path.basename(root)], idx)
        report["root"] = root
        report["exists"] = True
        return report
    if not os.path.isdir(root):
        return {"root": root, "exists": False, "entries": [], "counts": {}, "clean": True}

    names: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(dirnames) + sorted(filenames):
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            names.append(rel.replace(os.sep, "/"))
    report = scan_paths(names, idx)
    report["root"] = root
    report["exists"] = True
    return report


# --------------------------------------------------------------------------
# Self-test. Runs offline, asserts the properties the guard is claimed to have.
# --------------------------------------------------------------------------


def selftest() -> List[str]:
    """Return a list of failures; empty means the guard holds its own claims."""
    failures: List[str] = []
    idx = piles_index()

    def expect(label: str, got: str, want: str) -> None:
        if got != want:
            failures.append("%s: got %s, want %s" % (label, got, want))

    def refuses(label: str, command: str) -> None:
        if classify_command(command)["verdict"] == ALLOW:
            failures.append("%s: %r was ALLOWED" % (label, command))

    # 1. Every sealed game, in every plausible shape, is refused.
    for sealed in idx["sealed"]:
        for template in (
            "uv run main.py --agent=random --game=%s",
            'python -c \'arc.make("%s")\'',
            "ls environment_files/%s",
            "curl https://arcprize.org/tasks/%s",
        ):
            expect("sealed %s" % sealed, classify_command(template % sealed)["verdict"], DENY_SEALED)
            expect(
                "sealed prefix %s" % sealed,
                classify_command(template % _prefix(sealed))["verdict"],
                DENY_SEALED,
            )
            expect(
                "sealed upper %s" % sealed,
                classify_command(template % sealed.upper())["verdict"],
                DENY_SEALED,
            )

    # 2. The development pile passes on the one runner that documents a filter.
    for dev in idx["dev"]:
        expect(
            "dev %s" % dev,
            classify_command("uv run main.py --agent=x --game=%s" % dev)["verdict"],
            ALLOW,
        )
        expect(
            "dev prefix %s" % dev,
            classify_command("uv run main.py --agent=x --game=%s" % _prefix(dev))["verdict"],
            ALLOW,
        )

    # 3. Silence, and every make invocation form, is refused.
    for bare in (
        "make play-local",
        "make -C ARC-AGI-3-Agents play-local",
        "gmake play-local",
        "make -f Makefile list-games",
        "make play-local GAME=ar25",
        "uv run main.py --agent=random",
        "uv run main.py",
        "python -m agents.main --agent=x",
        "python -c 'import arc_agi_3'",
        "python swarm_runner.py --agent=random",
    ):
        refuses("unfiltered", bare)

    # 4. One dev token must not license the rest of the line.
    refuses("chained", "uv run main.py --agent=x --game=ar25 && uv run main.py")
    refuses("commented", "uv run main.py --agent=x #--game=ar25")
    refuses("empty selector", "uv run main.py --agent=x --game=ar25 --game=")

    # 5. Boundary anchoring: a prefix buried in a hash must not read as a game.
    if classify_name("blobs/9ar25f0e/data.bin", idx)[0] == ALLOW:
        failures.append("boundary anchoring failed: 9ar25f0e read as ar25")

    # 6. The two piles' prefixes are disjoint -- prefix matching is only safe if so.
    overlap = set(idx["dev_prefix"]) & set(idx["sealed_prefix"])
    if overlap:
        failures.append("dev and sealed prefixes overlap: %s" % sorted(overlap))
    for dp in idx["dev_prefix"]:
        for sp in idx["sealed_prefix"]:
            if dp.startswith(sp) or sp.startswith(dp):
                failures.append("prefix %r and %r are nested" % (dp, sp))

    # 7. Both piles named at once reads as sealed.
    expect(
        "mixed selector",
        classify_command("uv run main.py --agent=x --game=ar25,ls20")["verdict"],
        DENY_SEALED,
    )

    # 8. A generator must not fail open.
    try:
        assert_local_pull_allowed(g for g in [])
        failures.append("an empty generator was allowed through assert_local_pull_allowed")
    except LocalEngineRefusal:
        pass
    return failures


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

_USAGE = """usage:
  local_engine_guard.py check   [--json] -- <command argv...>
  local_engine_guard.py run     [--json] -- <command argv...>
  local_engine_guard.py scan    [--json] <directory>...
  local_engine_guard.py selftest [--json]

exit: 0 allowed/clean, 2 REFUSED, 1 the guard could not run"""


def _split_argv(argv: List[str]) -> Tuple[bool, List[str]]:
    """Read the guard's own flags, which are only the ones BEFORE `--`.

    Stripping `--json` from anywhere would eat it out of the child command:
    `run -- mytool --json` must still pass `--json` to mytool.
    """
    if "--" in argv:
        cut = argv.index("--")
        head, tail = argv[:cut], argv[cut + 1:]
        return "--json" in head, tail
    return "--json" in argv, [a for a in argv if a != "--json"]


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(_USAGE)
        return 1
    mode, rest = argv[0], argv[1:]
    as_json, rest = _split_argv(rest)

    try:
        if mode == "selftest":
            failures = selftest()
            if as_json:
                print(json.dumps({"failures": failures, "ok": not failures}, indent=2))
            else:
                for line in failures:
                    print("FAIL " + line)
                print("selftest: %s" % ("green" if not failures else "%d FAILURES" % len(failures)))
            return 0 if not failures else 2

        if mode in ("check", "run"):
            if not rest:
                print(_USAGE)
                return 1
            result = classify_command(rest)
            if as_json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print("%s: %s" % (result["verdict"].upper(), result["command"]))
                for reason in result["reasons"]:
                    print("  - " + reason)
            if result["verdict"] != ALLOW:
                if not as_json:
                    print(
                        "\nNothing was executed. Filter to the development pile "
                        "and try again."
                    )
                return 2
            if mode == "run":
                # stdout/stderr are inherited: the guard passes the child through
                # rather than reading it. It refuses content, it does not relay it.
                return subprocess.call(rest)
            return 0

        if mode == "scan":
            if not rest:
                print(_USAGE)
                return 1
            reports = [scan_dir(root) for root in rest]
            clean = all(r["clean"] for r in reports)
            if as_json:
                print(json.dumps(reports, indent=2, sort_keys=True))
            else:
                for report in reports:
                    if not report.get("exists"):
                        print("scan %s: absent -- nothing cached, nothing to refuse"
                              % report["root"])
                        continue
                    for entry in report["entries"]:
                        if entry["verdict"] != ALLOW:
                            print("%s  %s  (%s)"
                                  % (entry["verdict"], entry["path"], entry["detail"]))
                    print(
                        "scan %s: %d allow, %d sealed, %d unknown"
                        % (
                            report["root"],
                            report["counts"].get(ALLOW, 0),
                            report["counts"].get(DENY_SEALED, 0),
                            report["counts"].get(DENY_UNKNOWN, 0),
                        )
                    )
                if not clean:
                    print(
                        "\nREFUSED. Files naming sealed games are cached here. Nothing "
                        "was opened -- this is a name sieve. Do not read them; record "
                        "an incident and delete the cache."
                    )
            return 0 if clean else 2

        print(_USAGE)
        return 1

    except LocalEngineRefusal as exc:
        print("REFUSED: %s" % exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
