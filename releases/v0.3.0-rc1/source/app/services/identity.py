from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Identity:
    actor: str
    role: str
    authenticated: bool
    login_id: str | None = None
    status: str = "active"


ROOT = Path(__file__).resolve().parents[2]
AUTH_DB = ROOT / "data" / "access_identity.sqlite3"


def _connect() -> sqlite3.Connection:
    AUTH_DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(AUTH_DB)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS identity_sessions (
            token_hash TEXT PRIMARY KEY,
            login_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            role TEXT NOT NULL,
            device_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    return db


def _preregistered() -> dict[str, dict]:
    """Load server-managed preregistered people.

    Example server configuration:
    CCI_PREREGISTERED_IDENTITIES_JSON='{
      "13800000000": {
        "actor": "张三",
        "role": "project_manager",
        "department": "project",
        "verification_secret": "initial-code"
      }
    }'

    The client never assigns its own role. Only records present here can obtain a
    privileged role. In production the secret should be injected securely rather
    than committed to source control.
    """
    raw = os.getenv("CCI_PREREGISTERED_IDENTITIES_JSON", "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    out = {}
    for login_id, value in data.items():
        if not isinstance(login_id, str) or not login_id.strip() or not isinstance(value, dict):
            continue
        actor = str(value.get("actor") or "").strip()
        role = str(value.get("role") or "").strip()
        secret = str(value.get("verification_secret") or "")
        if actor and role and secret:
            out[login_id.strip()] = {**value, "actor": actor, "role": role, "verification_secret": secret}
    return out


def register_login(login_id: str, verification_secret: str, device_id: str | None = None) -> tuple[str | None, Identity]:
    record = _preregistered().get((login_id or "").strip())
    if not record:
        return None, Identity(actor="pending", role="viewer", authenticated=False, login_id=login_id or None, status="not_preregistered")
    expected = record["verification_secret"]
    if not hmac.compare_digest(str(verification_secret or ""), expected):
        return None, Identity(actor="pending", role="viewer", authenticated=False, login_id=login_id, status="verification_failed")

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    identity = Identity(
        actor=record["actor"],
        role=record["role"],
        authenticated=True,
        login_id=login_id,
        status="active",
    )
    with _connect() as db:
        db.execute(
            "INSERT INTO identity_sessions(token_hash,login_id,actor,role,device_id,status) VALUES(?,?,?,?,?,?)",
            (token_hash, login_id, identity.actor, identity.role, device_id, identity.status),
        )
        db.commit()
    return token, identity


def resolve_identity(token: str | None) -> Identity:
    if not token:
        return Identity(actor="anonymous", role="viewer", authenticated=False, status="anonymous")
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with _connect() as db:
        row = db.execute(
            "SELECT login_id,actor,role,status FROM identity_sessions WHERE token_hash=?",
            (token_hash,),
        ).fetchone()
        if not row or row[3] != "active":
            return Identity(actor="anonymous", role="viewer", authenticated=False, status="invalid_session")
        db.execute("UPDATE identity_sessions SET last_seen_at=CURRENT_TIMESTAMP WHERE token_hash=?", (token_hash,))
        db.commit()
    return Identity(actor=row[1], role=row[2], authenticated=True, login_id=row[0], status=row[3])
