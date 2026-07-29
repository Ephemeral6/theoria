"""The executable form of LEDGER_FORMAT.md v1.0.

Append-only by construction: there is no update, rewrite or delete path in this
module. Corrections are new `incident` records.

Every record goes through `redact.VAULT.scrub()` on its way to disk, so a
credential cannot reach the file even if an arm put one in a request body.

Every record is also checked against `proxy/canon.py` first, so a spelling the
format forbids never reaches disk at all (F-16: this file is the canon). A
field the format merely does not *mention* is a different case and is written:
the writer runs after the request has been sent, so refusing a record cannot
un-send it, and the one time this module refused one it discarded a reply that
had already cost $2.695 (INC-TA-006). Those fields are counted in
`Ledger.unknown_fields` so a run can report them; see `proxy/CONTRACT_CHANGES.md`.
"""

import errno
import hashlib
import json
import os
import threading
import time
import warnings
from typing import Any, Dict, List, Optional

from . import LEDGER_VERSION
from . import canon
from .paths import LEDGER_PATH
from .redact import VAULT, scrub_keyish

EVENTS = frozenset({
    "env_step", "model_call", "run_start", "run_end",
    "env_meta", "guard_block", "incident",
})

ARMS = frozenset({
    "bare_cc", "schema_repro", "theoria", "probe", "replay", "mock_arm",
})

INCIDENT_KINDS = frozenset({
    "score_mismatch", "replay_mismatch", "nondeterminism",
    "credential_in_body", "bypass_attempt", "sealed_pile_request",
    # A run that could not be reconciled at all is not a run that reconciled.
    # baseline-arms lost 22 of 23 scorecards to a transient 404 and the loss
    # was silent; an obligation that cannot be discharged is an incident.
    "score_unreconciled",
    # The frozen scorer's source no longer hashes to its freeze record.
    "scorer_drift",
    # An upstream handed our credential back and the proxy removed it before
    # the arm saw it. The arm holding no key is the property; a reflection is
    # an attempt on it, whether or not anyone meant one.
    "credential_reflected",
    # The transport finished somewhere other than where it was aimed, or asked
    # to. Redirects are refused, so this should be unreachable -- which is the
    # state a security property is in right before it stops holding.
    "redirect_refused",
    # A model prompt named a sealed game. The cut's rule 2 counts reading about
    # a sealed game as contamination, and a prompt is a way to do that.
    "sealed_pile_in_prompt",
    # A line in the file is not a v1.0 record. The file is append-only, so it
    # cannot be removed; recording it is the only correction available.
    "ledger_unreadable_line",
    # The shared spend pool refused, so a request the arm made did not complete
    # or its response never reached the arm. INC-BA-003's whole complaint was
    # that a budget stop left no trace anyone else could see; a refusal that
    # only appears as a 500 to the arm is that again, one layer down.
    "spend_gate_refused",
    # A `win_tighten` rewrote a WIN because the game reported no score at all,
    # so it did not tighten the win condition -- it removed it, at every
    # requirement value. The variant is still unsolvable and the rewrite is
    # still the safe direction; what is wrong is that its unsolvability no
    # longer follows from the construction its `justification` names (D-032).
    "variant_degenerate",
})

_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()

#: How long a writer waits for the ledger's cross-process lock before refusing.
#: Same figure the spend pool uses, for the same reason: long enough that an
#: honest writer never sees it, short enough that a dead holder is noticed.
LOCK_TIMEOUT_SECONDS = 30.0

# The lock primitive, imported the way `spend_gate.py` imports it. Both are
# optional at import time and checked at use, so a platform with neither fails
# closed at the moment of writing rather than silently at import.
try:                                                        # POSIX
    import fcntl
except ImportError:                                         # pragma: no cover
    fcntl = None                                            # type: ignore[assignment]
try:                                                        # Windows
    import msvcrt
except ImportError:                                         # pragma: no cover
    msvcrt = None                                           # type: ignore[assignment]


class LedgerLockUnavailable(RuntimeError):
    """The writer could not take the ledger lock, so it did not write.

    Refusing is the whole point. An append that goes ahead without the lock is
    indistinguishable on disk from one that held it, the file is append-only, so
    it cannot be taken back, and the damage is exactly what this class exists to
    prevent: two writers on the same `seq`, one hash chain in two pieces.
    """


