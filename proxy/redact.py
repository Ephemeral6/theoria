"""Credential handling: read from `.env`, never let the value out again.

Two rules, both structural:

  * A secret is registered with the process-wide `VAULT` the moment it is read.
    Everything the ledger writer emits passes through `VAULT.scrub()` first, so
    a key cannot reach disk even if an arm posted it in a request body.
  * Nothing here returns a secret to a caller that did not ask for it by name.
    `mask()` is what goes into logs.

The `.env` reader is deliberately local rather than imported from
`arc-recon/client.py`: that file belongs to another surface and this track must
not modify it, so ~30 lines of duplication is cheaper than a coupling we could
not fix.
"""

import os
import re
from typing import Any, Dict, Iterable, List, Optional

from .paths import DOTENV

SENSITIVE_HEADERS = frozenset({
    "authorization", "x-api-key", "x-api-token", "api-key",
    "proxy-authorization", "cookie", "set-cookie",
})

REDACTED = "<redacted>"

#: A value shorter than this is not treated as a secret worth substring-scanning
#: for -- scrubbing a 3-character "key" would corrupt unrelated text.
MIN_SECRET_LEN = 12


def load_dotenv(path: str = DOTENV) -> Dict[str, str]:
    """Parse `.env` into a dict. Missing file is an empty dict, not an error:
    the mock end-to-end path runs without one."""
    out: Dict[str, str] = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if value:
                out[name.strip()] = value
    return out


class Vault:
    """Every secret the process has touched, and the ability to remove them
    from anything on its way to disk."""

    def __init__(self) -> None:
        self._secrets: List[str] = []

    def register(self, value: Optional[str]) -> Optional[str]:
        if value and len(value) >= MIN_SECRET_LEN and value not in self._secrets:
            self._secrets.append(value)
        return value

    def register_all(self, values: Iterable[Optional[str]]) -> None:
        for value in values:
            self.register(value)

    @property
    def secrets(self) -> List[str]:
        return list(self._secrets)

    def contains_secret(self, blob: str) -> bool:
        return any(secret in blob for secret in self._secrets)

    def scrub_text(self, text: str) -> str:
        for secret in self._secrets:
            if secret in text:
                text = text.replace(secret, REDACTED)
        return text

    def scrub(self, obj: Any) -> Any:
        """Deep copy with every registered secret replaced, and every sensitive
        header key blanked whatever its value."""
        if isinstance(obj, str):
            return self.scrub_text(obj)
        if isinstance(obj, dict):
            out = {}
            for key, value in obj.items():
                if isinstance(key, str) and key.lower() in SENSITIVE_HEADERS:
                    out[key] = REDACTED
                else:
                    out[key] = self.scrub(value)
            return out
        if isinstance(obj, (list, tuple)):
            return [self.scrub(item) for item in obj]
        return obj


VAULT = Vault()


def mask(value: Optional[str]) -> str:
    """Safe to log: enough to tell two keys apart, not enough to use one."""
    if not value:
        return "<unset>"
    if len(value) <= 8:
        return "<short:%d>" % len(value)
    return "%s...%s (len %d)" % (value[:4], value[-4:], len(value))


def read_secret(name: str, env_path: str = DOTENV, required: bool = True) -> Optional[str]:
    """Read one credential from `.env`, falling back to the process environment,
    and register it with the vault. This is the only way a secret enters the
    process."""
    value = load_dotenv(env_path).get(name) or os.environ.get(name)
    if not value:
        if required:
            raise RuntimeError(
                "%s is not set. Put it in %s (gitignored) -- never in a tracked "
                "file." % (name, env_path)
            )
        return None
    return VAULT.register(value)


_KEYISH = re.compile(
    r"(?:sk-[A-Za-z0-9_\-]{16,}|[A-Za-z0-9]{32,})"
)


def looks_like_credential(blob: str) -> bool:
    """Heuristic used to raise a `credential_in_body` incident when an arm sends
    something key-shaped. Deliberately loose: a false positive costs one
    incident record, a false negative costs a published key."""
    return bool(_KEYISH.search(blob))
