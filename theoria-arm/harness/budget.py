"""The action budget, enforced before the money is spent rather than after.

P-8's red line is 120 actions including probes. Two facts from this repo's own
measurements decide what "an action" counts as here:

* `baseline-arms` compared four independent scorecards against its ledger and
  found `scorecard.total_actions` equal to the number of **successful** actions
  every time; failed 400s did not bill. So the ceiling is counted in successful
  ACTIONs.
* `arc-recon` measured 2.5-10x HTTP amplification per action under the retry
  envelope that actually works. Retries are therefore free of quota but not
  free of time, so a second, much looser ceiling on total HTTP commands stops a
  wave of transient 400s from turning into an unbounded run.

Both ceilings are hard: `spend()` raises rather than returning a flag, because
a budget that can be ignored by a caller who forgets to check is not a budget.
"""

from typing import Any, Dict, Optional


class BudgetExhausted(RuntimeError):
    """The action ceiling was reached. Not an error in the run -- the run's
    natural end when nothing else stopped it first."""


class Budget:
    def __init__(self, actions: int = 120, commands: int = 2000,
                 reserve_for_probes: int = 0):
        self.actions = actions
        self.commands = commands
        #: Actions held back so a probe designed late in the run can still be
        #: executed. `spend` refuses to dip into it unless `probe=True`.
        self.reserve_for_probes = reserve_for_probes

        self.actions_ok = 0
        self.actions_failed = 0
        self.probe_actions = 0
        self.resets = 0
        self.commands_sent = 0
        #: Read-only requests (scorecard fetches). Counted separately from
        #: `commands_sent` as well as inside it, so a reader can subtract them:
        #: a leg whose command count is inflated by scoreboard reads must not
        #: look like a leg whose retry envelope ran away.
        self.reads = 0

    # -- the two ceilings --------------------------------------------------
    @property
    def actions_left(self) -> int:
        return self.actions - self.actions_ok

    @property
    def actions_left_outside_reserve(self) -> int:
        return self.actions_left - self.reserve_for_probes

    def check(self, *, probe: bool = False, is_reset: bool = False) -> None:
        """Called before a command leaves. Raises rather than warns."""
        if self.commands_sent >= self.commands:
            raise BudgetExhausted(
                "HTTP command ceiling reached: %d commands sent. Retry waves, "
                "not actions, are what got us here." % self.commands_sent)
        if is_reset:
            # RESET is not billed as an action -- `scorecard.total_actions`
            # counts successful ACTIONs and reports resets separately -- so the
            # action ceiling must not gate it. Gating it would also make a run
            # that has spent its last action unable to open a session at all.
            return
        if probe:
            if self.actions_left <= 0:
                raise BudgetExhausted(
                    "action ceiling reached: %d/%d successful actions"
                    % (self.actions_ok, self.actions))
        elif self.actions_left_outside_reserve <= 0:
            raise BudgetExhausted(
                "action ceiling reached: %d/%d successful actions (%d held in "
                "the probe reserve)"
                % (self.actions_ok, self.actions, self.reserve_for_probes))

    # -- recording ---------------------------------------------------------
    def command(self) -> None:
        self.commands_sent += 1

    def succeeded(self, *, is_reset: bool = False, probe: bool = False) -> None:
        if is_reset:
            self.resets += 1                    # RESET is not billed as an action
            return
        self.actions_ok += 1
        if probe:
            self.probe_actions += 1

    def failed(self, *, is_reset: bool = False) -> None:
        if not is_reset:
            self.actions_failed += 1

    # -- read-only traffic -------------------------------------------------
    def check_readonly(self) -> None:
        """Called before a request that returns state and changes none.

        `GET /api/scorecard/{card_id}` is the only such request the arm makes.
        It costs a command -- it is a socket through the proxy and the shared
        pool counts it -- and it costs no action, because `total_actions` on the
        card counts successful ACTIONs and a read is not one. The action ceiling
        must therefore not gate it, exactly as it does not gate RESET, and for
        the symmetrical reason: a leg that has spent its last action is the leg
        that most needs to be able to read its own scorecard.

        It is a separate method rather than `check(is_reset=True)` so that
        `resets` stays a count of RESETs.
        """
        if self.commands_sent >= self.commands:
            raise BudgetExhausted(
                "HTTP command ceiling reached: %d commands sent, and a "
                "read-only scorecard fetch is still a request."
                % self.commands_sent)

    def read(self) -> None:
        self.reads += 1

    def as_json(self) -> Dict[str, Any]:
        return {
            "ceiling_actions": self.actions,
            "ceiling_commands": self.commands,
            "reserve_for_probes": self.reserve_for_probes,
            "actions_ok": self.actions_ok,
            "actions_failed": self.actions_failed,
            "probe_actions": self.probe_actions,
            "resets": self.resets,
            "commands_sent": self.commands_sent,
            "reads": self.reads,
            "actions_left": self.actions_left,
            # Attempts, not outbound requests. `Budget.command()` is called once
            # per arm-level attempt, and an attempt that the proxy refuses
            # before the wire increments it just the same. On
            # `runs/20260729T004020Z-leg01` that gap was 2000 attempts against
            # 104 records with `http.forwarded=true` -- so this number read
            # 222.222 for a leg whose transport managed 11.6 requests per
            # successful action, and a mid-run reading of it was quoted as
            # "86.7x amplification" in a commit message and a docstring.
            #
            # It is not renamed, because RUN_STATE.json readers and
            # `armtools/archive.py`'s reconciliation block already carry the old
            # key. It is stated instead: what it measures, and what it does not.
            "attempt_amplification": (round(self.commands_sent / self.actions_ok, 3)
                                      if self.actions_ok else None),
            "http_amplification": (round(self.commands_sent / self.actions_ok, 3)
                                   if self.actions_ok else None),
            "http_amplification_is_really_attempts": True,
            "http_amplification_note": (
                "arm-level attempts per successful ACTION, including attempts "
                "that never reached the network. The arm cannot compute the "
                "transport ratio: only the proxy ledger knows which attempts "
                "were forwarded (`http.forwarded`). Divide that count by "
                "`actions_ok` for the real one."),
        }

    def __repr__(self) -> str:
        return "Budget(%d/%d actions, %d commands)" % (
            self.actions_ok, self.actions, self.commands_sent)


def resume(state: Optional[Dict[str, Any]], **kwargs: Any) -> Budget:
    """Rebuild a budget from a previous run's `as_json()`.

    A run that is staged across several invocations must not get a fresh 120
    actions each time. `RUN_STATE.md` carries the counters between stages and
    this is the only way they are read back.
    """
    budget = Budget(**kwargs)
    if not state:
        return budget
    budget.actions_ok = int(state.get("actions_ok") or 0)
    budget.actions_failed = int(state.get("actions_failed") or 0)
    budget.probe_actions = int(state.get("probe_actions") or 0)
    budget.resets = int(state.get("resets") or 0)
    budget.commands_sent = int(state.get("commands_sent") or 0)
    budget.reads = int(state.get("reads") or 0)
    return budget
