"""The shared spend gate: one pool, one lock, one sum.

INC-BA-003 is the reason this file exists. Two Claude Code sessions started two
campaigns ninety seconds apart against one ARC key and one Anthropic bill. Both
had budget gates. Both gates were correct. Both were counters inside a process,
so neither could see the other, and the worst-case combined exposure was $214.9
that nobody had authorised as a total. One of the three damages is not
repairable: the variance envelope was measured under the other campaign's
four-process load, so its `http/action` and wall-clock figures carry contention
and cannot be compared with the M4 pilot's unit costs. That measurement was
paid for and cannot be re-bought at the same price.

`arc-recon/data/incidents.jsonl` INC-011 then recorded the same shape on a
$1.3544 measurement and called it, in its own words, a *standing hazard*.

The fix is not another convention. A convention failed here in the way
conventions fail: the second session obeyed every rule it knew about --
including the pile cut -- and the rule it needed did not exist to be known.
What works is what the sealed-pile guard does: be a function on the first line
of the path that spends, so that obeying is not a thing anyone has to remember.

    pool ceiling  --  a number a human wrote down, in spend_policy.json
    reservation   --  a claim on part of the pool, visible to every other
                      process before it starts
    record        --  what was actually spent, appended under an OS file lock
    the check     --  reads the GLOBAL sum, never this process's own counter

Three properties, and each is a test:

  * **Atomic.** Read-sum-append happens inside one exclusive file lock, so two
    processes cannot both observe the same headroom and both take it.
  * **Global.** Every query sums the whole ledger, every campaign, every
    session. A gate that reads its own counter is the defect, not the fix.
  * **Fail-closed, with no optional form.** No `enabled` flag, no environment
    variable, no `gate=None`. Missing lock primitive, unreadable policy,
    unwritable ledger, corrupt line, expired or absent reservation -- every one
    of them refuses egress and raises. There is no path through this module
    that silently allows.

Usage:

    from proxy.spend_gate import SpendGate

    gate = SpendGate()
    res = gate.reserve("phase3-variance-envelope", usd_cap=50.0, action_cap=2600)
    try:
        gate.check(res, usd=0.0, actions=1)      # before the money is spent
        ...                                       # spend it
        gate.record(res, usd=0.0217, actions=1)   # after, always
    finally:
        gate.release(res)

`SPEND_GATE.md` is the interface document and says how each track plugs in.
"""

import errno
import hashlib
import json
import os
import socket
import time
import uuid
from typing import Any, Dict, List, Optional

GATE_VERSION = "1.0"

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def main_checkout(start: str) -> Optional[str]:
    """The main worktree's root, if `start` is a linked worktree of one.

    A linked worktree has a `.git` **file** holding `gitdir: <path>`, and that
    path is `<main>/.git/worktrees/<name>`. Returns None for a normal checkout
    or anything unrecognised.
    """
    marker = os.path.join(start, ".git")
    if not os.path.isfile(marker):
        return None
    try:
        line = open(marker, encoding="utf-8").readline().strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    gitdir = os.path.abspath(os.path.join(start, line[len("gitdir:"):].strip()))
    parts = gitdir.replace("\\", "/").split("/")
    if len(parts) < 4 or parts[-3] != ".git" or parts[-2] != "worktrees":
        return None
    return os.path.dirname(os.path.dirname(os.path.dirname(gitdir)))


#: Where a *relative* ledger path in the policy resolves to.
#:
#: Not `REPO`, and the difference is the whole property. `proxy/var/` is
#: gitignored, so the ledger never travels with a branch; and CLAUDE.md
#: *instructs* every agent to work in `.worktrees/<id>/`. Resolved against the
#: importing checkout, "one shared pool" would have been **one pool per
#: worktree** -- 51 of them on this machine at the time of writing, each
#: carrying the full $214.90 ceiling, for a combined authorised exposure of
#: $10,959.90. That is INC-BA-003 reproduced exactly, by the very convention
#: meant to keep sessions out of each other's way, and it would have been
#: undetectable afterwards because `fingerprint()` reports the path *relative*
#: to REPO -- byte-identical provenance for two runs against two different
#: pools.
#:
#: So a relative ledger resolves against the **main checkout**, which every
#: linked worktree of this repository can find and which they all agree on.
POOL_ROOT = main_checkout(REPO) or REPO

#: Tracked. The pool ceiling is a number a human wrote down, so it lives in a
#: file review can see, not in an environment variable a process can set.
DEFAULT_POLICY_PATH = os.path.join(HERE, "spend_policy.json")

#: There is deliberately no environment variable that relocates the ledger.
#: A pool everyone can point somewhere else is a pool of one.
#: Tests pass a `SpendPolicy` object in-process instead.

# -- the one dependency, and the first way this module fails closed ----------
try:                                                        # POSIX
    import fcntl
except ImportError:                                         # pragma: no cover
    fcntl = None                                            # type: ignore[assignment]
try:                                                        # Windows
    import msvcrt
except ImportError:                                         # pragma: no cover
    msvcrt = None                                           # type: ignore[assignment]


class SpendGateError(RuntimeError):
    """Base. Every subclass means egress was refused."""


class SpendGateUnavailable(SpendGateError):
    """The gate could not do its job, so nothing may be spent.

    Raised for a missing lock primitive, an unreadable or malformed policy, an
    unwritable ledger, or a ledger line this reader cannot interpret. Every one
    of these is a case where a permissive fallback would be indistinguishable,
    from the caller's side, from a working gate.
    """


class SpendGateTripped(SpendGateError):
    """A cap was reached. Carries the totals that reached it."""

    def __init__(self, message: str, rule: str, totals: Dict[str, Any]):
        super().__init__(message)
        self.rule = rule
        self.totals = totals


