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

import base64
import os
import re
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional, Tuple

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


def _forms_of(value: Optional[str], force: bool = False) -> List[str]:
    """The spellings of one secret that are still that secret.

    `force` is for a value that is a credential **by construction** -- the one
    a proxy read out of `.env` to inject. The length floor exists so that
    scrubbing an incidental short string does not corrupt unrelated text; it
    has no business declining to protect the actual key because the operator
    chose a short one (RED-14).
    """
    if not value or (len(value) < MIN_SECRET_LEN and not force):
        return []
    forms = [value]
    raw = value.encode("utf-8")
    for encoded in (base64.b64encode(raw).decode("ascii"),
                    base64.urlsafe_b64encode(raw).decode("ascii"),
                    urllib.parse.quote(value, safe="")):
        if encoded and encoded != value:
            forms.append(encoded)
    stripped = forms[1].rstrip("=")            # padding-free base64 appears too
    if stripped and stripped not in forms:
        forms.append(stripped)
    return forms


class Vault:
    """Every secret the process has touched, and the ability to remove them
    from anything on its way to disk."""

    def __init__(self) -> None:
        self._secrets: List[str] = []

    def register(self, value: Optional[str], force: bool = False) -> Optional[str]:
        """Register a secret, and the encodings of it that are the same secret.

        A key that appears base64-encoded or percent-encoded in a body is the
        key. Registering those forms alongside the raw value costs nothing and
        closes the encoded half of RED-18; the half it does not close -- a
        secret split across two fields and rejoined downstream -- is not
        closable by substring scanning and is stated as a limitation in
        DECISIONS D-023 rather than pretended away.
        """
        for form in _forms_of(value, force=force):
            if form not in self._secrets:
                self._secrets.append(form)
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

    def _split_spans(self, obj: Any) -> Any:
        """Redact a secret that is only there once the pieces are joined.

        `{"a": "<first half>", "b": "<second half>"}` contains no secret in any
        one value, and rejoins into one at the far end (RED-18). Substring
        scanning cannot see it, so this looks at the concatenation of the
        values and blanks the ones that overlap a secret's span. It fires only
        when a *registered* secret is present, so a false positive means the
        real key was genuinely in the record.
        """
        pieces: List[Any] = []                       # (container, key, text)

        def collect(node: Any) -> None:
            if isinstance(node, dict):
                for key in list(node):
                    value = node[key]
                    if isinstance(value, str):
                        pieces.append((node, key, value))
                    else:
                        collect(value)
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    if isinstance(value, str):
                        pieces.append((node, index, value))
                    else:
                        collect(value)

        collect(obj)
        if len(pieces) < 2:
            return obj

        joined = "".join(text for _, _, text in pieces)
        for secret in self._secrets:
            start = joined.find(secret)
            while start != -1:
                end = start + len(secret)
                offset = 0
                for container, key, text in pieces:
                    if offset < end and offset + len(text) > start:
                        container[key] = REDACTED
                    offset += len(text)
                joined = joined[:start] + REDACTED + joined[end:]
                start = joined.find(secret)
        return obj

    def scrub(self, obj: Any) -> Any:
        """Deep copy with every registered secret replaced, and every sensitive
        header key blanked whatever its value.

        Dictionary **keys** are scrubbed as well as values. A secret used as a
        key survived the earlier version (RED-17), which is a real shape: an
        arm that builds `{"<key>": "..."}` puts the credential somewhere a
        value-only scrubber never looks.
        """
        return self._split_spans(self._scrub_one(obj))

    def _scrub_one(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return self.scrub_text(obj)
        if isinstance(obj, dict):
            out = {}
            for key, value in obj.items():
                clean_key = self.scrub_text(key) if isinstance(key, str) else key
                if isinstance(key, str) and key.lower() in SENSITIVE_HEADERS:
                    out[clean_key] = REDACTED
                else:
                    out[clean_key] = self._scrub_one(value)
            return out
        if isinstance(obj, (list, tuple)):
            return [self._scrub_one(item) for item in obj]
        return obj


#: Field names whose values are key-shaped by design. Scrubbing them would
#: destroy the record: a `card_id` and a `guid` are UUIDs, a `frame_hash` is 64
#: hex characters, and none of them is a secret.
STRUCTURAL_KEYS = frozenset({
    "card_id", "guid", "game_id", "run_id", "sha256", "frame_hash",
    "request_sha256", "cut_sha256", "source_sha256", "out_sha256",
    "opaque", "frames", "frame", "action", "pricing_ref", "proxy_version",
    "scorer", "variant", "spec_sha256", "piles_sha256",
})

KEYISH_REDACTED = "<redacted:key-shaped>"


def scrub_keyish(obj: Any, skip: frozenset = STRUCTURAL_KEYS) -> Any:
    """Remove strings that *look* like a credential, structural fields aside.

    The vault can only remove secrets it has been told about. A credential the
    proxies have never seen -- another service's key, pasted into a request by
    an arm -- was written out verbatim (RED-15), which falsified
    `LEDGER_FORMAT.md` §4's claim outright.

    This is the blunt half of the answer and it is deliberately narrow: it runs
    on environment traffic only, never on `model_call`, where §4 requires the
    request and response bodies verbatim and where a long run of alphanumerics
    is ordinary model output rather than a key. What it cannot do is recognise
    a secret that does not look like one; §4 now says so instead of promising
    otherwise.
    """
    if isinstance(obj, str):
        return _KEYISH.sub(KEYISH_REDACTED, obj)
    if isinstance(obj, dict):
        return {k: (v if (isinstance(k, str) and k.lower() in skip)
                    else scrub_keyish(v, skip))
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [scrub_keyish(item, skip) for item in obj]
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
    r"(?:sk-[A-Za-z0-9_\-]{16,}"
    r"|[A-Za-z0-9]{32,}"
    # A UUID-shaped 36-character string. This is the shape of the ARC key's own
    # mask (`7171...05dd (len 36)`), and the earlier pattern was blind to it
    # because of the hyphens (RED-16). It is a *detector*, not a scrubber:
    # `card_id` and `guid` are also UUIDs, so matching here raises an incident
    # and never rewrites the ledger -- see `scrub_outbound` for the difference.
    r"|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    r")"
)


