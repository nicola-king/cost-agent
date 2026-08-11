from __future__ import annotations

import json
from urllib.parse import parse_qsl, urlencode

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.services.identity import resolve_identity


TOKEN_HEADER = "x-cci-identity-token"


class IdentityBindingMiddleware(BaseHTTPMiddleware):
    """Bind client requests to a server-resolved local identity.

    The client may still send legacy `actor`/`role` fields for backward-compatible
    request shapes, but they are overwritten before business routes see them.
    Privileged role selection therefore cannot be achieved by editing UI/API input.
    """

    async def dispatch(self, request: Request, call_next):
        identity = resolve_identity(request.headers.get(TOKEN_HEADER))
        request.state.identity = identity

        path = request.url.path
        if path == "/api/capabilities/execute" and request.method.upper() == "POST":
            raw = await request.body()
            try:
                body = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                body = None
            if isinstance(body, dict):
                body["actor"] = identity.actor
                body["role"] = identity.role
                patched = json.dumps(body, ensure_ascii=False).encode("utf-8")

                async def receive():
                    return {"type": "http.request", "body": patched, "more_body": False}

                request._receive = receive

        if request.method.upper() == "GET" and (
            path.endswith("/workspace") or path.endswith("/commercial-access")
        ):
            pairs = [(k, v) for k, v in parse_qsl(request.scope.get("query_string", b"").decode()) if k != "role"]
            pairs.append(("role", identity.role))
            request.scope["query_string"] = urlencode(pairs).encode()

        response = await call_next(request)
        response.headers["X-CCI-Actor"] = identity.actor
        response.headers["X-CCI-Role"] = identity.role
        response.headers["X-CCI-Authenticated"] = "true" if identity.authenticated else "false"
        return response