class NoReservation(SpendGateError):
    """Nobody claimed headroom for this spend, or the claim has expired."""


# -- canonical serialisation -------------------------------------------------
# Local rather than imported from `.ledger`: the whole point of this module is
# that it is the first thing on the spending path, so it depends on as little
# as possible. A gate that cannot load is a gate that fails closed, and that
# should be caused by a real problem, not by an unrelated import.

def finite(value: float, what: str) -> float:
    """A money figure that is a real number, or a refusal.

    `NaN` is not `< 0`, so a bare non-negative check lets it through -- and then
    every `>` comparison against a NaN total is False, which silently voids the
    ceiling forever. `json.dumps` writes `NaN` and `json.loads` reads it back,
    and the ledger is append-only, so one such record could not be taken back
    short of a human moving the pool aside. `+inf` happens to fail closed, but
    only by accident of float comparison, and a rule that holds by accident is
    not a rule.
    """
    value = float(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise SpendGateError(
            "%s must be a finite number, got %r. A non-finite figure in an "
            "append-only money ledger voids every comparison made against it "
            "afterwards, and cannot be removed." % (what, value))
    return value


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def utcnow() -> str:
    seconds = time.time()
    base = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(seconds))
    return "%s.%03dZ" % (base, int((seconds % 1) * 1000))


# -- the cross-process lock --------------------------------------------------

class _PoolLock:
    """An exclusive lock on the pool, held across read-sum-append.

    A `threading.Lock` is not enough and never was: INC-BA-003's writers were
    four separate OS processes started by a different session. This takes an
    OS-level lock on a sidecar file, so the critical section holds across
    processes and across sessions.

    The lock file is separate from the ledger because the ledger is opened in
    append mode by the writer and read whole by the reader; locking a byte
    range of a file two different modes are touching is a portability problem
    nobody needs to have.
    """

    def __init__(self, path: str, timeout: float = 30.0):
        self.path = path
        self.timeout = timeout
        self._fh = None

    def __enter__(self) -> "_PoolLock":
        if fcntl is None and msvcrt is None:               # pragma: no cover
            raise SpendGateUnavailable(
                "neither fcntl nor msvcrt is importable, so this process "
                "cannot take a cross-process lock on the spend pool. Without "
                "the lock two writers can read the same headroom and both take "
                "it, which is INC-BA-003 with extra steps. Refusing to spend.")
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            # 'a+' so the file is created if absent and never truncated.
            self._fh = open(self.path, "a+b")
            if os.fstat(self._fh.fileno()).st_size == 0:
                # Windows locks a byte range; give it a byte to lock.
                self._fh.write(b"L")
                self._fh.flush()
            self._fh.seek(0)
        except OSError as exc:
            raise SpendGateUnavailable(
                "cannot open the spend pool lock at %s: %s. An unwritable pool "
                "is an uncountable pool; refusing to spend." % (self.path, exc))

        deadline = time.time() + self.timeout
        delay = 0.005
        while True:
            try:
                self._acquire()
                return self
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    self._close()
                    raise SpendGateUnavailable(
                        "locking the spend pool failed: %s" % exc)
                if time.time() >= deadline:
                    self._close()
                    raise SpendGateUnavailable(
                        "timed out after %.1fs waiting for the spend pool lock "
                        "at %s. Another process is holding it, or one died "
                        "holding it. Refusing to spend rather than proceeding "
                        "uncounted." % (self.timeout, self.path))
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


# -- policy ------------------------------------------------------------------