class _ChainLock:
    """Exclusive lock on one ledger file, held across read-tail → append.

    The same primitive, on the same reasoning, as `spend_gate._PoolLock`: a
    `threading.Lock` covers threads in one interpreter and nothing else, and the
    writers that actually collide here are separate OS processes -- two pytest
    sessions on 2026-07-28, and three arms sharing one ledger under item A10.
    `msvcrt` on Windows, `fcntl` on POSIX; this host has the former.

    The lock lives on a **sidecar** file (`<ledger>.lock`) rather than on the
    ledger itself, again following `_PoolLock`: the ledger is opened in append
    mode by writers and read whole by readers, and locking a byte range that two
    different open modes are touching is a portability problem nobody needs.
    """

    def __init__(self, path: str, timeout: float = LOCK_TIMEOUT_SECONDS):
        self.path = path
        self.timeout = timeout
        self._fh = None

    def __enter__(self) -> "_ChainLock":
        if fcntl is None and msvcrt is None:               # pragma: no cover
            raise LedgerLockUnavailable(
                "neither fcntl nor msvcrt is importable, so this process cannot "
                "take a cross-process lock on %s. Without it two writers read "
                "the same tail and both continue from it, which forks the hash "
                "chain into a stream whose provenance cannot be published. "
                "Refusing to append." % self.path)
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            # 'a+b' so the file is created if absent and never truncated.
            self._fh = open(self.path, "a+b")
            if os.fstat(self._fh.fileno()).st_size == 0:
                # Windows locks a byte range; give it a byte to lock.
                self._fh.write(b"L")
                self._fh.flush()
            self._fh.seek(0)
        except OSError as exc:
            raise LedgerLockUnavailable(
                "cannot open the ledger lock at %s: %s. An unlockable ledger is "
                "one two writers can fork; refusing to append."
                % (self.path, exc))

        deadline = time.time() + self.timeout
        delay = 0.005
        while True:
            try:
                self._acquire()
                return self
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    self._close()
                    raise LedgerLockUnavailable(
                        "locking the ledger at %s failed: %s" % (self.path, exc))
                if time.time() >= deadline:
                    self._close()
                    raise LedgerLockUnavailable(
                        "timed out after %.1fs waiting for the ledger lock at "
                        "%s. Another writer is holding it, or one died holding "
                        "it. Refusing to append rather than appending unlocked."
                        % (self.timeout, self.path))
                time.sleep(delay)
                delay = min(delay * 2, 0.25)

    def _acquire(self) -> None:
        fd = self._fh.fileno()                              # type: ignore[union-attr]
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            self._fh.seek(0)                                # type: ignore[union-attr]
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)          # type: ignore[union-attr]

    def _release(self) -> None:
        if self._fh is None:
            return
        fd = self._fh.fileno()
        try:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
            else:
                self._fh.seek(0)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)      # type: ignore[union-attr]
        except OSError:                                     # pragma: no cover
            pass

    def _close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            finally:
                self._fh = None

    def __exit__(self, *exc) -> None:
        self._release()
        self._close()


