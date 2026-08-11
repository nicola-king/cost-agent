from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.identity import register_login


router = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    login_id: str
    verification_secret: str
    device_id: str | None = None


@router.post("/register")
def register(body: LoginRequest):
    token, identity = register_login(body.login_id, body.verification_secret, body.device_id)
    if not token:
        return {
            "authenticated": False,
            "status": identity.status,
            "role": "viewer",
            "actor": identity.actor,
        }
    return {
        "authenticated": True,
        "status": identity.status,
        "actor": identity.actor,
        "role": identity.role,
        "login_id": identity.login_id,
        "session_token": token,
    }


@router.get("/me")
def me(request: Request):
    identity = request.state.identity
    return {
        "authenticated": identity.authenticated,
        "status": identity.status,
        "actor": identity.actor,
        "role": identity.role,
        "login_id": identity.login_id,
    }
