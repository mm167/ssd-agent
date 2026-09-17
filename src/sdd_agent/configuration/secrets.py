"""Secret rejection for committed project configuration (PLAN Section 78).

Secrets (API keys, credentials, tokens, passwords) must never be accepted in
committed `sdd.yaml` or `.sdd/`. This module scans raw configuration data
*before* it is bound to the fixed Pydantic schema, so either a secret-shaped
key (`api_key: ...`) or a credential-bearing scalar value (a URL with
embedded `user:password@host` userinfo, e.g. in `git.remote`) is rejected
with an explainable `ConfigurationError`, rather than a generic "extra
field" error or, worse, silent acceptance.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from sdd_agent.diagnostics.errors import ConfigurationError

_SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|credential|access[_-]?key)",
    re.IGNORECASE,
)

# Recognizable provider token formats may occur inside free-text diagnostics or
# session metadata, where a secret-shaped field name is unavailable. These are
# explicit credential families, not generic entropy heuristics, so ordinary
# opaque identifiers (Git SHAs, fingerprints, UUIDs, report IDs) remain valid
# evidence.
_BARE_CREDENTIAL_FAMILIES = (
    # GitHub classic fine-grained/application token prefixes.
    r"(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})",
    # Claude/Anthropic and OpenAI/Codex-style API keys.
    r"(?:sk-ant-[A-Za-z0-9_-]{8,}|sk-(?:proj-|live-)?[A-Za-z0-9_-]{8,})",
    # Google API keys.
    r"AIza[A-Za-z0-9_-]{20,}",
    # AWS access-key identifiers.
    r"(?:AKIA|ASIA)[0-9A-Z]{16}",
    # Slack bot/app/user tokens.
    r"xox[baprs]-[A-Za-z0-9-]{8,}",
)

_BARE_CREDENTIAL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(?:" + "|".join(_BARE_CREDENTIAL_FAMILIES) + r")(?![A-Za-z0-9])"
)


def find_secret_like_keys(data: Any, *, _path: str = "") -> list[str]:
    """Return dotted paths of any mapping keys that look like secrets."""
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_path = f"{_path}.{key}" if _path else str(key)
            if isinstance(key, str) and _SECRET_KEY_PATTERN.search(key):
                found.append(key_path)
            found.extend(find_secret_like_keys(value, _path=key_path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            found.extend(find_secret_like_keys(item, _path=f"{_path}[{index}]"))
    return found


def _has_embedded_url_password(value: str) -> bool:
    """Detect `scheme://user:password@host/...`-shaped credential-bearing URLs.

    Only values that parse as a URL *and* carry a non-empty password
    component are flagged. A bare username with no password (e.g. an SSH
    scp-like remote such as `git@github.com:org/repo.git`, which has no
    `://` at all, or `ssh://git@github.com/org/repo.git`, whose userinfo
    carries no password) is a normal, non-secret remote form and is left
    untouched -- this keeps the rule structural rather than tied to any
    single provider's token format.
    """
    if "://" not in value:
        return False
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return bool(parsed.password)


def _has_bare_credential_token(value: str) -> bool:
    """Detect narrowly recognizable provider tokens embedded in text."""
    return bool(_BARE_CREDENTIAL_PATTERN.search(value))


def find_secret_like_values(data: Any, *, _path: str = "") -> list[str]:
    """Return dotted paths of any scalar values that look like embedded credentials."""
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_path = f"{_path}.{key}" if _path else str(key)
            found.extend(find_secret_like_values(value, _path=key_path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            found.extend(find_secret_like_values(item, _path=f"{_path}[{index}]"))
    elif isinstance(data, str) and (
        _has_embedded_url_password(data) or _has_bare_credential_token(data)
    ):
        found.append(_path or "<root>")
    return found


def reject_secrets(data: Any) -> None:
    """Raise ConfigurationError if secret-shaped keys or credential-bearing
    values are present.
    """
    offending_keys = sorted(find_secret_like_keys(data))
    offending_values = sorted(find_secret_like_values(data))

    if not offending_keys and not offending_values:
        return

    messages = []
    if offending_keys:
        messages.append("secret-like key(s): " + ", ".join(offending_keys))
    if offending_values:
        messages.append("credential-bearing value(s) at: " + ", ".join(offending_values))

    raise ConfigurationError(
        "Configuration must not contain secrets; found " + "; ".join(messages),
        details={"offending_keys": offending_keys, "offending_values": offending_values},
    )