def canonical(obj: Any) -> str:
    """One JSON spelling per value, so a line's bytes are determined by its
    content and two writers cannot disagree."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha256(obj: Any) -> str:
    blob = obj if isinstance(obj, (bytes, bytearray)) else canonical(obj).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def utcnow() -> str:
    seconds = time.time()
    base = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
    return "%s.%03dZ" % (base, int((seconds % 1) * 1000))


def frame_hash(frames: Optional[List[Any]]) -> Optional[str]:
    """The unit of replay comparison. Hashes the frame list whole, so a command
    that returns seven frames is one hash, not seven."""
    if frames is None:
        return None
    return sha256(frames)


def _lock_for(path: str) -> threading.Lock:
    key = os.path.abspath(path)
    with _LOCKS_GUARD:
        if key not in _LOCKS:
            _LOCKS[key] = threading.Lock()
        return _LOCKS[key]


def line_hash(line: bytes) -> str:
    """The chain link: sha256 over one line's bytes as written, no terminator.

    Deliberately over *bytes*, not over a re-serialised record.  A verifier
    that re-canonicalises before hashing is really checking that today's
    `canonical()` agrees with the one that wrote the file -- so the day that
    function's behaviour changes, every ledger ever written goes red at once
    and the alarm means nothing.  Hashing the bytes on disk asks the only
    question worth asking: are these the bytes that were written?
    """
    return sha256(line)


def _scan_from(path: str, offset: int, seq: int = 0, prev: Optional[str] = None
               ) -> "tuple[int, int, Optional[str]]":
    """Fold the bytes after `offset` into a tail state.

    Returns `(offset now, last seq, hash of the last line)`. Reading from an
    offset rather than from the start is what keeps the fix affordable: the tail
    has to be re-read inside the lock before *every* append, and rescanning the
    whole file each time would make a shared campaign ledger quadratic in its own
    length -- 100k lines re-read 100k times. Folding is exact rather than
    approximate: `seq` is the maximum over every line seen so far and `prev` the
    last non-blank line seen so far, so scanning `[0, a)` then `[a, b)` gives
    precisely what scanning `[0, b)` gives.

    Read in binary in one pass, because the chain hashes bytes and decoding then
    re-encoding would be a second chance to disagree with the file.
    """
    if not os.path.exists(path):
        return 0, seq, prev
    with open(path, "rb") as fh:
        fh.seek(offset)
        for raw in fh:
            offset += len(raw)
            stripped = raw.rstrip(b"\r\n")
            if not stripped.strip():
                continue
            # An unreadable line still occupies its place in the chain (RED-44:
            # one bad line must not destroy the whole ledger), so it becomes the
            # predecessor before its seq is even looked at.
            prev = line_hash(stripped)
            try:
                seq = max(seq,
                          int(json.loads(stripped.decode("utf-8")).get("seq", 0)))
            except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
                continue
    return offset, seq, prev


def _tail_state(path: str) -> "tuple[int, Optional[str]]":
    """`(last seq, hash of the last line)` -- what a new writer must resume from."""
    _, seq, prev = _scan_from(path, 0)
    return seq, prev


class Ledger:
    """One ledger file. Safe against other threads *and other processes*.

    `seq` and `prev` are derived from the file inside a lock that spans the read
    of the tail and the append that follows it, so they are dense, monotonic and
    singly-linked no matter how many writers share the path.

    Both halves of that sentence were once false. The counter used to be seeded
    once in this constructor and guarded by a `threading.Lock` that did not span
    seed→append, so a writer that opened the file while another was mid-run
    resumed from a snapshot that was already invalid; both then emitted the same
    `seq` and the same `prev`, and the chain forked. One instance is on disk:
    `theoria-arm/runs/pytest-test_the_shell_turns_end_to_en0/ledger.jsonl`, seq
    137-143 written twice, `verify_chain` BREAK at line 144, and `--emit-head`
    consequently refusing to publish that stream's provenance. The regression is
    `tests/test_ledger_concurrency.py`, which forks the chain against the old
    writer using real OS processes.
    """

    def __init__(self, path: str = LEDGER_PATH,
                 lock_timeout: float = LOCK_TIMEOUT_SECONDS):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self._lock = _lock_for(path)
        #: `"<event>.<field>" -> count` for every field written to one of the
        #: two shapes that §3/§4 does not list. A warning on stderr is seen by
        #: whoever is watching at the time; this is seen by the run report.
        #: Empty is the normal state and the interesting one is non-empty.
        #: Per-file, and now per-file across *processes* too: the tally is this
        #: object's, so three arms sharing one ledger each keep their own.
        self.unknown_fields: Dict[str, int] = {}
        #: The sidecar the cross-process lock is taken on. Never written to
        #: beyond the single byte Windows needs to have a range to lock.
        self._lock_path = path + ".lock"
        self._lock_timeout = lock_timeout
        #: How far into the file this object has already read. A cache, not a
        #: source of truth: `_reseed_locked` re-derives from disk before every
        #: append and this only saves it from re-reading bytes it has seen.
        self._scan_pos = 0
        self._seq, self._prev = 0, None
        with self._lock:
            # Seeded here so a reader can ask cheaply, but no write ever uses
            # this value without re-deriving it under the lock first.
            self._scan_pos, self._seq, self._prev = _scan_from(path, 0)

    def _reseed_locked(self) -> None:
        """Bring `seq`/`prev` up to date with the file. Call under both locks.

        This is the fix in one method: whatever this object last believed, the
        numbers it is about to write are taken from the bytes on disk now, with
        no other writer able to add to them until the append is done.
        """
        size = os.path.getsize(self.path) if os.path.exists(self.path) else 0
        if size < self._scan_pos:
            # The file shrank, so it was truncated or replaced under us and the
            # cached state describes bytes that are no longer there. Re-read it
            # whole rather than resume from a position into a different file.
            self._scan_pos, self._seq, self._prev = 0, 0, None
        if size == self._scan_pos:
            return
        self._scan_pos, self._seq, self._prev = _scan_from(
            self.path, self._scan_pos, self._seq, self._prev)

    def _note_unknown(self, event: str, names: List[str], message: str) -> None:
        """Say it out loud, and *never* let saying it stop the write.

        `canon.check`'s default is `warnings.warn`, which is right for a
        validator and wrong here: a warning is an exception whenever the
        ambient filter says `error` -- `python -W error`, `PYTHONWARNINGS=error`,
        a hardened CI runner, or a `simplefilter("error")` left on by something
        earlier in the process. On this path that would raise inside the writer,
        after the request has been sent and the provider has been paid, and an
        arm's `except Exception` would record "the desk failed" and discard the
        reply. That is INC-TA-006 exactly, rebuilt out of the warning that was
        supposed to replace it. So the warning is emitted defensively and the
        tally, which cannot raise, is the durable half.
        """
        with self._lock:
            for name in names:
                key = "%s.%s" % (event, name)
                self.unknown_fields[key] = self.unknown_fields.get(key, 0) + 1
        try:
            warnings.warn(message, canon.UnknownField, stacklevel=4)
        except Exception:                       # noqa: BLE001 -- see docstring
            pass

    def append(self, event: str, run_id: str, arm: str, **fields: Any) -> Dict[str, Any]:
        if event not in EVENTS:
            raise ValueError("unknown event %r (LEDGER_FORMAT.md §3, §4, §6)" % event)
        if arm not in ARMS:
            # Still a hard refusal, and the reason it is not the after-the-money
            # refusal D-030 argues against: `arm` and `event` are fixed when the
            # RunLedger is constructed, so a wrong one fails on the run's very
            # first record -- before any request is sent and any dollar is spent.
            # A refusal that fires in the first second of a run is a typo caught;
            # a refusal that fires on record 40 is evidence destroyed.
            raise ValueError("unknown arm %r; register it in ledger.ARMS" % (arm,))
        unknown = canon.check(event, fields, on_unknown=self._note_unknown)
        if event == "env_step":
            # The writer computes this itself on every normal path; a caller
            # that supplies one has to supply the right one. A frame_hash that
            # does not hash its own frames makes every replay that consulted it
            # meaningless, and nothing downstream would notice (RED-41).
            expected = frame_hash(fields.get("frames"))
            if fields.get("frame_hash") != expected:
                raise canon.NonCanonicalField(
                    "frame_hash is %r but the frames on this record hash to %r. "
                    "The hash is the unit of replay comparison; a record that "
                    "disagrees with itself cannot be replayed against anything."
                    % (fields.get("frame_hash"), expected))
        record: Dict[str, Any] = {
            "v": LEDGER_VERSION,
            "event": event,
            "run_id": run_id,
            "arm": arm,
        }
        clean = VAULT.scrub(fields)
        if event != "model_call":
            # Environment traffic only. `model_call` keeps its bodies verbatim
            # (§4, D-005), and a long run of alphanumerics there is ordinary
            # model output; an arm putting a key in a *prompt* still raises a
            # `credential_in_body` incident at the proxy.
            clean = scrub_keyish(clean)
        elif unknown:
            # ...but the exemption is for `request` and `response`, which §4
            # *requires* verbatim. A field the format has never heard of
            # carries no such requirement, and additive-safe must not quietly
            # widen a hole the exemption was never drawn around: before S9 an
            # unlisted field on a model_call could not reach disk at all.
            clean = dict(clean)
            for name in unknown:
                clean[name] = scrub_keyish({name: clean[name]})[name]
        record.update(clean)
        # Threads first, then processes, always in that order so two writers can
        # never each hold one of the pair. The critical section spans the read of
        # the tail *and* the append: a seed taken outside it is a snapshot that
        # another writer may already have invalidated.
        with self._lock:
            with _ChainLock(self._lock_path, timeout=self._lock_timeout):
                self._reseed_locked()
                self._seq += 1
                record["seq"] = self._seq
                record["ts"] = utcnow()
                # The chain link, set under the same lock that assigns `seq` so
                # the two can never disagree about the order records were
                # written in. The first record of a file carries `null`: there
                # is nothing before it, and saying so explicitly distinguishes
                # "start of chain" from "chain field forgotten".
                record["prev"] = self._prev
                line = canonical(record)
                blob = line.encode("utf-8")
                with open(self.path, "a", encoding="utf-8", newline="") as fh:
                    fh.write(line)
                    fh.write("\n")
                self._prev = line_hash(blob)
                # Exactly the bytes this writer added -- computed rather than
                # re-stat'ed, so anything a writer outside the lock managed to
                # append still gets scanned next time round instead of being
                # skipped over.
                self._scan_pos += len(blob) + 1
        return record

    # -- reading -----------------------------------------------------------
    def read(self) -> List[Dict[str, Any]]:
        return read_ledger(self.path)


def read_ledger(path: str = LEDGER_PATH, strict: bool = True,
                rejected: Optional[List[Dict[str, Any]]] = None
                ) -> List[Dict[str, Any]]:
    """Read a ledger. §8: a reader rejects what it does not know.

    `strict=False` rejects the *line* instead of the *file*. The distinction
    matters because the file is append-only and anyone who can append can add
    one `{"v":"2.0"}` line — under strict reading that single line makes every
    record before it permanently unauditable, which turns an append-only log
    into a denial-of-service surface (RED-44). Non-strict readers still refuse
    to interpret the unknown line; they collect it in `rejected` so the caller
    can report it, and the frozen scorer turns it into a failed check rather
    than an exception.
    """
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                if strict:
                    raise ValueError("%s:%d is not JSON: %s" % (path, lineno, exc))
                if rejected is not None:
                    rejected.append({"line": lineno, "kind": "not_json",
                                     "detail": str(exc)})
                continue
            version = record.get("v")
            if version != LEDGER_VERSION:
                message = (
                    "%s:%d has ledger version %r, this reader knows %r. A reader "
                    "must reject what it does not know rather than guess "
                    "(LEDGER_FORMAT.md §8)." % (path, lineno, version, LEDGER_VERSION)
                )
                if strict:
                    raise ValueError(message)
                if rejected is not None:
                    rejected.append({"line": lineno, "kind": "unknown_version",
                                     "detail": message})
                continue
            out.append(record)
    return out


def records_for(run_id: str, path: str = LEDGER_PATH, event: Optional[str] = None):
    return [r for r in read_ledger(path)
            if r.get("run_id") == run_id and (event is None or r.get("event") == event)]


class RunLedger:
    """A ledger bound to one run: keeps the step and call counters, and derives
    the level boundaries that LEDGER_FORMAT.md §3 assigns to the ledger."""

    def __init__(self, ledger: Ledger, run_id: str, arm: str,
                 game_id: Optional[str] = None):
        self.ledger = ledger
        self.run_id = run_id
        self.arm = arm
        #: One run is one arm playing one game once, so the game is a property
        #: of the run and every record it writes can carry it. The Phase 2
        #: battery asked for this on `model_call`: without it a run that
        #: thought and never acted lands as `unknown`, and its guardrail can
        #: only filter model traffic by rejoining it to `env_step` records.
        self.game_id = game_id
        self._step_idx = -1
        self._call_idx = -1
        self._levels_completed = 0
        self._counter_lock = threading.Lock()

    def _next_step(self) -> int:
        with self._counter_lock:
            self._step_idx += 1
            return self._step_idx

    def _next_call(self) -> int:
        with self._counter_lock:
            self._call_idx += 1
            return self._call_idx

    def _append(self, event: str, **fields: Any) -> Dict[str, Any]:
        return self.ledger.append(event, self.run_id, self.arm, **fields)

    @property
    def unknown_fields(self) -> Dict[str, int]:
        """Fields written to the two shapes that §3/§4 does not list.

        Counted per *file*, not per run: one `Ledger` can hold many runs, and
        the tally is the writer's. In the normal case -- one run, one file --
        the distinction does not arise, and when it does, over-reporting is the
        safe direction for a notice.
        """
        return dict(self.ledger.unknown_fields)

    # -- the two shapes ----------------------------------------------------
    def env_step(self, game_id: str, action: Dict[str, Any],
                 frames: Optional[List[Any]] = None, *,
                 card_id: Optional[str] = None, guid: Optional[str] = None,
                 state: Optional[str] = None, score: Optional[int] = None,
                 levels_completed: Optional[int] = None,
                 variant: Optional[Dict[str, Any]] = None,
                 guard: Optional[Dict[str, Any]] = None,
                 http: Optional[Dict[str, Any]] = None,
                 step_idx: Optional[int] = None,
                 **extra: Any) -> Dict[str, Any]:
        idx = self._next_step() if step_idx is None else step_idx

        # Level derivation. `levels_completed` before the step is the level the
        # step happened on; an increase means the step ended a level.
        before = self._levels_completed
        after = before if levels_completed is None else int(levels_completed)
        boundary = bool(after > before)
        self._levels_completed = after

        # `status` is always present, null when unknown. A reader must be able
        # to tell "the command failed" from "nobody wrote down whether it did".
        http = dict(http or {})
        http.setdefault("status", None)

        return self._append(
            "env_step",
            game_id=game_id,
            card_id=card_id,
            guid=guid,
            step_idx=idx,
            action=action,
            frames=frames,
            n_frames=0 if frames is None else len(frames),
            frame_hash=frame_hash(frames),
            state=state,
            score=score,
            levels_completed=levels_completed,
            level=before,
            level_boundary=boundary,
            variant=variant,
            guard=guard or {"decision": "allow"},
            http=http,
            **extra,
        )

    def model_call(self, provider: str, model: str, *,
                   request: Any = None, response: Any = None,
                   usage: Optional[Dict[str, Any]] = None,
                   pricing_ref: Optional[Dict[str, Any]] = None,
                   step_idx: Optional[int] = None,
                   game_id: Optional[str] = None,
                   http: Optional[Dict[str, Any]] = None,
                   **extra: Any) -> Dict[str, Any]:
        # `canon.check` refuses `cost`/`cost_usd` along with the rest of the
        # non-canonical vocabulary, and says what to write instead.
        return self._append(
            "model_call",
            call_idx=self._next_call(),
            provider=provider,
            model=model,
            request=request,
            response=response,
            # Copied, not coerced: `dict(usage)` on something that is not a
            # mapping would either raise a confusing error or invent a shape,
            # and canon.check is the thing that should be saying no here.
            usage=dict(usage) if isinstance(usage, dict) else (
                {} if usage is None else usage),
            pricing_ref=pricing_ref,
            step_idx=step_idx,
            game_id=game_id if game_id is not None else self.game_id,
            http=http or {},
            **extra,
        )

    # -- auxiliaries -------------------------------------------------------
    def run_start(self, **fields: Any) -> Dict[str, Any]:
        return self._append("run_start", **fields)

    def run_end(self, **fields: Any) -> Dict[str, Any]:
        return self._append("run_end", **fields)

    def env_meta(self, **fields: Any) -> Dict[str, Any]:
        return self._append("env_meta", **fields)

    def guard_block(self, **fields: Any) -> Dict[str, Any]:
        return self._append("guard_block", **fields)

    def incident(self, kind: str, detail: Any, **fields: Any) -> Dict[str, Any]:
        if kind not in INCIDENT_KINDS:
            raise ValueError("unknown incident kind %r" % kind)
        return self._append("incident", kind=kind, detail=detail, **fields)
