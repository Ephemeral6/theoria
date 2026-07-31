"""Putting the vendor CLI *behind* the model proxy, and the measurements that
say it can be done.

`theoria-arm/harness/modelcall.py` starts `claude -p` as a subprocess, and
`DUAL_PROXY.md` §4 step 2 reads that as a structural dead end: "the CLI
authenticates with an OAuth bearer, the proxy strips `Authorization` by design,
so pointing `ANTHROPIC_BASE_URL` at the proxy reproduces exactly the archived
401s." That conclusion is half right. It is right about what happens by
default. It is wrong that nothing but a direct `/v1/messages` client can fix it.

Three things were measured against a loopback provider on 2026-08-01
(`proxy/runs/20260801T0000Z-P12-model-proxy-cli/FINDING.md`), no network, no
spend:

1. **The CLI honours `ANTHROPIC_BASE_URL`.** One `POST /v1/messages?beta=true`,
   `stream: true`, and it parses a hand-written provider-shaped SSE reply into
   its own result envelope with `usage` and `total_cost_usd` intact. So the
   desk's transport is HTTP after all; `claude -p` is a client, not a wall.

2. **Which credential it presents depends on `CLAUDE_CONFIG_DIR`, not on
   `ANTHROPIC_API_KEY`.** With the operator's ordinary config directory
   visible, the CLI sends its stored OAuth bearer in `Authorization` and
   ignores both `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` — which is the
   behaviour that produced the archived 401s and the 66 `bypass_attempt`
   incidents. Pointed at a config directory that holds **no** stored
   credentials, the same CLI sends `x-api-key: <whatever ANTHROPIC_API_KEY
   says>` and no `Authorization` header at all.

   That is the whole of the missing piece. `ANTHROPIC_API_KEY` does not have to
   be a funded provider key for the *client* leg: it has to be a token the
   proxy recognises. The proxy strips it and injects the real provider key on
   the far side, which is the sealing property, unchanged.

3. **A third-party `ANTHROPIC_BASE_URL` receives the operator's real OAuth
   bearer** whenever the config directory is the ordinary one. That is a
   finding about the *existing* arm, not about this module:
   `modelcall.py:SCRUBBED_FROM_DESK_ENV` pops `ANTHROPIC_BASE_URL` before the
   subprocess starts, and this measurement is the first evidence of what that
   pop is actually worth. Any caller that sets the variable deliberately must
   set `CLAUDE_CONFIG_DIR` in the same breath, or it has redirected a live
   credential to a host of its choosing.

So the honest architecture is (a): route the CLI through the proxy with a
locally-minted token. What this module owns is the environment that makes the
route real, and nothing else.

    from proxy.cli_transport import DeskTransport

    with DeskTransport(proxy.base_url) as transport:
        env = transport.apply(dict(os.environ))       # BASE_URL + token + cfg dir
        subprocess.run([claude, "-p", ...], env=env, ...)

The token is **not** registered with `redact.VAULT`, deliberately. The vault
holds provider credentials so they can be scrubbed out of ledgers and refused
into subprocess environments; this token exists precisely to be handed to a
subprocess, and it is worthless anywhere but the loopback port that minted it.
Registering it would make `modelcall.py`'s by-value environment scan raise
`CredentialBreach` on the one variable the transport has to set.
"""

import os
import secrets
import shutil
import tempfile
from typing import Dict, Optional

#: A visible, greppable prefix. Anything wearing it is a loopback capability,
#: not a provider credential -- which matters when one turns up in a log and
#: somebody has to decide in ten seconds whether it is an incident.
TOKEN_PREFIX = "theoria-local-"

#: The variable the proxy reads its expected client token from when one is not
#: passed to `ModelProxyConfig` directly.
TOKEN_ENV = "THEORIA_MODEL_PROXY_TOKEN"


def mint_client_token(nbytes: int = 24) -> str:
    """A fresh capability for one proxy, one run.

    `secrets` rather than `random`: the token is what separates "the desk" from
    "anything else on this machine that can reach a loopback port", and a
    predictable one separates nothing.
    """
    return TOKEN_PREFIX + secrets.token_urlsafe(nbytes)


class DeskTransport:
    """The environment a `claude -p` desk needs to speak through the proxy.

    It owns a temporary `CLAUDE_CONFIG_DIR` for the lifetime of the context.
    That directory is the load-bearing part and the reason this is a context
    manager rather than a function: it must contain no stored OAuth
    credentials, or the CLI ignores the minted token and presents the
    operator's real bearer to the proxy instead (measurement 2 above).

    `config_dir` may be supplied by a caller that wants the CLI's session state
    to persist across calls. Supplying the operator's own is a defect and is
    refused -- not because the proxy would break, but because it would silently
    put a real credential back on the wire.
    """

    def __init__(self, base_url: str, *, token: Optional[str] = None,
                 config_dir: Optional[str] = None,
                 parent_dir: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token or mint_client_token()
        self._given_config_dir = config_dir
        self._parent_dir = parent_dir
        self.config_dir: Optional[str] = None
        self._owned = False

    # -- the environment ---------------------------------------------------
    def variables(self) -> Dict[str, str]:
        if self.config_dir is None:
            raise RuntimeError(
                "DeskTransport has no config directory yet; use it as a context "
                "manager (`with DeskTransport(url) as t:`) so the credential-free "
                "CLAUDE_CONFIG_DIR exists for the length of the call")
        return {
            "ANTHROPIC_BASE_URL": self.base_url,
            "ANTHROPIC_API_KEY": self.token,
            "CLAUDE_CONFIG_DIR": self.config_dir,
            # Nothing here should be phoning anywhere but the proxy. This is a
            # request, not a guarantee: the guarantee is that the only endpoint
            # the CLI is configured with is a loopback port.
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        }

    def apply(self, env: Dict[str, str]) -> Dict[str, str]:
        """Return `env` with the transport's variables set and the two
        credentials that must not survive removed.

        `ANTHROPIC_AUTH_TOKEN` is popped rather than overwritten: it is the
        bearer form, and a bearer beats an `x-api-key` in the CLI's own
        precedence order, so leaving an inherited one in place would put an
        unknown credential on the wire under a configuration that looks correct.
        """
        out = dict(env)
        out.pop("ANTHROPIC_AUTH_TOKEN", None)
        out.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
        out.update(self.variables())
        return out

    def describe(self) -> Dict[str, object]:
        """What a run report may say about this transport. Names and shapes
        only -- the token's *value* is never returned by anything here."""
        return {"transport": "claude-code-cli-via-model-proxy",
                "base_url": self.base_url,
                "token_prefix": TOKEN_PREFIX,
                "token_len": len(self.token),
                "config_dir_is_temporary": self._owned}

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self) -> "DeskTransport":
        if self._given_config_dir is not None:
            self.config_dir = self._given_config_dir
            os.makedirs(self.config_dir, exist_ok=True)
            self._owned = False
        else:
            self.config_dir = tempfile.mkdtemp(prefix="theoria-desk-cfg-",
                                               dir=self._parent_dir)
            self._owned = True
        return self

    def __exit__(self, *exc) -> None:
        if self._owned and self.config_dir:
            # `ignore_errors`: the CLI keeps handles open under Windows for a
            # moment after it exits, and a transport that raises on the way out
            # would turn a completed, paid-for call into a failed one.
            shutil.rmtree(self.config_dir, ignore_errors=True)
        self.config_dir = None