def looks_like_credential(blob: str) -> bool:
    """Heuristic used to raise a `credential_in_body` incident when an arm sends
    something key-shaped. Deliberately loose: a false positive costs one
    incident record, a false negative costs a published key."""
    return bool(_KEYISH.search(blob))


def scrub_outbound(body: bytes, headers: Dict[str, str],
                   vault: "Vault") -> Tuple[bytes, Dict[str, str], List[str]]:
    """Remove registered secrets from what a proxy is about to hand the *arm*.

    `Vault.scrub` used to run in one direction only -- toward disk -- which
    left the other direction open: an upstream that echoes the key in its
    response body or in a header hands it straight to the arm, and the ledger
    stays clean, so the leak is unrecorded as well as unstopped (RED-10/11/12).
    The arm holding no credential is the property the whole double proxy is
    built to make true; a response is as good a way to acquire one as a
    request.

    Returns the cleaned body, the cleaned headers, and the places a secret was
    found -- which the caller records as an incident, because an upstream
    reflecting our key back at us is an event somebody should see.
    """
    found: List[str] = []

    text = body.decode("utf-8", "replace") if body else ""
    if text and vault.contains_secret(text):
        found.append("body")
        body = vault.scrub_text(text).encode("utf-8")

    clean: Dict[str, str] = {}
    for name, value in headers.items():
        if isinstance(value, str) and vault.contains_secret(value):
            found.append("header:%s" % name)
            value = vault.scrub_text(value)
        clean[name] = value

    return body, clean, found