class SpendPolicy:
    """The pool: what may be spent in total, and where the record lives."""

    def __init__(self, spec: Dict[str, Any], source: Optional[str] = None):
        self.source = source
        self.spec = spec
        try:
            self.pool = str(spec["pool"])
            self.usd_ceiling = float(spec["usd_ceiling"])
            self.action_ceiling = int(spec["action_ceiling"])
            ledger = str(spec["ledger"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SpendGateUnavailable(
                "the spend policy at %s is missing or malformed (%s). A gate "
                "with no ceiling is not a gate; refusing to spend."
                % (source or "<literal>", exc))
        if self.usd_ceiling <= 0 or self.action_ceiling <= 0:
            raise SpendGateUnavailable(
                "the spend policy at %s has a non-positive ceiling "
                "(usd=%r actions=%r). Refusing to spend."
                % (source or "<literal>", self.usd_ceiling, self.action_ceiling))
        self.ledger_path = (ledger if os.path.isabs(ledger)
                            else os.path.join(POOL_ROOT,
                                              ledger.replace("/", os.sep)))
        self.default_ttl_seconds = float(spec.get("default_ttl_seconds", 3600))
        self.lock_timeout_seconds = float(spec.get("lock_timeout_seconds", 30.0))
        caps = spec.get("default_run_caps") or {}
        try:
            self.default_run_caps = {"usd": float(caps["usd"]),
                                     "actions": int(caps["actions"])}
        except (KeyError, TypeError, ValueError) as exc:
            raise SpendGateUnavailable(
                "the spend policy at %s has no usable `default_run_caps` (%s). "
                "That is what a run which declares no budget of its own is "
                "given, and 'no declared budget' must not resolve to "
                "'unlimited'. Refusing to spend."
                % (source or "<literal>", exc))
        if self.default_run_caps["usd"] < 0 or self.default_run_caps["actions"] < 0:
            raise SpendGateUnavailable(
                "default_run_caps must be non-negative (%r)" % (caps,))
        self.sha256 = (sha256_file(source) if source and os.path.exists(source)
                       else hashlib.sha256(canonical(spec).encode()).hexdigest())

    @classmethod
    def load(cls, path: str = DEFAULT_POLICY_PATH) -> "SpendPolicy":
        try:
            with open(path, encoding="utf-8") as fh:
                spec = json.load(fh)
        except FileNotFoundError:
            raise SpendGateUnavailable(
                "no spend policy at %s. The pool ceiling is a number a human "
                "wrote down; without it this process does not know what it is "
                "allowed to spend, and 'unknown' is not 'unlimited'. Refusing "
                "to spend." % path)
        except (OSError, json.JSONDecodeError) as exc:
            raise SpendGateUnavailable(
                "the spend policy at %s is unreadable: %s. Refusing to spend."
                % (path, exc))
        return cls(spec, source=path)

    def fingerprint(self) -> Dict[str, Any]:
        try:
            where = os.path.relpath(self.source or "", REPO).replace(os.sep, "/")
        except ValueError:                                  # a different drive
            where = self.source or ""
        return {"pool": self.pool, "policy_path": where or None,
                "policy_sha256": self.sha256,
                "usd_ceiling": self.usd_ceiling,
                "action_ceiling": self.action_ceiling,
                # ABSOLUTE, deliberately. A path relative to REPO is identical
                # in every worktree, so two runs against two different pool
                # files would have carried byte-identical provenance and the
                # split would have been undetectable after the fact. This field
                # is how a reader tells which pool a run actually drew on.
                "ledger_abspath": os.path.abspath(self.ledger_path),
                "pool_root": POOL_ROOT,
                "gate_version": GATE_VERSION}


# -- reservations ------------------------------------------------------------

class Reservation:
    """A claim on part of the pool, written down where other processes see it.

    A reservation is not an announcement. It *holds* headroom: while it is
    live, its unspent remainder is subtracted from what anyone else may
    reserve. That is the whole difference between this and INC-BA-003, where
    both sessions were told the truth about the pool and both were told it
    before the other one took its share.

    It is a lease, not a lock. A session that dies mid-campaign would otherwise
    hold its headroom until a human noticed, so a reservation expires. Expiry
    releases the *hold*; it never releases the *spend*, which is permanent and
    keeps counting against the pool forever.
    """

    def __init__(self, reservation_id: str, campaign: str, usd_cap: float,
                 action_cap: int, expires_epoch: float, holder: Dict[str, Any]):
        self.reservation_id = reservation_id
        self.campaign = campaign
        self.usd_cap = usd_cap
        self.action_cap = action_cap
        self.expires_epoch = expires_epoch
        self.holder = holder

    def expired(self, now: Optional[float] = None) -> bool:
        return (now if now is not None else time.time()) >= self.expires_epoch

    def __repr__(self) -> str:
        return "<Reservation %s campaign=%r usd_cap=%.4f action_cap=%d>" % (
            self.reservation_id[:8], self.campaign, self.usd_cap, self.action_cap)


#: Only `SpendGate` mints permits. This is a guard against routing around the
#: gate by accident or by convenience -- the failure mode that actually
#: happened -- not against an in-process attacker with import rights, who can
#: reach this name as easily as you just did. `SPEND_GATE.md` states the threat
#: model at the size it actually holds, the way LEDGER_FORMAT.md had to after
#: RED-15.
_MINT = object()


class SpendPermit:
    """What `proxy.forward.forward` requires before it opens a socket.

    Egress takes an argument that can only come from a live reservation. That
    makes 'forgot to check the gate' a `TypeError` at the call site rather than
    a discovery in the next incident report.
    """

    def __init__(self, gate: "SpendGate", reservation: Reservation,
                 usd: float = 0.0, actions: int = 1, _mint: Any = None):
        if _mint is not _MINT:
            raise SpendGateError(
                "a SpendPermit is minted by SpendGate.permit(), from a live "
                "reservation. Constructing one directly is how the gate stops "
                "being a gate.")
        self.gate = gate
        self.reservation = reservation
        self.usd = usd
        self.actions = actions
        #: How many sockets `forward()` actually opened under this permit.
        #: The caller records against *this*, not against the Response's
        #: `attempts`, because a permit refused on attempt 3 raises and there is
        #: no Response to read -- while attempts 1 and 2 really did happen and
        #: really did cost the pool. Counting them is the difference between an
        #: accounting record and an optimistic one.
        self.attempts_made = 0

    def check(self) -> None:
        """Called by `forward()` immediately before the socket opens."""
        self.gate.check(self.reservation, usd=self.usd, actions=self.actions)

    def describe(self) -> Dict[str, Any]:
        return {"reservation_id": self.reservation.reservation_id,
                "campaign": self.reservation.campaign,
                "pool": self.gate.policy.pool}


# -- totals ------------------------------------------------------------------

class Totals:
    """The global sum. Every field is over the whole pool, all campaigns."""

    def __init__(self, usd: float, actions: int, by_campaign: Dict[str, Any],
                 by_reservation: Dict[str, Any], live: List[Dict[str, Any]],
                 unpriced_calls: int, ceiling_usd: float, ceiling_actions: int,
                 records: int):
        self.usd = round(usd, 6)
        self.actions = actions
        self.by_campaign = by_campaign
        self.by_reservation = by_reservation
        self.live = live
        self.unpriced_calls = unpriced_calls
        self.ceiling_usd = ceiling_usd
        self.ceiling_actions = ceiling_actions
        self.records = records

    @property
    def held_usd(self) -> float:
        """Unspent remainder of every live reservation. Committed, not spent."""
        return round(sum(r["usd_remaining"] for r in self.live), 6)

    @property
    def held_actions(self) -> int:
        return sum(r["action_remaining"] for r in self.live)

    @property
    def free_usd(self) -> float:
        return round(self.ceiling_usd - self.usd - self.held_usd, 6)

    @property
    def free_actions(self) -> int:
        return self.ceiling_actions - self.actions - self.held_actions

    def as_dict(self) -> Dict[str, Any]:
        return {
            "usd_spent": self.usd, "actions_spent": self.actions,
            "usd_held": self.held_usd, "actions_held": self.held_actions,
            "usd_free": self.free_usd, "actions_free": self.free_actions,
            "usd_ceiling": self.ceiling_usd, "action_ceiling": self.ceiling_actions,
            "unpriced_calls": self.unpriced_calls,
            "by_campaign": self.by_campaign,
            "live_reservations": self.live,
            "records": self.records,
        }


# -- the gate ----------------------------------------------------------------

class SpendGate:
    """One pool. Construct it, reserve, check, record, release."""

    def __init__(self, policy: Optional[SpendPolicy] = None, *,
                 policy_path: str = DEFAULT_POLICY_PATH):
        self.policy = policy if policy is not None else SpendPolicy.load(policy_path)
        self.ledger_path = self.policy.ledger_path
        self.lock_path = self.ledger_path + ".lock"
        self._assert_writable()

    # -- fail-closed preconditions ----------------------------------------
    def _assert_writable(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.ledger_path))
        # The probe name carries this process's pid. A shared name is a race:
        # two gates constructed at the same instant -- the normal case for this
        # module, since concurrency is what it exists for -- would each create
        # and each remove the same file, and whichever lost would see
        # FileNotFoundError from its own `os.remove` and refuse to spend. A
        # fail-closed gate that fails closed on *itself* is an outage.
        probe = os.path.join(directory, ".spend_gate_write_probe.%d" % os.getpid())
        try:
            os.makedirs(directory, exist_ok=True)
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("")
        except OSError as exc:
            raise SpendGateUnavailable(
                "the spend ledger directory %s is not writable: %s. Spend that "
                "cannot be recorded is spend that cannot be gated; refusing."
                % (directory, exc))
        finally:
            try:
                os.remove(probe)
            except OSError:
                pass

    # -- reading -----------------------------------------------------------
    def _read_locked(self) -> List[Dict[str, Any]]:
        """Read the whole pool. Caller holds the lock.

        A line this reader cannot interpret fails the *file*, not just the
        line -- the opposite of `proxy/ledger.read_ledger`, and deliberately.
        There, a strict reader turns one bad append into a denial of service on
        an audit trail (RED-44), so rejecting the line is right. Here the file
        is money: a line we cannot read is spend we cannot count, and a gate
        that quietly under-counts is worse than no gate, because it reports a
        number and the number is wrong. The recovery is a human act -- move the
        file aside, record an incident, start a fresh pool -- not a shrug.
        """
        if not os.path.exists(self.ledger_path):
            return []
        out: List[Dict[str, Any]] = []
        with open(self.ledger_path, encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SpendGateUnavailable(
                        "%s:%d is not JSON (%s). A spend ledger line that "
                        "cannot be read is spend that cannot be counted. "
                        "Refusing to spend against a pool whose total is "
                        "unknown." % (self.ledger_path, lineno, exc))
                if not isinstance(record, dict) or record.get("v") != GATE_VERSION:
                    raise SpendGateUnavailable(
                        "%s:%d has spend-gate version %r; this reader knows %r. "
                        "Refusing to spend against a pool it cannot total."
                        % (self.ledger_path, lineno,
                           (record or {}).get("v") if isinstance(record, dict) else None,
                           GATE_VERSION))
                out.append(record)
        return out

    def _totals_locked(self, now: Optional[float] = None) -> Totals:
        now = time.time() if now is None else now
        records = self._read_locked()

        reservations: Dict[str, Dict[str, Any]] = {}
        by_campaign: Dict[str, Dict[str, Any]] = {}
        usd_total = 0.0
        action_total = 0
        unpriced = 0

        for record in records:
            kind = record.get("kind")
            rid = record.get("reservation_id")
            campaign = record.get("campaign") or "unknown"
            bucket = by_campaign.setdefault(
                campaign, {"usd": 0.0, "actions": 0, "reservations": 0})

            if kind == "reserve":
                reservations[rid] = {
                    "reservation_id": rid,
                    "campaign": campaign,
                    "usd_cap": float(record.get("usd_cap") or 0.0),
                    "action_cap": int(record.get("action_cap") or 0),
                    "expires_epoch": float(record.get("expires_epoch") or 0.0),
                    "holder": record.get("holder") or {},
                    "opened": record.get("ts"),
                    "released": False,
                    "usd": 0.0,
                    "actions": 0,
                }
                bucket["reservations"] += 1
            elif kind == "renew":
                if rid in reservations:
                    reservations[rid]["expires_epoch"] = float(
                        record.get("expires_epoch") or 0.0)
            elif kind == "release":
                if rid in reservations:
                    reservations[rid]["released"] = True
            elif kind == "spend":
                usd = float(record.get("usd") or 0.0)
                actions = int(record.get("actions") or 0)
                usd_total += usd
                action_total += actions
                bucket["usd"] = round(bucket["usd"] + usd, 6)
                bucket["actions"] += actions
                if record.get("unpriced"):
                    unpriced += 1
                if rid in reservations:
                    reservations[rid]["usd"] = round(
                        reservations[rid]["usd"] + usd, 6)
                    reservations[rid]["actions"] += actions
            elif kind == "price_correction":
                # The way out of blindness, in the only idiom an append-only
                # ledger has: a later record that supplies what an earlier one
                # could not. It adds the dollars and says how many unpriced
                # calls it accounts for. Deleting the bad line is not an option
                # and never was.
                usd = float(record.get("usd") or 0.0)
                usd_total += usd
                bucket["usd"] = round(bucket["usd"] + usd, 6)
                unpriced -= int(record.get("resolves") or 0)
                if rid in reservations:
                    reservations[rid]["usd"] = round(
                        reservations[rid]["usd"] + usd, 6)
            # `trip` records are evidence, not arithmetic.

        unpriced = max(0, unpriced)

        live: List[Dict[str, Any]] = []
        for entry in reservations.values():
            if entry["released"] or now >= entry["expires_epoch"]:
                continue
            item = dict(entry)
            item["usd_remaining"] = round(max(0.0, entry["usd_cap"] - entry["usd"]), 6)
            item["action_remaining"] = max(0, entry["action_cap"] - entry["actions"])
            live.append(item)
        live.sort(key=lambda r: r["reservation_id"])

        return Totals(usd_total, action_total, by_campaign,
                      {k: dict(v) for k, v in reservations.items()}, live,
                      unpriced, self.policy.usd_ceiling,
                      self.policy.action_ceiling, len(records))

    def totals(self) -> Totals:
        """The global sum, over every campaign and every session."""
        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            return self._totals_locked()

    # -- writing -----------------------------------------------------------
    def _append_locked(self, record: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._read_locked()
        record = dict(record)
        record["v"] = GATE_VERSION
        record["seq"] = len(existing) + 1
        record["ts"] = utcnow()
        line = canonical(record)
        try:
            with open(self.ledger_path, "a", encoding="utf-8", newline="") as fh:
                fh.write(line)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as exc:
            raise SpendGateUnavailable(
                "cannot append to the spend ledger %s: %s. Refusing to spend "
                "what cannot be recorded." % (self.ledger_path, exc))
        return record

    # -- the four verbs ----------------------------------------------------
    def reserve(self, campaign: str, usd_cap: float, action_cap: int, *,
                holder: Optional[Dict[str, Any]] = None,
                ttl_seconds: Optional[float] = None) -> Reservation:
        """Claim headroom before spending any of it.

        Refuses if the pool's already-spent total, plus every other live
        reservation's unspent remainder, plus this claim, would exceed the
        ceiling. The middle term is the one INC-BA-003 did not have.
        """
        if not campaign or not isinstance(campaign, str):
            raise SpendGateError(
                "a reservation needs a campaign name. `ledger.jsonl` mixed two "
                "campaigns in one append-only file and no line could say which "
                "was which (PARTNER_SYNC.md:456); an unnamed spend is that "
                "again.")
        usd_cap = finite(usd_cap, "a reservation's usd_cap")
        action_cap = int(action_cap)
        if usd_cap < 0 or action_cap < 0:
            raise SpendGateError("caps must be non-negative")

        ttl = float(ttl_seconds if ttl_seconds is not None
                    else self.policy.default_ttl_seconds)
        holder = dict(holder or {})
        holder.setdefault("pid", os.getpid())
        holder.setdefault("host", socket.gethostname())

        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            now = time.time()
            totals = self._totals_locked(now)

            if usd_cap > totals.free_usd:
                raise SpendGateTripped(
                    "reserving $%.4f for %r would exceed the pool: $%.4f already "
                    "spent + $%.4f held by %d live reservation(s) + $%.4f "
                    "requested > $%.2f ceiling (pool %r). This is the check "
                    "INC-BA-003 did not have: the held term is the other "
                    "session's claim, and it is why both campaigns cannot each "
                    "believe they have the whole budget."
                    % (usd_cap, campaign, totals.usd, totals.held_usd,
                       len(totals.live), usd_cap, totals.ceiling_usd,
                       self.policy.pool),
                    "POOL_USD_CEILING", totals.as_dict())

            if action_cap > totals.free_actions:
                raise SpendGateTripped(
                    "reserving %d actions for %r would exceed the pool: %d spent "
                    "+ %d held + %d requested > %d ceiling (pool %r)"
                    % (action_cap, campaign, totals.actions, totals.held_actions,
                       action_cap, totals.ceiling_actions, self.policy.pool),
                    "POOL_ACTION_CEILING", totals.as_dict())

            reservation_id = "res-" + uuid.uuid4().hex[:16]
            expires = now + ttl
            self._append_locked({
                "kind": "reserve",
                "reservation_id": reservation_id,
                "campaign": campaign,
                "usd_cap": round(usd_cap, 6),
                "action_cap": action_cap,
                "expires_epoch": expires,
                "expires": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expires)),
                "holder": holder,
                "pool": self.policy.pool,
                "policy_sha256": self.policy.sha256,
            })
            return Reservation(reservation_id, campaign, usd_cap, action_cap,
                               expires, holder)

    def renew(self, reservation: Reservation,
              ttl_seconds: Optional[float] = None) -> Reservation:
        """Extend a lease. A long campaign heartbeats; it does not re-reserve."""
        ttl = float(ttl_seconds if ttl_seconds is not None
                    else self.policy.default_ttl_seconds)
        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            totals = self._totals_locked()
            entry = totals.by_reservation.get(reservation.reservation_id)
            if entry is None:
                raise NoReservation(
                    "reservation %s is not in the pool ledger"
                    % reservation.reservation_id)
            if entry["released"]:
                raise NoReservation(
                    "reservation %s was released; renewing a released claim "
                    "would resurrect headroom somebody else may already have "
                    "taken." % reservation.reservation_id)
            now = time.time()
            if now >= entry["expires_epoch"]:
                # The same objection as the released case, and it took an
                # adversarial pass to notice that only one of the two was
                # checked. An expired lease has already given its headroom
                # back, and somebody else may already hold it: renewing would
                # leave two campaigns each believing they own the whole budget,
                # which is the decision-making failure INC-BA-003 actually was.
                raise NoReservation(
                    "reservation %s expired at %s; renewing it would resurrect "
                    "headroom that has already been re-let. Reserve again -- "
                    "the spend already recorded still counts either way."
                    % (reservation.reservation_id,
                       time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                     time.gmtime(entry["expires_epoch"]))))
            expires = now + ttl
            self._append_locked({
                "kind": "renew",
                "reservation_id": reservation.reservation_id,
                "campaign": reservation.campaign,
                "expires_epoch": expires,
                "expires": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(expires)),
            })
            reservation.expires_epoch = expires
            return reservation

    def release(self, reservation: Reservation, reason: str = "closed") -> None:
        """Give the unspent remainder back. Spend already recorded stays."""
        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            self._append_locked({
                "kind": "release",
                "reservation_id": reservation.reservation_id,
                "campaign": reservation.campaign,
                "reason": reason,
            })

    def check(self, reservation: Optional[Reservation], *,
              usd: float = 0.0, actions: int = 0) -> Totals:
        """The pre-flight. Called before the money leaves; raises to refuse.

        Reads the global sum, not this process's counter. That sentence is the
        entire point of the module.
        """
        if reservation is None:
            raise NoReservation(
                "no reservation held. Spending against a shared pool without "
                "first claiming headroom is what made INC-BA-003's exposure "
                "unbounded: both sessions were correct about their own budget "
                "and neither had claimed it where the other could see. Call "
                "SpendGate.reserve() first.")
        usd = finite(usd, "the amount being checked")
        actions = int(actions)

        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            now = time.time()
            totals = self._totals_locked(now)
            entry = totals.by_reservation.get(reservation.reservation_id)

            if entry is None:
                raise NoReservation(
                    "reservation %s is not in the pool ledger %s. A handle "
                    "whose claim is not on disk is not a claim."
                    % (reservation.reservation_id, self.ledger_path))
            if entry["released"]:
                raise NoReservation(
                    "reservation %s has been released; reserve again before "
                    "spending more." % reservation.reservation_id)
            if now >= entry["expires_epoch"]:
                raise NoReservation(
                    "reservation %s expired at %s. A lease expires so that a "
                    "session that died mid-campaign does not hold the pool's "
                    "headroom until a human notices. Renew it, or reserve "
                    "again -- the spend already recorded still counts either "
                    "way." % (reservation.reservation_id,
                              time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime(entry["expires_epoch"]))))

            # Blindness is scoped to the quantity it actually blinds.
            #
            # An unpriced model call makes the pool's *dollar* total a lower
            # bound, so no further dollar may be spent against it: the gate
            # would be comparing a real number to a number it knows is wrong.
            # It says nothing whatever about ARC actions, which are counted by
            # the request and not by a price table.
            #
            # The first version of this check refused *everything*, and wiring
            # the gate to the egress path is what exposed that: one mock model
            # call with a name absent from `proxy/pricing/` stopped the
            # environment proxy -- which spends no dollars at all -- for every
            # session sharing the pool, permanently, because the ledger is
            # append-only and nothing could take it back. A gate that can brick
            # the whole programme on one missing price-table row is not
            # fail-closed, it is a single point of failure wearing fail-closed's
            # clothes. `price_unpriced` is the way back, and it is an explicit,
            # recorded act rather than a flag.
            if totals.unpriced_calls and usd > 0:
                raise SpendGateTripped(
                    "%d call(s) in this pool could not be priced, so the pool's "
                    "dollar total is a lower bound and this gate would be "
                    "checking $%.4f against a number it knows is too small. Add "
                    "the model to proxy/pricing/, then account for the missing "
                    "dollars with SpendGate.price_unpriced(). Action-only spend "
                    "is unaffected: actions are counted by the request, not by "
                    "a price table." % (totals.unpriced_calls, usd),
                    "UNPRICED_SPEND", totals.as_dict())

            # -- the global sums, which is the whole reason this exists ----
            if totals.usd + usd > totals.ceiling_usd:
                raise SpendGateTripped(
                    "pool %r would pass its ceiling: $%.4f spent across %d "
                    "campaign(s) + $%.4f now > $%.2f. This is a GLOBAL total, "
                    "not this campaign's: %s"
                    % (self.policy.pool, totals.usd, len(totals.by_campaign),
                       usd, totals.ceiling_usd,
                       ", ".join("%s $%.4f" % (k, v["usd"])
                                 for k, v in sorted(totals.by_campaign.items()))),
                    "POOL_USD_CEILING", totals.as_dict())

            if totals.actions + actions > totals.ceiling_actions:
                raise SpendGateTripped(
                    "pool %r would pass its action ceiling: %d spent across %d "
                    "campaign(s) + %d now > %d"
                    % (self.policy.pool, totals.actions,
                       len(totals.by_campaign), actions, totals.ceiling_actions),
                    "POOL_ACTION_CEILING", totals.as_dict())

            # -- and this reservation's own caps ---------------------------
            if entry["usd"] + usd > entry["usd_cap"]:
                raise SpendGateTripped(
                    "reservation %s for %r is at $%.4f of its $%.4f cap"
                    % (reservation.reservation_id, reservation.campaign,
                       entry["usd"], entry["usd_cap"]),
                    "RESERVATION_USD_CAP", totals.as_dict())

            if entry["actions"] + actions > entry["action_cap"]:
                raise SpendGateTripped(
                    "reservation %s for %r is at %d of its %d action cap"
                    % (reservation.reservation_id, reservation.campaign,
                       entry["actions"], entry["action_cap"]),
                    "RESERVATION_ACTION_CAP", totals.as_dict())

            return totals

    def record(self, reservation: Reservation, *, usd: float = 0.0,
               actions: int = 0, unpriced: bool = False,
               detail: Optional[Dict[str, Any]] = None) -> Totals:
        """Register spend that has already happened.

        The record is appended **before** the caps are evaluated, and it is
        appended even when it is the record that breaches them. Money that was
        spent is a fact; a gate that refused to write it down because it was
        over budget would be a gate that makes the pool look under budget. The
        breach then raises, after the fact is on disk.

        This is the opposite ordering from `check`, which runs before the money
        moves and refuses. Both are needed: `check` prevents, `record` accounts.
        """
        if reservation is None:
            raise NoReservation("record() needs the reservation the spend was "
                                "made under")
        usd = finite(usd, "a recorded spend")
        actions = int(actions)
        if usd < 0 or actions < 0:
            raise SpendGateError("spend is not negative; a correction is a new "
                                 "record in an append-only ledger, not a "
                                 "smaller number")

        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            before = self._totals_locked()
            if reservation.reservation_id not in before.by_reservation:
                raise NoReservation(
                    "reservation %s is not in the pool ledger; the spend cannot "
                    "be attributed and an unattributable spend is the thing "
                    "this file exists to prevent."
                    % reservation.reservation_id)

            self._append_locked({
                "kind": "spend",
                "reservation_id": reservation.reservation_id,
                "campaign": reservation.campaign,
                "usd": round(usd, 6),
                "actions": actions,
                "unpriced": bool(unpriced),
                "detail": detail or {},
            })
            after = self._totals_locked()

            tripped = self._first_breach(after, reservation)
            if tripped is not None:
                rule, message = tripped
                self._append_locked({
                    "kind": "trip",
                    "reservation_id": reservation.reservation_id,
                    "campaign": reservation.campaign,
                    "rule": rule,
                    "detail": {"message": message,
                               "usd_spent": after.usd,
                               "actions_spent": after.actions},
                })
                raise SpendGateTripped(message, rule, after.as_dict())
            return after

    def price_unpriced(self, reservation: Reservation, *, usd: float,
                       resolves: int, reason: str) -> Totals:
        """Account, after the fact, for calls the gate could not price.

        The only way out of `UNPRICED_SPEND`, and deliberately a narrow one: it
        is a deliberate act with a stated reason, it is appended rather than
        edited, and it names how many blind calls it accounts for so the count
        can go down but the history cannot go away. Editing or deleting the
        unpriced `spend` line is not an option and never was -- the ledger is
        append-only because it is money.

        Typical use: the model was missing from `proxy/pricing/`, somebody adds
        it, and the dollars for the calls made in the meantime are computed from
        the price table and the `usage` blocks the *proxy ledger* recorded
        verbatim for exactly this reason.
        """
        if not reason.strip():
            raise SpendGateError(
                "price_unpriced needs a reason: what made these calls "
                "unpriceable, and where did the figure now being claimed come "
                "from? A correction with no provenance is a number somebody "
                "typed.")
        usd = finite(usd, "a price correction")
        resolves = int(resolves)
        if usd <= 0 or resolves <= 0:
            # `usd=0` would clear the blindness for nothing: N real calls
            # accounted for at $0.00, and the gate re-opened on the strength of
            # it. A call that genuinely cost nothing is a *priced* call worth
            # zero -- record it with `record(usd=0.0)` and no `unpriced` flag.
            raise SpendGateError(
                "a correction supplies a positive amount for at least one "
                "unpriced call. Clearing blindness for $0.00 is not a "
                "correction, it is the gate re-opening on nothing.")

        with _PoolLock(self.lock_path, self.policy.lock_timeout_seconds):
            before = self._totals_locked()
            if reservation.reservation_id not in before.by_reservation:
                raise NoReservation(
                    "reservation %s is not in the pool ledger"
                    % reservation.reservation_id)
            if resolves > before.unpriced_calls:
                raise SpendGateError(
                    "this correction claims to account for %d unpriced calls "
                    "but the pool only has %d. A correction that resolves more "
                    "blindness than exists would let the count be driven "
                    "negative and the gate re-opened on nothing."
                    % (resolves, before.unpriced_calls))
            self._append_locked({
                "kind": "price_correction",
                "reservation_id": reservation.reservation_id,
                "campaign": reservation.campaign,
                "usd": round(usd, 6),
                "resolves": resolves,
                "reason": reason,
            })
            return self._totals_locked()

    @staticmethod
    def _first_breach(totals: Totals, reservation: Reservation):
        entry = totals.by_reservation.get(reservation.reservation_id, {})
        if totals.usd > totals.ceiling_usd:
            return ("POOL_USD_CEILING",
                    "pool is over its ceiling: $%.4f > $%.2f (global, across "
                    "%d campaign(s))" % (totals.usd, totals.ceiling_usd,
                                         len(totals.by_campaign)))
        if totals.actions > totals.ceiling_actions:
            return ("POOL_ACTION_CEILING",
                    "pool is over its action ceiling: %d > %d (global)"
                    % (totals.actions, totals.ceiling_actions))
        if entry and entry["usd"] > entry["usd_cap"]:
            return ("RESERVATION_USD_CAP",
                    "reservation %s is over its cap: $%.4f > $%.4f"
                    % (reservation.reservation_id, entry["usd"], entry["usd_cap"]))
        if entry and entry["actions"] > entry["action_cap"]:
            return ("RESERVATION_ACTION_CAP",
                    "reservation %s is over its action cap: %d > %d"
                    % (reservation.reservation_id, entry["actions"],
                       entry["action_cap"]))
        return None

    # -- egress ------------------------------------------------------------
    def permit(self, reservation: Optional[Reservation], *,
               usd: float = 0.0, actions: int = 1) -> SpendPermit:
        """Mint what `forward()` demands. Does not itself check; the permit
        checks at the moment the socket is about to open, which is the moment
        the answer has to be current."""
        if reservation is None:
            raise NoReservation(
                "cannot mint a spend permit without a reservation. Every "
                "outbound request from this package needs one -- that is what "
                "makes the gate a function rather than a convention.")
        return SpendPermit(self, reservation, usd=usd, actions=actions,
                           _mint=_MINT)

    # -- reporting ---------------------------------------------------------
    def fingerprint(self) -> Dict[str, Any]:
        """Goes into `run_start`, so a run records which pool it drew on."""
        out = self.policy.fingerprint()
        try:
            out["ledger_path"] = os.path.relpath(
                self.ledger_path, REPO).replace(os.sep, "/")
        except ValueError:                                  # pragma: no cover
            out["ledger_path"] = self.ledger_path
        return out


