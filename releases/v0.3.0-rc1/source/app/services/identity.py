from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Identity:
    actor: str
    role: str
    authenticated: bool


def _configured_identities() -> dict[str, Identity]:
    """Read local token -> identity mapping from server environment.

    Example:
    CCI_LOCAL_IDENTITIES_JSON='{
      "pm-secret-token":{"actor":"zhangsan","role":"project_manager"},
      "tech-secret-token":{"actor":"lisi","role":"technical"}
    }'

    No privileged identity is shipped in source code. Missing/invalid configuration
    falls back to anonymous viewer access only.
    """
    raw = os.getenv("CCI_LOCAL_IDENTITIES_JSON", "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    out: dict[str, Identity] = {}
    if not isinstance(data, dict):
        return out
    for token, value in data.items():
        if not isinstance(token, str) or not token or not isinstance(value, dict):
            continue
        actor = str(value.get("actor") or "").strip()
        role = str(value.get("role") or "").strip()
        if actor and role:
            out[token] = Identity(actor=actor, role=role, authenticated=True)
    return out


def resolve_identity(token: str | None) -> Identity:
    if token:
        identity = _configured_identities().get(token)
        if identity:
            return identity
    return Identity(actor="anonymous", role="viewer", authenticated=False)