# -- the module-level form ---------------------------------------------------
# `theoria-arm/armtools/spend_check.py` was written against the gate before the
# gate existed, and it calls `module.reserve(campaign, usd_cap, action_cap)` on
# whatever it loads from this path. That caller is right to exist and right to
# be defensive, so the shape it guessed is provided rather than broken: these
# are the same four verbs on a lazily-constructed default gate.
#
# This is a convenience, not a second implementation and not a looser one. Every
# call goes through `SpendGate`, the default gate reads the same tracked policy,
# and a failure raises exactly as it would through the class.

_DEFAULT_GATE: Optional["SpendGate"] = None


def default_gate() -> "SpendGate":
    """The process's gate on the tracked pool. Constructed once, never optional."""
    global _DEFAULT_GATE
    if _DEFAULT_GATE is None:
        _DEFAULT_GATE = SpendGate()
    return _DEFAULT_GATE


def set_default_gate(gate: Optional["SpendGate"]) -> Optional["SpendGate"]:
    """Point this *process* at a different pool. Returns the previous gate.

    This is not the environment variable the module refuses to have. The
    difference is not cosmetic: an env var relocates the pool for anything
    launched with it set, including production, which is how a pool becomes a
    pool of one. This is an in-process call with no file and no inheritance --
    a child process gets the tracked policy again, because it re-imports.

    It exists for tests, which must not append their fictional dollars to the
    real pool ledger, and for a caller that is deliberately running against a
    scratch pool and knows it. `proxy/tests/conftest.py` uses it once, for the
    whole session, so a test that forgets cannot reach the tracked pool.
    """
    global _DEFAULT_GATE
    previous, _DEFAULT_GATE = _DEFAULT_GATE, gate
    return previous


def default_campaign(arm: str, run_id: str) -> str:
    """The campaign name for a caller that did not choose one.

    Never `None` and never `"unknown"`: `baseline-arms/ledger.jsonl` mixed two
    campaigns into one append-only file and no line could say which was which
    (PARTNER_SYNC.md:456), and that is unrecoverable after the fact. A derived
    name is worse than a chosen one -- it does not say what the run was *for* --
    but it is attributable, which is the property that cannot be added later.
    """
    return "%s:%s" % (arm or "unknown-arm", run_id or "unknown-run")


def attach_reservation(gate: "SpendGate", campaign: str,
                       reservation: Optional[Reservation] = None,
                       holder: Optional[Dict[str, Any]] = None) -> Reservation:
    """Return the caller's reservation, or take the default one.

    A caller that declares its budget passes a `Reservation` and this is a
    no-op. A caller that does not gets the policy's `default_run_caps` -- which
    are deliberately small, because not declaring a budget should be
    inconvenient rather than unlimited. Either way there **is** a reservation
    before the process can open a socket, and either way the global pool
    ceiling binds on top of it.
    """
    if reservation is not None:
        return reservation
    caps = gate.policy.default_run_caps
    return gate.reserve(campaign, caps["usd"], caps["actions"],
                        holder=dict(holder or {}, undeclared=True))


def reserve(campaign: str, usd_cap: float, action_cap: int, **kwargs) -> Reservation:
    return default_gate().reserve(campaign, usd_cap, action_cap, **kwargs)


def check(reservation: Optional[Reservation], **kwargs) -> Totals:
    return default_gate().check(reservation, **kwargs)


def record(reservation: Reservation, **kwargs) -> Totals:
    return default_gate().record(reservation, **kwargs)


def release(reservation: Reservation, reason: str = "closed") -> None:
    return default_gate().release(reservation, reason)


def totals() -> Totals:
    return default_gate().totals()


def main(argv=None) -> int:
    """`python -m proxy.spend_gate` -- what the pool says right now."""
    import argparse
    ap = argparse.ArgumentParser(description="report the shared spend pool")
    ap.add_argument("--policy", default=DEFAULT_POLICY_PATH)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    gate = SpendGate(policy_path=args.policy)
    totals = gate.totals()
    if args.json:
        print(json.dumps({"gate": gate.fingerprint(), "totals": totals.as_dict()},
                         indent=2, sort_keys=True))
        return 0

    print("pool %s  (policy %s)" % (gate.policy.pool, gate.policy.sha256[:12]))
    print("  spent    $%9.4f / $%.2f   %6d / %d actions"
          % (totals.usd, totals.ceiling_usd, totals.actions, totals.ceiling_actions))
    print("  held     $%9.4f            %6d actions   (%d live reservation(s))"
          % (totals.held_usd, totals.held_actions, len(totals.live)))
    print("  free     $%9.4f            %6d actions"
          % (totals.free_usd, totals.free_actions))
    if totals.by_campaign:
        print("  by campaign:")
        for name, bucket in sorted(totals.by_campaign.items()):
            print("    %-32s $%9.4f  %6d actions"
                  % (name, bucket["usd"], bucket["actions"]))
    for entry in totals.live:
        print("  LIVE %s %-28s $%.4f/%.4f  %d/%d actions  pid=%s"
              % (entry["reservation_id"][:12], entry["campaign"], entry["usd"],
                 entry["usd_cap"], entry["actions"], entry["action_cap"],
                 entry["holder"].get("pid")))
    if len(totals.live) > 1:
        print("  NOTE: %d concurrent reservations are open on one pool. That is "
              "allowed and counted -- it is exactly what INC-BA-003 could not "
              "see." % len(totals.live))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
